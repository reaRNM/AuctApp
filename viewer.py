# viewer.py
import streamlit as st
import pandas as pd
import sqlite3

from utils.db import create_connection, get_active_auctions, get_auction_items, update_item_field, update_item_status
from utils.parse import classify_risk
from utils.inventory import auto_link_products
from components.grid import render_grid
from components.research import render_research_station

# === CONSTANTS & MAPPING ===
COL_LOT = "Lot"
COL_BID = "Bid"
COL_TITLE = "Title"
COL_BRAND = "Brand"
COL_MODEL = "Model"
COL_WATCH = "Watch"
COL_RISK = "Risk"
COL_PACKAGING = "Packaging"
COL_CONDITION = "Condition"
COL_FUNCTIONAL = "Functional"
COL_MISSING = "Missing Parts"
COL_MISSING_DESC = "Missing Parts Desc"
COL_DAMAGED = "Damaged"
COL_DAMAGE_DESC = "Damaged Desc"
COL_NOTES = "Notes"
COL_UPC = "UPC"
COL_ASIN = "ASIN"
COL_URL = "URL"

# Explicit mapping for safer updates
DB_COL_MAP = {
    COL_TITLE: 'title', COL_BRAND: 'brand', COL_MODEL: 'model',
    COL_UPC: 'upc', COL_ASIN: 'asin',
    COL_PACKAGING: 'packaging', COL_CONDITION: 'condition', 
    COL_FUNCTIONAL: 'functional', COL_MISSING: 'missing_parts',
    COL_MISSING_DESC: 'missing_parts_desc', COL_DAMAGED: 'damaged',
    COL_DAMAGE_DESC: 'damage_desc', COL_NOTES: 'item_notes'
}

st.set_page_config(page_title="Active Viewer", layout="wide")
st.title("🔭 Active Auction Viewer")

# Dashboard Nav
col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    st.page_link("pages/1_Product_Library.py", label="📚 Go to Product Library", icon="📚", use_container_width=True)
with col_nav2:
    st.page_link("pages/2_Auction_History.py", label="🏆 Go to Auction History", icon="🏆", use_container_width=True)
st.divider()

# === SAFE DB CONNECTION ===
try:
    conn = create_connection()
    auction_list = get_active_auctions(conn)

    if auction_list.empty:
        st.warning("No active auctions found.")
        st.stop()

    # --- SIDEBAR ---
    st.sidebar.header("Auction Selection")
    auction_options = {f"{r['id']} – {r['url']} ({r['item_count']})": r["id"] for _, r in auction_list.iterrows()}
    selected = st.sidebar.selectbox("Select Auction", list(auction_options.keys()))
    auction_id = auction_options[selected]

    st.sidebar.divider()
    st.sidebar.header("Inventory Actions")
    show_hidden = st.sidebar.checkbox("Show Crossed Out Items", value=False)
    hide_high = st.sidebar.checkbox("Hide High Risk", value=False)
    hide_med = st.sidebar.checkbox("Hide Medium Risk", value=False)
    show_no_bids = st.sidebar.checkbox("Show 'No Bids' Only", value=False)

    # --- DATA ---
    df = get_auction_items(conn, auction_id)
    if df.empty: st.warning("No items found."); st.stop()

    # Process
    df[COL_RISK] = df.apply(classify_risk, axis=1)
    if "current_bid" in df.columns:
        df["current_bid"] = pd.to_numeric(df["current_bid"], errors="coerce").fillna(0.00)
        df[COL_BID] = df["current_bid"].apply(lambda x: f"${x:,.2f}")
    df[COL_WATCH] = df["is_watched"].apply(lambda x: True if x == 1 else False)

    rename_map = {
        "lot_number": COL_LOT, "title": COL_TITLE, "brand": COL_BRAND, "model": COL_MODEL,
        "packaging": COL_PACKAGING, "condition": COL_CONDITION, "functional": COL_FUNCTIONAL,
        "missing_parts": COL_MISSING, "missing_parts_desc": COL_MISSING_DESC,
        "damaged": COL_DAMAGED, "damage_desc": COL_DAMAGE_DESC,
        "item_notes": COL_NOTES, "upc": COL_UPC, "asin": COL_ASIN, "url": COL_URL
    }
    df = df.rename(columns=rename_map)

    if not show_hidden: df = df[df["is_hidden"] == 0]
    if hide_high: df = df[df[COL_RISK] != "HIGH RISK"]
    if hide_med: df = df[df[COL_RISK] != "MEDIUM RISK"]
    if show_no_bids: df = df[df[COL_RISK] == "NO BIDS"]

    desired_cols = [
        COL_RISK, COL_WATCH, COL_LOT, COL_BID, 
        COL_TITLE, COL_BRAND, COL_MODEL, 
        COL_PACKAGING, COL_CONDITION, COL_FUNCTIONAL, 
        COL_MISSING, COL_MISSING_DESC, 
        COL_DAMAGED, COL_DAMAGE_DESC, 
        COL_NOTES, COL_UPC, COL_ASIN, COL_URL, 
        "id", "is_hidden", "current_bid", "product_id"
    ]
    df_display = df[[c for c in desired_cols if c in df.columns]].copy()

    # --- RENDER GRID ---
    grid_result = render_grid(df_display)
    selected_rows = grid_result["selected_rows"]
    updated_data = grid_result["data"]

    # --- ACTIONS ---
    st.sidebar.divider()
    if st.sidebar.button("❌ Cross Out Selected"):
        if not selected_rows: st.sidebar.warning("No items selected.")
        else:
            try:
                with conn: # Transaction
                    for row in selected_rows:
                        if row.get("id"): update_item_status(conn, row.get("id"), "is_hidden", 1)
                st.sidebar.success("Items crossed out.")
                st.rerun()
            except Exception as e:
                st.error(f"Error updating items: {e}")

    if show_hidden and st.sidebar.button("↺ Restore Selected") and selected_rows:
        try:
            with conn: # Transaction
                for row in selected_rows:
                    if row.get("id"): update_item_status(conn, row.get("id"), "is_hidden", 0)
            st.sidebar.success("Items restored.")
            st.rerun()
        except Exception as e:
            st.error(f"Error restoring items: {e}")

    st.sidebar.divider()
    if st.sidebar.button("🔗 Auto-Match Products"):
        with st.spinner("Linking..."): count = auto_link_products(conn, auction_id)
        st.sidebar.success(f"Linked {count} items!"); st.rerun()

    # --- SAVE ---
    st.markdown("---")
    col_save, col_dl = st.columns([2, 8])
    with col_save:
        if st.button("💾 Save Data Edits"):
            if updated_data is not None and not updated_data.empty:
                progress = st.progress(0)
                try:
                    # Using 'with conn:' wraps this loop in a SQL transaction
                    # If one fails, they all rollback
                    with conn: 
                        for i, (index, row) in enumerate(updated_data.iterrows()):
                            item_id = row.get("id")
                            if not item_id: continue
                            
                            # Update Watch
                            update_item_status(conn, item_id, "is_watched", 1 if row.get(COL_WATCH) else 0)
                            
                            # Update Text Fields using Safe Map
                            for disp_col, db_col in DB_COL_MAP.items():
                                val = row.get(disp_col)
                                if pd.notna(val):
                                    update_item_field(conn, item_id, db_col, val)
                            
                            progress.progress((i + 1) / len(updated_data))
                    st.success("Saved successfully!")
                    st.rerun()
                except sqlite3.Error as e:
                    st.error(f"Database Error during save: {e}")

    with col_dl:
        try:
            csv_data = df_display.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv_data, f"auction_{auction_id}.csv", "text/csv")
        except Exception: pass

    # --- RESEARCH STATION ---
    render_research_station(conn, selected_rows)

finally:
    if 'conn' in locals():
        conn.close()