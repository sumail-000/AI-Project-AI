import pandas as pd
import numpy as np
import json
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from loguru import logger

class DeviceAIAssistant:
    """AI Assistant for mobile device data analysis and NLP-based interactions."""
    
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
        
        # Build search index
        self.device_index = self._build_device_index()
        
        # Load NLP model
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence transformer model successfully")
        except Exception as e:
            logger.error(f"Error loading sentence transformer model: {str(e)}")
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
        self._create_device_embeddings()
    
    def _process_device_data(self):
        """Load and process device data from CSV files."""
        try:
            # Load device basic info
            devices_df = pd.read_csv(self.device_data_path)
            logger.info(f"Loaded {len(devices_df)} devices from {self.device_data_path}")
            
            # Load specifications
            specs_df = pd.read_csv(self.specs_data_path)
            logger.info(f"Loaded {len(specs_df)} device specifications from {self.specs_data_path}")
            
            # Join the data on device_url
            unified_data = pd.merge(devices_df, specs_df, on='device_url', how='left')
            logger.info(f"Created unified data with {len(unified_data)} entries")
            
            # Process specifications (convert JSON strings to structured data)
            def parse_specs(specs_str):
                try:
                    if pd.isna(specs_str):
                        return {}
                    return json.loads(specs_str)
                except:
                    return {}
            
            unified_data['specs_dict'] = unified_data['specifications'].apply(parse_specs)
            
            return unified_data
        except Exception as e:
            logger.error(f"Error processing device data: {str(e)}")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['brand_name', 'device_name', 'device_url', 'device_image', 
                                         'name', 'pictures', 'specifications', 'specs_dict'])
    
    def _build_device_index(self):
        """Build a searchable index for quick device retrieval."""
        device_index = {}
        
        for _, row in self.unified_data.iterrows():
            # Skip rows with missing data
            if pd.isna(row['brand_name']) or pd.isna(row['device_name']):
                continue
                
            # Index by full name (brand + device)
            device_name = f"{row['brand_name']} {row['device_name']}"
            device_index[device_name.lower()] = row['device_url']
            
            # Index by device name only
            device_index[row['device_name'].lower()] = row['device_url']
            
            # Add common variations
            if "galaxy" in device_name.lower():
                device_index[device_name.lower().replace("galaxy", "").strip()] = row['device_url']
            
        logger.info(f"Built device index with {len(device_index)} entries")
        return device_index
    
    def _create_device_embeddings(self):
        """Create embeddings for all devices for semantic search."""
        if self.model is None:
            logger.warning("Sentence transformer model not available, skipping embeddings creation")
            self.device_embeddings = None
            self.device_texts = None
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
                    except:
                        pass
                
                device_texts.append(text)
                device_urls.append(row['device_url'])
            
            # Create embeddings
            self.device_embeddings = self.model.encode(device_texts)
            self.device_texts = device_texts
            self.device_urls = device_urls
            
            logger.info(f"Created embeddings for {len(device_texts)} devices")
        except Exception as e:
            logger.error(f"Error creating device embeddings: {str(e)}")
            self.device_embeddings = None
            self.device_texts = None
    
    def process_query(self, query):
        """Process a natural language query and generate a response.
        
        Args:
            query: Natural language query from the user
            
        Returns:
            A dictionary containing the response type and content
        """
        try:
            # Recognize intent
            intent = self._recognize_intent(query)
            logger.info(f"Recognized intent: {intent}")
            
            # Extract entities
            entities = self._extract_entities(query)
            logger.info(f"Extracted entities: {entities}")
            
            # Process based on intent
            if intent == 'search':
                return self._handle_search_intent(entities)
            elif intent == 'compare':
                return self._handle_compare_intent(entities)
            elif intent == 'specs':
                return self._handle_specs_intent(entities)
            elif intent == 'recommend':
                return self._handle_recommend_intent(entities)
            else:
                return {
                    "type": "text",
                    "content": "I'm not sure what you're asking for. You can search for devices, compare them, ask about specifications, or get recommendations."
                }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "type": "text",
                "content": "Sorry, I encountered an error while processing your request. Please try again."
            }
    
    def _recognize_intent(self, query):
        """Recognize the intent of the user query.
        
        Args:
            query: Natural language query from the user
            
        Returns:
            Intent string: 'search', 'compare', 'specs', or 'recommend'
        """
        query = query.lower()
        
        # Check for compare intent (highest priority)
        for keyword in self.intents['compare']:
            if keyword in query:
                return 'compare'
        
        # Check for specs intent
        for keyword in self.intents['specs']:
            if keyword in query:
                # Check if a specific spec is mentioned
                for spec_category in self.spec_categories:
                    for spec_keyword in self.spec_categories[spec_category]:
                        if spec_keyword in query:
                            return 'specs'
        
        # Check for recommend intent
        for keyword in self.intents['recommend']:
            if keyword in query:
                return 'recommend'
        
        # Default to search intent
        return 'search'
    
    def _extract_entities(self, query):
        """Extract entities from the user query.
        
        Args:
            query: Natural language query from the user
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {
            'device_names': [],
            'spec_category': None
        }
        
        # Extract device names
        device_names = self._extract_device_names(query)
        entities['device_names'] = device_names
        
        # Extract spec category
        for category, keywords in self.spec_categories.items():
            for keyword in keywords:
                if keyword in query.lower():
                    entities['spec_category'] = category
                    break
            if entities['spec_category']:
                break
        
        return entities
    
    def _extract_device_names(self, query):
        """Extract device names from the query using semantic search.
        
        Args:
            query: Natural language query from the user
            
        Returns:
            List of extracted device names
        """
        # First try exact matches from the device index
        exact_matches = []
        for device_name in self.device_index.keys():
            if device_name in query.lower():
                exact_matches.append(device_name)
        
        if exact_matches:
            return exact_matches
        
        # If no exact matches, try semantic search
        if self.model is not None and self.device_embeddings is not None:
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
                if similarities[idx] > threshold:
                    device_names.append(self.device_texts[idx])
            
            return device_names
        
        # Fallback to simple keyword extraction
        words = re.findall(r'\b\w+\b', query.lower())
        potential_devices = []
        
        for i in range(len(words)):
            for j in range(i+1, min(i+5, len(words)+1)):
                potential_device = ' '.join(words[i:j])
                if potential_device in self.device_index:
                    potential_devices.append(potential_device)
        
        return potential_devices
    
    def _get_device_data(self, device_name):
        """Get device data from the unified data.
        
        Args:
            device_name: Name of the device
            
        Returns:
            DataFrame row with device data or None if not found
        """
        device_name = device_name.lower()
        
        # Check if device is in the index
        if device_name in self.device_index:
            device_url = self.device_index[device_name]
            device_data = self.unified_data[self.unified_data['device_url'] == device_url]
            if not device_data.empty:
                return device_data.iloc[0]
        
        # Try semantic search
        if self.model is not None and self.device_embeddings is not None:
            query_embedding = self.model.encode([device_name])
            similarities = cosine_similarity(query_embedding, self.device_embeddings)[0]
            top_idx = similarities.argmax()
            
            if similarities[top_idx] > 0.7:  # Higher threshold for confidence
                device_url = self.device_urls[top_idx]
                device_data = self.unified_data[self.unified_data['device_url'] == device_url]
                if not device_data.empty:
                    return device_data.iloc[0]
        
        return None
    
    def _handle_search_intent(self, entities):
        """Handle search intent.
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Response dictionary
        """
        if not entities['device_names']:
            return {
                "type": "text",
                "content": "I couldn't identify which device you're looking for. Please specify a device name."
            }
        
        device_name = entities['device_names'][0]
        device_data = self._get_device_data(device_name)
        
        if device_data is None:
            return {
                "type": "text",
                "content": f"I couldn't find any information about {device_name}. Please check the device name and try again."
            }
        
        # Format the device data for display
        formatted_device = self._format_device_data(device_data)
        
        return {
            "type": "device_details",
            "summary": f"Here's the information about {formatted_device['name']}:",
            "device": formatted_device
        }
    
    def _handle_compare_intent(self, entities):
        """Handle compare intent.
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Response dictionary
        """
        if len(entities['device_names']) < 2:
            return {
                "type": "text",
                "content": "To compare devices, please specify at least two device names."
            }
        
        # Get data for the first two devices
        device_name1 = entities['device_names'][0]
        device_name2 = entities['device_names'][1]
        
        device_data1 = self._get_device_data(device_name1)
        device_data2 = self._get_device_data(device_name2)
        
        if device_data1 is None:
            return {
                "type": "text",
                "content": f"I couldn't find any information about {device_name1}. Please check the device name and try again."
            }
        
        if device_data2 is None:
            return {
                "type": "text",
                "content": f"I couldn't find any information about {device_name2}. Please check the device name and try again."
            }
        
        # Format the device data for comparison
        formatted_device1 = self._format_device_data(device_data1)
        formatted_device2 = self._format_device_data(device_data2)
        
        # Generate comparison summary
        comparison_summary = self._generate_comparison_summary(formatted_device1, formatted_device2)
        
        return {
            "type": "comparison",
            "summary": f"Here's a comparison between {formatted_device1['name']} and {formatted_device2['name']}:",
            "comparison_text": comparison_summary,
            "devices": [formatted_device1, formatted_device2]
        }
    
    def _handle_specs_intent(self, entities):
        """Handle specs intent.
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Response dictionary
        """
        if not entities['device_names']:
            return {
                "type": "text",
                "content": "I couldn't identify which device you're asking about. Please specify a device name."
            }
        
        device_name = entities['device_names'][0]
        device_data = self._get_device_data(device_name)
        
        if device_data is None:
            return {
                "type": "text",
                "content": f"I couldn't find any information about {device_name}. Please check the device name and try again."
            }
        
        # Format the device data
        formatted_device = self._format_device_data(device_data)
        
        # If a specific spec category was requested
        if entities['spec_category']:
            category = entities['spec_category']
            spec_value = self._get_spec_value(formatted_device, category)
            
            if spec_value:
                return {
                    "type": "spec_details",
                    "summary": f"The {category} of {formatted_device['name']} is:",
                    "spec_category": category,
                    "spec_value": spec_value,
                    "device": formatted_device
                }
            else:
                return {
                    "type": "text",
                    "content": f"I couldn't find information about the {category} of {formatted_device['name']}."
                }
        
        # If no specific category, return all specs
        return {
            "type": "device_details",
            "summary": f"Here are the specifications of {formatted_device['name']}:",
            "device": formatted_device
        }
    
    def _handle_recommend_intent(self, entities):
        """Handle recommend intent.
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Response dictionary
        """
        # For now, just return a simple recommendation based on the latest devices
        latest_devices = self.unified_data.sort_values('device_url', ascending=False).head(5)
        
        if latest_devices.empty:
            return {
                "type": "text",
                "content": "I don't have enough data to make recommendations at the moment."
            }
        
        # Format the latest devices
        formatted_devices = []
        for _, device in latest_devices.iterrows():
            formatted_devices.append(self._format_device_data(device))
        
        return {
            "type": "recommendation",
            "summary": "Here are some of the latest devices I can recommend:",
            "devices": formatted_devices
        }
    
    def _format_device_data(self, device_data):
        """Format device data for display.
        
        Args:
            device_data: DataFrame row with device data
            
        Returns:
            Dictionary with formatted device data
        """
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
            except:
                formatted_device["pictures"] = []
        else:
            formatted_device["pictures"] = []
        
        # Add specifications if available
        if not pd.isna(device_data['specifications']):
            try:
                specs = json.loads(device_data['specifications'])
                formatted_device["specifications"] = specs
            except:
                pass
        
        return formatted_device
    
    def _get_spec_value(self, formatted_device, category):
        """Get the value of a specific specification category.
        
        Args:
            formatted_device: Dictionary with formatted device data
            category: Specification category
            
        Returns:
            String with the specification value or None if not found
        """
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
                    return specs[key]
        
        # Direct lookup
        if category in specs:
            return specs[category]
        
        return None
    
    def _generate_comparison_summary(self, device1, device2):
        """Generate a text summary comparing two devices.
        
        Args:
            device1: Dictionary with formatted device data for first device
            device2: Dictionary with formatted device data for second device
            
        Returns:
            String with comparison summary
        """
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
        
        if not summary:
            summary.append(f"I don't have enough detailed information to compare {device1['name']} and {device2['name']}.")
        
        return "\n".join(summary)
