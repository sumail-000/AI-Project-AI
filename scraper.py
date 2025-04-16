import requests
from bs4 import BeautifulSoup
import csv
from loguru import logger
import time
import json
from typing import Dict, List, Optional, Tuple
import os

class GSMArenaScraper:
    def __init__(self):
        self.base_url = "https://www.gsmarena.com/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.setup_logger()
        self.brands_file = 'brands_devices.csv'
        self.specs_file = 'device_specifications.csv'
        self.last_request_time = 0
        self.min_request_interval = 3  # Minimum seconds between requests
        self.max_retries = 3

    def setup_logger(self):
        logger.add("debug.log", rotation="500 MB", level="DEBUG")

    def _make_request(self, url, headers=None):
        """Make a rate-limited request with retries"""
        headers = headers or self.headers
        retries = 0
        
        while retries < self.max_retries:
            # Ensure minimum time between requests
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                logger.info(f"Rate limiting: waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                self.last_request_time = time.time()
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', self.min_request_interval * (retries + 2)))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds before retry {retries + 1}/{self.max_retries}")
                    time.sleep(retry_after)
                    retries += 1
                    continue
                    
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                if retries == self.max_retries - 1:
                    raise
                retries += 1
                wait_time = self.min_request_interval * (retries + 1)
                logger.warning(f"Request failed: {str(e)}. Retrying in {wait_time} seconds... ({retries}/{self.max_retries})")
                time.sleep(wait_time)
        
        raise Exception(f"Failed after {self.max_retries} retries")

    def get_brands(self) -> List[Dict]:
        try:
            logger.info("Fetching brands list")
            response = self._make_request(f"{self.base_url}makers.php3")
            soup = BeautifulSoup(response.text, 'html.parser')
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

    def get_device_pictures(self, url: str) -> List[str]:
        try:
            logger.info(f"Fetching pictures for device: {url}")
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            pictures = []
            # Get main picture
            main_pic = soup.select_one('div.specs-photo-main img')
            if main_pic and 'src' in main_pic.attrs:
                pictures.append(main_pic['src'])
            
            # Get pictures from the Pictures section if available
            pictures_link = soup.select_one('a[href*="pictures"]')
            if pictures_link:
                pics_url = self.base_url + pictures_link['href']
                pics_response = self._make_request(pics_url)
                if pics_response.status_code == 200:
                    pics_soup = BeautifulSoup(pics_response.text, 'html.parser')
                    for pic in pics_soup.select('div.specs-photo-main img'):
                        if 'src' in pic.attrs and pic['src'] not in pictures:
                            pictures.append(pic['src'])
            
            return pictures
        except Exception as e:
            logger.error(f"Error fetching device pictures: {str(e)}")
            return []

    def get_device_specs(self, url: str) -> Optional[Dict]:
        try:
            logger.info(f"Fetching specs for device: {url}")
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            specs = {
                'url': url,
                'pictures': json.dumps(self.get_device_pictures(url))
            }
            
            # Get device name
            name_elem = soup.select_one('h1.specs-phone-name-title')
            if name_elem:
                specs['name'] = name_elem.text.strip()
            
            # Get all specification tables
            for spec_table in soup.select('table'):
                category = spec_table.select_one('th')
                if not category:
                    continue
                    
                category = category.text.strip()
                specs[category] = {}
                
                for row in spec_table.select('tr'):
                    label = row.select_one('td.ttl')
                    value = row.select_one('td.nfo')
                    if label and value:
                        label_text = label.text.strip()
                        value_text = value.text.strip()
                        specs[category][label_text] = value_text
            
            logger.debug(f"Successfully extracted specs for {specs.get('name', 'Unknown device')}")
            return specs
        except Exception as e:
            logger.error(f"Error fetching device specs: {str(e)}")
            return None

    def get_devices_from_brand(self, brand_url: str) -> List[Dict]:
        """Get all devices from a brand, handling pagination."""
        try:
            all_devices = []
            current_url = brand_url
            page = 1
            
            while current_url:
                logger.info(f"Fetching devices from page {page} at {current_url}")
                response = self._make_request(current_url)
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Get devices from current page
                devices_section = soup.select('div.makers li')
                if not devices_section:
                    break
                
                for device in devices_section:
                    link = device.select_one('a')
                    if not link:
                        continue
                        
                    img = device.select_one('img')
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
                    time.sleep(1)  # Respect rate limiting between pages
                else:
                    break
                
            logger.info(f"Found total {len(all_devices)} devices across {page} pages")
            return all_devices
            
        except Exception as e:
            logger.error(f"Error fetching devices for brand: {str(e)}")
            return []

    def save_to_csv(self):
        try:
            # Create/clear the CSV files
            with open(self.brands_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['brand_name', 'device_name', 'device_url', 'device_image'])
            
            with open(self.specs_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['device_url', 'name', 'pictures', 'specifications'])
            
            # Get all brands
            brands = self.get_brands()
            total_brands = len(brands)
            
            for brand_idx, brand in enumerate(brands, 1):
                logger.info(f"Processing brand {brand_idx}/{total_brands}: {brand['name']}")
                
                # Get all devices for the brand
                devices = self.get_devices_from_brand(brand['url'])
                
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
                
                # Get and save specifications for each device
                for device_idx, device in enumerate(devices, 1):
                    logger.info(f"Processing device {device_idx}/{len(devices)}: {device['name']}")
                    specs = self.get_device_specs(device['url'])
                    if specs:
                        with open(self.specs_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                device['url'],
                                specs.get('name', ''),
                                specs.get('pictures', '[]'),
                                json.dumps(specs)
                            ])
                    time.sleep(1)  # Respect the website
                
            logger.success("Data extraction completed successfully!")
            return True
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            return False
