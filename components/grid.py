# components/grid.py
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, JsCode
from components.grid_options import configure_column_editors
from components.grid_styles import (
    JS_CHECKBOX_RENDERER, JS_EMPTY_TEXT, JS_ROW_STYLE,
    JS_RISK_CELL_STYLE, JS_PROFIT_STYLE, JS_BID_PERCENT_STYLE,
    JS_STYLE_BAD_YES, JS_STYLE_BAD_NO, JS_STYLE_BAD_COND,
    JS_ACTIONS_RENDERER, JS_NATURAL_SORT, JS_CURRENCY_SORT,
    get_persistence_js
)

COLUMN_BID = "Bid"
COLUMN_BID_PER = "Bid %"
COLUMN_EST_PROFIT = "Est. Profit"

def _hide_utility_cols(gb, columns):
    hidden = [
        "id", "current_bid", "is_hidden", "product_id", "auction_id", 
        "sold_price", "suggested_msrp", "url", "URL",
        "master_msrp", "master_target_price", "profit_val", "MSRP Status", "scraped_category"
    ]
    for col in hidden:
        if col in columns: gb.configure_column(col, hide=True)

def _setup_interaction_cols(gb, columns):
    # === 1. RESTORED: DEDICATED SELECTION COLUMN ===
    if "Select" in columns:
        gb.configure_column("Select", 
            checkboxSelection=True,       # Put checkbox HERE
            headerCheckboxSelection=True, # Select All
            width=50, 
            pinned="left", 
            headerName="",                # Blank Header 
            suppressMenu=True, 
            valueFormatter=JS_EMPTY_TEXT  # Hide "False" text
        )
    
    if "Risk" in columns:
        gb.configure_column("Risk", width=130, pinned="left", cellStyle=JS_RISK_CELL_STYLE)
    
    if "Watch" in columns:
        gb.configure_column("Watch", editable=True, cellRenderer=JS_CHECKBOX_RENDERER, cellEditor='agCheckboxCellEditor', valueFormatter=JS_EMPTY_TEXT, width=60, pinned="left", headerName="⭐")

    if "Actions" in columns:
        gb.configure_column(
            "Actions",
            cellRenderer=JS_ACTIONS_RENDERER,
            editable=False,
            filter=False,
            sortable=False,
            width=70,
            pinned="left",
            headerName="",
            suppressMenu=True
        )

def _setup_metrics_cols(gb, columns):
    if COLUMN_EST_PROFIT in columns:
        gb.configure_column(COLUMN_EST_PROFIT, width=100, cellStyle=JS_PROFIT_STYLE, comparator=JS_CURRENCY_SORT)
    
    if COLUMN_BID_PER in columns:
        gb.configure_column(COLUMN_BID_PER, width=90, cellStyle=JS_BID_PERCENT_STYLE)
        
    if "MSRP" in columns:
        gb.configure_column("MSRP", width=90)

def _setup_widths_and_sorting(gb, columns):
    text_cols = ["Lot", "Title", "Brand", "Model", "UPC", "ASIN", "Category", "Scraped MSRP"]
    for col in text_cols:
        if col in columns: gb.configure_column(col, comparator=JS_NATURAL_SORT)
    
    if COLUMN_BID in columns:
        gb.configure_column(COLUMN_BID, width=100, comparator=JS_CURRENCY_SORT)

    tight_cols = ["Lot", "Packaging", "Condition", "Functional", "Missing Parts", "Damaged", "UPC", "ASIN", "Category"]
    for col in tight_cols:
        if col in columns: gb.configure_column(col, width=110)
        
    if "Title" in columns:
        gb.configure_column("Title", width=300, pinned="left", comparator=JS_NATURAL_SORT, wrapText=True, autoHeight=True)

def _setup_styles(gb, columns):
    if "Functional" in columns: gb.configure_column("Functional", cellStyle=JS_STYLE_BAD_NO)
    if "Condition" in columns: gb.configure_column("Condition", cellStyle=JS_STYLE_BAD_COND)
    for col in ["Damaged", "Missing Parts"]:
        if col in columns: gb.configure_column(col, cellStyle=JS_STYLE_BAD_YES)

def _configure_columns(gb: GridOptionsBuilder, df: pd.DataFrame):
    columns = df.columns
    _hide_utility_cols(gb, columns)
    _setup_interaction_cols(gb, columns)
    _setup_metrics_cols(gb, columns)
    _setup_widths_and_sorting(gb, columns)
    _setup_styles(gb, columns)
    configure_column_editors(gb)

def render_grid(df: pd.DataFrame, height: int = 650, allow_selection: bool = True, grid_key: str = "default", refresh_id: int = 0):
    if df is None or df.empty: return {"selected": [], "data": df}

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, filterable=True, resizable=True, wrapText=True, autoHeight=True)
    gb.configure_grid_options(getRowStyle=JS_ROW_STYLE)
    
    gb.configure_grid_options(enableRangeSelection=True) 
    gb.configure_grid_options(rowSelection='multiple')
    gb.configure_grid_options(onGridReady=get_persistence_js(grid_key))
    
    _configure_columns(gb, df)

    if allow_selection:
        # === FIXED: DISABLE AUTO-CHECKBOX ===
        # We manually configured "Select" column above, so we turn off the auto-one here
        # to prevent it from merging into the Risk column.
        gb.configure_selection(
            selection_mode="multiple", 
            use_checkbox=False,             # <--- FALSE (Use our manual column)
            header_checkbox=False,          # <--- FALSE (Handled by manual column)
            suppressRowClickSelection=True 
        )

    grid_options = gb.build()

    return AgGrid(
        df, 
        gridOptions=grid_options, 
        height=height, 
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED, 
        update_mode=GridUpdateMode.MODEL_CHANGED, 
        allow_unsafe_jscode=True, 
        theme="streamlit",
        key=f"ag_grid_{grid_key}_{refresh_id}",
        reload_data=True
    )
