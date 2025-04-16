import json
import os
import time
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional

from scraper import GSMArenaScraper
from loguru import logger

class IncrementalScraper(GSMArenaScraper):
    """
    Enhanced scraper that supports incremental updates.
    Only scrapes new devices or devices that have been updated since the last scrape.
    """
    
    def __init__(self):
        super().__init__()
        self.updates_file = 'device_updates.json'
        self.device_updates = self._load_device_updates()
    
    def _load_device_updates(self) -> Dict:
        """Load the device updates database."""
        if os.path.exists(self.updates_file):
            try:
                with open(self.updates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading device updates: {str(e)}")
        
        # Return default structure if file doesn't exist or has errors
        return {
            "last_full_update": None,
            "devices": {}
        }
    
    def _save_device_updates(self):
        """Save the device updates database."""
        try:
            with open(self.updates_file, 'w', encoding='utf-8') as f:
                json.dump(self.device_updates, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving device updates: {str(e)}")
    
    def get_existing_devices(self) -> Dict[str, Dict]:
        """
        Get all existing devices from the CSV files.
        Returns a dictionary with device URLs as keys and device info as values.
        """
        existing_devices = {}
        
        # Read from brands_devices.csv
        if os.path.exists(self.brands_file):
            try:
                with open(self.brands_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    for row in reader:
                        if len(row) >= 4:  # brand_name, device_name, device_url, device_image
                            device_url = row[2]
                            existing_devices[device_url] = {
                                'brand_name': row[0],
                                'device_name': row[1],
                                'device_url': device_url,
                                'device_image': row[3]
                            }
            except Exception as e:
                logger.error(f"Error reading brands file: {str(e)}")
        
        return existing_devices
    
    def get_devices_needing_update(self, brand: Dict) -> Tuple[List[Dict], List[Dict]]:
        """
        Compare current devices with existing devices to find which ones need to be scraped.
        Returns a tuple of (new_devices, updated_devices).
        """
        # Get current devices from website
        current_devices = self.get_devices_from_brand(brand['url'])
        
        # Get existing devices from database
        existing_devices = self.get_existing_devices()
        
        # Find new devices (not in our database)
        new_devices = []
        updated_devices = []
        
        for device in current_devices:
            device_url = device['url']
            
            if device_url not in existing_devices:
                # This is a new device
                new_devices.append(device)
            elif device_url not in self.device_updates['devices']:
                # Device exists in CSV but not in our updates tracking
                # Consider it as needing an update
                updated_devices.append(device)
        
        return new_devices, updated_devices
    
    def incremental_update(self, brands_to_update: List[Dict]) -> Dict:
        """
        Perform an incremental update for the specified brands.
        Only scrapes new devices or devices that have been updated.
        """
        results = {
            'new_devices': 0,
            'updated_devices': 0,
            'brands_processed': 0,
            'total_brands': len(brands_to_update)
        }
        
        current_time = datetime.now().isoformat()
        
        for brand_idx, brand in enumerate(brands_to_update, 1):
            logger.info(f"Processing brand {brand_idx}/{len(brands_to_update)}: {brand['name']}")
            results['brands_processed'] = brand_idx
            
            # Get devices needing update
            new_devices, updated_devices = self.get_devices_needing_update(brand)
            
            # Log what we found
            logger.info(f"Found {len(new_devices)} new devices and {len(updated_devices)} devices needing updates for {brand['name']}")
            
            # Process new devices
            for device in new_devices:
                logger.info(f"Processing new device: {device['name']}")
                specs = self.get_device_specs(device['url'])
                if specs:
                    # Save to brands file
                    with open(self.brands_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            brand['name'],
                            device['name'],
                            device['url'],
                            device['image_url']
                        ])
                    
                    # Save to specs file
                    with open(self.specs_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            device['url'],
                            specs.get('name', ''),
                            specs.get('pictures', '[]'),
                            json.dumps(specs)
                        ])
                    
                    # Update the device updates database
                    self.device_updates['devices'][device['url']] = {
                        'last_updated': current_time,
                        'brand': brand['name']
                    }
                    results['new_devices'] += 1
                
                time.sleep(1)  # Respect the website
            
            # Process updated devices
            for device in updated_devices:
                logger.info(f"Processing updated device: {device['name']}")
                specs = self.get_device_specs(device['url'])
                if specs:
                    # For updated devices, we need to update the specs file
                    # First, read the existing specs file to find the line to update
                    updated = False
                    if os.path.exists(self.specs_file):
                        temp_specs_file = self.specs_file + '.temp'
                        with open(self.specs_file, 'r', encoding='utf-8') as input_file, \
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
                        os.replace(temp_specs_file, self.specs_file)
                    
                    # Update the device updates database
                    self.device_updates['devices'][device['url']] = {
                        'last_updated': current_time,
                        'brand': brand['name']
                    }
                    results['updated_devices'] += 1
                
                time.sleep(1)  # Respect the website
        
        # Update the last full update time if we processed all brands
        if results['brands_processed'] == results['total_brands']:
            self.device_updates['last_full_update'] = current_time
        
        # Save the device updates database
        self._save_device_updates()
        
        return results

# Fix missing import
import csv
