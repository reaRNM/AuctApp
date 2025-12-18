# utils/parse.py
import pandas as pd
import re

# === PAGE PATHS ===
PAGE_ACTIVE = "pages/1_Active_Viewer.py"
PAGE_LIBRARY = "pages/2_Product_Library.py"
PAGE_HISTORY = "pages/3_Auction_History.py"
PAGE_CLEANUP = "pages/4_Database_Cleanup.py"
PAGE_INVENTORY = "pages/5_My_Inventory.py"

# === COLUMN HEADERS (DISPLAY & SCRAPER KEYS) ===
# These are used for Grid Headers and Scraper Dictionary Keys
COL_SELECT = "Select"
COL_WATCH = "Watch"
COL_WON = "Won?"
COL_RISK = "Risk"
COL_FAV = "Favorite"

# Identification
COL_LOT = "Lot"
COL_TITLE = "Title"
COL_PRD_TITLE = "Product Title"
COL_BRAND = "Brand"
COL_MODEL = "Model"
COL_CAT = "Category"
COL_UPC = "UPC"
COL_ASIN = "ASIN"
COL_URL = "URL"

# Condition & Notes
COL_PKG = "Packaging"
COL_COND = "Condition"
COL_FUNC = "Functional"
COL_MISSING = "Missing Parts"
COL_MISSING_DESC = "Missing Parts Desc"
COL_DMG = "Damaged"
COL_DMG_DESC = "Damaged Desc"
COL_NOTES = "Notes" # Scraper output key

# Pricing & Profit
COL_MSRP = "MSRP"
COL_MSRP_STAT = "MSRP Status"
COL_BID = "Bid"
COL_CUR_BID = "Current Bid"
COL_TARGET = "Target List Price"
COL_EST_PROFIT = "Est. Profit"
COL_SOLD = "Sold Price"
COL_AVG_SOLD = "Avg Sold"
COL_PROFIT_REALIZED = "Realized Profit"
COL_TOTAL_COST = "Total Cost"
COL_STATUS = "Status"
COL_DATE = "Date"
COL_SOURCE = "Source"
COL_PURCHASE = "Purchase Price"  # NEW
COL_LISTING = "Listing Price"    # NEW

# === DATABASE KEYS (Internal Table Column Names) ===
# Core
KEY_DB_TITLE = "title"
KEY_DB_BRAND = "brand"
KEY_DB_MODEL = "model"
KEY_DB_UPC = "upc"
KEY_DB_ASIN = "asin"
KEY_DB_CAT = "category"
KEY_DB_MSRP = "msrp"
KEY_DB_AVG_SOLD = "avg_sold_price"
KEY_DB_TARGET = "target_list_price"
KEY_SHIP_COST = "shipping_cost_basis"
KEY_DB_PROD_NOTES = "notes" # Product table notes
KEY_IS_FAV = "is_favorite"

# Auction Items Specific
KEY_DB_PKG = "packaging"
KEY_DB_COND = "condition"
KEY_DB_FUNC = "functional"
KEY_DB_MISSING = "missing_parts"
KEY_DB_MISSING_DESC = "missing_parts_desc"
KEY_DB_DMG = "damaged"
KEY_DB_DMG_DESC = "damage_desc"
KEY_DB_ITEM_NOTES = "item_notes" # Auction Item table notes
KEY_DB_URL = "url"
KEY_DB_SCRAPED_CAT = "scraped_category"

# Physical Specs
KEY_WEIGHT_LBS = "weight_lbs"
KEY_WEIGHT_OZ = "weight_oz"
KEY_LENGTH = "length"
KEY_WIDTH = "width"
KEY_HEIGHT = "height"
KEY_IRREGULAR = "is_irregular"

# eBay Data
KEY_EBAY_AVG_SOLD = "ebay_avg_sold_price"
KEY_EBAY_SOLD_LOW = "ebay_sold_range_low"
KEY_EBAY_SOLD_HIGH = "ebay_sold_range_high"
KEY_EBAY_AVG_SHIP = "ebay_avg_shipping_sold"
KEY_EBAY_STR = "ebay_sell_through_rate"
KEY_EBAY_SOLD_COUNT = "ebay_total_sold_count"
KEY_EBAY_SELLERS = "ebay_total_sellers"
KEY_EBAY_ACTIVE_CNT = "ebay_active_count"
KEY_EBAY_LIST_AVG = "ebay_avg_list_price"
KEY_EBAY_ACTIVE_LOW = "ebay_active_low"
KEY_EBAY_ACTIVE_HIGH = "ebay_active_high"
KEY_EBAY_ACTIVE_SHIP = "ebay_avg_shipping_active"
KEY_EBAY_WATCHERS = "ebay_num_watchers"
KEY_MKT_NOTES = "market_notes"

# Amazon Data
KEY_AMZ_URL = "amazon_url"
KEY_AMZ_NEW = "amazon_new_price"
KEY_AMZ_USED = "amazon_used_price"
KEY_AMZ_LIST = "amazon_listing_price"
KEY_AMZ_RANK = "amazon_sales_rank"
KEY_AMZ_REVS = "amazon_reviews"
KEY_AMZ_STARS = "amazon_stars"
KEY_AMZ_RANK_MAIN = "amazon_rank_main"
KEY_AMZ_CAT_MAIN = "amazon_cat_name"
KEY_AMZ_RANK_SUB = "amazon_rank_sub"
KEY_AMZ_CAT_SUB = "amazon_subcat_name"

# Other Internal Keys
KEY_MASTER_MSRP = "master_msrp"
KEY_SUG_MSRP = "suggested_msrp" # This replaces COL_SUG_MSRP
KEY_WORK_MSRP = "working_msrp"
KEY_TARGET_PRICE = "master_target_price"
KEY_PROFIT_VAL = "profit_val"
KEY_CURRENT_BID = "current_bid"
KEY_SOLD_PRICE = "sold_price"
KEY_IS_HIDDEN = "is_hidden"
KEY_IS_WATCHED = "is_watched"
KEY_IS_WON = "is_won"
KEY_PROD_ID = "product_id"
KEY_AUC_ID = "auction_id"
KEY_EST_PROFIT = "est_profit"
KEY_STATUS = "status"

# AI/Scraper Keys
KEY_SCRAPED_MSRP = "Scraped MSRP"
KEY_SCRAPED_CAT = "scraped_category"

# === DROPDOWN OPTIONS ===
OPT_PACKAGING = ["Yes", "No", "Unknown", "Not in Original", "Open Box - Tested", "Damaged"]
OPT_CONDITION = ["Excellent", "New (Other)", "Used", "For Parts Only", "Bad", "Ok", "Unknown"]
OPT_FUNCTIONAL = ["Yes", "No", "Unknown", "Unable to Test"]
OPT_YES_NO = ["Yes", "No", "Unknown"]
OPT_RISK = ["HIGH RISK", "MEDIUM RISK", "NO BIDS", ""]

# === LOGIC FUNCTIONS ===
def normalize_value(val: str) -> str:
    val = str(val).strip().lower()
    if val in ["yes", "y", "true"]: return "Yes"
    if val in ["no", "n", "false"]: return "No"
    if "unknown" in val: return "Unknown"
    if "unable" in val or "untested" in val: return "Unable To Test"
    return val.title()

def classify_risk(row: pd.Series) -> str:
    # Use keys that match the DataFrame columns (usually lowercase DB keys)
    cond = str(row.get(KEY_DB_COND, "")).strip().lower()
    func = str(row.get(KEY_DB_FUNC, "")).strip().lower()
    miss = str(row.get(KEY_DB_MISSING, "")).strip().lower()
    dmg  = str(row.get(KEY_DB_DMG, "")).strip().lower()
    pack = str(row.get(KEY_DB_PKG, "")).strip().lower()
    
    raw_bid = row.get(KEY_CURRENT_BID, 0)
    try:
        bid_val = float(str(raw_bid).replace("$", "").replace(",", ""))
    except (ValueError, TypeError):
        bid_val = 0.0

    if (cond == "for parts only" or func == "no" or "yes" in miss or "yes" in dmg):
        return "HIGH RISK"

    if ("no" in pack or cond == "used" or "unable" in func or "unknown" in func or "unknown" in miss or "unknown" in dmg):
        return "MEDIUM RISK"

    if bid_val <= 0:
        return "NO BIDS"

    return ""