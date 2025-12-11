# pages/2_Product_Library.py
import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import create_connection
from utils.inventory import save_product_to_library, get_product_by_id, delete_product
from components.research_ui import render_product_form_fields 
from utils.ai import extract_data_with_gemini, get_api_key # <--- Import

st.set_page_config(page_title="Product Library", layout="wide")
st.title("📚 Master Product Library")

# Session state for Library AI
if 'lib_ai_result' not in st.session_state:
    st.session_state.lib_ai_result = None

try:
    conn = create_connection()

    # 1. SEARCH
    search_term = st.text_input("🔍 Search Library (Title, Brand, UPC, ASIN)", "")

    # 2. LOAD MASTER DATA
    query = """
        SELECT id, title, brand, model, category, upc, asin, avg_sold_price 
        FROM products
        WHERE title LIKE ? OR brand LIKE ? OR model LIKE ? OR upc LIKE ? OR asin LIKE ?
        ORDER BY title ASC
    """
    params = tuple([f"%{search_term}%"] * 5)
    df = pd.read_sql_query(query, conn, params=params)

    # 3. LIST
    col_list, col_detail = st.columns([5, 5])

    with col_list:
        st.subheader(f"Products ({len(df)})")
        from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
        
        gb = GridOptionsBuilder.from_dataframe(df[['id', 'title', 'brand', 'model', 'category']])
        gb.configure_selection('single', use_checkbox=False)
        gb.configure_column("id", hide=True)
        gb.configure_grid_options(domLayout='autoHeight')
        
        grid_response = AgGrid(
            df[['id', 'title', 'brand', 'model', 'category']],
            gridOptions=gb.build(),
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=True,
            height=600,
            theme="streamlit"
        )

    # 4. DETAILS & ACTIONS
    with col_detail:
        selected = grid_response['selected_rows']
        
        if selected:
            prod_id = selected[0]['id']
            product_series = get_product_by_id(conn, prod_id)
            
            if product_series is not None:
                full_data = product_series.to_dict()
                
                # MERGE AI DATA IF AVAILABLE
                if st.session_state.lib_ai_result:
                    clean_ai = {k: v for k, v in st.session_state.lib_ai_result.items() if v is not None and v != 0 and v != ""}
                    full_data.update(clean_ai)

                st.subheader(f"✏️ Edit: {full_data.get('title')}")
                
                # --- TABS FOR AI ---
                tab_edit, tab_ai = st.tabs(["📝 Edit Product", "🤖 AI Import"])
                
                with tab_ai:
                    st.caption("Upload screenshots to auto-fill missing data for this product.")
                    uploaded_files = st.file_uploader("Upload Screenshots", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key="lib_uploader")
                    
                    has_key = get_api_key() is not None
                    if st.button("✨ Extract Data", disabled=not uploaded_files or not has_key, key="lib_ai_btn"):
                        with st.spinner("Gemini is analyzing..."):
                            extracted = extract_data_with_gemini(uploaded_files)
                            if extracted:
                                st.session_state.lib_ai_result = extracted
                                st.success("Data extracted! Switch to 'Edit Product' to review & save.")
                                st.rerun()
                                
                    if st.button("🧹 Clear AI Data", key="lib_clear_ai"):
                        st.session_state.lib_ai_result = None
                        st.rerun()

                with tab_edit:
                    with st.form("library_edit_form"):
                        form_values = render_product_form_fields(full_data)
                        form_values['id'] = prod_id
                        
                        st.markdown("---")
                        is_fav = st.checkbox("❤️ Mark as Favorite", value=bool(full_data.get('is_favorite')))
                        
                        if st.form_submit_button("💾 Save Changes", use_container_width=True):
                            save_product_to_library(conn, form_values)
                            cursor = conn.cursor()
                            cursor.execute("UPDATE products SET is_favorite = ? WHERE id = ?", (1 if is_fav else 0, prod_id))
                            conn.commit()
                            
                            st.session_state.lib_ai_result = None # Clear after save
                            st.success("Saved!")
                            st.rerun()
                
                # ... (Keep existing Price History & Delete Logic)
                st.markdown("---")
                with st.expander("🗑️ Delete Product"):
                    st.warning("This will delete the product and unlink all associated auction items.")
                    confirm_del = st.checkbox("I understand this cannot be undone")
                    if st.button("Permanently Delete", disabled=not confirm_del):
                        if delete_product(conn, prod_id):
                            st.success("Product Deleted.")
                            st.rerun()
                        else:
                            st.error("Delete failed.")
            else:
                st.error("Error: Product details could not be found.")
                    
        else:
            st.info("Select a product from the list to view details.")
            st.markdown("---")
            with st.expander("➕ Create New Product from Scratch"):
                with st.form("new_product_form"):
                    empty_data = {}
                    new_values = render_product_form_fields(empty_data)
                    if st.form_submit_button("Create Product"):
                        save_product_to_library(conn, new_values)
                        st.success("Created!")
                        st.rerun()

finally:
    if 'conn' in locals():
        conn.close()