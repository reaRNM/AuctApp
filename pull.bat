@echo off
:: -------------------------------------------------
:: scrape_auction.bat
:: Runs the scraper with the URL you give it
:: -------------------------------------------------

:: Make sure we are in the project folder
cd /d "%~dp0"

:: Activate the virtual environment (adjust if your venv name differs)
call .\.venv\Scripts\activate

:: Run the scraper with the first argument (the URL)
python scraper.py "%~1"

:: Keep the window open so you can see the output
pause