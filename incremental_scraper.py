import json
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional

from scraper import GSMArenaScraper
from loguru import logger
import aiohttp

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
    
    async def get_existing_devices_impl(self) -> Dict[str, Dict]:
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
        
    def get_existing_devices(self) -> Dict[str, Dict]:
        """Synchronous wrapper for the async get_existing_devices_impl method"""
        return asyncio.run(self.get_existing_devices_impl())
    
    async def get_devices_needing_update_impl(self, brand: Dict, session) -> Tuple[List[Dict], List[Dict]]:
        """
        Compare current devices with existing devices to find which ones need to be scraped.
        Returns a tuple of (new_devices, updated_devices).
        """
        # Get current devices from website
        current_devices = await self.get_devices_from_brand_impl(brand['url'], session)
        
        # Get existing devices from database
        existing_devices = await self.get_existing_devices_impl()
        
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
        
    def get_devices_needing_update(self, brand: Dict) -> Tuple[List[Dict], List[Dict]]:
        """Synchronous wrapper for the async get_devices_needing_update_impl method"""
        return asyncio.run(self._get_devices_needing_update_with_session(brand))
    
    async def _get_devices_needing_update_with_session(self, brand: Dict) -> Tuple[List[Dict], List[Dict]]:
        """Helper method to create a session and call get_devices_needing_update_impl"""
        async with aiohttp.ClientSession() as session:
            return await self.get_devices_needing_update_impl(brand, session)
    
    async def incremental_update_impl(self, brands_to_update: List[Dict]) -> Dict:
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
        
        async with aiohttp.ClientSession() as session:
            for brand_idx, brand in enumerate(brands_to_update, 1):
                brand_name = brand['name']
                logger.info(f"Processing brand {brand_idx}/{len(brands_to_update)}: {brand_name}")
                
                # Get devices needing update
                new_devices, updated_devices = await self.get_devices_needing_update_impl(brand, session)
                
                logger.info(f"Found {len(new_devices)} new devices and {len(updated_devices)} devices needing updates")
                
                # Process new devices
                for device in new_devices:
                    logger.info(f"Processing new device: {device['name']}")
                    specs = await self.get_device_specs_impl(device['url'], session)
                    if specs:
                        # Add to brands file
                        with open(self.brands_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                brand_name,
                                device['name'],
                                device['url'],
                                device['image_url']
                            ])
                        
                        # Add to specs file
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
                    
                    await asyncio.sleep(1)  # Respect the website
                
                # Process updated devices
                for device in updated_devices:
                    logger.info(f"Processing updated device: {device['name']}")
                    specs = await self.get_device_specs_impl(device['url'], session)
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
                    
                    await asyncio.sleep(1)  # Respect the website
                
                # Update the brands processed count
                results['brands_processed'] += 1
        
        # Update the last full update time if we processed all brands
        if results['brands_processed'] == results['total_brands']:
            self.device_updates['last_full_update'] = current_time
        
        # Save the device updates database
        self._save_device_updates()
        
        return results
        
    def incremental_update(self, brands_to_update: List[Dict]) -> Dict:
        """Synchronous wrapper for the async incremental_update_impl method"""
        return asyncio.run(self.incremental_update_impl(brands_to_update))

# Fix missing import
import csv
