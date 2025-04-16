import json
import os
import time
import random
import asyncio
import aiohttp
import csv
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from loguru import logger
from scraper import AsyncGSMArenaScraper
from aiohttp import ClientTimeout

class AsyncIncrementalScraper(AsyncGSMArenaScraper):
    """
    Asynchronous implementation of incremental scraper using async/await pattern.
    Only scrapes new devices or devices that have been updated since the last scrape.
    """
    
    def __init__(self):
        super().__init__()
        self.updates_file = 'device_updates.json'
        self.device_updates = self._load_device_updates()
        # Incremental scraper can use even more concurrent requests
        self.max_concurrent_requests = 150  # Even higher for incremental updates

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
    
    async def get_existing_devices(self) -> Dict[str, Dict]:
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
    
    async def get_devices_needing_update(self, brand: Dict, session) -> Tuple[List[Dict], List[Dict]]:
        """
        Compare current devices with existing devices to find which ones need to be scraped.
        Returns a tuple of (new_devices, updated_devices).
        """
        # Get current devices from website
        current_devices = await self.get_devices_from_brand(brand['url'], session)
        
        # Get existing devices from database
        existing_devices = await self.get_existing_devices()
        
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
    
    async def _process_device_update(self, device, brand, current_time, is_new, session) -> Dict:
        """
        Process a single device update (new or existing) asynchronously
        Returns a dictionary with the results
        """
        try:
            logger.info(f"Processing {'new' if is_new else 'updated'} device: {device['name']}")
            specs = await self.get_device_specs(device['url'], session)
            if not specs:
                return {'success': False, 'device_url': device['url']}
            
            result = {
                'success': True,
                'device': device,
                'specs': specs,
                'brand': brand,
                'is_new': is_new,
                'current_time': current_time
            }
            
            return result
        except Exception as e:
            logger.error(f"Error processing device {device['name']}: {str(e)}")
            return {'success': False, 'device_url': device['url'], 'error': str(e)}
    
    async def _process_brand_updates(self, brand, brand_idx, total_brands, current_time, session) -> Dict:
        """
        Process all updates for a single brand using concurrent async requests
        """
        try:
            logger.info(f"Processing brand {brand_idx}/{total_brands}: {brand['name']}")
            
            # Find devices that need to be updated
            new_devices, updated_devices = await self.get_devices_needing_update(brand, session)
            
            logger.info(f"Found {len(new_devices)} new devices and {len(updated_devices)} devices to update for {brand['name']}")
            
            # Process all devices concurrently
            all_tasks = []
            
            # Create tasks for new devices
            for device in new_devices:
                task = asyncio.create_task(
                    self._process_device_update(device, brand, current_time, True, session)
                )
                all_tasks.append(task)
                
            # Create tasks for updated devices
            for device in updated_devices:
                task = asyncio.create_task(
                    self._process_device_update(device, brand, current_time, False, session)
                )
                all_tasks.append(task)
            
            # Wait for all tasks to complete
            results = []
            for task in asyncio.as_completed(all_tasks):
                result = await task
                if result['success']:
                    results.append(result)
            
            return {
                'brand': brand,
                'results': results,
                'new_count': len(new_devices),
                'updated_count': len(updated_devices),
                'processed_count': len(results)
            }
        except Exception as e:
            logger.error(f"Error processing brand {brand['name']}: {str(e)}")
            return {
                'brand': brand,
                'results': [],
                'new_count': 0,
                'updated_count': 0,
                'processed_count': 0,
                'error': str(e)
            }

    async def incremental_update_async(self, brands_to_update: List[Dict]) -> Dict:
        """
        Perform an incremental update for the specified brands asynchronously.
        Only scrapes new devices or devices that have been updated.
        """
        results = {
            "brands_processed": 0,
            "total_brands": len(brands_to_update),
            "new_devices": 0,
            "updated_devices": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        
        current_time = datetime.now().isoformat()
        
        async with aiohttp.ClientSession() as session:
            for brand_idx, brand in enumerate(brands_to_update, 1):
                # Process this brand's updates concurrently
                brand_result = await self._process_brand_updates(
                    brand, brand_idx, results['total_brands'], current_time, session
                )
                
                # Process the results
                for result in brand_result['results']:
                    device = result['device']
                    specs = result['specs']
                    is_new = result['is_new']
                    
                    if is_new:
                        # Add to brands_devices.csv
                        with open(self.brands_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                brand['name'],
                                device['name'],
                                device['url'],
                                device['image_url']
                            ])
                        
                        # Add to device_specifications.csv
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
                    else:
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
                
                results['brands_processed'] += 1
        
        # Update the last full update time if we processed all brands
        if results['brands_processed'] == results['total_brands']:
            self.device_updates['last_full_update'] = current_time
        
        # Save the device updates database
        self._save_device_updates()
        
        results['end_time'] = datetime.now().isoformat()
        
        return results

    def incremental_update(self, brands_to_update: List[Dict]) -> Dict:
        """Synchronous wrapper for the async method"""
        return asyncio.run(self.incremental_update_async(brands_to_update))

# Example usage
if __name__ == "__main__":
    scraper = AsyncIncrementalScraper()
    # Get all brands
    brands = asyncio.run(scraper.get_brands(aiohttp.ClientSession()))
    # Update all brands
    results = scraper.incremental_update(brands)
    print(f"Updated {results['new_devices']} new devices and {results['updated_devices']} existing devices")
