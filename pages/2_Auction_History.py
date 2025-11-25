# pages/2_Auction_History.py
import streamlit as st
import pandas as pd
import sys
import os
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode

# Allow imports from parent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import create_connection, get_closed_auctions, get_auction_items
from components.grid_styles import JS_CURRENCY_SORT, JS_NATURAL_SORT
from components.research import render_research_station 

# CONSTANTS
COL_LOT = "Lot"
COL_SOLD = "Sold Price"
COL_STATUS = "Status"
COL_TITLE = "Title"

def render_history_grid(df: pd.DataFrame):
    """Helper to configure and render the AgGrid."""
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, filterable=True, resizable=True)

    # Hide Utility Columns
    for col in ["id", "current_bid", "sold_price", "is_hidden", "product_id", "auction_id"]:
        if col in df.columns:
            gb.configure_column(col, hide=True)

    # === SORTING FIXES ===
    # 1. Lot Number
    if COL_LOT in df.columns:
        gb.configure_column(COL_LOT, comparator=JS_NATURAL_SORT)
    
    # 2. Text Columns (Case-Insensitive Sort)
    # This fixes the "Z before a" issue
    for col in [COL_TITLE, "Brand", "Model"]:
        if col in df.columns:
            gb.configure_column(col, comparator=JS_NATURAL_SORT)

    # 3. Currency Sort
    if "Display_Sold" in df.columns:
        gb.configure_column("Display_Sold", comparator=JS_CURRENCY_SORT, headerName="Sold Price")

    # Styles: Green for Sold, Red for Unsold
    status_style = JsCode("""
        function(params) {
            if (params.value === 'Sold') return {color: 'green', fontWeight: 'bold'};
            if (params.value === 'Unsold/Passed') return {color: 'red', fontWeight: 'bold'};
            return {};
        }
    """)
    if COL_STATUS in df.columns:
        gb.configure_column(COL_STATUS, cellStyle=status_style)
    
    # Selection (Enabled so we can click to research)
    gb.configure_selection(selection_mode="single", use_checkbox=True)

    grid_options = gb.build()
    
    # Row Styles
    grid_options['getRowStyle'] = JsCode("""
        function(params) {
            if (params.data.Status === 'Sold') return {'backgroundColor': '#e8f5e9', 'color': 'black'}; 
            if (params.data.Status === 'Unsold/Passed') return {'backgroundColor': '#ffebee', 'color': 'black'};
            return {};
        }
    """)

    return AgGrid(
        df,
        gridOptions=grid_options,
        height=600,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        theme="streamlit",
        allow_unsafe_jscode=True
    )

def main():
    st.set_page_config(page_title="Auction History", layout="wide")
    st.title("🏆 Auction Results & History")

    try:
        conn = create_connection()
        
        # 1. Sidebar Selection
        auctions = get_closed_auctions(conn)
        if auctions.empty:
            st.warning("No closed auctions found with sales data.")
            return

        st.sidebar.header("History Selection")
        auction_options = {f"{r['id']} – {r['url']}": r["id"] for _, r in auctions.iterrows()}
        selected = st.sidebar.selectbox("Select Closed Auction", list(auction_options.keys()))
        auction_id = auction_options[selected]

        # 2. Load Data
        df = get_auction_items(conn, auction_id)
        if df.empty:
            st.warning("No items found for this auction.")
            return

        # 3. Process Data
        rename_map = {
            "lot_number": COL_LOT, 
            "sold_price": COL_SOLD, 
            "status": COL_STATUS,
            "title": COL_TITLE, 
            "brand": "Brand", 
            "model": "Model"
        }
        df = df.rename(columns=rename_map)

        # Format Currency
        if COL_SOLD in df.columns:
            df[COL_SOLD] = pd.to_numeric(df[COL_SOLD], errors='coerce').fillna(0.0)
            df["Display_Sold"] = df[COL_SOLD].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")
        else:
            df["Display_Sold"] = "-"

        # Columns to Display
        display_cols = [
            COL_LOT, COL_STATUS, "Display_Sold", 
            COL_TITLE, "Brand", "Model", 
            "id", "product_id" # Hidden IDs needed for linking
        ]
        safe_cols = [c for c in display_cols if c in df.columns]
        
        # 4. Render Grid
        grid_result = render_history_grid(df[safe_cols].copy())
        selected_rows = grid_result["selected_rows"]

        # 5. Research Station
        render_research_station(conn, selected_rows)
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()