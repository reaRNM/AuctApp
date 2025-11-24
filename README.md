# AuctApp

An auction data scraping and analysis application for HiBid auctions.

## Features

- **Auction Scraping**: Extract auction data from HiBid
- **Data Analysis**: Track product performance and statistics
- **Auction Closing**: Process final prices and update records
- **Web Interface**: Streamlit-based dashboard for viewing data

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd AuctApp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Scrape Auction Data
```bash
python scraper.py <auction_url>
```

### Close Auction (Update Final Prices)
```bash
python closer.py <auction_url>
```

### View Dashboard
```bash
streamlit run viewer.py
```

## Project Structure

- `scraper.py` - Main auction data scraper
- `closer.py` - Auction closing and final price updates
- `viewer.py` - Streamlit dashboard
- `utils/` - Database and analytics utilities
- `components/` - UI components for the dashboard
- `pages/` - Additional dashboard pages

## Requirements

See `requirements.txt` for Python dependencies.