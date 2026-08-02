#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automatic Configuration File Loader for ACME

This module provides automatic discovery and loading of configuration files
from standard locations with support for environment variable overrides.
"""

import os
import sys
import json
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


class ConfigLoadError(Exception):
    """Exception raised when config loading fails."""
    pass


class ConfigLoader:
    """
    Automatic configuration file loader.
    
    Searches for configuration files in standard locations and loads them
    in order of precedence, with environment variables taking highest priority.
    """
    
    # Default search paths in order of precedence
    DEFAULT_SEARCH_PATHS = [
        './acme.yaml',                          # Current directory
        './acme.json',
        './.env',
        os.path.expanduser('~/.acme/config.yaml'),     # User home
        os.path.expanduser('~/.acme/config.json'),
        os.path.expanduser('~/.acmerc'),
        '/etc/acme/config.yaml',                # System-wide
        '/etc/acme/config.json',
    ]
    
    def __init__(self, config_paths=None, env_var='ACME_CONFIG'):
        """
        Initialize the config loader.
        
        Args:
            config_paths: List of config file paths to search. 
                         Defaults to DEFAULT_SEARCH_PATHS.
            env_var: Environment variable name to check for config file override.
                    Defaults to 'ACME_CONFIG'.
        """
        self.config_paths = config_paths or self.DEFAULT_SEARCH_PATHS
        self.env_var = env_var
        self.config = {}
        self.config_file_loaded = None
        
    def load(self, required=False):
        """
        Automatically load configuration from files and environment.
        
        Searches for config files in order and loads the first one found.
        Environment variable override takes precedence.
        
        Args:
            required: If True, raises ConfigLoadError if no config file found.
                     If False, returns empty dict.
        
        Returns:
            Dictionary containing loaded configuration.
            
        Raises:
            ConfigLoadError: If required=True and no config file found,
                           or if there's an error parsing the config file.
        """
        # Check for environment variable override
        env_config_path = os.getenv(self.env_var)
        if env_config_path:
            return self._load_file(env_config_path, from_env=True)
        
        # Search default paths
        for path in self.config_paths:
            if os.path.exists(path):
                return self._load_file(path)
        
        # No config file found
        if required:
            paths_str = '\n  '.join(self.config_paths)
            raise ConfigLoadError(
                f"No configuration file found. Searched:\n  {paths_str}\n"
                f"Set {self.env_var} environment variable to override."
            )
        
        return {}
    
    def _load_file(self, path, from_env=False):
        """
        Load a specific configuration file.
        
        Args:
            path: Path to the config file.
            from_env: Whether this path came from environment variable.
        
        Returns:
            Dictionary containing loaded configuration.
            
        Raises:
            ConfigLoadError: If there's an error reading or parsing the file.
        """
        try:
            path = os.path.expanduser(path)
            
            if not os.path.exists(path):
                raise ConfigLoadError(f"Config file not found: {path}")
            
            if not os.path.isfile(path):
                raise ConfigLoadError(f"Config path is not a file: {path}")
            
            # Determine file type and load accordingly
            if path.endswith('.yaml') or path.endswith('.yml'):
                config = self._load_yaml(path)
            elif path.endswith('.json'):
                config = self._load_json(path)
            elif path.endswith('.env') or path.endswith('rc'):
                config = self._load_env(path)
            else:
                # Try to detect format by content
                config = self._load_auto(path)
            
            source = f"environment variable {self.env_var}" if from_env else path
            print(f"[INFO] Configuration loaded from: {source}")
            
            self.config = config
            self.config_file_loaded = path
            return config
            
        except ConfigLoadError:
            raise
        except Exception as e:
            raise ConfigLoadError(f"Error loading config from {path}: {str(e)}")
    
    def _load_yaml(self, path):
        """Load YAML configuration file."""
        if not HAS_YAML:
            raise ConfigLoadError(
                "YAML support not available. Install PyYAML: pip install pyyaml"
            )
        
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _load_json(self, path):
        """Load JSON configuration file."""
        with open(path, 'r') as f:
            return json.load(f)
    
    def _load_env(self, path):
        """Load .env configuration file."""
        config = {}
        
        if HAS_DOTENV:
            load_dotenv(path)
        
        # Parse the .env file manually for consistent behavior
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    config[key] = value
        
        return config
    
    def _load_auto(self, path):
        """Attempt to auto-detect and load config file."""
        with open(path, 'r') as f:
            content = f.read().strip()
        
        # Try JSON first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try YAML if available
        if HAS_YAML:
            try:
                return yaml.safe_load(content) or {}
            except yaml.YAMLError:
                pass
        
        # Try as .env format
        config = {}
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
        
        if config:
            return config
        
        raise ConfigLoadError(
            f"Unable to determine config format for {path}. "
            "Use .yaml, .json, or .env extension."
        )
    
    def get(self, key, default=None):
        """Get a configuration value by key."""
        return self.config.get(key, default)
    
    def __getitem__(self, key):
        """Get a configuration value using subscript notation."""
        return self.config[key]
    
    def __contains__(self, key):
        """Check if a key exists in the configuration."""
        return key in self.config
    
    def __repr__(self):
        """String representation of the config."""
        return f"ConfigLoader(loaded_from='{self.config_file_loaded}', " \
               f"config_keys={list(self.config.keys())})"


def load_config(required=False, config_paths=None, env_var='ACME_CONFIG'):
    """
    Convenience function to load configuration automatically.
    
    Args:
        required: If True, raises ConfigLoadError if no config file found.
        config_paths: List of config file paths to search.
        env_var: Environment variable name for config file override.
    
    Returns:
        Dictionary containing loaded configuration.
    """
    loader = ConfigLoader(config_paths=config_paths, env_var=env_var)
    return loader.load(required=required)


if __name__ == '__main__':
    # Example usage
    try:
        loader = ConfigLoader()
        config = loader.load()
        
        print(f"\nLoaded Configuration ({len(config)} keys):")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        print(f"\nLoader Info: {loader}")
        
    except ConfigLoadError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
