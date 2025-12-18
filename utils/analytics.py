# utils/analytics.py
import sqlite3
import pandas as pd
from utils.db import create_connection
# IMPORT CONSTANTS
from utils.parse import COL_CAT, COL_TOTAL_COST, COL_PROFIT_REALIZED

def get_inventory_stats(conn: sqlite3.Connection):
    query_invest = "SELECT SUM(total_cost) FROM inventory_ledger"
    total_invest = conn.execute(query_invest).fetchone()[0] or 0.0

    query_revenue = "SELECT SUM(sold_price) FROM inventory_ledger WHERE status = 'Sold'"
    total_revenue = conn.execute(query_revenue).fetchone()[0] or 0.0

    query_cogs = "SELECT SUM(total_cost) FROM inventory_ledger WHERE status = 'Sold'"
    cogs = conn.execute(query_cogs).fetchone()[0] or 0.0

    gross_profit = total_revenue - cogs
    roi = (gross_profit / cogs * 100) if cogs > 0 else 0.0
    query_potential = "SELECT SUM(listing_price) FROM inventory_ledger WHERE status = 'Listed'"
    potential_revenue = conn.execute(query_potential).fetchone()[0] or 0.0

    return {
        "total_investment": total_invest,
        "total_revenue": total_revenue,
        "gross_profit": gross_profit,
        "roi": roi,
        "potential_revenue": potential_revenue
    }

def get_sales_over_time(conn: sqlite3.Connection, period='Month'):
    date_format = "%Y-%m" if period == 'Month' else "%Y-%W"
    query = f"""
        SELECT 
            strftime('{date_format}', sold_date) as period, 
            SUM(sold_price) as revenue,
            SUM(sold_price - total_cost) as profit,
            COUNT(id) as items_sold
        FROM inventory_ledger
        WHERE status = 'Sold' AND sold_date IS NOT NULL
        GROUP BY period
        ORDER BY period ASC
    """
    return pd.read_sql_query(query, conn)

def get_category_breakdown(conn: sqlite3.Connection):
    # Returns DF with standardized columns
    query = f"""
        SELECT 
            p.category as "{COL_CAT}",
            COUNT(l.id) as items_count,
            SUM(l.total_cost) as "{COL_TOTAL_COST}",
            SUM(CASE WHEN l.status='Sold' THEN l.sold_price - l.total_cost ELSE 0 END) as "{COL_PROFIT_REALIZED}"
        FROM inventory_ledger l
        LEFT JOIN products p ON l.product_id = p.id
        WHERE p.category IS NOT NULL
        GROUP BY p.category
        ORDER BY "{COL_PROFIT_REALIZED}" DESC
    """
    return pd.read_sql_query(query, conn)

def get_market_trends(conn: sqlite3.Connection, product_id: int):
    query = """
        SELECT sold_date, sold_price, auction_source
        FROM product_price_history
        WHERE product_id = ?
        ORDER BY sold_date ASC
    """
    return pd.read_sql_query(query, conn, params=(product_id,))