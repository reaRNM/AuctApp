# components/grid_options.py

# Define Dropdown Choices
OPT_PACKAGING = ["Yes", "No", "Unknown", "Not in Original", "Damaged"]
OPT_CONDITION = ["Excellent", "New (Other)", "Used", "For Parts Only", "Bad", "Ok", "Unknown"]
OPT_FUNCTIONAL = ["Yes", "No", "Unknown", "Unable to Test"]
OPT_YES_NO = ["Yes", "No", "Unknown"]

# Product Categories
OPT_CATEGORIES = [
    "Fashion & Accessories - Clothing (men, women, kids)",
    "Fashion & Accessories - Shoes",
    "Fashion & Accessories - Jewelry",
    "Fashion & Accessories - Watches",
    "Fashion & Accessories - Bags & luggage",
    "Fashion & Accessories - Makeup & beauty",
    "Fashion & Accessories - Hair products",
    "Fashion & Accessories - Hygiene",
    "Fashion & Accessories - Other",
    
    "Electronics & Technology - Computers & cellphones",
    "Electronics & Technology - Accessories",
    "Electronics & Technology - Wearable tech",
    "Electronics & Technology - Office electronics",
    "Electronics & Technology - Cameras & photo",
    "Electronics & Technology - Audio equipment",
    "Electronics & Technology - Other gadgets",
    
    "Smart Home & Appliances - Lighting",
    "Smart Home & Appliances - Security (Locks/Cameras)",
    "Smart Home & Appliances - Heating & cooling",
    "Smart Home & Appliances - Cleaning devices",
    "Smart Home & Appliances - Kitchen appliances",
    "Smart Home & Appliances - Other",
    
    "Home, Garden & Tools - Furniture",
    "Home, Garden & Tools - Décor & art",
    "Home, Garden & Tools - Crafts & DIY",
    "Home, Garden & Tools - Mattresses & bedding",
    "Home, Garden & Tools - Storage & organization",
    "Home, Garden & Tools - Kitchenware",
    "Home, Garden & Tools - Garden tools",
    "Home, Garden & Tools - Auto parts",
    "Home, Garden & Tools - Tools & machinery",
    "Home, Garden & Tools - Office supplies",
    "Home, Garden & Tools - Sporting goods",
    "Home, Garden & Tools - Outdoor gear",
    "Home, Garden & Tools - Pet supplies",
    
    "Baby & Children - Essentials",
    "Baby & Children - Toys & games",
    "Baby & Children - Clothing",
    
    "Other"
]

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

    # FIXED: Re-enabled editing for Identity Fields (Title, Brand, etc.)
    # This allows you to clean data directly in the Viewer grid.
    text_fields = [
        "Title", "Brand", "Model", "UPC", "ASIN",
        "Notes", "Missing Parts Desc", "Damaged Desc"
    ]
    for col in text_fields:
        gb.configure_column(col, editable=True)