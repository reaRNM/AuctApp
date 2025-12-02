# components/grid_options.py

# Define Dropdown Choices
OPT_PACKAGING = ["Yes", "No", "Unknown", "Not in Original", "Damaged"]
OPT_CONDITION = ["Excellent", "New (Other)", "Used", "For Parts Only", "Bad", "Ok", "Unknown"]
OPT_FUNCTIONAL = ["Yes", "No", "Unknown", "Unable to Test"]
OPT_YES_NO = ["Yes", "No", "Unknown"]

# (OPT_CATEGORIES removed since we are using scraped data now)

def configure_column_editors(gb):
    """
    Applies the dropdown editors (SelectCellEditor) to the GridBuilder.
    """
    # Packaging
    gb.configure_column("Packaging", 
        editable=True, 
        cellEditor="agSelectCellEditor", 
        cellEditorParams={"values": OPT_PACKAGING}
    )

    # Condition
    gb.configure_column("Condition", 
        editable=True, 
        cellEditor="agSelectCellEditor", 
        cellEditorParams={"values": OPT_CONDITION}
    )

    # Functional
    gb.configure_column("Functional", 
        editable=True, 
        cellEditor="agSelectCellEditor", 
        cellEditorParams={"values": OPT_FUNCTIONAL}
    )

    # Binary Flags
    for col in ["Damaged", "Missing Parts"]:
        gb.configure_column(col, 
            editable=True, 
            cellEditor="agSelectCellEditor", 
            cellEditorParams={"values": OPT_YES_NO}
        )

    # FIXED: Removed "Category" from this list so it is NOT editable
    text_fields = [
        "Title", "Brand", "Model", "UPC", "ASIN", 
        "Notes", "Missing Parts Desc", "Damaged Desc"
    ]
    for col in text_fields:
        gb.configure_column(col, editable=True)