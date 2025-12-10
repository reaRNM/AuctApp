# pages/1_Active_Viewer.py
import streamlit as st
import pandas as pd
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import create_connection, get_active_auctions, get_auction_items, update_item_field, update_item_status
from utils.parse import classify_risk
from utils.inventory import auto_link_products
from components.grid import render_grid, COLUMN_BID, COLUMN_EST_PROFIT
from components.research import render_research_station
from components.filters import render_filters, apply_filters

# === CONSTANTS ===
COL_SELECT = "Select"
COL_LOT = "Lot"
COL_MSRP_STAT = "MSRP Status"
COL_TITLE = "Title"
COL_BRAND = "Brand"
COL_MODEL = "Model"
COL_CATEGORY = "Category"
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
# COL_URL = "URL" # REMOVED from display
COL_SCRAPED_MSRP = "MSRP"

DB_COL_MAP = {
    COL_TITLE: 'title', COL_BRAND: 'brand', COL_MODEL: 'model',
    COL_UPC: 'upc', COL_ASIN: 'asin', COL_CATEGORY: 'scraped_category',
    COL_PACKAGING: 'packaging', COL_CONDITION: 'condition', 
    COL_FUNCTIONAL: 'functional', COL_MISSING: 'missing_parts',
    COL_MISSING_DESC: 'missing_parts_desc', COL_DAMAGED: 'damaged',
    COL_DAMAGE_DESC: 'damage_desc', COL_NOTES: 'item_notes'
}

st.set_page_config(page_title="Active Viewer", layout="wide")
st.title("🔭 Active Auction Viewer")

if 'refresh_id' not in st.session_state:
    st.session_state.refresh_id = 0

def force_refresh():
    st.session_state.refresh_id += 1

col_nav1, col_nav2 = st.columns(2)
with col_nav1: st.page_link("pages/2_Product_Library.py", label="📚 Go to Product Library", icon="📚", use_container_width=True)
with col_nav2: st.page_link("pages/3_Auction_History.py", label="🏆 Go to Auction History", icon="🏆", use_container_width=True)
st.divider()

try:
    conn = create_connection()
    auction_list = get_active_auctions(conn)

    if auction_list.empty:
        st.warning("No active auctions found.")
        st.stop()

    # --- AUCTION SELECTION ---
    st.sidebar.header("Auction Selection")
    auction_options = {}
    auction_urls = {}
    for _, r in auction_list.iterrows():
        label = f"{r['id']} – {r['url']} ({r['item_count']})"
        if r.get('auctioneer') and r.get('end_date'):
            label = f"{r['auctioneer']} - {r['end_date']} ({r['item_count']} items)"
        auction_options[label] = r["id"]
        auction_urls[r["id"]] = r["url"]
        
    selected = st.sidebar.selectbox("Select Auction", list(auction_options.keys()))
    auction_id = auction_options[selected]
    current_url = auction_urls.get(auction_id)

    current_auc = auction_list[auction_list['id'] == auction_id].iloc[0]
    
    # --- HEADER & LINK ---
    c_head, c_link = st.columns([8, 2])
    with c_head:
        if current_auc.get('auction_title'):
            st.subheader(f"📂 {current_auc['auction_title']}")
            st.caption(f"Ends: {current_auc.get('end_date')} | Auctioneer: {current_auc.get('auctioneer')}")
        else:
            st.subheader(f"Auction #{auction_id}")
    
    with c_link:
        st.write("") # Spacing
        if current_url:
            st.link_button("🔗 Go to Auction Website", current_url, use_container_width=True)

    # --- INVENTORY ACTIONS ---
    st.sidebar.divider()
    st.sidebar.header("Inventory Actions")
    
    # --- GET DATA ---
    df = get_auction_items(conn, auction_id)
    if df.empty: st.warning("No items found."); st.stop()

    # 1. FAVORITE IDS
    fav_query = "SELECT id FROM products WHERE is_favorite = 1"
    fav_ids = pd.read_sql_query(fav_query, conn)['id'].tolist()

    # 2. CALCULATIONS
    df[COL_RISK] = df.apply(classify_risk, axis=1)
    df["current_bid"] = pd.to_numeric(df["current_bid"], errors="coerce").fillna(0.00)
    df["suggested_msrp"] = pd.to_numeric(df["suggested_msrp"], errors="coerce").fillna(0.00)
    df["master_msrp"] = pd.to_numeric(df["master_msrp"], errors="coerce").fillna(0.00)
    df["master_target_price"] = pd.to_numeric(df["master_target_price"], errors="coerce").fillna(0.00)
    df["is_hidden"] = pd.to_numeric(df["is_hidden"], errors="coerce").fillna(0).astype(int)
    df["is_watched"] = pd.to_numeric(df["is_watched"], errors="coerce").fillna(0).astype(int)

    # MSRP Logic
    df["working_msrp"] = df["master_msrp"]
    df.loc[df["working_msrp"] == 0, "working_msrp"] = df["suggested_msrp"]
    df[COL_SCRAPED_MSRP] = df["working_msrp"]

    # Favorite Logic
    def flag_favorites(row):
        title = row['title']
        if row['product_id'] in fav_ids:
            return f"❤️ {title}" 
        return title
    
    df['title'] = df.apply(flag_favorites, axis=1)

    # Other Metrics
    def determine_msrp_status(row):
        if row["product_id"] and row["master_msrp"] > 0: return "✅ Linked"
        if row["suggested_msrp"] > 0: return "⚠️ Scraped"
        return "❌ Missing"
    df[COL_MSRP_STAT] = df.apply(determine_msrp_status, axis=1)

    # Profit Logic
    df["profit_val"] = df.apply(lambda x: (x['master_target_price'] - x['current_bid']) if x['master_target_price'] > 0 else 0, axis=1)
    df[COLUMN_EST_PROFIT] = df["profit_val"].apply(lambda x: f"${x:,.2f}" if x != 0 else "-")
    
    df[COLUMN_BID] = df["current_bid"].apply(lambda x: f"${x:,.2f}")
    df[COL_WATCH] = df["is_watched"].apply(lambda x: True if x == 1 else False)
    
    df[COL_SELECT] = False 
    
    # 3. RENAME
    rename_map = {
        "lot_number": COL_LOT, "title": COL_TITLE, "brand": COL_BRAND, "model": COL_MODEL,
        "scraped_category": COL_CATEGORY,
        "packaging": COL_PACKAGING, "condition": COL_CONDITION, "functional": COL_FUNCTIONAL,
        "missing_parts": COL_MISSING, "missing_parts_desc": COL_MISSING_DESC,
        "damaged": COL_DAMAGED, "damage_desc": COL_DAMAGE_DESC,
        "item_notes": COL_NOTES, "upc": COL_UPC, "asin": COL_ASIN, 
        # "url": COL_URL # Removed from map
    }
    df = df.rename(columns=rename_map)

    # 4. FILTERS
    with st.expander("🔎 Filters", expanded=True):
        active_filters = render_filters(df)
    
    df_display = apply_filters(df, active_filters)

    # Sidebar Toggle: Show Hidden
    show_hidden = st.sidebar.checkbox("Show Crossed Out Items", value=False, on_change=force_refresh)
    if not show_hidden:
        df_display = df_display[df_display["is_hidden"] == 0]

    # 5. GRID SETUP
    desired_cols = [
        COL_SELECT, COL_RISK, COL_WATCH, COL_LOT, COLUMN_BID,
        COL_TITLE, COL_BRAND, COL_MODEL, COL_CATEGORY, COL_SCRAPED_MSRP, COLUMN_EST_PROFIT,
        COL_PACKAGING, COL_CONDITION, COL_FUNCTIONAL, 
        COL_MISSING, COL_MISSING_DESC, COL_DAMAGED, COL_DAMAGE_DESC, 
        COL_NOTES, COL_UPC, COL_ASIN, 
        # COL_URL, # Removed from Grid
        "id", "is_hidden", "current_bid", "product_id", 
        "master_msrp", "master_target_price", "profit_val",
    ]
    final_cols = [c for c in desired_cols if c in df_display.columns]
    
    # Render Grid
    grid_result = render_grid(df_display[final_cols].copy(), grid_key=str(auction_id), refresh_id=st.session_state.refresh_id)
    
    # --- SAFE SELECTION EXTRACTION ---
    selected_rows = []
    updated_data = None
    
    if grid_result:
        try:
            if isinstance(grid_result, dict):
                selected_rows = grid_result.get("selected_rows", [])
                updated_data = grid_result.get("data")
            else:
                selected_rows = getattr(grid_result, "selected_rows", [])
                updated_data = getattr(grid_result, "data", None)
        except Exception:
            selected_rows = []
            updated_data = None

    # --- SIDEBAR ACTIONS ---
    # Cross Out
    if st.sidebar.button("❌ Cross Out Selected"):
        if not selected_rows: st.sidebar.warning("No items selected.")
        else:
            with conn:
                for row in selected_rows:
                    raw_id = row.get("id")
                    if raw_id is not None:
                        update_item_status(conn, int(raw_id), "is_hidden", 1)
            st.sidebar.success("Items crossed out.")
            force_refresh()
            st.rerun()

    # Restore
    if show_hidden and st.sidebar.button("↺ Restore Selected"):
        if not selected_rows: st.sidebar.warning("No items selected.")
        else:
            with conn:
                for row in selected_rows:
                    raw_id = row.get("id")
                    if raw_id is not None:
                        update_item_status(conn, int(raw_id), "is_hidden", 0)
            st.sidebar.success("Items restored.")
            force_refresh()
            st.rerun()

    if st.sidebar.button("🔗 Auto-Match Products"):
        with st.spinner("Linking..."): count = auto_link_products(conn, auction_id)
        st.sidebar.success(f"Linked {count} items!")
        force_refresh()
        st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("🛑 Close Auction"):
        from closer import process_closed_auction
        if not current_url: st.error("No URL found.")
        else:
            with st.status("Processing..."):
                process_closed_auction(current_url)
                st.success("Closed!")
                time.sleep(1)
                st.switch_page("pages/3_Auction_History.py")

    # --- SAVE ---
    st.markdown("---")
    col_save, col_dl = st.columns([2, 8])
    with col_save:
        if st.button("💾 Save Data Edits"):
            if updated_data is not None and isinstance(updated_data, pd.DataFrame) and not updated_data.empty:
                progress = st.progress(0)
                with conn:
                    for i, (index, row) in enumerate(updated_data.iterrows()):
                        raw_id = row.get("id")
                        if raw_id is None: continue
                        
                        item_id = int(raw_id)
                        
                        update_item_status(conn, item_id, "is_watched", 1 if row.get(COL_WATCH) else 0)
                        for disp_col, db_col in DB_COL_MAP.items():
                            val = row.get(disp_col)
                            if pd.notna(val): update_item_field(conn, item_id, db_col, val)
                        progress.progress((i + 1) / len(updated_data))
                st.success("Saved!")
                st.rerun()

    with col_dl:
        try:
            csv_data = df_display.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv_data, f"auction_{auction_id}.csv", "text/csv")
        except Exception: pass

    render_research_station(conn, selected_rows)

finally:
    if 'conn' in locals(): conn.close()