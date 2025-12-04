"""Configuration manager for MinTool application."""
import json
import os


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_file="mintool_config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """
        Load configuration from JSON file.
        
        Returns:
            dict: Configuration dictionary
        """
        default_config = {
            "default_min_id": 16,
            "tester_present_interval_ms": 3000,
            "enable_tester_present_on_connect": False,
            "tester_present_suppress": False,
            "security_exe_path": "",
            "automation_script_path": "",
            "security_levels": [
                {
                    "level": 1,
                    "name": "Programming Session",
                    "color": "lightblue"
                },
                {
                    "level": 2,
                    "name": "Extended Diagnostic",
                    "color": "lightgreen"
                }
            ]
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to handle missing keys
                    default_config.update(loaded_config)
                    return default_config
            except Exception as e:
                print(f"Error loading config: {e}")
                return default_config
        return default_config
    
    def save_config(self):
        """
        Save configuration to JSON file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def set(self, key, value):
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
    
    def update(self, updates):
        """
        Update multiple configuration values.
        
        Args:
            updates: Dictionary of updates
        """
        self.config.update(updates)
