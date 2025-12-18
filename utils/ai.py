# utils/ai.py
import requests
import json
import base64
import os
import re
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

    # Use 2025 valid models
    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash-latest"]
    
    parts = []
    
    # 1. Prompt
    prompt_text = """
    Analyze these screenshots (eBay Sold, eBay Active, Amazon) and extract product data into this EXACT JSON structure.
    
    JSON Keys required:
    {{
        "{KEY_DB_TITLE}": "Full product title",
        "{KEY_DB_BRAND}": "Brand name",
        "{KEY_DB_MODEL}": "Model number",
        "{KEY_DB_UPC}": "UPC code",
        "{KEY_DB_ASIN}": "ASIN",
        "{KEY_DB_CAT}": "Category Name",
        "{KEY_DB_MSRP}": 0.0,
        
        "{KEY_WEIGHT_LBS}": 0.0, "{KEY_WEIGHT_OZ}": 0.0,
        "{KEY_LENGTH}": 0.0, "{KEY_WIDTH}": 0.0, "{KEY_HEIGHT}": 0.0,
        
        "{KEY_AMZ_STARS}": 0.0, "{KEY_AMZ_REVS}": 0,
        "{KEY_AMZ_RANK_MAIN}": 0, "{KEY_AMZ_CAT_MAIN}": "Category Name",
        "{KEY_AMZ_RANK_SUB}": 0, "{KEY_AMZ_CAT_SUB}": "Subcat Name",
        
        "{KEY_EBAY_AVG_SOLD}": 0.0, "{KEY_EBAY_AVG_SHIP}": 0.0,
        "{KEY_EBAY_STR}": 0.0, "{KEY_EBAY_SOLD_COUNT}": 0,
        "{KEY_EBAY_SELLERS}": 0,
        "{KEY_EBAY_SOLD_LOW}": 0.0, "{KEY_EBAY_SOLD_HIGH}": 0.0,
        
        "{KEY_EBAY_ACTIVE_CNT}": 0, "{KEY_EBAY_LIST_AVG}": 0.0,
        "{KEY_EBAY_ACTIVE_LOW}": 0.0, "{KEY_EBAY_ACTIVE_HIGH}": 0.0, "{KEY_EBAY_ACTIVE_SHIP}": 0.0,
        "{KEY_EBAY_WATCHERS}": 0,
        
        "{KEY_MKT_NOTES}": "Short summary of price distribution"
    }}
    
    RULES:
    - If a field is missing, use null (or 0 for numbers).
    - Convert currency strings to float (remove '$').
    - For percentages, return the absolute number (e.g. 12.5, NOT 0.125).
    
    - WEIGHT RULES (CRITICAL):
      1. If weight is "16 oz", set {KEY_WEIGHT_LBS}=1, {KEY_WEIGHT_OZ}=0.
      2. If weight is decimal pounds (e.g. "5.64 lbs"):
         - Set '{KEY_WEIGHT_LBS}' to the integer part (5).
         - Calculate '{KEY_WEIGHT_OZ}' by multiplying the decimal part by 16 (.64 * 16 = 10.24).
         - Result: {KEY_WEIGHT_LBS}=5, {KEY_WEIGHT_OZ}=10.24.
      3. DO NOT put the pound value into the ounce field.
    
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

    # 3. Request Loop
    last_error = None
    
    for model_name in models_to_try:
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
                    
                    # SAFETY: Clean markdown formatting if present
                    text_content = re.sub(r"```json|```", "", text_content).strip()
                    
                    return json.loads(text_content)
            else:
                error_msg = response.text
                if "404" in str(response.status_code):
                    last_error = f"Model {model_name} not found (404)."
                else:
                    last_error = f"Error {response.status_code}: {error_msg}"
                continue 
                
        except Exception as e:
            last_error = str(e)
            continue

    st.error(f"AI Extraction Failed. Last error: {last_error}")
    return None