# AuctApp: Auction Intelligence Dashboard

A Streamlit-based ERP system for resellers to track active auctions, manage inventory, and analyze historical pricing.

## Features

* **Active Viewer:** Scan live auctions, flag high-risk items, and cross out junk.
* **Product Library:** Master database to store research (MSRP, Dimensions, Shipping).
* **Auction History:** Track realized prices and automatically update average market values.
* **Smart Linking:** Auto-match auction lots to your Master Product library.

## Setup

1. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2. **Configure Secrets:**
    Create a `.env` file in the root directory and add your HiBid token:

    ```env
    HIBID_TOKEN=Bearer YOUR_TOKEN_HERE
    ```

3. **Run the App:**

    ```bash
    streamlit run viewer.py
    ```

## Workflow

1. **Scrape:** Run `python scraper.py "https://hibid.com/catalog/..."`
2. **View:** Open the Viewer to clean data and link products.
3. **Close:** After auction ends, run `python closer.py "https://hibid.com/catalog/..."` to capture sold prices.
