# pages/2_Auction_History.py
import streamlit as st
import pandas as pd
import sys
import os
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import create_connection, get_closed_auctions, get_auction_items, update_item_field
from components.grid_styles import JS_CURRENCY_SORT, JS_NATURAL_SORT
from components.research import render_research_station
from utils.inventory import auto_link_products

COL_LOT = "Lot"
COL_SOLD = "Sold Price"
COL_STATUS = "Status"
COL_TITLE = "Title"

# ----------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------
def render_history_grid(df: pd.DataFrame):
    """Configures and renders the AgGrid."""
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, filterable=True, resizable=True)

    # Hide Utility Cols
    for col in ["id", "current_bid", "sold_price", "is_hidden", "product_id", "auction_id"]:
        if col in df.columns: gb.configure_column(col, hide=True)

    # Sorters
    if COL_LOT in df.columns: gb.configure_column(COL_LOT, comparator=JS_NATURAL_SORT)
    if "Display_Sold" in df.columns: gb.configure_column("Display_Sold", comparator=JS_CURRENCY_SORT, headerName="Sold Price")

    # Styles
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
    options = {f"{r['id']} – {r['url']}": r["id"] for _, r in auctions.iterrows()}
    selected = st.sidebar.selectbox("Select Closed Auction", list(options.keys()))
    return options[selected]

def _load_and_process_data(conn, auction_id):
    df = get_auction_items(conn, auction_id)
    if df.empty: return df

    rename_map = {
        "lot_number": COL_LOT, "sold_price": COL_SOLD, "status": COL_STATUS,
        "title": COL_TITLE, "brand": "Brand", "model": "Model"
    }
    df = df.rename(columns=rename_map)

    if COL_SOLD in df.columns:
        df[COL_SOLD] = pd.to_numeric(df[COL_SOLD], errors='coerce').fillna(0.0)
        df["Display_Sold"] = df[COL_SOLD].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
    else:
        df["Display_Sold"] = "-"
        
    return df

def _perform_bulk_update(conn, selected_rows, title, brand, model):
    """Helper to execute the bulk update loop."""
    progress = st.sidebar.progress(0)
    total = len(selected_rows)
    
    for i, row in enumerate(selected_rows):
        item_id = row.get("id")
        if not item_id: continue
        
        if title: update_item_field(conn, item_id, "title", title)
        if brand: update_item_field(conn, item_id, "brand", brand)
        if model: update_item_field(conn, item_id, "model", model)
        
        progress.progress((i + 1) / total)
    
    st.sidebar.success("Updated!")
    st.rerun()

def _handle_sidebar_actions(conn, selected_rows, auction_id):
    """Handles Bulk Edit and Auto-Match buttons in sidebar."""
    st.sidebar.divider()
    
    # 1. Bulk Edit
    if len(selected_rows) > 1:
        st.sidebar.subheader(f"✏️ Bulk Edit ({len(selected_rows)} Items)")
        with st.sidebar.form("bulk_history_edit"):
            b_title = st.text_input("Title")
            b_brand = st.text_input("Brand")
            b_model = st.text_input("Model")
            
            if st.form_submit_button("Update Items"):
                _perform_bulk_update(conn, selected_rows, b_title, b_brand, b_model)
    
    # 2. Auto-Match
    st.sidebar.divider()
    if st.sidebar.button("🔗 Auto-Match History"):
        with st.spinner("Linking..."):
            count = auto_link_products(conn, auction_id)
        st.sidebar.success(f"Linked {count} items!")
        st.rerun()

# ----------------------------------------------------------------------
# MAIN ORCHESTRATOR
# ----------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Auction History", layout="wide")
    st.title("🏆 Auction Results & History")

    try:
        conn = create_connection()
        
        # 1. Select Auction
        auction_id = _get_auction_selection(conn)
        if not auction_id: return

        # 2. Load Data
        df = _load_and_process_data(conn, auction_id)
        if df.empty:
            st.warning("No items found.")
            return

        # 3. Prepare Display Columns
        display_cols = [
            COL_LOT, COL_STATUS, "Display_Sold", 
            COL_TITLE, "Brand", "Model", 
            "id", "product_id"
        ]
        safe_cols = [c for c in display_cols if c in df.columns]
        
        # 4. Render Grid
        grid_result = render_history_grid(df[safe_cols].copy())
        selected_rows = grid_result["selected_rows"]

        # 5. Handle Actions & Research
        _handle_sidebar_actions(conn, selected_rows, auction_id)
        render_research_station(conn, selected_rows)
        
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    main()