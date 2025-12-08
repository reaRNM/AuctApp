# utils/db.py
import sqlite3
import pandas as pd
from typing import Tuple, Any

def create_connection(db_path: str = "auctions.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    ensure_schema(conn)
    return conn

def ensure_schema(conn: sqlite3.Connection) -> None:
    with conn:
        # 1. AUCTIONS (Updated with Title)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auctions (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE,
                scrape_date TEXT DEFAULT CURRENT_TIMESTAMP,
                auctioneer TEXT,
                auction_title TEXT, -- NEW
                end_date TEXT
            )
        """)

        # 2. PRODUCTS (Update to include is_favorite)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, brand TEXT, model TEXT,
                upc TEXT UNIQUE, asin TEXT UNIQUE, category TEXT,
                msrp REAL, avg_sold_price REAL, target_list_price REAL,
                shipping_cost_basis REAL,
                weight_lbs REAL, weight_oz REAL,
                length REAL, width REAL, height REAL,
                is_irregular BOOLEAN DEFAULT 0, ship_method TEXT,
                ebay_url TEXT, ebay_active_low REAL, ebay_active_high REAL,
                ebay_sold_low REAL, ebay_sold_high REAL, ebay_sell_through REAL,
                amazon_url TEXT, amazon_new_price REAL, amazon_used_price REAL,
                amazon_sales_rank INTEGER,
                notes TEXT, 
                is_favorite BOOLEAN DEFAULT 0, -- NEW FIELD
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. AUCTION ITEMS
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auction_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id INTEGER NOT NULL,
                product_id INTEGER, 
                lot TEXT, current_bid REAL DEFAULT 0,
                sold_price REAL DEFAULT 0, status TEXT DEFAULT 'Active', 
                title TEXT, brand TEXT, model TEXT,
                packaging TEXT, condition TEXT, functional TEXT,
                missing_parts TEXT, missing_parts_desc TEXT,
                damaged TEXT, damage_desc TEXT,
                item_notes TEXT, upc TEXT, asin TEXT, url TEXT,
                suggested_msrp REAL DEFAULT 0, scraped_category TEXT,
                is_watched INTEGER DEFAULT 0, is_hidden INTEGER DEFAULT 0,
                FOREIGN KEY (auction_id) REFERENCES auctions(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
            )
        """)
        
        # --- MIGRATIONS ---
        cursor = conn.cursor()
        
        # Add auction_title if missing
        auc_cols = [row[1] for row in cursor.execute("PRAGMA table_info(auctions)")]
        if 'auction_title' not in auc_cols:
            try: cursor.execute("ALTER TABLE auctions ADD COLUMN auction_title TEXT")
            except sqlite3.OperationalError: pass
        if 'auctioneer' not in auc_cols:
            try: cursor.execute("ALTER TABLE auctions ADD COLUMN auctioneer TEXT")
            except sqlite3.OperationalError: pass
        if 'end_date' not in auc_cols:
            try: cursor.execute("ALTER TABLE auctions ADD COLUMN end_date TEXT")
            except sqlite3.OperationalError: pass

        # Item Migrations
        item_cols = [row[1] for row in cursor.execute("PRAGMA table_info(auction_items)")]
        for col, dtype in {'sold_price': 'REAL', 'status': 'TEXT', 'suggested_msrp': 'REAL', 'scraped_category': 'TEXT'}.items():
            if col not in item_cols:
                try: cursor.execute(f"ALTER TABLE auction_items ADD COLUMN {col} {dtype}")
                except sqlite3.OperationalError: pass

        # Product Migrations
        prod_cols = [row[1] for row in cursor.execute("PRAGMA table_info(products)")]
        new_prod_cols = {
            'ebay_url': 'TEXT', 'ebay_active_low': 'REAL', 'ebay_active_high': 'REAL',
            'ebay_sold_low': 'REAL', 'ebay_sold_high': 'REAL', 'ebay_sell_through': 'REAL',
            'amazon_url': 'TEXT', 'amazon_new_price': 'REAL', 'amazon_used_price': 'REAL',
            'amazon_sales_rank': 'INTEGER',
            'ebay_sold_30d': 'INTEGER', 'ebay_sold_60d': 'INTEGER', 'ebay_sold_90d': 'INTEGER',
            'ebay_num_sellers': 'INTEGER', 'ebay_avg_sold': 'REAL', 'ebay_low_sold': 'REAL', 'ebay_high_sold': 'REAL',
            'ebay_avg_ship_sold': 'REAL', 'ebay_free_ship_pct_sold': 'REAL', 'ebay_ctr': 'REAL',
            'ebay_active_count': 'INTEGER', 'ebay_avg_list': 'REAL', 'ebay_low_list': 'REAL', 'ebay_high_list': 'REAL',
            'ebay_avg_ship_list': 'REAL', 'ebay_free_ship_pct_list': 'REAL', 'ebay_promoted_pct': 'REAL',
            'amazon_price': 'REAL', 'amazon_stars': 'REAL', 'amazon_cat_rank': 'TEXT', 'amazon_subcat_rank': 'TEXT',
            'amazon_sold_30d': 'INTEGER', 'amazon_freq_returned': 'BOOLEAN DEFAULT 0'
        }
        for col, dtype in new_prod_cols.items():
            if col not in prod_cols:
                try: cursor.execute(f"ALTER TABLE products ADD COLUMN {col} {dtype}")
                except sqlite3.OperationalError: pass

        # NEW: Product Favorite Migration
        prod_cols = [row[1] for row in cursor.execute("PRAGMA table_info(products)")]
        if 'is_favorite' not in prod_cols:
            try: cursor.execute("ALTER TABLE products ADD COLUMN is_favorite BOOLEAN DEFAULT 0")
            except sqlite3.OperationalError: pass
            
            
# --- WRITES ---
def insert_auction(conn, auction_id, url):
    conn.execute("INSERT OR IGNORE INTO auctions (id, url) VALUES (?, ?)", (auction_id, url))
    conn.commit()

# NEW: Added title to update function
def update_auction_metadata(conn, auction_id, title, auctioneer, end_date):
    conn.execute("""
        UPDATE auctions 
        SET auction_title = ?, auctioneer = ?, end_date = ? 
        WHERE id = ?
    """, (title, auctioneer, end_date, auction_id))
    conn.commit()

def insert_auction_item(conn, auction_id, lot, current_bid, details: dict):
    conn.execute("""
        INSERT INTO auction_items (
            auction_id, lot, current_bid, title, brand, model,
            packaging, condition, functional, missing_parts, missing_parts_desc,
            damaged, damage_desc, item_notes, upc, asin, url, 
            suggested_msrp, scraped_category
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        auction_id, lot, current_bid,
        details.get('Title'), details.get('Brand'), details.get('Model'),
        details.get('Packaging'), details.get('Condition'), details.get('Functional'),
        details.get('Missing Parts'), details.get('Missing Parts Description'),
        details.get('Damaged'), details.get('Damage Description'),
        details.get('Notes'), details.get('UPC'), details.get('ASIN'), details.get('URL'),
        details.get('SuggestedMSRP', 0), details.get('Category')
    ))
    conn.commit()

def update_item_field(conn, item_id: int, field: str, value: Any):
    allowed = [
        'title', 'brand', 'model', 'packaging', 'condition', 'functional', 
        'missing_parts', 'missing_parts_desc', 'damaged', 'damage_desc', 
        'item_notes', 'upc', 'asin', 'is_watched', 'is_hidden',
        'sold_price', 'status', 'suggested_msrp', 'scraped_category'
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

# --- READS (Updated with Title) ---
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

def get_auctions(conn) -> pd.DataFrame:
    return get_active_auctions(conn)

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
            
            i.packaging, i.condition, i.functional, 
            i.missing_parts, i.missing_parts_desc,
            i.damaged, i.damage_desc, 
            i.item_notes, i.url,
            i.is_watched, i.is_hidden
            
        FROM auction_items i
        LEFT JOIN products p ON i.product_id = p.id
        WHERE i.auction_id = ?
    """, conn, params=(auction_id,))