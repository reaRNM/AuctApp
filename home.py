# home.py
import streamlit as st
import pandas as pd
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.db import create_connection
from scraper import scrape_auction
# FULL IMPORT OF CONSTANTS
from utils.parse import (
    PAGE_ACTIVE, PAGE_LIBRARY, 
    KEY_DB_TARGET, KEY_SHIP_COST, KEY_CURRENT_BID, KEY_EST_PROFIT,
    COL_LOT, COL_TITLE, COL_CUR_BID, COL_TARGET, COL_EST_PROFIT
)

st.set_page_config(page_title="AuctApp Dashboard", layout="wide", page_icon="📊")
st.title("📊 Reseller Command Center")

# Initialize connection variable
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
            # Close UI connection before scraping to prevent locks
            conn.close()
            conn = None 

            with st.status("Scraping Auction...", expanded=True) as status:
                st.write("Initializing scraper...")
                try:
                    scrape_auction(new_url)
                    status.update(label="Scrape Complete!", state="complete", expanded=False)
                    st.success("Auction scraped successfully! Go to 'Active Viewer' to see it.")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    status.update(label="Scrape Failed", state="error")
                    st.error(f"Error: {e}")
                    conn = create_connection() # Re-open if failed

    st.divider()

    # --- 3. ACTIVE OPPORTUNITIES ---
    if conn:
        st.subheader("🔥 Top Active Opportunities")
        
        # Query Logic: Profit = Target - Bid - Shipping - (Target * 0.15)
        query_opps = f"""
            SELECT 
                i.lot, 
                COALESCE(p.title, i.title) as title, 
                i.{KEY_CURRENT_BID}, 
                p.{KEY_DB_TARGET},
                p.{KEY_SHIP_COST},
                (p.{KEY_DB_TARGET} - i.{KEY_CURRENT_BID} - IFNULL(p.{KEY_SHIP_COST}, 0) - (p.{KEY_DB_TARGET} * 0.15)) as {KEY_EST_PROFIT}
            FROM auction_items i
            JOIN products p ON i.product_id = p.id
            WHERE i.status = 'Active' AND p.{KEY_DB_TARGET} > 0
            ORDER BY {KEY_EST_PROFIT} DESC
            LIMIT 10
        """
        df_opps = pd.read_sql_query(query_opps, conn)

        if not df_opps.empty:
            df_display = df_opps.copy()
            df_display[KEY_EST_PROFIT] = df_display[KEY_EST_PROFIT].astype(float).apply(lambda x: f"${x:,.2f}")
            df_display[KEY_CURRENT_BID] = df_display[KEY_CURRENT_BID].astype(float).apply(lambda x: f"${x:,.2f}")
            df_display[KEY_DB_TARGET] = df_display[KEY_DB_TARGET].astype(float).apply(lambda x: f"${x:,.2f}")
            
            # Use Constants for Renaming
            df_display = df_display.rename(columns={
                "lot": COL_LOT,
                "title": COL_TITLE,
                KEY_CURRENT_BID: COL_CUR_BID,
                KEY_DB_TARGET: COL_TARGET,
                KEY_EST_PROFIT: COL_EST_PROFIT
            })

            # Chart Data
            df_chart = df_opps.copy()
            df_chart = df_chart.rename(columns={
                KEY_EST_PROFIT: COL_EST_PROFIT,
                KEY_CURRENT_BID: COL_CUR_BID
            })
            c_table, c_chart = st.columns([6, 4])
            
            with c_table:
                # Use Constants for Column Selection
                st.dataframe(
                    df_display[[COL_LOT, COL_TITLE, COL_CUR_BID, COL_TARGET, COL_EST_PROFIT]], 
                    hide_index=True, 
                    use_container_width=True
                )
            
            with c_chart:
                st.caption("Profit Potential vs Current Bid Cost")
                # Using 'lot' directly as it's the raw column name before rename in df_chart, or we can use "lot" if SQL returns it lower case.
                # Since df_chart only renamed profit and bid, 'lot' is still 'lot'.
                st.bar_chart(
                    df_chart.set_index("lot")[[COL_EST_PROFIT, COL_CUR_BID]],
                    stack=False
                )
        else:
            st.info("No active items with 'Target Price' set yet. Go to Research Station to value items!")

    # --- 4. NAV ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1: st.page_link(PAGE_ACTIVE, label="Go to Active Auctions", icon="🔭", use_container_width=True)
    with c2: st.page_link(PAGE_LIBRARY, label="Manage Product Library", icon="📚", use_container_width=True)

finally:
    if conn:
        try:
            conn.close()
        except Exception:
            pass