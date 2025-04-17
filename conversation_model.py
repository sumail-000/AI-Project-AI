import os
import json
import random
import numpy as np
from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import re

class ConversationModel:
    """A trainable conversation model for the AI assistant."""
    
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
    
    def add_default_responses(self):
        """Add default responses for various conversation patterns."""
        # Greetings
        self.conversation_data['greeting'] = [
            "Hello! I'm Sumail-000, your mobile device assistant. How can I help you today?",
            "Hi there! I'm Sumail-000, and I'm ready to help with any mobile device questions you have.",
            "Hey! I'm Sumail-000. What can I do for you today?",
            "Greetings! Sumail-000 at your service. I'm here to help with all your mobile device needs.",
            "Good day! I'm Sumail-000, your personal AI assistant for mobile devices. What would you like to know?"
        ]
        
        # Farewells
        self.conversation_data['farewell'] = [
            "Goodbye! Feel free to come back if you have more questions. Sumail-000 will be here for you.",
            "See you later! I'm here whenever you need mobile device assistance. Just ask for Sumail-000.",
            "Take care! Don't hesitate to return if you need more help. I'll be waiting.",
            "Farewell! Sumail-000 will be here when you need mobile device information again.",
            "Until next time! I'm always ready to help with your mobile device questions."
        ]
        
        # Thanks
        self.conversation_data['thanks'] = [
            "You're welcome! I'm happy I could help. That's what Sumail-000 is here for!",
            "Glad I could be of assistance! Anything else you'd like to know? I'm all ears.",
            "My pleasure! Is there anything else you'd like to know about mobile devices? Sumail-000 knows quite a bit.",
            "No problem at all! Feel free to ask if you have more questions. I enjoy helping.",
            "Happy to help! Let me know if you need anything else. Sumail-000 is always ready to assist."
        ]
        
        # Confusion
        self.conversation_data['confusion'] = [
            "I apologize for the confusion. Could you please rephrase your question? I want to make sure I understand correctly.",
            "I'm not sure I understood correctly. Can you explain what you're looking for? Sumail-000 wants to help accurately.",
            "I might have misunderstood. Could you provide more details about what you need? I'm eager to assist properly.",
            "I'm having trouble understanding your request. Could you try asking in a different way? I want to give you the right information.",
            "Sorry for the confusion. Could you be more specific about what you're asking? Sumail-000 wants to be helpful."
        ]
        
        # Frustration
        self.conversation_data['frustration'] = [
            "I apologize for the frustration. Let's try a different approach to solve your problem. Sumail-000 won't give up until we find a solution.",
            "I understand this is frustrating. Let me try to help you more effectively. I'm determined to get this right for you.",
            "I'm sorry you're having issues. Let's take a step back and try again. Sumail-000 is here to make things easier, not harder.",
            "I apologize for the difficulty. Let me try to address your concern differently. I want to make sure you get what you need.",
            "I'm sorry this isn't working as expected. Let's try another way to find what you need. Sumail-000 is committed to helping you."
        ]
        
        # Default fallback
        self.conversation_data['default'] = [
            "I'm Sumail-000, your mobile device assistant. Could you ask about a specific device or feature?",
            "Sumail-000 here! I'm specialized in mobile device information. Could you clarify what you're looking for?",
            "I'm Sumail-000, and I know a lot about mobile devices. What specific device or topic are you interested in?",
            "I might have missed your question. Could you ask Sumail-000 about a specific mobile device or feature?",
            "Sumail-000 at your service! How can I help you find information about phones or tablets?"
        ]
        
        # Identity
        self.conversation_data['identity'] = [
            "I'm Sumail-000, your personal mobile device assistant. I was created to help you with all your mobile device questions and needs.",
            "My name is Sumail-000. I'm a specialized AI designed to provide information and assistance with mobile devices.",
            "I'm Sumail-000! I'm here to be your go-to resource for mobile device information, comparisons, and recommendations.",
            "Sumail-000 is my name, and helping with mobile devices is my game! I'm designed to make finding device information easy and enjoyable.",
            "I'm Sumail-000, an AI assistant focused on mobile devices. I can search for information, compare devices, and give recommendations based on your needs."
        ]
    
    def categorize_input(self, user_input):
        """Categorize user input into a conversation category.
        
        Args:
            user_input: User's input text
            
        Returns:
            Category string
        """
        user_input_lower = user_input.lower()
        
        # Check for category matches
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in user_input_lower:
                    return category
        
        # If no category matches, try semantic matching
        if self.vectorizer and self.conversation_data:
            try:
                # Get all patterns we know
                all_patterns = []
                pattern_to_category = {}
                
                for category, responses in self.conversation_data.items():
                    if category != 'default':  # Skip default category
                        all_patterns.extend([category] * 3)  # Add category name as a pattern
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
        """Get a response based on user input.
        
        Args:
            user_input: User's input text
            
        Returns:
            Response text
        """
        category = self.categorize_input(user_input)
        
        if category in self.conversation_data and self.conversation_data[category]:
            return random.choice(self.conversation_data[category])
        else:
            return random.choice(self.conversation_data['default'])
    
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
