from flask import Flask, render_template, jsonify, request
from scraper import GSMArenaScraper
from brand_scanner import BrandScanner
import threading
import queue
import time
from loguru import logger
import os
import csv
import json
import traceback
from typing import Dict, List

app = Flask(__name__)
scraper = GSMArenaScraper()
brand_scanner = BrandScanner()
progress_queue = queue.Queue()

current_status = {
    "message": "",
    "progress": 0,
    "current_brand": "",
    "current_brand_devices": 0,
    "current_brand_progress": 0,
    "brands_processed": 0,
    "total_brands": 0,
    "devices_processed": 0,
    "total_devices": 0,
    "completed_brands": []
}

# Store scanned brands
all_brands = []
scraping_paused = False

def update_status(**kwargs):
    current_status.update(kwargs)
    progress_queue.put(current_status.copy())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan-brands')
def scan_brands():
    try:
        global all_brands
        
        # Use the brand scanner to get brands
        brands = brand_scanner.scan_brands()
        all_brands = brands
        
        # Get detailed cache information
        cache_info = brand_scanner.get_cache_status()
        cache_status = "cached" if brand_scanner.loaded_from_cache else "fresh"
        
        # Create a user-friendly cache message
        if cache_status == "cached":
            cache_message = f"Loaded {cache_info['brand_count']} brands from cache (last updated {cache_info['time_since_update']})"
        else:
            cache_message = f"Freshly scanned {len(brands)} brands from website"
        
        return jsonify({
            "status": "success",
            "cache_status": cache_status,
            "cache_message": cache_message,
            "cache_info": cache_info,
            "brands": [{
                "name": brand["name"],
                "device_count": brand["device_count"],
                "url": brand["url"]
            } for brand in all_brands]
        })
    except Exception as e:
        logger.error(f"Error in scan_brands: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "status": "error", 
            "message": f"Failed to scan brands: {str(e)}"
        }), 500

@app.route('/check-brand-data', methods=['POST'])
def check_brand_data_endpoint():
    """Check if brand data already exists."""
    try:
        data = request.get_json()
        brand_name = data.get('brand_name')
        if not brand_name:
            return jsonify({'status': 'error', 'message': 'Brand name required'})
            
        result = check_brand_data(brand_name)
        return jsonify({
            'status': 'success',
            'exists': result['exists'],
            'device_count': result['device_count']
        })
    except Exception as e:
        logger.error(f"Error in check_brand_data_endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/start', methods=['POST'])
def start_scraping():
    try:
        data = request.get_json()
        selected_brands = data.get('brands', [])
        
        if not selected_brands:
            return jsonify({"status": "error", "message": "No brands selected"})
            
        # Filter all_brands to only include selected ones
        brands_to_scrape = [brand for brand in all_brands if brand["url"] in selected_brands]
        
        # Check if we have any brands to scrape
        if not brands_to_scrape:
            return jsonify({"status": "error", "message": "No valid brands selected"})
            
        # Check each brand for existing data
        brand_checks = []
        for brand in brands_to_scrape:
            result = check_brand_data(brand['name'])
            brand_checks.append({
                'brand': brand,
                'exists': result['exists'],
                'device_count': result['device_count']
            })
        
        # Send brand checks to frontend
        return jsonify({
            'status': 'ready',
            'brand_checks': brand_checks
        })
    except Exception as e:
        logger.error(f"Error starting scraper: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/scrape', methods=['POST'])
def start_scraping_final():
    try:
        data = request.get_json()
        selected_brands = data.get('brands', [])
        delete_existing = data.get('delete_existing', [])
        
        if not selected_brands:
            return jsonify({"status": "error", "message": "No brands selected"})
            
        # Filter all_brands to only include selected ones
        brands_to_scrape = [brand for brand in all_brands if brand["url"] in selected_brands]
        
        global scraping_thread
        scraping_thread = threading.Thread(target=scrape_worker, args=(brands_to_scrape, delete_existing))
        scraping_thread.daemon = True
        scraping_thread.start()
        return jsonify({"status": "started"})
    except Exception as e:
        logger.error(f"Error starting scraper: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/preview-data')
def preview_data():
    try:
        brands_devices = []
        specifications = []
        
        # Read brands and devices
        if os.path.exists(scraper.brands_file):
            with open(scraper.brands_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                brands_devices = list(reader)[:50]  # Limit to 50 entries for preview
        
        # Read specifications
        if os.path.exists(scraper.specs_file):
            with open(scraper.specs_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                specifications = list(reader)[:50]  # Limit to 50 entries for preview
        
        return jsonify({
            'brands_devices': brands_devices,
            'specifications': specifications
        })
    except Exception as e:
        logger.error(f"Error getting preview data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/pause-resume', methods=['POST'])
def pause_resume():
    try:
        global scraping_paused
        data = request.get_json()
        scraping_paused = data.get('paused', False)
        return jsonify({'status': 'paused' if scraping_paused else 'resumed'})
    except Exception as e:
        logger.error(f"Error in pause/resume: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear-cache')
def clear_cache():
    """Clear the brands cache file to force a fresh scan"""
    try:
        cache_file = brand_scanner.cache_file
        if os.path.exists(cache_file):
            os.remove(cache_file)
            logger.info(f"Cache file {cache_file} deleted successfully")
            return jsonify({
                "status": "success",
                "message": "Cache cleared successfully"
            })
        else:
            logger.info("No cache file found to delete")
            return jsonify({
                "status": "success",
                "message": "No cache file found"
            })
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"Failed to clear cache: {str(e)}"
        }), 500

def scrape_worker(brands_to_scrape: List[Dict], delete_existing: List[str] = None):
    """Scrape worker with option to delete existing data for specific brands."""
    try:
        # Start scraping
        update_status(
            message="Starting data extraction...",
            progress=0,
            brands_processed=0,
            devices_processed=0
        )
        
        # Initialize delete_existing if None
        if delete_existing is None:
            delete_existing = []
            
        # Create files with headers if they don't exist
        if not os.path.exists(scraper.brands_file):
            with open(scraper.brands_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['brand_name', 'device_name', 'device_url', 'device_image'])
        
        if not os.path.exists(scraper.specs_file):
            with open(scraper.specs_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['device_url', 'name', 'pictures', 'specifications'])
        
        # If delete_existing contains brand URLs, selectively delete data for those brands
        if delete_existing:
            # Get brand names from URLs
            brand_names_to_delete = []
            for brand_url in delete_existing:
                for brand in brands_to_scrape:
                    if brand['url'] == brand_url:
                        brand_names_to_delete.append(brand['name'])
                        break
            
            if brand_names_to_delete:
                # Process brands_devices.csv - remove entries for selected brands
                if os.path.exists(scraper.brands_file):
                    temp_brands_file = scraper.brands_file + '.temp'
                    with open(scraper.brands_file, 'r', encoding='utf-8') as input_file, \
                         open(temp_brands_file, 'w', newline='', encoding='utf-8') as output_file:
                        reader = csv.reader(input_file)
                        writer = csv.writer(output_file)
                        
                        # Write header
                        header = next(reader)
                        writer.writerow(header)
                        
                        # Get device URLs to delete
                        device_urls_to_delete = set()
                        
                        # First pass to collect device URLs to delete
                        input_file.seek(0)
                        next(reader)  # Skip header
                        for row in reader:
                            if row and row[0] in brand_names_to_delete:
                                device_urls_to_delete.add(row[2])  # device_url is at index 2
                        
                        # Second pass to write rows that should be kept
                        input_file.seek(0)
                        next(reader)  # Skip header
                        for row in reader:
                            if row and row[0] not in brand_names_to_delete:
                                writer.writerow(row)
                    
                    # Replace original file with temp file
                    os.replace(temp_brands_file, scraper.brands_file)
                    
                    # Process device_specifications.csv - remove entries for selected brands' devices
                    if os.path.exists(scraper.specs_file):
                        temp_specs_file = scraper.specs_file + '.temp'
                        with open(scraper.specs_file, 'r', encoding='utf-8') as input_file, \
                             open(temp_specs_file, 'w', newline='', encoding='utf-8') as output_file:
                            reader = csv.reader(input_file)
                            writer = csv.writer(output_file)
                            
                            # Write header
                            header = next(reader)
                            writer.writerow(header)
                            
                            # Write rows that should be kept
                            for row in reader:
                                if row and row[0] not in device_urls_to_delete:
                                    writer.writerow(row)
                        
                        # Replace original file with temp file
                        os.replace(temp_specs_file, scraper.specs_file)
                
                update_status(
                    message=f"Deleted data for {len(brand_names_to_delete)} brands: {', '.join(brand_names_to_delete)}"
                )
        
        # Calculate total devices
        total_devices = sum(brand['device_count'] for brand in brands_to_scrape)
        update_status(
            total_devices=total_devices,
            total_brands=len(brands_to_scrape)
        )
        
        # Process each brand
        devices_processed = 0
        for brand_idx, brand in enumerate(brands_to_scrape, 1):
            # Check if paused
            while scraping_paused:
                time.sleep(1)
                continue
                
            # Update status for current brand
            brand_name = brand['name']
            brand_devices = brand['device_count']
            
            update_status(
                message=f"Processing brand: {brand_name}",
                current_brand=brand_name,
                current_brand_devices=brand_devices,
                current_brand_progress=0,
                brands_processed=brand_idx
            )
            
            # Get devices for current brand
            devices = scraper.get_devices_from_brand(brand['url'])
            total_brand_devices = len(devices)
            
            # Save devices and their specs
            for device_idx, device in enumerate(devices, 1):
                # Check if paused
                while scraping_paused:
                    time.sleep(1)
                    continue
                    
                device_progress = (device_idx / total_brand_devices) * 100
                update_status(
                    message=f"Processing {device['name']} ({device_idx}/{total_brand_devices})",
                    current_brand_progress=device_progress,
                    devices_processed=devices_processed + device_idx
                )
                
                # Process device specs
                specs = scraper.get_device_specs(device['url'])
                if specs:
                    with open(scraper.brands_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([brand_name, device['name'], device['url'], device['image_url']])
                    
                    with open(scraper.specs_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([device['url'], specs.get('name', ''), specs.get('pictures', '[]'), json.dumps(specs)])
                
                time.sleep(1)  # Respect the website
            
            # Update completed brands
            devices_processed += total_brand_devices
            completed_brand = {
                'name': brand_name,
                'devices': total_brand_devices,
                'expected': brand_devices
            }
            current_status['completed_brands'].append(completed_brand)
            
            # Calculate overall progress
            overall_progress = (devices_processed / total_devices) * 100
            update_status(progress=overall_progress)
        
        update_status(
            message="Data extraction completed successfully!",
            progress=100
        )
    except Exception as e:
        logger.error(f"Error in scraper: {str(e)}")
        update_status(message=f"Error: {str(e)}")

@app.route('/progress')
def get_progress():
    try:
        # Get latest status without blocking
        status = current_status.copy()
        while not progress_queue.empty():
            status = progress_queue.get_nowait()
        return jsonify(status)
    except queue.Empty:
        return jsonify(current_status)

def check_brand_data(brand_name: str) -> Dict:
    """Check if brand data already exists in files."""
    try:
        existing_brands = set()
        # Check brands_devices.csv
        if os.path.exists(scraper.brands_file):
            with open(scraper.brands_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                existing_brands.update(row[0] for row in reader)
        
        # Check device_specifications.csv
        existing_devices = set()
        if os.path.exists(scraper.specs_file):
            with open(scraper.specs_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                existing_devices.update(row[0] for row in reader)
        
        return {
            'exists': brand_name in existing_brands,
            'device_count': len(existing_devices)
        }
    except Exception as e:
        logger.error(f"Error checking brand data: {str(e)}")
        return {'exists': False, 'device_count': 0}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
