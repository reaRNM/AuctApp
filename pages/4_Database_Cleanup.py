# pages/4_Database_Cleanup.py
import streamlit as st
import pandas as pd
import sys
import os
import difflib
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import create_connection
from utils.inventory import merge_products
from utils.parse import KEY_DB_TITLE, KEY_DB_BRAND, KEY_DB_MODEL, KEY_DB_UPC, KEY_DB_ASIN, KEY_IS_FAV

st.set_page_config(page_title="Cleanup Tool", layout="wide")
st.title("🧹 Database Cleanup & Merge Tool")

conn = None

def find_duplicates(df, threshold=0.85):
    groups = []
    seen = set()
    
    # 1. UPC
    df['upc_norm'] = df[KEY_DB_UPC].fillna('').astype(str).str.strip().str.lstrip('0')
    mask_upc = df['upc_norm'] != ''
    upc_dupes = df[mask_upc & df.duplicated('upc_norm', keep=False)]
    for norm_val, group in upc_dupes.groupby('upc_norm'):
        ids = group['id'].tolist()
        new_ids = [i for i in ids if i not in seen]
        if len(new_ids) > 1:
            groups.append({'ids': new_ids, 'reason': f"Same UPC: {norm_val}"})
            seen.update(new_ids)

    # 2. ASIN
    df[KEY_DB_ASIN] = df[KEY_DB_ASIN].replace('', None)
    asin_dupes = df[df.duplicated(KEY_DB_ASIN, keep=False) & df[KEY_DB_ASIN].notna()]
    for asin, group in asin_dupes.groupby(KEY_DB_ASIN):
        ids = group['id'].tolist()
        new_ids = [i for i in ids if i not in seen]
        if len(new_ids) > 1:
            groups.append({'ids': new_ids, 'reason': f"Same ASIN: {asin}"})
            seen.update(new_ids)

    # 3. Fuzzy
    remaining = df[~df['id'].isin(seen)].copy()
    if not remaining.empty:
        titles = remaining[KEY_DB_TITLE].fillna("").tolist()
        ids = remaining['id'].tolist()
        for i, title1 in enumerate(titles):
            if ids[i] in seen or len(title1) < 4: continue
            current_group = [ids[i]]
            for j, title2 in enumerate(titles):
                if i == j or ids[j] in seen: continue
                ratio = difflib.SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
                if ratio >= threshold:
                    current_group.append(ids[j])
            if len(current_group) > 1:
                groups.append({'ids': current_group, 'reason': "Similar Titles"})
                seen.update(current_group)
    return groups

try:
    conn = create_connection()
    tab_scan, tab_orphan = st.tabs(["🔍 Duplicate Scanner", "🏚️ Old Orphan Manager"])

    with tab_scan:
        st.info("Finds products with matching UPCs, ASINs, or similar titles.")
        if st.button("🚀 Scan for Duplicates"):
            with st.spinner("Scanning..."):
                query = f"SELECT id, {KEY_DB_TITLE}, {KEY_DB_BRAND}, {KEY_DB_MODEL}, {KEY_DB_UPC}, {KEY_DB_ASIN} FROM products ORDER BY {KEY_DB_TITLE}"
                df_prods = pd.read_sql_query(query, conn)
                duplicate_groups = find_duplicates(df_prods)
                if not duplicate_groups:
                    st.success("No duplicates found!")
                    if 'dup_groups' in st.session_state: del st.session_state.dup_groups
                else:
                    st.session_state.dup_groups = duplicate_groups
                    st.rerun()

        if 'dup_groups' in st.session_state and st.session_state.dup_groups:
            st.divider()
            st.subheader(f"Found {len(st.session_state.dup_groups)} Potential Groups")
            groups_to_show = st.session_state.dup_groups.copy()
            for i, group_data in enumerate(groups_to_show):
                group_ids = group_data['ids']
                reason = group_data['reason']
                with st.expander(f"Group #{i+1}: {reason} ({len(group_ids)} items)", expanded=True):
                    placeholders = ",".join("?" * len(group_ids))
                    query = f"""
                        SELECT p.id, p.{KEY_DB_TITLE}, p.{KEY_DB_BRAND}, p.{KEY_DB_MODEL}, p.{KEY_DB_UPC}, p.{KEY_DB_ASIN}, COUNT(i.id) as linked_items 
                        FROM products p 
                        LEFT JOIN auction_items i ON p.id = i.product_id 
                        WHERE p.id IN ({placeholders}) 
                        GROUP BY p.id
                    """
                    group_df = pd.read_sql_query(query, conn, params=group_ids)
                    st.dataframe(group_df, hide_index=True, use_container_width=True)
                    
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        best_candidate = None
                        idx = 0
                        if not group_df.empty:
                            best_candidate = group_df.sort_values(by=['linked_items', KEY_DB_TITLE], ascending=False).iloc[0]['id']
                            idx = group_df[group_df['id'] == best_candidate].index[0].item()
                        
                        keep_id = st.selectbox(
                            f"Select MASTER to keep (Group {i+1})", 
                            group_df['id'].tolist(), 
                            index=idx, 
                            key=f"sel_{i}",
                            format_func=lambda x: f"ID #{x} - {group_df[group_df['id']==x][KEY_DB_TITLE].values[0] if not group_df[group_df['id']==x].empty else 'Unknown'}"
                        )
                    with c2:
                        st.write("")
                        st.write("")
                        if st.button("⚔️ Merge & Fix", key=f"btn_{i}"):
                            # CHECK: Ensure keep_id is not None
                            if keep_id is not None:
                                to_merge = [x for x in group_ids if x != keep_id]
                                if merge_products(conn, int(keep_id), to_merge):
                                    st.success("Merged!")
                                    st.session_state.dup_groups.pop(i)
                                    st.rerun()
                            else:
                                st.error("No Master Product selected.")

    with tab_orphan:
        st.info("Manage products that are not linked to any active/closed auction items.")
        c_filter1, c_filter2 = st.columns(2)
        with c_filter1:
            days_old = st.number_input("Only show items created more than X days ago:", min_value=0, value=30, step=5)
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        orphan_query = f"""
            SELECT p.id, p.{KEY_DB_TITLE}, p.{KEY_DB_BRAND}, p.created_at, p.{KEY_IS_FAV}
            FROM products p
            LEFT JOIN auction_items i ON p.id = i.product_id
            WHERE i.id IS NULL AND p.created_at < ?
        """
        orphan_df = pd.read_sql_query(orphan_query, conn, params=(cutoff_str,))
        
        if orphan_df.empty:
            st.success(f"No orphans older than {days_old} days found.")
        else:
            orphan_df.insert(0, "Delete?", False)
            st.warning(f"Found {len(orphan_df)} products created before {cutoff_str} that are not in use.")
            edited_df = st.data_editor(orphan_df, column_config={"Delete?": st.column_config.CheckboxColumn(required=True, default=False), "created_at": st.column_config.DatetimeColumn(format="YYYY-MM-DD")},
                disabled=["id", KEY_DB_TITLE, KEY_DB_BRAND, "created_at", KEY_IS_FAV], hide_index=True, use_container_width=True, key="orphan_editor")
            to_delete = edited_df[edited_df["Delete?"] == True]
            count_del = len(to_delete)
            if st.button(f"🗑️ Delete {count_del} Selected Items", disabled=count_del==0, type="primary"):
                cursor = conn.cursor()
                ids = to_delete['id'].tolist()
                placeholders = ",".join("?" * len(ids))
                cursor.execute(f"DELETE FROM products WHERE id IN ({placeholders})", ids)
                conn.commit()
                st.success(f"Cleaned {count_del} items!")
                st.rerun()

finally:
    if conn:
        try: conn.close()
        except: pass