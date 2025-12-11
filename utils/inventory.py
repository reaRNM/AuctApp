# utils/inventory.py
import sqlite3
import pandas as pd
import difflib
from typing import Optional, Dict, Any, List, Union

def _clean_str(val: Any) -> Optional[str]:
    """Returns stripped string or None if empty."""
    if val is not None:
        s = str(val).strip()
        if s and s.lower() != "nan" and s.lower() != "none": 
            return s
    return None

def _prepare_product_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts and cleans dictionary for DB insertion."""
    return {
        'title': data.get('title'),
        'brand': data.get('brand'),
        'model': data.get('model'),
        'upc': _clean_str(data.get('upc')),
        'asin': _clean_str(data.get('asin')),
        'category': data.get('category'),
        'msrp': data.get('msrp'),
        'avg_sold_price': data.get('avg_sold_price'),
        'target_list_price': data.get('target_list_price'),
        'shipping_cost_basis': data.get('shipping_cost_basis'),
        'weight_lbs': data.get('weight_lbs'),
        'weight_oz': data.get('weight_oz'),
        'length': data.get('length'),
        'width': data.get('width'),
        'height': data.get('height'),
        'is_irregular': 1 if data.get('is_irregular') else 0,
        
        # eBay Data (Sold)
        'ebay_avg_sold_price': data.get('ebay_avg_sold_price'),
        'ebay_sold_range_low': data.get('ebay_sold_range_low'),
        'ebay_sold_range_high': data.get('ebay_sold_range_high'),
        'ebay_avg_shipping_sold': data.get('ebay_avg_shipping_sold'),
        'ebay_sell_through_rate': data.get('ebay_sell_through_rate'),
        'ebay_total_sold_count': data.get('ebay_total_sold_count'),
        
        # eBay Data (Active)
        'ebay_active_count': data.get('ebay_active_count'),
        'ebay_avg_list_price': data.get('ebay_avg_list_price'),
        'ebay_active_low': data.get('ebay_active_low'),         # NEW
        'ebay_active_high': data.get('ebay_active_high'),       # NEW
        'ebay_avg_shipping_active': data.get('ebay_avg_shipping_active'), # NEW
        
        'market_notes': data.get('market_notes'),

        # Amazon Data
        'amazon_url': data.get('amazon_url'),
        'amazon_new_price': data.get('amazon_new_price'),
        'amazon_used_price': data.get('amazon_used_price'),
        'amazon_sales_rank': data.get('amazon_sales_rank'),
        'amazon_reviews': data.get('amazon_reviews'),
        'amazon_stars': data.get('amazon_stars'),
        'amazon_rank_main': data.get('amazon_rank_main'),
        'amazon_cat_name': data.get('amazon_cat_name'),       # NEW
        'amazon_rank_sub': data.get('amazon_rank_sub'),
        'amazon_subcat_name': data.get('amazon_subcat_name'), # NEW
        
        'notes': data.get('notes'),
        'is_favorite': 1 if data.get('is_favorite') else 0
    }

# ... (keep existing helper functions: _resolve_existing_id, _match_brand_model, _check_for_conflicts, _execute_db_write, _link_items)
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

    # Exact
    match = products_df[
        (products_df['brand'].str.lower().str.strip() == i_brand) & 
        (products_df['model'].str.lower().str.strip() == i_model)
    ]
    if not match.empty: return int(match.iloc[0]['id'])

    # Fuzzy
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