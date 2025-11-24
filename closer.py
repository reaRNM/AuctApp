# closer.py
import requests
import argparse
import re
import os
from utils.db import create_connection, update_final_price
from utils.analytics import update_all_product_stats
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === CONFIGURATION ===
BEARER_TOKEN = os.getenv("HIBID_TOKEN")

if not BEARER_TOKEN:
    raise ValueError("Error: HIBID_TOKEN not found in .env file")

graphql_url = "https://hibid.com/graphql"

headers = {
    'authority': 'hibid.com',
    'method': 'POST',
    'path': '/graphql',
    'scheme': 'https',
    'accept': 'application/json, text/plain, */*',
    'authorization': BEARER_TOKEN,
    'content-type': 'application/json',
    'origin': 'https://hibid.com',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
}

# Query to get Final Price (priceRealized)
query = """
    query LotSearch($auctionId: Int = null, $pageNumber: Int!, $pageLength: Int!) {
      lotSearch(
        input: {auctionId: $auctionId}
        pageNumber: $pageNumber
        pageLength: $pageLength
        sortDirection: DESC
      ) {
        pagedResults {
          results {
            lotNumber
            lotState {
              highBid
              priceRealized
              status
            }
          }
        }
      }
    }
"""

def extract_auction_id(url: str) -> int:
    pattern = r'/catalog/(\d+)|/lots/(\d+)'
    m = re.search(pattern, url)
    if not m: raise ValueError("Invalid URL")
    return int(m.group(1) or m.group(2))

def process_closed_auction(auction_url: str):
    auction_id = extract_auction_id(auction_url)
    print(f"🔒 Closing Auction ID: {auction_id}")
    
    conn = create_connection()
    
    payload = {
        "operationName": "LotSearch",
        "query": query,
        "variables": {
            "auctionId": auction_id,
            "pageNumber": 1,
            "pageLength": 9000
        },
    }
    
    response = requests.post(graphql_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        return

    data = response.json()
    items = data['data']['lotSearch']['pagedResults']['results']
    print(f"Processing {len(items)} items...")
    
    updated_count = 0
    
    for item in items:
        lot_num = item['lotNumber']
        state = item.get('lotState', {})
        
        # Get Realized Price
        sold_price = state.get('priceRealized') or 0.0
        
        # Determine Status
        if sold_price > 0:
            status = "Sold"
        else:
            if state.get('highBid', 0) > 0:
                status = "Passed (Reserve Not Met)"
            else:
                status = "Unsold/Passed"
            
        update_final_price(conn, auction_id, lot_num, sold_price, status)
        updated_count += 1
    
    # === RUN THE BRAIN ===
    print("🧠 Running Post-Auction Analytics...")
    try:
        update_all_product_stats(conn)
        print("✅ Analytics updated.")
    except Exception as e:
        print(f"⚠️ Analytics skipped (Error: {e})")
        
    conn.close()
    print(f"✅ Successfully updated {updated_count} items with final prices!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Close out an auction.")
    parser.add_argument("url", type=str, help="Auction URL")
    args = parser.parse_args()
    
    process_closed_auction(args.url)