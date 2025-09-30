import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

class BotConfigParser:
    """
    Parse and manage bot configuration files
    """
    
    def __init__(self, config_dir: str = "configs"):
        """Initialize with config directory"""
        self.config_dir = config_dir
        
        # Create config directory if it doesn't exist
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir)
            except:
                # In case of permission issues, use current directory
                self.config_dir = "."
    
    def save_config(self, config: Dict[str, Any], name: str = "default") -> bool:
        """
        Save a configuration to file
        
        Args:
            config: Configuration dictionary
            name: Name of the configuration
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        filename = f"{name}.json"
        filepath = os.path.join(self.config_dir, filename)
        
        try:
            # Add timestamp
            config["saved_at"] = datetime.now().isoformat()
            
            # Make a copy to avoid modifying the original
            config_copy = dict(config)
            
            # Write to file
            with open(filepath, "w") as f:
                json.dump(config_copy, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def load_config(self, name: str = "default") -> Optional[Dict[str, Any]]:
        """
        Load a configuration from file
        
        Args:
            name: Name of the configuration
            
        Returns:
            Optional[Dict[str, Any]]: Configuration dictionary if found, None otherwise
        """
        filename = f"{name}.json"
        filepath = os.path.join(self.config_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, "r") as f:
                config = json.load(f)
            
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return None
    
    def list_configs(self) -> List[str]:
        """
        List all available configurations
        
        Returns:
            List[str]: List of configuration names
        """
        configs = []
        
        try:
            for filename in os.listdir(self.config_dir):
                if filename.endswith(".json"):
                    configs.append(filename[:-5])  # Remove .json extension
        except Exception as e:
            print(f"Error listing configs: {e}")
        
        return configs
    
    def delete_config(self, name: str) -> bool:
        """
        Delete a configuration
        
        Args:
            name: Name of the configuration
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        filename = f"{name}.json"
        filepath = os.path.join(self.config_dir, filename)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            os.remove(filepath)
            return True
        except Exception as e:
            print(f"Error deleting config: {e}")
            return False
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get the default configuration
        
        Returns:
            Dict[str, Any]: Default configuration
        """
        return {
            'market': 'R_10',
            'trade_type': 'DIGITEVEN',
            'base_stake': 1.0,
            'stake_multiplier': 1.2,
            'probability_threshold': 0.65,
            'confidence_threshold': 0.6,
            'risk_tolerance': 0.5,
            'max_consecutive_losses': 5,
            'cooldown_period': 60,
            'is_active': False,
            'daily_loss_limit': 50.0,
            'stop_loss': 100.0,
            'take_profit': 100.0,
            'max_trades_per_day': 20,
            'max_drawdown': 15,
            'total_capital': 1000.0,
            'risk_per_trade': 1.0,
            'trading_start': "00:00",
            'trading_end': "23:59",
            'trading_days': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            'analysis_window': 50,
            'use_trend_filter': True,
            'use_volatility_filter': True
        }
    
    def export_config(self, config: Dict[str, Any], filepath: str) -> bool:
        """
        Export a configuration to an external file
        
        Args:
            config: Configuration dictionary
            filepath: Path to export to
            
        Returns:
            bool: True if exported successfully, False otherwise
        """
        try:
            # Add timestamp
            config["exported_at"] = datetime.now().isoformat()
            
            # Make a copy to avoid modifying the original
            config_copy = dict(config)
            
            # Write to file
            with open(filepath, "w") as f:
                json.dump(config_copy, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Import a configuration from an external file
        
        Args:
            filepath: Path to import from
            
        Returns:
            Optional[Dict[str, Any]]: Configuration dictionary if imported successfully, None otherwise
        """
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, "r") as f:
                config = json.load(f)
            
            # Add import timestamp
            config["imported_at"] = datetime.now().isoformat()
            
            return config
        except Exception as e:
            print(f"Error importing config: {e}")
            return None
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a configuration and fill in missing values with defaults
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Dict[str, Any]: Validated configuration with default values for missing keys
        """
        default_config = self.get_default_config()
        validated_config = {}
        
        # Copy all values from config, using defaults for missing values
        for key, default_value in default_config.items():
            validated_config[key] = config.get(key, default_value)
        
        return validated_config
    
    def parse_bot_xml(self, xml_str: str) -> Dict[str, Any]:
        """
        Parse a bot configuration from XML string
        
        Args:
            xml_str: XML string containing bot configuration
            
        Returns:
            Dict[str, Any]: Bot configuration dictionary
        """
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        try:
            # Parse XML
            root = ET.fromstring(xml_str)
            
            # Initialize config
            config = {}
            
            # Parse settings
            settings = root.find('settings')
            if settings is not None:
                for setting in settings:
                    # Convert value to appropriate type
                    value = setting.text.strip() if setting.text else ""
                    
                    # Try to convert to numeric types if possible
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        # Handle boolean values
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                    
                    config[setting.tag] = value
            
            # Parse trading days (if present)
            trading_days = root.find('trading_days')
            if trading_days is not None:
                days = []
                for day in trading_days:
                    days.append(day.text.strip() if day.text else "")
                config['trading_days'] = days
            
            # Parse filters (if present)
            filters = root.find('filters')
            if filters is not None:
                for filter_elem in filters:
                    enabled = filter_elem.get('enabled', 'false').lower() == 'true'
                    config[f'use_{filter_elem.tag}_filter'] = enabled
            
            # Validate and fill in missing values
            return self.validate_config(config)
            
        except Exception as e:
            print(f"Error parsing XML: {e}")
            return self.get_default_config()
    
    def generate_bot_xml(self, config: Dict[str, Any]) -> str:
        """
        Generate an XML string from a bot configuration
        
        Args:
            config: Bot configuration dictionary
            
        Returns:
            str: XML string representation of the configuration
        """
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        try:
            # Create root element
            root = ET.Element('bot_config')
            
            # Add version
            root.set('version', '1.0')
            
            # Create settings element
            settings = ET.SubElement(root, 'settings')
            
            # Add settings
            for key, value in config.items():
                # Skip special elements that will be handled separately
                if key in ['trading_days', 'saved_at', 'exported_at', 'imported_at']:
                    continue
                
                # Skip filter settings that will be handled separately
                if key.startswith('use_') and key.endswith('_filter'):
                    continue
                
                # Add setting
                setting = ET.SubElement(settings, key)
                setting.text = str(value)
            
            # Add trading days if present
            if 'trading_days' in config and isinstance(config['trading_days'], list):
                trading_days = ET.SubElement(root, 'trading_days')
                for day in config['trading_days']:
                    day_elem = ET.SubElement(trading_days, 'day')
                    day_elem.text = day
            
            # Add filters
            filters = ET.SubElement(root, 'filters')
            
            # Add filter elements
            for key, value in config.items():
                if key.startswith('use_') and key.endswith('_filter'):
                    filter_name = key[4:-7]  # Remove 'use_' prefix and '_filter' suffix
                    filter_elem = ET.SubElement(filters, filter_name)
                    filter_elem.set('enabled', str(value).lower())
            
            # Convert to string with pretty formatting
            rough_string = ET.tostring(root, 'utf-8')
            parsed = minidom.parseString(rough_string)
            pretty_xml = parsed.toprettyxml(indent="  ")
            
            return pretty_xml
            
        except Exception as e:
            print(f"Error generating XML: {e}")
            return ""
