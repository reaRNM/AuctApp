# viewer.py
import streamlit as st
import pandas as pd

from utils.db import create_connection, get_auctions, get_auction_items, update_item_field, update_item_status
from utils.parse import classify_risk
from utils.inventory import auto_link_products
from components.grid import render_grid
from components.research import render_research_station

# === CONSTANTS ===
COL_SELECT = "Select" # New
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

st.set_page_config(page_title="Active Viewer", layout="wide")
st.title("🔭 Active Auction Viewer")

# Dashboard Nav
col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    st.page_link("pages/1_Product_Library.py", label="📚 Go to Product Library", icon="📚", use_container_width=True)
with col_nav2:
    st.page_link("pages/2_Auction_History.py", label="🏆 Go to Auction History", icon="🏆", use_container_width=True)
st.divider()

conn = create_connection()
auction_list = get_auctions(conn)

if auction_list.empty: st.warning("No auctions found."); st.stop()

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

# ADD SELECT COLUMN (For Checkboxes)
df[COL_SELECT] = False 

# Rename
rename_map = {
    "lot_number": COL_LOT, "title": COL_TITLE, "brand": COL_BRAND, "model": COL_MODEL,
    "packaging": COL_PACKAGING, "condition": COL_CONDITION, "functional": COL_FUNCTIONAL,
    "missing_parts": COL_MISSING, "missing_parts_desc": COL_MISSING_DESC,
    "damaged": COL_DAMAGED, "damage_desc": COL_DAMAGE_DESC,
    "item_notes": COL_NOTES, "upc": COL_UPC, "asin": COL_ASIN, "url": COL_URL
}
df = df.rename(columns=rename_map)

# Filters
if not show_hidden: df = df[df["is_hidden"] == 0]
if hide_high: df = df[df[COL_RISK] != "HIGH RISK"]
if hide_med: df = df[df[COL_RISK] != "MEDIUM RISK"]
if show_no_bids: df = df[df[COL_RISK] == "NO BIDS"]

# Select Cols (Order matters!)
desired_cols = [
    COL_SELECT, # 1. Explicit Select Column
    COL_RISK,   # 2. Risk
    COL_WATCH,  # 3. Watch
    COL_LOT, 
    COL_BID, 
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

# BULK EDIT (Shows only if items selected)
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

if st.sidebar.button("❌ Cross Out Selected"):
    if not selected_rows: st.sidebar.warning("No items selected.")
    else:
        for row in selected_rows:
            if row.get("id"): update_item_status(conn, row.get("id"), "is_hidden", 1)
        st.sidebar.success("Items crossed out."); st.rerun()

if show_hidden and st.sidebar.button("↺ Restore Selected") and selected_rows:
    for row in selected_rows:
        if row.get("id"): update_item_status(conn, row.get("id"), "is_hidden", 0)
    st.sidebar.success("Items restored."); st.rerun()

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
            editable_cols = [
                'title', 'brand', 'model', 'upc', 'asin',
                'packaging', 'condition', 'functional', 
                'missing_parts', 'missing_parts_desc', 'damaged', 'damage_desc', 
                'item_notes'
            ]
            reverse_map = {v: k for k, v in rename_map.items() if k in editable_cols}
            progress = st.progress(0)
            for i, (index, row) in enumerate(updated_data.iterrows()):
                item_id = row.get("id")
                if not item_id: continue
                update_item_status(conn, item_id, "is_watched", 1 if row.get(COL_WATCH) else 0)
                for disp_col, db_col in reverse_map.items():
                    val = row.get(disp_col)
                    if pd.notna(val): update_item_field(conn, item_id, db_col.lower(), val)
                progress.progress((i + 1) / len(updated_data))
            st.success("Saved!"); st.rerun()

with col_dl:
    try:
        csv_data = df_display.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv_data, f"auction_{auction_id}.csv", "text/csv")
    except Exception: pass

render_research_station(conn, selected_rows)

conn.close()