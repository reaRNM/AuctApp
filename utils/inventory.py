# utils/inventory.py
import sqlite3
import pandas as pd
import difflib
from typing import Optional, Dict, Any, List, Union
# NEW: Import Constants
from utils.parse import (
    KEY_DB_TITLE, KEY_DB_BRAND, KEY_DB_MODEL, KEY_DB_UPC, KEY_DB_ASIN, KEY_DB_CAT, KEY_DB_MSRP, KEY_DB_AVG_SOLD,
    KEY_DB_TARGET, KEY_SHIP_COST, KEY_DB_NOTES, KEY_IS_FAV,
    KEY_WEIGHT_LBS, KEY_WEIGHT_OZ, KEY_LENGTH, KEY_WIDTH, KEY_HEIGHT, KEY_IRREGULAR,
    KEY_EBAY_AVG_SOLD, KEY_EBAY_SOLD_LOW, KEY_EBAY_SOLD_HIGH, KEY_EBAY_AVG_SHIP, KEY_EBAY_STR,
    KEY_EBAY_SOLD_COUNT, KEY_EBAY_SELLERS, KEY_EBAY_ACTIVE_CNT, KEY_EBAY_LIST_AVG,
    KEY_EBAY_ACTIVE_LOW, KEY_EBAY_ACTIVE_HIGH, KEY_EBAY_ACTIVE_SHIP, KEY_EBAY_WATCHERS, KEY_MKT_NOTES,
    KEY_AMZ_URL, KEY_AMZ_NEW, KEY_AMZ_USED, KEY_AMZ_LIST, KEY_AMZ_RANK, KEY_AMZ_REVS, KEY_AMZ_STARS,
    KEY_AMZ_RANK_MAIN, KEY_AMZ_CAT_MAIN, KEY_AMZ_RANK_SUB, KEY_AMZ_CAT_SUB
)

# ... (Keep existing helpers: _clean_str, _prepare_product_fields, etc.) ...
def _clean_str(val: Any) -> Optional[str]:
    if val is not None:
        s = str(val).strip()
        if s and s.lower() != "nan" and s.lower() != "none": return s
    return None

def _prepare_product_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        KEY_DB_TITLE: data.get(KEY_DB_TITLE),
        KEY_DB_BRAND: data.get(KEY_DB_BRAND),
        KEY_DB_MODEL: data.get(KEY_DB_MODEL),
        KEY_DB_UPC: _clean_str(data.get(KEY_DB_UPC)),
        KEY_DB_ASIN: _clean_str(data.get(KEY_DB_ASIN)),
        KEY_DB_CAT: data.get(KEY_DB_CAT),
        KEY_DB_MSRP: data.get(KEY_DB_MSRP),
        KEY_DB_AVG_SOLD: data.get(KEY_DB_AVG_SOLD),
        KEY_DB_TARGET: data.get(KEY_DB_TARGET),
        KEY_SHIP_COST: data.get(KEY_SHIP_COST),
        KEY_DB_NOTES: data.get(KEY_DB_NOTES),
        KEY_IS_FAV: 1 if data.get(KEY_IS_FAV) else 0,
        
        # Physical
        KEY_WEIGHT_LBS: data.get(KEY_WEIGHT_LBS),
        KEY_WEIGHT_OZ: data.get(KEY_WEIGHT_OZ),
        KEY_LENGTH: data.get(KEY_LENGTH),
        KEY_WIDTH: data.get(KEY_WIDTH),
        KEY_HEIGHT: data.get(KEY_HEIGHT),
        KEY_IRREGULAR: 1 if data.get(KEY_IRREGULAR) else 0,
        
        # eBay Data
        KEY_EBAY_AVG_SOLD: data.get(KEY_EBAY_AVG_SOLD),
        KEY_EBAY_SOLD_LOW: data.get(KEY_EBAY_SOLD_LOW),
        KEY_EBAY_SOLD_HIGH: data.get(KEY_EBAY_SOLD_HIGH),
        KEY_EBAY_AVG_SHIP: data.get(KEY_EBAY_AVG_SHIP),
        KEY_EBAY_STR: data.get(KEY_EBAY_STR),
        KEY_EBAY_SOLD_COUNT: data.get(KEY_EBAY_SOLD_COUNT),
        KEY_EBAY_SELLERS: data.get(KEY_EBAY_SELLERS),
        KEY_EBAY_ACTIVE_CNT: data.get(KEY_EBAY_ACTIVE_CNT),
        KEY_EBAY_LIST_AVG: data.get(KEY_EBAY_LIST_AVG),
        KEY_EBAY_ACTIVE_LOW: data.get(KEY_EBAY_ACTIVE_LOW),
        KEY_EBAY_ACTIVE_HIGH: data.get(KEY_EBAY_ACTIVE_HIGH),
        KEY_EBAY_ACTIVE_SHIP: data.get(KEY_EBAY_ACTIVE_SHIP),
        KEY_EBAY_WATCHERS: data.get(KEY_EBAY_WATCHERS),
        KEY_MKT_NOTES: data.get(KEY_MKT_NOTES),

        # Amazon Data
        KEY_AMZ_URL: data.get(KEY_AMZ_URL),
        KEY_AMZ_NEW: data.get(KEY_AMZ_NEW),
        KEY_AMZ_USED: data.get(KEY_AMZ_USED),
        KEY_AMZ_LIST: data.get(KEY_AMZ_LIST),
        KEY_AMZ_RANK: data.get(KEY_AMZ_RANK),
        KEY_AMZ_REVS: data.get(KEY_AMZ_REVS),
        KEY_AMZ_STARS: data.get(KEY_AMZ_STARS),
        KEY_AMZ_RANK_MAIN: data.get(KEY_AMZ_RANK_MAIN),
        KEY_AMZ_CAT_MAIN: data.get(KEY_AMZ_CAT_MAIN),
        KEY_AMZ_RANK_SUB: data.get(KEY_AMZ_RANK_SUB),
        KEY_AMZ_CAT_SUB: data.get(KEY_AMZ_CAT_SUB),
    }

# ... (Keep helpers: _resolve_existing_id, _match_brand_model, _check_for_conflicts, _execute_db_write, _link_items) ...
def _resolve_existing_id(cursor: sqlite3.Cursor, data_id: Optional[int], 
                        upc: Optional[str], asin: Optional[str]) -> Optional[int]:
    if data_id: return data_id
    if upc:
        res = cursor.execute("SELECT id FROM products WHERE upc = ?", (upc,)).fetchone()
        if res: return res[0]
    if asin:
        res = cursor.execute("SELECT id FROM products WHERE asin = ?", (asin,)).fetchone()
        if res: return res[0]
    return None

def _match_brand_model(item: pd.Series, products_df: pd.DataFrame) -> Optional[int]:
    if not (item.get('brand') and item.get('model')): return None
    i_brand = str(item['brand']).strip().lower()
    i_model = str(item['model']).strip().lower()
    if len(i_brand) < 2 or len(i_model) < 2: return None
    match = products_df[
        (products_df['brand'].str.lower().str.strip() == i_brand) & 
        (products_df['model'].str.lower().str.strip() == i_model)
    ]
    if not match.empty: return int(match.iloc[0]['id'])
    for _, prod in products_df.iterrows():
        p_brand = str(prod['brand']).lower().strip()
        p_model = str(prod['model']).lower().strip()
        brand_score = difflib.SequenceMatcher(None, i_brand, p_brand).ratio()
        model_score = difflib.SequenceMatcher(None, i_model, p_model).ratio()
        if brand_score > 0.85 and model_score > 0.85:
            return int(prod['id'])
    return None

def _check_for_conflicts(cursor: sqlite3.Cursor, product_id: int, upc: Optional[str], asin: Optional[str]) -> int:
    target_id = product_id
    if upc:
        conflict = cursor.execute("SELECT id FROM products WHERE upc = ? AND id != ?", (upc, product_id)).fetchone()
        if conflict: target_id = conflict[0]
    if asin:
        conflict = cursor.execute("SELECT id FROM products WHERE asin = ? AND id != ?", (asin, product_id)).fetchone()
        if conflict: target_id = conflict[0]
    return target_id

def _execute_db_write(cursor: sqlite3.Cursor, product_id: Optional[int], fields: Dict[str, Any]) -> Optional[int]:
    try:
        if product_id:
            final_id = _check_for_conflicts(cursor, product_id, fields['upc'], fields['asin'])
            set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
            values = list(fields.values()) + [final_id]
            cursor.execute(f"UPDATE products SET {set_clause} WHERE id = ?", values)
            return final_id
        else:
            cols = ", ".join(fields.keys())
            placeholders = ", ".join(["?"] * len(fields))
            values = list(fields.values())
            cursor.execute(f"INSERT INTO products ({cols}) VALUES ({placeholders})", values)
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def _link_items(cursor: sqlite3.Cursor, product_id: int, link_item_ids: Union[int, List[int], None]):
    if not link_item_ids: return
    ids_to_link = [link_item_ids] if isinstance(link_item_ids, int) else link_item_ids
    if ids_to_link:
        placeholders = ",".join(["?"] * len(ids_to_link))
        cursor.execute(f"UPDATE auction_items SET product_id = ? WHERE id IN ({placeholders})", [product_id] + ids_to_link)

def get_product_by_id(conn: sqlite3.Connection, product_id: int) -> Optional[pd.Series]:
    if not product_id: return None
    try:
        df = pd.read_sql_query("SELECT * FROM products WHERE id = ?", conn, params=(product_id,))
        if not df.empty: return df.iloc[0]
    except Exception: pass
    return None

def delete_product(conn: sqlite3.Connection, product_id: int) -> bool:
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE auction_items SET product_id = NULL WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        return True
    except Exception: return False

def save_product_to_library(conn: sqlite3.Connection, data: Dict[str, Any], link_item_ids: Union[int, List[int], None] = None) -> Optional[int]:
    cursor = conn.cursor()
    fields = _prepare_product_fields(data)
    product_id = _resolve_existing_id(cursor, data.get('id'), fields['upc'], fields['asin'])
    final_id = _execute_db_write(cursor, product_id, fields)
    if final_id: _link_items(cursor, final_id, link_item_ids)
    conn.commit()
    return final_id

def auto_link_products(conn: sqlite3.Connection, auction_id: Optional[int] = None) -> int:
    cursor = conn.cursor()
    query = "SELECT id, title, brand, model, upc, asin FROM auction_items WHERE product_id IS NULL"
    if auction_id is not None: query += f" AND auction_id = {auction_id}"
    
    items = pd.read_sql_query(query, conn)
    linked_count = 0
    products_df = pd.read_sql_query("SELECT id, upc, asin, brand, model FROM products", conn)
    
    for _, item in items.iterrows():
        p_id = _find_product_match(item, products_df)
        if p_id:
            cursor.execute("UPDATE auction_items SET product_id = ? WHERE id = ?", (p_id, item['id']))
            linked_count += 1
            
    conn.commit()
    return linked_count

def _find_product_match(item: pd.Series, products_df: pd.DataFrame) -> Optional[int]:
    if item.get('upc') and str(item['upc']).strip():
        match = products_df[products_df['upc'] == item['upc']]
        if not match.empty: return int(match.iloc[0]['id'])
            
    if item.get('asin') and str(item['asin']).strip():
        match = products_df[products_df['asin'] == item['asin']]
        if not match.empty: return int(match.iloc[0]['id'])
            
    return _match_brand_model(item, products_df)

# === NEW MERGE LOGIC ===
def merge_products(conn: sqlite3.Connection, keep_id: int, merge_ids: List[int]) -> bool:
    """
    Merges duplicate products into a single Master record.
    1. Moves auction items to Master.
    2. Copies missing data from duplicates to Master.
    3. Deletes duplicates.
    """
    if not merge_ids: return False
    
    cursor = conn.cursor()
    
    # 1. Get Master Record
    master = get_product_by_id(conn, keep_id)
    if master is None: return False
    master_data = master.to_dict()
    
    updates = {}
    
    # 2. Iterate through Duplicates to find missing data
    for mid in merge_ids:
        dup = get_product_by_id(conn, mid)
        if dup is None: continue
        dup_data = dup.to_dict()
        
        for key, val in dup_data.items():
            # If Master is empty but Duplicate has value, copy it
            if key in master_data and (master_data[key] is None or master_data[key] == "" or master_data[key] == 0):
                if val is not None and val != "" and val != 0:
                    master_data[key] = val # Update local ref
                    updates[key] = val     # Queue for DB update

    # 3. Update Master with new found data
    if updates:
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [keep_id]
        cursor.execute(f"UPDATE products SET {set_clause} WHERE id = ?", values)

    # 4. Move Auction Items
    placeholders = ",".join("?" * len(merge_ids))
    sql_relink = f"UPDATE auction_items SET product_id = ? WHERE product_id IN ({placeholders})"
    cursor.execute(sql_relink, [keep_id] + merge_ids)
    
    # 5. Delete Duplicates
    sql_delete = f"DELETE FROM products WHERE id IN ({placeholders})"
    cursor.execute(sql_delete, merge_ids)
    
    conn.commit()
    return True