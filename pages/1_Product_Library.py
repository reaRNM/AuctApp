# pages/1_Product_Library.py
import streamlit as st
import pandas as pd
import sys
import os

# Allow imports from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import create_connection
from utils.inventory import save_product_to_library, get_product_by_id, delete_product
from components.research import _render_form_fields

st.set_page_config(page_title="Product Library", layout="wide")
st.title("📚 Master Product Library")

# Use context manager for connection (Safety)
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
                st.subheader(f"✏️ Edit: {full_data.get('title')}")
                
                with st.form("library_edit_form"):
                    form_values = _render_form_fields(full_data)
                    form_values['id'] = prod_id
                    
                    st.markdown("###")
                    if st.form_submit_button("💾 Save Changes", use_container_width=True):
                        save_product_to_library(conn, form_values)
                        st.success("Saved!")
                        st.rerun()
                
                # --- PRICE HISTORY (Moved to correct indentation) ---
                st.markdown("---")
                st.subheader("📈 Price History")
                hist_query = """
                    SELECT a.scrape_date, i.sold_price 
                    FROM auction_items i
                    JOIN auctions a ON i.auction_id = a.id
                    WHERE i.product_id = ? AND i.sold_price > 0
                    ORDER BY a.scrape_date ASC
                """
                history_df = pd.read_sql_query(hist_query, conn, params=(prod_id,))
                
                if not history_df.empty:
                    st.line_chart(history_df, x="scrape_date", y="sold_price")
                    avg = history_df['sold_price'].mean()
                    low = history_df['sold_price'].min()
                    high = history_df['sold_price'].max()
                    s1, s2, s3 = st.columns(3)
                    s1.metric("Lowest", f"${low:,.2f}")
                    s2.metric("Average", f"${avg:,.2f}")
                    s3.metric("Highest", f"${high:,.2f}")
                else:
                    st.caption("No sales history recorded yet.")

                # --- DELETE SECTION (With Confirmation) ---
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
                    new_values = _render_form_fields(empty_data)
                    if st.form_submit_button("Create Product"):
                        save_product_to_library(conn, new_values)
                        st.success("Created!")
                        st.rerun()

finally:
    if 'conn' in locals():
        conn.close()