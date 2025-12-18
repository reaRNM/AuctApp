# components/research_ui.py
import streamlit as st
import math
from utils.shipping import estimate_shipping
# NEW: Import ALL display constants
from utils.parse import (
    COL_PRD_TITLE, COL_BRAND, COL_MODEL, COL_CAT, COL_UPC, COL_ASIN, COL_MSRP, COL_NOTES,
    KEY_DB_TITLE, KEY_DB_BRAND, KEY_DB_MODEL, KEY_DB_CAT, KEY_DB_UPC, KEY_DB_ASIN, KEY_DB_MSRP, KEY_DB_AVG_SOLD,
    KEY_DB_TARGET, KEY_SHIP_COST, KEY_MKT_NOTES,
    KEY_WEIGHT_LBS, KEY_WEIGHT_OZ, KEY_LENGTH, KEY_WIDTH, KEY_HEIGHT,
    KEY_EBAY_AVG_SOLD, KEY_EBAY_SOLD_LOW, KEY_EBAY_SOLD_HIGH, KEY_EBAY_AVG_SHIP, KEY_EBAY_STR,
    KEY_EBAY_SOLD_COUNT, KEY_EBAY_SELLERS, KEY_EBAY_ACTIVE_CNT, KEY_EBAY_LIST_AVG,
    KEY_EBAY_ACTIVE_LOW, KEY_EBAY_ACTIVE_HIGH, KEY_EBAY_ACTIVE_SHIP, KEY_EBAY_WATCHERS,
    KEY_AMZ_LIST, KEY_AMZ_REVS, KEY_AMZ_STARS, KEY_AMZ_RANK_MAIN, KEY_AMZ_CAT_MAIN,
    KEY_AMZ_RANK_SUB, KEY_AMZ_CAT_SUB
)




def _get_val(data, key):
    """Helper to handle 0.0 vs None for inputs."""
    val = data.get(key)
    return float(val) if val and float(val) > 0 else None

def render_product_form_fields(product_data: dict):
    
    # --- HEADER ---
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    with c1: new_title = st.text_input(COL_PRD_TITLE, value=product_data.get(KEY_DB_TITLE, ''))
    with c2: new_brand = st.text_input(COL_BRAND, value=product_data.get(KEY_DB_BRAND, ''))
    with c3: new_model = st.text_input(COL_MODEL, value=product_data.get(KEY_DB_MODEL, ''))
    with c4: new_cat = st.text_input(COL_CAT, value=product_data.get(KEY_DB_CAT, ''), placeholder="e.g. Electronics")
    
    st.markdown("---")
    
    # --- TABS ---
    tab_specs, tab_market, tab_profit = st.tabs(["📦 Specs & Identity", "📊 Market Data (Terapeak)", "💰 Valuation"])

    # === TAB 1: SPECS & AMAZON ===
    with tab_specs:
        col_id1, col_id2 = st.columns(2)
        with col_id1: new_upc = st.text_input(COL_UPC, value=product_data.get(KEY_DB_UPC, ''))
        with col_id2: new_asin = st.text_input(COL_ASIN, value=product_data.get(KEY_DB_ASIN, ''))
        
        st.divider()
        st.caption("Physical Attributes (Calculates Shipping)")
        
        c_wt, c_dim = st.columns(2)
        with c_wt:
            w1, w2 = st.columns(2)
            with w1: val_lbs = st.number_input("Lbs", min_value=0.0, value=_get_val(product_data, KEY_WEIGHT_LBS))
            with w2: val_oz = st.number_input("Oz", min_value=0.0, value=_get_val(product_data, KEY_WEIGHT_OZ))
        with c_dim:
            d1, d2, d3 = st.columns(3)
            with d1: val_l = st.number_input("L", value=_get_val(product_data, KEY_LENGTH))
            with d2: val_w = st.number_input("W", value=_get_val(product_data, KEY_WIDTH))
            with d3: val_h = st.number_input("H", value=_get_val(product_data, KEY_HEIGHT))
        # --- LIVE CALCULATION & EXPLANATION ---
        live_ship = estimate_shipping(val_lbs or 0, val_oz or 0, val_l or 0, val_w or 0, val_h or 0)
        
        if live_ship > 0:
            total_lbs = (val_lbs or 0) + ((val_oz or 0)/16)
            dim_weight = ((val_l or 0) * (val_w or 0) * (val_h or 0)) / 166
            msg = f"🚚 **Estimated Zone 9 Shipping:** ${live_ship:.2f}"
            if dim_weight > total_lbs:
                msg += f" (Billed as {math.ceil(dim_weight)} lbs Dim Weight)"
            st.info(msg)
        elif (val_lbs or 0) > 0:
            st.warning("⚠️ Item too heavy/large for standard shipping.")

        st.divider()
        st.caption("Amazon Intelligence")
        a_price_col, a_stars_col, a_rev_col = st.columns(3)
        with a_price_col: val_amz_price = st.number_input("Current Listing Price ($)", value=_get_val(product_data, KEY_AMZ_LIST))
        with a_stars_col: val_amz_stars = st.number_input("Stars (0-5)", min_value=0.0, max_value=5.0, value=_get_val(product_data, KEY_AMZ_STARS))
        with a_rev_col: val_amz_reviews = st.number_input("Num Reviews", min_value=0, value=int(product_data.get(KEY_AMZ_REVS) or 0))
        
        st.write("") 
        ar1, ar2 = st.columns([1, 2])
        with ar1: val_amz_rank_m = st.number_input("Main Rank #", min_value=0, value=int(product_data.get(KEY_AMZ_RANK_MAIN) or 0))
        with ar2: val_amz_cat_m = st.text_input("Main Category Name", value=product_data.get(KEY_AMZ_CAT_MAIN, ''), placeholder="e.g. Office Products")
        
        ar3, ar4 = st.columns([1, 2])
        with ar3: val_amz_rank_s = st.number_input("Sub Rank #", min_value=0, value=int(product_data.get(KEY_AMZ_RANK_SUB) or 0))
        with ar4: val_amz_cat_s = st.text_input("Sub Category Name", value=product_data.get(KEY_AMZ_CAT_SUB, ''), placeholder="e.g. Inkjet Printers")
    # === TAB 2: MARKET DATA (EBAY) ===
    with tab_market:
        st.caption("eBay SOLD Data (The Realized Value)")
        e1, e2, e3 = st.columns(3)
        with e1: val_e_avg_sold = st.number_input("Avg Sold ($)", value=_get_val(product_data, KEY_EBAY_AVG_SOLD))
        with e2: val_e_avg_ship = st.number_input("Avg Ship ($)", value=_get_val(product_data, KEY_EBAY_AVG_SHIP))
        with e3: val_e_str = st.number_input("Sell-Through %", value=_get_val(product_data, KEY_EBAY_STR))
        
        e4, e5 = st.columns(2)
        with e4: val_e_total_sold = st.number_input("Total Sold Count", value=int(product_data.get(KEY_EBAY_SOLD_COUNT) or 0))
        with e5: val_e_total_sellers = st.number_input("Total Sellers Count", value=int(product_data.get(KEY_EBAY_SELLERS) or 0))
        
        c_rng1, c_rng2 = st.columns(2)
        with c_rng1: val_e_low = st.number_input("Sold Range Low", value=_get_val(product_data, KEY_EBAY_SOLD_LOW))
        with c_rng2: val_e_high = st.number_input("Sold Range High", value=_get_val(product_data, KEY_EBAY_SOLD_HIGH))

        st.divider()
        st.caption("eBay ACTIVE Data (The Competition)")
        ea1, ea2, ea3 = st.columns(3)
        with ea1: val_e_active_cnt = st.number_input("Active Listings Count", value=int(product_data.get(KEY_EBAY_ACTIVE_CNT) or 0))
        with ea2: val_e_list_avg = st.number_input("Avg List Price ($)", value=_get_val(product_data, KEY_EBAY_LIST_AVG))
        with ea3: val_e_active_ship = st.number_input("Active Avg Ship ($)", value=_get_val(product_data, KEY_EBAY_ACTIVE_SHIP))
        
        ea4, ea5, ea6 = st.columns(3)
        with ea4: val_e_act_low = st.number_input("Active Range Low ($)", value=_get_val(product_data, KEY_EBAY_ACTIVE_LOW))
        with ea5: val_e_act_high = st.number_input("Active Range High ($)", value=_get_val(product_data, KEY_EBAY_ACTIVE_HIGH))
        with ea6: val_e_watchers = st.number_input("Num Watchers", value=int(product_data.get(KEY_EBAY_WATCHERS) or 0))
        
        val_mkt_notes = st.text_area("Market Notes", value=product_data.get(KEY_MKT_NOTES, ''))
    # === TAB 3: VALUATION ===
    with tab_profit:
        st.info("Set your 'Target' based on the Market Data in Tab 2.")
        
        saved_ship = _get_val(product_data, KEY_SHIP_COST)
        calculated_ship = live_ship 
        display_ship = saved_ship if saved_ship else calculated_ship
        if calculated_ship > 0 and (saved_ship is None or saved_ship == 0):
            display_ship = calculated_ship

        m1, m2, m3 = st.columns(3)
        with m1:
            val_msrp = st.number_input(f"{COL_MSRP} ($)", min_value=0.0, value=_get_val(product_data, KEY_DB_MSRP), step=1.0)
        with m2: 
            val_target = st.number_input("🎯 Target Sell Price ($)", min_value=0.0, value=_get_val(product_data, KEY_DB_TARGET), step=1.0)
        with m3:
            val_ship_cost = st.number_input("🚚 Est. Shipping Cost ($)", min_value=0.0, value=display_ship, step=1.0)
        
        st.caption("Profit Formula: Target - (Target * 15% Fee) - Shipping - Bid")
        if val_target and val_ship_cost is not None:
            fees = val_target * 0.15
            net = val_target - fees - val_ship_cost
            color = "green" if net > 0 else "red"
            st.markdown(f"**Net Payout:** :{color}[${net:,.2f}] (after ${fees:,.2f} fees)")

    return {
        KEY_DB_TITLE: new_title, KEY_DB_BRAND: new_brand, KEY_DB_MODEL: new_model,
        KEY_DB_CAT: new_cat,
        KEY_DB_UPC: new_upc, KEY_DB_ASIN: new_asin,
        KEY_DB_MSRP: val_msrp,
        KEY_WEIGHT_LBS: val_lbs, KEY_WEIGHT_OZ: val_oz, 
        KEY_LENGTH: val_l, KEY_WIDTH: val_w, KEY_HEIGHT: val_h,
        KEY_AMZ_STARS: val_amz_stars, KEY_AMZ_REVS: val_amz_reviews, 
        KEY_AMZ_LIST: val_amz_price,
        KEY_AMZ_RANK_MAIN: val_amz_rank_m, KEY_AMZ_CAT_MAIN: val_amz_cat_m,
        KEY_AMZ_RANK_SUB: val_amz_rank_s, KEY_AMZ_CAT_SUB: val_amz_cat_s,
        KEY_EBAY_AVG_SOLD: val_e_avg_sold, KEY_EBAY_AVG_SHIP: val_e_avg_ship,
        KEY_EBAY_STR: val_e_str, KEY_EBAY_SOLD_COUNT: val_e_total_sold,
        KEY_EBAY_SELLERS: val_e_total_sellers,
        KEY_EBAY_SOLD_LOW: val_e_low, KEY_EBAY_SOLD_HIGH: val_e_high,
        KEY_EBAY_ACTIVE_CNT: val_e_active_cnt, KEY_EBAY_LIST_AVG: val_e_list_avg,
        KEY_EBAY_ACTIVE_LOW: val_e_act_low, KEY_EBAY_ACTIVE_HIGH: val_e_act_high,
        KEY_EBAY_ACTIVE_SHIP: val_e_active_ship,
        KEY_EBAY_WATCHERS: val_e_watchers,
        KEY_MKT_NOTES: val_mkt_notes,
        KEY_DB_TARGET: val_target, KEY_SHIP_COST: val_ship_cost
    }