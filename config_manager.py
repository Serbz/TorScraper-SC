"""
Manages loading and saving the JSON configuration file.
"""

import json
import logging
import os

def save_parameters(config_file, settings_dict):
    """Saves the provided settings dictionary to the config file."""
    try:
        with open(config_file, 'w') as f:
            json.dump(settings_dict, f, indent=4)
        logging.info("[INFO] Parameters saved.")
    except Exception as e:
        logging.error(f"[ERROR] Error saving parameters: {e}")

def load_parameters(config_file):
    """Loads settings from the config file if it exists."""
    defaults = {
        'db_file': '',
        'batch_size': '150',
        'onion_only': False,
        'top_level_only': False,
        'titles_only': False,
        'keyword_search': False,
        'save_page_data': 'Keyword Match', # <-- Changed from boolean
        'url_file': None,
        'keyword_file': None,
        'overwrite_torrc_auto': False
    }
    
    if not os.path.exists(config_file):
        return defaults

    try:
        with open(config_file, 'r') as f:
            saved_params = json.load(f)
        
        # Merge saved params with defaults to ensure all keys exist
        defaults.update(saved_params)
        
        # --- Compatibility for old boolean 'save_page_data' ---
        save_mode = defaults.get('save_page_data')
        if isinstance(save_mode, bool):
            if save_mode == True:
                defaults['save_page_data'] = "All"
            else:
                defaults['save_page_data'] = "Keyword Match"
        # --- End Compatibility ---

        logging.info("[INFO] Parameters loaded from previous session.")
        
    except Exception as e:
        logging.error(f"[ERROR] Error loading parameters: {e}")
    
    return defaults
