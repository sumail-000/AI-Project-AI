import pandas as pd
import numpy as np
import json
import re
import os
from loguru import logger
import traceback
import random
# Import responses from the responses module
from responses import (
    CATEGORY_RESPONSES, FALLBACK_RESPONSES, DEVICE_TEMPLATES, 
    FEATURE_KEYWORDS, RECOMMENDATION_KEYWORDS, DEVICE_TYPES, 
    POPULAR_BRANDS, COMPARISON_KEYWORDS, SPECIFICATION_KEYWORDS,
    QUERY_TYPES, SENTIMENT_KEYWORDS, USAGE_PATTERN_KEYWORDS,
    ADVANCED_RESPONSES, USAGE_PATTERN_RESPONSES, TROUBLESHOOTING_RESPONSES
)

class DeviceAIAssistant:
    """AI Assistant for mobile device data search using direct CSV linking."""
    
    def __init__(self, device_data_path='brands_devices.csv', specs_data_path='device_specifications.csv'):
        """Initialize the AI assistant with device data.
        
        Args:
            device_data_path: Path to the CSV file containing device basic info
            specs_data_path: Path to the CSV file containing device specifications
        """
        self.device_data_path = device_data_path
        self.specs_data_path = specs_data_path
        
        # Load and process data
        self.unified_data = self._process_device_data()
        logger.info("AI Assistant initialized with direct CSV linking")
    
    def _process_device_data(self):
        """Load and process device data from CSV files according to file structure.
        
        brands_devices.csv structure:
        Brand,DeviceName,DeviceURL,ImageURL
        
        Example: 
        Amazon,Fire Max 11,https://www.gsmarena.com/amazon_fire_max_11-12382.php,https://fdn2.gsmarena.com/vv/bigpic/amazon-fire-max-11.jpg
        
        device_specifications.csv structure:
        device_url,full_device_name,pictures,specifications
        
        Example:
        https://www.gsmarena.com/amazon_fire_max_11-12382.php,Amazon Fire Max 11,...
        """
        try:
            # Load brands_devices.csv (no header in file)
            # Format: Brand,DeviceName,DeviceURL,ImageURL
            brands_df = pd.read_csv(self.device_data_path, header=None)
            if len(brands_df.columns) >= 4:
                brands_df.columns = ['brand_name', 'device_name', 'device_url', 'device_image']
                logger.info(f"Loaded {len(brands_df)} devices from {self.device_data_path}")
            else:
                logger.error(f"Unexpected format in {self.device_data_path}, needs 4 columns")
                return pd.DataFrame()
            
            # Load device_specifications.csv with header
            # Format: device_url,full_device_name,pictures,specifications
            specs_df = pd.read_csv(self.specs_data_path)
            if len(specs_df.columns) >= 4:
                logger.info(f"Loaded {len(specs_df)} device specifications from {self.specs_data_path}")
            else:
                logger.error(f"Unexpected format in {self.specs_data_path}, needs 4 columns")
                return brands_df
            
            # Join the data on device_url
            unified_data = pd.merge(brands_df, specs_df, on='device_url', how='left')
            logger.info(f"Created unified data with {len(unified_data)} entries")
            
            # Parse specifications JSON
            def parse_specs(specs_str):
                try:
                    if pd.isna(specs_str):
                        return {}
                    return json.loads(specs_str)
                except Exception as e:
                    logger.warning(f"Error parsing specs JSON: {str(e)}")
                    return {}
            
            # Parse specifications JSON
            unified_data['specs_dict'] = unified_data['specifications'].apply(parse_specs)
            
            return unified_data
        except Exception as e:
            logger.error(f"Error processing device data: {str(e)}")
            logger.error(traceback.format_exc())
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['brand_name', 'device_name', 'device_url', 'device_image', 
                                        'specifications', 'specs_dict'])
    
    def analyze_query_intent(self, query):
        """
        Advanced algorithm to analyze user query, extract intents and entities.
        
        Args:
            query: User's original query text
            
        Returns:
            dict: Analysis results containing intents, entities, and suggested action
        """
        logger.info(f"Performing advanced intent analysis on query: {query}")
        
        # Normalize query text
        query_text = query.lower().strip()
        
        # Initialize analysis structure
        analysis = {
            "original_query": query,
            "normalized_query": query_text,
            "intents": {},
            "entities": {
                "devices": [],
                "brands": [],
                "features": [],
                "specifications": []
            },
            "primary_intent": None,
            "secondary_intent": None,
            "response_type": None,
            "confidence_score": 0.0
        }
        
        # Extract device names and brands
        device_names = self._extract_device_names(query_text)
        for device in device_names:
            analysis["entities"]["devices"].append({
                "brand": device.get("brand", ""),
                "device": device.get("device", ""),
                "full_name": f"{device.get('brand', '')} {device.get('device', '')}"
            })
            if device.get("brand") and device.get("brand") not in analysis["entities"]["brands"]:
                analysis["entities"]["brands"].append(device.get("brand"))
        
        # Extract specifications
        requested_specs = self._extract_specification_requests(query_text)
        for spec in requested_specs:
            analysis["entities"]["specifications"].append(spec)
        
        # Extract features of interest
        for feature, keywords in FEATURE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_text:
                    if feature not in analysis["entities"]["features"]:
                        analysis["entities"]["features"].append(feature)
                    break
        
        # Calculate intent confidence scores
        intent_scores = {}
        
        # Device search intent
        if analysis["entities"]["devices"]:
            intent_scores["device_search"] = 0.7
        
        # Recommendation intent
        for keyword in RECOMMENDATION_KEYWORDS:
            if keyword in query_text:
                intent_scores["recommendation"] = 0.7
                break
        
        # Specification intent
        if analysis["entities"]["specifications"]:
            intent_scores["specification"] = 0.7
        
        # Comparison intent
        for keyword in COMPARISON_KEYWORDS:
            if keyword in query_text:
                intent_scores["comparison"] = 0.7
                break
        
        # Feature-specific intents
        for feature in analysis["entities"]["features"]:
            if feature in ["camera", "battery", "performance", "display"]:
                intent_scores[feature] = 0.7
        
        # Simple intents
        simple_intents = {
            'greeting': ['hi', 'hello', 'hey', 'greetings'],
            'farewell': ['bye', 'goodbye', 'see you'],
            'thanks': ['thank you', 'thanks'],
            'help': ['help', 'assist', 'how to use']
        }
        
        for intent, keywords in simple_intents.items():
            for keyword in keywords:
                if keyword in query_text:
                    intent_scores[intent] = 0.5
                    break
        
        # Default intent
        if not intent_scores:
            intent_scores["general"] = 0.3
        
        # Sort intents by confidence score
        analysis["intents"] = dict(sorted(intent_scores.items(), key=lambda x: x[1], reverse=True))
        
        # Assign primary and secondary intents
        if analysis["intents"]:
            intents_list = list(analysis["intents"].items())
            analysis["primary_intent"] = intents_list[0][0]
            analysis["confidence_score"] = intents_list[0][1]
            if len(intents_list) > 1:
                analysis["secondary_intent"] = intents_list[1][0]
        
        # Determine response type
        if "comparison" in analysis["intents"] and len(analysis["entities"]["devices"]) >= 2:
            analysis["response_type"] = "comparison"
        elif "device_search" in analysis["intents"] and "specification" in analysis["intents"]:
            analysis["response_type"] = "device_specs"
        elif "device_search" in analysis["intents"]:
            analysis["response_type"] = "device_details"
        elif "recommendation" in analysis["intents"]:
            analysis["response_type"] = "recommendations"
        else:
            # Default to conversational
            analysis["response_type"] = "conversation"
        
        logger.info(f"Query intent analysis complete. Primary intent: {analysis['primary_intent']}, Response type: {analysis['response_type']}")
        
        return analysis
    
    def _log_intent_analysis(self, analysis):
        """
        Log the query intent analysis in a formatted, easy-to-read way.
        
        Args:
            analysis: The analysis dictionary returned by analyze_query_intent
        """
        logger.info("===== QUERY INTENT ANALYSIS =====")
        logger.info(f"Original query: '{analysis['original_query']}'")
        logger.info(f"Primary intent: {analysis['primary_intent']} (confidence: {analysis['confidence_score']:.2f})")
        
        if analysis.get('secondary_intent'):
            logger.info(f"Secondary intent: {analysis['secondary_intent']}")
        
        logger.info(f"Response type: {analysis['response_type']}")
        
        # Log all detected intents with scores
        if analysis['intents']:
            logger.info("Detected intents (ordered by confidence):")
            for intent, score in analysis['intents'].items():
                logger.info(f"  - {intent}: {score:.2f}")
        
        # Log entities
        if analysis['entities']['devices']:
            logger.info("Detected devices:")
            for device in analysis['entities']['devices']:
                if isinstance(device, dict) and 'full_name' in device:
                    logger.info(f"  - {device['full_name']}")
                elif isinstance(device, dict) and 'type' in device:
                    logger.info(f"  - Device type: {device['type']}")
        
        if analysis['entities']['brands']:
            logger.info(f"Detected brands: {', '.join(analysis['entities']['brands'])}")
        
        if analysis['entities']['features']:
            logger.info(f"Detected features: {', '.join(analysis['entities']['features'])}")
        
        if analysis['entities']['specifications']:
            logger.info(f"Requested specifications: {', '.join(analysis['entities']['specifications'])}")
        
        logger.info("==================================")
    
    def handle_conversation(self, user_input):
        """Handle conversation input with advanced intent analysis and targeted responses."""
        # Log the query
        logger.info(f"Processing query: {user_input}")
        
        # Perform comprehensive query analysis
        query_analysis = self.analyze_query_intent(user_input)
        
        # Log the full analysis
        self._log_intent_analysis(query_analysis)
        
        # Extract key analysis results
        primary_intent = query_analysis["primary_intent"]
        response_type = query_analysis["response_type"]
        devices = query_analysis["entities"]["devices"]
        brands = query_analysis["entities"]["brands"]
        features = query_analysis["entities"]["features"]
        specs = query_analysis["entities"]["specifications"]
        
        # Convert device entries to a format compatible with existing methods
        device_names = []
        for device in devices:
            if isinstance(device, dict) and "brand" in device and "device" in device:
                device_names.append({
                    "brand": device["brand"],
                    "device": device["device"]
                })
        
        # Handle different response types based on the analysis
        if response_type == "comparison" and len(device_names) >= 2:
            # Handle device comparison
            logger.info(f"Handling comparison between devices: {device_names}")
            return self.compare_devices(user_input)
            
        elif response_type == "device_specs" and device_names:
            # Get device info with specific specs highlighted
            devices_df = self._search_devices_by_name(device_names)
            if not devices_df.empty:
                device_info = self._format_device_data(devices_df.iloc[0])
                # Extract requested specs
                if specs and 'specifications' in device_info:
                    requested_specs = self._extract_requested_specs(
                        device_info['specifications'],
                        specs
                    )
                    return self._generate_spec_response(device_info, specs, requested_specs)
            else:
                logger.info(f"No device found matching names: {device_names}")
                return FALLBACK_RESPONSES['no_device_found']
                
        elif response_type == "device_details" and device_names:
            # Get general device details
            devices_df = self._search_devices_by_name(device_names)
            if not devices_df.empty:
                device_info = self._format_device_data(devices_df.iloc[0])
                return self._generate_general_device_response(device_info)
            else:
                logger.info(f"No device found matching names: {device_names}")
                return FALLBACK_RESPONSES['no_device_found']
                
        elif response_type == "recommendations":
            # Get device recommendations
            recommendations = self.get_device_recommendations(user_input)
            if recommendations:
                # Determine appropriate message based on features
                if features and len(features) > 0:
                    feature = features[0]  # Use the first detected feature
                    message = DEVICE_TEMPLATES['recommendation_specific'].format(feature=feature)
                elif brands and len(brands) > 0:
                    brand = brands[0]  # Use the first detected brand
                    message = DEVICE_TEMPLATES['recommendation_brand'].format(brand=brand)
                else:
                    message = DEVICE_TEMPLATES['recommendation_intro']
                
                logger.info(f"Returning {len(recommendations)} recommendations with message: {message}")
                return {
                    'type': 'recommendations',
                    'devices': recommendations,
                    'message': message
                }
            else:
                logger.info("No recommendations found, using fallback")
                return FALLBACK_RESPONSES['no_recommendations']
        
        # Handle feature-specific queries (camera, battery, etc.)
        elif primary_intent in ["camera", "battery", "performance", "display"] and device_names:
            # Get specific feature details for a device
            devices_df = self._search_devices_by_name(device_names)
            if not devices_df.empty:
                device_info = self._format_device_data(devices_df.iloc[0])
                
                # Map features to spec categories
                feature_to_spec = {
                    "camera": ["camera", "main_camera", "selfie_camera"],
                    "battery": ["battery", "battery_life", "charging"],
                    "performance": ["processor", "cpu", "chipset", "platform"],
                    "display": ["display", "screen"]
                }
                
                if primary_intent in feature_to_spec:
                    requested_specs = self._extract_requested_specs(
                        device_info.get('specifications', {}),
                        feature_to_spec[primary_intent]
                    )
                    return self._generate_spec_response(device_info, feature_to_spec[primary_intent], requested_specs)
                else:
                    return self._generate_general_device_response(device_info)
            else:
                # If no specific device, show recommendations for this feature
                recommendations = self.get_device_recommendations(user_input)
                if recommendations:
                    message = DEVICE_TEMPLATES['recommendation_specific'].format(feature=primary_intent)
                    return {
                        'type': 'recommendations',
                        'devices': recommendations,
                        'message': message
                    }
        
        # For conversation and other intents, use the standard category-based approach
        return self._get_response_for_category(primary_intent, user_input)
    
    def _extract_device_names(self, query):
        """Extract potential device names from the query."""
        device_names = []
        
        # Create a list of all brand and device name combinations
        all_devices = []
        for _, row in self.unified_data.iterrows():
            brand = row.get('brand_name', '').lower()
            device = row.get('device_name', '').lower()
            # Add full name (brand + device)
            all_devices.append({
                'full_name': f"{brand} {device}",
                'brand': brand,
                'device': device
            })
            # Also add just device name for cases where brand isn't mentioned
            all_devices.append({
                'full_name': device,
                'brand': brand,
                'device': device
            })
        
        # Sort by length (descending) to match longest names first
        all_devices.sort(key=lambda x: len(x['full_name']), reverse=True)
        
        # Convert query to lowercase for matching
        query_lower = query.lower()
        
        # Find matches in query
        for device_info in all_devices:
            if device_info['full_name'] in query_lower:
                # Avoid duplicate additions
                if not any(d['device'] == device_info['device'] and d['brand'] == device_info['brand'] for d in device_names):
                    device_names.append({
                        'brand': device_info['brand'],
                        'device': device_info['device']
                    })
        
        return device_names
    
    def _extract_specification_requests(self, query):
        """Extract requested specifications from query."""
        query_lower = query.lower()
        
        # Common specification keywords to look for
        spec_keywords = {
            'battery': ['battery', 'battery capacity', 'battery life', 'charge', 'charging'],
            'camera': ['camera', 'megapixel', 'mp', 'photo', 'selfie', 'front camera', 'rear camera'],
            'display': ['display', 'screen', 'resolution', 'refresh rate', 'hz', 'amoled', 'lcd', 'oled'],
            'processor': ['processor', 'cpu', 'chipset', 'snapdragon', 'exynos', 'mediatek', 'tensor'],
            'memory': ['memory', 'ram', 'storage', 'gb', 'tb'],
            'dimensions': ['dimensions', 'size', 'width', 'height', 'weight'],
            'os': ['os', 'android', 'ios', 'operating system', 'software'],
            'price': ['price', 'cost', 'value', 'dollars', 'expensive', 'cheap']
        }
        
        # Track which specifications were requested
        requested_specs = []
        
        # Check for each specification type
        for spec_type, keywords in spec_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    requested_specs.append(spec_type)
                    break  # Once we find one keyword for this spec type, move to next
        
        return requested_specs
    
    def _search_devices_by_name(self, device_names):
        """Search for devices using extracted device names."""
        if not device_names:
            return pd.DataFrame()
        
        # Build filter mask for each device
        all_masks = []
        for device_info in device_names:
            brand = device_info.get('brand', '').lower()
            device = device_info.get('device', '').lower()
            
            # Match by brand and device name
            mask = (
                self.unified_data['brand_name'].str.lower() == brand
            ) & (
                self.unified_data['device_name'].str.lower() == device
            )
            
            all_masks.append(mask)
        
        # Combine all masks with OR logic
        final_mask = all_masks[0]
        for mask in all_masks[1:]:
            final_mask = final_mask | mask
        
        matching_devices = self.unified_data[final_mask]
        
        if len(matching_devices) > 0:
            return matching_devices
        
        # If no exact matches, try partial matches
        all_masks = []
        for device_info in device_names:
            brand = device_info.get('brand', '').lower()
            device = device_info.get('device', '').lower()
            
            # Match by partial brand and device name
            mask = (
                self.unified_data['brand_name'].str.lower().str.contains(brand, na=False)
            ) & (
                self.unified_data['device_name'].str.lower().str.contains(device, na=False)
            )
            
            all_masks.append(mask)
        
        # Combine all masks with OR logic
        final_mask = all_masks[0]
        for mask in all_masks[1:]:
            final_mask = final_mask | mask
        
        return self.unified_data[final_mask].head(10)  # Limit to top 10 matches
    
    def _search_by_exact_match(self, query):
        """Search for devices by exact name match."""
        query = query.lower()
        
        # Try exact match on device name
        exact_matches = self.unified_data[
            self.unified_data['device_name'].str.lower().str.contains(query, na=False) |
            (self.unified_data['brand_name'].str.lower() + " " + self.unified_data['device_name'].str.lower()).str.contains(query, na=False)
        ]
        
        if len(exact_matches) > 0:
            return exact_matches.head(10)  # Limit to top 10 matches
        
        return pd.DataFrame()  # No matches
    
    def _extract_requested_specs(self, specs_dict, requested_specs):
        """Extract requested specifications from the full specs dictionary."""
        if not specs_dict or not requested_specs:
            return {}
            
        result = {}
        
        # Map requested spec categories to relevant paths in specs dictionary
        spec_mapping = {
            'battery': ['battery', 'Battery', 'battery_type', 'battery life', 'charging'],
            'camera': ['main_camera', 'selfie_camera', 'Main Camera', 'Selfie camera'],
            'display': ['display', 'Display', 'display_type', 'resolution'],
            'processor': ['platform', 'Platform', 'cpu', 'chipset', 'gpu'],
            'memory': ['memory', 'Memory', 'internal', 'ram'],
            'dimensions': ['dimensions', 'body', 'Body', 'weight'],
            'os': ['os', 'platform', 'Platform'],
            'price': ['price', 'price_info', 'Misc']
        }
        
        # Track added keys to prevent duplicates
        added_keys = set()
        
        # For each requested spec, try to find it in the specs dictionary
        for spec_type in requested_specs:
            if spec_type in spec_mapping:
                # Initialize result for this spec type if not already present
                if spec_type not in result:
                    result[spec_type] = {}
                
                # Try each possible path for this spec type
                for path in spec_mapping[spec_type]:
                    # Look for the path in the top level
                    if path in specs_dict:
                        # If it's a dictionary, add all its contents that haven't been added yet
                        if isinstance(specs_dict[path], dict):
                            for key, value in specs_dict[path].items():
                                # Check for similar keys that might already be added with different casing
                                key_lower = key.lower()
                                if not any(k.lower() == key_lower for k in added_keys):
                                    result[spec_type][key] = value
                                    added_keys.add(key)
                        else:
                            # If it's a string or other value, add it directly if not already added
                            path_lower = path.lower()
                            if not any(k.lower() == path_lower for k in added_keys):
                                result[spec_type][path] = specs_dict[path]
                                added_keys.add(path)
                    
                    # Also check in nested dictionaries
                    for key, value in specs_dict.items():
                        if isinstance(value, dict) and path in value:
                            if isinstance(value[path], dict):
                                for sub_key, sub_value in value[path].items():
                                    # Check if similar key already exists
                                    sub_key_lower = sub_key.lower()
                                    if not any(k.lower() == sub_key_lower for k in added_keys):
                                        result[spec_type][sub_key] = sub_value
                                        added_keys.add(sub_key)
                            else:
                                # Skip if a similar key is already present
                                path_lower = path.lower()
                                if not any(k.lower() == path_lower for k in added_keys):
                                    result[spec_type][path] = value[path]
                                    added_keys.add(path)
        
        return result
    
    def _format_device_data(self, device_data):
        """Format device data for API response."""
        try:
            formatted_device = {
                'brand_name': device_data.get('brand_name', ''),
                'device_name': device_data.get('device_name', ''),
                'device_url': device_data.get('device_url', ''),
                'device_image': device_data.get('device_image', '')
            }
            
            # Add full name
            formatted_device['name'] = f"{formatted_device['brand_name']} {formatted_device['device_name']}"
            
            # For URL compatibility
            formatted_device['url'] = formatted_device['device_url']
            formatted_device['image_url'] = formatted_device['device_image']
            
            # Add image from pictures if available
            if 'pictures' in device_data and not pd.isna(device_data['pictures']):
                try:
                    pictures_str = device_data['pictures']
                    if isinstance(pictures_str, str):
                        pictures = json.loads(pictures_str.replace("'", '"'))
                        if isinstance(pictures, list) and len(pictures) > 0:
                            formatted_device['pictures'] = pictures
                    elif isinstance(pictures_str, list):
                        formatted_device['pictures'] = pictures_str
                except Exception as e:
                    logger.warning(f"Error parsing pictures JSON: {str(e)}")
                    # If we can't parse it, try to convert it to a string
                    if isinstance(device_data['pictures'], (list, dict)):
                        try:
                            formatted_device['pictures'] = [str(p) for p in device_data['pictures'] if p]
                        except:
                            pass
            
            # Add specifications
            if 'specs_dict' in device_data:
                specs = {}
                if isinstance(device_data['specs_dict'], dict):
                    specs = device_data['specs_dict']
                # Ensure all values are serializable
                for key, value in specs.items():
                    if isinstance(value, pd.Series) or hasattr(value, 'to_dict'):
                        specs[key] = value.to_dict() if hasattr(value, 'to_dict') else {str(k): str(v) for k, v in value.items()}
                
                # Log the structure of the specs_dict
                logger.info(f"Specs structure for {device_data.get('device_name', 'unknown device')}: {list(specs.keys())}")
                formatted_device['specifications'] = specs
            
            return formatted_device
        except Exception as e:
            logger.error(f"Error formatting device data: {str(e)}")
            return {'error': str(e)}
    
    def _generate_spec_response(self, device_info, requested_specs, spec_data):
        """Generate a response about specific device specifications."""
        device_name = f"{device_info.get('brand_name', '')} {device_info.get('device_name', '')}"
        
        if not spec_data:
            return FALLBACK_RESPONSES['no_specs_found']
        
        # Start with device name
        response = DEVICE_TEMPLATES['spec_intro'].format(
            specs=', '.join(requested_specs),
            device_name=device_name
        ) + "\n\n"
        
        # Add each requested spec
        for spec_type, data in spec_data.items():
            response += f"• {spec_type.capitalize()}:\n"
            for key, value in data.items():
                # Format the key for better readability
                readable_key = key.replace('_', ' ').title()
                if isinstance(value, dict):
                    response += f"  - {readable_key}: "
                    for sub_key, sub_value in value.items():
                        sub_readable_key = sub_key.replace('_', ' ').title()
                        response += f"{sub_readable_key}: {sub_value}, "
                    response = response.rstrip(', ') + "\n"
                else:
                    response += f"  - {readable_key}: {value}\n"
            response += "\n"
        
        return response.strip()
    
    def _generate_general_device_response(self, device_info):
        """Generate a general response about a device."""
        device_name = f"{device_info.get('brand_name', '')} {device_info.get('device_name', '')}"
        
        response = DEVICE_TEMPLATES['found_device'].format(
            brand_name=device_info.get('brand_name', ''),
            device_name=device_info.get('device_name', '')
        )
        
        # Add some basic specs if available
        specs = device_info.get('specifications', {})
        highlights = []
        
        # Look for display information
        if 'display' in specs or 'Display' in specs:
            display_info = specs.get('display', specs.get('Display', {}))
            if isinstance(display_info, dict):
                size = display_info.get('size', '')
                if size:
                    highlights.append(f"It has a {size} display")
        
        # Look for processor information
        if 'platform' in specs or 'Platform' in specs:
            platform_info = specs.get('platform', specs.get('Platform', {}))
            if isinstance(platform_info, dict):
                chipset = platform_info.get('chipset', '')
                if chipset:
                    highlights.append(f"It's powered by a {chipset}")
        
        # Look for camera information
        if 'main_camera' in specs or 'Main Camera' in specs:
            camera_info = specs.get('main_camera', specs.get('Main Camera', {}))
            if isinstance(camera_info, dict) and 'modules' in camera_info:
                highlights.append(f"The main camera is {camera_info['modules']}")
            elif isinstance(camera_info, str):
                highlights.append(f"The main camera is {camera_info}")
        
        # Look for battery information
        if 'battery_type' in specs:
            highlights.append(f"It has a {specs['battery_type']}")
        elif 'battery' in specs and isinstance(specs['battery'], dict) and 'type' in specs['battery']:
            highlights.append(f"It has a {specs['battery']['type']}")
        
        # Add the highlights to the response
        if highlights:
            response += " " + ". ".join(highlights) + "."
        
        # Ask if the user wants more information
        response += " Would you like to know more specific information about this device?"
        
        return response
    
    def _categorize_input(self, user_input):
        """Categorize user input into predefined categories using pattern matching."""
        user_input = user_input.lower()
        
        logger.info(f"Categorizing input: {user_input}")
        
        # Check for direct device type references
        for device_type in DEVICE_TYPES:
            if device_type in user_input:
                logger.info(f"Detected device type reference: {device_type}")
                # If it also contains a recommendation keyword, it's likely a recommendation request
                if any(keyword in user_input for keyword in RECOMMENDATION_KEYWORDS):
                    logger.info("Categorized as recommendation based on device type + recommendation keywords")
                    return 'recommendation'
                # Otherwise it's likely a general device search
                logger.info("Categorized as device_search based on device type reference")
                return 'device_search'
        
        # Check for brand references
        for brand in POPULAR_BRANDS:
            if brand in user_input:
                logger.info(f"Detected brand reference: {brand}")
                # If we also have recommendation keywords, it's likely a brand-specific recommendation
                if any(keyword in user_input for keyword in RECOMMENDATION_KEYWORDS):
                    logger.info("Categorized as recommendation based on brand + recommendation keywords")
                    return 'recommendation'
        
        # Check for comparison intent
        if any(keyword in user_input for keyword in COMPARISON_KEYWORDS):
            logger.info("Categorized as comparison based on comparison keywords")
            return 'comparison'
        
        # Check for specification intent
        if any(keyword in user_input for keyword in SPECIFICATION_KEYWORDS):
            logger.info("Categorized as specification based on specification keywords")
            return 'specification'
        
        # Check for feature-specific queries
        for feature, keywords in FEATURE_KEYWORDS.items():
            if any(keyword in user_input for keyword in keywords):
                logger.info(f"Detected feature reference: {feature}")
                # If it's a price feature, categorize as price
                if feature == 'price':
                    logger.info("Categorized as price based on price keywords")
                    return 'price'
                # If it's a camera feature, categorize as camera
                elif feature == 'camera':
                    logger.info("Categorized as camera based on camera keywords")
                    return 'camera'
                # If it's a battery feature, categorize as battery
                elif feature == 'battery':
                    logger.info("Categorized as battery based on battery keywords")
                    return 'battery'
                # If it's a performance feature, categorize as performance
                elif feature == 'performance':
                    logger.info("Categorized as performance based on performance keywords")
                    return 'performance'
                # If it's a display feature, categorize as display
                elif feature == 'display':
                    logger.info("Categorized as display based on display keywords")
                    return 'display'
        
        # Define simple keyword-based categories
        categories = {
            'greeting': ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening'],
            'farewell': ['bye', 'goodbye', 'see you', 'talk to you later'],
            'thanks': ['thank you', 'thanks', 'appreciate it'],
            'identity': ['who are you', 'what are you', 'your name', 'about you'],
            'help': ['help', 'assist', 'guidance', 'how to use', 'what can you do', 'capabilities']
        }
        
        # Check for recommendation intent (this is important enough to check separately)
        if any(keyword in user_input for keyword in RECOMMENDATION_KEYWORDS):
            logger.info("Categorized as recommendation based on recommendation keywords")
            return 'recommendation'
        
        # Check for other simple categories
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in user_input:
                    logger.info(f"Categorized as: {category} based on keyword: {keyword}")
                    return category
        
        # Check for specific device references
        for _, row in self.unified_data.iterrows():
            brand_name = row.get('brand_name', '').lower()
            device_name = row.get('device_name', '').lower()
            
            # If both brand and device name are in the query, it's probably a device search
            if brand_name in user_input and device_name in user_input:
                logger.info(f"Categorized as device_search for device: {brand_name} {device_name}")
                return 'device_search'
        
        # Default category
        logger.info("No specific category found, using 'general'")
        return 'general'
    
    def _get_response_for_category(self, category, user_input):
        """Get a hardcoded response based on the category."""
        # Check for recommendation keywords and return a more helpful message
        if any(keyword in user_input.lower() for keyword in RECOMMENDATION_KEYWORDS):
            logger.info(f"Recommendation request in _get_response_for_category: {user_input}")
            # Force recommendations if we somehow end up here with a recommendation request
            recommendations = self.get_device_recommendations(user_input)
            if recommendations:
                logger.info(f"Returning {len(recommendations)} recommendations from _get_response_for_category")
                return {
                    'type': 'recommendations',
                    'devices': recommendations,
                    'message': DEVICE_TEMPLATES['recommendation_intro']
                }
            else:
                return FALLBACK_RESPONSES['no_recommendations']
        
        # First check if the input mentions a specific device
        for _, row in self.unified_data.iterrows():
            brand_name = row.get('brand_name', '').lower()
            device_name = row.get('device_name', '').lower()
            
            # If both brand and device name are in the query, it's probably a device search
            if brand_name in user_input.lower() and device_name in user_input.lower():
                return DEVICE_TEMPLATES['found_device'].format(
                    brand_name=brand_name,
                    device_name=device_name
                )
        
        # Handle recommendation category separately
        if category == 'recommendation':
            # Instead of using a hardcoded response, actually return recommendations
            recommendations = self.get_device_recommendations(user_input)
            if recommendations:
                return {
                    'type': 'recommendations',
                    'devices': recommendations,
                    'message': DEVICE_TEMPLATES['recommendation_intro']
                }
            
        # If no specific device mentioned, return a random response for the category
        if category in CATEGORY_RESPONSES:
            return random.choice(CATEGORY_RESPONSES[category])
        
        # Fallback response
        return FALLBACK_RESPONSES['general_error']
    
    def get_device_recommendations(self, query=None):
        """Generate device recommendations based on the query and available data.
        
        Args:
            query: Optional query string to filter recommendations
        
        Returns:
            List of recommended devices with their details
        """
        try:
            # If no data is available, return empty list
            if self.unified_data.empty:
                logger.warning("No device data available for recommendations")
                return []
            
            # Add debugging
            logger.info(f"Generating recommendations for query: {query}")
            logger.info(f"Data available: {len(self.unified_data)} devices")
            
            # Start with all devices
            device_pool = self.unified_data.copy()
            
            # Default to high-end devices if no specific category is mentioned
            price_category = 'high_end'
            focus_areas = []
            
            # If a specific brand is mentioned, filter for that brand
            brand_focus = None
            for brand in POPULAR_BRANDS:
                if query and brand in query.lower():
                    brand_focus = brand
                    logger.info(f"Filtering recommendations for brand: {brand}")
                    # Create a more flexible pattern to match variations of the brand name
                    pattern = brand.lower()
                    device_pool = device_pool[device_pool['brand_name'].str.lower().str.contains(pattern, na=False)]
                    break
            
            # Extract category and focus areas from query
            if query:
                query_lower = query.lower()
                
                # Determine price category
                for cat, terms in FEATURE_KEYWORDS.items():
                    if cat in ['high_end', 'mid_range', 'budget']:
                        for term in terms:
                            if term in query_lower:
                                price_category = cat
                                logger.info(f"Detected price category: {price_category}")
                                break
                
                # Determine focus areas
                for focus, terms in FEATURE_KEYWORDS.items():
                    if focus not in ['high_end', 'mid_range', 'budget']:
                        for term in terms:
                            if term in query_lower:
                                focus_areas.append(focus)
                                logger.info(f"Detected focus area: {focus}")
                                break
            
            logger.info(f"Selected price category: {price_category}, focus areas: {focus_areas}")
            
            # Prepare recommendations
            recommendations = []
            unique_devices = set()  # To avoid duplicates
            
            # Define popular brands if not already filtered by brand
            popular_brands = ['Samsung', 'Apple', 'Google', 'Xiaomi', 'OnePlus', 'Huawei']
            
            # If we're already focusing on a specific brand, prioritize devices from that brand
            if brand_focus:
                for brand in popular_brands:
                    if brand.lower() == brand_focus:
                        popular_brands = [brand]
                        break
            
            # Prioritize popular brands first
            brand_prioritized = device_pool[device_pool['brand_name'].isin(popular_brands)]
            other_brands = device_pool[~device_pool['brand_name'].isin(popular_brands)]
            
            # Combine with popular brands first
            device_pool = pd.concat([brand_prioritized, other_brands]).drop_duplicates()
            
            # Filter based on price category if possible
            # This is a simplification - in a real implementation, you would need price data
            # or a way to categorize devices by price range
            if price_category == 'high_end':
                # For high-end, assume the most recent devices are high-end
                # In a real implementation, you would filter based on actual price or specs
                filtered_devices = device_pool.head(30)  # Take the first 30 as high-end
            elif price_category == 'mid_range':
                # For mid-range, take devices in the middle of the list
                mid_start = max(0, len(device_pool) // 3)
                mid_end = min(len(device_pool), mid_start + 30)
                filtered_devices = device_pool.iloc[mid_start:mid_end]
            elif price_category == 'budget':
                # For budget, take devices from the end of the list
                # In a real implementation, you would filter based on actual price
                budget_start = max(0, len(device_pool) - 30)
                filtered_devices = device_pool.iloc[budget_start:]
            else:
                # Default to all devices
                filtered_devices = device_pool
            
            logger.info(f"Found {len(filtered_devices)} devices after filtering")
            
            # Collect recommendations (limit to top 5)
            for _, device in filtered_devices.iterrows():
                # Create a unique key for this device
                device_key = f"{device['brand_name']}_{device['device_name']}"
                
                # Skip if we already added this device
                if device_key in unique_devices:
                    continue
                
                # Format the device data
                formatted_device = self._format_device_data(device)
                
                # Find highlight features based on focus areas
                highlights = []
                
                # Check for main features in specifications
                if 'specifications' in formatted_device and formatted_device['specifications']:
                    specs = formatted_device['specifications']
                    
                    # Look for camera information
                    if 'camera' in focus_areas or not focus_areas:
                        if 'main_camera' in specs or 'Main Camera' in specs:
                            camera_info = specs.get('main_camera', specs.get('Main Camera', {}))
                            if isinstance(camera_info, dict) and 'modules' in camera_info:
                                highlights.append(f"Main camera: {camera_info['modules']}")
                            elif isinstance(camera_info, str):
                                highlights.append(f"Main camera: {camera_info}")
                    
                    # Look for battery information
                    if 'battery' in focus_areas or not focus_areas:
                        if 'battery_type' in specs:
                            highlights.append(f"Battery: {specs['battery_type']}")
                        elif 'battery' in specs and isinstance(specs['battery'], dict) and 'type' in specs['battery']:
                            highlights.append(f"Battery: {specs['battery']['type']}")
                    
                    # Look for performance information
                    if 'performance' in focus_areas or not focus_areas:
                        if 'platform' in specs or 'Platform' in specs:
                            platform_info = specs.get('platform', specs.get('Platform', {}))
                            if isinstance(platform_info, dict):
                                chipset = platform_info.get('chipset', '')
                                if chipset:
                                    highlights.append(f"Processor: {chipset}")
                    
                    # Look for display information
                    if 'display' in focus_areas or not focus_areas:
                        if 'display' in specs or 'Display' in specs:
                            display_info = specs.get('display', specs.get('Display', {}))
                            if isinstance(display_info, dict):
                                size = display_info.get('size', '')
                                if size:
                                    highlights.append(f"Display: {size}")
                    
                    # Look for storage information
                    if 'storage' in focus_areas or not focus_areas:
                        if 'memory' in specs or 'Memory' in specs:
                            memory_info = specs.get('memory', specs.get('Memory', {}))
                            if isinstance(memory_info, dict):
                                storage = memory_info.get('internal', '')
                                if storage:
                                    highlights.append(f"Storage: {storage}")
                    
                    # Add other focus areas similarly
                    for focus in focus_areas:
                        if focus not in ['camera', 'battery', 'performance', 'display', 'storage']:
                            for key in specs.keys():
                                if focus.lower() in key.lower():
                                    if isinstance(specs[key], dict):
                                        for subkey, value in specs[key].items():
                                            highlights.append(f"{focus.title()} - {subkey}: {value}")
                                            break
                                    else:
                                        highlights.append(f"{focus.title()}: {specs[key]}")
                                        break
                
                # If we have focus areas but couldn't find matching highlights,
                # add a generic highlight for the device
                if focus_areas and not highlights:
                    highlights.append(f"A great choice for {', '.join(focus_areas)}")
                
                # Add default highlight if none found
                if not highlights:
                    if price_category == 'high_end':
                        highlights.append("Premium flagship device")
                    elif price_category == 'mid_range':
                        highlights.append("Great value mid-range device")
                    elif price_category == 'budget':
                        highlights.append("Affordable device with good features")
                    else:
                        highlights.append(f"Popular {device['brand_name']} device")
                
                # Add highlights to the formatted device
                formatted_device['highlights'] = highlights
                
                # Add to recommendations
                recommendations.append(formatted_device)
                unique_devices.add(device_key)
                
                # Limit to 5 recommendations
                if len(recommendations) >= 5:
                    break
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            if len(recommendations) > 0:
                logger.info(f"First recommendation: {recommendations[0]['brand_name']} {recommendations[0]['device_name']}")
            
            # If no recommendations found, use fallback approach to just get the most recent popular devices
            if not recommendations:
                logger.info("No matching recommendations found, using fallback approach")
                for brand in popular_brands:
                    brand_devices = device_pool[device_pool['brand_name'] == brand]
                    if not brand_devices.empty:
                        device = brand_devices.iloc[0]
                        formatted_device = self._format_device_data(device)
                        formatted_device['highlights'] = [f"Top {brand} device"]
                        recommendations.append(formatted_device)
                        if len(recommendations) >= 5:
                            break
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating device recommendations: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def train_conversation_model(self, user_input, category, response):
        """Train the conversation model with a new example.
        
        This is a simple placeholder implementation.
        """
        logger.info(f"Training conversation model with: category={category}, input={user_input}")
        # In a real implementation, this would update a machine learning model
        return True

    def compare_devices(self, query):
        """
        Extract devices for comparison and their aspects from the query
        
        Args:
            query (str): The user query for comparing devices
            
        Returns:
            dict: Comparison results with devices and compared specifications
        """
        logger.info(f"Processing comparison query: {query}")
        
        # Extract potential device names from the query
        device_names = self._extract_device_names(query)
        
        if len(device_names) < 2:
            logger.info("Not enough devices found for comparison")
            return {
                "success": False,
                "message": "I need at least two devices to compare. Please specify the devices you want to compare."
            }
        
        # Limit to comparing two devices for simplicity
        devices_to_compare = device_names[:2]
        logger.info(f"Devices to compare: {devices_to_compare}")
        
        # Extract specifications to compare
        specs_to_compare = self._extract_specification_requests(query)
        if not specs_to_compare:
            # If no specific specs mentioned, use common comparison points
            specs_to_compare = ["processor", "camera", "display", "battery", "memory"]
        
        logger.info(f"Specifications to compare: {specs_to_compare}")
        
        # Find devices in the database
        device_data = []
        formatted_devices = []
        for device_info in devices_to_compare:
            # Pass a list containing a single device_info to _search_devices_by_name
            devices_df = self._search_devices_by_name([device_info])
            
            if not devices_df.empty:
                device_data.append(devices_df.iloc[0])
                # Format the device data to ensure it's JSON serializable
                formatted_device = self._format_device_data(devices_df.iloc[0])
                formatted_devices.append(formatted_device)
            else:
                device_name = f"{device_info.get('brand', '')} {device_info.get('device', '')}"
                return {
                    "success": False,
                    "message": f"I couldn't find information for {device_name}. Please check the device name."
                }
        
        if len(device_data) < 2 or len(formatted_devices) < 2:
            return {
                "success": False,
                "message": "I couldn't find enough information to compare these devices."
            }
        
        # Create comparison data structure
        comparison_result = {
            "success": True,
            "devices": formatted_devices,
            "compared_specs": {},
            "summary": f"Comparison between {devices_to_compare[0]['brand']} {devices_to_compare[0]['device']} and {devices_to_compare[1]['brand']} {devices_to_compare[1]['device']}"
        }
        
        # Extract and format specs for comparison
        for spec in specs_to_compare:
            comparison_result["compared_specs"][spec] = []
            for i, device in enumerate(device_data):
                spec_value = self._extract_requested_specs(device['specs_dict'], [spec])
                
                # Ensure spec_value is JSON serializable
                formatted_spec_value = {}
                if spec_value and spec in spec_value and isinstance(spec_value[spec], dict):
                    # Convert all values to strings to ensure serializability
                    for key, value in spec_value[spec].items():
                        if isinstance(value, dict):
                            # Handle nested dictionaries
                            nested_values = []
                            for sub_key, sub_value in value.items():
                                nested_values.append(f"{sub_key}: {sub_value}")
                            formatted_spec_value[key] = ", ".join(nested_values)
                        else:
                            formatted_spec_value[key] = str(value)
                elif spec_value:
                    formatted_spec_value = {"value": str(spec_value)}
                
                comparison_result["compared_specs"][spec].append({
                    "device_name": f"{formatted_devices[i]['brand_name']} {formatted_devices[i]['device_name']}",
                    "value": formatted_spec_value if formatted_spec_value else "Not specified"
                })
        
        return comparison_result
