import json
import os

_config_cache = {}
_config_file_path = "user.config"

def get_config(key, default=None):
    """
    Retrieves a configuration value from the user.config file, using a cache.

    Args:
        key (str): The key of the configuration value to retrieve.
        default (any, optional): The default value to return if the key is not found. Defaults to None.

    Returns:
        any: The configuration value if found, otherwise the default value.
    """
    global _config_cache

    if not _config_cache:
        try:
            if os.path.exists(_config_file_path):
                with open(_config_file_path, "r", encoding="utf-8") as f:
                    _config_cache = json.load(f)
            else:
                print(f"Error: {_config_file_path} file not found.")
                return default
        except json.JSONDecodeError:
            print(f"Error: {_config_file_path} file is not a valid JSON.")
            return default
        except FileNotFoundError:
            print(f"Error: {_config_file_path} file not found.")
            return default

    return _config_cache.get(key, default)
