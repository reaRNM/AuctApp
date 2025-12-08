
import requests
import pandas as pd
import json
import argparse
import re  # For regex
import time
import os
from typing import Optional, Dict, Any
from utils.db import create_connection, ensure_schema, insert_auction_item, insert_auction, update_auction_metadata
from dotenv import load_dotenv

# Create output directory just in case
os.makedirs("output", exist_ok=True)

load_dotenv()


# === CONFIGURATION ===
BEARER_TOKEN = os.getenv("HIBID_TOKEN")

if not BEARER_TOKEN:
    raise ValueError("Error: HIBID_TOKEN not found in .env file")
  
  
graphql_url = "https://hibid.com/graphql"

headers_template = {
    'authority': 'hibid.com',
    'method': 'POST',
    'path': '/graphql',
    'scheme': 'https',
    'accept': 'application/json, text/plain, */*',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': BEARER_TOKEN,
    'content-type': 'application/json',
    'origin': 'https://hibid.com',
    'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Chrome OS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'site_subdomain': 'hibid.com',
    'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
}

cookies = {
    '_cq_duid': '1.1740059255.RYtXvKLAuzifedS4',
    '_cq_suid': '1.1740059255.PbHQAuoyQBy4y0no',
    '_pin_unauth': 'dWlkPU1HRTFObUZpWVRRdE5HVTFZeTAwTW1RekxUbGlNRGt0TnpFMk5UQmxORFF5WkRWaQ',
    '_hjSessionUser_1002726': 'eyJpZCI6ImExM2QzYTliLTc0ZmItNWQyOS05MGE0LTgxNDkxY2I1Zjc3ZiIsImNyZWF0ZWQiOjE3NDAwNjAxMTU2MTIsImV4aXN0aW5nIjp0cnVlfQ==',
    'HBCookieTracking': 'DefaultCookieSet-Exp:3/22/2025 9:03:14 AM',
    'HBIsLoggedIn': '1',
    'navCounter': '3',
    'subDoNotPrompt': 'true',
    'lotViewMode': '0',
    'UseInfiniteScroll': 'true',
    'lotsperpage': '100',
    '_ga_6MG77QNJZX': 'GS1.1.1740181624.3.0.1740182446.0.0.0',
    '_gid': 'GA1.2.1150965580.1740546808',
    '__gads': 'ID=c967a7ba2cd5cba1:T=1740060112:RT=1740711145:S=ALNI_MbaL9Yc0lXWI5sTsiYfJeHbR8UUSw',
    '__eoi': 'ID=77b2d2f33d297f0c:T=1740060112:RT=1740711145:S=AA-AfjZqQXB3p-_6U6TayZRks5Ua',
    '__cf_bm': 'DPZnaaXFUGCKUsFGvzOUL6r7q7L5pqetrTeqAusdc3s-1740736285-1.0.1.1-gj0cxCUFynQOhlkOehjH2_ha_1Zw.01KFFyFfZNHgHjKHtGWoF.qSs7p3tC25LahP2wXXlN9Mzzm.D1k1zOYTQ',
    '_gat_UA-772246-8': '1',
    '_gat_gtag_UA_772246_5': '1',
    '_ga_WDTLCRKGW8': 'GS1.1.1740736657.29.1.1740736659.0.0.0',
    '_ga': 'GA1.1.1022542906.1740059254',
    '_hjSession_1002726': 'eyJpZCI6IjYyOGY1ZTBlLTY1MWYtNDAwMS1iNmM2LWE3MTgyZWExMjNhNSIsImMiOjE3NDA3MzY2NTk4MjAsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=',
    '_uetsid': '6a470970f40011ef99e8f3f2da8fe138',
    '_uetvid': '3ddd11f0ef9111ef9dd9dde7cb131fcf',
    '_derived_epik': 'dj0yJnU9TnZwTDhrYVVpMU40anBnNTVTcHNhWTl6eEprQVlQS0wmbj16MEdISkQ1UGZNSDFkemNqU2ZnMTNBJm09MSZ0PUFBQUFBR2ZCaUpVJnJtPTEmcnQ9QUFBQUFHZkJpSlUmc3A9Mg',
}

# UPDATED QUERY: Now includes the correct "category" structure
query = """
    query LotSearch($auctionId: Int = null, $pageNumber: Int!, $pageLength: Int!, $category: CategoryId = null, $searchText: String = null, $zip: String = null, $miles: Int = null, $shippingOffered: Boolean = false, $countryName: String = null, $status: AuctionLotStatus = null, $sortOrder: EventItemSortOrder = null, $filter: AuctionLotFilter = null, $isArchive: Boolean = false, $dateStart: DateTime, $dateEnd: DateTime, $countAsView: Boolean = true, $hideGoogle: Boolean = false) {
      lotSearch(
        input: {auctionId: $auctionId, category: $category, searchText: $searchText, zip: $zip, miles: $miles, shippingOffered: $shippingOffered, countryName: $countryName, status: $status, sortOrder: $sortOrder, filter: $filter, isArchive: $isArchive, dateStart: $dateStart, dateEnd: $dateEnd, countAsView: $countAsView, hideGoogle: $hideGoogle}
        pageNumber: $pageNumber
        pageLength: $pageLength
        sortDirection: DESC
      ) {
        pagedResults {
          pageLength
          pageNumber
          totalCount
          filteredCount
          results {
            category {
              categoryName
              fullCategory
              __typename
            }
            auction {
              ...auctionMinimum
              __typename
            }
            bidAmount
            bidList
            bidQuantity
            description
            estimate
            featuredPicture {
              description
              fullSizeLocation
              height
              hdThumbnailLocation
              thumbnailLocation
              width
              __typename
            }
            forceLiveCatalog
            fr8StarUrl
            hideLeadWithDescription
            id
            itemId
            lead
            links {
              description
              id
              type
              url
              videoId
              __typename
            }
            linkTypes
            lotNumber
            lotState {
              bidCount
              biddingExtended
              bidMax
              bidMaxTotal
              buyerBidStatus
              buyerHighBid
              buyerHighBidTotal
              buyNow
              choiceType
              highBid
              highBuyerId
              isArchived
              isClosed
              isHidden
              isLive
              isNotYetLive
              isOnLiveCatalog
              isPosted
              isPublicHidden
              isRegistered
              isWatching
              linkedSoftClose
              mayHaveWonStatus
              minBid
              priceRealized
              priceRealizedMessage
              priceRealizedPerEach
              productStatus
              productUrl
              quantitySold
              reserveSatisfied
              sealed
              showBidStatus
              showReserveStatus
              softCloseMinutes
              softCloseSeconds
              status
              timeLeft
              timeLeftLead
              timeLeftSeconds
              timeLeftTitle
              timeLeftWithLimboSeconds
              watchNotes
              __typename
            }
            pictureCount
            quantity
            ringNumber
            rv
            shippingOffered
            simulcastStatus
            site {
              domain
              fr8StarUrl
              isDomainRequest
              isExtraWWWRequest
              siteType
              subdomain
              __typename
            }
            distanceMiles
            __typename
          }
          __typename
        }
        __typename
      }
    }

    fragment auctionMinimum on Auction {
      id
      altBiddingUrl
      altBiddingUrlCaption
      amexAccepted
      discoverAccepted
      mastercardAccepted
      visaAccepted
      regType
      holdAmount
      auctioneer {
        ...auctioneer
        __typename
      }
      auctionOptions {
        bidding
        altBidding
        catalog
        liveCatalog
        shippingType
        preview
        registration
        webcast
        useLotNumber
        useSaleOrder
        __typename
      }
      auctionState {
        auctionStatus
        bidCardNumber
        isRegistered
        openLotCount
        timeToOpen
        __typename
      }
      bidAmountType
      bidIncrements {
        minBidIncrement
        upToAmount
        __typename
      }
      bidOpenDateTime
      bidCloseDateTime
      bidType
      buyerPremium
      buyerPremiumRate
      checkoutDateInfo
      previewDateInfo
      currencyAbbreviation
      description
      eventAddress
      eventCity
      eventDateBegin
      eventDateEnd
      eventDateInfo
      eventName
      eventState
      eventZip
      featuredPicture {
        description
        fullSizeLocation
        height
        hdThumbnailLocation
        thumbnailLocation
        width
        __typename
      }
      links {
        description
        id
        type
        url
        videoId
        __typename
      }
      lotCount
      showBuyerPremium
      audioVideoChatInfo {
        aVCEnabled
        blockChat
        __typename
      }
      hidden
      sourceType
      distanceMiles
      __typename
    }

    fragment auctioneer on Auctioneer {
      address
      bidIncrementDisclaimer
      buyerRegNotesCaption
      city
      countryId
      country
      cRMID
      email
      fax
      id
      internetAddress
      missingThumbnail
      name
      noMinimumCaption
      phone
      state
      postalCode
      __typename
    }
"""

# === CONSTANTS ===
DAMAGE_DESCRIPTION = "Damage Description"
MISSING_PARTS_DESCRIPTION = "Missing Parts Description"
MISSING_PARTS = "Missing Parts"

# Regex for extracting MSRP from title ($123 Title)
PRICE_PATTERN = re.compile(r'^\s*\$(\d+(?:,\d+)*(?:\.\d+)?)\s+(.*)')

# === HELPER FUNCTIONS ===
def extract_auction_id(url: str) -> int:
    """Extract numeric auction ID from a HiBid URL."""
    pattern = r'/catalog/(\d+)|/lots/(\d+)'
    m = re.search(pattern, url)
    if not m:
        raise ValueError("Could not extract auction ID from URL. Check format.")
    return int(m.group(1) or m.group(2))

def get_current_bid(item: dict) -> float:
    lot_state = item.get('lotState', {})
    bid_count = lot_state.get('bidCount', 0)
    if bid_count > 0:
        return lot_state.get('highBid', 0.0)
    return 0.0

def parse_description(description_text: str) -> dict:
    lines = description_text.splitlines()
    data = {}
    field_mappings = {
        "Title:": ("Title", 6), 
        "Brand:": ("Brand", 6),
        "Model:": ("Model", 6),
        "In Packaging?:": ("Packaging", 14),
        "Condition:": ("Condition", 10),
        "Functional?:": ("Functional", 12),
        "Missing Parts?:": ("Missing Parts", 15),
        "Missing Parts Description:": ("Missing Parts Description", 26),
        "Damaged?:": ("Damaged", 9), 
        "Damage Description:": ("Damage Description", 19),
        "Notes:": ("Notes", 6), 
        "UPC:": ("UPC", 4),
        "ASIN:": ("ASIN", 5),
        "Retailer Item URL:": ("URL", 18),
    }
    for line in lines:
        line = line.strip()
        for prefix, (key, offset) in field_mappings.items():
            if line.startswith(prefix):
                data[key] = line[offset:].strip()
                break
    
    if 'Title' in data:
        match = PRICE_PATTERN.match(data['Title'])
        if match:
            try:
                data['SuggestedMSRP'] = float(match.group(1).replace(',', ''))
                data['Title'] = match.group(2).strip()
            except ValueError: pass
    return data

def process_items(conn, auction_id: int, items: list) -> None:
    for item in items:
        lot_number = item['lotNumber']
        current_bid = get_current_bid(item)
        parsed = parse_description(item.get('description', ''))

        # Fallback: if description doesn't contain a Retailer URL, use HiBid's productUrl/links
        if not parsed.get("URL"):
            lot_state = item.get("lotState", {}) or {}
            hibid_url = lot_state.get("productUrl")
            if not hibid_url:
                links = item.get("links") or []
                # Prefer the first link with a URL
                for link in links:
                    if link.get("url"):
                        hibid_url = link["url"]
                        break
            if hibid_url:
                parsed["URL"] = hibid_url
        
        cat_list = item.get('category', [])
        if cat_list and isinstance(cat_list, list) and len(cat_list) > 0:
            parsed['Category'] = cat_list[0].get('categoryName', 'Uncategorized')
        else:
            cat_obj = item.get('primaryCategory')
            parsed['Category'] = cat_obj['name'] if cat_obj else "Uncategorized"

        insert_auction_item(conn, auction_id, lot_number, current_bid, parsed)

def create_request_payload(auction_id: int, page_number: int) -> dict:
    return {
        "operationName": "LotSearch",
        "query": query,
        "variables": {
            "auctionId": auction_id, 
            "pageNumber": page_number, 
            "pageLength": 100,
            "category": None,
            "searchText": None,
            "zip": "", 
            "miles": 50,
            "shippingOffered": False,
            "countryName": "",
            "status": "ALL",
            "sortOrder": "LOT_NUMBER", 
            "filter": "ALL",
            "isArchive": False,
            "dateStart": None,
            "dateEnd": None,
            "countAsView": True, 
            "hideGoogle": False,
        },
    }

# FIXED: Correct Type Hint (Optional[Dict])
def _fetch_page(auction_id: int, page: int, headers: dict) -> Optional[Dict[str, Any]]:
    print(f"Fetching page {page}...")
    try:
        response = requests.post(graphql_url, headers=headers, json=create_request_payload(auction_id, page), cookies=cookies, timeout=60)
        if response.status_code == 200:
            return response.json()
        print(f"Failed: {response.status_code}")
        return None
    except Exception as e:
        print(f"Network error: {e}")
        return None

def _process_page_results(conn, auction_id: int, data: dict) -> int:
    if 'data' not in data or 'lotSearch' not in data['data']:
        print("Error: Invalid JSON response")
        return -1

    items = data['data']['lotSearch']['pagedResults']['results']
    if not items:
        print("No more items found.")
        return 0
    
    process_items(conn, auction_id, items)
    return len(items)

def _setup_database(auction_id: int, auction_url: str):
    conn = create_connection()
    if not conn: return None
    ensure_schema(conn)
    insert_auction(conn, auction_id, auction_url)
    return conn

# FIXED: Helper function to handle Metadata logic (Reduces complexity)
def _try_capture_metadata(conn, auction_id: int, items: list) -> bool:
    try:
        if items:
            first = items[0]
            auc_info = first.get('auction', {})
            title = auc_info.get('eventName', 'Unknown Title')
            auctioneer = auc_info.get('auctioneer', {}).get('name', 'Unknown')
            end_date = auc_info.get('eventDateEnd', '').split('T')[0]
            print(f"📌 Info: {title} | {auctioneer} | Ends: {end_date}")
            update_auction_metadata(conn, auction_id, title, auctioneer, end_date)
            return True
    except Exception as e:
        print(f"Metadata Warning: {e}")
    return False

def _scrape_loop(conn, auction_id: int, headers: dict) -> int:
    page = 1
    total_saved = 0
    metadata_saved = False
    
    while True:
        data = _fetch_page(auction_id, page, headers)
        if not data: break
            
        items = data.get('data', {}).get('lotSearch', {}).get('pagedResults', {}).get('results', [])
        if not items: break
        
        # Capture Metadata once
        if not metadata_saved:
            metadata_saved = _try_capture_metadata(conn, auction_id, items)

        count = _process_page_results(conn, auction_id, data)
        if count <= 0: break
            
        total_saved += count
        print(f"  Processed {count} items. (Total: {total_saved})")
        
        if count < 100: break
        page += 1
        time.sleep(0.5)
        
    return total_saved

def scrape_auction(auction_url: str) -> None:
    try: auction_id = extract_auction_id(auction_url)
    except ValueError as e: print(f"Error: {e}"); return

    conn = _setup_database(auction_id, auction_url)
    if not conn: return

    headers = headers_template.copy()
    headers['referer'] = auction_url
    
    print(f"Scraping auction: {auction_url}")
    total = _scrape_loop(conn, auction_id, headers)

    conn.close()
    print(f"Done! Total items saved: {total}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str)
    args = parser.parse_args()
    scrape_auction(args.url)
