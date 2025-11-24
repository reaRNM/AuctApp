# components/research.py
import streamlit as st
import pandas as pd
from utils.inventory import get_product_by_id, save_product_to_library
from components.grid_options import OPT_CATEGORIES  # <--- Import Categories

# FIXED: Removed unused 'is_linked' parameter
def _render_form_fields(product_data: dict):
    """Helper to render the UI inputs inside the form."""
    
    # --- SECTION 1: IDENTITY ---
    st.markdown("#### 1. Product Identity (Master Record)")
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1: new_title = st.text_input("Clean Title", value=product_data.get('title', ''))
    with c2: new_brand = st.text_input("Brand", value=product_data.get('brand', ''))
    with c3: new_model = st.text_input("Model", value=product_data.get('model', ''))

    c4, c5, c6 = st.columns(3)
    with c4: new_upc = st.text_input("UPC", value=product_data.get('upc', ''))
    with c5: new_asin = st.text_input("ASIN", value=product_data.get('asin', ''))
    # FIXED: Use Selectbox for Category
    with c6: 
        curr_cat = product_data.get('category')
        # Ensure current value is in the list, default to 'Other' if not
        idx = OPT_CATEGORIES.index(curr_cat) if curr_cat in OPT_CATEGORIES else OPT_CATEGORIES.index("Other")
        new_cat = st.selectbox("Category", OPT_CATEGORIES, index=idx)

    # --- SECTION 2: PRICING ---
    st.markdown("#### 2. Pricing Research")
    p1, p2, p3, p4 = st.columns(4)
    with p1: val_msrp = st.number_input("MSRP ($)", min_value=0.0, value=float(product_data.get('msrp') or 0.0), step=1.0)
    with p2: val_avg = st.number_input("Avg Sold Price ($)", min_value=0.0, value=float(product_data.get('avg_sold_price') or 0.0), step=1.0)
    with p3: val_target = st.number_input("Target List Price ($)", min_value=0.0, value=float(product_data.get('target_list_price') or 0.0), step=1.0)
    with p4: val_ship_cost = st.number_input("Est. Ship Cost ($)", min_value=0.0, value=float(product_data.get('shipping_cost_basis') or 0.0), step=0.5)

    # --- SECTION 3: LOGISTICS ---
    st.markdown("#### 3. Shipping Logistics")
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    with s1: val_lbs = st.number_input("Lbs", min_value=0.0, value=float(product_data.get('weight_lbs') or 0.0), step=1.0)
    with s2: val_oz = st.number_input("Oz", min_value=0.0, value=float(product_data.get('weight_oz') or 0.0), step=1.0)
    with s3: val_l = st.number_input("L (in)", min_value=0.0, value=float(product_data.get('length') or 0.0))
    with s4: val_w = st.number_input("W (in)", min_value=0.0, value=float(product_data.get('width') or 0.0))
    with s5: val_h = st.number_input("H (in)", min_value=0.0, value=float(product_data.get('height') or 0.0))
    with s6: val_irreg = st.checkbox("Irregular?", value=bool(product_data.get('is_irregular')))

    # Return dictionary of values
    return {
        'title': new_title, 'brand': new_brand, 'model': new_model,
        'upc': new_upc, 'asin': new_asin, 'category': new_cat,
        'msrp': val_msrp, 'avg_sold_price': val_avg, 
        'target_list_price': val_target, 'shipping_cost_basis': val_ship_cost,
        'weight_lbs': val_lbs, 'weight_oz': val_oz, 
        'length': val_l, 'width': val_w, 'height': val_h, 
        'is_irregular': val_irreg
    }

def render_research_station(conn, selected_rows):
    """Main logic controller for the Research Station."""
    if not selected_rows or len(selected_rows) != 1:
        st.info("👆 Select exactly one item in the grid above to open the Research Station.")
        return

    item = selected_rows[0]
    item_id = item.get('id')
    existing_product_id = item.get('product_id')
    
    product_data = {}
    is_linked = False
    
    # Load Data Logic
    if existing_product_id and existing_product_id > 0:
        loaded_prod = get_product_by_id(conn, existing_product_id)
        if loaded_prod is not None:
            product_data = loaded_prod.to_dict()
            is_linked = True
            st.success(f"✅ Linked to Master Product #{existing_product_id}: {product_data.get('title')}")
    else:
        # Pre-fill logic
        product_data = {
            'title': item.get('Title'), 'brand': item.get('Brand'),
            'model': item.get('Model'), 'upc': item.get('UPC'),
            'asin': item.get('ASIN'), 'notes': item.get('Notes')
        }
        st.warning("🚫 This item is NOT in your Product Library. Edit the details below to add it.")

    st.markdown("---")
    st.subheader("📚 Product Research Station")

    with st.form("research_form"):
        # FIXED: Removed is_linked argument from call
        form_values = _render_form_fields(product_data)
        
        st.markdown("###")
        btn_label = "💾 Update Master Record" if is_linked else "➕ Create & Link to Library"
        submitted = st.form_submit_button(btn_label, use_container_width=True)

        if submitted:
            # Merge ID into the form data
            form_values['id'] = existing_product_id if is_linked else None
            
            new_id = save_product_to_library(conn, form_values, link_item_id=item_id)
            
            if new_id:
                st.success("Product saved to Library successfully!")
                st.rerun()
            else:
                st.error("Could not save product. Check for duplicate UPC/ASIN.")