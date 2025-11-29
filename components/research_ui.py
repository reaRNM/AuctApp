# components/research_ui.py
import streamlit as st


def _get_val(data, key):
    """Helper to handle 0.0 vs None for inputs."""
    val = data.get(key)
    return float(val) if val and float(val) > 0 else None


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
        new_cat = st.text_input("Category", value=product_data.get('category', ''))

    st.markdown("---")
    
    
    # --- TABS FOR RESEARCH ---
    tab_price, tab_ebay, tab_amazon, tab_ship = st.tabs(["💰 Pricing", "🛒 eBay Data", "📦 Amazon Data", "🚚 Shipping"])

    with tab_price:
        p1, p2, p3 = st.columns(3)
        with p1: val_msrp = st.number_input("MSRP ($)", min_value=0.0, value=_get_val(product_data, 'msrp'), step=1.0)
        with p2: val_target = st.number_input("Target Sell Price ($)", min_value=0.0, value=_get_val(product_data, 'target_list_price'), step=1.0)
        with p3: val_avg = st.number_input("Avg History Price ($)", min_value=0.0, value=_get_val(product_data, 'avg_sold_price'), disabled=True) # Read only (calculated)

    with tab_ebay:
        e1, e2 = st.columns([3, 1])
        with e1: val_ebay_url = st.text_input("eBay Link", value=product_data.get('ebay_url', ''))
        with e2: val_sell_through = st.number_input("Sell-Through %", min_value=0.0, value=_get_val(product_data, 'ebay_sell_through'), step=1.0)
        
        e3, e4, e5, e6 = st.columns(4)
        with e3: val_e_act_low = st.number_input("Active Low ($)", value=_get_val(product_data, 'ebay_active_low'))
        with e4: val_e_act_high = st.number_input("Active High ($)", value=_get_val(product_data, 'ebay_active_high'))
        with e5: val_e_sold_low = st.number_input("Sold Low ($)", value=_get_val(product_data, 'ebay_sold_low'))
        with e6: val_e_sold_high = st.number_input("Sold High ($)", value=_get_val(product_data, 'ebay_sold_high'))

    with tab_amazon:
        a1, a2 = st.columns([3, 1])
        with a1: val_amz_url = st.text_input("Amazon Link", value=product_data.get('amazon_url', ''))
        with a2: val_amz_rank = st.number_input("Sales Rank", min_value=0, value=int(product_data.get('amazon_sales_rank') or 0))
        
        a3, a4 = st.columns(2)
        with a3: val_amz_new = st.number_input("Amazon New Price ($)", value=_get_val(product_data, 'amazon_new_price'))
        with a4: val_amz_used = st.number_input("Amazon Used Price ($)", value=_get_val(product_data, 'amazon_used_price'))

    with tab_ship:
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        with s1: val_lbs = st.number_input("Lbs", value=_get_val(product_data, 'weight_lbs'))
        with s2: val_oz = st.number_input("Oz", value=_get_val(product_data, 'weight_oz'))
        with s3: val_l = st.number_input("L", value=_get_val(product_data, 'length'))
        with s4: val_w = st.number_input("W", value=_get_val(product_data, 'width'))
        with s5: val_h = st.number_input("H", value=_get_val(product_data, 'height'))
        with s6: val_irreg = st.checkbox("Irregular?", value=bool(product_data.get('is_irregular')))
        
        st.caption("Shipping Cost Basis")
        val_ship_cost = st.number_input("Est. Shipping Cost ($)", value=_get_val(product_data, 'shipping_cost_basis'))

    return {
        'title': new_title, 'brand': new_brand, 'model': new_model,
        'upc': new_upc, 'asin': new_asin, 'category': new_cat,
        'msrp': val_msrp, 'avg_sold_price': val_avg, 'target_list_price': val_target, 
        'shipping_cost_basis': val_ship_cost,
        'weight_lbs': val_lbs, 'weight_oz': val_oz, 'length': val_l, 'width': val_w, 'height': val_h, 'is_irregular': val_irreg,
        # New Fields
        'ebay_url': val_ebay_url, 'ebay_sell_through': val_sell_through,
        'ebay_active_low': val_e_act_low, 'ebay_active_high': val_e_act_high,
        'ebay_sold_low': val_e_sold_low, 'ebay_sold_high': val_e_sold_high,
        'amazon_url': val_amz_url, 'amazon_sales_rank': val_amz_rank,
        'amazon_new_price': val_amz_new, 'amazon_used_price': val_amz_used
    }