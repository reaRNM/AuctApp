# Home.py
import streamlit as st
import pandas as pd
import sys
import os
import time

# Connect to utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.db import create_connection
# Import Scraper
from scraper import scrape_auction

st.set_page_config(page_title="AuctApp Dashboard", layout="wide", page_icon="📊")
st.title("📊 Reseller Command Center")

# Initialize connection variable outside try block
conn = None

try:
    conn = create_connection()
    cursor = conn.cursor()

    # --- 1. METRICS ---
    c1, c2, c3, c4 = st.columns(4)
    cursor.execute("SELECT COUNT(*) FROM products")
    c1.metric("📦 Master Products", cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM auctions")
    c2.metric("🔨 Auctions Tracked", cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM auction_items WHERE is_watched = 1 AND status = 'Active'")
    c3.metric("⭐ Active Watches", cursor.fetchone()[0])

    cursor.execute("SELECT SUM(sold_price) FROM auction_items WHERE status = 'Sold'")
    res = cursor.fetchone()[0]
    c4.metric("💰 Total Sales Tracked", f"${res if res else 0:,.2f}")

    st.divider()

    # --- 2. NEW AUCTION SCRAPER ---
    st.subheader("🕷️ Scrape New Auction")
    with st.form("scrape_form"):
        col_input, col_btn = st.columns([4, 1])
        with col_input:
            new_url = st.text_input("Auction URL", placeholder="https://hibid.com/catalog/...")
        with col_btn:
            st.write("") # Spacing
            st.write("") 
            scrape_submitted = st.form_submit_button("🚀 Start Scraping", use_container_width=True)

        if scrape_submitted and new_url:
            # 1. Close current UI connection to release DB lock
            conn.close()
            conn = None 

            with st.status("Scraping Auction...", expanded=True) as status:
                st.write("Initializing scraper...")
                try:
                    # 2. Run the heavy scraper (which opens its own connection)
                    scrape_auction(new_url)
                    status.update(label="Scrape Complete!", state="complete", expanded=False)
                    st.success("Auction scraped successfully! Go to 'Active Viewer' to see it.")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    status.update(label="Scrape Failed", state="error")
                    st.error(f"Error: {e}")
                    # Re-open connection if we failed and are staying on page
                    conn = create_connection() 

    st.divider()

    # --- 3. ACTIVE OPPORTUNITIES ---
    # Only run this if connection is still open (wasn't closed for scraping)
    if conn:
        st.subheader("🔥 Top Active Opportunities")
        query_opps = """
            SELECT 
                i.lot, COALESCE(p.title, i.title) as title, i.current_bid, p.target_list_price,
                (p.target_list_price - i.current_bid - p.shipping_cost_basis) as est_profit
            FROM auction_items i
            JOIN products p ON i.product_id = p.id
            WHERE i.status = 'Active' AND p.target_list_price > 0
            ORDER BY est_profit DESC LIMIT 10
        """
        df_opps = pd.read_sql_query(query_opps, conn)

        if not df_opps.empty:
            df_opps['est_profit'] = df_opps['est_profit'].astype(float).apply(lambda x: f"${x:,.2f}")
            df_opps['current_bid'] = df_opps['current_bid'].astype(float).apply(lambda x: f"${x:,.2f}")
            df_opps['target_list_price'] = df_opps['target_list_price'].astype(float).apply(lambda x: f"${x:,.2f}")
            st.dataframe(df_opps, hide_index=True, use_container_width=True)
        else:
            st.info("No linked active items with profit data found.")

    # --- 4. NAV ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1: st.page_link("pages/1_Active_Viewer.py", label="Go to Active Auctions", icon="🔭", use_container_width=True)
    with c2: st.page_link("pages/2_Product_Library.py", label="Manage Product Library", icon="📚", use_container_width=True)

finally:
    # Ensure connection is closed even if an error occurs in the UI rendering
    if conn:
        try:
            conn.close()
        except Exception:
            pass