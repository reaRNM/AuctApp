# components/filters.py
import streamlit as st
import pandas as pd

# === HELPER: Extract Numeric Bid ===
def get_bid_values(df: pd.DataFrame) -> pd.Series:
    """
    Robustly find bid values. 
    If 'current_bid' (raw) is missing, parse the formatted 'Bid' column ($1,200.00).
    """
    if "current_bid" in df.columns:
        return pd.to_numeric(df["current_bid"], errors="coerce").fillna(0.0)
    
    if "Bid" in df.columns:
        # Remove '$' and ',' then convert to float
        return (
            df["Bid"]
            .astype(str)
            .replace(r"[$,]", "", regex=True)
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0.0)
        )

    
    # Fallback if neither exists
    return pd.Series([0.0] * len(df))
        
        
# === RENDER FILTERS ===
def render_filters(df: pd.DataFrame) -> dict:
    """Render Streamlit filters and return dictionary of selected values."""
    df = df.copy()
    
    bid_values = get_bid_values(df)
    max_val = float(bid_values.max()) if not bid_values.empty else 0.0
    if max_val <= 0: max_val = 1.0 

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1: min_bid = st.slider("Min Bid ($)", 0.0, max_val, 0.0, step=5.0)
    with col2: max_bid = st.slider("Max Bid ($)", 0.0, max_val, max_val, step=5.0)

    # Brand
    brand_col = "Brand" if "Brand" in df.columns else "brand"
    brands = sorted(df[brand_col].dropna().unique().tolist()) if brand_col in df.columns else []
    with col3: selected_brands = st.multiselect("Brand", brands, default=[])

    # Category
    cat_col = "Category" if "Category" in df.columns else "category"
    cats = sorted(df[cat_col].dropna().unique().tolist()) if cat_col in df.columns else []
    with col4: selected_cats = st.multiselect("Category", cats, default=[])

    with col5: show_no_bids = st.checkbox("Show Only No Bids", value=False)
    
    with col6:
        hide_high = st.checkbox("Hide High Risk", value=False)
        hide_med = st.checkbox("Hide Medium Risk", value=False)

    return {
        "min_bid": min_bid,
        "max_bid": max_bid,
        "selected_brands": selected_brands,
        "selected_cats": selected_cats,
        "show_no_bids_only": show_no_bids,
        "hide_high_risk": hide_high,
        "hide_medium_risk": hide_med,
        "brand_col_name": brand_col,
        "cat_col_name": cat_col
    }

# === LOGIC HELPERS ===
def _filter_by_bids(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    bid_values = get_bid_values(df)
    
    if filters.get("show_no_bids_only"):
        return df[bid_values == 0]
    
    min_bid = filters.get("min_bid", 0)
    max_bid = filters.get("max_bid", 0)

    mask = bid_values >= min_bid
    if max_bid > 0:
        mask &= (bid_values <= max_bid)
    
    return df[mask]

def _filter_by_brand(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    brands = filters.get("selected_brands", [])
    brand_col = filters.get("brand_col_name")
    
    if brands and brand_col and brand_col in df.columns:
        return df[df[brand_col].isin(brands)]
    return df

def _filter_by_category(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    cats = filters.get("selected_cats", [])
    cat_col = filters.get("cat_col_name")
    
    if cats and cat_col and cat_col in df.columns:
        return df[df[cat_col].isin(cats)]
    return df

def _filter_by_risk(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    if "Risk" not in df.columns:
        return df
        
    if filters.get("hide_high_risk"):
        df = df[df["Risk"] != "HIGH RISK"]
        
    if filters.get("hide_medium_risk"):
        df = df[df["Risk"] != "MEDIUM RISK"]
        
    return df

# === MAIN APPLY FUNCTION ===
def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply all selected filters to the DataFrame."""
    if df.empty: return df

    filtered = df.copy()
    
    filtered = _filter_by_bids(filtered, filters)
    filtered = _filter_by_brand(filtered, filters)
    filtered = _filter_by_category(filtered, filters)
    filtered = _filter_by_risk(filtered, filters)

    return filtered