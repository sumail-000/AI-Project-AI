import os
import json
import random
import numpy as np
from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

class ConversationModel:
    """A trainable conversation model for the AI assistant with neural capabilities."""
    
    def __init__(self, data_dir='conversation_data'):
        """Initialize the conversation model.
        
        Args:
            data_dir: Directory to store conversation data and model files
        """
        self.data_dir = data_dir
        self.ensure_data_directory()
        
        # Load or initialize conversation data
        self.conversation_data = self.load_conversation_data()
        
        # Initialize vectorizer
        self.vectorizer = None
        self.load_or_initialize_vectorizer()
        
        # Initialize transformers model for improved responses
        try:
            # Use smaller model for resource constraints
            self.tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
            self.lm_model = None  # Lazy loading to save memory until needed
            self.generation_pipeline = None
            logger.info("Initialized conversation model with distilgpt2 tokenizer")
        except Exception as e:
            logger.error(f"Error initializing transformer model: {str(e)}")
            self.tokenizer = None
            self.lm_model = None
            self.generation_pipeline = None
        
        # Define conversation categories
        self.categories = {
            'greeting': ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'howdy'],
            'farewell': ['bye', 'goodbye', 'see you', 'talk to you later', 'until next time', 'farewell'],
            'thanks': ['thank you', 'thanks', 'appreciate it', 'grateful', 'thank you very much'],
            'affirmation': ['yes', 'yeah', 'sure', 'absolutely', 'definitely', 'correct', 'right'],
            'negation': ['no', 'nope', 'not really', 'negative', 'disagree', 'incorrect'],
            'question': ['what', 'why', 'how', 'when', 'where', 'who', 'which', 'whose', 'whom', '?'],
            'confusion': ['confused', 'don\'t understand', 'unclear', 'what do you mean', 'explain'],
            'frustration': ['frustrated', 'annoying', 'irritating', 'not working', 'problem', 'issue', 'error'],
            'praise': ['good job', 'well done', 'excellent', 'amazing', 'awesome', 'great', 'fantastic'],
            'criticism': ['bad', 'terrible', 'awful', 'poor', 'disappointing', 'useless', 'not helpful'],
            'identity': ['who are you', 'what are you', 'what is your name', 'your name', 'about you', 'tell me about you', 
                        'sumail', 'sumail-000', 'who created you', 'what can you do', 'your purpose', 'what do you do']
        }
        
        # Initialize conversation context
        self.conversation_context = []
        self.max_context_length = 5
        
        # Add default responses if none exist
        if not self.conversation_data:
            self.add_default_responses()
            self.save_conversation_data()
    
    def ensure_data_directory(self):
        """Ensure the data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Created conversation data directory: {self.data_dir}")
    
    def load_conversation_data(self):
        """Load conversation data from file."""
        data_file = os.path.join(self.data_dir, 'conversation_data.json')
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded {len(data)} conversation patterns")
                return data
            except Exception as e:
                logger.error(f"Error loading conversation data: {str(e)}")
                return {}
        else:
            logger.info("No conversation data file found, initializing empty data")
            return {}
    
    def save_conversation_data(self):
        """Save conversation data to file."""
        data_file = os.path.join(self.data_dir, 'conversation_data.json')
        try:
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_data, f, indent=2)
            logger.info(f"Saved {len(self.conversation_data)} conversation patterns")
        except Exception as e:
            logger.error(f"Error saving conversation data: {str(e)}")
    
    def load_or_initialize_vectorizer(self):
        """Load or initialize the TF-IDF vectorizer."""
        vectorizer_file = os.path.join(self.data_dir, 'vectorizer.pkl')
        if os.path.exists(vectorizer_file):
            try:
                with open(vectorizer_file, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                logger.info("Loaded TF-IDF vectorizer")
            except Exception as e:
                logger.error(f"Error loading vectorizer: {str(e)}")
                self.vectorizer = TfidfVectorizer(ngram_range=(1, 3), min_df=1, max_df=0.9)
        else:
            logger.info("Initializing new TF-IDF vectorizer")
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 3), min_df=1, max_df=0.9)
    
    def save_vectorizer(self):
        """Save the TF-IDF vectorizer."""
        vectorizer_file = os.path.join(self.data_dir, 'vectorizer.pkl')
        try:
            with open(vectorizer_file, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            logger.info("Saved TF-IDF vectorizer")
        except Exception as e:
            logger.error(f"Error saving vectorizer: {str(e)}")
            
    def _initialize_language_model(self):
        """Initialize the language model for improved response generation."""
        if self.lm_model is None and self.tokenizer is not None:
            try:
                self.lm_model = AutoModelForCausalLM.from_pretrained("distilgpt2")
                self.generation_pipeline = pipeline(
                    "text-generation",
                    model=self.lm_model,
                    tokenizer=self.tokenizer,
                    max_length=100,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9
                )
                logger.info("Initialized language model for conversation generation")
            except Exception as e:
                logger.error(f"Error initializing language model: {str(e)}")
                
    def update_conversation_context(self, role, message):
        """Update the conversation context with a new message.
        
        Args:
            role: 'user' or 'assistant'
            message: Message content
        """
        self.conversation_context.append({
            'role': role,
            'content': message
        })
        
        # Keep context to a manageable size
        if len(self.conversation_context) > self.max_context_length:
            self.conversation_context = self.conversation_context[-self.max_context_length:]
    
    def add_default_responses(self):
        """Add default responses for various conversation patterns."""
        # Identity only as requested
        self.conversation_data['identity'] = [
            "I'm Sumail-000, your personal mobile device assistant. I was created to help you with all your mobile device questions and needs.",
            "My name is Sumail-000. I'm a specialized AI designed to provide information and assistance with mobile devices.",
            "I'm Sumail-000! I'm here to be your go-to resource for mobile device information, comparisons, and recommendations.",
            "Sumail-000 is my name, and helping with mobile devices is my game! I'm designed to make finding device information easy and enjoyable.",
            "I'm Sumail-000, an AI assistant focused on mobile devices. I can search for information, compare devices, and give recommendations based on your needs."
        ]
    
    def categorize_input(self, user_input):
        """Categorize user input into one of the defined categories.
        
        Args:
            user_input: User's input text
            
        Returns:
            Category name
        """
        if not user_input or user_input.strip() == '':
            return 'default'
            
        user_input_lower = user_input.lower()
        
        # Check for exact matches in categories
        for category, patterns in self.categories.items():
            for pattern in patterns:
                if pattern in user_input_lower:
                    return category
        
        # Try semantic matching if no exact match
        try:
            all_patterns = []
            pattern_to_category = {}
            
            # Collect all patterns
            for category, patterns in self.categories.items():
                for pattern in patterns:
                    all_patterns.append(pattern)
                    pattern_to_category[pattern] = category
                    
                # Also add any existing responses as patterns
                if category in self.conversation_data:
                    for response in self.conversation_data[category]:
                        # Add the category as a pattern for itself (helps with classification)
                        all_patterns.append(category)
                        pattern_to_category[category] = category
                        
                # Add multiple instances of the category name itself to weight it more heavily
                for _ in range(3):
                    all_patterns.append(category)
                    pattern_to_category.update({category: category for _ in range(3)})
                
            if not all_patterns:
                return 'default'
            
            # Vectorize patterns and input
            all_vectors = self.vectorizer.fit_transform(all_patterns + [user_input_lower])
            input_vector = all_vectors[-1]
            pattern_vectors = all_vectors[:-1]
            
            # Calculate similarities
            similarities = cosine_similarity(input_vector, pattern_vectors)[0]
            
            # Find best match
            if len(similarities) > 0:
                best_idx = np.argmax(similarities)
                if similarities[best_idx] > 0.3:  # Threshold for a good match
                    return pattern_to_category[all_patterns[best_idx]]
        
        except Exception as e:
            logger.error(f"Error in semantic matching: {str(e)}")
        
        return 'default'
    
    def get_response(self, user_input):
        """Get a response based on user input using both pattern matching and neural generation.
        
        Args:
            user_input: User's input text
            
        Returns:
            Response text
        """
        # Update conversation context
        self.update_conversation_context('user', user_input)
        
        # First, categorize the input
        category = self.categorize_input(user_input)
        
        # Try to generate a neural response if available
        neural_response = self._generate_neural_response(user_input, category)
        
        # If we have a good neural response, use it
        if neural_response:
            # Update conversation context with response
            self.update_conversation_context('assistant', neural_response)
            return neural_response
        
        # Otherwise, fall back to pattern-based response
        if category in self.conversation_data and self.conversation_data[category]:
            pattern_response = random.choice(self.conversation_data[category])
            # Update conversation context
            self.update_conversation_context('assistant', pattern_response)
            return pattern_response
        else:
            default_response = "I'm Sumail-000, your mobile device assistant. How can I help you today?"
            # Update conversation context
            self.update_conversation_context('assistant', default_response)
            return default_response
    
    def _generate_neural_response(self, user_input, category):
        """Generate a response using neural language model.
        
        Args:
            user_input: User's input text
            category: Detected conversation category
            
        Returns:
            Generated response or None if generation failed
        """
        if self.tokenizer is None or (self.lm_model is None and self.generation_pipeline is None):
            try:
                self._initialize_language_model()
            except Exception as e:
                logger.error(f"Error initializing language model for response: {str(e)}")
                return None
        
        try:
            # If still not initialized, return None
            if self.generation_pipeline is None:
                return None
                
            # Create prompt from conversation context
            prompt = self._create_prompt_from_context(category)
            
            # Generate response
            generated_texts = self.generation_pipeline(prompt, max_length=100, num_return_sequences=1)
            
            if generated_texts and len(generated_texts) > 0:
                generated_text = generated_texts[0]['generated_text']
                
                # Extract just the assistant's response (after the prompt)
                response = generated_text[len(prompt):].strip()
                
                # Clean up the response
                response = self._clean_generated_response(response)
                
                # If the response is too short or empty, fall back to pattern-based
                if len(response) < 10:
                    return None
                    
                return response
                
            return None
        except Exception as e:
            logger.error(f"Error generating neural response: {str(e)}")
            return None
            
    def _create_prompt_from_context(self, category):
        """Create a prompt for the language model from conversation context.
        
        Args:
            category: Detected conversation category
            
        Returns:
            Prompt string
        """
        # Start with a system prompt
        prompt = "I am Sumail-000, a helpful AI assistant for mobile devices. "
        
        # Add some category-specific context
        if category == 'greeting':
            prompt += "I greet users warmly. "
        elif category == 'farewell':
            prompt += "I say goodbye politely. "
        elif category == 'thanks':
            prompt += "I respond to gratitude graciously. "
        elif category == 'identity':
            prompt += "I explain who I am and what I can do. "
        elif category == 'confusion':
            prompt += "I help clarify misunderstandings. "
        
        # Add recent conversation context
        for item in self.conversation_context[-3:]:  # Last 3 messages
            role = "User" if item['role'] == 'user' else "Sumail-000"
            prompt += f"{role}: {item['content']} "
            
        # Add a start for the assistant's response
        prompt += "Sumail-000: "
        
        return prompt
        
    def _clean_generated_response(self, response):
        """Clean up the generated response.
        
        Args:
            response: Raw generated response
            
        Returns:
            Cleaned response
        """
        # Remove any further "User:" or "Sumail-000:" parts
        response = re.split(r'User:|Sumail-000:', response)[0].strip()
        
        # Remove unwanted characters
        response = response.replace('\n', ' ').strip()
        
        # Fix spacing
        response = re.sub(r'\s+', ' ', response)
        
        return response
    
    def train(self, user_input, category, response):
        """Train the model with a new pattern and response.
        
        Args:
            user_input: User's input text
            category: Conversation category
            response: Response text
        """
        # Add the category if it doesn't exist
        if category not in self.conversation_data:
            self.conversation_data[category] = []
        
        # Add the response if it's not already in the list
        if response not in self.conversation_data[category]:
            self.conversation_data[category].append(response)
            logger.info(f"Added new response to category '{category}'")
        
        # Save the updated data
        self.save_conversation_data()
        
        # Update the vectorizer
        self.save_vectorizer()
        
        # Simulate learning by adding to conversation context
        self.update_conversation_context('user', user_input)
        self.update_conversation_context('assistant', response)
    
    def get_all_categories(self):
        """Get all available conversation categories.
        
        Returns:
            List of category names
        """
        return list(self.conversation_data.keys())
    
    def get_responses_for_category(self, category):
        """Get all responses for a specific category.
        
        Args:
            category: Conversation category
            
        Returns:
            List of responses
        """
        if category in self.conversation_data:
            return self.conversation_data[category]
        else:
            return []