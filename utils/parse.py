# utils/parse.py
import re
import pandas as pd

def normalize_value(val: str) -> str:
    val = str(val).strip().lower()
    if val in ["yes", "y", "true"]: return "Yes"
    if val in ["no", "n", "false"]: return "No"
    if "unknown" in val: return "Unknown"
    if "unable" in val or "untested" in val: return "Unable To Test"
    return val.title()

def classify_risk(row: pd.Series) -> str:
    # Normalize
    cond = str(row.get("condition", "")).strip().lower()
    func = str(row.get("functional", "")).strip().lower()
    miss = str(row.get("missing_parts", "")).strip().lower()
    dmg  = str(row.get("damaged", "")).strip().lower()
    pack = str(row.get("packaging", "")).strip().lower()
    
    # Parse Bid
    raw_bid = row.get("current_bid", 0)
    try:
        bid_val = float(str(raw_bid).replace("$", "").replace(",", ""))
    except (ValueError, TypeError):
        bid_val = 0.0

    # 1. HIGH RISK
    if (
        cond == "for parts only" or
        func == "no" or
        "yes" in miss or
        "yes" in dmg
    ):
        return "HIGH RISK"

    # 2. MEDIUM RISK
    if (
        "no" in pack or
        cond == "used" or
        "unable" in func or "unknown" in func or
        "unknown" in miss or
        "unknown" in dmg
    ):
        return "MEDIUM RISK"

    # 3. NO BIDS
    # Uses accurate 0.00 from new scraper logic
    if bid_val <= 0:
        return "NO BIDS"

    return ""