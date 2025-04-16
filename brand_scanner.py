from scraper import GSMArenaScraper
from loguru import logger
from bs4 import BeautifulSoup
import requests
import re
import time
import json
import os
from datetime import datetime

class BrandScanner:
    def __init__(self):
        self.scraper = GSMArenaScraper()
        self.brands = []
        self.last_request_time = 0
        self.min_request_interval = 3  # Minimum seconds between requests
        self.max_retries = 3
        self.cache_file = 'brands_cache.json'
        self.cache_expiry_hours = 24  # Cache expires after 24 hours
        self.loaded_from_cache = False
        self.cache_info = {
            "last_updated": None,
            "brand_count": 0,
            "time_since_update": None,
            "is_expired": False
        }

    def _make_request(self, url, headers=None):
        """Make a rate-limited request with retries"""
        headers = headers or self.scraper.headers
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

    def scan_brands(self):
        """
        Scans brand names, URLs, and gets their device counts.
        First tries to load from cache, if not available or expired, performs actual scan.
        """
        # Try to load from cache first
        cached_brands = self.load_brands_from_cache()
        if cached_brands:
            logger.info("Loaded brands from cache file")
            self.brands = cached_brands
            self.loaded_from_cache = True
            return self.brands

        try:
            logger.info("Starting brand scan...")
            
            # Use rate-limited request
            response = self._make_request(f"{self.scraper.base_url}makers.php3")
            
            if not response.text:
                raise Exception("Empty response received from GSMArena")
                
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all brand links in the brand menu
            brand_menu = soup.find('div', {'class': 'st-text'})
            if not brand_menu:
                logger.error("Could not find brands menu div with class 'st-text'")
                raise Exception("Could not find brands menu")

            brand_links = brand_menu.find_all('a')
            if not brand_links:
                logger.error("No brand links found in the brands menu")
                raise Exception("No brand links found")
                
            brands_list = []
            logger.info(f"Found {len(brand_links)} potential brand links")

            for link in brand_links:
                try:
                    # Get the brand name by taking everything before any numbers
                    full_text = link.text.strip()
                    brand_name = re.sub(r'\d+.*$', '', full_text).strip()
                    brand_url = link.get('href')
                    
                    if not brand_name or not brand_url:
                        logger.warning(f"Skipping invalid brand link: {full_text}")
                        continue
                        
                    # Extract device count from the text
                    count_match = re.search(r'(\d+)\s*devices?', full_text)
                    device_count = 0
                    if count_match:
                        device_count = int(count_match.group(1))
                    
                    brand_data = {
                        "name": brand_name,
                        "url": self.scraper.base_url + brand_url,
                        "device_count": device_count
                    }
                    brands_list.append(brand_data)
                    logger.debug(f"Scanned {brand_name}: {device_count} devices")
                except Exception as e:
                    logger.error(f"Error processing brand link {full_text}: {str(e)}")
                    continue

            if not brands_list:
                logger.error("No valid brands found")
                raise Exception("No valid brands found")

            self.brands = sorted(brands_list, key=lambda x: x['name'])
            logger.success(f"Successfully scanned {len(self.brands)} brands")
            
            # Save to cache
            self.save_brands_to_cache(self.brands)
            self.loaded_from_cache = False
            
            return self.brands

        except requests.RequestException as e:
            error_msg = f"Network error while scanning brands: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error scanning brands: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def save_brands_to_cache(self, brands):
        """Save brands data to cache file with timestamp"""
        try:
            current_time = datetime.now()
            cache_data = {
                'timestamp': current_time.isoformat(),
                'brands': brands,
                'brand_count': len(brands)
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            # Update cache info
            self.cache_info = {
                "last_updated": current_time.isoformat(),
                "brand_count": len(brands),
                "time_since_update": "just now",
                "is_expired": False
            }
                
            logger.info(f"Saved {len(brands)} brands to cache file")
            return True
        except Exception as e:
            logger.error(f"Error saving brands to cache: {str(e)}")
            return False
            
    def load_brands_from_cache(self):
        """Load brands from cache file if it exists and is not expired"""
        try:
            if not os.path.exists(self.cache_file):
                logger.info("Cache file does not exist")
                return None
                
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # Check if cache is expired
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            current_time = datetime.now()
            time_diff_seconds = (current_time - cache_time).total_seconds()
            time_diff_hours = time_diff_seconds / 3600  # Hours
            
            # Format time since update in a human-readable way
            if time_diff_seconds < 60:
                time_since_update = f"{int(time_diff_seconds)} seconds ago"
            elif time_diff_seconds < 3600:
                time_since_update = f"{int(time_diff_seconds / 60)} minutes ago"
            elif time_diff_seconds < 86400:
                time_since_update = f"{int(time_diff_hours)} hours ago"
            else:
                time_since_update = f"{int(time_diff_hours / 24)} days ago"
            
            # Update cache info
            self.cache_info = {
                "last_updated": cache_time.isoformat(),
                "brand_count": len(cache_data['brands']),
                "time_since_update": time_since_update,
                "is_expired": time_diff_hours > self.cache_expiry_hours
            }
            
            if time_diff_hours > self.cache_expiry_hours:
                logger.info(f"Cache is expired ({time_diff_hours:.1f} hours old)")
                return None
                
            logger.info(f"Cache is valid ({time_diff_hours:.1f} hours old)")
            return cache_data['brands']
        except Exception as e:
            logger.error(f"Error loading brands from cache: {str(e)}")
            return None
            
    def get_cache_status(self):
        """Return the current cache status information"""
        # Check if cache exists even if not loaded
        if not self.cache_info["last_updated"] and os.path.exists(self.cache_file):
            self.load_brands_from_cache()  # This will update cache_info
            
        return self.cache_info

    def get_brand_devices_count(self, brand_url):
        """Get the total number of devices for a brand from its page"""
        try:
            response = self._make_request(brand_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # First try to get count from the review-header h1 text
            review_header = soup.find('div', {'class': 'review-header'})
            if review_header:
                h1_text = review_header.find('h1')
                if h1_text:
                    count_match = re.search(r'(\d+)\s+phones?', h1_text.text)
                    if count_match:
                        return int(count_match.group(1))

            # If not found in header, get it from the makers div
            makers_div = soup.find('div', {'class': 'makers'})
            if makers_div:
                devices = makers_div.find_all('li')
                return len(devices)

            return 0

        except Exception as e:
            logger.error(f"Error getting device count for {brand_url}: {str(e)}")
            return 0
