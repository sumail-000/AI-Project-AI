import aiohttp
from bs4 import BeautifulSoup
import csv
from loguru import logger
import time
import json
from typing import Dict, List, Optional, Tuple
import os
import asyncio

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
        self.min_request_interval = 2  # Minimum seconds between requests (reduced from 3)
        self.max_retries = 5  # Increased from 3 for better resilience

    def setup_logger(self):
        logger.add("debug.log", rotation="500 MB", level="DEBUG")

    async def _make_request_impl(self, url, session, headers=None):
        """Make a rate-limited request with retries (async implementation)"""
        headers = headers or self.headers
        retries = 0
        
        while retries < self.max_retries:
            # Ensure minimum time between requests
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                logger.info(f"Rate limiting: waiting {sleep_time:.1f} seconds...")
                await asyncio.sleep(sleep_time)
            
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    self.last_request_time = time.time()
                    
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', self.min_request_interval * (retries + 2)))
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds before retry {retries + 1}/{self.max_retries}")
                        await asyncio.sleep(retry_after)
                        retries += 1
                        continue
                    
                    response.raise_for_status()
                    return await response.text()
                
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if retries == self.max_retries - 1:
                    raise
                retries += 1
                wait_time = self.min_request_interval * (retries + 1)
                logger.warning(f"Request failed: {str(e)}. Retrying in {wait_time} seconds... ({retries}/{self.max_retries})")
                await asyncio.sleep(wait_time)
        
        raise Exception(f"Failed after {self.max_retries} retries")
        
    def _make_request(self, url, headers=None):
        """Synchronous wrapper for the async _make_request_impl method"""
        return asyncio.run(self._make_request_with_session(url, headers))
    
    async def _make_request_with_session(self, url, headers=None):
        """Helper method to create a session and call _make_request_impl"""
        async with aiohttp.ClientSession() as session:
            return await self._make_request_impl(url, session, headers)

    async def get_brands_impl(self, session) -> List[Dict]:
        try:
            logger.info("Fetching brands list")
            html_content = await self._make_request_impl(f"{self.base_url}makers.php3", session)
            soup = BeautifulSoup(html_content, 'html.parser')
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
            
    def get_brands(self) -> List[Dict]:
        """Synchronous wrapper for the async get_brands_impl method"""
        return asyncio.run(self._get_brands_with_session())
    
    async def _get_brands_with_session(self) -> List[Dict]:
        """Helper method to create a session and call get_brands_impl"""
        async with aiohttp.ClientSession() as session:
            return await self.get_brands_impl(session)

    async def get_device_pictures_impl(self, url: str, session) -> List[str]:
        try:
            logger.info(f"Fetching pictures for device: {url}")
            html_content = await self._make_request_impl(url, session)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            pictures = []
            # Get main picture from specs page
            picture_elements = soup.select('div.specs-photo-main a')
            if picture_elements:
                main_picture = picture_elements[0]['href']
                if main_picture:
                    pictures.append(self.base_url + main_picture)
            
            # Try to find additional pictures on specs page
            thumbnail_elements = soup.select('div.specs-photo-sub a')
            for thumbnail in thumbnail_elements:
                if 'href' in thumbnail.attrs:
                    picture_url = thumbnail['href']
                    if picture_url:
                        pictures.append(self.base_url + picture_url)
            
            # Try to get additional pictures from the pictures page
            try:
                # Extract the device ID from the URL to build the pictures page URL
                device_id = url.split('-')[-1].split('.')[0]
                # Extract the base device name without the ID
                device_base_name = url.split('/')[-1].split('.')[0]
                if '-' in device_base_name:
                    device_base_name = device_base_name.rsplit('-', 1)[0]  # Remove the ID part if present
                # Correct format is: device_base_name-pictures-device_id.php
                pictures_url = f"{self.base_url}{device_base_name}-pictures-{device_id}.php"
                
                logger.info(f"Fetching additional pictures from: {pictures_url}")
                
                try:
                    pics_html_content = await self._make_request_impl(pictures_url, session)
                    pics_soup = BeautifulSoup(pics_html_content, 'html.parser')
                    
                    # Get all images in the pictures list
                    image_elements = pics_soup.select('#pictures-list img')
                    for img in image_elements:
                        if 'src' in img.attrs:
                            picture_url = img['src']
                            if picture_url and not picture_url.endswith('placeholder.jpg'):
                                if picture_url not in pictures:  # Avoid duplicates
                                    pictures.append(picture_url)
                except Exception as e:
                    logger.warning(f"Could not fetch pictures page: {str(e)}")
            except Exception as e:
                logger.warning(f"Error processing pictures page URL: {str(e)}")
            
            logger.info(f"Found {len(pictures)} pictures for device")
            return pictures
        except Exception as e:
            logger.error(f"Error fetching device pictures: {str(e)}")
            return []
            
    def get_device_pictures(self, url: str) -> List[str]:
        """Synchronous wrapper for the async get_device_pictures_impl method"""
        return asyncio.run(self._get_device_pictures_with_session(url))
    
    async def _get_device_pictures_with_session(self, url: str) -> List[str]:
        """Helper method to create a session and call get_device_pictures_impl"""
        async with aiohttp.ClientSession() as session:
            return await self.get_device_pictures_impl(url, session)

    async def get_additional_pictures_impl(self, url: str, session) -> List[str]:
        try:
            # Extract the device ID from the URL to build the pictures page URL
            device_id = url.split('-')[-1].split('.')[0]
            device_name = url.split('/')[-1].split('.')[0]
            # Correct URL format is device_name-pictures-device_id.php without duplicating the ID
            # The device_name already contains the brand and model name
            pictures_url = f"{self.base_url}{device_name}-pictures-{device_id}.php"
            
            logger.info(f"Fetching additional pictures from: {pictures_url}")
            
            try:
                html_content = await self._make_request_impl(pictures_url, session)
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Look for pictures in the pictures gallery
                pictures = []
                picture_heading = None
                heading_element = soup.select_one('#pictures-list h2')
                if heading_element:
                    picture_heading = heading_element.text.strip()
                
                # Get all images in the pictures list
                image_elements = soup.select('#pictures-list img')
                for img in image_elements:
                    if 'src' in img.attrs:
                        picture_url = img['src']
                        if picture_url and not picture_url.endswith('placeholder.jpg'):
                            pictures.append(picture_url)
                
                logger.info(f"Found {len(pictures)} additional pictures for device from pictures page")
                return pictures
            except Exception as e:
                logger.warning(f"Could not fetch pictures page: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching additional device pictures: {str(e)}")
            return []
            
    def get_additional_pictures(self, url: str) -> List[str]:
        """Synchronous wrapper for the async get_additional_pictures_impl method"""
        return asyncio.run(self._get_additional_pictures_with_session(url))
    
    async def _get_additional_pictures_with_session(self, url: str) -> List[str]:
        """Helper method to create a session and call get_additional_pictures_impl"""
        async with aiohttp.ClientSession() as session:
            return await self.get_additional_pictures_impl(url, session)
            
    def get_device_specs(self, url: str) -> Dict:
        """Synchronous wrapper for the async get_device_specs_impl method"""
        return asyncio.run(self._get_device_specs_with_session(url))
    
    async def _get_device_specs_with_session(self, url: str) -> Dict:
        """Helper method to create a session and call get_device_specs_impl"""
        async with aiohttp.ClientSession() as session:
            return await self.get_device_specs_impl(url, session)
            
    async def get_device_specs_impl(self, url: str, session) -> Dict:
        try:
            logger.info(f"Fetching specs for device: {url}")
            html_content = await self._make_request_impl(url, session)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get device name
            name_element = soup.select_one('h1.specs-phone-name-title')
            device_name = name_element.text.strip() if name_element else ""
            
            # Get device pictures
            pictures = await self.get_device_pictures_impl(url, session)
            
            # Extract specifications with proper hierarchy
            specs = {}
            detailed_specs = {}
            spec_tables = soup.select('table')
            
            for table in spec_tables:
                category_element = table.select_one('th')
                if not category_element:
                    continue
                
                category = category_element.text.strip()
                specs[category] = {}
                category_lower = category.lower().replace(' ', '_')
                detailed_specs[category_lower] = {}
                
                # Process all rows in the table
                current_subcategory = None
                rows = table.select('tr')
                
                for row in rows:
                    # Skip the header row with the category name
                    if row.select_one('th') and row.select_one('th').text.strip() == category:
                        continue
                        
                    cells = row.select('td')
                    if len(cells) >= 2:
                        # Get the feature name and value
                        feature = cells[0].text.strip()
                        feature_key = cells[0].get('data-spec', '').strip()
                        
                        # Get the value cell and extract its content
                        value_cell = cells[1]
                        value = value_cell.text.strip()
                        
                        # Special handling for network bands - preserve multiline formatting
                        if category == "Network" and feature in ["2G bands", "3G bands", "4G bands", "5G bands"]:
                            # Check if there are multiple band configurations (e.g., International vs USA models)
                            band_lines = value_cell.get_text(separator='\n').strip().split('\n')
                            if len(band_lines) > 1 or ' - ' in value:
                                # Multiple band configurations detected
                                bands_list = []
                                for line in band_lines:
                                    if line.strip():
                                        bands_list.append(line.strip())
                                
                                # If we didn't get multiple lines but have model indicators
                                if len(bands_list) <= 1 and ' - ' in value:
                                    # Split by model indicators
                                    bands_list = [part.strip() for part in value.split('\n') if part.strip()]
                                    if len(bands_list) <= 1:
                                        # Try another approach for splitting
                                        bands_list = []
                                        current_band = ""
                                        for part in value.split(' - '):
                                            if any(model_indicator in part for model_indicator in ['International', 'USA', 'EU', 'China', 'Japan', 'Korea', 'India']):
                                                if current_band:
                                                    bands_list.append(f"{current_band} - {part}")
                                                    current_band = ""
                                                else:
                                                    current_band = part
                                            else:
                                                if current_band:
                                                    current_band = f"{current_band} - {part}"
                                                else:
                                                    current_band = part
                                        if current_band and current_band not in bands_list:
                                            bands_list.append(current_band)
                                
                                if bands_list:
                                    value = bands_list
                        
                        # Extract technology field for both hierarchies
                        if category == "Network" and feature == "Technology":
                            specs["technology"] = value
                            detailed_specs["network"]["technology"] = value
                        
                        # Handle empty feature cells (continuation of previous subcategory)
                        if feature == "" and cells[0].get('class') and 'ttl' in cells[0].get('class'):
                            if current_subcategory and current_subcategory in specs[category]:
                                # This is additional data for the current subcategory
                                if isinstance(specs[category][current_subcategory], list):
                                    specs[category][current_subcategory].append(value)
                                else:
                                    # Convert to list if it wasn't already
                                    specs[category][current_subcategory] = [specs[category][current_subcategory], value]
                            continue
                        
                        # Store data in both hierarchies
                        specs[category][feature] = value
                        
                        # Also store in the detailed_specs with data-spec attribute as key if available
                        if feature_key:
                            detailed_specs[category_lower][feature_key] = value
                        else:
                            # Convert feature name to snake_case for consistency
                            feature_snake = feature.lower().replace(' ', '_').replace('-', '_')
                            detailed_specs[category_lower][feature_snake] = value
                        
                        current_subcategory = feature
            
            # Extract additional important fields directly from the HTML for more accuracy using data-spec attributes
            
            # Network technology
            technology = ""
            tech_element = soup.select_one('td.nfo[data-spec="nettech"]')
            if tech_element:
                technology = tech_element.text.strip()
                detailed_specs["network"]["technology"] = technology
            elif 'Network' in specs and 'Technology' in specs['Network']:
                technology = specs['Network']['Technology']
                detailed_specs["network"]["technology"] = technology
                
            # Display type
            display_type = ""
            display_element = soup.select_one('td.nfo[data-spec="displaytype"]')
            if display_element:
                display_type = display_element.text.strip()
                detailed_specs["display"]["displaytype"] = display_type
            elif 'Display' in specs and 'Type' in specs['Display']:
                display_type = specs['Display']['Type']
                detailed_specs["display"]["displaytype"] = display_type
                
            # Dimensions
            dimensions = ""
            dimensions_element = soup.select_one('td.nfo[data-spec="dimensions"]')
            if dimensions_element:
                dimensions = dimensions_element.text.strip()
                detailed_specs["body"]["dimensions"] = dimensions
            elif 'Body' in specs and 'Dimensions' in specs['Body']:
                dimensions = specs['Body']['Dimensions']
                detailed_specs["body"]["dimensions"] = dimensions
                
            # OS information
            os_info = ""
            os_element = soup.select_one('td.nfo[data-spec="os"]')
            if os_element:
                os_info = os_element.text.strip()
                detailed_specs["platform"]["os"] = os_info
            elif 'Platform' in specs and 'OS' in specs['Platform']:
                os_info = specs['Platform']['OS']
                detailed_specs["platform"]["os"] = os_info
                
            # Colors
            colors = ""
            colors_element = soup.select_one('td.nfo[data-spec="colors"]')
            if colors_element:
                colors = colors_element.text.strip()
                detailed_specs["misc"]["colors"] = colors
            elif 'Misc' in specs and 'Colors' in specs['Misc']:
                colors = specs['Misc']['Colors']
                detailed_specs["misc"]["colors"] = colors
                
            # Battery type
            battery_type = ""
            battery_element = soup.select_one('td.nfo[data-spec="batdescription1"]')
            if battery_element:
                battery_type = battery_element.text.strip()
                detailed_specs["battery"]["type"] = battery_type
            elif 'Battery' in specs and 'Type' in specs['Battery']:
                battery_type = specs['Battery']['Type']
                detailed_specs["battery"]["type"] = battery_type
                
            # Main camera - improved extraction with proper formatting
            main_camera = ""
            camera_element = soup.select_one('td.nfo[data-spec="cam1modules"]')
            if camera_element:
                # Preserve the original formatting with newlines
                main_camera = camera_element.get_text(separator='\n').strip()
                detailed_specs["main_camera"]["modules"] = main_camera
            elif 'Main Camera' in specs:
                # Try to reconstruct from the specs dictionary
                camera_specs = []
                for key, value in specs['Main Camera'].items():
                    if key in ['Single', 'Dual', 'Triple', 'Quad']:
                        camera_specs.append(value)
                        break
                if camera_specs:
                    main_camera = '\n'.join(camera_specs)
                    detailed_specs["main_camera"]["modules"] = main_camera
                    
            # Selfie camera - improved extraction with proper formatting
            selfie_camera = ""
            selfie_element = soup.select_one('td.nfo[data-spec="cam2modules"]')
            if selfie_element:
                # Preserve the original formatting with newlines
                selfie_camera = selfie_element.get_text(separator='\n').strip()
                detailed_specs["selfie_camera"]["modules"] = selfie_camera
            elif 'Selfie camera' in specs:
                # Try to reconstruct from the specs dictionary
                camera_specs = []
                for key, value in specs['Selfie camera'].items():
                    if key in ['Single', 'Dual']:
                        camera_specs.append(value)
                        break
                if camera_specs:
                    selfie_camera = '\n'.join(camera_specs)
                    detailed_specs["selfie_camera"]["modules"] = selfie_camera
                    
            # Extract sensors
            sensors = ""
            sensors_element = soup.select_one('td.nfo[data-spec="sensors"]')
            if sensors_element:
                sensors = sensors_element.text.strip()
                detailed_specs["features"]["sensors"] = sensors
            elif 'Features' in specs and 'Sensors' in specs['Features']:
                sensors = specs['Features']['Sensors']
                detailed_specs["features"]["sensors"] = sensors
            
            # Extract additional features
            features_element = soup.select_one('td.nfo[data-spec="featuresother"]')
            if features_element:
                features_text = features_element.get_text(separator='\n').strip()
                if features_text:
                    detailed_specs["features"]["other"] = features_text
            
            # Extract price information with proper formatting
            price_info = {}
            price_element = soup.select_one('td.nfo[data-spec="price"]')
            if price_element:
                price_text = price_element.text.strip()
                price_info['text'] = price_text
                detailed_specs["price"] = {"text": price_text}
                
                # Try to extract structured price data
                price_links = price_element.select('a')
                if price_links:
                    price_url = price_links[0].get('href')
                    if price_url:
                        # There might be detailed pricing available
                        full_price_url = self.base_url + price_url
                        price_info['url'] = full_price_url
                        detailed_specs["price"]["url"] = full_price_url
            
            # Combine all data into a comprehensive result
            result = {
                "name": device_name,
                "url": url,
                "pictures": json.dumps(pictures),
                "specifications": specs,  # Original hierarchical specs
                "detailed_specs": detailed_specs,  # New detailed specs with consistent keys
                "technology": technology,
                "display_type": display_type,
                "dimensions": dimensions,
                "os": os_info,
                "colors": colors,
                "battery_type": battery_type,
                "main_camera": main_camera,
                "selfie_camera": selfie_camera,
                "sensors": sensors,
                "price_info": json.dumps(price_info)
            }
            
            # Log successful extraction
            logger.success(f"Successfully extracted specifications for {device_name}")
            return result
        except Exception as e:
            logger.error(f"Error fetching device specs: {str(e)}")
            return {}

    async def get_devices_from_brand_impl(self, brand_url: str, session) -> List[Dict]:
        try:
            logger.info(f"Fetching devices from brand: {brand_url}")
            all_devices = []
            current_url = brand_url
            page = 1
            
            while True:
                logger.info(f"Fetching page {page} from {current_url}")
                html_content = await self._make_request_impl(current_url, session)
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract devices from current page
                device_elements = soup.select('div.makers ul li')
                for device_element in device_elements:
                    link = device_element.select_one('a')
                    img = device_element.select_one('img')
                    
                    if not link or 'href' not in link.attrs:
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
                    await asyncio.sleep(1)  # Respect rate limiting between pages
                else:
                    break
                
            logger.info(f"Found total {len(all_devices)} devices across {page} pages")
            return all_devices
        except Exception as e:
            logger.error(f"Error fetching devices for brand: {str(e)}")
            return []
            
    def get_devices_from_brand(self, brand_url: str) -> List[Dict]:
        """Synchronous wrapper for the async get_devices_from_brand_impl method"""
        return asyncio.run(self._get_devices_from_brand_with_session(brand_url))
    
    async def _get_devices_from_brand_with_session(self, brand_url: str) -> List[Dict]:
        """Helper method to create a session and call get_devices_from_brand_impl"""
        async with aiohttp.ClientSession() as session:
            return await self.get_devices_from_brand_impl(brand_url, session)

    async def save_to_csv_impl(self):
        try:
            # Create/clear the CSV files
            with open(self.brands_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['brand_name', 'device_name', 'device_url', 'device_image'])
            
            # Enhanced CSV structure with more detailed specifications
            with open(self.specs_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'device_url', 'name', 'pictures', 'specifications', 'technology',
                    'display_type', 'dimensions', 'os', 'colors', 'battery_type',
                    'main_camera', 'selfie_camera', 'sensors', 'price_info'
                ])
            
            # Create a shared session for all requests
            async with aiohttp.ClientSession() as session:
                # Get all brands
                brands = await self.get_brands_impl(session)
                total_brands = len(brands)
                
                for brand_idx, brand in enumerate(brands, 1):
                    logger.info(f"Processing brand {brand_idx}/{total_brands}: {brand['name']}")
                    
                    # Get all devices for the brand
                    devices = await self.get_devices_from_brand_impl(brand['url'], session)
                    
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
                        specs = await self.get_device_specs_impl(device['url'], session)
                        if specs:
                            with open(self.specs_file, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                # Check if this device URL already exists in the file to avoid duplicates
                                duplicate_found = False
                                try:
                                    with open(self.specs_file, 'r', newline='', encoding='utf-8') as check_file:
                                        reader = csv.reader(check_file)
                                        next(reader)  # Skip header
                                        for row in reader:
                                            if row and row[0] == device['url']:
                                                duplicate_found = True
                                                logger.warning(f"Skipping duplicate entry for {specs.get('name', '')} at {device['url']}")
                                                break
                                except (FileNotFoundError, csv.Error) as e:
                                    logger.warning(f"Error checking for duplicates: {str(e)}")
                                
                                if not duplicate_found:
                                    writer.writerow([
                                        device['url'],
                                        specs.get('name', ''),
                                        specs.get('pictures', '[]'),
                                        json.dumps(specs.get('specifications', {})),
                                        specs.get('technology', ''),
                                        specs.get('display_type', ''),
                                        specs.get('dimensions', ''),
                                        specs.get('os', ''),
                                        specs.get('colors', ''),
                                        specs.get('battery_type', ''),
                                        specs.get('main_camera', ''),
                                        specs.get('selfie_camera', ''),
                                        specs.get('sensors', ''),
                                        json.dumps(specs.get('price_info', '{}'))
                                    ])
                        # Respect the website's rate limits with optimized value from memory
                        await asyncio.sleep(2)  
                
            logger.success("Data extraction completed successfully!")
            return True
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            return False
            
    def save_to_csv(self):
        """Synchronous wrapper for the async save_to_csv_impl method"""
        return asyncio.run(self.save_to_csv_impl())
