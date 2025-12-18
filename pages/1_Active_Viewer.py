# pages/1_Active_Viewer.py
import streamlit as st
import pandas as pd
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import create_connection, get_active_auctions, get_auction_items, update_item_field, update_item_status
from utils.inventory import auto_link_products
from components.grid import render_grid
from components.research import render_research_station
from components.filters import render_filters, apply_filters

# IMPORT CONSTANTS & FUNCTIONS
from utils.parse import (
    classify_risk, # <--- ADDED THIS IMPORT
    COL_SELECT, COL_LOT, COL_MSRP_STAT, COL_TITLE, COL_BRAND, COL_MODEL, COL_CAT,
    COL_WATCH, COL_RISK, COL_PKG, COL_COND, COL_FUNC, COL_MISSING, COL_MISSING_DESC,
    COL_DMG, COL_DMG_DESC, COL_NOTES, COL_UPC, COL_ASIN, COL_URL, COL_MSRP, COL_WON,
    COL_BID, COL_EST_PROFIT,
    # Import DB Keys for Mapping
    KEY_DB_TITLE, KEY_DB_BRAND, KEY_DB_MODEL, KEY_DB_UPC, KEY_DB_ASIN, KEY_DB_SCRAPED_CAT,
    KEY_DB_PKG, KEY_DB_COND, KEY_DB_FUNC, KEY_DB_MISSING, KEY_DB_MISSING_DESC,
    KEY_DB_DMG, KEY_DB_DMG_DESC, KEY_DB_ITEM_NOTES, KEY_IS_WON, KEY_IS_WATCHED,
    KEY_CURRENT_BID, KEY_SUG_MSRP, KEY_MASTER_MSRP, KEY_TARGET_PRICE, KEY_IS_HIDDEN, KEY_PROD_ID
)

# MAP DISPLAY COLUMNS (Grid Headers) -> TO DATABASE COLUMNS (SQLite Keys)
DB_COL_MAP = {
    COL_TITLE: KEY_DB_TITLE,
    COL_BRAND: KEY_DB_BRAND,
    COL_MODEL: KEY_DB_MODEL,
    COL_UPC: KEY_DB_UPC,
    COL_ASIN: KEY_DB_ASIN,
    COL_CAT: KEY_DB_SCRAPED_CAT,
    COL_PKG: KEY_DB_PKG,
    COL_COND: KEY_DB_COND, 
    COL_FUNC: KEY_DB_FUNC,
    COL_MISSING: KEY_DB_MISSING,
    COL_MISSING_DESC: KEY_DB_MISSING_DESC,
    COL_DMG: KEY_DB_DMG,
    COL_DMG_DESC: KEY_DB_DMG_DESC,
    COL_NOTES: KEY_DB_ITEM_NOTES, 
    COL_WON: KEY_IS_WON
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
    
    c_head, c_link = st.columns([8, 2])
    with c_head:
        if current_auc.get('auction_title'):
            st.subheader(f"📂 {current_auc['auction_title']}")
            st.caption(f"Ends: {current_auc.get('end_date')} | Auctioneer: {current_auc.get('auctioneer')}")
        else:
            st.subheader(f"Auction #{auction_id}")
    
    with c_link:
        st.write("") 
        if current_url:
            st.link_button("🔗 Go to Auction Website", current_url, use_container_width=True)

    st.sidebar.divider()
    st.sidebar.header("Inventory Actions")
    
    search_query = st.sidebar.text_input("🔍 Search Items", placeholder="Lot #, Title, Brand...").strip().lower()
    st.sidebar.divider()
    
    df = get_auction_items(conn, auction_id)
    if df.empty: st.warning("No items found."); st.stop()

    fav_query = "SELECT id FROM products WHERE is_favorite = 1"
    fav_ids = pd.read_sql_query(fav_query, conn)['id'].tolist()

    # FUNCTION NOW DEFINED
    df[COL_RISK] = df.apply(lambda row: classify_risk(row), axis=1)

    df[KEY_CURRENT_BID] = pd.to_numeric(df[KEY_CURRENT_BID], errors="coerce").fillna(0.00)
    df[KEY_SUG_MSRP] = pd.to_numeric(df[KEY_SUG_MSRP], errors="coerce").fillna(0.00)
    df[KEY_MASTER_MSRP] = pd.to_numeric(df[KEY_MASTER_MSRP], errors="coerce").fillna(0.00)
    df[KEY_TARGET_PRICE] = pd.to_numeric(df[KEY_TARGET_PRICE], errors="coerce").fillna(0.00)
    df[KEY_IS_HIDDEN] = pd.to_numeric(df[KEY_IS_HIDDEN], errors="coerce").fillna(0).astype(int)
    df[KEY_IS_WATCHED] = pd.to_numeric(df[KEY_IS_WATCHED], errors="coerce").fillna(0).astype(int)
    df[KEY_IS_WON] = pd.to_numeric(df[KEY_IS_WON], errors="coerce").fillna(0).astype(int)

    df["working_msrp"] = df[KEY_MASTER_MSRP]
    df.loc[df["working_msrp"] == 0, "working_msrp"] = df[KEY_SUG_MSRP]
    df[COL_MSRP] = df["working_msrp"]

    def flag_favorites(row):
        title = row['title']
        if row[KEY_PROD_ID] in fav_ids:
            return f"❤️ {title}" 
        return title
    
    df['title'] = df.apply(flag_favorites, axis=1)

    def determine_msrp_status(row):
        if row[KEY_PROD_ID] and row[KEY_MASTER_MSRP] > 0: return "✅ Linked"
        if row[KEY_SUG_MSRP] > 0: return "⚠️ Scraped"
        return "❌ Missing"
    df[COL_MSRP_STAT] = df.apply(determine_msrp_status, axis=1)

    def calc_real_profit(row):
        target = row[KEY_TARGET_PRICE]
        if target <= 0: return 0
        bid = row[KEY_CURRENT_BID]
        ship = row.get('shipping_cost_basis', 0) or 0
        fees = target * 0.15 
        return target - bid - ship - fees

    df["profit_val"] = df.apply(calc_real_profit, axis=1)
    df[COL_EST_PROFIT] = df.apply(lambda x: f"${x['profit_val']:,.2f}" if x[KEY_TARGET_PRICE] > 0 else "-", axis=1)
    
    df[COL_BID] = df[KEY_CURRENT_BID].apply(lambda x: f"${x:,.2f}")
    df[COL_WATCH] = df[KEY_IS_WATCHED].apply(lambda x: True if x == 1 else False)
    df[COL_WON] = df[KEY_IS_WON].apply(lambda x: True if x == 1 else False)
    
    df[COL_SELECT] = False 
    
    rename_map = {
        "lot_number": COL_LOT, 
        KEY_DB_TITLE: COL_TITLE, 
        KEY_DB_BRAND: COL_BRAND, 
        KEY_DB_MODEL: COL_MODEL,
        KEY_DB_SCRAPED_CAT: COL_CAT,
        KEY_DB_PKG: COL_PKG, 
        KEY_DB_COND: COL_COND, 
        KEY_DB_FUNC: COL_FUNC,
        KEY_DB_MISSING: COL_MISSING, 
        KEY_DB_MISSING_DESC: COL_MISSING_DESC,
        KEY_DB_DMG: COL_DMG, 
        KEY_DB_DMG_DESC: COL_DMG_DESC,
        KEY_DB_ITEM_NOTES: COL_NOTES, 
        KEY_DB_UPC: COL_UPC, 
        KEY_DB_ASIN: COL_ASIN, 
    }
    df = df.rename(columns=rename_map)

    with st.expander("🔎 Filters", expanded=True):
        active_filters = render_filters(df)
    
    df_display = apply_filters(df, active_filters)

    if search_query:
        mask = (
            df_display[COL_TITLE].astype(str).str.lower().str.contains(search_query) |
            df_display[COL_BRAND].astype(str).str.lower().str.contains(search_query) |
            df_display[COL_MODEL].astype(str).str.lower().str.contains(search_query) |
            df_display[COL_LOT].astype(str).str.lower().str.contains(search_query)
        )
        df_display = df_display[mask]

    show_hidden = st.sidebar.checkbox("Show Crossed Out Items", value=False, on_change=force_refresh)
    if not show_hidden:
        df_display = df_display[df_display[KEY_IS_HIDDEN] == 0]

    desired_cols = [
        COL_SELECT, COL_RISK, COL_WATCH, COL_WON, COL_LOT, COL_BID,
        COL_TITLE, COL_BRAND, COL_MODEL, COL_CAT, COL_MSRP, COL_EST_PROFIT,
        COL_PKG, COL_COND, COL_FUNC, 
        COL_MISSING, COL_MISSING_DESC, COL_DMG, COL_DMG_DESC, 
        COL_NOTES, COL_UPC, COL_ASIN, 
        "id", KEY_IS_HIDDEN, KEY_CURRENT_BID, KEY_PROD_ID, 
        KEY_MASTER_MSRP, KEY_TARGET_PRICE, "profit_val",
    ]
    final_cols = [c for c in desired_cols if c in df_display.columns]
    
    grid_result = render_grid(df_display[final_cols].copy(), grid_key=str(auction_id), refresh_id=st.session_state.refresh_id)
    
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

    if st.sidebar.button("❌ Cross Out Selected"):
        if not selected_rows: st.sidebar.warning("No items selected.")
        else:
            with conn:
                for row in selected_rows:
                    raw_id = row.get("id")
                    if raw_id is not None:
                        update_item_status(conn, int(raw_id), KEY_IS_HIDDEN, 1)
            st.sidebar.success("Items crossed out.")
            force_refresh()
            st.rerun()

    if show_hidden and st.sidebar.button("↺ Restore Selected"):
        if not selected_rows: st.sidebar.warning("No items selected.")
        else:
            with conn:
                for row in selected_rows:
                    raw_id = row.get("id")
                    if raw_id is not None:
                        update_item_status(conn, int(raw_id), KEY_IS_HIDDEN, 0)
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
                        
                        update_item_status(conn, item_id, KEY_IS_WATCHED, 1 if row.get(COL_WATCH) else 0)
                        update_item_status(conn, item_id, KEY_IS_WON, 1 if row.get(COL_WON) else 0)
                        
                        for disp_col, db_col in DB_COL_MAP.items():
                            if disp_col == COL_WON: continue 
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