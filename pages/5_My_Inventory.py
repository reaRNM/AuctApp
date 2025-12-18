# pages/5_My_Inventory.py
import streamlit as st
import pandas as pd
import sys
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import create_connection

# IMPORT CONSTANTS
from utils.parse import (
    COL_TITLE, COL_STATUS, COL_DATE, COL_TOTAL_COST, COL_SOURCE, 
    COL_PURCHASE, COL_SOLD
)

st.set_page_config(page_title="My Inventory", layout="wide")
st.title("📦 My Inventory (Won Items)")

conn = create_connection()

# Metrics (Uses internal SQL aliases, display strings are hardcoded which is fine for UI labels)
stats = pd.read_sql_query("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN status='In Stock' THEN 1 ELSE 0 END) as stock,
        SUM(CASE WHEN status='Sold' THEN 1 ELSE 0 END) as sold,
        SUM(total_cost) as invest
    FROM inventory_ledger
""", conn).iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Items", stats['total'])
c2.metric("In Stock", stats['stock'])
c3.metric("Sold", stats['sold'])
c4.metric("Total Investment", f"${stats['invest'] or 0:,.2f}")

st.divider()

# QUERY USES CONSTANTS FOR COLUMN HEADERS
query = f"""
    SELECT l.id, 
           l.purchase_date as "{COL_DATE}", 
           l.status as "{COL_STATUS}", 
           p.title as "{COL_TITLE}", 
           l.purchase_price as "{COL_PURCHASE}", 
           l.total_cost as "{COL_TOTAL_COST}", 
           l.auction_source as "{COL_SOURCE}"
    FROM inventory_ledger l
    LEFT JOIN products p ON l.product_id = p.id
    ORDER BY l.purchase_date DESC
"""
df = pd.read_sql_query(query, conn)

if not df.empty:
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_column("id", hide=True)
    
    # Configure Columns using Constants
    gb.configure_column(COL_TITLE, minWidth=300)
    gb.configure_column(COL_STATUS, editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': ['In Stock', 'Listed', 'Sold']})
    
    gb.configure_column(COL_PURCHASE, valueFormatter="'$' + x")
    gb.configure_column(COL_TOTAL_COST, valueFormatter="'$' + x")
    
    AgGrid(df, gridOptions=gb.build(), update_mode=GridUpdateMode.VALUE_CHANGED, theme="streamlit")
else:
    st.info("No items yet. Close an auction with 'Won' items to see them here!")