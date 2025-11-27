# components/research_ui.py
import streamlit as st
from components.grid_options import OPT_CATEGORIES

def render_product_form_fields(product_data: dict):
    """
    Renders the input fields for the Product Research form.
    Returns a dictionary of the user's inputs.
    """
    # --- SECTION 1: IDENTITY ---
    st.markdown("#### 1. Product Identity (Master Record)")
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1: new_title = st.text_input("Clean Title", value=product_data.get('title', ''))
    with c2: new_brand = st.text_input("Brand", value=product_data.get('brand', ''))
    with c3: new_model = st.text_input("Model", value=product_data.get('model', ''))

    c4, c5, c6 = st.columns(3)
    with c4: new_upc = st.text_input("UPC", value=product_data.get('upc', ''))
    with c5: new_asin = st.text_input("ASIN", value=product_data.get('asin', ''))
    
    with c6: 
        curr_cat = product_data.get('category')
        # Default to "Other" if category is missing or invalid
        idx = OPT_CATEGORIES.index(curr_cat) if curr_cat in OPT_CATEGORIES else OPT_CATEGORIES.index("Other")
        new_cat = st.selectbox("Category", OPT_CATEGORIES, index=idx)

    # --- SECTION 2: PRICING ---
    st.markdown("#### 2. Pricing Research")
    p1, p2, p3, p4 = st.columns(4)
    raw_msrp = product_data.get('msrp')
    val_msrp_input = float(raw_msrp) if raw_msrp and float(raw_msrp) > 0 else None

    raw_avg = product_data.get('avg_sold_price')
    val_avg_input = float(raw_avg) if raw_avg and float(raw_avg) > 0 else None

    raw_target = product_data.get('target_list_price')
    val_target_input = float(raw_target) if raw_target and float(raw_target) > 0 else None

    raw_ship = product_data.get('shipping_cost_basis')
    val_ship_input = float(raw_ship) if raw_ship and float(raw_ship) > 0 else None
    with p1: val_msrp = st.number_input("MSRP ($)", min_value=0.0, value=val_msrp_input, step=1.0, placeholder="0.00")
    with p2: val_avg = st.number_input("Avg Sold Price ($)", min_value=0.0, value=val_avg_input, step=1.0, placeholder="0.00")
    with p3: val_target = st.number_input("Target List Price ($)", min_value=0.0, value=val_target_input, step=1.0, placeholder="0.00")
    with p4: val_ship_cost = st.number_input("Est. Ship Cost ($)", min_value=0.0, value=val_ship_input, step=0.5, placeholder="0.00")
    
    
    # --- SECTION 3: LOGISTICS ---
    st.markdown("#### 3. Shipping Logistics")
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    with s1: val_lbs = st.number_input("Lbs", min_value=0.0, value=float(product_data.get('weight_lbs') or 0.0), step=1.0)
    with s2: val_oz = st.number_input("Oz", min_value=0.0, value=float(product_data.get('weight_oz') or 0.0), step=1.0)
    with s3: val_l = st.number_input("L (in)", min_value=0.0, value=float(product_data.get('length') or 0.0))
    with s4: val_w = st.number_input("W (in)", min_value=0.0, value=float(product_data.get('width') or 0.0))
    with s5: val_h = st.number_input("H (in)", min_value=0.0, value=float(product_data.get('height') or 0.0))
    with s6: val_irreg = st.checkbox("Irregular?", value=bool(product_data.get('is_irregular')))

    # Return structured data
    return {
        'title': new_title, 'brand': new_brand, 'model': new_model,
        'upc': new_upc, 'asin': new_asin, 'category': new_cat,
        'msrp': val_msrp, 'avg_sold_price': val_avg, 
        'target_list_price': val_target, 'shipping_cost_basis': val_ship_cost,
        'weight_lbs': val_lbs, 'weight_oz': val_oz, 
        'length': val_l, 'width': val_w, 'height': val_h, 
        'is_irregular': val_irreg
    }