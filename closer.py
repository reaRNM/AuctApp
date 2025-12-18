# closer.py
import argparse
from dotenv import load_dotenv
from utils.db import create_connection
from scraper import scrape_auction 
# NEW: Import Constants
from utils.parse import KEY_CURRENT_BID, KEY_PROD_ID, KEY_SOLD_PRICE, KEY_IS_WON

load_dotenv(override=True)

def process_closed_auction(auction_url: str):
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Get Auction Info
        res = cursor.execute("SELECT id, auction_title, auctioneer, end_date FROM auctions WHERE url = ?", (auction_url,)).fetchone()
        if not res: print("Auction not found."); return
        
        auction_id, auc_title, auctioneer, end_date = res
        source_name = f"{auctioneer} - {auc_title}"
        close_date = end_date or "Unknown"

        # 2. REFRESH PRICES (Scraper Mode: Update)
        print("🕷️ Refreshing final prices...")
        try:
            scrape_auction(auction_url, is_update=True)
        except Exception as e:
            print(f"⚠️ Scrape warning: {e}. Using cached data.")

        # 3. HARVEST MARKET DATA
        print("🧠 Harvesting market data...")
        # Uses Constants in SQL logic where appropriate, though SQL structure is fixed
        market_items = cursor.execute(f"""
            SELECT {KEY_PROD_ID}, {KEY_CURRENT_BID} FROM auction_items 
            WHERE auction_id = ? AND {KEY_PROD_ID} IS NOT NULL AND {KEY_CURRENT_BID} > 0
        """, (auction_id,)).fetchall()
        
        for pid, price in market_items:
            cursor.execute("INSERT INTO product_price_history (product_id, sold_price, sold_date, auction_source) VALUES (?, ?, ?, ?)", 
                           (pid, price, close_date, source_name))
            
            avg = cursor.execute("SELECT AVG(sold_price) FROM product_price_history WHERE product_id=?", (pid,)).fetchone()[0]
            if avg: cursor.execute("UPDATE products SET avg_sold_price = ? WHERE id=?", (round(avg,2), pid))

        # 4. MIGRATE WON ITEMS
        print("📦 Moving winners to Inventory...")
        won_items = cursor.execute(f"""
            SELECT {KEY_PROD_ID}, lot, {KEY_CURRENT_BID}, title FROM auction_items 
            WHERE auction_id = ? AND {KEY_IS_WON} = 1
        """, (auction_id,)).fetchall()
        
        for pid, lot, price, title in won_items:
            cursor.execute("""
                INSERT INTO inventory_ledger (product_id, auction_source, lot_number, purchase_price, total_cost, status, notes)
                VALUES (?, ?, ?, ?, ?, 'In Stock', ?)
            """, (pid, source_name, lot, price, price, f"Won: {title}"))

        # 5. PURGE
        print("🗑️ Deleting auction...")
        cursor.execute("DELETE FROM auctions WHERE id = ?", (auction_id,))
        conn.commit()
        print("✅ Auction Closed & Cleaned.")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str)
    args = parser.parse_args()
    process_closed_auction(args.url)