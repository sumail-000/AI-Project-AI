import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

class AIAssistantLogger:
    """
    Custom logger for the AI Assistant module that provides detailed logging
    with timestamps, log levels, and rotation capabilities.
    """
    
    def __init__(self, log_file='ai_assistant.log', max_size_mb=50, backup_count=3):
        """
        Initialize the AI Assistant logger.
        
        Args:
            log_file: Path to the log file
            max_size_mb: Maximum size of log file in MB before rotation
            backup_count: Number of backup files to keep
        """
        self.log_file = log_file
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.backup_count = backup_count
        
        # Create logs directory if it doesn't exist
        logs_dir = os.path.dirname(log_file)
        if logs_dir and not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Set up the logger
        self.logger = logging.getLogger('ai_assistant')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create a file handler for the log file with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_size_bytes,
            backupCount=self.backup_count
        )
        
        # Create a formatter with timestamp, level, and message
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Set the formatter for the handler
        file_handler.setFormatter(formatter)
        
        # Add the handler to the logger
        self.logger.addHandler(file_handler)
        
        # Also log to console for development purposes
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Log initialization
        self.logger.info("AI Assistant Logger initialized")
    
    def debug(self, message):
        """Log a debug message."""
        self.logger.debug(message)
    
    def info(self, message):
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message):
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message):
        """Log an error message."""
        self.logger.error(message)
    
    def critical(self, message):
        """Log a critical message."""
        self.logger.critical(message)
    
    def log_function_entry(self, function_name, **kwargs):
        """
        Log function entry with parameters.
        
        Args:
            function_name: Name of the function being entered
            **kwargs: Parameters passed to the function
        """
        params_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.debug(f"ENTER: {function_name}({params_str})")
    
    def log_function_exit(self, function_name, result=None):
        """
        Log function exit with result.
        
        Args:
            function_name: Name of the function being exited
            result: Result of the function (optional)
        """
        if result is not None:
            # Truncate result if it's too long
            result_str = str(result)
            if len(result_str) > 200:
                result_str = result_str[:200] + "..."
            self.logger.debug(f"EXIT: {function_name} -> {result_str}")
        else:
            self.logger.debug(f"EXIT: {function_name}")
    
    def log_exception(self, function_name, exception):
        """
        Log an exception that occurred in a function.
        
        Args:
            function_name: Name of the function where the exception occurred
            exception: The exception object
        """
        self.logger.error(f"EXCEPTION in {function_name}: {str(exception)}", exc_info=True)

# Create a singleton instance
ai_logger = AIAssistantLogger()
