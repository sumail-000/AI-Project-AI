from flask import Flask, render_template, jsonify, request, Response
from scraper import GSMArenaScraper
from brand_scanner import BrandScanner
from incremental_scraper import IncrementalScraper
from api import api_bp, limiter
import threading
import queue
import time
import json
import os
import csv
import logging
from loguru import logger
from typing import Dict, List
import traceback  # Add this import for better error reporting
from ai_assistant import DeviceAIAssistant  # Import the AI assistant
from responses import RECOMMENDATION_KEYWORDS, DEVICE_TEMPLATES, COMPARISON_KEYWORDS, FALLBACK_RESPONSES
import asyncio
import aiohttp
from datetime import datetime  # Add datetime module for timestamp generation

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'your-secret-key'
app.register_blueprint(api_bp)
limiter.init_app(app)
scraper = GSMArenaScraper()
incremental_scraper = IncrementalScraper()
brand_scanner = BrandScanner()
ai_assistant = DeviceAIAssistant()  # Initialize the AI assistant
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

# Maximum size for the progress queue
MAX_QUEUE_SIZE = 1000

def update_status(**kwargs):
    global current_status
    # Update the current status
    current_status.update(kwargs)
    
    # Create a timestamped message for the queue
    status_copy = current_status.copy()
    status_copy['timestamp'] = time.time()
    
    # Log the message to help with debugging
    if 'message' in kwargs:
        logger.debug(f"Progress update: {kwargs['message']}")
    
    # Ensure the queue doesn't get too large
    try:
        if progress_queue.qsize() > MAX_QUEUE_SIZE:
            # Clear half of the queue if it gets too large
            for _ in range(MAX_QUEUE_SIZE // 2):
                try:
                    progress_queue.get_nowait()
                except queue.Empty:
                    break
    except Exception as e:
        logger.error(f"Error managing queue size: {str(e)}")
    
    # Add the new status to the queue
    try:
        progress_queue.put(status_copy)
    except Exception as e:
        logger.error(f"Error adding to progress queue: {str(e)}")

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

@app.route('/train-conversation', methods=['POST'])
def train_conversation():
    try:
        data = request.get_json()
        user_input = data.get('user_input')
        category = data.get('category')
        response = data.get('response')
        
        if not all([user_input, category, response]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters: user_input, category, and response are required'
            })
        
        success = ai_assistant.train_conversation_model(user_input, category, response)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Successfully trained model with new {category} response'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to train model'
            })
    except Exception as e:
        app.logger.error(f"Error in train conversation API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"An error occurred: {str(e)}"
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

@app.route('/incremental-update', methods=['POST'])
def start_incremental_update():
    try:
        data = request.get_json()
        selected_brands = data.get('brands', [])
        
        if not selected_brands:
            return jsonify({"status": "error", "message": "No brands selected"})
            
        # Filter all_brands to only include selected ones
        brands_to_scrape = [brand for brand in all_brands if brand["url"] in selected_brands]
        
        # Reset status for new scraping session
        global current_status
        current_status = {
            'message': 'Starting incremental update...',
            'progress': 0,
            'current_brand': '',
            'current_brand_devices': 0,
            'current_brand_progress': 0,
            'brands_processed': 0,
            'devices_processed': 0,
            'total_brands': 0,
            'total_devices': 0,
            'completed_brands': [],
            'is_incremental': True
        }
        
        # Start the incremental update in a separate thread
        global scraping_thread
        scraping_thread = threading.Thread(target=incremental_update_worker, args=(brands_to_scrape,))
        scraping_thread.daemon = True
        scraping_thread.start()
        
        return jsonify({"status": "started"})
    except Exception as e:
        logger.error(f"Error starting incremental update: {str(e)}")
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

@app.route('/get-extracted-brands')
def get_extracted_brands():
    try:
        # Dictionary to store brand data
        extracted_brands = {}
        
        # Read from brands_devices.csv to get all brands and their devices
        if os.path.exists(scraper.brands_file):
            with open(scraper.brands_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 3:  # Ensure row has enough data
                        brand_name = row[0]
                        if brand_name not in extracted_brands:
                            extracted_brands[brand_name] = {
                                'name': brand_name,
                                'devices': 0,
                                'expected': 0  # We don't know the expected count from CSV
                            }
                        extracted_brands[brand_name]['devices'] += 1
        
        # Convert to list for the response
        brands_list = list(extracted_brands.values())
        
        return jsonify({
            'status': 'success',
            'brands': brands_list
        })
    except Exception as e:
        logger.error(f"Error getting extracted brands: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/progress')
def get_progress():
    try:
        # Create a copy of the current status to avoid race conditions
        status = current_status.copy()
        
        # Get the latest status from the queue without blocking
        latest_status = None
        latest_timestamp = 0
        
        # Process all available items in the queue
        items_to_process = min(progress_queue.qsize(), 50)  # Limit to 50 items at a time
        
        for _ in range(items_to_process):
            try:
                queue_status = progress_queue.get_nowait()
                # Keep the status with the most recent timestamp
                if 'timestamp' in queue_status and queue_status['timestamp'] > latest_timestamp:
                    latest_status = queue_status
                    latest_timestamp = queue_status['timestamp']
            except queue.Empty:
                break
        
        # If we found a newer status in the queue, use it
        if latest_status:
            # Remove the timestamp before sending to frontend
            if 'timestamp' in latest_status:
                del latest_status['timestamp']
            status = latest_status
        
        # Log the status being sent to help with debugging
        if 'message' in status:
            logger.debug(f"Sending progress to frontend: {status['message']}")
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error in get_progress: {str(e)}")
        return jsonify(current_status)

@app.route('/api-management')
def api_management():
    """Render the API management page."""
    return render_template('api.html')

@app.route('/api-docs')
def api_docs():
    """Render the API documentation page."""
    return render_template('swagger.html')

@app.route('/ai-assistant')
def ai_assistant_page():
    """Render the AI assistant page."""
    return render_template('ai_assistant.html')

@app.route('/device-search-api', methods=['POST'])
def device_search_api():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Query is required',
                'devices': []
            })
        
        # Process the search query using our simplified AI assistant
        results = ai_assistant.process_query(query)
        
        return jsonify({
            'status': 'success',
            'devices': results.get('devices', [])
        })
    except Exception as e:
        app.logger.error(f"Error in device search API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"An error occurred: {str(e)}",
            'devices': []
        })

@app.route('/ai-assistant-api', methods=['POST'])
def ai_assistant_api():
    """API endpoint for the AI assistant with advanced query analysis."""
    try:
        print("=== AI ASSISTANT API CALLED ===")
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            print("Error: No query provided")
            return jsonify({'status': 'error', 'message': 'Query required'})
        
        print(f"Processing query: {query}")
        
        # Perform comprehensive query analysis using our new algorithm
        query_analysis = ai_assistant.analyze_query_intent(query)
        
        # Log key analysis results
        print(f"Query analysis results:")
        print(f"- Primary intent: {query_analysis['primary_intent']}")
        print(f"- Response type: {query_analysis['response_type']}")
        print(f"- Detected devices: {len(query_analysis['entities']['devices'])}")
        print(f"- Detected specifications: {query_analysis['entities']['specifications']}")
        
        # Extract key analysis components
        response_type = query_analysis['response_type']
        primary_intent = query_analysis['primary_intent']
        devices = query_analysis['entities']['devices']
        specifications = query_analysis['entities']['specifications']
        features = query_analysis['entities']['features']
        brands = query_analysis['entities']['brands']
        
        # Convert devices to the format used by existing methods
        device_names = []
        for device in devices:
            if isinstance(device, dict) and 'brand' in device and 'device' in device:
                device_names.append({
                    'brand': device['brand'],
                    'device': device['device']
                })
        
        # Handle different response types
        if response_type == "comparison":
            print("Handling comparison request")
            comparison_result = ai_assistant.compare_devices(query)
            
            if comparison_result.get('success', False):
                print(f"Returning comparison. Devices: {len(comparison_result.get('devices', []))}")
                try:
                    # Ensure all data is serializable
                    devices = comparison_result.get('devices', [])
                    compared_specs = comparison_result.get('compared_specs', {})
                    
                    # Convert any non-serializable data in compared_specs
                    for spec_key, spec_values in compared_specs.items():
                        for i, spec_value in enumerate(spec_values):
                            if 'value' in spec_value and not isinstance(spec_value['value'], (str, dict, list, int, float, bool, type(None))):
                                # Convert non-serializable value to string
                                spec_values[i]['value'] = str(spec_value['value'])
                    
                    return jsonify({
                        'status': 'success',
                        'response': {
                            'type': 'comparison',
                            'summary': comparison_result.get('summary', 'Here\'s a comparison:'),
                            'devices': devices,
                            'compared_specs': compared_specs
                        }
                    })
                except TypeError as e:
                    print(f"Serialization error: {str(e)}")
                    # Fallback to text response in case of serialization error
                    return jsonify({
                        'status': 'success',
                        'response': {
                            'type': 'text',
                            'content': f"I found information about these devices, but encountered an error preparing the comparison: {str(e)}"
                        }
                    })
            else:
                # Return error message if comparison failed
                return jsonify({
                    'status': 'success',
                    'response': {
                        'type': 'text',
                        'content': comparison_result.get('message', FALLBACK_RESPONSES['no_comparison_devices'])
                    }
                })
                
        elif response_type in ["device_specs", "device_feature"] and device_names:
            print(f"Handling device specifications request for {device_names}")
            # Find the device in the database
            devices_df = ai_assistant._search_devices_by_name(device_names)
            
            if not devices_df.empty:
                # Format device data
                device = ai_assistant._format_device_data(devices_df.iloc[0])
                
                # Get specifications to display
                spec_categories = specifications
                if response_type == "device_feature" and features:
                    # Map features to specification categories
                    feature_to_spec = {
                        "camera": ["camera", "main_camera", "selfie_camera"],
                        "battery": ["battery", "battery_life", "charging"],
                        "performance": ["processor", "cpu", "chipset", "platform"],
                        "display": ["display", "screen"]
                    }
                    
                    for feature in features:
                        if feature in feature_to_spec:
                            spec_categories.extend(feature_to_spec[feature])
                
                # Extract the requested specifications
                requested_specs = ai_assistant._extract_requested_specs(
                    device.get('specifications', {}), 
                    spec_categories
                )
                
                # Format response for frontend
                formatted_response = {
                    'type': 'device_specs',
                    'summary': f"Here are the specifications for {device['brand_name']} {device['device_name']}:",
                    'device': {
                        'name': f"{device['brand_name']} {device['device_name']}",
                        'image_url': device.get('device_image', ''),
                        'url': device.get('device_url', ''),
                        'specifications': device.get('specifications', {}),
                        'requested_specs': requested_specs,
                        'spec_types': spec_categories
                    }
                }
                
                # Add pictures if available
                if 'pictures' in device:
                    formatted_response['device']['pictures'] = device['pictures']
                    
                return jsonify({'status': 'success', 'response': formatted_response})
            else:
                print(f"No device found matching: {device_names}")
                return jsonify({
                    'status': 'success',
                    'response': {
                        'type': 'text',
                        'content': FALLBACK_RESPONSES['no_device_found']
                    }
                })
                
        elif response_type == "device_details" and device_names:
            print(f"Handling device details request for {device_names}")
            # Find the device in the database
            devices_df = ai_assistant._search_devices_by_name(device_names)
            
            if not devices_df.empty:
                # Format device data
                device = ai_assistant._format_device_data(devices_df.iloc[0])
                
                # Format response for frontend
                formatted_response = {
                    'type': 'device_details',
                    'summary': f"Here's information about {device['brand_name']} {device['device_name']}:",
                    'device': {
                        'name': f"{device['brand_name']} {device['device_name']}",
                        'image_url': device.get('device_image', ''),
                        'url': device.get('device_url', ''),
                        'specifications': device.get('specifications', {})
                    }
                }
                
                # Add pictures if available
                if 'pictures' in device:
                    formatted_response['device']['pictures'] = device['pictures']
                    
                return jsonify({'status': 'success', 'response': formatted_response})
            else:
                print(f"No device found matching: {device_names}")
                return jsonify({
                    'status': 'success',
                    'response': {
                        'type': 'text',
                        'content': FALLBACK_RESPONSES['no_device_found']
                    }
                })
                
        elif response_type in ["recommendations", "feature_recommendations", "general_recommendations"]:
            print("Handling recommendations request")
            # Get recommendations based on query
            recommendations = ai_assistant.get_device_recommendations(query)
            
            if recommendations:
                # Determine message based on features or brands
                if features and len(features) > 0:
                    message = DEVICE_TEMPLATES['recommendation_specific'].format(feature=features[0])
                elif brands and len(brands) > 0:
                    message = DEVICE_TEMPLATES['recommendation_brand'].format(brand=brands[0])
                else:
                    message = DEVICE_TEMPLATES['recommendation_intro']
                
                print(f"Returning {len(recommendations)} recommendations with message: {message}")
                return jsonify({
                    'status': 'success',
                    'response': {
                        'type': 'recommendations',
                        'message': message,
                        'devices': recommendations
                    }
                })
            else:
                print("No recommendations found, using fallback")
                return jsonify({
                    'status': 'success',
                    'response': {
                        'type': 'text',
                        'content': FALLBACK_RESPONSES['no_recommendations']
                    }
                })
        
        # Handle all other query types (conversation, troubleshooting, usage patterns, etc.)
        print(f"Handling general conversation with intent: {primary_intent}")
        conversation_response = ai_assistant.handle_conversation(query)
        
        # Check if the response is a structured object or plain text
        if isinstance(conversation_response, dict) and 'type' in conversation_response:
            response_type = conversation_response['type']
            
            if response_type == 'recommendations':
                print(f"Returning recommendations from conversation handler")
                return jsonify({
                    'status': 'success',
                    'response': {
                        'type': 'recommendations',
                        'message': conversation_response.get('message', DEVICE_TEMPLATES['recommendation_intro']),
                        'devices': conversation_response.get('devices', [])
                    }
                })
        
        # For general text responses
        print("Returning text response from conversation handler")
        return jsonify({
            'status': 'success',
            'response': {
                'type': 'text',
                'content': conversation_response
            }
        })
            
    except Exception as e:
        error_msg = f"Error in AI assistant API: {str(e)}"
        print(f"EXCEPTION: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        logger.error(error_msg)
        return jsonify({'status': 'error', 'message': 'An error occurred processing your request. Please try again.'})

async def scrape_worker_impl(brands_to_scrape: List[Dict], delete_existing: List[str] = None):
    """Async implementation of scrape worker with option to delete existing data for specific brands."""
    try:
        # Start scraping
        update_status(
            message="Starting data extraction...",
            progress=0,
            brands_processed=0,
            devices_processed=0
        )
        logger.info("Starting data extraction...")
        
        # Initialize delete_existing if None
        if delete_existing is None:
            delete_existing = []
            
        # Create files with headers if they don't exist
        if not os.path.exists(scraper.brands_file):
            with open(scraper.brands_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['brand_name', 'device_name', 'device_url', 'device_image'])
            logger.info(f"Created brands file: {scraper.brands_file}")
        
        if not os.path.exists(scraper.specs_file):
            with open(scraper.specs_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['device_url', 'name', 'pictures', 'specifications'])
            logger.info(f"Created specs file: {scraper.specs_file}")
        
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
                        rows_to_keep = []
                        
                        for row in reader:
                            if row and row[0] in brand_names_to_delete:
                                device_urls_to_delete.add(row[2])  # URL is in the third column
                            else:
                                rows_to_keep.append(row)
                        
                        # Write rows that should be kept
                        for row in rows_to_keep:
                            writer.writerow(row)
                    
                    # Replace original file with temp file
                    os.replace(temp_brands_file, scraper.brands_file)
                
                # Process device_specifications.csv - remove entries for selected brands
                if os.path.exists(scraper.specs_file) and device_urls_to_delete:
                    temp_specs_file = scraper.specs_file + '.temp'
                    with open(scraper.specs_file, 'r', encoding='utf-8') as input_file, \
                         open(temp_specs_file, 'w', newline='', encoding='utf-8') as output_file:
                        reader = csv.reader(input_file)
                        writer = csv.writer(output_file)
                        
                        # Write header
                        header = next(reader)
                        writer.writerow(header)
                        
                        # Write rows, updating the one we need
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
        
        # Create a shared session for all requests
        async with aiohttp.ClientSession() as session:
            for brand_idx, brand in enumerate(brands_to_scrape, 1):
                # Check if paused
                while scraping_paused:
                    await asyncio.sleep(1)
                    continue
                    
                brand_name = brand['name']
                brand_devices = brand['device_count']
                
                update_status(
                    message=f"Processing brand {brand_idx}/{len(brands_to_scrape)}: {brand_name}",
                    current_brand=brand_name,
                    current_brand_devices=brand_devices,
                    current_brand_progress=0,
                    brands_processed=brand_idx
                )
                logger.info(f"Processing brand {brand_idx}/{len(brands_to_scrape)}: {brand_name}")
                
                # Get devices for this brand
                devices = await scraper.get_devices_from_brand_impl(brand['url'], session)
                
                # Save devices to brands file
                with open(scraper.brands_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for device in devices:
                        writer.writerow([
                            brand_name,
                            device['name'],
                            device['url'],
                            device['image_url']
                        ])
                
                # Process each device
                for device_idx, device in enumerate(devices, 1):
                    # Check if paused
                    while scraping_paused:
                        await asyncio.sleep(1)
                        continue
                        
                    device_progress = (device_idx / len(devices)) * 100 if len(devices) > 0 else 100
                    devices_processed += 1
                    overall_progress = (devices_processed / total_devices) * 100 if total_devices > 0 else 100
                    
                    update_status(
                        message=f"Processing device {device_idx}/{len(devices)}: {device['name']}",
                        current_brand_progress=device_progress,
                        devices_processed=devices_processed,
                        progress=overall_progress
                    )
                    logger.info(f"Processing device {device_idx}/{len(devices)}: {device['name']}")
                    
                    # Get specs for this device
                    specs = await scraper.get_device_specs_impl(device['url'], session)
                    if specs:
                        with open(scraper.specs_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                device['url'],
                                specs.get('name', ''),
                                specs.get('pictures', '[]'),
                                json.dumps(specs)
                            ])
                    
                    # Add a small delay to respect the website
                    await asyncio.sleep(1)
                
                # Add this brand to completed brands
                completed_brand = {
                    'name': brand_name,
                    'devices': len(devices),
                    'expected': brand_devices
                }
                current_status['completed_brands'].append(completed_brand)
                
                # Update progress after each brand
                update_status(
                    current_brand_progress=100,  # Brand is complete
                    message=f"Completed brand: {brand_name}"
                )
                logger.info(f"Completed brand: {brand_name} with {len(devices)} devices")
                
                # Respect the website by adding a delay
                await asyncio.sleep(1)
        
        # Final status update
        update_status(
            message="Data extraction completed!",
            progress=100
        )
        logger.info("Data extraction completed!")
    except Exception as e:
        error_msg = f"Error in scraper: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        update_status(message=f"Error: {str(e)}")

async def incremental_update_worker_impl(brands_to_update: List[Dict]):
    """Async implementation of worker function to perform incremental updates."""
    try:
        # Reset status for new update session
        update_status(
            message="Starting incremental update...",
            progress=0,
            current_brand="",
            current_brand_devices=0,
            current_brand_progress=0,
            brands_processed=0,
            devices_processed=0,
            total_brands=0,
            total_devices=0,
            completed_brands=[],
            is_incremental=True
        )
        logger.info("Starting incremental update...")
        
        # Calculate total devices for progress tracking
        total_devices = sum(brand['device_count'] for brand in brands_to_update)
        update_status(
            total_devices=total_devices,
            total_brands=len(brands_to_update)
        )
        logger.info(f"Total brands to update: {len(brands_to_update)}, Total devices: {total_devices}")
        
        # Process each brand incrementally
        results = {
            'new_devices': 0,
            'updated_devices': 0,
            'brands_processed': 0
        }
        
        # Create a shared session for all requests
        async with aiohttp.ClientSession() as session:
            for brand_idx, brand in enumerate(brands_to_update, 1):
                # Check if paused
                while scraping_paused:
                    await asyncio.sleep(1)
                    continue
                    
                # Update status for current brand
                brand_name = brand['name']
                brand_devices = brand['device_count']
                
                update_status(
                    message=f"Processing brand for incremental update: {brand_name}",
                    current_brand=brand_name,
                    current_brand_devices=brand_devices,
                    current_brand_progress=0,
                    brands_processed=brand_idx
                )
                logger.info(f"Processing brand for incremental update: {brand_name} ({brand_idx}/{len(brands_to_update)})")
                
                # Get devices needing update
                new_devices, updated_devices = await incremental_scraper.get_devices_needing_update_impl(brand, session)
                total_devices_to_process = len(new_devices) + len(updated_devices)
                
                # Update console with what we found
                addConsoleMessage = f"Found {len(new_devices)} new devices and {len(updated_devices)} devices needing updates for {brand_name}"
                update_status(message=addConsoleMessage)
                logger.info(addConsoleMessage)
                
                # Process new devices
                devices_processed = 0
                
                # Process new devices
                for device_idx, device in enumerate(new_devices, 1):
                    # Check if paused
                    while scraping_paused:
                        await asyncio.sleep(1)
                        continue
                        
                    device_progress = (device_idx / len(new_devices)) * 100 if len(new_devices) > 0 else 100
                    update_status(
                        message=f"Processing new device: {device['name']} ({device_idx}/{len(new_devices)})",
                        current_brand_progress=device_progress,
                        devices_processed=results['new_devices'] + results['updated_devices'] + device_idx
                    )
                    logger.info(f"Processing new device: {device['name']} ({device_idx}/{len(new_devices)})")
                    
                    # Process device specs
                    specs = await incremental_scraper.get_device_specs_impl(device['url'], session)
                    if specs:
                        with open(scraper.brands_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([brand_name, device['name'], device['url'], device['image_url']])
                        
                        with open(scraper.specs_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([device['url'], specs.get('name', ''), specs.get('pictures', '[]'), json.dumps(specs)])
                        
                        results['new_devices'] += 1
                    
                    await asyncio.sleep(1)  # Respect the website
                
                # Process updated devices
                for device_idx, device in enumerate(updated_devices, 1):
                    # Check if paused
                    while scraping_paused:
                        await asyncio.sleep(1)
                        continue
                        
                    device_progress = (device_idx / len(updated_devices)) * 100 if len(updated_devices) > 0 else 100
                    update_status(
                        message=f"Processing updated device: {device['name']} ({device_idx}/{len(updated_devices)})",
                        current_brand_progress=device_progress,
                        devices_processed=results['new_devices'] + results['updated_devices'] + device_idx
                    )
                    logger.info(f"Processing updated device: {device['name']} ({device_idx}/{len(updated_devices)})")
                    
                    # Process device specs
                    specs = await incremental_scraper.get_device_specs_impl(device['url'], session)
                    if specs:
                        # Update the specs file
                        updated = False
                        if os.path.exists(scraper.specs_file):
                            temp_specs_file = scraper.specs_file + '.temp'
                            with open(scraper.specs_file, 'r', encoding='utf-8') as input_file, \
                                 open(temp_specs_file, 'w', newline='', encoding='utf-8') as output_file:
                                reader = csv.reader(input_file)
                                writer = csv.writer(output_file)
                                
                                # Write header
                                header = next(reader)
                                writer.writerow(header)
                                
                                # Write rows, updating the one we need
                                for row in reader:
                                    if row and row[0] == device['url']:
                                        # This is the row to update
                                        writer.writerow([
                                            device['url'],
                                            specs.get('name', ''),
                                            specs.get('pictures', '[]'),
                                            json.dumps(specs)
                                        ])
                                        updated = True
                                    else:
                                        writer.writerow(row)
                                
                                # If we didn't find the row to update, append it
                                if not updated:
                                    writer.writerow([
                                        device['url'],
                                        specs.get('name', ''),
                                        specs.get('pictures', '[]'),
                                        json.dumps(specs)
                                    ])
                        
                        # Replace original file with temp file
                        os.replace(temp_specs_file, scraper.specs_file)
                        
                        # Update the device updates database
                        incremental_scraper.device_updates['devices'][device['url']] = {
                            'last_updated': datetime.now().isoformat(),
                            'brand': brand['name']
                        }
                        results['updated_devices'] += 1
                    
                    await asyncio.sleep(1)  # Respect the website
                
                # Update completed brands
                completed_brand = {
                    'name': brand_name,
                    'devices': len(new_devices) + len(updated_devices),
                    'expected': brand_devices
                }
                current_status['completed_brands'].append(completed_brand)
                
                # Calculate overall progress
                results['brands_processed'] += 1
                overall_progress = (results['brands_processed'] / len(brands_to_update)) * 100
                update_status(progress=overall_progress)
        
        # Update the device updates database
        incremental_scraper._save_device_updates()
        
        # Final status update
        update_status(
            message=f"Incremental update completed! Added {results['new_devices']} new devices and updated {results['updated_devices']} devices.",
            progress=100
        )
        logger.info(f"Incremental update completed! Added {results['new_devices']} new devices and updated {results['updated_devices']} devices.")
    except Exception as e:
        logger.error(f"Error in incremental update: {str(e)}")
        update_status(message=f"Error: {str(e)}")

def scrape_worker(brands_to_scrape: List[Dict], delete_existing: List[str] = None):
    """Synchronous wrapper for the async scrape_worker_impl function"""
    try:
        asyncio.run(scrape_worker_impl(brands_to_scrape, delete_existing))
    except Exception as e:
        logger.error(f"Error in scrape_worker: {str(e)}\n{traceback.format_exc()}")
        update_status(message=f"Error: {str(e)}")

def incremental_update_worker(brands_to_update: List[Dict]):
    """Synchronous wrapper for the async incremental_update_worker_impl function"""
    try:
        asyncio.run(incremental_update_worker_impl(brands_to_update))
    except Exception as e:
        logger.error(f"Error in incremental update worker: {str(e)}\n{traceback.format_exc()}")
        update_status(message=f"Error: {str(e)}")

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

@app.route('/events')
def events():
    def event_stream():
        while True:
            # Get the latest status from the queue without blocking
            latest_status = None
            latest_timestamp = 0
            
            # Process all available items in the queue
            items_to_process = min(progress_queue.qsize(), 50)  # Limit to 50 items at a time
            
            for _ in range(items_to_process):
                try:
                    queue_status = progress_queue.get_nowait()
                    # Keep the status with the most recent timestamp
                    if 'timestamp' in queue_status and queue_status['timestamp'] > latest_timestamp:
                        latest_status = queue_status
                        latest_timestamp = queue_status['timestamp']
                except queue.Empty:
                    break
            
            # If we found a newer status in the queue, use it
            if latest_status:
                # Remove the timestamp before sending to frontend
                if 'timestamp' in latest_status:
                    del latest_status['timestamp']
                yield 'data: {}\n\n'.format(json.dumps(latest_status))
            else:
                yield 'data: {}\n\n'.format(json.dumps(current_status))
            
            # Wait a bit before checking again
            time.sleep(1)
    
    return Response(event_stream(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
