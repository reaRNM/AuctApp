# components/grid.py
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, JsCode, ColumnsAutoSizeMode
from components.grid_options import configure_column_editors
from components.grid_styles import (
    JS_CHECKBOX_RENDERER, JS_EMPTY_TEXT, JS_ROW_STYLE,
    JS_RISK_CELL_STYLE, JS_PROFIT_STYLE,
    JS_STYLE_MED_PACKAGING, JS_STYLE_MED_COND, JS_STYLE_MED_FUNC, JS_STYLE_MED_UNKNOWN,
    JS_NATURAL_SORT, JS_CURRENCY_SORT, JS_MSRP_STYLE,
    get_persistence_js
)

# === CONSTANTS ===
COLUMN_BID = "Bid"
COLUMN_EST_PROFIT = "Est. Profit"
COLUMN_MSRP = "MSRP"
COL_MISSING = "Missing Parts"
COL_DAMAGED = "Damaged"

def _hide_utility_cols(gb, columns):
    hidden = [
        "id", "current_bid", "is_hidden", "product_id", "auction_id", 
        "sold_price", "suggested_msrp", "url", "URL",
        "master_msrp", "master_target_price", "profit_val", "MSRP Status", "scraped_category"
    ]
    for col in hidden:
        if col in columns: gb.configure_column(col, hide=True)

def _setup_interaction_cols(gb, columns):
    if "Select" in columns:
        gb.configure_column("Select", 
            checkboxSelection=True, 
            headerCheckboxSelection=True,
            width=50, 
            pinned="left", 
            headerName="", 
            suppressMenu=True, 
            valueFormatter=JS_EMPTY_TEXT
        )
    if "Risk" in columns:
         gb.configure_column("Risk", width=130, pinned="left", cellStyle=JS_RISK_CELL_STYLE)
    if "Watch" in columns:
        gb.configure_column("Watch", editable=True, cellRenderer=JS_CHECKBOX_RENDERER, cellEditor='agCheckboxCellEditor', valueFormatter=JS_EMPTY_TEXT, width=60, pinned="left", headerName="⭐")

def _setup_metrics_cols(gb, columns):
    if COLUMN_EST_PROFIT in columns:
        gb.configure_column(COLUMN_EST_PROFIT, width=85, cellStyle=JS_PROFIT_STYLE, comparator=JS_CURRENCY_SORT)
        
    if COLUMN_MSRP in columns:
        gb.configure_column(COLUMN_MSRP, width=80, comparator=JS_CURRENCY_SORT, cellStyle=JS_MSRP_STYLE, 
                            type=["numericColumn", "numberColumnFilter"], 
                            valueFormatter="x > 0 ? '$' + x.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : ''")

def _setup_widths_and_sorting(gb, columns):
    # FIXED: Remove Custom Sorting for simple text columns
    
    if COLUMN_BID in columns:
        gb.configure_column(COLUMN_BID, width=80, pinned="left", comparator=JS_CURRENCY_SORT)
        
    if "Lot" in columns:
        gb.configure_column("Lot", width=80, pinned="left")
    
    if "Title" in columns:
        gb.configure_column("Title", autoWidth=True, pinned="left", sortable=True, wrapText=False, autoHeight=True)
    

    tight_cols = ["Packaging", "Condition", "Functional", COL_MISSING, COL_DAMAGED, "UPC", "ASIN", "Category"]
    for col in tight_cols:
        if col in columns: gb.configure_column(col, width=110)

def _setup_styles(gb, columns):
    if "Functional" in columns: gb.configure_column("Functional", cellStyle=JS_STYLE_MED_FUNC)
    if "Condition" in columns: gb.configure_column("Condition", cellStyle=JS_STYLE_MED_COND)
    if "Packaging" in columns: gb.configure_column("Packaging", cellStyle=JS_STYLE_MED_PACKAGING)
    
    for col in [COL_DAMAGED, COL_MISSING]:
        if col in columns: gb.configure_column(col, cellStyle=JS_STYLE_MED_UNKNOWN)

def _configure_columns(gb: GridOptionsBuilder, df: pd.DataFrame):
    columns = df.columns
    _hide_utility_cols(gb, columns)
    _setup_interaction_cols(gb, columns)
    _setup_metrics_cols(gb, columns)
    _setup_widths_and_sorting(gb, columns)
    _setup_styles(gb, columns)
    configure_column_editors(gb)

def render_grid(df: pd.DataFrame, height: int = 650, allow_selection: bool = True, grid_key: str = "default", refresh_id: int = 0):
    if df is None: return None

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        sortable=True, 
        filterable=True, 
        resizable=True, 
        wrapText=True, 
        autoHeight=True,
        flex=1
    )
    
    gb.configure_grid_options(getRowStyle=JS_ROW_STYLE)
    gb.configure_grid_options(enableRangeSelection=True) 
    gb.configure_grid_options(rowSelection='multiple')
    
    key_suffix = f"{len(df)}_{refresh_id}" 
    gb.configure_grid_options(onGridReady=get_persistence_js(grid_key))
    gb.configure_grid_options(domLayout='normal') 
    
    _configure_columns(gb, df)

    if allow_selection:
        gb.configure_selection(
            selection_mode="multiple", 
            use_checkbox=False,
            rowMultiSelectWithClick=True,
            header_checkbox=False
        )

    grid_options = gb.build()

    # FIXED: Added SELECTION_CHANGED to update_mode
    return AgGrid(
        df, 
        gridOptions=grid_options, 
        height=height, 
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED, 
        update_mode=GridUpdateMode.MODEL_CHANGED | GridUpdateMode.SELECTION_CHANGED, 
        allow_unsafe_jscode=True, 
        theme="streamlit",
        key=f"ag_grid_{grid_key}_{key_suffix}",
        reload_data=True,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS 
    )