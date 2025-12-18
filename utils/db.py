# utils/db.py
import sqlite3
import pandas as pd
from typing import Tuple, Any

# NEW: Import ALL necessary keys
from utils.parse import (
    # Scraper Keys (Dict Inputs)
    COL_TITLE, COL_BRAND, COL_MODEL, COL_PKG, COL_COND, COL_FUNC,
    COL_MISSING, COL_MISSING_DESC, COL_DMG, COL_DMG_DESC, COL_NOTES,
    COL_UPC, COL_ASIN, COL_URL, COL_CAT,
    
    # DB Keys (Column Names)
    KEY_DB_TITLE, KEY_DB_BRAND, KEY_DB_MODEL, KEY_DB_PKG, KEY_DB_COND, 
    KEY_DB_FUNC, KEY_DB_MISSING, KEY_DB_MISSING_DESC, KEY_DB_DMG, 
    KEY_DB_DMG_DESC, KEY_DB_ITEM_NOTES, KEY_DB_UPC, KEY_DB_ASIN, KEY_DB_URL,
    KEY_IS_WATCHED, KEY_IS_HIDDEN, KEY_SOLD_PRICE, KEY_STATUS, 
    KEY_SUG_MSRP, KEY_DB_SCRAPED_CAT, KEY_IS_WON
)

def create_connection(db_path: str = "auctions.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    ensure_schema(conn)
    return conn

def ensure_schema(conn: sqlite3.Connection) -> None:
    # (Schema creation strings remain literal SQL)
    with conn:
        conn.execute("CREATE TABLE IF NOT EXISTS auctions (id INTEGER PRIMARY KEY, url TEXT UNIQUE, scrape_date TEXT DEFAULT CURRENT_TIMESTAMP, auctioneer TEXT, auction_title TEXT, end_date TEXT)")
        conn.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, brand TEXT, model TEXT, upc TEXT UNIQUE, asin TEXT UNIQUE, category TEXT, msrp REAL, avg_sold_price REAL, target_list_price REAL, shipping_cost_basis REAL, weight_lbs REAL, weight_oz REAL, length REAL, width REAL, height REAL, is_irregular BOOLEAN DEFAULT 0, ship_method TEXT,
            ebay_avg_sold_price REAL, ebay_sold_range_low REAL, ebay_sold_range_high REAL, ebay_avg_shipping_sold REAL, ebay_sell_through_rate REAL, ebay_total_sold_count INTEGER, ebay_total_sellers INTEGER, ebay_active_count INTEGER, ebay_avg_list_price REAL, ebay_active_low REAL, ebay_active_high REAL, ebay_avg_shipping_active REAL, ebay_num_watchers INTEGER, market_notes TEXT,
            amazon_url TEXT, amazon_new_price REAL, amazon_used_price REAL, amazon_listing_price REAL, amazon_sales_rank INTEGER, amazon_reviews INTEGER, amazon_stars REAL, amazon_rank_main INTEGER, amazon_cat_name TEXT, amazon_rank_sub INTEGER, amazon_subcat_name TEXT,
            notes TEXT, is_favorite BOOLEAN DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS auction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, auction_id INTEGER NOT NULL, product_id INTEGER, lot TEXT, current_bid REAL DEFAULT 0, sold_price REAL DEFAULT 0, status TEXT DEFAULT 'Active', title TEXT, brand TEXT, model TEXT, packaging TEXT, condition TEXT, functional TEXT, missing_parts TEXT, missing_parts_desc TEXT, damaged TEXT, damage_desc TEXT, item_notes TEXT, upc TEXT, asin TEXT, url TEXT, suggested_msrp REAL DEFAULT 0, scraped_category TEXT, is_watched INTEGER DEFAULT 0, is_hidden INTEGER DEFAULT 0, is_won INTEGER DEFAULT 0,
            FOREIGN KEY (auction_id) REFERENCES auctions(id) ON DELETE CASCADE, FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        )""")
        conn.execute("CREATE TABLE IF NOT EXISTS inventory_ledger (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, auction_source TEXT, purchase_date TEXT DEFAULT CURRENT_TIMESTAMP, lot_number TEXT, purchase_price REAL, fees_paid REAL DEFAULT 0, shipping_paid REAL DEFAULT 0, total_cost REAL DEFAULT 0, status TEXT DEFAULT 'In Stock', listing_price REAL DEFAULT 0, sold_price REAL DEFAULT 0, sold_date TEXT, notes TEXT, FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS product_price_history (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL, sold_price REAL, sold_date TEXT, auction_source TEXT, FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE)")
        
        cursor = conn.cursor()
        cols = [row[1] for row in cursor.execute("PRAGMA table_info(auction_items)")]
        if 'is_won' not in cols: cursor.execute("ALTER TABLE auction_items ADD COLUMN is_won INTEGER DEFAULT 0")

def insert_auction(conn, auction_id, url):
    conn.execute("INSERT OR IGNORE INTO auctions (id, url) VALUES (?, ?)", (auction_id, url))
    conn.commit()

def update_auction_metadata(conn, auction_id, title, auctioneer, end_date):
    conn.execute("UPDATE auctions SET auction_title = ?, auctioneer = ?, end_date = ? WHERE id = ?", (title, auctioneer, end_date, auction_id))
    conn.commit()

def insert_auction_item(conn, auction_id, lot, current_bid, details: dict):
    # Lookup values using Display Keys (COL_) because that's what Scraper sends
    # Use KEY_SUG_MSRP because we updated Scraper to use that specific Key
    conn.execute("""
        INSERT INTO auction_items (
            auction_id, lot, current_bid, title, brand, model,
            packaging, condition, functional, missing_parts, missing_parts_desc,
            damaged, damage_desc, item_notes, upc, asin, url, 
            suggested_msrp, scraped_category
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        auction_id, lot, current_bid,
        details.get(COL_TITLE), details.get(COL_BRAND), details.get(COL_MODEL),
        details.get(COL_PKG), details.get(COL_COND), details.get(COL_FUNC),
        details.get(COL_MISSING), details.get(COL_MISSING_DESC),
        details.get(COL_DMG), details.get(COL_DMG_DESC),
        details.get(COL_NOTES), details.get(COL_UPC), details.get(COL_ASIN), details.get(COL_URL),
        details.get(KEY_SUG_MSRP, 0), details.get(COL_CAT)
    ))
    conn.commit()

def update_item_field(conn, item_id: int, field: str, value: Any):
    # Uses Database Keys (KEY_DB_)
    allowed = [
        KEY_DB_TITLE, KEY_DB_BRAND, KEY_DB_MODEL, KEY_DB_PKG, KEY_DB_COND, 
        KEY_DB_FUNC, KEY_DB_MISSING, KEY_DB_MISSING_DESC, KEY_DB_DMG, 
        KEY_DB_DMG_DESC, KEY_DB_ITEM_NOTES, KEY_DB_UPC, KEY_DB_ASIN, KEY_DB_URL,
        KEY_IS_WATCHED, KEY_IS_HIDDEN, KEY_SOLD_PRICE, KEY_STATUS, 
        KEY_SUG_MSRP, KEY_DB_SCRAPED_CAT, KEY_IS_WON
    ]
    if field.lower() not in allowed: return
    conn.execute(f"UPDATE auction_items SET {field} = ? WHERE id = ?", (value, item_id))
    conn.commit()

def update_item_status(conn, item_id: int, field: str, value: int):
    update_item_field(conn, item_id, field, value)

def update_final_price(conn, auction_id: int, lot_number: str, sold_price: float, status: str):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE auction_items SET sold_price = ?, status = ? WHERE auction_id = ? AND lot = ?
    """, (sold_price, status, auction_id, lot_number))
    conn.commit()

def get_active_auctions(conn) -> pd.DataFrame:
    return pd.read_sql_query("""
        SELECT a.id, a.url, a.scrape_date, a.auction_title, a.auctioneer, a.end_date, COUNT(i.id) AS item_count
        FROM auctions a
        LEFT JOIN auction_items i ON i.auction_id = a.id
        GROUP BY a.id, a.url, a.scrape_date
        HAVING SUM(CASE WHEN i.sold_price > 0 THEN 1 ELSE 0 END) = 0
        ORDER BY a.scrape_date DESC
    """, conn)

def get_closed_auctions(conn) -> pd.DataFrame:
    return pd.read_sql_query("""
        SELECT a.id, a.url, a.scrape_date, a.auction_title, a.auctioneer, a.end_date, COUNT(i.id) AS item_count
        FROM auctions a
        LEFT JOIN auction_items i ON i.auction_id = a.id
        GROUP BY a.id, a.url, a.scrape_date
        HAVING SUM(CASE WHEN i.sold_price > 0 THEN 1 ELSE 0 END) > 0
        ORDER BY a.scrape_date DESC
    """, conn)

def get_auction_items(conn, auction_id: int) -> pd.DataFrame:
    return pd.read_sql_query("""
        SELECT
            i.id, i.auction_id, i.product_id,
            i.lot as lot_number, 
            i.current_bid, i.sold_price, i.status, 
            i.suggested_msrp,
            i.scraped_category,
            
            COALESCE(p.title, i.title) as title,
            COALESCE(p.brand, i.brand) as brand,
            COALESCE(p.model, i.model) as model,
            COALESCE(p.upc, i.upc) as upc,
            COALESCE(p.asin, i.asin) as asin,
            COALESCE(p.category, i.scraped_category) as category,
            
            p.msrp as master_msrp,
            p.target_list_price as master_target_price,
            p.shipping_cost_basis,
            
            i.packaging, i.condition, i.functional, 
            i.missing_parts, i.missing_parts_desc,
            i.damaged, i.damage_desc, 
            i.item_notes, i.url,
            i.is_watched, i.is_hidden,
            i.is_won
            
        FROM auction_items i
        LEFT JOIN products p ON i.product_id = p.id
        WHERE i.auction_id = ?
    """, conn, params=(auction_id,))