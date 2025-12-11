# utils/ai.py
import requests
import json
import base64
import os
import streamlit as st
from dotenv import load_dotenv

# Force reload of .env file
load_dotenv(override=True)

def get_api_key():
    """Retrieves the API key from .env."""
    key = os.getenv("GOOGLE_API_KEY", "")
    return key.strip() if key else None

def extract_data_with_gemini(uploaded_files):
    """Sends images to Gemini using specific model versions."""
    api_key = get_api_key()
    
    if not api_key:
        st.error("⚠️ GOOGLE_API_KEY missing from .env file.")
        return None

    # UPDATED: Use 2025 valid models (1.5 is deprecated)
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    parts = []
    
    # 1. Prompt
    prompt_text = """
    Analyze these screenshots (eBay Sold, eBay Active, Amazon) and extract product data into this EXACT JSON structure.
    
    JSON Keys required:
    {
        "title": "Full product title",
        "brand": "Brand name",
        "model": "Model number",
        "upc": "UPC code",
        "asin": "ASIN",
        "weight_lbs": 0.0, "weight_oz": 0.0,
        "length": 0.0, "width": 0.0, "height": 0.0,
        "amazon_stars": 0.0, "amazon_reviews": 0,
        "amazon_rank_main": 0, "amazon_cat_name": "Category Name",
        "amazon_rank_sub": 0, "amazon_subcat_name": "Subcat Name",
        "ebay_avg_sold_price": 0.0, "ebay_avg_shipping_sold": 0.0,
        "ebay_sell_through_rate": 0.0, "ebay_total_sold_count": 0,
        "ebay_sold_range_low": 0.0, "ebay_sold_range_high": 0.0,
        "ebay_active_count": 0, "ebay_avg_list_price": 0.0,
        "ebay_active_low": 0.0, "ebay_active_high": 0.0, "ebay_avg_shipping_active": 0.0,
        "market_notes": "Short summary of price distribution"
    }
    
    RULES:
    - If a field is missing, use null (or 0 for numbers).
    - Convert currency strings to float (remove '$').
    - Return ONLY valid JSON.
    """
    parts.append({"text": prompt_text})

    # 2. Encode Images
    for file in uploaded_files:
        bytes_data = file.getvalue()
        b64_data = base64.b64encode(bytes_data).decode('utf-8')
        parts.append({
            "inline_data": {
                "mime_type": file.type,
                "data": b64_data
            }
        })

    # 3. Request Loop (Try models until one works)
    last_error = None
    
    for model_name in models_to_try:
        # Using v1beta endpoint which supports the newer models
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        
        try:
            response = requests.post(
                url, 
                headers={"Content-Type": "application/json"}, 
                params={"key": api_key}, 
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    text_content = result['candidates'][0]['content']['parts'][0]['text']
                    return json.loads(text_content)
            else:
                # Log error and try next model
                error_msg = response.text
                if "404" in str(response.status_code):
                    last_error = f"Model {model_name} not found (404)."
                else:
                    last_error = f"Error {response.status_code}: {error_msg}"
                continue 
                
        except Exception as e:
            last_error = str(e)
            continue

    # If we get here, all models failed
    st.error(f"AI Extraction Failed. Last error: {last_error}")
    return None