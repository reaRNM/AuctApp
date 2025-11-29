# pages/1_Active_Viewer.py
import streamlit as st
import pandas as pd
import sys
import os

# === PATH SETUP ===
# Allow imports from parent directory (since this is now in /pages)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import create_connection, get_auctions, get_auction_items, update_item_field, update_item_status
from utils.parse import classify_risk
from utils.inventory import auto_link_products
from components.grid import render_grid
from components.research import render_research_station

# === CONSTANTS ===
COL_SELECT = "Select"
COL_ACTIONS = "Actions"
COL_LOT = "Lot"
COL_BID = "Bid"
COL_PROFIT = "Est. Profit"
COL_BID_PCT = "Bid %"
COL_MSRP_STAT = "MSRP Status"
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

# Safe Column Map for Updates
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

# === DASHBOARD NAVIGATION (FIXED LINKS) ===
col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    # FIXED: Points to 2_Product_Library.py
    st.page_link("pages/2_Product_Library.py", label="📚 Go to Product Library", icon="📚", use_container_width=True)
with col_nav2:
    # FIXED: Points to 3_Auction_History.py
    st.page_link("pages/3_Auction_History.py", label="🏆 Go to Auction History", icon="🏆", use_container_width=True)

st.divider()

# === CONNECT DB ===
try:
    conn = create_connection()
    auction_list = get_auctions(conn)

    if auction_list.empty:
        st.warning("No auctions found.")
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
    if df.empty:
        st.warning("No items found.")
        st.stop()

    # === CALCULATIONS ===
    df[COL_RISK] = df.apply(classify_risk, axis=1)

    df["current_bid"] = pd.to_numeric(df["current_bid"], errors="coerce").fillna(0.00)
    df["suggested_msrp"] = pd.to_numeric(df["suggested_msrp"], errors="coerce").fillna(0.00)
    df["master_msrp"] = pd.to_numeric(df["master_msrp"], errors="coerce").fillna(0.00)
    df["master_target_price"] = pd.to_numeric(df["master_target_price"], errors="coerce").fillna(0.00)

    # Determine "Working MSRP"
    df["working_msrp"] = df["master_msrp"]
    df.loc[df["working_msrp"] == 0, "working_msrp"] = df["suggested_msrp"]

    # MSRP Status
    def determine_msrp_status(row):
        if row["product_id"] and row["master_msrp"] > 0:
            return "✅ Linked"
        if row["suggested_msrp"] > 0:
            return "⚠️ Scraped"
        return "❌ Missing"

    df[COL_MSRP_STAT] = df.apply(determine_msrp_status, axis=1)

    # Bid %
    df[COL_BID_PCT] = df.apply(
        lambda x: f"{(x['current_bid'] / x['working_msrp']) * 100:.0f}%" 
        if x['working_msrp'] > 0 else "-", axis=1
    )

    # Profit
    df["profit_val"] = df.apply(
        lambda x: (x['master_target_price'] if x['master_target_price'] > 0 else x['working_msrp'] * 0.5) 
        - x['current_bid'], axis=1
    )
    df[COL_PROFIT] = df["profit_val"].apply(lambda x: f"${x:,.2f}")
    df[COL_BID] = df["current_bid"].apply(lambda x: f"${x:,.2f}")

    df[COL_WATCH] = df["is_watched"].apply(lambda x: True if x == 1 else False)
    df[COL_SELECT] = False 
    df[COL_ACTIONS] = ""

    # Rename
    rename_map = {
        "lot_number": COL_LOT, "title": COL_TITLE, "brand": COL_BRAND, "model": COL_MODEL,
        "packaging": COL_PACKAGING, "condition": COL_CONDITION, "functional": COL_FUNCTIONAL,
        "missing_parts": COL_MISSING, "missing_parts_desc": COL_MISSING_DESC,
        "damaged": COL_DAMAGED, "damage_desc": COL_DAMAGE_DESC,
        "item_notes": COL_NOTES, "upc": COL_UPC, "asin": COL_ASIN, "url": COL_URL,
        "suggested_msrp": "Scraped MSRP" # Rename for consistency
    }
    df = df.rename(columns=rename_map)

    # Filters
    if not show_hidden: df = df[df["is_hidden"] == 0]
    if hide_high: df = df[df[COL_RISK] != "HIGH RISK"]
    if hide_med: df = df[df[COL_RISK] != "MEDIUM RISK"]
    if show_no_bids: df = df[df[COL_RISK] == "NO BIDS"]

    # Select Cols
    desired_cols = [
        COL_SELECT, COL_ACTIONS, COL_RISK, COL_WATCH,
        COL_LOT, COL_PROFIT, COL_BID, COL_BID_PCT,
        COL_TITLE, COL_BRAND, COL_MODEL, 
        COL_PACKAGING, COL_CONDITION, COL_FUNCTIONAL, 
        COL_MISSING, COL_MISSING_DESC, 
        COL_DAMAGED, COL_DAMAGE_DESC, 
        COL_NOTES, COL_UPC, COL_ASIN, COL_URL, 
        "id", "is_hidden", "current_bid", "product_id", 
        "master_msrp", "master_target_price", "profit_val",
        "Scraped MSRP" # Needed for research logic
    ]
    # Ensure cols exist
    final_cols = [c for c in desired_cols if c in df.columns]
    df_display = df[final_cols].copy()

    # --- RENDER GRID ---
    grid_result = render_grid(df_display, grid_key=str(auction_id))
    selected_rows = grid_result["selected_rows"]
    updated_data = grid_result["data"]

    # --- SIDEBAR ACTIONS ---
    st.sidebar.divider()

    # Bulk Edit
    if len(selected_rows) > 1:
        st.sidebar.subheader(f"✏️ Bulk Edit ({len(selected_rows)} Items)")
        with st.sidebar.form("bulk_edit_form"):
            st.caption("Update all selected items at once.")
            b_title = st.text_input("Title")
            b_brand = st.text_input("Brand")
            b_model = st.text_input("Model")
            c1, c2 = st.columns(2)
            with c1: b_upc = st.text_input("UPC")
            with c2: b_asin = st.text_input("ASIN")
            
            if st.form_submit_button("Apply to Selected", use_container_width=True):
                progress = st.sidebar.progress(0)
                for i, row in enumerate(selected_rows):
                    item_id = row.get("id")
                    if not item_id: continue
                    if b_title: update_item_field(conn, item_id, "title", b_title)
                    if b_brand: update_item_field(conn, item_id, "brand", b_brand)
                    if b_model: update_item_field(conn, item_id, "model", b_model)
                    if b_upc: update_item_field(conn, item_id, "upc", b_upc)
                    if b_asin: update_item_field(conn, item_id, "asin", b_asin)
                    progress.progress((i + 1) / len(selected_rows))
                st.sidebar.success("Bulk update complete!")
                st.rerun()
        st.sidebar.divider()

    # Standard Actions
    if st.sidebar.button("❌ Cross Out Selected"):
        if not selected_rows: st.sidebar.warning("No items selected.")
        else:
            for row in selected_rows:
                if row.get("id"): update_item_status(conn, row.get("id"), "is_hidden", 1)
            st.sidebar.success("Items crossed out.")
            st.rerun()

    if show_hidden and st.sidebar.button("↺ Restore Selected") and selected_rows:
        for row in selected_rows:
            if row.get("id"): update_item_status(conn, row.get("id"), "is_hidden", 0)
        st.sidebar.success("Items restored.")
        st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("🔗 Auto-Match Products"):
        with st.spinner("Linking..."): count = auto_link_products(conn, auction_id)
        st.sidebar.success(f"Linked {count} items!")
        st.rerun()

    # --- SAVE ---
    st.markdown("---")
    col_save, col_dl = st.columns([2, 8])
    with col_save:
        if st.button("💾 Save Data Edits"):
            if updated_data is not None and not updated_data.empty:
                progress = st.progress(0)
                try:
                    with conn:
                        for i, (index, row) in enumerate(updated_data.iterrows()):
                            item_id = row.get("id")
                            if not item_id: continue
                            
                            update_item_status(conn, item_id, "is_watched", 1 if row.get(COL_WATCH) else 0)
                            
                            for disp_col, db_col in DB_COL_MAP.items():
                                val = row.get(disp_col)
                                if pd.notna(val):
                                    update_item_field(conn, item_id, db_col, val)
                            
                            progress.progress((i + 1) / len(updated_data))
                    st.success("Saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving: {e}")

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