# GSMArena Phone Data Scraper

A web application that scrapes mobile phone specifications from GSMArena.com and saves them to a CSV file.

## Features

- Web interface to monitor scraping progress
- Real-time progress updates
- Detailed logging
- Organized phone specifications by category
- CSV export
- Error handling and debugging

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

4. Click "Start Extraction" to begin the scraping process.

## Output Files

- `phones_data.csv`: Contains all scraped phone specifications
- `debug.log`: Contains detailed logging information and any errors

## Note

This scraper includes rate limiting and respects the website by adding delays between requests. For testing purposes, it's limited to 3 brands and 5 phones per brand. You can modify these limits in the `app.py` file.
