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
    
    # 1. Calculate Max Bid safely
    bid_values = get_bid_values(df)
    max_val = float(bid_values.max()) if not bid_values.empty else 0.0
    
    # PREVENT CRASH: Ensure slider max > min
    if max_val <= 0:
        max_val = 1.0 

    col1, col2, col3, col4, col5 = st.columns(5)

    # --- Min Bid ---
    with col1:
        min_bid = st.slider("Min Bid ($)", 0.0, max_val, 0.0, step=5.0)

    # --- Max Bid ---
    with col2:
        max_bid_filter = st.slider("Max Bid ($)", 0.0, max_val, max_val, step=5.0)

    # --- Brand Dropdown ---
    # Check for "Brand" (Capitalized) or "brand" (lowercase)
    brand_col = "Brand" if "Brand" in df.columns else "brand"
    
    with col3:
        brands = []
        if brand_col in df.columns:
            brands = sorted(df[brand_col].dropna().unique().tolist())
        selected_brands = st.multiselect("Brand", brands, default=[])

    # --- Show Only No Bids ---
    with col4:
        show_no_bids_only = st.checkbox("Show Only No Bids", value=False)

    # --- Hide Risks ---
    with col5:
        hide_high_risk = st.checkbox("Hide High Risk", value=False)
        hide_medium_risk = st.checkbox("Hide Medium Risk", value=False)

    return {
        "min_bid": min_bid,
        "max_bid": max_bid_filter,
        "selected_brands": selected_brands,
        "show_no_bids_only": show_no_bids_only,
        "hide_high_risk": hide_high_risk,
        "hide_medium_risk": hide_medium_risk,
        "brand_col_name": brand_col # Pass this along so we know which column to filter
    }


# === APPLY FILTERS ===
def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply all selected filters to the DataFrame."""
    if df.empty:
        return df

    filtered = df.copy()
    bid_values = get_bid_values(filtered)

    # --- Show only "No Bids" ---
    if filters.get("show_no_bids_only"):
        # Keep rows where bid is effectively 0
        filtered = filtered[bid_values == 0]
    else:
        # --- Min / Max bid filters ---
        min_bid = filters.get("min_bid", 0)
        max_bid = filters.get("max_bid", 0)

        if min_bid > 0:
            filtered = filtered[bid_values >= min_bid]
        
        # Only apply max filter if it's not the default fallback
        if max_bid > 0:
             filtered = filtered[bid_values <= max_bid]

    # --- Brand filter ---
    brands = filters.get("selected_brands", [])
    brand_col = filters.get("brand_col_name")
    
    if brands and brand_col and brand_col in filtered.columns:
        filtered = filtered[filtered[brand_col].isin(brands)]

    # --- Risk filters (Only if column exists) ---
    if "Risk" in filtered.columns:
        if filters.get("hide_high_risk"):
            filtered = filtered[filtered["Risk"] != "HIGH RISK"]
        if filters.get("hide_medium_risk"):
            filtered = filtered[filtered["Risk"] != "MEDIUM RISK"]

    return filtered