# components/grid_options.py
from utils.parse import (
    OPT_PACKAGING, OPT_CONDITION, OPT_FUNCTIONAL, OPT_RISK, OPT_YES_NO,
    COL_PKG, COL_COND, COL_FUNC, COL_RISK, COL_DMG, COL_MISSING,
    COL_TITLE, COL_BRAND, COL_MODEL, COL_UPC, COL_ASIN, COL_NOTES, 
    COL_MISSING_DESC, COL_DMG_DESC
)

def configure_column_editors(gb):
    """
    Applies the dropdown editors (SelectCellEditor) to the GridBuilder using centralized constants.
    """
    gb.configure_column(COL_PKG, editable=True, cellEditor="agSelectCellEditor", cellEditorParams={"values": OPT_PACKAGING})
    gb.configure_column(COL_COND, editable=True, cellEditor="agSelectCellEditor", cellEditorParams={"values": OPT_CONDITION})
    gb.configure_column(COL_FUNC, editable=True, cellEditor="agSelectCellEditor", cellEditorParams={"values": OPT_FUNCTIONAL})
    gb.configure_column(COL_RISK, editable=True, cellEditor="agSelectCellEditor", cellEditorParams={"values": OPT_RISK})
    
    # Binary Flags
    for col in [COL_DMG, COL_MISSING]:
        gb.configure_column(col, editable=True, cellEditor="agSelectCellEditor", cellEditorParams={"values": OPT_YES_NO})

    # Free Text Fields
    text_fields = [
        COL_TITLE, COL_BRAND, COL_MODEL, COL_UPC, COL_ASIN, 
        COL_NOTES, COL_MISSING_DESC, COL_DMG_DESC
    ]
    for col in text_fields:
        gb.configure_column(col, editable=True)