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
        # 1. AUCTIONS
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auctions (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE,
                scrape_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. PRODUCTS
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, brand TEXT, model TEXT,
                upc TEXT UNIQUE, asin TEXT UNIQUE,
                category TEXT,
                msrp REAL, avg_sold_price REAL, target_list_price REAL,
                shipping_cost_basis REAL,
                weight_lbs REAL, weight_oz REAL,
                length REAL, width REAL, height REAL,
                is_irregular BOOLEAN DEFAULT 0, ship_method TEXT,
                notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. AUCTION ITEMS
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auction_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id INTEGER NOT NULL,
                product_id INTEGER, 
                lot TEXT,
                current_bid REAL DEFAULT 0,
                sold_price REAL DEFAULT 0,
                status TEXT DEFAULT 'Active', 
                
                title TEXT, brand TEXT, model TEXT,
                packaging TEXT, condition TEXT, functional TEXT,
                missing_parts TEXT, missing_parts_desc TEXT,
                damaged TEXT, damage_desc TEXT,
                item_notes TEXT, upc TEXT, asin TEXT, url TEXT,
                
                suggested_msrp REAL DEFAULT 0, -- NEW COLUMN
                
                is_watched INTEGER DEFAULT 0,
                is_hidden INTEGER DEFAULT 0,
                FOREIGN KEY (auction_id) REFERENCES auctions(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
            )
        """)
        
        # --- MIGRATIONS ---
        # Defined INSIDE the 'with conn' block so it's safe
        cursor = conn.cursor()
        existing_cols = [row[1] for row in cursor.execute("PRAGMA table_info(auction_items)")]
        
        if 'sold_price' not in existing_cols:
            try: cursor.execute("ALTER TABLE auction_items ADD COLUMN sold_price REAL DEFAULT 0")
            except sqlite3.OperationalError: pass
        
        if 'status' not in existing_cols:
            try: cursor.execute("ALTER TABLE auction_items ADD COLUMN status TEXT DEFAULT 'Active'")
            except sqlite3.OperationalError: pass

        if 'suggested_msrp' not in existing_cols:
            try: cursor.execute("ALTER TABLE auction_items ADD COLUMN suggested_msrp REAL DEFAULT 0")
            except sqlite3.OperationalError: pass
# ----------------------------------------------------------------------
# WRITES
# ----------------------------------------------------------------------
def insert_auction(conn, auction_id, url):
    conn.execute("INSERT OR IGNORE INTO auctions (id, url) VALUES (?, ?)", (auction_id, url))
    conn.commit()

def insert_auction_item(conn, auction_id, lot, current_bid, details: dict):
    # Updated to include suggested_msrp
    conn.execute("""
        INSERT INTO auction_items (
            auction_id, lot, current_bid, title, brand, model,
            packaging, condition, functional, missing_parts, missing_parts_desc,
            damaged, damage_desc, item_notes, upc, asin, url, suggested_msrp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        auction_id, lot, current_bid,
        details.get('Title'), details.get('Brand'), details.get('Model'),
        details.get('Packaging'), details.get('Condition'), details.get('Functional'),
        details.get('Missing Parts'), details.get('Missing Parts Description'),
        details.get('Damaged'), details.get('Damage Description'),
        details.get('Notes'), details.get('UPC'), details.get('ASIN'), details.get('URL'),
        details.get('SuggestedMSRP', 0) # NEW
    ))
    conn.commit()

def update_item_field(conn, item_id: int, field: str, value: Any):
    allowed = [
        'title', 'brand', 'model', 'packaging', 'condition', 'functional', 
        'missing_parts', 'missing_parts_desc', 'damaged', 'damage_desc', 
        'item_notes', 'upc', 'asin', 'is_watched', 'is_hidden',
        'sold_price', 'status'
    ]
    if field.lower() not in allowed: return
    conn.execute(f"UPDATE auction_items SET {field} = ? WHERE id = ?", (value, item_id))
    conn.commit()

def update_item_status(conn, item_id: int, field: str, value: int):
    update_item_field(conn, item_id, field, value)

def update_final_price(conn, auction_id: int, lot_number: str, sold_price: float, status: str):
    """Updates an existing item with its final auction result."""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE auction_items 
        SET sold_price = ?, status = ?
        WHERE auction_id = ? AND lot = ?
    """, (sold_price, status, auction_id, lot_number))
    conn.commit()

# ----------------------------------------------------------------------
# READS
# ----------------------------------------------------------------------
def get_active_auctions(conn) -> pd.DataFrame:
    """Returns auctions where NO items have a 'sold_price' > 0 yet."""
    return pd.read_sql_query("""
        SELECT a.id, a.url, a.scrape_date, COUNT(i.id) AS item_count
        FROM auctions a
        LEFT JOIN auction_items i ON i.auction_id = a.id
        GROUP BY a.id, a.url, a.scrape_date
        HAVING SUM(CASE WHEN i.sold_price > 0 THEN 1 ELSE 0 END) = 0
        ORDER BY a.scrape_date DESC
    """, conn)

def get_closed_auctions(conn) -> pd.DataFrame:
    """Returns auctions where AT LEAST ONE item has a 'sold_price' > 0."""
    return pd.read_sql_query("""
        SELECT a.id, a.url, a.scrape_date, COUNT(i.id) AS item_count
        FROM auctions a
        LEFT JOIN auction_items i ON i.auction_id = a.id
        GROUP BY a.id, a.url, a.scrape_date
        HAVING SUM(CASE WHEN i.sold_price > 0 THEN 1 ELSE 0 END) > 0
        ORDER BY a.scrape_date DESC
    """, conn)

# Legacy wrapper
def get_auctions(conn) -> pd.DataFrame:
    return get_active_auctions(conn)

def get_auction_items(conn, auction_id: int) -> pd.DataFrame:
    return pd.read_sql_query("""
        SELECT
            i.id, i.auction_id, i.product_id,
            i.lot as lot_number, 
            i.current_bid, 
            i.sold_price, 
            i.status,
            i.suggested_msrp,
            
            COALESCE(p.title, i.title) as title,
            COALESCE(p.brand, i.brand) as brand,
            COALESCE(p.model, i.model) as model,
            COALESCE(p.upc, i.upc) as upc,
            COALESCE(p.asin, i.asin) as asin,
            
            i.packaging, i.condition, i.functional, 
            i.missing_parts, i.missing_parts_desc,
            i.damaged, i.damage_desc, 
            i.item_notes, i.url,
            i.is_watched, i.is_hidden
            
        FROM auction_items i
        LEFT JOIN products p ON i.product_id = p.id
        WHERE i.auction_id = ?
    """, conn, params=(auction_id,))