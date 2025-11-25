# pages/3_Database_Cleanup.py
import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import create_connection

st.set_page_config(page_title="Cleanup Tool", layout="wide")
st.title("🧹 Database Cleanup Tool")

conn = create_connection()

# 1. FIND DUPLICATES (Simple Title Match)
st.subheader("Find Potential Duplicates")
search_dupe = st.text_input("Search for duplicates (e.g., 'Tray')", "")

if search_dupe:
    query = """
        SELECT id, title, brand, model, upc 
        FROM products 
        WHERE title LIKE ? 
        ORDER BY title
    """
    df = pd.read_sql_query(query, conn, params=(f"%{search_dupe}%",))
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # 2. MERGE INTERFACE
        st.divider()
        st.subheader("⚔️ Merge Products")
        
        c1, c2 = st.columns(2)
        
        with c1:
            keep_id = st.selectbox("Select the MASTER product to KEEP:", df['id'].tolist(), format_func=lambda x: f"#{x} - {df[df['id']==x]['title'].values[0]}")
        
        with c2:
            # Filter out the one we are keeping
            merge_options = df[df['id'] != keep_id]
            remove_ids = st.multiselect("Select duplicates to MERGE into Master (and delete):", merge_options['id'].tolist(), format_func=lambda x: f"#{x} - {merge_options[merge_options['id']==x]['title'].values[0]}")
            
        if remove_ids:
            st.warning(f"⚠️ This will move all history from products {remove_ids} to product #{keep_id}, and then PERMANENTLY DELETE the duplicates.")
            
            if st.button("Confirm Merge"):
                cursor = conn.cursor()
                try:
                    # A. Re-link Auction Items
                    placeholders = ",".join("?" * len(remove_ids))
                    sql_relink = f"UPDATE auction_items SET product_id = ? WHERE product_id IN ({placeholders})"
                    cursor.execute(sql_relink, [keep_id] + remove_ids)
                    
                    # B. Delete Duplicates
                    sql_delete = f"DELETE FROM products WHERE id IN ({placeholders})"
                    cursor.execute(sql_delete, remove_ids)
                    
                    conn.commit()
                    st.success(f"Merged {len(remove_ids)} products into #{keep_id}!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Merge failed: {e}")
    else:
        st.info("No products found matching that search.")

conn.close()