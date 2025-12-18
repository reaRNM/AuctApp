# pages/3_Auction_History.py
import streamlit as st
import pandas as pd
import sys
import os
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import create_connection, get_closed_auctions, get_auction_items, update_item_field
from components.grid_styles import JS_CURRENCY_SORT, JS_NATURAL_SORT, JS_PROFIT_STYLE
from components.research import render_research_station
from utils.inventory import auto_link_products
# Constants
from utils.parse import COL_LOT, COL_SOLD, COL_STATUS, COL_TITLE, COL_PROFIT_REALIZED, COL_MSRP_STAT, COL_MSRP, COL_BRAND, COL_MODEL

def render_history_grid(df: pd.DataFrame):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, filterable=True, resizable=True)

    for col in ["id", "current_bid", "sold_price", "is_hidden", "product_id", "auction_id", 
                "master_msrp", "master_target_price", "suggested_msrp", "profit_val"]:
        if col in df.columns: gb.configure_column(col, hide=True)

    if COL_LOT in df.columns: 
        gb.configure_column(COL_LOT, width=80, comparator=JS_NATURAL_SORT)
    
    if COL_STATUS in df.columns: 
        gb.configure_column(COL_STATUS, width=100)
        
    if COL_SOLD in df.columns: 
        gb.configure_column(COL_SOLD, width=100, comparator=JS_CURRENCY_SORT)
        
    if COL_PROFIT_REALIZED in df.columns: 
        gb.configure_column(COL_PROFIT_REALIZED, width=100, comparator=JS_CURRENCY_SORT, cellStyle=JS_PROFIT_STYLE)
        
    if COL_MSRP in df.columns:
        gb.configure_column(COL_MSRP, width=100)

    if COL_TITLE in df.columns:
        gb.configure_column(COL_TITLE, width=350, wrapText=True, autoHeight=True)

    status_style = JsCode("""
        function(params) {
            if (params.value === 'Sold') return {color: 'green', fontWeight: 'bold'};
            if (params.value === 'Unsold/Passed') return {color: 'red', fontWeight: 'bold'};
            return {};
        }
    """)
    if COL_STATUS in df.columns: gb.configure_column(COL_STATUS, cellStyle=status_style)
    
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    grid_options = gb.build()
    
    grid_options['getRowStyle'] = JsCode("""
        function(params) {
            if (params.data.Status === 'Sold') return {'backgroundColor': '#e8f5e9', 'color': 'black'}; 
            if (params.data.Status === 'Unsold/Passed') return {'backgroundColor': '#ffebee', 'color': 'black'};
            return {};
        }
    """)

    return AgGrid(
        df, gridOptions=grid_options, height=600,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        theme="streamlit", allow_unsafe_jscode=True
    )

def _get_auction_selection(conn):
    auctions = get_closed_auctions(conn)
    if auctions.empty:
        st.warning("No closed auctions found with sales data.")
        return None

    st.sidebar.header("History Selection")
    options = {}
    for _, r in auctions.iterrows():
        label = f"{r['id']} - {r['url']}"
        if r['auctioneer'] and r['end_date']:
            label = f"{r['auctioneer']} - {r['end_date']} (ID: {r['id']})"
        options[label] = r["id"]
        
    selected = st.sidebar.selectbox("Select Closed Auction", list(options.keys()))
    return options[selected]

def _load_and_process_data(conn, auction_id):
    df = get_auction_items(conn, auction_id)
    if df.empty: return df

    df["sold_price"] = pd.to_numeric(df["sold_price"], errors="coerce").fillna(0.00)
    df["suggested_msrp"] = pd.to_numeric(df["suggested_msrp"], errors="coerce").fillna(0.00)
    df["master_msrp"] = pd.to_numeric(df["master_msrp"], errors="coerce").fillna(0.00)
    df["master_target_price"] = pd.to_numeric(df["master_target_price"], errors="coerce").fillna(0.00)

    df["working_msrp"] = df["master_msrp"]
    df.loc[df["working_msrp"] == 0, "working_msrp"] = df["suggested_msrp"]
    
    df[COL_MSRP] = df["working_msrp"].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")

    def determine_msrp_status(row):
        if row["product_id"] and row["master_msrp"] > 0: return "✅ Linked"
        if row["suggested_msrp"] > 0: return "⚠️ Scraped"
        return "❌ Missing"
    df[COL_MSRP_STAT] = df.apply(determine_msrp_status, axis=1)

    df["profit_val"] = df.apply(
        lambda x: (x['master_target_price'] if x['master_target_price'] > 0 else x['working_msrp'] * 0.5) 
        - x['sold_price'], axis=1
    )
    df[COL_PROFIT_REALIZED] = df["profit_val"].apply(lambda x: f"${x:,.2f}")

    rename_map = {
        "lot_number": COL_LOT, 
        "status": COL_STATUS,
        "title": COL_TITLE, 
        "brand": COL_BRAND, 
        "model": COL_MODEL
    }
    df = df.rename(columns=rename_map)

    # Use constant for Sold column
    if "sold_price" in df.columns:
        df[COL_SOLD] = df["sold_price"].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
        
    return df

def _perform_bulk_update(conn, selected_rows, title, brand, model):
    progress = st.sidebar.progress(0)
    total = len(selected_rows)
    for i, row in enumerate(selected_rows):
        if not row.get("id"): continue
        if title: update_item_field(conn, row['id'], "title", title)
        if brand: update_item_field(conn, row['id'], "brand", brand)
        if model: update_item_field(conn, row['id'], "model", model)
        progress.progress((i + 1) / total)
    st.sidebar.success("Updated!")
    st.rerun()

def _handle_sidebar_actions(conn, selected_rows, auction_id):
    st.sidebar.divider()
    if len(selected_rows) > 1:
        st.sidebar.subheader(f"✏️ Bulk Edit ({len(selected_rows)} Items)")
        with st.sidebar.form("bulk_history_edit"):
            b_title = st.text_input("Title")
            b_brand = st.text_input("Brand")
            b_model = st.text_input("Model")
            if st.form_submit_button("Update Items"):
                _perform_bulk_update(conn, selected_rows, b_title, b_brand, b_model)
    st.sidebar.divider()
    if st.sidebar.button("🔗 Auto-Match History"):
        with st.spinner("Linking..."):
            count = auto_link_products(conn, auction_id)
        st.sidebar.success(f"Linked {count} items!")
        st.rerun()

def main():
    st.set_page_config(page_title="Auction History", layout="wide")
    st.title("🏆 Auction Results & History")

    try:
        conn = create_connection()
        auction_id = _get_auction_selection(conn)
        if not auction_id: return

        df = _load_and_process_data(conn, auction_id)
        if df.empty: st.warning("No items found."); return

        display_cols = [
            COL_LOT, COL_STATUS, COL_SOLD, COL_MSRP,
            COL_PROFIT_REALIZED, COL_MSRP_STAT, 
            COL_TITLE, COL_BRAND, COL_MODEL, 
            "id", "product_id"
        ]
        safe_cols = [c for c in display_cols if c in df.columns]
        
        grid_result = render_history_grid(df[safe_cols].copy())
        selected_rows = grid_result["selected_rows"]

        _handle_sidebar_actions(conn, selected_rows, auction_id)
        render_research_station(conn, selected_rows)
        
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    main()