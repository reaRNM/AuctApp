# utils/analytics.py
import sqlite3
import pandas as pd

def recalculate_product_stats(conn: sqlite3.Connection, product_id: int) -> bool:
    """
    Analyzes all sold history for a Master Product and updates its stats.
    """
    if not product_id: return False
    
    # 1. Get all "Sold" items linked to this product
    query = """
        SELECT sold_price 
        FROM auction_items 
        WHERE product_id = ? 
          AND sold_price > 0 
          AND status = 'Sold'
    """
    df = pd.read_sql_query(query, conn, params=(product_id,))
    
    if df.empty:
        return False

    # 2. Calculate Stats
    avg_price = df['sold_price'].mean()
    sold_count = len(df)
    
    # 3. Update Master Record
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products 
        SET avg_sold_price = ?
        WHERE id = ?
    """, (avg_price, product_id))
    
    conn.commit()
    print(f"🧠 Updated Product #{product_id}: Avg ${avg_price:.2f} ({sold_count} sales)")
    return True

def update_all_product_stats(conn: sqlite3.Connection):
    """Runs the analyzer on EVERY product in the library."""
    print("🧠 Starting Analytics Run...")
    
    # Get all unique product IDs that have sold items
    query = """
        SELECT DISTINCT product_id 
        FROM auction_items 
        WHERE product_id IS NOT NULL 
          AND sold_price > 0
    """
    product_ids = pd.read_sql_query(query, conn)['product_id'].tolist()
    
    print(f"Analyzing {len(product_ids)} products...")
    for p_id in product_ids:
        recalculate_product_stats(conn, p_id)
    
    print("🧠 Analytics Run Complete.")