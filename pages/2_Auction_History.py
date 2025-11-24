# pages/2_Auction_History.py
import streamlit as st
import pandas as pd
import sys
import os
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import create_connection, get_closed_auctions, get_auction_items # Updated Import
from components.grid_styles import JS_CURRENCY_SORT, JS_NATURAL_SORT

# CONSTANTS
COL_LOT = "Lot"
COL_SOLD = "Sold Price"
COL_STATUS = "Status"
COL_TITLE = "Title"

def render_history_grid(df: pd.DataFrame):
    """Helper to configure and render the AgGrid."""
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, filterable=True, resizable=True)

    # Sorters
    gb.configure_column(COL_LOT, comparator=JS_NATURAL_SORT)
    gb.configure_column("Display_Sold", comparator=JS_CURRENCY_SORT, headerName="Sold Price")

    # Styles
    gb.configure_column(COL_STATUS, cellStyle=JsCode("""
        function(params) {
            if (params.value === 'Sold') return {backgroundColor: '#c8e6c9', color: 'black'};
            if (params.value === 'Unsold/Passed') return {backgroundColor: '#ffcdd2', color: 'black'};
            return {};
        }
    """))

    grid_options = gb.build()

    AgGrid(
        df,
        gridOptions=grid_options,
        height=800,
        theme="streamlit",
        allow_unsafe_jscode=True
    )

def main():
    st.set_page_config(page_title="Auction History", layout="wide")
    st.title("🏆 Auction Results & History")

    conn = create_connection()
    auctions = get_closed_auctions(conn) # Updated Function

    if auctions.empty:
        st.warning("No data found.")
        return

    # Sidebar
    auction_options = {f"{r['id']} – {r['url']}": r["id"] for _, r in auctions.iterrows()}
    selected = st.sidebar.selectbox("Select Closed Auction", list(auction_options.keys()))
    auction_id = auction_options[selected]

    # Load Data
    df = get_auction_items(conn, auction_id)

    if df.empty:
        st.warning("No items found.")
        return

    # Rename
    rename_map = {
        "lot_number": COL_LOT, "sold_price": COL_SOLD, "status": COL_STATUS,
        "title": COL_TITLE, "brand": "Brand", "model": "Model"
    }
    df = df.rename(columns=rename_map)

    # Format
    df[COL_SOLD] = pd.to_numeric(df[COL_SOLD], errors='coerce').fillna(0.0)
    df["Display_Sold"] = df[COL_SOLD].apply(lambda x: f"${x:,.2f}" if x > 0 else "-")

    # Display
    display_cols = [COL_LOT, COL_STATUS, "Display_Sold", COL_TITLE, "Brand", "Model", "upc", "asin"]
    # Ensure cols exist
    safe_cols = [c for c in display_cols if c in df.columns]
    
    render_history_grid(df[safe_cols].copy())
    conn.close()

if __name__ == "__main__":
    main()