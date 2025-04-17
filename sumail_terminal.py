import os
import sys
import json
import random
import time
from colorama import init, Fore, Style
from ai_assistant import DeviceAIAssistant
from conversation_model import ConversationModel

# Initialize colorama for colored terminal output
init()

class SumailTerminal:
    """Terminal interface for interacting with Sumail-000 and teaching him through conversation."""
    
    def __init__(self):
        """Initialize the terminal interface."""
        self.ai_assistant = DeviceAIAssistant()
        self.conversation_model = self.ai_assistant.conversation_model
        self.conversation_history = []
        self.training_mode = False
        self.current_category = None
        
        # Create conversation data directory if it doesn't exist
        os.makedirs('conversation_data', exist_ok=True)
        
        # Load conversation history if available
        self.load_conversation_history()
        
        # Commands that Sumail-000 can recognize
        self.commands = {
            '/help': self.show_help,
            '/train': self.toggle_training_mode,
            '/category': self.set_category,
            '/categories': self.show_categories,
            '/save': self.save_conversation,
            '/exit': self.exit_terminal,
            '/clear': self.clear_screen
        }
    
    def load_conversation_history(self):
        """Load conversation history from file."""
        history_file = os.path.join('conversation_data', 'conversation_history.json')
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.conversation_history = json.load(f)
                print(f"{Fore.GREEN}Loaded {len(self.conversation_history)} previous conversations{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error loading conversation history: {str(e)}{Style.RESET_ALL}")
                self.conversation_history = []
    
    def save_conversation_history(self):
        """Save conversation history to file."""
        history_file = os.path.join('conversation_data', 'conversation_history.json')
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2)
            print(f"{Fore.GREEN}Saved {len(self.conversation_history)} conversations to history{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error saving conversation history: {str(e)}{Style.RESET_ALL}")
    
    def show_help(self):
        """Show help information."""
        print(f"\n{Fore.CYAN}=== Sumail-000 Terminal Commands ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}/help{Style.RESET_ALL} - Show this help message")
        print(f"{Fore.YELLOW}/train{Style.RESET_ALL} - Toggle training mode (teach Sumail-000 new responses)")
        print(f"{Fore.YELLOW}/category <name>{Style.RESET_ALL} - Set the category for training")
        print(f"{Fore.YELLOW}/categories{Style.RESET_ALL} - Show available categories")
        print(f"{Fore.YELLOW}/save{Style.RESET_ALL} - Save the current conversation")
        print(f"{Fore.YELLOW}/clear{Style.RESET_ALL} - Clear the screen")
        print(f"{Fore.YELLOW}/exit{Style.RESET_ALL} - Exit the terminal")
        print(f"\n{Fore.CYAN}=== Training Mode ==={Style.RESET_ALL}")
        print("When in training mode, your messages will be used to teach Sumail-000.")
        print("First set a category with /category, then type your response.")
        print("Sumail-000 will learn from your examples and use them in future conversations.")
        print(f"\n{Fore.CYAN}=== Regular Mode ==={Style.RESET_ALL}")
        print("In regular mode, you can chat with Sumail-000 normally.")
        print("He will use what he's learned to respond to your messages.")
    
    def toggle_training_mode(self):
        """Toggle training mode on/off."""
        self.training_mode = not self.training_mode
        if self.training_mode:
            print(f"{Fore.GREEN}Training mode activated. Teach Sumail-000 new responses!{Style.RESET_ALL}")
            print(f"Use {Fore.YELLOW}/category <name>{Style.RESET_ALL} to set the category for your examples.")
        else:
            print(f"{Fore.GREEN}Training mode deactivated. Back to normal conversation.{Style.RESET_ALL}")
    
    def set_category(self, category_name=None):
        """Set the current category for training."""
        if not category_name:
            print(f"{Fore.RED}Please specify a category name.{Style.RESET_ALL}")
            return
        
        self.current_category = category_name
        print(f"{Fore.GREEN}Category set to: {category_name}{Style.RESET_ALL}")
        print(f"Now type examples of responses for this category. Sumail-000 will learn from them.")
    
    def show_categories(self):
        """Show available categories."""
        if self.conversation_model:
            categories = self.conversation_model.get_all_categories()
            print(f"\n{Fore.CYAN}=== Available Categories ==={Style.RESET_ALL}")
            for category in categories:
                print(f"- {category}")
            print(f"\nYou can also create new categories by using {Fore.YELLOW}/category <new_name>{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Conversation model not available.{Style.RESET_ALL}")
    
    def save_conversation(self):
        """Save the current conversation."""
        self.save_conversation_history()
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def exit_terminal(self):
        """Exit the terminal interface."""
        print(f"{Fore.GREEN}Saving conversation history...{Style.RESET_ALL}")
        self.save_conversation_history()
        print(f"{Fore.CYAN}Thank you for chatting with Sumail-000. Goodbye!{Style.RESET_ALL}")
        sys.exit(0)
    
    def process_command(self, user_input):
        """Process a command from the user."""
        parts = user_input.split(' ', 1)
        command = parts[0].lower()
        
        if command in self.commands:
            if len(parts) > 1:
                self.commands[command](parts[1])
            else:
                self.commands[command]()
            return True
        
        return False
    
    def train_model(self, user_input):
        """Train the model with a new example."""
        if not self.current_category:
            print(f"{Fore.RED}Please set a category first using {Fore.YELLOW}/category <name>{Style.RESET_ALL}")
            return
        
        if self.conversation_model:
            # Generate a sample query for this response based on the category
            sample_query = self.generate_sample_query(self.current_category)
            
            # Train the model with the new example
            success = self.ai_assistant.train_conversation_model(
                sample_query, self.current_category, user_input
            )
            
            if success:
                print(f"{Fore.GREEN}Sumail-000 learned a new {self.current_category} response!{Style.RESET_ALL}")
                # Add a simulated thinking delay
                print(f"{Fore.CYAN}Sumail-000 is processing...{Style.RESET_ALL}")
                time.sleep(1.5)
                # Have Sumail-000 acknowledge the learning
                responses = [
                    f"I've learned this {self.current_category} response. Thank you for teaching me!",
                    f"I'll remember this {self.current_category} pattern for future conversations.",
                    f"Got it! I've added this to my {self.current_category} responses.",
                    f"Thanks for helping me learn! I've stored this {self.current_category} response.",
                    f"I appreciate you teaching me. I've updated my {self.current_category} knowledge."
                ]
                print(f"{Fore.CYAN}Sumail-000: {random.choice(responses)}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Failed to train Sumail-000 with the new response.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Conversation model not available for training.{Style.RESET_ALL}")
    
    def generate_sample_query(self, category):
        """Generate a sample query for a category to use in training."""
        # Default queries for common categories
        category_queries = {
            'greeting': ['hi', 'hello', 'hey there', 'good morning', 'greetings'],
            'farewell': ['bye', 'goodbye', 'see you later', 'farewell', 'until next time'],
            'thanks': ['thank you', 'thanks', 'appreciate it', 'thank you so much', 'thanks a lot'],
            'identity': ['who are you', 'what is your name', 'tell me about yourself', 'what are you'],
            'help': ['help', 'i need help', 'can you help me', 'assist me', 'support'],
            'affirmation': ['yes', 'yeah', 'sure', 'of course', 'definitely'],
            'negation': ['no', 'nope', 'not really', 'i don\'t think so', 'negative']
        }
        
        if category in category_queries:
            return random.choice(category_queries[category])
        else:
            # For custom categories, use the category name as the query
            return f"{category}"
    
    def get_ai_response(self, user_input):
        """Get a response from the AI assistant."""
        response = self.ai_assistant.process_query(user_input)
        
        # Extract the content from the response
        if isinstance(response, dict):
            if 'content' in response:
                return response['content']
            elif 'summary' in response:
                return response['summary']
        
        # Fallback response
        return "I'm not sure how to respond to that."
    
    def run(self):
        """Run the terminal interface."""
        print(f"\n{Fore.CYAN}=== Welcome to Sumail-000 Terminal Interface ==={Style.RESET_ALL}")
        print(f"Type {Fore.YELLOW}/help{Style.RESET_ALL} for a list of commands.")
        print(f"{Fore.CYAN}Sumail-000: Hello! I'm Sumail-000, your mobile device assistant. How can I help you today?{Style.RESET_ALL}")
        
        while True:
            try:
                # Get user input
                user_input = input(f"{Fore.GREEN}You: {Style.RESET_ALL}")
                
                # Add to conversation history
                self.conversation_history.append({'user': user_input, 'timestamp': time.time()})
                
                # Check if it's a command
                if user_input.startswith('/'):
                    if not self.process_command(user_input):
                        print(f"{Fore.RED}Unknown command. Type {Fore.YELLOW}/help{Style.RESET_ALL}{Fore.RED} for a list of commands.{Style.RESET_ALL}")
                    continue
                
                # Handle training mode
                if self.training_mode:
                    self.train_model(user_input)
                    continue
                
                # Get AI response
                print(f"{Fore.CYAN}Sumail-000 is thinking...{Style.RESET_ALL}")
                time.sleep(0.5)  # Add a small delay to simulate thinking
                
                ai_response = self.get_ai_response(user_input)
                print(f"{Fore.CYAN}Sumail-000: {ai_response}{Style.RESET_ALL}")
                
                # Add to conversation history
                self.conversation_history.append({'ai': ai_response, 'timestamp': time.time()})
                
                # Auto-save every 10 messages
                if len(self.conversation_history) % 10 == 0:
                    self.save_conversation_history()
                
            except KeyboardInterrupt:
                print("\nExiting...")
                self.save_conversation_history()
                break
            
            except Exception as e:
                print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    terminal = SumailTerminal()
    terminal.run()
