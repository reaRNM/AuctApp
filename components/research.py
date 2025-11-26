# components/research.py
import streamlit as st
import pandas as pd
from utils.inventory import get_product_by_id, save_product_to_library
from components.research_ui import render_product_form_fields # <--- Import the UI

def _get_initial_data(conn, first_item):
    """Loads existing product data or creates a template from the auction item."""
    existing_product_id = first_item.get('product_id')
    product_data = {}
    is_linked = False

    if existing_product_id and existing_product_id > 0:
        loaded_prod = get_product_by_id(conn, existing_product_id)
        if loaded_prod is not None:
            product_data = loaded_prod.to_dict()
            is_linked = True
    else:
        # Template from raw auction data
        # NEW: Check if we scraped a Suggested MSRP
        # We need to ensure 'suggested_msrp' is passed in 'first_item'. 
        # If it's missing from the grid view, we might need to fetch it or rely on what's available.
        # For now, let's assume it might be passed or we default to 0.
        
        # NOTE: You might need to add 'suggested_msrp' to get_auction_items in db.py 
        # if you want it available here instantly without a fetch.
        # For now, we check if it exists in the row data.
        
        msrp_guess = first_item.get('suggested_msrp', 0.0)
        
        product_data = {
            'title': first_item.get('Title'), 
            'brand': first_item.get('Brand'),
            'model': first_item.get('Model'), 
            'upc': first_item.get('UPC'),
            'asin': first_item.get('ASIN'), 
            'notes': first_item.get('Notes'),
            'msrp': msrp_guess # Pre-fill!
        }
    
    return product_data, existing_product_id, is_linked

def _handle_save(conn, form_values, existing_id, is_linked, selected_ids):
    """Handles the database save operation."""
    # If linked, we update that ID. If not, we create new (ID is None)
    target_prod_id = existing_id if is_linked else None
    form_values['id'] = target_prod_id
    
    # Save to DB
    new_id = save_product_to_library(conn, form_values, link_item_ids=selected_ids)
    
    if new_id:
        st.success(f"Success! Saved Product #{new_id} and linked items.")
        st.rerun()
    else:
        st.error("Could not save product. Check for duplicate UPC/ASIN.")

def render_research_station(conn, selected_rows):
    """Main Controller for the Research Station."""
    if not selected_rows:
        st.info("👆 Select items in the grid above to edit or link.")
        return

    # 1. Setup Context
    count = len(selected_rows)
    is_bulk = count > 1
    selected_ids = [row.get('id') for row in selected_rows if row.get('id')]
    
    # 2. Load Data (Helper Function)
    product_data, existing_id, is_linked = _get_initial_data(conn, selected_rows[0])

    # 3. Render Header
    st.markdown("---")
    if is_bulk:
        st.subheader(f"📚 Bulk Linker ({count} Items)")
        st.info(f"Updating Master Product and linking {count} items.")
    else:
        st.subheader("📚 Product Research Station")
        if is_linked:
            st.success(f"✅ Linked to Master Product #{existing_id}")
        else:
            st.warning("🚫 Not in Product Library. Edit details below to add.")

    # 4. Render Form
    with st.form("research_form"):
        # Call the UI Component
        form_values = render_product_form_fields(product_data)
        
        st.markdown("###")
        
        # Determine Button Label
        if is_bulk:
            btn_label = f"🔗 Create Master & Link {count} Items"
        elif is_linked:
            btn_label = "💾 Update Master Record"
        else:
            btn_label = "➕ Create & Link to Library"
            
        submitted = st.form_submit_button(btn_label, use_container_width=True)

        # 5. Handle Submission (Helper Function)
        if submitted:
            _handle_save(conn, form_values, existing_id, is_linked, selected_ids)