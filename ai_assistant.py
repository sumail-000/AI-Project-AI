import pandas as pd
import numpy as np
import json
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from loguru import logger

# Import the conversation model
try:
    from conversation_model import ConversationModel
    logger.info("Loaded conversation model module")
except ImportError as e:
    logger.error(f"Error importing conversation model: {str(e)}")
    ConversationModel = None

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
            
        # Initialize conversation model
        try:
            if ConversationModel is not None:
                self.conversation_model = ConversationModel()
                logger.info("Initialized conversation model")
            else:
                self.conversation_model = None
                logger.warning("Conversation model not available")
        except Exception as e:
            logger.error(f"Error initializing conversation model: {str(e)}")
            self.conversation_model = None
            
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
            
            # Rename columns to match expected format
            devices_df = devices_df.rename(columns={
                'brand': 'brand_name',
                'image_url': 'device_image'
            })
            
            # Load specifications
            specs_df = pd.read_csv(self.specs_data_path)
            logger.info(f"Loaded {len(specs_df)} device specifications from {self.specs_data_path}")
            
            # Rename columns to match expected format
            specs_df = specs_df.rename(columns={
                'device_name': 'name',
                'device_pictures': 'pictures',
                'device_data': 'specifications'
            })
            
            # Join the data on device_url
            unified_data = pd.merge(devices_df, specs_df, on='device_url', how='left')
            logger.info(f"Created unified data with {len(unified_data)} entries")
            
            # Process specifications (convert JSON strings to structured data)
            def parse_specs(specs_str):
                try:
                    if pd.isna(specs_str):
                        return {}
                    return json.loads(specs_str)
                except Exception as e:
                    logger.warning(f"Error parsing specs JSON: {str(e)}")
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
            try:
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
                
                # Add brand-specific variations
                if "google" in device_name.lower() and "pixel" in device_name.lower():
                    # Index as just "pixel X" for Google Pixel devices
                    pixel_name = re.search(r'pixel\s+([\w\d]+)', device_name.lower())
                    if pixel_name:
                        device_index[f"pixel {pixel_name.group(1)}"] = row['device_url']
                
                if "iphone" in device_name.lower():
                    # Index as just "iphone X" for Apple iPhone devices
                    iphone_name = re.search(r'iphone\s+([\w\d]+)', device_name.lower())
                    if iphone_name:
                        device_index[f"iphone {iphone_name.group(1)}"] = row['device_url']
            except Exception as e:
                logger.warning(f"Error indexing device {row.get('device_name', 'unknown')}: {str(e)}")
                continue
            
        logger.info(f"Built device index with {len(device_index)} entries")
        return device_index
    
    def _create_device_embeddings(self):
        """Create embeddings for all devices for semantic search."""
        if self.model is None:
            logger.warning("Sentence transformer model not available, skipping embeddings creation")
            self.device_embeddings = None
            self.device_texts = None
            self.device_urls = None
            return
            
        try:
            # Create text representations for all devices
            device_texts = []
            device_urls = []
            
            for _, row in self.unified_data.iterrows():
                try:
                    if pd.isna(row['brand_name']) or pd.isna(row['device_name']):
                        continue
                        
                    # Create a text representation of the device
                    text = f"{row['brand_name']} {row['device_name']}"
                    
                    # Add some key specifications if available
                    if 'specs_dict' in row and isinstance(row['specs_dict'], dict) and row['specs_dict']:
                        specs = row['specs_dict']
                        # Add some key specs to the text representation
                        for key in ['display', 'camera', 'chipset', 'battery', 'cpu', 'memory', 'ram']:
                            if key in specs and specs[key]:
                                text += f" {specs[key]}"
                    
                    device_texts.append(text)
                    device_urls.append(row['device_url'])
                except Exception as e:
                    logger.warning(f"Error processing device for embeddings: {str(e)}")
                    continue
            
            # Only create embeddings if we have devices
            if device_texts:
                # Create embeddings
                self.device_embeddings = self.model.encode(device_texts)
                self.device_texts = device_texts
                self.device_urls = device_urls
                
                logger.info(f"Created embeddings for {len(device_texts)} devices")
            else:
                logger.warning("No valid devices found for creating embeddings")
                self.device_embeddings = None
                self.device_texts = None
                self.device_urls = None
        except Exception as e:
            logger.error(f"Error creating device embeddings: {str(e)}")
            self.device_embeddings = None
            self.device_texts = None
            self.device_urls = None
    
    def process_query(self, query):
        """Process a natural language query and generate a response.
        
        Args:
            query: Natural language query from the user
            
        Returns:
            A dictionary containing the response type and content
        """
        try:
            # Initialize conversation category storage if it doesn't exist
            if not hasattr(self, '_last_conversation_category'):
                self._last_conversation_category = None
                
            # Recognize intent
            intent = self._recognize_intent(query)
            logger.info(f"Recognized intent: {intent}")
            
            # Extract entities
            entities = self._extract_entities(query)
            logger.info(f"Extracted entities: {entities}")
            
            # Process based on intent
            if intent == 'conversation':
                response = self._handle_conversation_intent(query)
            elif intent == 'search':
                response = self._handle_search_intent(entities)
            elif intent == 'compare':
                response = self._handle_compare_intent(entities)
            elif intent == 'specs':
                response = self._handle_specs_intent(entities)
            elif intent == 'recommend':
                response = self._handle_recommend_intent(entities)
            elif intent == 'count':
                response = self._handle_count_intent(query, entities)
            elif intent == 'general':
                response = self._handle_general_intent(query, entities)
            else:
                return {
                    "type": "text",
                    "content": "I'm not sure what you're asking for. You can search for devices, compare them, ask about specifications, or get recommendations."
                }
            
            # For non-conversation intents, add conversational elements to the response
            if intent != 'conversation' and "summary" in response:
                conversational_prefix = self._generate_conversational_prefix(query, intent)
                response["summary"] = f"{conversational_prefix} {response['summary']}"
            
            return response
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
            Intent string: 'search', 'compare', 'specs', 'recommend', 'general', 'count', or 'conversation'
        """
        query = query.lower()
        
        # Check for conversational intent first (greetings, thanks, etc.)
        if self.conversation_model is not None:
            # Use the conversation model to categorize the input
            category = self.conversation_model.categorize_input(query)
            
            # If it's a recognized conversational category (not default), return conversation intent
            if category != 'default':
                # Store the category for later use
                self._last_conversation_category = category
                return 'conversation'
        
        # Check for count intent (counting brands, devices, etc.)
        count_patterns = [
            'how many brands', 'number of brands', 'total brands',
            'how many devices', 'number of devices', 'total devices',
            'count of', 'quantity of'
        ]
        for pattern in count_patterns:
            if pattern in query:
                return 'count'
        
        # Check for general questions about mobile devices
        general_patterns = [
            'what is', 'tell me about', 'explain', 'what are',
            'how does', 'why is', 'when was', 'who makes',
            'should i buy', 'is it worth', 'good choice', 'better option',
            'your opinion', 'what do you think', 'advice', 'suggest'
        ]
        
        # Check if it's a general question without specific device mention
        for pattern in general_patterns:
            if pattern in query:
                # If no specific device is mentioned, it's a general question
                device_names = self._extract_device_names(query)
                if not device_names:
                    return 'general'
        
        # Check for compare intent (highest priority for specific devices)
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
        
        # Check if query is very short (1-2 words) - likely conversational
        words = query.split()
        if len(words) <= 2:
            return 'conversation'
        
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
    
    def _generate_conversational_prefix(self, query, intent):
        """Generate a conversational prefix for the response based on the query and intent.
        
        Args:
            query: Natural language query from the user
            intent: Recognized intent
            
        Returns:
            Conversational prefix string
        """
        # List of conversational prefixes for different intents
        search_prefixes = [
            "I found some information about",
            "Here's what I know about",
            "Let me tell you about",
            "I'd be happy to share details about",
            "Great question! Here's information on"
        ]
        
        specs_prefixes = [
            "Looking at the specifications,",
            "According to the device details,",
            "The technical specifications show that",
            "I can tell you that",
            "Based on the device data,"
        ]
        
        compare_prefixes = [
            "When comparing these devices,",
            "Looking at both devices side by side,",
            "Here's how these devices stack up:",
            "Let me break down the comparison for you:",
            "If we look at the differences,"
        ]
        
        recommend_prefixes = [
            "Based on your interests, I'd recommend",
            "You might want to consider",
            "From what I understand, these devices would suit your needs:",
            "Here are some great options for you:",
            "I think you'd be happy with"
        ]
        
        # Select a random prefix based on intent
        import random
        if intent == 'search':
            return random.choice(search_prefixes)
        elif intent == 'specs':
            return random.choice(specs_prefixes)
        elif intent == 'compare':
            return random.choice(compare_prefixes)
        elif intent == 'recommend':
            return random.choice(recommend_prefixes)
        else:
            return "Here's what I found:"
    
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
        if self.model is not None and self.device_embeddings is not None and len(self.device_embeddings) > 0:
            try:
                # Encode the query
                query_embedding = self.model.encode([query])
                
                # Make sure query_embedding is 2D
                if len(query_embedding.shape) == 1:
                    query_embedding = query_embedding.reshape(1, -1)
                
                # Calculate similarity with all device embeddings
                similarities = cosine_similarity(query_embedding, self.device_embeddings)[0]
                
                # Get the top 2 matches (only if we have at least 2 devices)
                num_matches = min(2, len(self.device_embeddings))
                if num_matches > 0:
                    top_indices = similarities.argsort()[-num_matches:][::-1]
                    
                    # Only consider matches with similarity above threshold
                    threshold = 0.5
                    device_names = []
                    for idx in top_indices:
                        if similarities[idx] > threshold:
                            device_names.append(self.device_texts[idx])
                    
                    if device_names:
                        return device_names
            except Exception as e:
                logger.error(f"Error in semantic search: {str(e)}")
        
        # Extract potential device names by looking for brand names followed by model names
        query_lower = query.lower()
        potential_devices = []
        
        # Look for common brand names in the query
        common_brands = ['google', 'pixel', 'apple', 'iphone', 'samsung', 'galaxy', 'huawei', 'xiaomi', 'oppo', 'vivo', 'oneplus']
        for brand in common_brands:
            if brand in query_lower:
                # Look for patterns like "google pixel 6" or "iphone 15"
                pattern = f"{brand}\s+([\w\d]+)"
                matches = re.findall(pattern, query_lower)
                if matches:
                    for match in matches:
                        potential_device = f"{brand} {match}"
                        potential_devices.append(potential_device)
        
        # If we found potential devices, return them
        if potential_devices:
            return potential_devices
        
        # Fallback to simple keyword extraction
        words = re.findall(r'\b\w+\b', query_lower)
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
                "content": "I couldn't identify a device in your query. Could you please specify which mobile device you're interested in learning about?"
            }
        
        # Get data for the first device
        device_name = entities['device_names'][0]
        device_data = self._get_device_data(device_name)
        
        if device_data is None:
            # Provide a more helpful response with suggestions
            similar_devices = self._find_similar_devices(device_name)
            suggestion_text = ""
            
            if similar_devices:
                suggestion_text = f" Did you perhaps mean one of these: {', '.join(similar_devices[:3])}?"
            
            return {
                "type": "text",
                "content": f"I couldn't find any information about {device_name}.{suggestion_text} Please try again with a different device name."
            }
        
        # Format the device data for display
        formatted_device = self._format_device_data(device_data)
        
        # Create a more conversational summary with key highlights
        highlights = self._extract_device_highlights(formatted_device)
        
        return {
            "type": "device_details",
            "summary": f"{formatted_device['name']}. {highlights}",
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
    
    def _find_similar_devices(self, device_name):
        """Find devices with similar names to the given device name.
        
        Args:
            device_name: The device name to find similar devices for
            
        Returns:
            List of similar device names
        """
        similar_devices = []
        device_name_lower = device_name.lower()
        
        # Try to find devices that contain parts of the query
        for name in self.device_index.keys():
            # Skip exact matches (which we already determined don't exist)
            if name == device_name_lower:
                continue
                
            # Check if the device name contains parts of the query
            words = device_name_lower.split()
            match_score = 0
            
            for word in words:
                if len(word) > 2 and word in name:  # Only consider words with more than 2 characters
                    match_score += 1
            
            if match_score > 0:
                similar_devices.append((name, match_score))
        
        # Sort by match score (descending)
        similar_devices.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the names
        return [name for name, _ in similar_devices[:5]]
    
    def _extract_device_highlights(self, device):
        """Extract key highlights from device specifications for a more conversational response.
        
        Args:
            device: Formatted device data
            
        Returns:
            String with key highlights
        """
        highlights = []
        specs = device.get('specifications', {})
        
        # Extract key specifications that users typically care about
        if specs:
            # Display
            if 'display' in specs:
                highlights.append(f"It features a {specs['display']} display")
                
            # Camera
            if 'main_camera' in specs:
                highlights.append(f"The main camera is {specs['main_camera']}")
            elif 'camera' in specs:
                highlights.append(f"It has a {specs['camera']} camera")
                
            # Processor/Chipset
            if 'chipset' in specs:
                highlights.append(f"Powered by a {specs['chipset']} processor")
            elif 'cpu' in specs:
                highlights.append(f"Equipped with a {specs['cpu']} CPU")
                
            # Battery
            if 'battery' in specs:
                highlights.append(f"The battery capacity is {specs['battery']}")
                
            # Memory
            if 'memory' in specs:
                highlights.append(f"It comes with {specs['memory']} storage options")
        
        # If we couldn't extract any highlights, provide a generic message
        if not highlights:
            return "I have the full specifications available for you to review."
            
        # Join the highlights with proper punctuation
        if len(highlights) == 1:
            return highlights[0] + "."
        elif len(highlights) == 2:
            return highlights[0] + " and " + highlights[1] + "."
        else:
            return ", ".join(highlights[:-1]) + ", and " + highlights[-1] + "."
    
    def _handle_recommend_intent(self, entities):
        """Handle recommend intent.
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Response dictionary
        """
        # Get top 3 devices based on popularity or ratings
        top_devices = self._get_top_devices(3)
        
        if not top_devices:
            return {
                "type": "text",
                "content": "I couldn't find any devices to recommend right now. Could you tell me what features are most important to you so I can provide better suggestions?"
            }
        
        # Format the device data for display
        formatted_devices = [self._format_device_data(device) for device in top_devices]
        
        # Create personalized recommendations
        recommendations = []
        for i, device in enumerate(formatted_devices):
            highlights = self._extract_device_highlights(device)
            recommendations.append(f"{i+1}. {device['name']}: {highlights}")
        
        recommendation_text = "\n\n".join(recommendations)
        
        return {
            "type": "device_list",
            "summary": "Based on your interests, here are some top recommendations:",
            "devices": formatted_devices,
            "recommendations": recommendation_text
        }
    
    def _handle_count_intent(self, query, entities):
        """Handle count intent - counting brands, devices, etc.
        
        Args:
            query: The original query string
            entities: Dictionary of extracted entities
            
        Returns:
            Response dictionary
        """
        query_lower = query.lower()
        
        # Count brands
        if any(x in query_lower for x in ['brands', 'manufacturers', 'companies']):
            unique_brands = self.unified_data['brand_name'].unique()
            brand_count = len(unique_brands)
            brand_list = ', '.join(sorted(unique_brands)[:10])
            
            if len(unique_brands) > 10:
                brand_list += f", and {len(unique_brands) - 10} more"
            
            return {
                "type": "text",
                "content": f"I have information on {brand_count} different mobile device brands in my database. These include {brand_list}. Is there a specific brand you'd like to know more about?"
            }
        
        # Count devices
        elif any(x in query_lower for x in ['devices', 'phones', 'models']):
            device_count = len(self.unified_data)
            specs_count = sum(~self.unified_data['specifications'].isna())
            
            return {
                "type": "text",
                "content": f"I have information on {device_count} different mobile devices in my database, with detailed specifications for {specs_count} of them. You can ask me about any specific device or brand you're interested in."
            }
        
        # Default count response
        else:
            return {
                "type": "text",
                "content": f"I have information on {len(self.unified_data['brand_name'].unique())} brands and {len(self.unified_data)} devices in my database. What would you like to know about?"
            }
    
    def _handle_conversation_intent(self, query):
        """Handle conversational interactions like greetings, thanks, etc.
        
        Args:
            query: The original query string
            
        Returns:
            Response dictionary
        """
        # Use the conversation model to get a response if available
        if self.conversation_model is not None:
            response_text = self.conversation_model.get_response(query)
            return {
                "type": "text",
                "content": response_text
            }
        
        # Fallback responses if conversation model is not available
        if hasattr(self, '_last_conversation_category') and self._last_conversation_category:
            category = self._last_conversation_category
            
            # Basic responses for common categories
            if category == 'greeting':
                return {
                    "type": "text",
                    "content": "Hello! I'm Sumail-000, your mobile device assistant. How can I help you today?"
                }
            elif category == 'farewell':
                return {
                    "type": "text",
                    "content": "Goodbye! Feel free to come back if you have more questions. Sumail-000 will be here for you."
                }
            elif category == 'thanks':
                return {
                    "type": "text",
                    "content": "You're welcome! I'm happy I could help. That's what Sumail-000 is here for!"
                }
            elif category == 'identity':
                return {
                    "type": "text",
                    "content": "I'm Sumail-000, your personal mobile device assistant. I was created to help you with all your mobile device questions and needs. I can search for information, compare devices, and give personalized recommendations based on your preferences."
                }
        
        # Default conversational response
        return {
            "type": "text",
            "content": "I'm Sumail-000, your mobile device assistant. I can help you find information about phones, compare devices, or get recommendations. What would you like to know?"
        }
    
    def _handle_general_intent(self, query, entities):
        """Handle general questions about mobile devices.
        
        Args:
            query: The original query string
            entities: Dictionary of extracted entities
            
        Returns:
            Response dictionary
        """
        query_lower = query.lower()
        
        # Handle buying advice questions
        if any(x in query_lower for x in ['should i buy', 'worth buying', 'good choice', 'recommend', 'suggestion']):
            return {
                "type": "text",
                "content": "When deciding on a new mobile device, it's important to consider your specific needs. If you're looking for excellent camera quality, Google Pixel and iPhone devices are often top choices. For customization and powerful hardware, Samsung and OnePlus offer great options. Budget-conscious buyers might consider Xiaomi or Realme. What features are most important to you? I can recommend specific devices based on your preferences."
            }
        
        # Handle questions about mobile technology
        elif any(x in query_lower for x in ['what is', 'explain', 'how does']):
            if 'processor' in query_lower or 'chipset' in query_lower or 'cpu' in query_lower:
                return {
                    "type": "text",
                    "content": "A mobile processor or chipset is the brain of your smartphone. Top manufacturers include Qualcomm (Snapdragon series), Apple (A-series), Samsung (Exynos), and MediaTek (Dimensity). Higher-end processors offer better performance for gaming, multitasking, and camera processing. They're typically identified by model numbers - generally, the higher the number, the more powerful the processor."
                }
            elif 'camera' in query_lower:
                return {
                    "type": "text",
                    "content": "Modern smartphone cameras are sophisticated systems that combine hardware and software. While megapixel count (MP) matters, it's not the only factor - sensor size, aperture, and image processing are equally important. Google Pixels are known for excellent computational photography, iPhones for consistent quality, and Samsung for versatile multi-lens setups. Many flagships now feature multiple cameras for different focal lengths and special features like night mode and portrait effects."
                }
            elif 'battery' in query_lower:
                return {
                    "type": "text",
                    "content": "Smartphone battery capacity is measured in milliampere-hours (mAh). Most modern phones range from 3,000-5,000 mAh, with larger numbers generally meaning longer battery life. However, actual battery performance depends on many factors including screen size, processor efficiency, and software optimization. Fast charging technology is also important - look for standards like Qualcomm Quick Charge, USB Power Delivery, or proprietary systems like OnePlus' Warp Charge."
                }
            elif 'display' in query_lower or 'screen' in query_lower:
                return {
                    "type": "text",
                    "content": "Smartphone displays vary in technology (LCD, OLED, AMOLED), resolution, refresh rate, and size. OLED/AMOLED screens offer better contrast and power efficiency than LCD. Resolution is measured in pixels (1080p, 1440p, etc.), while refresh rates (60Hz, 90Hz, 120Hz) affect smoothness of scrolling and animations. Higher is generally better for both, but impacts battery life. Screen size is a personal preference - larger screens are better for media but less pocketable."
                }
            else:
                return {
                    "type": "text",
                    "content": "Mobile devices have evolved tremendously over the years. Modern smartphones combine powerful processors, sophisticated cameras, high-resolution displays, and various sensors into pocket-sized computers. They typically run either iOS (Apple) or Android (various manufacturers) operating systems. Is there a specific aspect of mobile technology you'd like to learn more about?"
                }
        
        # Default general response
        else:
            return {
                "type": "text",
                "content": "I'm your mobile device assistant, trained on a database of hundreds of smartphones and their specifications. I can help you find information about specific devices, compare models, understand technical specifications, or get personalized recommendations. What would you like to know about today?"
            }
    
    def _get_top_devices(self, count=3):
        """Get top devices based on popularity or ratings.
        
        Args:
            count: Number of devices to return
            
        Returns:
            List of top device data rows
        """
        try:
            # For now, we'll use the most recent devices as a proxy for popularity
            # In a real system, this would use actual popularity metrics or user ratings
            if not self.unified_data.empty:
                # Sort by device_url (assuming newer devices have higher IDs in the URL)
                top_devices = self.unified_data.sort_values('device_url', ascending=False).head(count)
                return top_devices.to_dict('records')
            return []
        except Exception as e:
            logger.error(f"Error getting top devices: {str(e)}")
            return []
    
    def train_conversation_model(self, user_input, category, response):
        """Train the conversation model with a new pattern and response.
        
        Args:
            user_input: User's input text
            category: Conversation category
            response: Response text
            
        Returns:
            True if training was successful, False otherwise
        """
        if self.conversation_model is not None:
            try:
                self.conversation_model.train(user_input, category, response)
                logger.info(f"Trained conversation model with new {category} response")
                return True
            except Exception as e:
                logger.error(f"Error training conversation model: {str(e)}")
                return False
        else:
            logger.warning("Conversation model not available for training")
            return False
    
    def _format_device_data(self, device_data):
        """Format device data for display.
        
        Args:
            device_data: Device data from the unified dataset
            
        Returns:
            Formatted device data dictionary
        """
        device_specs = {}
        
        # Extract device specifications from JSON string
        if 'specifications' in device_data and device_data['specifications']:
            try:
                device_specs = json.loads(device_data['specifications'])
            except Exception as e:
                logger.error(f"Error parsing device data JSON for {device_data['device_name']}: {str(e)}")
        
        # Format the device data for display with safe access to columns
        formatted_device = {
            'name': f"{device_data.get('brand_name', '')} {device_data.get('device_name', '')}",
            'brand': device_data.get('brand_name', ''),
            'model': device_data.get('device_name', ''),
            'url': device_data.get('device_url', ''),
            'image_url': device_data.get('device_image', ''),  # Changed from image_url to device_image
            'specifications': device_specs
        }
        
        # Extract device pictures if available
        if 'pictures' in device_data and device_data['pictures']:
            try:
                pictures = json.loads(device_data['pictures'])
                formatted_device['pictures'] = pictures
            except Exception as e:
                logger.error(f"Error parsing device pictures JSON for {device_data['device_name']}: {str(e)}")
                formatted_device['pictures'] = []
        else:
            formatted_device['pictures'] = []
        
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
