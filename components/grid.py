# components/grid.py
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode
from components.grid_styles import (
    JS_CHECKBOX_RENDERER, JS_EMPTY_TEXT, JS_ROW_STYLE,
    JS_STYLE_BAD_YES, JS_STYLE_BAD_NO, JS_STYLE_BAD_COND,
    JS_NATURAL_SORT, JS_CURRENCY_SORT
)
from components.grid_options import configure_column_editors

COLUMN_BID = "Bid"

def _configure_columns(gb: GridOptionsBuilder, df: pd.DataFrame):
    columns = df.columns

    # Hide Utility Columns
    for col in ["id", "current_bid", "is_hidden", "product_id", "auction_id"]:
        if col in columns:
            gb.configure_column(col, hide=True)

    # Watch Column
    if "Watch" in columns:
        gb.configure_column("Watch", 
            editable=True, cellRenderer=JS_CHECKBOX_RENDERER, 
            cellEditor='agCheckboxCellEditor', valueFormatter=JS_EMPTY_TEXT, 
            width=60, headerName=" ⭐ "
        )

    # Sorting
    if "Lot" in columns: gb.configure_column("Lot", comparator=JS_NATURAL_SORT)
    if COLUMN_BID in columns: gb.configure_column(COLUMN_BID, width=100, comparator=JS_CURRENCY_SORT)

    # Risk Styles
    if "Functional" in columns: gb.configure_column("Functional", cellStyle=JS_STYLE_BAD_NO)
    if "Condition" in columns: gb.configure_column("Condition", cellStyle=JS_STYLE_BAD_COND)
    for col in ["Damaged", "Missing Parts"]:
        if col in columns: gb.configure_column(col, cellStyle=JS_STYLE_BAD_YES)

    # Editors
    configure_column_editors(gb)


def render_grid(df: pd.DataFrame, height: int = 650, allow_selection: bool = True):
    if df is None or df.empty:
        return {"selected": [], "data": df}

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, filterable=True, resizable=True, wrapText=True, autoHeight=True)
    gb.configure_grid_options(getRowStyle=JS_ROW_STYLE)
    
    # ENABLE EXCEL-STYLE SELECTION
    # This allows you to highlight cells for copy/paste
    gb.configure_grid_options(enableRangeSelection=True) 

    _configure_columns(gb, df)

    if allow_selection:
        gb.configure_selection(
            selection_mode="multiple", 
            use_checkbox=True, 
            header_checkbox=True,
            suppressRowClickSelection=False 
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
    )