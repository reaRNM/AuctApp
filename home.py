# Home.py
import streamlit as st
import pandas as pd
import sqlite3
import sys
import os

# Connect to utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.db import create_connection

st.set_page_config(page_title="AuctApp Dashboard", layout="wide", page_icon="📊")

st.title("📊 Reseller Command Center")

conn = create_connection()
cursor = conn.cursor()

# --- 1. HIGH LEVEL METRICS ---
c1, c2, c3, c4 = st.columns(4)

# Total Master Products
# FIX: Use cursor.execute for scalar values (Returns standard Python int, satisfying Pylance)
cursor.execute("SELECT COUNT(*) FROM products")
total_products = cursor.fetchone()[0]
c1.metric("📦 Master Products", total_products)

# Active Auctions
cursor.execute("SELECT COUNT(*) FROM auctions")
active_auctions = cursor.fetchone()[0]
c2.metric("🔨 Auctions Tracked", active_auctions)

# Items Watched (Active)
cursor.execute("SELECT COUNT(*) FROM auction_items WHERE is_watched = 1 AND status = 'Active'")
watched_items = cursor.fetchone()[0]
c3.metric("⭐ Active Watches", watched_items)

# Total Sold Value (History)
cursor.execute("SELECT SUM(sold_price) FROM auction_items WHERE status = 'Sold'")
result = cursor.fetchone()[0]
total_sold = float(result) if result else 0.0
c4.metric("💰 Total Sales Tracked", f"${total_sold:,.2f}")

st.divider()

# --- 2. ACTIVE OPPORTUNITIES ---
st.subheader("🔥 Top Active Opportunities (High Profit Potential)")

# Logic: Find Active items linked to products where (Target Price - Current Bid) is high
query_opps = """
    SELECT 
        i.lot, 
        COALESCE(p.title, i.title) as title,
        i.current_bid,
        p.target_list_price,
        (p.target_list_price - i.current_bid - p.shipping_cost_basis) as est_profit
    FROM auction_items i
    JOIN products p ON i.product_id = p.id
    WHERE i.status = 'Active' 
      AND p.target_list_price > 0
    ORDER BY est_profit DESC
    LIMIT 10
"""
df_opps = pd.read_sql_query(query_opps, conn)

if not df_opps.empty:
    # Formatting for display
    # We cast to float before formatting to be safe
    df_opps['est_profit'] = df_opps['est_profit'].astype(float).apply(lambda x: f"${x:,.2f}")
    df_opps['current_bid'] = df_opps['current_bid'].astype(float).apply(lambda x: f"${x:,.2f}")
    df_opps['target_list_price'] = df_opps['target_list_price'].astype(float).apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(
        df_opps, 
        column_config={
            "lot": "Lot",
            "title": "Item",
            "current_bid": "Current Bid",
            "target_list_price": "Target",
            "est_profit": "Est. Profit"
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No linked active items with profit data found yet.")

# --- 3. QUICK ACTIONS ---
st.divider()
st.subheader("⚡ Quick Actions")
c1, c2 = st.columns(2)
with c1:
    st.page_link("pages/1_Active_Viewer.py", label="Go to Active Auctions", icon="🔭", use_container_width=True)
with c2:
    st.page_link("pages/2_Product_Library.py", label="Manage Product Library", icon="📚", use_container_width=True)

conn.close()