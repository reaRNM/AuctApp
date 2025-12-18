# components/grid.py
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, JsCode, ColumnsAutoSizeMode
from components.grid_options import configure_column_editors
from components.grid_styles import (
    JS_CHECKBOX_RENDERER, JS_EMPTY_TEXT, JS_ROW_STYLE,
    JS_RISK_CELL_STYLE, JS_PROFIT_STYLE, JS_MSRP_STYLE,
    JS_STYLE_CONDITION, JS_STYLE_FUNCTIONAL, JS_STYLE_PACKAGING, JS_STYLE_BINARY_FLAG,
    JS_NATURAL_SORT, JS_CURRENCY_SORT, get_persistence_js
)
# UPDATED IMPORTS: Removed COL_SCRP_MSRP, Added Keys
from utils.parse import (
    COL_BID, COL_EST_PROFIT, COL_MSRP, COL_MISSING, COL_DMG,
    COL_TITLE, COL_BRAND, COL_MODEL, COL_UPC, COL_ASIN, COL_CAT,
    COL_LOT, COL_PKG, COL_COND, COL_FUNC, COL_RISK, COL_WATCH, COL_SELECT, COL_WON,
    COL_MSRP_STAT,
    # Keys for hiding columns
    KEY_CURRENT_BID, KEY_IS_HIDDEN, KEY_PROD_ID, KEY_AUC_ID, KEY_SOLD_PRICE,
    KEY_SUG_MSRP, KEY_MASTER_MSRP, KEY_TARGET_PRICE, KEY_PROFIT_VAL,
    KEY_SCRAPED_CAT, KEY_IS_WON
)


# === RENDERERS ==="
def _hide_utility_cols(gb, columns):
    # UPDATED: Uses Constants instead of hardcoded strings
    hidden = [
        "id", 
        KEY_CURRENT_BID, KEY_IS_HIDDEN, KEY_PROD_ID, KEY_AUC_ID, 
        KEY_SOLD_PRICE, KEY_SUG_MSRP, 
        "url", "URL", # Keeping these as strings since they vary by source
        KEY_MASTER_MSRP, KEY_TARGET_PRICE, KEY_PROFIT_VAL, 
        COL_MSRP_STAT, KEY_SCRAPED_CAT, KEY_IS_WON
    ]
    for col in hidden:
        if col in columns: gb.configure_column(col, hide=True)

def _setup_interaction_cols(gb, columns):
    if COL_SELECT in columns:
        gb.configure_column(COL_SELECT, checkboxSelection=True, headerCheckboxSelection=True, width=50, pinned="left", headerName="", suppressMenu=True, valueFormatter=JS_EMPTY_TEXT)
    if COL_RISK in columns:
         gb.configure_column(COL_RISK, width=130, pinned="left", cellStyle=JS_RISK_CELL_STYLE)
    if COL_WATCH in columns:
        gb.configure_column(COL_WATCH, editable=True, cellRenderer=JS_CHECKBOX_RENDERER, cellEditor='agCheckboxCellEditor', valueFormatter=JS_EMPTY_TEXT, width=60, pinned="left", headerName="⭐")
    if COL_WON in columns:
        gb.configure_column(COL_WON, editable=True, cellRenderer=JS_CHECKBOX_RENDERER, cellEditor='agCheckboxCellEditor', valueFormatter=JS_EMPTY_TEXT, width=60, pinned="left", headerName="🏆")

def _setup_metrics_cols(gb, columns):
    if COL_EST_PROFIT in columns:
        gb.configure_column(COL_EST_PROFIT, width=85, cellStyle=JS_PROFIT_STYLE, comparator=JS_CURRENCY_SORT)
    if COL_MSRP in columns:
        gb.configure_column(COL_MSRP, width=80, comparator=JS_CURRENCY_SORT, cellStyle=JS_MSRP_STYLE, type=["numericColumn", "numberColumnFilter"], valueFormatter="x > 0 ? '$' + x.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : ''")
    if COL_BID in columns:
        gb.configure_column(COL_BID, width=80, comparator=JS_CURRENCY_SORT)

def _setup_widths_and_sorting(gb, columns):
    if COL_TITLE in columns:
        gb.configure_column(COL_TITLE, autoWidth=True, pinned="left", sortable=True, wrapText=True, autoHeight=True)
    
    tight_cols = [COL_LOT, COL_PKG, COL_COND, COL_FUNC, COL_MISSING, COL_DMG, COL_UPC, COL_ASIN, COL_CAT]
    for col in tight_cols: 
        if col in columns: gb.configure_column(col, width=110)
        
def _setup_styles(gb, columns):
    # UPDATED: Use the unified styles that handle both RED and ORANGE
    if COL_FUNC in columns: gb.configure_column(COL_FUNC, cellStyle=JS_STYLE_FUNCTIONAL)
    if COL_COND in columns: gb.configure_column(COL_COND, cellStyle=JS_STYLE_CONDITION)
    if COL_PKG in columns: gb.configure_column(COL_PKG, cellStyle=JS_STYLE_PACKAGING)
    
    for col in [COL_DMG, COL_MISSING]:
        if col in columns: gb.configure_column(col, cellStyle=JS_STYLE_BINARY_FLAG)

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
    gb.configure_default_column(sortable=True, filterable=True, resizable=True, wrapText=True, autoHeight=True, flex=1)
    
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
            header_checkbox=False,
            suppressRowClickSelection=False,
            rowMultiSelectWithClick=True
        )

    grid_options = gb.build()

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