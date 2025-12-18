# components/research.py
import streamlit as st
from typing import Any
from utils.inventory import get_product_by_id, save_product_to_library
from components.research_ui import render_product_form_fields
from utils.ai import extract_data_with_gemini, get_api_key
# IMPORT ALL NECESSARY CONSTANTS
from utils.parse import (
    KEY_SUG_MSRP, KEY_SCRAPED_MSRP, COL_MSRP, COL_CAT, KEY_SCRAPED_CAT, KEY_PROD_ID,
    COL_TITLE, COL_BRAND, COL_MODEL, COL_UPC, COL_ASIN, COL_NOTES
)



# === HELPERS ===
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
    existing_product_id = first_item.get(KEY_PROD_ID)
    
    if existing_product_id and existing_product_id > 0:
        loaded_prod = get_product_by_id(conn, existing_product_id)
        if loaded_prod is not None:
            return loaded_prod.to_dict(), existing_product_id, True

    # Uses Constants
    msrp_guess = _find_best_value(first_item, [KEY_SCRAPED_MSRP, KEY_SUG_MSRP, COL_MSRP], float)
    cat_guess = _find_best_value(first_item, [COL_CAT, KEY_SCRAPED_CAT], str)

    # FIXED: Now using constants for dictionary lookups
    product_data = {
        'title': first_item.get(COL_TITLE), 
        'brand': first_item.get(COL_BRAND),
        'model': first_item.get(COL_MODEL), 
        'upc': first_item.get(COL_UPC),
        'asin': first_item.get(COL_ASIN), 
        'notes': first_item.get(COL_NOTES),
        'msrp': msrp_guess,
        'category': cat_guess
    }
    
    return product_data, existing_product_id, False

def _handle_save(conn, form_values, existing_id, is_linked, selected_ids):
    target_prod_id = existing_id if is_linked else None
    form_values['id'] = target_prod_id
    
    new_id = save_product_to_library(conn, form_values, link_item_ids=selected_ids)
    
    if new_id:
        st.success(f"Success! Saved Product #{new_id}.")
        if 'ai_result' in st.session_state:
            del st.session_state.ai_result
        st.rerun()
    else:
        st.error("Save failed. Check for duplicate UPC/ASIN.")

def _manage_session_state(selected_rows):
    """Handles clearing AI data when selection changes."""
    current_ids = sorted([row.get('id') for row in selected_rows if row.get('id')])
    
    if 'last_selected_ids' not in st.session_state:
        st.session_state.last_selected_ids = current_ids
        
    if st.session_state.last_selected_ids != current_ids:
        if 'ai_result' in st.session_state:
            del st.session_state.ai_result
        st.session_state.last_selected_ids = current_ids
    
    return current_ids

def _get_button_label(is_bulk: bool, is_linked: bool, count: int) -> str:
    if is_bulk:
        return f"🔗 Create Master & Link {count} Items"
    if is_linked:
        return "💾 Update Master Record"
    return "➕ Create & Link to Library"

# === UI COMPONENT RENDERERS ===
def _render_ai_tab():
    """Renders the content for the AI Import tab."""
    c_ai1, c_ai2 = st.columns([3, 1])
    with c_ai1:
        uploaded_files = st.file_uploader(
            "Upload Screenshots", 
            type=['png', 'jpg', 'jpeg'], 
            accept_multiple_files=True, 
            key="viewer_uploader"
        )
    with c_ai2:
        st.write("")
        st.write("")
        has_key = get_api_key() is not None
        if st.button("✨ Extract Data", disabled=not uploaded_files or not has_key, use_container_width=True, key="viewer_ai_btn"):
            with st.spinner("Gemini is analyzing..."):
                extracted = extract_data_with_gemini(uploaded_files)
                if extracted:
                    st.session_state.ai_result = extracted
                    st.success("Data Extracted! Switch to 'Manual Entry' to review.")
                    st.rerun()
        if not has_key:
            st.error("Missing API Key in .env")

    if 'ai_result' in st.session_state:
        with st.expander("View Raw AI Data"):
            st.json(st.session_state.ai_result)

def _render_manual_tab(conn, product_data, is_bulk, is_linked, count, existing_id, selected_ids):
    """Renders the Manual Entry form and Save buttons."""
    with st.form("research_form"):
        form_values = render_product_form_fields(product_data)
        st.markdown("###")
        
        btn_label = _get_button_label(is_bulk, is_linked, count)
        
        c_sub, c_clear = st.columns([4, 1])
        with c_sub:
            submitted = st.form_submit_button(btn_label, use_container_width=True)
        with c_clear: 
            if st.form_submit_button("🧹 Clear AI"):
                if 'ai_result' in st.session_state:
                    del st.session_state.ai_result
                st.rerun()

        if submitted:
            _handle_save(conn, form_values, existing_id, is_linked, selected_ids)

# === MAIN FUNCTION ===
def render_research_station(conn, selected_rows):
    """Main logic controller for the Research Station."""
    if not selected_rows:
        st.info("👆 Select items in the grid above to edit or link.")
        return

    # 1. Session Management
    current_ids = _manage_session_state(selected_rows)
    count = len(selected_rows)
    is_bulk = count > 1
    
    # 2. Prepare Data
    product_data, existing_id, is_linked = _get_initial_data(conn, selected_rows[0])
    
    if 'ai_result' in st.session_state and st.session_state.ai_result:
        ai_data = st.session_state.ai_result
        
        # --- FIX: Handle List vs Dict ---
        if isinstance(ai_data, list):
            if len(ai_data) > 0 and isinstance(ai_data[0], dict):
                ai_data = ai_data[0] # Unwrap list
            else:
                ai_data = {} # Invalid format
        
        if isinstance(ai_data, dict):
            clean_ai = {k: v for k, v in ai_data.items() if v is not None and v != 0 and v != ""}
            product_data.update(clean_ai)

    # 3. Render Header
    st.markdown("---")
    if is_bulk:
        st.subheader(f"📚 Bulk Linker ({count} Items)")
    else:
        st.subheader("📚 Product Research Station")
    
    if is_linked:
        st.success(f"✅ Linked to Master Product #{existing_id}")
    else:
        st.warning("🚫 Not in Product Library.")

    # 4. Render Tabs
    tab_manual, tab_ai = st.tabs(["📝 Manual Entry", "🤖 AI Import (Screenshots)"])
    
    with tab_ai:
        _render_ai_tab()
        
    with tab_manual:
        _render_manual_tab(conn, product_data, is_bulk, is_linked, count, existing_id, current_ids)