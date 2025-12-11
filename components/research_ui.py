# components/research_ui.py
import streamlit as st
from utils.shipping import estimate_shipping

def _get_val(data, key):
    """Helper to handle 0.0 vs None for inputs."""
    val = data.get(key)
    return float(val) if val and float(val) > 0 else None

def render_product_form_fields(product_data: dict):
    """
    Renders the new 3-Tab Research Interface.
    Returns a dictionary of the user's inputs.
    """
    
    # --- HEADER ---
    c1, c2, c3 = st.columns([4, 2, 1])
    with c1: new_title = st.text_input("Product Title", value=product_data.get('title', ''))
    with c2: new_brand = st.text_input("Brand", value=product_data.get('brand', ''))
    with c3: new_model = st.text_input("Model", value=product_data.get('model', ''))
    
    st.markdown("---")
    
    # --- TABS ---
    tab_specs, tab_market, tab_profit = st.tabs(["📦 Specs & Identity", "📊 Market Data (Terapeak)", "💰 Valuation"])

    # === TAB 1: SPECS & AMAZON ===
    with tab_specs:
        col_id1, col_id2 = st.columns(2)
        with col_id1: new_upc = st.text_input("UPC", value=product_data.get('upc', ''))
        with col_id2: new_asin = st.text_input("ASIN", value=product_data.get('asin', ''))
        
        st.divider()
        st.caption("Physical Attributes (Calculates Shipping)")
        
        # 1. INPUTS
        c_wt, c_dim = st.columns(2)
        with c_wt:
            w1, w2 = st.columns(2)
            with w1: val_lbs = st.number_input("Lbs", min_value=0.0, value=_get_val(product_data, 'weight_lbs'))
            with w2: val_oz = st.number_input("Oz", min_value=0.0, value=_get_val(product_data, 'weight_oz'))
        with c_dim:
            d1, d2, d3 = st.columns(3)
            with d1: val_l = st.number_input("L", value=_get_val(product_data, 'length'))
            with d2: val_w = st.number_input("W", value=_get_val(product_data, 'width'))
            with d3: val_h = st.number_input("H", value=_get_val(product_data, 'height'))

        # 2. LIVE CALCULATION (NEW VISUAL)
        live_ship = estimate_shipping(val_lbs or 0, val_oz or 0, val_l or 0, val_w or 0, val_h or 0)
        
        if live_ship > 0:
            st.info(f"🚚 **Estimated Zone 9 Shipping:** ${live_ship:.2f}")
        elif (val_lbs or 0) + (val_oz or 0) > 0:
            st.warning("⚠️ Item may be too heavy/large for standard Ground shipping.")

        st.divider()
        st.caption("Amazon Intelligence")
        a1, a2 = st.columns([1, 2])
        with a1: val_amz_stars = st.number_input("Stars (0-5)", min_value=0.0, max_value=5.0, value=_get_val(product_data, 'amazon_stars'))
        with a2: val_amz_reviews = st.number_input("Num Reviews", min_value=0, value=int(product_data.get('amazon_reviews') or 0))
        
        st.write("") # Spacing
        ar1, ar2 = st.columns([1, 2])
        with ar1: val_amz_rank_m = st.number_input("Main Rank #", min_value=0, value=int(product_data.get('amazon_rank_main') or 0))
        with ar2: val_amz_cat_m = st.text_input("Main Category Name", value=product_data.get('amazon_cat_name', ''), placeholder="e.g. Office Products")
        
        ar3, ar4 = st.columns([1, 2])
        with ar3: val_amz_rank_s = st.number_input("Sub Rank #", min_value=0, value=int(product_data.get('amazon_rank_sub') or 0))
        with ar4: val_amz_cat_s = st.text_input("Sub Category Name", value=product_data.get('amazon_subcat_name', ''), placeholder="e.g. Inkjet Printers")

    # === TAB 2: MARKET DATA (EBAY) ===
    with tab_market:
        st.caption("eBay SOLD Data (The Realized Value)")
        e1, e2, e3, e4 = st.columns(4)
        with e1: val_e_avg_sold = st.number_input("Avg Sold ($)", value=_get_val(product_data, 'ebay_avg_sold_price'))
        with e2: val_e_avg_ship = st.number_input("Avg Ship ($)", value=_get_val(product_data, 'ebay_avg_shipping_sold'))
        with e3: val_e_str = st.number_input("Sell-Through %", value=_get_val(product_data, 'ebay_sell_through_rate'))
        with e4: val_e_total_sold = st.number_input("Total Sold Count", value=int(product_data.get('ebay_total_sold_count') or 0))
        
        c_rng1, c_rng2 = st.columns(2)
        with c_rng1: val_e_low = st.number_input("Sold Range Low", value=_get_val(product_data, 'ebay_sold_range_low'))
        with c_rng2: val_e_high = st.number_input("Sold Range High", value=_get_val(product_data, 'ebay_sold_range_high'))

        st.divider()
        st.caption("eBay ACTIVE Data (The Competition)")
        ea1, ea2, ea3 = st.columns(3)
        with ea1: val_e_active_cnt = st.number_input("Active Listings Count", value=int(product_data.get('ebay_active_count') or 0))
        with ea2: val_e_list_avg = st.number_input("Avg List Price ($)", value=_get_val(product_data, 'ebay_avg_list_price'))
        with ea3: val_e_active_ship = st.number_input("Active Avg Ship ($)", value=_get_val(product_data, 'ebay_avg_shipping_active'))
        
        ea4, ea5 = st.columns(2)
        with ea4: val_e_act_low = st.number_input("Active Range Low ($)", value=_get_val(product_data, 'ebay_active_low'))
        with ea5: val_e_act_high = st.number_input("Active Range High ($)", value=_get_val(product_data, 'ebay_active_high'))
        
        val_mkt_notes = st.text_area("Market Notes (e.g. 'Most sold in $100-120 range')", value=product_data.get('market_notes', ''))

    # === TAB 3: VALUATION ===
    with tab_profit:
        st.info("Set your 'Target' based on the Market Data in Tab 2.")
        
        # 1. Get existing saved value (if any)
        saved_ship = _get_val(product_data, 'shipping_cost_basis')
        
        # 2. Use the same calculation as Tab 1
        calculated_ship = live_ship 
        
        # 3. Determine which to show
        display_ship = saved_ship if saved_ship else calculated_ship
        if calculated_ship > 0 and (saved_ship is None or saved_ship == 0):
            display_ship = calculated_ship

        v1, v2 = st.columns(2)
        with v1: 
            val_target = st.number_input("🎯 Target Sell Price ($)", min_value=0.0, value=_get_val(product_data, 'target_list_price'), step=1.0)
        with v2:
            val_ship_cost = st.number_input("🚚 Est. Shipping Cost ($)", min_value=0.0, value=display_ship, step=1.0, help=f"Auto-calculated Zone 9 Rate: ${calculated_ship:.2f}")
        
        st.caption("Profit Formula: Target - (Target * 15% Fee) - Shipping - Bid")
        if val_target and val_ship_cost is not None:
            fees = val_target * 0.15
            net = val_target - fees - val_ship_cost
            color = "green" if net > 0 else "red"
            st.markdown(f"**Net Payout:** :{color}[${net:,.2f}] (after ${fees:,.2f} fees)")

    # Return Dictionary matching DB columns
    return {
        'title': new_title, 'brand': new_brand, 'model': new_model,
        'upc': new_upc, 'asin': new_asin,
        'weight_lbs': val_lbs, 'weight_oz': val_oz, 
        'length': val_l, 'width': val_w, 'height': val_h,
        
        # Amazon
        'amazon_stars': val_amz_stars, 'amazon_reviews': val_amz_reviews, 
        'amazon_rank_main': val_amz_rank_m, 'amazon_cat_name': val_amz_cat_m,
        'amazon_rank_sub': val_amz_rank_s, 'amazon_subcat_name': val_amz_cat_s,
        
        # eBay Sold
        'ebay_avg_sold_price': val_e_avg_sold,
        'ebay_avg_shipping_sold': val_e_avg_ship,
        'ebay_sell_through_rate': val_e_str,
        'ebay_total_sold_count': val_e_total_sold,
        'ebay_sold_range_low': val_e_low, 'ebay_sold_range_high': val_e_high,
        
        # eBay Active
        'ebay_active_count': val_e_active_cnt,
        'ebay_avg_list_price': val_e_list_avg,
        'ebay_active_low': val_e_act_low, 'ebay_active_high': val_e_act_high,
        'ebay_avg_shipping_active': val_e_active_ship,
        'market_notes': val_mkt_notes,
        
        # Valuation
        'target_list_price': val_target,
        'shipping_cost_basis': val_ship_cost
    }