# pages/2_Product_Library.py
import streamlit as st
import pandas as pd
import sys
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import create_connection
from utils.inventory import save_product_to_library, get_product_by_id, delete_product
from components.research_ui import render_product_form_fields 
from utils.ai import extract_data_with_gemini, get_api_key 
from components.grid_styles import JS_CURRENCY_SORT, JS_MSRP_STYLE 
# NEW: Import All Constants
from utils.parse import COL_MSRP, COL_TITLE, COL_BRAND, COL_CAT, COL_AVG_SOLD

st.set_page_config(page_title="Product Library", layout="wide")
st.title("📚 Master Product Library")

if 'lib_ai_result' not in st.session_state:
    st.session_state.lib_ai_result = None

try:
    conn = create_connection()

    # 1. SEARCH
    search_term = st.text_input("🔍 Search Library (Title, Brand, UPC, ASIN)", "")

    # 2. LOAD MASTER DATA (ADDED MSRP, AVG SOLD)
    query = """
        SELECT id, title, brand, model, category, upc, asin, msrp, avg_sold_price, is_favorite 
        FROM products
        WHERE title LIKE ? OR brand LIKE ? OR model LIKE ? OR upc LIKE ? OR asin LIKE ?
        ORDER BY title ASC
    """
    params = tuple([f"%{search_term}%"] * 5)
    df = pd.read_sql_query(query, conn, params=params)

    # RENAME DB COLUMNS TO CONSTANTS
    df = df.rename(columns={
        "title": COL_TITLE,
        "brand": COL_BRAND,
        "category": COL_CAT,
        "msrp": COL_MSRP,
        "avg_sold_price": COL_AVG_SOLD
    })

    # 3. LIST
    col_list, col_detail = st.columns([6, 4]) # Adjusted width

    with col_list:
        st.subheader(f"Products ({len(df)})")
        
        # Grid Configuration
        gb = GridOptionsBuilder.from_dataframe(df[['id', COL_TITLE, COL_BRAND, COL_CAT, COL_MSRP, COL_AVG_SOLD]])
        gb.configure_selection('single', use_checkbox=False)
        gb.configure_column("id", hide=True)
        gb.configure_grid_options(domLayout='autoHeight')
        
        # USE CONSTANTS FOR CONFIGURATION
        gb.configure_column(COL_MSRP, width=90, 
                            type=["numericColumn", "numberColumnFilter"],
                            valueFormatter="x > 0 ? '$' + x.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : ''",
                            comparator=JS_CURRENCY_SORT, cellStyle=JS_MSRP_STYLE)
                            
        gb.configure_column(COL_AVG_SOLD, width=90, 
                            type=["numericColumn", "numberColumnFilter"],
                            valueFormatter="x > 0 ? '$' + x.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : ''",
                            comparator=JS_CURRENCY_SORT)

        grid_response = AgGrid(
            df[['id', COL_TITLE, COL_BRAND, COL_CAT, COL_MSRP, COL_AVG_SOLD]],
            gridOptions=gb.build(),
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=True,
            height=600,
            theme="streamlit",
            allow_unsafe_jscode=True
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
                    ai_data = st.session_state.lib_ai_result
                    if isinstance(ai_data, list):
                        if len(ai_data) > 0 and isinstance(ai_data[0], dict):
                            ai_data = ai_data[0] 
                        else:
                            ai_data = {}
                    if isinstance(ai_data, dict):
                        clean_ai = {k: v for k, v in ai_data.items() if v is not None and v != 0 and v != ""}
                        full_data.update(clean_ai)

                st.subheader(f"✏️ Edit: {full_data.get(COL_TITLE)}")
                
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
                
                # DELETE
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