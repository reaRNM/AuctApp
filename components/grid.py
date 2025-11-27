# components/grid.py
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode
from components.grid_styles import (
    JS_CHECKBOX_RENDERER, JS_EMPTY_TEXT, JS_ROW_STYLE,
    JS_STYLE_BAD_YES, JS_STYLE_BAD_NO, JS_STYLE_BAD_COND,
    JS_NATURAL_SORT, JS_CURRENCY_SORT,
    JS_ACTIONS_RENDERER, JS_PROFIT_STYLE, JS_BID_PERCENT_STYLE # <--- New Imports
)
from components.grid_options import configure_column_editors

from st_aggrid import JsCode
JS_RISK_CELL_STYLE = JsCode("""
function(params) {
    if (params.value === 'HIGH RISK') return {'color': '#d32f2f', 'fontWeight': 'bold'};
    if (params.value === 'MEDIUM RISK') return {'color': '#e65100', 'fontWeight': 'bold'};
    if (params.value === 'NO BIDS') return {'color': '#1565c0', 'fontWeight': 'bold'};
    return {};
}
""")

COLUMN_BID = "Bid"

def _configure_hidden_cols(gb, columns):
    hidden_cols = [
        "id", "current_bid", "is_hidden", "product_id", "auction_id", 
        "sold_price", "suggested_msrp", "url", 
        "master_msrp", "master_target_price", "profit_val"
    ]
    for col in hidden_cols:
        if col in columns: gb.configure_column(col, hide=True)

def _configure_special_cols(gb, columns):
    # Selection
    if "Select" in columns:
        gb.configure_column("Select", checkboxSelection=True, headerCheckboxSelection=True, width=50, pinned="left", headerName="Select", suppressMenu=True, valueFormatter=JS_EMPTY_TEXT)
    
    # Actions
    if "Actions" in columns:
        gb.configure_column("Actions", cellRenderer=JS_ACTIONS_RENDERER, width=50, pinned="left", headerName="", suppressMenu=True)

    # Indicators
    if "Risk" in columns:
        gb.configure_column("Risk", width=130, pinned="left")

    if "Watch" in columns:
        gb.configure_column("Watch", editable=True, cellRenderer=JS_CHECKBOX_RENDERER, cellEditor='agCheckboxCellEditor', valueFormatter=JS_EMPTY_TEXT, width=60, pinned="left", headerName="⭐")

def _configure_metrics_cols(gb, columns):
    if "Est. Profit" in columns:
        gb.configure_column("Est. Profit", width=100, cellStyle=JS_PROFIT_STYLE, comparator=JS_CURRENCY_SORT)
    
    if "Bid %" in columns:
        gb.configure_column("Bid %", width=90, cellStyle=JS_BID_PERCENT_STYLE)

    if "MSRP Status" in columns:
        gb.configure_column("MSRP Status", width=110)

def _configure_sorting(gb, columns):
    text_cols = ["Lot", "Title", "Brand", "Model", "UPC", "ASIN", "Category"]
    for col in text_cols:
        if col in columns: gb.configure_column(col, comparator=JS_NATURAL_SORT)

    if COLUMN_BID in columns: 
        gb.configure_column(COLUMN_BID, width=100, comparator=JS_CURRENCY_SORT)

def _configure_styles(gb, columns):
    if "Functional" in columns: gb.configure_column("Functional", cellStyle=JS_STYLE_BAD_NO)
    if "Condition" in columns: gb.configure_column("Condition", cellStyle=JS_STYLE_BAD_COND)
    for col in ["Damaged", "Missing Parts"]:
        if col in columns: gb.configure_column(col, cellStyle=JS_STYLE_BAD_YES)

# ----------------------------------------------------------------------
# MAIN CONFIGURATION
# ----------------------------------------------------------------------
def _configure_columns(gb: GridOptionsBuilder, df: pd.DataFrame):
    columns = df.columns
    
    _configure_hidden_cols(gb, columns)
    _configure_special_cols(gb, columns)
    _configure_metrics_cols(gb, columns)
    _configure_sorting(gb, columns)
    _configure_styles(gb, columns)
    
    # Apply Dropdown Editors
    configure_column_editors(gb)

def render_grid(df: pd.DataFrame, height: int = 550, allow_selection: bool = True):
    # ... (Render logic remains the same) ...
    if df is None or df.empty: return {"selected": [], "data": df}
    
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, filterable=True, resizable=True, wrapText=True, autoHeight=True)
    gb.configure_grid_options(getRowStyle=JS_ROW_STYLE)
    gb.configure_grid_options(enableRangeSelection=True) 
    
    # === CLIPBOARD SUPPORT ===
    gb.configure_grid_options(enableRangeSelection=True) 
    gb.configure_grid_options(rowSelection='multiple') # Helper for clipboard
    
    _configure_columns(gb, df)

    if allow_selection:
        gb.configure_selection(selection_mode="multiple", use_checkbox=False, header_checkbox=False, suppressRowClickSelection=True)

    grid_options = gb.build()

    return AgGrid(
        df, gridOptions=grid_options, height=height, 
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED, 
        update_mode=GridUpdateMode.MODEL_CHANGED, 
        allow_unsafe_jscode=True, theme="streamlit"
    )