import pandas as pd
import numpy as np
import json
import re
import os
import traceback
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from loguru import logger
from ai_assistant_logger import ai_logger

class DeviceAIAssistant:
    """AI Assistant for mobile device data analysis and NLP-based interactions."""
    
    def __init__(self, device_data_path='brands_devices.csv', specs_data_path='device_specifications.csv'):
        """Initialize the AI assistant with device data.
        
        Args:
            device_data_path: Path to the CSV file containing device basic info
            specs_data_path: Path to the CSV file containing device specifications
        """
        ai_logger.info(f"Initializing DeviceAIAssistant with data paths: {device_data_path}, {specs_data_path}")
        
        self.device_data_path = device_data_path
        self.specs_data_path = specs_data_path
        
        try:
            # Load and process data
            ai_logger.info("Loading and processing device data")
            self.unified_data = self._process_device_data()
            
            # Build search index
            ai_logger.info("Building device search index")
            self.device_index = self._build_device_index()
            
            # Load NLP model
            ai_logger.info("Loading sentence transformer model")
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                ai_logger.info("Loaded sentence transformer model successfully")
                logger.info("Loaded sentence transformer model successfully")
            except Exception as e:
                error_msg = f"Error loading sentence transformer model: {str(e)}"
                ai_logger.error(error_msg)
                ai_logger.error(traceback.format_exc())
                logger.error(error_msg)
                self.model = None
                
            # Define intents
            self.intents = {
                'search': ['show', 'find', 'search', 'look for', 'get', 'display'],
                'compare': ['compare', 'versus', 'vs', 'difference', 'better'],
                'specs': ['specs', 'specifications', 'features', 'what is the', 'how much', 'how many'],
                'recommend': ['recommend', 'suggest', 'best', 'top', 'good']
            }
            
            # Define spec categories for mapping natural language to actual spec fields
            self.spec_categories = {
                'battery': ['battery', 'battery capacity', 'battery life', 'mah'],
                'camera': ['camera', 'rear camera', 'front camera', 'selfie', 'mp', 'megapixel'],
                'display': ['display', 'screen', 'resolution', 'size', 'inch', 'ppi'],
                'processor': ['processor', 'cpu', 'chipset', 'soc'],
                'memory': ['memory', 'ram', 'storage', 'rom', 'gb'],
                'os': ['os', 'operating system', 'android', 'ios'],
                'network': ['network', '5g', '4g', 'lte', 'connectivity'],
                'dimensions': ['dimensions', 'size', 'weight', 'thickness']
            }
            
            # Create embeddings for devices
            ai_logger.info("Creating device embeddings")
            self._create_device_embeddings()
            
            ai_logger.info("DeviceAIAssistant initialization complete")
        except Exception as e:
            ai_logger.critical(f"Failed to initialize DeviceAIAssistant: {str(e)}")
            ai_logger.critical(traceback.format_exc())
            logger.error(f"Failed to initialize DeviceAIAssistant: {str(e)}")
            raise
    
    def _process_device_data(self):
        """Load and process device data from CSV files."""
        ai_logger.log_function_entry("_process_device_data")
        
        try:
            # Load device basic info
            if not os.path.exists(self.device_data_path):
                ai_logger.error(f"Device data file not found: {self.device_data_path}")
                return pd.DataFrame()
                
            devices_df = pd.read_csv(self.device_data_path)
            ai_logger.info(f"Loaded {len(devices_df)} devices from {self.device_data_path}")
            logger.info(f"Loaded {len(devices_df)} devices from {self.device_data_path}")
            
            # Load specifications
            if not os.path.exists(self.specs_data_path):
                ai_logger.error(f"Specs data file not found: {self.specs_data_path}")
                return devices_df
                
            specs_df = pd.read_csv(self.specs_data_path)
            ai_logger.info(f"Loaded {len(specs_df)} device specifications from {self.specs_data_path}")
            logger.info(f"Loaded {len(specs_df)} device specifications from {self.specs_data_path}")
            
            # Join the data on device_url
            unified_data = pd.merge(devices_df, specs_df, on='device_url', how='left')
            ai_logger.info(f"Created unified data with {len(unified_data)} entries")
            logger.info(f"Created unified data with {len(unified_data)} entries")
            
            # Process specifications (convert JSON strings to structured data)
            def parse_specs(specs_str):
                try:
                    if pd.isna(specs_str):
                        return {}
                    return json.loads(specs_str)
                except Exception as e:
                    ai_logger.warning(f"Error parsing specs JSON: {str(e)}")
                    return {}
            
            unified_data['specs_dict'] = unified_data['specifications'].apply(parse_specs)
            ai_logger.info("Successfully processed specifications data")
            
            ai_logger.log_function_exit("_process_device_data", f"DataFrame with {len(unified_data)} rows")
            return unified_data
        except Exception as e:
            ai_logger.error(f"Error processing device data: {str(e)}")
            ai_logger.error(traceback.format_exc())
            logger.error(f"Error processing device data: {str(e)}")
            # Return empty DataFrame with expected columns
            ai_logger.log_function_exit("_process_device_data", "Empty DataFrame (error)")
            return pd.DataFrame(columns=['brand_name', 'device_name', 'device_url', 'device_image', 
                                         'name', 'pictures', 'specifications', 'specs_dict'])
    
    def _build_device_index(self):
        """Build a searchable index for quick device retrieval."""
        ai_logger.log_function_entry("_build_device_index")
        
        try:
            device_index = {}
            
            if self.unified_data.empty:
                ai_logger.warning("Cannot build device index: unified data is empty")
                logger.warning("Cannot build device index: unified data is empty")
                ai_logger.log_function_exit("_build_device_index", "Empty index (no data)")
                return device_index
            
            # Create a lookup index for device names
            for _, row in self.unified_data.iterrows():
                if pd.isna(row['brand_name']) or pd.isna(row['device_name']):
                    continue
                    
                # Index by full name (brand + device)
                device_name = f"{row['brand_name']} {row['device_name']}"
                device_index[device_name.lower()] = row
                
                # Index by device name only
                device_index[row['device_name'].lower()] = row
                
                # Add common variations
                if "galaxy" in device_name.lower():
                    device_index[device_name.lower().replace("galaxy", "").strip()] = row
            
            ai_logger.info(f"Built device index with {len(device_index)} entries")
            logger.info(f"Built device index with {len(device_index)} entries")
            ai_logger.log_function_exit("_build_device_index", f"Index with {len(device_index)} entries")
            return device_index
        except Exception as e:
            ai_logger.error(f"Error building device index: {str(e)}")
            ai_logger.error(traceback.format_exc())
            logger.error(f"Error building device index: {str(e)}")
            ai_logger.log_function_exit("_build_device_index", "Empty index (error)")
            return {}
    
    def _create_device_embeddings(self):
        """Create embeddings for all devices for semantic search."""
        ai_logger.log_function_entry("_create_device_embeddings")
        
        if self.model is None:
            ai_logger.warning("Sentence transformer model not available, skipping embeddings creation")
            logger.warning("Sentence transformer model not available, skipping embeddings creation")
            self.device_embeddings = None
            self.device_texts = None
            self.device_urls = None
            ai_logger.log_function_exit("_create_device_embeddings", "None (no model)")
            return
            
        try:
            # Create text representations for all devices
            device_texts = []
            device_urls = []
            
            for _, row in self.unified_data.iterrows():
                if pd.isna(row['brand_name']) or pd.isna(row['device_name']):
                    continue
                    
                # Create a text representation of the device
                text = f"{row['brand_name']} {row['device_name']}"
                
                # Add some key specifications if available
                if not pd.isna(row['specifications']):
                    try:
                        specs = json.loads(row['specifications'])
                        if isinstance(specs, dict):
                            # Add some key specs to the text representation
                            for key in ['display', 'camera', 'chipset', 'battery']:
                                if key in specs:
                                    text += f" {specs[key]}"
                    except Exception as e:
                        ai_logger.warning(f"Error parsing specs for embedding: {str(e)}")
                
                device_texts.append(text)
                device_urls.append(row['device_url'])
            
            # Create embeddings
            ai_logger.debug(f"Creating embeddings for {len(device_texts)} device texts")
            self.device_embeddings = self.model.encode(device_texts)
            self.device_texts = device_texts
            self.device_urls = device_urls
            
            ai_logger.info(f"Created embeddings for {len(device_texts)} devices")
            logger.info(f"Created embeddings for {len(device_texts)} devices")
            ai_logger.log_function_exit("_create_device_embeddings", f"Embeddings for {len(device_texts)} devices")
        except Exception as e:
            ai_logger.error(f"Error creating device embeddings: {str(e)}")
            ai_logger.error(traceback.format_exc())
            logger.error(f"Error creating device embeddings: {str(e)}")
            self.device_embeddings = None
            self.device_texts = None
            self.device_urls = None
            ai_logger.log_function_exit("_create_device_embeddings", "None (error)")
    
    def process_query(self, query):
        """Process a natural language query and generate a response.
        
        Args:
            query: Natural language query from the user
            
        Returns:
            A dictionary containing the response type and content
        """
        ai_logger.log_function_entry("process_query", query=query)
        
        try:
            # Recognize intent
            intent = self._recognize_intent(query)
            ai_logger.info(f"Recognized intent: {intent}")
            logger.info(f"Recognized intent: {intent}")
            
            # Extract entities
            entities = self._extract_entities(query)
            ai_logger.info(f"Extracted entities: {entities}")
            logger.info(f"Extracted entities: {entities}")
            
            # If we didn't find any device names through basic extraction, try semantic search
            if not entities['device_names'] and self.model is not None:
                ai_logger.info("No device names found with basic extraction, trying semantic search")
                device_names = self._extract_device_names(query)
                entities['device_names'] = device_names
                ai_logger.info(f"Device names from semantic search: {device_names}")
            
            # Process based on intent
            response = None
            if intent == 'search':
                ai_logger.debug("Handling search intent")
                response = self._handle_search_intent(entities)
            elif intent == 'compare':
                ai_logger.debug("Handling compare intent")
                response = self._handle_compare_intent(entities)
            elif intent == 'specs':
                ai_logger.debug("Handling specs intent")
                response = self._handle_specs_intent(entities)
            elif intent == 'recommend':
                ai_logger.debug("Handling recommend intent")
                response = self._handle_recommend_intent(entities)
            else:
                ai_logger.warning(f"Unhandled intent: {intent}")
                response = {
                    "type": "text",
                    "content": "I'm not sure what you're asking for. You can search for devices, compare them, ask about specifications, or get recommendations."
                }
            
            ai_logger.log_function_exit("process_query", f"Response type: {response.get('type', 'unknown')}")
            return response
        except Exception as e:
            ai_logger.error(f"Error processing query: {str(e)}")
            ai_logger.error(traceback.format_exc())
            logger.error(f"Error processing query: {str(e)}")
            
            error_response = {
                "type": "text",
                "content": f"Sorry, I encountered an error while processing your request: {str(e)}"
            }
            ai_logger.log_function_exit("process_query", "Error response")
            return error_response
    
    def _recognize_intent(self, query):
        """Recognize the intent of the user query.
        
        Args:
            query: Natural language query from the user
            
        Returns:
            Intent string: 'search', 'compare', 'specs', or 'recommend'
        """
        ai_logger.log_function_entry("_recognize_intent", query=query)
        
        query = query.lower()
        intent = 'search'  # Default intent
        
        # Check for compare intent (highest priority)
        for keyword in self.intents['compare']:
            if keyword in query:
                ai_logger.debug(f"Compare intent detected with keyword: '{keyword}'")
                intent = 'compare'
                break
        
        # If not compare, check for specs intent
        if intent == 'search':
            for keyword in self.intents['specs']:
                if keyword in query:
                    # Check if a specific spec is mentioned
                    for spec_category in self.spec_categories:
                        for spec_keyword in self.spec_categories[spec_category]:
                            if spec_keyword in query:
                                ai_logger.debug(f"Specs intent detected with keywords: '{keyword}', '{spec_keyword}'")
                                intent = 'specs'
                                break
                        if intent == 'specs':
                            break
                if intent == 'specs':
                    break
        
        # If not compare or specs, check for recommend intent
        if intent == 'search':
            for keyword in self.intents['recommend']:
                if keyword in query:
                    ai_logger.debug(f"Recommend intent detected with keyword: '{keyword}'")
                    intent = 'recommend'
                    break
        
        # If no other intent detected, it's a search intent
        if intent == 'search':
            ai_logger.debug("No specific intent detected, defaulting to search intent")
        
        ai_logger.log_function_exit("_recognize_intent", intent)
        return intent
    
    def _extract_entities(self, query):
        """Extract entities from the user query.
        
        Args:
            query: Natural language query from the user
            
        Returns:
            Dictionary of extracted entities
        """
        ai_logger.log_function_entry("_extract_entities", query=query)
        
        query = query.lower()
        entities = {
            'device_names': [],
            'spec_category': None
        }
        
        # Extract device names (basic approach, will be enhanced by semantic search)
        device_names = []
        
        # Check for device names in our index
        if self.device_index:
            ai_logger.debug(f"Searching for device names in index with {len(self.device_index)} entries")
            matched_devices = []
            
            for device_name in self.device_index.keys():
                if device_name in query:
                    device_names.append(device_name)
                    matched_devices.append(device_name)
            
            if matched_devices:
                ai_logger.debug(f"Found device names in query: {matched_devices}")
            else:
                ai_logger.debug("No exact device names found in query")
        else:
            ai_logger.warning("Device index is empty, cannot extract device names")
        
        entities['device_names'] = device_names
        
        # Extract specification categories
        spec_categories = []
        for category, keywords in self.spec_categories.items():
            matched_keywords = []
            for keyword in keywords:
                if keyword in query:
                    spec_categories.append(category)
                    matched_keywords.append(keyword)
                    break
            
            if matched_keywords:
                ai_logger.debug(f"Category '{category}' matched keywords: {matched_keywords}")
        
        entities['spec_category'] = list(set(spec_categories))[0] if spec_categories else None
        ai_logger.debug(f"Extracted spec categories: {entities['spec_category']}")
        
        ai_logger.log_function_exit("_extract_entities", entities)
        return entities
    
    def _extract_device_names(self, query):
        """Extract device names from the query using semantic search.
        
        Args:
            query: Natural language query from the user
            
        Returns:
            List of extracted device names
        """
        ai_logger.log_function_entry("_extract_device_names", query=query)
        
        # First try exact matches from the device index
        exact_matches = []
        if self.device_index:
            for device_name in self.device_index.keys():
                if device_name in query.lower():
                    exact_matches.append(device_name)
            
            if exact_matches:
                ai_logger.debug(f"Found exact device name matches: {exact_matches}")
                ai_logger.log_function_exit("_extract_device_names", exact_matches)
                return exact_matches
            else:
                ai_logger.debug("No exact device name matches found")
        else:
            ai_logger.warning("Device index is empty, cannot find exact matches")
        
        # If no exact matches, try semantic search
        if self.model is not None and self.device_embeddings is not None:
            ai_logger.debug("Attempting semantic search for device names")
            try:
                # Encode the query
                query_embedding = self.model.encode([query])
                
                # Calculate similarity with all device embeddings
                similarities = cosine_similarity(query_embedding, self.device_embeddings)[0]
                
                # Get the top 2 matches
                top_indices = similarities.argsort()[-2:][::-1]
                
                # Only consider matches with similarity above threshold
                threshold = 0.5
                device_names = []
                for idx in top_indices:
                    similarity = similarities[idx]
                    if similarity > threshold:
                        device_name = self.device_texts[idx]
                        device_names.append(device_name)
                        ai_logger.debug(f"Semantic match: '{device_name}' with similarity {similarity:.4f}")
                
                if device_names:
                    ai_logger.debug(f"Found {len(device_names)} semantic matches above threshold {threshold}")
                    ai_logger.log_function_exit("_extract_device_names", device_names)
                    return device_names
                else:
                    ai_logger.debug(f"No semantic matches above threshold {threshold}")
            except Exception as e:
                ai_logger.error(f"Error during semantic search: {str(e)}")
                ai_logger.error(traceback.format_exc())
        else:
            ai_logger.debug("Semantic search not available (model or embeddings missing)")
        
        # Fallback to simple keyword extraction
        ai_logger.debug("Falling back to n-gram keyword extraction")
        words = re.findall(r'\b\w+\b', query.lower())
        potential_devices = []
        
        for i in range(len(words)):
            for j in range(i+1, min(i+5, len(words)+1)):
                potential_device = ' '.join(words[i:j])
                if self.device_index and potential_device in self.device_index:
                    potential_devices.append(potential_device)
                    ai_logger.debug(f"Found n-gram match: '{potential_device}'")
        
        ai_logger.log_function_exit("_extract_device_names", potential_devices)
        return potential_devices
    
    def _get_device_data(self, device_name):
        """Get device data from the unified data.
        
        Args:
            device_name: Name of the device
            
        Returns:
            DataFrame row with device data or None if not found
        """
        ai_logger.log_function_entry("_get_device_data", device_name=device_name)
        
        if not device_name:
            ai_logger.warning("Empty device name provided")
            ai_logger.log_function_exit("_get_device_data", None)
            return None
            
        device_name = device_name.lower()
        
        # Check if the device name is in our index
        if self.device_index and device_name in self.device_index:
            ai_logger.debug(f"Found exact match for device: '{device_name}'")
            ai_logger.log_function_exit("_get_device_data", "Found exact match")
            return self.device_index[device_name]
        
        # Try to find a partial match
        if self.device_index:
            ai_logger.debug(f"Searching for partial match for: '{device_name}'")
            best_match = None
            best_match_name = None
            
            for name in self.device_index.keys():
                if device_name in name or name in device_name:
                    best_match = self.device_index[name]
                    best_match_name = name
                    ai_logger.debug(f"Found partial match: '{name}'")
                    break
            
            if best_match is not None:
                ai_logger.debug(f"Using partial match: '{best_match_name}'")
                ai_logger.log_function_exit("_get_device_data", "Found partial match")
                return best_match
        
        # Try semantic search if available
        if self.model is not None and self.device_embeddings is not None and self.device_urls is not None:
            ai_logger.debug("Attempting semantic search for device data")
            try:
                query_embedding = self.model.encode([device_name])
                similarities = cosine_similarity(query_embedding, self.device_embeddings)[0]
                top_idx = similarities.argmax()
                
                if similarities[top_idx] > 0.7:  # Higher threshold for confidence
                    device_url = self.device_urls[top_idx]
                    device_data = self.unified_data[self.unified_data['device_url'] == device_url]
                    if not device_data.empty:
                        ai_logger.debug(f"Found device via semantic search: similarity={similarities[top_idx]:.4f}")
                        ai_logger.log_function_exit("_get_device_data", "Found via semantic search")
                        return device_data.iloc[0]
                else:
                    ai_logger.debug(f"Best semantic match has low similarity: {similarities[top_idx]:.4f}")
            except Exception as e:
                ai_logger.error(f"Error during semantic search for device data: {str(e)}")
                ai_logger.error(traceback.format_exc())
        
        ai_logger.warning(f"No device data found for: '{device_name}'")
        ai_logger.log_function_exit("_get_device_data", None)
        return None
    
    def _handle_search_intent(self, entities):
        """Handle search intent.
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Response dictionary
        """
        ai_logger.log_function_entry("_handle_search_intent", entities=entities)
        
        if not entities['device_names']:
            response = {
                "type": "text",
                "content": "I couldn't identify which device you're looking for. Please specify a device name."
            }
            ai_logger.log_function_exit("_handle_search_intent", "No device names found")
            return response
        
        device_name = entities['device_names'][0]
        ai_logger.debug(f"Searching for device: '{device_name}'")
        device_data = self._get_device_data(device_name)
        
        if device_data is None:
            response = {
                "type": "text",
                "content": f"I couldn't find any information about {device_name}. Please check the device name and try again."
            }
            ai_logger.log_function_exit("_handle_search_intent", "Device not found")
            return response
        
        # Format the device data for display
        formatted_device = self._format_device_data(device_data)
        
        response = {
            "type": "device_details",
            "summary": f"Here's the information about {formatted_device['name']}:",
            "device": formatted_device
        }
        
        ai_logger.log_function_exit("_handle_search_intent", "Success")
        return response
    
    def _handle_compare_intent(self, entities):
        """Handle compare intent.
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Response dictionary
        """
        ai_logger.log_function_entry("_handle_compare_intent", entities=entities)
        
        if len(entities['device_names']) < 2:
            response = {
                "type": "text",
                "content": "To compare devices, please specify at least two device names."
            }
            ai_logger.log_function_exit("_handle_compare_intent", "Not enough devices")
            return response
        
        # Get data for the first two devices
        device_name1 = entities['device_names'][0]
        device_name2 = entities['device_names'][1]
        
        ai_logger.debug(f"Comparing devices: '{device_name1}' and '{device_name2}'")
        
        device_data1 = self._get_device_data(device_name1)
        device_data2 = self._get_device_data(device_name2)
        
        if device_data1 is None:
            response = {
                "type": "text",
                "content": f"I couldn't find any information about {device_name1}. Please check the device name and try again."
            }
            ai_logger.log_function_exit("_handle_compare_intent", f"Device not found: {device_name1}")
            return response
        
        if device_data2 is None:
            response = {
                "type": "text",
                "content": f"I couldn't find any information about {device_name2}. Please check the device name and try again."
            }
            ai_logger.log_function_exit("_handle_compare_intent", f"Device not found: {device_name2}")
            return response
        
        # Format the device data for comparison
        formatted_device1 = self._format_device_data(device_data1)
        formatted_device2 = self._format_device_data(device_data2)
        
        # Generate comparison summary
        comparison_summary = self._generate_comparison_summary(formatted_device1, formatted_device2)
        
        response = {
            "type": "comparison",
            "summary": f"Here's a comparison between {formatted_device1['name']} and {formatted_device2['name']}:",
            "comparison_text": comparison_summary,
            "devices": [formatted_device1, formatted_device2]
        }
        
        ai_logger.log_function_exit("_handle_compare_intent", "Success")
        return response
    
    def _handle_specs_intent(self, entities):
        """Handle specs intent.
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Response dictionary
        """
        ai_logger.log_function_entry("_handle_specs_intent", entities=entities)
        
        if not entities['device_names']:
            response = {
                "type": "text",
                "content": "I couldn't identify which device you're asking about. Please specify a device name."
            }
            ai_logger.log_function_exit("_handle_specs_intent", "No device names found")
            return response
        
        device_name = entities['device_names'][0]
        ai_logger.debug(f"Getting specs for device: '{device_name}'")
        device_data = self._get_device_data(device_name)
        
        if device_data is None:
            response = {
                "type": "text",
                "content": f"I couldn't find any information about {device_name}. Please check the device name and try again."
            }
            ai_logger.log_function_exit("_handle_specs_intent", "Device not found")
            return response
        
        # Format the device data
        formatted_device = self._format_device_data(device_data)
        
        # If a specific spec category was requested
        if entities['spec_category']:
            category = entities['spec_category']
            ai_logger.debug(f"Looking for specific spec category: '{category}'")
            spec_value = self._get_spec_value(formatted_device, category)
            
            if spec_value:
                response = {
                    "type": "spec_details",
                    "summary": f"The {category} of {formatted_device['name']} is:",
                    "spec_category": category,
                    "spec_value": spec_value,
                    "device": formatted_device
                }
                ai_logger.log_function_exit("_handle_specs_intent", f"Found spec: {category}")
                return response
            else:
                response = {
                    "type": "text",
                    "content": f"I couldn't find information about the {category} of {formatted_device['name']}."
                }
                ai_logger.log_function_exit("_handle_specs_intent", f"Spec not found: {category}")
                return response
        
        # If no specific category, return all specs
        response = {
            "type": "device_details",
            "summary": f"Here are the specifications of {formatted_device['name']}:",
            "device": formatted_device
        }
        
        ai_logger.log_function_exit("_handle_specs_intent", "Success - all specs")
        return response
    
    def _handle_recommend_intent(self, entities):
        """Handle recommend intent.
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Response dictionary
        """
        ai_logger.log_function_entry("_handle_recommend_intent", entities=entities)
        
        # For now, just return a simple recommendation based on the latest devices
        try:
            latest_devices = self.unified_data.sort_values('device_url', ascending=False).head(5)
            
            if latest_devices.empty:
                response = {
                    "type": "text",
                    "content": "I don't have enough data to make recommendations at the moment."
                }
                ai_logger.log_function_exit("_handle_recommend_intent", "No data available")
                return response
            
            # Format the latest devices
            formatted_devices = []
            for _, device in latest_devices.iterrows():
                formatted_devices.append(self._format_device_data(device))
            
            response = {
                "type": "recommendation",
                "summary": "Here are some of the latest devices I can recommend:",
                "devices": formatted_devices
            }
            
            ai_logger.log_function_exit("_handle_recommend_intent", f"Success - {len(formatted_devices)} recommendations")
            return response
        except Exception as e:
            ai_logger.error(f"Error generating recommendations: {str(e)}")
            ai_logger.error(traceback.format_exc())
            
            response = {
                "type": "text",
                "content": "I encountered an error while generating recommendations. Please try again later."
            }
            ai_logger.log_function_exit("_handle_recommend_intent", "Error")
            return response
    
    def _format_device_data(self, device_data):
        """Format device data for display.
        
        Args:
            device_data: DataFrame row with device data
            
        Returns:
            Dictionary with formatted device data
        """
        ai_logger.log_function_entry("_format_device_data", device_name=f"{device_data['brand_name']} {device_data['device_name']}")
        
        try:
            formatted_device = {
                "name": f"{device_data['brand_name']} {device_data['device_name']}",
                "brand": device_data['brand_name'],
                "model": device_data['device_name'],
                "url": device_data['device_url'],
                "image_url": device_data['device_image'],
                "specifications": {}
            }
            
            # Add pictures if available
            if not pd.isna(device_data['pictures']):
                try:
                    formatted_device["pictures"] = json.loads(device_data['pictures'])
                    ai_logger.debug(f"Added {len(formatted_device['pictures'])} pictures")
                except Exception as e:
                    ai_logger.warning(f"Error parsing pictures JSON: {str(e)}")
                    formatted_device["pictures"] = []
            else:
                formatted_device["pictures"] = []
            
            # Add specifications if available
            if not pd.isna(device_data['specifications']):
                try:
                    specs = json.loads(device_data['specifications'])
                    formatted_device["specifications"] = specs
                    ai_logger.debug(f"Added {len(specs)} specification entries")
                except Exception as e:
                    ai_logger.warning(f"Error parsing specifications JSON: {str(e)}")
            
            ai_logger.log_function_exit("_format_device_data", "Success")
            return formatted_device
        except Exception as e:
            ai_logger.error(f"Error formatting device data: {str(e)}")
            ai_logger.error(traceback.format_exc())
            ai_logger.log_function_exit("_format_device_data", "Error")
            # Return minimal formatted device to avoid errors
            return {
                "name": "Unknown Device",
                "specifications": {},
                "pictures": []
            }
    
    def _get_spec_value(self, formatted_device, category):
        """Get the value of a specific specification category.
        
        Args:
            formatted_device: Dictionary with formatted device data
            category: Specification category
            
        Returns:
            String with the specification value or None if not found
        """
        ai_logger.log_function_entry("_get_spec_value", device=formatted_device['name'], category=category)
        
        specs = formatted_device["specifications"]
        
        # Map category to actual keys in the specifications
        category_keys = {
            'battery': ['battery', 'battery_c', 'batlife'],
            'camera': ['camera', 'cam', 'cam1', 'cam2', 'selfiecam'],
            'display': ['display', 'displaytype', 'displaysize', 'displayres'],
            'processor': ['chipset', 'cpu', 'gpu'],
            'memory': ['memory', 'ram', 'storage'],
            'os': ['os', 'platform'],
            'network': ['network', 'sim', '2g', '3g', '4g', '5g'],
            'dimensions': ['dimensions', 'weight']
        }
        
        # Check if any of the keys for the category exist in the specs
        if category in category_keys:
            for key in category_keys[category]:
                if key in specs:
                    value = specs[key]
                    ai_logger.debug(f"Found spec value for key '{key}': {value}")
                    ai_logger.log_function_exit("_get_spec_value", f"Found: {key}")
                    return value
        
        # Direct lookup
        if category in specs:
            value = specs[category]
            ai_logger.debug(f"Found spec value for direct category '{category}': {value}")
            ai_logger.log_function_exit("_get_spec_value", "Found direct")
            return value
        
        ai_logger.debug(f"No spec value found for category '{category}'")
        ai_logger.log_function_exit("_get_spec_value", None)
        return None
    
    def _generate_comparison_summary(self, device1, device2):
        """Generate a text summary comparing two devices.
        
        Args:
            device1: Dictionary with formatted device data for first device
            device2: Dictionary with formatted device data for second device
            
        Returns:
            String with comparison summary
        """
        ai_logger.log_function_entry("_generate_comparison_summary", device1=device1['name'], device2=device2['name'])
        
        summary = []
        
        # Compare key specifications
        specs_to_compare = [
            ('display', 'Display'),
            ('camera', 'Camera'),
            ('chipset', 'Processor'),
            ('battery', 'Battery'),
            ('memory', 'Memory'),
            ('os', 'Operating System')
        ]
        
        for spec_key, spec_name in specs_to_compare:
            spec1 = self._get_spec_value(device1, spec_key)
            spec2 = self._get_spec_value(device2, spec_key)
            
            if spec1 and spec2:
                summary.append(f"{spec_name}: {device1['name']} has {spec1}, while {device2['name']} has {spec2}.")
                ai_logger.debug(f"Added comparison for {spec_name}")
        
        if not summary:
            message = f"I don't have enough detailed information to compare {device1['name']} and {device2['name']}."
            summary.append(message)
            ai_logger.debug("No comparable specifications found")
        
        result = "\n".join(summary)
        ai_logger.log_function_exit("_generate_comparison_summary", f"{len(summary)} comparison points")
        return result
