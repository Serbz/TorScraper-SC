"""
Utility functions, constants, and global script directory setup.
"""

import os
import sys
import argparse
import random
import traceback
import subprocess
import threading
import time
import socket
import json
import logging
import sqlite3
import binascii
import re2 as re # <-- MODIFIED: Using re2
import shutil
import importlib.util # <-- ADDED for robust package checking
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse
from pathlib import Path # Used for path manipulation

# --- Library Installation ---
def install_package(package_name, import_name=None):
    """
    Tries to import a package. If it fails, installs it via pip.
    Returns True if an installation was attempted, False otherwise.
    """
    if import_name is None:
        import_name = package_name
    
    # --- MODIFIED: Use find_spec for a more reliable check ---
    spec = importlib.util.find_spec(import_name)
    if spec is not None:
        return False # Package is found
    # --- END MODIFIED ---

    # Package not found, proceed with installation
    logging.warning(f"Library '{import_name}' not found. Attempting to install '{package_name}'...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logging.info(f"Successfully installed '{package_name}'. A restart is required.")
        return True # Installation occurred
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install '{package_name}'. Please install it manually using 'pip install {package_name}'.")
        logging.error(f"Error: {e}")
        sys.exit(1)

# --- Helper Functions & Constants ---

def get_script_dir():
    """Gets the script's directory, handling frozen executables."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

# Define script directory globally for other modules to import
SCRIPT_DIR = get_script_dir()

# --- FIX: Regex for filtering junk URLs ---
# This looks for any single character (like 'a' or '7') repeated 8 or more times
JUNK_URL_REGEX = re.compile(r'(.)\1{7,}')
# --- END FIX ---

def is_junk_url(url):
    """Checks if a URL is likely junk based on repetitive characters in the domain."""
    if not url:
        return False
    try:
        # We only check the domain part (netloc) for the repetitive pattern
        netloc = urlparse(url).netloc
        if JUNK_URL_REGEX.search(netloc):
            return True
    except Exception:
        return False # Fail-safe on malformed URLs
    return False

def get_top_level_url(url):
    """Extracts the scheme and netloc to get the base URL and normalizes it."""
    try:
        parsed = urlparse(url)
        # Reconstruct the URL with only the scheme and netloc (domain)
        base_url = urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
        return base_url.rstrip('/')
    except Exception:
        # Return None if the URL is malformed or cannot be parsed
        return None

def get_tor_auth_cookie_path():
    """Finds the path to the Tor control auth cookie in the local tor_data."""
    # This now points to the local portable data directory
    return SCRIPT_DIR / "tor" / "tor_data" / "control_auth_cookie"

def extract_urls_from_text(text):
    """Uses regex to find all http/httpsURLs in a block of text."""
    # This regex finds URLs starting with http://, https://, or www.
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    found_urls = url_pattern.findall(text)
    # Add http:// to www links that are missing it
    normalized_urls = [f"http://{url}" if url.startswith('www.') else url for url in found_urls]
    return list(set(normalized_urls)) # Return unique URLs

# --- MODE Constants (Moved from gui_components.py) ---
MODE_PAGINATE = 0
MODE_PULL_TOP_LEVEL = 1
MODE_PULL_KEYWORDS = 2
# --- END MODE Constants ---

# --- Scraper Constants ---
PROXIES = [
    'socks5h://127.0.0.1:9100', 'socks5h://127.0.0.1:9101', 'socks5h://127.0.0.1:9102',
    'socks5h://127.0.0.1:9103', 'socks5h://127.0.0.1:9104', 'socks5h://127.0.0.1:9105',
    'socks5h://127.0.0.1:9106',
]
HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}
