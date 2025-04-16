import asyncio
import aiohttp
from bs4 import BeautifulSoup
import csv
from loguru import logger
import time
import json
import random
import os
from typing import Dict, List, Optional, Tuple
from aiohttp import ClientTimeout

class AsyncGSMArenaScraper:
    """
    Asynchronous implementation of GSMArena scraper using async/await pattern
    for significantly improved performance over thread-based concurrency.
    """
    def __init__(self):
        self.base_url = "https://www.gsmarena.com/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.setup_logger()
        self.brands_file = 'brands_devices.csv'
        self.specs_file = 'device_specifications.csv'
        
        # Rate limiting settings
        self.min_request_interval = 2.0  # Base seconds between requests
        self.interval_variation = 0.5  # Variation in seconds (±) for randomization
        self.max_retries = 5  # Retries for failed requests
        
        # Concurrency settings
        self.max_concurrent_requests = 100  # Much higher than thread-based version
        self.semaphore = None  # Will be initialized in run() method
        
        # Request tracking
        self.last_request_time = 0
        self.request_times = {}  # Track request times per URL domain

    def setup_logger(self):
        logger.add("debug.log", rotation="500 MB", level="DEBUG")

    async def _sleep_for_rate_limit(self, url):
        """Implement rate limiting with randomization"""
        domain = url.split('/')[2]  # Extract domain from URL
        
        current_time = time.time()
        last_time = self.request_times.get(domain, 0)
        time_since_last = current_time - last_time
        
        # Calculate random interval within the specified range
        random_interval = self.min_request_interval + random.uniform(-self.interval_variation, self.interval_variation)
        random_interval = max(random_interval, 1.5)  # Ensure minimum delay
        
        if time_since_last < random_interval:
            sleep_time = random_interval - time_since_last
            logger.info(f"Rate limiting for {domain}: waiting {sleep_time:.1f} seconds...")
            await asyncio.sleep(sleep_time)
        
        # Update last request time for this domain
        self.request_times[domain] = time.time()

    async def _make_request(self, url, session):
        """Make an async rate-limited request with retries"""
        retries = 0
        
        while retries < self.max_retries:
            try:
                # Apply rate limiting
                await self._sleep_for_rate_limit(url)
                
                # Make the request with timeout
                timeout = ClientTimeout(total=10)
                async with session.get(url, headers=self.headers, timeout=timeout) as response:
                    if response.status == 429:  # Too Many Requests
                        retry_after = int(response.headers.get('Retry-After', self.min_request_interval * (retries + 2)))
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds before retry {retries + 1}/{self.max_retries}")
                        await asyncio.sleep(retry_after)
                        retries += 1
                        continue
                    
                    response.raise_for_status()
                    return await response.text()
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if retries == self.max_retries - 1:
                    logger.error(f"Failed after {self.max_retries} retries for URL {url}: {str(e)}")
                    raise
                
                retries += 1
                wait_time = self.min_request_interval * (retries + 1)
                logger.warning(f"Request failed: {str(e)}. Retrying in {wait_time} seconds... ({retries}/{self.max_retries})")
                await asyncio.sleep(wait_time)
        
        raise Exception(f"Failed after {self.max_retries} retries")

    async def get_brands(self, session) -> List[Dict]:
        """Fetch all brands from GSMArena"""
        try:
            logger.info("Fetching brands list")
            html = await self._make_request(f"{self.base_url}makers.php3", session)
            soup = BeautifulSoup(html, 'html.parser')
            brands = []
            
            for brand in soup.select('div.brandmenu-v2 ul li a'):
                brand_name = brand.text.strip()
                brand_url = self.base_url + brand['href']
                device_count = brand.select_one('span')
                if device_count:
                    device_count = int(''.join(filter(str.isdigit, device_count.text)))
                else:
                    device_count = 0
                
                brands.append({
                    'name': brand_name,
                    'url': brand_url,
                    'device_count': device_count
                })
                logger.debug(f"Found brand: {brand_name} with {device_count} devices")
            
            return brands
        except Exception as e:
            logger.error(f"Error fetching brands: {str(e)}")
            return []

    async def get_device_pictures(self, url: str, session) -> List[str]:
        """Fetch device pictures asynchronously"""
        try:
            logger.info(f"Fetching pictures for device: {url}")
            html = await self._make_request(url, session)
            soup = BeautifulSoup(html, 'html.parser')
            
            pictures = []
            # Find the pictures section
            pictures_section = soup.select_one('div.specs-photo-main')
            if pictures_section:
                main_pic = pictures_section.select_one('img')
                if main_pic and 'src' in main_pic.attrs:
                    pictures.append(main_pic['src'])
            
            # Look for additional pictures
            thumbs = soup.select('div.specs-photo-sub img')
            for thumb in thumbs:
                if 'src' in thumb.attrs:
                    # Convert thumbnail URL to full-size image URL
                    pic_url = thumb['src'].replace('t_thumb', 'full')
                    if pic_url not in pictures:
                        pictures.append(pic_url)
            
            return pictures
        except Exception as e:
            logger.error(f"Error fetching pictures for {url}: {str(e)}")
            return []

    async def get_device_specs(self, url: str, session) -> Optional[Dict]:
        """Fetch and parse device specifications asynchronously"""
        try:
            logger.info(f"Fetching specs for device: {url}")
            html = await self._make_request(url, session)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract device name
            title = soup.select_one('h1.specs-phone-name-title')
            device_name = title.text.strip() if title else ""
            
            # Get pictures
            pictures = await self.get_device_pictures(url, session)
            
            # Extract specifications
            specs = {}
            spec_tables = soup.select('table.specs-table')
            
            for table in spec_tables:
                category = table.select_one('th.ttl').text.strip() if table.select_one('th.ttl') else "Unknown"
                specs[category] = {}
                
                rows = table.select('tr')
                for row in rows:
                    name_cell = row.select_one('td.ttl')
                    value_cell = row.select_one('td.nfo')
                    
                    if name_cell and value_cell:
                        spec_name = name_cell.text.strip()
                        spec_value = value_cell.text.strip()
                        specs[category][spec_name] = spec_value
            
            result = {
                'name': device_name,
                'url': url,
                'pictures': json.dumps(pictures),
                'specifications': specs
            }
            
            logger.debug(f"Successfully extracted specs for {device_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching specs for {url}: {str(e)}")
            return None

    async def get_devices_from_brand(self, brand_url: str, session) -> List[Dict]:
        """Get all devices from a brand, handling pagination asynchronously"""
        try:
            logger.info(f"Fetching devices for brand: {brand_url}")
            all_devices = []
            current_url = brand_url
            page = 1
            
            while True:
                logger.info(f"Processing page {page} for {brand_url}")
                html = await self._make_request(current_url, session)
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all device entries
                device_list = soup.select('div.makers ul li')
                for device in device_list:
                    link = device.select_one('a')
                    img = device.select_one('img')
                    
                    if not link:
                        continue
                        
                    device_data = {
                        'name': link.text.strip(),
                        'url': self.base_url + link['href'],
                        'image_url': img['src'] if img and 'src' in img.attrs else ''
                    }
                    all_devices.append(device_data)
                
                # Look for next page
                next_page = None
                nav_section = soup.select_one('div.nav-pages')
                if nav_section:
                    # Find the current page marker (strong tag)
                    current_page = nav_section.select_one('strong')
                    if current_page:
                        # Look for the next page link after the current page
                        next_sibling = current_page.find_next_sibling('a')
                        if next_sibling and 'href' in next_sibling.attrs and next_sibling['href'] != '#':
                            next_page = next_sibling['href']
                
                if next_page:
                    current_url = self.base_url + next_page
                    page += 1
                    # No need for explicit sleep here as _make_request handles rate limiting
                else:
                    break
                
            logger.info(f"Found total {len(all_devices)} devices across {page} pages")
            return all_devices
            
        except Exception as e:
            logger.error(f"Error fetching devices for brand: {str(e)}")
            return []

    async def _process_device_specs(self, device, brand_name, session):
        """Process a single device's specifications asynchronously"""
        try:
            logger.info(f"Processing device: {device['name']}")
            specs = await self.get_device_specs(device['url'], session)
            if not specs:
                return None
                
            return {
                'brand_name': brand_name,
                'device': device,
                'specs': specs
            }
        except Exception as e:
            logger.error(f"Error processing device {device['name']}: {str(e)}")
            return None

    async def _process_brand_devices(self, brand, session):
        """Process all devices for a brand asynchronously"""
        try:
            logger.info(f"Processing brand: {brand['name']}")
            devices = await self.get_devices_from_brand(brand['url'], session)
            
            # Process all devices concurrently with semaphore to limit concurrency
            tasks = []
            for device in devices:
                task = asyncio.create_task(self._process_device_specs(device, brand['name'], session))
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = []
            for task in asyncio.as_completed(tasks):
                result = await task
                if result:
                    results.append(result)
            
            return {
                'brand': brand,
                'devices': devices,
                'results': results
            }
        except Exception as e:
            logger.error(f"Error processing brand {brand['name']}: {str(e)}")
            return None

    async def _save_to_csv_async(self, brands_results):
        """Save all scraped data to CSV files asynchronously"""
        try:
            # Create/clear the CSV files
            with open(self.brands_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['brand_name', 'device_name', 'device_url', 'device_image'])
            
            with open(self.specs_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['device_url', 'name', 'pictures', 'specifications'])
            
            # Process each brand's results
            for brand_result in brands_results:
                if not brand_result:
                    continue
                    
                brand = brand_result['brand']
                devices = brand_result['devices']
                
                # Save devices to brands file
                with open(self.brands_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for device in devices:
                        writer.writerow([
                            brand['name'],
                            device['name'],
                            device['url'],
                            device['image_url']
                        ])
                
                # Save specifications to specs file
                with open(self.specs_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for result in brand_result['results']:
                        specs = result['specs']
                        device = result['device']
                        writer.writerow([
                            device['url'],
                            specs.get('name', ''),
                            specs.get('pictures', '[]'),
                            json.dumps(specs)
                        ])
            
            logger.success("Data extraction completed successfully!")
            return True
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            return False

    async def save_to_csv_async(self):
        """Main method to scrape and save all data asynchronously"""
        try:
            # Create client session
            async with aiohttp.ClientSession() as session:
                # Get all brands
                brands = await self.get_brands(session)
                total_brands = len(brands)
                logger.info(f"Found {total_brands} brands to process")
                
                # Process each brand sequentially, but devices concurrently
                brands_results = []
                for brand_idx, brand in enumerate(brands, 1):
                    logger.info(f"Processing brand {brand_idx}/{total_brands}: {brand['name']}")
                    brand_result = await self._process_brand_devices(brand, session)
                    if brand_result:
                        brands_results.append(brand_result)
                
                # Save all results to CSV
                await self._save_to_csv_async(brands_results)
                
            return True
        except Exception as e:
            logger.error(f"Error in save_to_csv_async: {str(e)}")
            return False

    def save_to_csv(self):
        """Synchronous wrapper for the async method"""
        return asyncio.run(self.save_to_csv_async())

# Example usage
if __name__ == "__main__":
    scraper = AsyncGSMArenaScraper()
    scraper.save_to_csv()
