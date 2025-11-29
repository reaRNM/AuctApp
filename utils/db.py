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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auctions (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE,
                scrape_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. PRODUCTS (Master Library - Updated with User's Exact Fields)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- Identity
                title TEXT, brand TEXT, model TEXT,
                upc TEXT UNIQUE, asin TEXT UNIQUE, category TEXT,
                
                -- Internal Pricing
                msrp REAL, avg_sold_price REAL, target_list_price REAL,
                shipping_cost_basis REAL,
                
                -- Logistics
                weight_lbs REAL, weight_oz REAL,
                length REAL, width REAL, height REAL,
                is_irregular BOOLEAN DEFAULT 0, ship_method TEXT,
                
                -- EBAY RESEARCH (Exact User List)
                ebay_sold_30d INTEGER,          -- 1a. # Sold Last Month
                ebay_sold_60d INTEGER,          -- 1b. # Sold Last 60 Days
                ebay_sold_90d INTEGER,          -- 1c. # Sold Last 90 Days
                ebay_num_sellers INTEGER,       -- 2. Number of Sellers
                ebay_avg_sold REAL,             -- 3. Avg Price Sold
                ebay_low_sold REAL,             -- 4. Lowest Price Sold
                ebay_high_sold REAL,            -- 5. Highest Price Sold
                ebay_avg_ship_sold REAL,        -- 6. Avg Shipping (Sold)
                ebay_free_ship_pct_sold REAL,   -- 7. % Free Shipping (Sold)
                ebay_ctr REAL,                  -- 8. Click Through Rate
                ebay_active_count INTEGER,      -- 9. Number of Current Listings
                ebay_avg_list REAL,             -- 10. Avg Listing Price
                ebay_low_list REAL,             -- 11. Lowest Listing Price
                ebay_high_list REAL,            -- 12. Highest Listing Price
                ebay_avg_ship_list REAL,        -- 13. Avg Shipping (Listing)
                ebay_free_ship_pct_list REAL,   -- 14. % Free Shipping (List)
                ebay_promoted_pct REAL,         -- 15. % Promoted Rate
                ebay_url TEXT,                  -- (Keep URL for reference)

                -- AMAZON RESEARCH (Exact User List)
                amazon_price REAL,              -- 1. Price
                amazon_stars REAL,              -- 2. Star Rating
                amazon_cat_rank TEXT,           -- 3. Ranking in Categories
                amazon_subcat_rank TEXT,        -- 4. Ranking in Subcategories
                amazon_sold_30d INTEGER,        -- 5. # Sold Last Month
                amazon_freq_returned BOOLEAN DEFAULT 0, -- 6. Frequently Returned
                amazon_url TEXT,                -- (Keep URL)
                
                notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

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
        
        cursor = conn.cursor()
        
        # Add new eBay columns
        prod_cols = [row[1] for row in cursor.execute("PRAGMA table_info(products)")]
        new_prod_cols = {
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
        
        item_cols = [row[1] for row in cursor.execute("PRAGMA table_info(auction_items)")]
        
        # Migrations
        migrations = {
            'sold_price': 'REAL DEFAULT 0',
            'status': "TEXT DEFAULT 'Active'",
            'suggested_msrp': 'REAL DEFAULT 0',
            'scraped_category': 'TEXT' # Add new migration
        }
        for col, dtype in migrations.items():
            if col not in item_cols:
                try: cursor.execute(f"ALTER TABLE auction_items ADD COLUMN {col} {dtype}")
                except sqlite3.OperationalError: pass

        prod_cols = [row[1] for row in cursor.execute("PRAGMA table_info(products)")]
        new_prod_cols = {
            'ebay_url': 'TEXT', 'ebay_active_low': 'REAL', 'ebay_active_high': 'REAL',
            'ebay_sold_low': 'REAL', 'ebay_sold_high': 'REAL', 'ebay_sell_through': 'REAL',
            'amazon_url': 'TEXT', 'amazon_new_price': 'REAL', 'amazon_used_price': 'REAL',
            'amazon_sales_rank': 'INTEGER'
        }
        for col, dtype in new_prod_cols.items():
            if col not in prod_cols:
                try: cursor.execute(f"ALTER TABLE products ADD COLUMN {col} {dtype}")
                except sqlite3.OperationalError: pass

# ... (insert_auction remains same) ...
def insert_auction(conn, auction_id, url):
    conn.execute("INSERT OR IGNORE INTO auctions (id, url) VALUES (?, ?)", (auction_id, url))
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
        details.get('SuggestedMSRP', 0),
        details.get('Category') # New Field
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

# ... (Getters remain largely same, just updated column list) ...
def get_active_auctions(conn) -> pd.DataFrame:
    return pd.read_sql_query("""
        SELECT a.id, a.url, a.scrape_date, COUNT(i.id) AS item_count
        FROM auctions a
        LEFT JOIN auction_items i ON i.auction_id = a.id
        GROUP BY a.id, a.url, a.scrape_date
        HAVING SUM(CASE WHEN i.sold_price > 0 THEN 1 ELSE 0 END) = 0
        ORDER BY a.scrape_date DESC
    """, conn)

def get_closed_auctions(conn) -> pd.DataFrame:
    return pd.read_sql_query("""
        SELECT a.id, a.url, a.scrape_date, COUNT(i.id) AS item_count
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
            i.scraped_category, -- NEW
            
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