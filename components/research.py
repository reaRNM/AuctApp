# components/research.py
import streamlit as st
import pandas as pd
from typing import Any
from utils.inventory import get_product_by_id, save_product_to_library
from components.research_ui import render_product_form_fields

# FIXED: Changed type_cast type hint to 'Any' to allow both str and float
def _find_best_value(item: dict, keys: list, type_cast: Any = str):
    """Helper to find the first non-empty value from a list of keys."""
    for k in keys:
        val = item.get(k)
        if val:
            try:
                return type_cast(val)
            except (ValueError, TypeError):
                continue
    return 0.0 if type_cast == float else ""

def _get_initial_data(conn, first_item):
    """Loads existing product data or creates a template from the auction item."""
    existing_product_id = first_item.get('product_id')
    
    if existing_product_id and existing_product_id > 0:
        loaded_prod = get_product_by_id(conn, existing_product_id)
        if loaded_prod is not None:
            return loaded_prod.to_dict(), existing_product_id, True

    # Template from raw auction data
    # Now this works without Pylance errors because we allow 'float'
    msrp_guess = _find_best_value(first_item, ['Scraped MSRP', 'suggested_msrp', 'SuggestedMSRP', 'MSRP'], float)
    cat_guess = _find_best_value(first_item, ['Category', 'scraped_category', 'primaryCategory'], str)

    product_data = {
        'title': first_item.get('Title'), 
        'brand': first_item.get('Brand'),
        'model': first_item.get('Model'), 
        'upc': first_item.get('UPC'),
        'asin': first_item.get('ASIN'), 
        'notes': first_item.get('Notes'),
        'msrp': msrp_guess,
        'category': cat_guess
    }
    
    return product_data, existing_product_id, False

def _handle_save(conn, form_values, existing_id, is_linked, selected_ids):
    target_prod_id = existing_id if is_linked else None
    form_values['id'] = target_prod_id
    
    new_id = save_product_to_library(conn, form_values, link_item_ids=selected_ids)
    
    if new_id:
        st.success(f"Success! Saved Product #{new_id} and linked items.")
        st.rerun()
    else:
        st.error("Could not save product. Check for duplicate UPC/ASIN.")

def render_research_station(conn, selected_rows):
    """Main logic controller for the Research Station."""
    if not selected_rows:
        st.info("👆 Select items in the grid above to edit or link.")
        return

    count = len(selected_rows)
    is_bulk = count > 1
    selected_ids = [row.get('id') for row in selected_rows if row.get('id')]
    
    product_data, existing_id, is_linked = _get_initial_data(conn, selected_rows[0])

    # --- UI HEADER ---
    st.markdown("---")
    if is_bulk:
        st.subheader(f"📚 Bulk Editor ({count} Items)")
    else:
        st.subheader("📚 Product Research Station")

    # --- TABS: Manual vs AI ---
    tab_manual, tab_ai = st.tabs(["📝 Manual Entry", "🤖 AI Import (Screenshot)"])

    with tab_ai:
        st.info("Upload screenshots of Amazon/Terapeak to auto-extract data (Coming Soon with AI API).")
        uploaded_file = st.file_uploader("Choose a screenshot...", type=['png', 'jpg', 'jpeg'])
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Analysis Target", width=300)
            if st.button("✨ Extract Data (Simulated)"):
                st.warning("AI features require an API Key. For now, please use Manual Entry.")
                # Future: Call Gemini API here, parse JSON, and update `product_data`

    with tab_manual:
        with st.form("research_form"):
            form_values = render_product_form_fields(product_data)
            
            st.markdown("###")
            
            if is_bulk:
                btn_label = f"💾 Update {count} Items"
            elif is_linked:
                btn_label = "💾 Update Master Record"
            else:
                btn_label = "➕ Create & Link to Library"
                
            submitted = st.form_submit_button(btn_label, use_container_width=True)

            if submitted:
                _handle_save(conn, form_values, existing_id, is_linked, selected_ids)