"""
Contains the main PySide6 QMainWindow class `ScraperApp`
and all its associated UI setup and event handling logic.
"""

# === BOOTSTRAPPER: STAGE 1 ===
# Import *only* standard libraries needed for the dependency check.
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
import binascii
import re
import shutil 
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

# === BOOTSTRAPPER: STAGE 2 ===
# Set up a minimal console logger *before* doing anything else.
# The full GUI/file logger will be initialized later in setup_logging().
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# === BOOTSTRAPPER: STAGE 3 ===
# Import the installer function from utils.py (which is safe, as it only
# uses standard libraries) and run the dependency check.
try:
    from utils import install_package, SCRIPT_DIR
except ImportError as e:
    logging.critical(f"Failed to import 'utils.py'. Make sure it is in the same directory. Error: {e}")
    print(f"FATAL: Failed to import 'utils.py'. Make sure it is in the same directory. Error: {e}")
    time.sleep(5)
    sys.exit(1)

logging.info("Checking for required Python packages...")
# We'll check for all third-party packages, not just scapy.
packages_to_check = {
    'PySide6': 'PySide6',
    'requests': 'requests',
    'psutil': 'psutil',
    'scapy': 'scapy',
    'curl_cffi': 'curl_cffi',
    'beautifulsoup4': 'bs4',
    'lxml': 'lxml'
}

installation_happened = False
for pkg_name, import_name in packages_to_check.items():
    if install_package(pkg_name, import_name):
        installation_happened = True

# === BOOTSTRAPPER: STAGE 4 ===
# If anything was installed, the script *must* restart to load them.
if installation_happened:
    logging.warning("One or more required packages were installed.")
    print("\n\n" + "="*50)
    print(" PACKAGES INSTALLED")
    print(" One or more required Python packages were just installed.")
    print(" Please close this window and run the script again.")
    print("="*50 + "\n\n")
    time.sleep(5) # Give user time to read
    sys.exit(0) # Clean exit

logging.info("All packages are present. Proceeding with application load...")

# === BOOTSTRAPPER: STAGE 5 ===
# All packages are confirmed. Now we can safely import them.

# Scapy/Npcap Imports
try:
    if sys.platform == "win32":
        from scapy.arch.windows import get_windows_if_list
        import scapy.all as scapy
        # --- MODIFIED: Fixed config path ---
        scapy.conf.ifaces.reload() 
        # --- END MODIFIED ---
except ImportError:
    # This should not happen, but it's a good safeguard.
    logging.critical("Scapy import failed even after check. The application cannot start.")
    sys.exit(1)
except Exception as e:
    logging.critical(f"Failed to configure scapy: {e}")
    sys.exit(1)

# PySide6 Imports
try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                   QHBoxLayout, QGroupBox, QLabel, QLineEdit,
                                   QPushButton, QTextEdit, QMessageBox, QFileDialog, QCheckBox, 
                                   QInputDialog) 
    from PySide6.QtCore import Signal, Qt, QTimer
    from PySide6.QtGui import QFont, QColor, QTextCursor, QAction
except ImportError:
    logging.critical("PySide6 import failed. The application cannot start.")
    sys.exit(1)

# Local Imports
# These are now safe because their dependencies (scapy, etc.) are loaded.
from database import DatabaseManager
from gui_components import DbViewer, QLogHandler, ScraperWorker, DataViewerDialog
# SCRIPT_DIR is already imported, but we need the other utils
from utils import extract_urls_from_text
# from network_viewer import NetworkActivityViewer  # <--- REMOVED: Will be imported later
from tor_manager import TorManager
from system_checks import check_and_install_npcap
import config_manager
import database_actions


class ScraperApp(QMainWindow):
    resume_controls = Signal()

    def __init__(self):
        super().__init__()
        
        self.script_dir = SCRIPT_DIR
        
        self.data_dir = self.script_dir / "TSData"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.CONFIG_FILE = self.data_dir / "scraper_config.json"
        
        self.setWindowTitle("Web Scraper GUI")
        self.setGeometry(100, 100, 850, 750)
        
        # --- NEW: Clear Temp Folder on launch ---
        self.clear_temp_folder()
        # --- END NEW ---
        
        # --- Refactored Managers ---
        self.tor_manager = TorManager(self.script_dir)
        self.tor_manager.kill_existing_tor_processes()
        
        self.backup_script() 
        
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.db_viewer = None
        self.scraper_thread = None
        self.network_viewer = None
        
        self.active_tasks_dict = {}
        self.active_tasks_lock = threading.Lock()

        self.setup_ui()
        self.setup_logging() 
        
        # --- Refactored Config ---
        self.load_parameters() 
        # ---

        if not check_and_install_npcap(self.script_dir, self):
             QMessageBox.critical(self, "Npcap Required",
                                  "Npcap is required for network monitoring and could not be verified. The application will now close.")
             QTimer.singleShot(100, self.close)
             return 

        # --- FIX: Import NetworkActivityViewer AFTER Npcap check ---
        try:
            from network_viewer import NetworkActivityViewer
            # Store the imported class as an attribute
            self.NetworkActivityViewer = NetworkActivityViewer
            logging.info("NetworkActivityViewer loaded successfully.")
        except ImportError as e:
            logging.critical(f"Failed to import NetworkActivityViewer (Scapy/Npcap error): {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to load network components: {e}\n\nNetwork monitor will be disabled.")
            self.network_activity_button.setEnabled(False)
        except Exception as e:
            logging.critical(f"An unknown error occurred loading NetworkActivityViewer: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to load network components: {e}\n\nNetwork monitor will be disabled.")
            self.network_activity_button.setEnabled(False)
        # --- END FIX ---

        # --- Refactored Tor Launch ---
        if self.tor_manager.ensure_local_torrc(self.overwrite_torrc_auto):
            self.tor_manager.launch_monitoring_tools()
        else:
            logging.critical("[FATAL] Tor configuration was cancelled or failed.")
            QMessageBox.critical(self, "Tor Error", "Tor configuration failed. See logs. The application will exit.")
            QTimer.singleShot(100, self.close)
            return
        
        self.tor_manager.tor_ready.connect(self.on_tor_ready)
        self.resume_controls.connect(self.on_resume_controls)
        # ---

    def clear_temp_folder(self):
        """Wipes the Temp folder and recreates it."""
        temp_dir = self.script_dir / "Temp"
        
        if temp_dir.exists():
            logging.info(f"Clearing Temp directory: {temp_dir}")
            try:
                # Forcefully remove the entire directory tree
                shutil.rmtree(temp_dir, ignore_errors=True)
                logging.info("Temp directory cleared.")
            except Exception as e:
                logging.error(f"Failed to clear Temp directory {temp_dir}: {e}")
        
        # Recreate the directory to ensure it exists for later use (e.g., Npcap download)
        try:
            temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.critical(f"FATAL: Could not create Temp directory: {e}")

    def backup_script(self):
        """Creates a timestamped backup of .py files."""
        try:
            bak_dir = self.script_dir / "bak"
            bak_dir.mkdir(parents=True, exist_ok=True)
            now_str = (Path.cwd().name + "_" + 
                       datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            backup_folder_path = bak_dir / now_str
            backup_folder_path.mkdir()

            py_files = list(self.script_dir.glob("*.py"))
            if not py_files:
                return

            for file_path in py_files:
                shutil.copy2(file_path, backup_folder_path / file_path.name)
            logging.info(f"Created backup in: {backup_folder_path}")
        except Exception as e:
            logging.error(f"Failed to create script backup: {e}")

    def setup_ui(self):
        """Builds the main user interface."""
        
        menu_bar = self.menuBar()
        
        # --- Scrapes Menu ---
        scrapes_menu = menu_bar.addMenu("Scrapes")
        self.rescape_action = QAction("Rescrape Failed", self)
        self.rescape_action.triggered.connect(lambda: self.start_scraping_thread(rescrape_mode=True))
        scrapes_menu.addAction(self.rescape_action)
        
        self.rescrape_data_action = QAction("Rescrape for page data", self)
        self.rescrape_data_action.triggered.connect(lambda: self.start_scraping_thread(rescrape_page_data_mode=True))
        scrapes_menu.addAction(self.rescrape_data_action)
        
        # --- DB Actions Menu ---
        db_menu = menu_bar.addMenu("DB Actions")
        view_db_action = QAction("View DB File", self)
        view_db_action.triggered.connect(self.open_db_viewer)
        db_menu.addAction(view_db_action)
        
        pull_keywords_action = QAction("Pull Keyword Matches", self)
        pull_keywords_action.triggered.connect(self.pull_keyword_matches)
        db_menu.addAction(pull_keywords_action)
        
        pull_top_level_action = QAction("Pull Top Level URLs", self)
        pull_top_level_action.triggered.connect(self.pull_top_level_urls)
        db_menu.addAction(pull_top_level_action)
        
        # --- RENAME: Export Links -> Export Links from DB ---
        export_links_action = QAction("Export Links from DB", self)
        export_links_action.triggered.connect(self.export_all_links)
        db_menu.addAction(export_links_action)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Parameters Group ---
        param_group = QGroupBox("Parameters")
        param_layout = QVBoxLayout()
        self.entries = {}

        db_layout = QHBoxLayout()
        db_btn = QPushButton("Database File:"); db_btn.setFixedWidth(100)
        db_btn.clicked.connect(self.select_db_file)
        self.entries['db_file'] = QLineEdit(); self.entries['db_file'].setReadOnly(True)
        db_layout.addWidget(db_btn); db_layout.addWidget(self.entries['db_file'])
        param_layout.addLayout(db_layout)

        url_file_layout = QHBoxLayout()
        url_file_btn = QPushButton("URL File:"); url_file_btn.setFixedWidth(100)
        url_file_btn.clicked.connect(self.select_url_file)
        self.url_file_display = QLineEdit(); self.url_file_display.setReadOnly(True)
        self.url_file_display.setPlaceholderText("Optional: Select a text file with starting URLs")
        clear_url_file_btn = QPushButton("Clear"); clear_url_file_btn.setFixedWidth(60)
        clear_url_file_btn.clicked.connect(self.clear_url_file_selection)
        url_file_layout.addWidget(url_file_btn)
        url_file_layout.addWidget(self.url_file_display)
        url_file_layout.addWidget(clear_url_file_btn)
        param_layout.addLayout(url_file_layout)

        self.keyword_file_layout = QHBoxLayout()
        self.keyword_file_btn = QPushButton("Keyword File:"); self.keyword_file_btn.setFixedWidth(100)
        self.keyword_file_btn.clicked.connect(self.select_keyword_file)
        self.keyword_file_display = QLineEdit(); self.keyword_file_display.setReadOnly(True)
        self.keyword_file_display.setPlaceholderText("Optional: Select a text file with keywords")
        self.clear_keyword_file_btn = QPushButton("Clear"); self.clear_keyword_file_btn.setFixedWidth(60)
        self.clear_keyword_file_btn.clicked.connect(self.clear_keyword_file)
        self.keyword_file_layout.addWidget(self.keyword_file_btn)
        self.keyword_file_layout.addWidget(self.keyword_file_display)
        self.keyword_file_layout.addWidget(self.clear_keyword_file_btn)
        param_layout.addLayout(self.keyword_file_layout)

        concurrency_layout = QHBoxLayout()
        concurrency_label = QLabel("Concurrent Requests:"); concurrency_label.setFixedWidth(120)
        self.entries['batch_size'] = QLineEdit("150") # Default value
        self.entries['batch_size'].setFixedWidth(80) 
        
        # --- FIX: Center widgets ---
        concurrency_layout.addStretch() 
        # --- END FIX ---
        
        concurrency_layout.addWidget(concurrency_label)
        concurrency_layout.addWidget(self.entries['batch_size'])
        
        self.onion_only_checkbox = QCheckBox("Only scrape .onion links")
        self.keyword_checkbox = QCheckBox("Keyword Search")
        self.keyword_checkbox.toggled.connect(self.toggle_keyword_widgets)
        
        concurrency_layout.addWidget(self.onion_only_checkbox)
        concurrency_layout.addWidget(self.keyword_checkbox)
        concurrency_layout.addStretch()
        param_layout.addLayout(concurrency_layout)
        
        checkbox_layout = QHBoxLayout()
        self.top_level_checkbox = QCheckBox("Scrape Top-Level URLs Only")
        self.titles_only_checkbox = QCheckBox("Scrape Titles Only")
        self.save_page_data_checkbox = QCheckBox("Save page data")
        self.save_page_data_checkbox.setToolTip("If unchecked, page data is only saved if a keyword matches.")
        
        # --- FIX: Center widgets ---
        checkbox_layout.addStretch()
        # --- END FIX ---

        checkbox_layout.addWidget(self.top_level_checkbox)
        checkbox_layout.addWidget(self.titles_only_checkbox)
        checkbox_layout.addWidget(self.save_page_data_checkbox)
        checkbox_layout.addStretch()
        param_layout.addLayout(checkbox_layout)

        param_group.setLayout(param_layout)
        
        self.toggle_keyword_widgets(False)

        # --- Control Buttons ---
        start_button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Scraping")
        self.start_button.clicked.connect(self.start_scraping_thread)
        self.stop_button = QPushButton("Stop Scraping")
        self.stop_button.clicked.connect(self.stop_scraping)
        
        start_button_layout.addStretch()
        start_button_layout.addWidget(self.start_button)
        start_button_layout.addWidget(self.stop_button)
        start_button_layout.addStretch()
        
        self.start_button.setEnabled(False)
        self.rescape_action.setEnabled(False) 
        self.rescrape_data_action.setEnabled(False) 
        self.stop_button.setEnabled(False)

        # --- Log Panes ---
        log_panes_layout = QHBoxLayout()
        log_group = QGroupBox("Log"); log_layout = QVBoxLayout()
        self.log_viewer = QTextEdit(); self.log_viewer.setReadOnly(True)
        log_layout.addWidget(self.log_viewer); log_group.setLayout(log_layout)
        error_log_group = QGroupBox("Errors"); error_log_layout = QVBoxLayout()
        self.error_viewer = QTextEdit(); self.error_viewer.setReadOnly(True)
        error_log_layout.addWidget(self.error_viewer); error_log_group.setLayout(error_log_layout)
        log_panes_layout.addWidget(log_group, 3); log_panes_layout.addWidget(error_log_group, 1)

        # --- Bottom Buttons ---
        bottom_button_layout = QHBoxLayout()
        
        self.network_activity_button = QPushButton("Network Activity")
        self.network_activity_button.clicked.connect(self.open_network_viewer)
        self.network_activity_button.setStyleSheet("background-color: #0078D4; color: white; padding: 5px;")
        self.network_activity_button.setToolTip("Shows active scrape tasks and total network I/O for the Tor process.")
        self.network_activity_button.setEnabled(False) 
        bottom_button_layout.addWidget(self.network_activity_button)
        
        bottom_button_layout.addStretch() 
        
        self.new_identity_button = QPushButton("New Tor Identity")
        self.new_identity_button.clicked.connect(self.request_new_identity_thread)
        self.new_identity_button.setEnabled(False)
        
        self.reload_button = QPushButton("Reload Script")
        self.reload_button.clicked.connect(self.reload_script)
        
        bottom_button_layout.addWidget(self.new_identity_button)
        bottom_button_layout.addWidget(self.reload_button)

        main_layout.addWidget(param_group)
        main_layout.addLayout(start_button_layout)
        main_layout.addLayout(log_panes_layout)
        main_layout.addLayout(bottom_button_layout)

    def on_tor_ready(self):
        """Slot to enable controls once Tor has bootstrapped."""
        logging.info("Controls enabled. Ready to scrape.")
        self.start_button.setEnabled(True)
        self.rescape_action.setEnabled(True)
        self.rescrape_data_action.setEnabled(True)
        self.new_identity_button.setEnabled(True)
        self.network_activity_button.setEnabled(True) 

    def on_resume_controls(self):
        """Slot to re-enable controls after a pause (like new identity)."""
        is_scraping = self.scraper_thread and self.scraper_thread.isRunning()
        self.new_identity_button.setEnabled(True)
        self.stop_button.setEnabled(is_scraping)

    def open_network_viewer(self):
        """Opens the Network Activity monitoring dialog."""
        
        # --- FIX: Check if the class was loaded successfully in __init__ ---
        if not hasattr(self, 'NetworkActivityViewer'):
            QMessageBox.warning(self, "Error", "Network Activity Viewer component failed to load on startup.")
            return
        # --- END FIX ---

        if not self.tor_manager.tor_process:
            QMessageBox.warning(self, "Error", "Tor process object does not exist.")
            return

        try:
            # --- ADDED: psutil import ---
            import psutil
            # --- END ADDED ---
            tor_ps_process = psutil.Process(self.tor_manager.tor_process.pid)
            if not tor_ps_process.is_running():
                QMessageBox.warning(self, "Error", "Tor process has ended.")
                return
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, "Error", "Tor process not found (PID invalid).")
            return
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred while checking the Tor process: {e}")
            return
            
        if self.network_viewer is None:
            try:
                # --- FIX: Use the class attribute ---
                self.network_viewer = self.NetworkActivityViewer(
                    self.active_tasks_dict, 
                    self.active_tasks_lock, 
                    self.tor_manager.tor_process.pid, 
                    self
                )
                # --- END FIX ---
            except Exception as e:
                logging.error(f"Failed to create NetworkActivityViewer: {e}\n{traceback.format_exc()}")
                QMessageBox.critical(self, "Network Viewer Error", f"Failed to initialize network sniffer:\n\n{e}\n\nMake sure Npcap is installed correctly.")
                return

        if not self.network_viewer.isVisible():
            self.network_viewer.show() 
        
        self.network_viewer.raise_() 
        self.network_viewer.activateWindow() 
            
    def open_db_viewer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Database File to View", "", "SQLite Database (*.sqlite *.db)")
        if path:
            if self.db_viewer and self.db_viewer.isVisible():
                self.db_viewer.close()
            try:
                # Pass the main DB file path to the viewer
                self.db_viewer = DbViewer(path, self)
                self.db_viewer.show()
            except Exception as e:
                logging.error(f"Failed to open DB Viewer: {e}")
                QMessageBox.critical(self, "DB Viewer Error", f"An error occurred: {e}\n\n{traceback.format_exc()}")

    def pull_keyword_matches(self):
        """Pulls all rows with keyword matches into a temp DB, clears memory, and displays the DB in a viewer."""
        db_path = self.entries['db_file'].text()
        if not db_path:
            QMessageBox.critical(self, "Error", "A 'Database File' must be selected first.")
            return
            
        # 1. Get Keywords
        keywords = None
        if self.keyword_checkbox.isChecked():
            # Check for valid keyword file path
            if not hasattr(self, 'keyword_file_path') or not self.keyword_file_path or not os.path.exists(self.keyword_file_path):
                QMessageBox.critical(self, "Error", "Keyword Search is checked, but no valid keyword file is selected.")
                return
            
            # Attempt to load keywords
            try:
                with open(self.keyword_file_path, 'r', encoding='utf-8') as f:
                    keywords = [line.strip() for line in f if line.strip()]
                
                if not keywords:
                    logging.warning("Keyword file is empty or contains no valid keywords.")
                    QMessageBox.warning(self, "Warning", "Keyword file is empty or contains no valid keywords.")
                    return # Exit if file is empty
                else:
                    logging.info(f"Loaded {len(keywords)} keywords from {os.path.basename(self.keyword_file_path)}.")
                    
            except Exception as e:
                logging.error(f"Failed to read keyword file: {e}")
                QMessageBox.critical(self, "Error", f"Failed to read keyword file: {e}")
                return
        
        # --- CRITICAL CHECK: If keywords don't exist, stop. ---
        if not keywords:
            QMessageBox.critical(self, "Error", "Keyword Search is not enabled or keywords could not be loaded.")
            return

        # 2. PROMPT FOR THRESHOLD (Standard synchronous call, protected by try/except)
        logging.info("Attempting to launch Keyword Match Threshold dialogue box.")
        
        try:
            # --- FIX: Removed unsupported keyword 'min=1' ---
            i, ok = QInputDialog.getInt(self, "Keyword Match Threshold",
                                        "Enter the minimum number of unique keyword matches required per site:", 
                                        value=1) 
            # -------------------------------------------------------------------
        except Exception as e:
            # If it fails here, the application cannot proceed safely. Log and exit cleanly.
            logging.critical(f"FATAL DIALOG EXECUTION ERROR: {e}")
            QMessageBox.critical(self, "Dialog Error", f"Failed to run input dialog. Check logs for details.")
            return

        if not ok:
            logging.info("Keyword Match Threshold dialogue cancelled by user.")
            return # User cancelled

        match_threshold = i
        logging.info(f"Using keyword match threshold: {match_threshold}")
            
        # 3. Pull data, write to temp DB, and get the temp file path
        temp_db_path = database_actions.pull_keyword_matches_to_temp_db(
            db_path, self.script_dir, keywords, match_threshold, self
        )
        
        if not temp_db_path:
            # Error occurred or no matches found (message shown inside pull_keyword_matches_to_temp_db)
            return
            
        # 4. Open the paginated DbViewer using the temp DB file path
        logging.info(f"Opening DbViewer for temporary keyword file: {temp_db_path}")
        
        # Close existing viewer if open
        if self.db_viewer and self.db_viewer.isVisible():
            self.db_viewer.close()
            
        try:
            # We now use the standard DbViewer, which handles pagination and low memory usage
            self.db_viewer = DbViewer(temp_db_path, self)
            self.db_viewer.setWindowTitle(f"Keyword Matches (Threshold: {match_threshold}): {os.path.basename(temp_db_path)}")
            self.db_viewer.show()
        except Exception as e:
            logging.error(f"Failed to open DB Viewer for keyword matches: {e}")
            QMessageBox.critical(self, "DB Viewer Error", f"An error occurred: {e}\n\n{traceback.format_exc()}")

    def select_db_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.Option.DontConfirmOverwrite
        
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Select or Create Database File", 
            str(self.data_dir), # Start in the data directory
            "SQLite Database (*.sqlite *.db)", 
            options=options
        )
        if path:
            self.entries['db_file'].setText(path)

    def select_url_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select URL File", str(self.data_dir), "Text Files (*.txt)")
        if path:
            self.url_file_path = path
            self.url_file_display.setText(path)

    def clear_url_file_selection(self):
        self.url_file_path = None
        self.url_file_display.clear()

    def select_keyword_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Keyword File", str(self.data_dir), "Text Files (*.txt)")
        if path:
            self.keyword_file_path = path
            self.keyword_file_display.setText(path)

    def clear_keyword_file(self):
        self.keyword_file_path = None
        self.keyword_file_display.clear()

    def toggle_keyword_widgets(self, checked):
        self.keyword_file_btn.setEnabled(checked)
        self.keyword_file_display.setEnabled(checked)
        self.clear_keyword_file_btn.setEnabled(checked)

    def append_log_message(self, record):
        color_map = {
            'INFO': QColor('green'), 
            'WARNING': QColor('orange'), 
            'ERROR': QColor('red'),
            'CRITICAL': QColor('red'),
            'DEBUG': QColor('grey')
        }
        
        message = self.gui_handler.format(record).strip()
        color = color_map.get(record.levelname, QColor('green')) 

        red_flag_keywords = [
            "--- Batch", "Scraping finished", "No new links discovered", 
            "Starting in", "failed links", "--- Processing batch", 
            "No failed links found", "Adding/updating", "[KEYWORD HIT]",
            "Parsed Title:", "Iteration", "Waiting for queue", "Producer finished"
        ]

        if record.levelno == logging.INFO and any(keyword in message for keyword in red_flag_keywords):
            color = QColor('red')
        
        if message.startswith("[SUCCESS]"):
            color = QColor('cyan')

        log_widget = self.error_viewer if record.levelno >= logging.WARNING else self.log_viewer
        
        cursor = log_widget.textCursor()
        cursor.movePosition(QTextCursor.End)
        char_format = cursor.charFormat()
        char_format.setForeground(color)
        
        if record.levelno == logging.CRITICAL:
            char_format.setFontWeight(QFont.Bold)
            
        cursor.setCharFormat(char_format)
        cursor.insertText(message + '\n')
        log_widget.moveCursor(QTextCursor.End) 

    def setup_logging(self):
        """Set up the GUI and File loggers."""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        log_file = self.data_dir / "scraper_debug.log"
        
        logger = logging.getLogger()
        # --- MODIFIED: Clear bootstrap basicConfig ---
        if logger.hasHandlers(): 
            logger.handlers.clear()
        # --- END MODIFIED ---
        logger.setLevel(logging.DEBUG) 
        
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(logging.DEBUG) 
        logger.addHandler(file_handler)
        
        self.gui_handler = QLogHandler()
        self.gui_handler.setFormatter(logging.Formatter('%(message)s'))
        self.gui_handler.setLevel(logging.INFO) 
        self.gui_handler.log_received.connect(self.append_log_message)
        logger.addHandler(self.gui_handler)
        
        # --- MODIFIED: Log that the main app logger is ready ---
        logging.info("Main application logger initialized.")
        # --- END MODIFIED ---

    def save_parameters(self):
        params_to_save = {
            'db_file': self.entries['db_file'].text(),
            'batch_size': self.entries['batch_size'].text(),
            'onion_only': self.onion_only_checkbox.isChecked(),
            'top_level_only': self.top_level_checkbox.isChecked(),
            'titles_only': self.titles_only_checkbox.isChecked(),
            'keyword_search': self.keyword_checkbox.isChecked(),
            'save_page_data': self.save_page_data_checkbox.isChecked(),
            'url_file': self.url_file_path,
            'keyword_file': self.keyword_file_path,
            'overwrite_torrc_auto': self.overwrite_torrc_auto
        }
        config_manager.save_parameters(self.CONFIG_FILE, params_to_save)

    def load_parameters(self):
        params = config_manager.load_parameters(self.CONFIG_FILE)
        
        self.entries['db_file'].setText(params['db_file'])
        self.entries['batch_size'].setText(params['batch_size'])
        self.onion_only_checkbox.setChecked(params['onion_only'])
        self.top_level_checkbox.setChecked(params['top_level_only'])
        self.titles_only_checkbox.setChecked(params['titles_only'])
        self.keyword_checkbox.setChecked(params['keyword_search'])
        self.save_page_data_checkbox.setChecked(params['save_page_data'])
        self.url_file_path = params['url_file']
        if self.url_file_path:
            self.url_file_display.setText(self.url_file_path)
        self.keyword_file_path = params['keyword_file']
        if self.keyword_file_path:
            self.keyword_file_display.setText(self.keyword_file_path)
        self.overwrite_torrc_auto = params['overwrite_torrc_auto']
        
        self.toggle_keyword_widgets(self.keyword_checkbox.isChecked())

    def reload_script(self):
        logging.warning("[WARN] Reloading script...")
        self.on_closing(reloading=True)
        time.sleep(0.5)
        os.execv(sys.executable, ['python'] + sys.argv)

    def closeEvent(self, event):
        self.on_closing()
        event.accept()

    def on_closing(self, reloading=False):
        self.save_parameters()
        if self.network_viewer:
            self.network_viewer.close()
        self.tor_manager.terminate_tor()
        if not reloading: QApplication.quit()

    def pull_top_level_urls(self):
        db_path = self.entries['db_file'].text()
        if not db_path:
            QMessageBox.critical(self, "Error", "A 'Database File' must be selected first.")
            return

        # --- FIX: Automate file naming ---
        base_name, ext = os.path.splitext(db_path)
        new_db_path = f"{base_name}_TOP{ext}"
        logging.info(f"Pulling top-level URLs to: {new_db_path}")
        # --- END FIX ---
        
        # Call the action
        db_action_success = database_actions.pull_top_level_urls(db_path, new_db_path, self)
        
        # --- FIX: Auto-open the new DB file ---
        if db_action_success:
            if self.db_viewer and self.db_viewer.isVisible():
                self.db_viewer.close()
            try:
                self.db_viewer = DbViewer(new_db_path, self)
                self.db_viewer.setWindowTitle(f"Top-Level URLs: {os.path.basename(new_db_path)}")
                self.db_viewer.show()
            except Exception as e:
                logging.error(f"Failed to auto-open new DB Viewer: {e}")
                QMessageBox.critical(self, "DB Viewer Error", f"An error occurred: {e}\n\n{traceback.format_exc()}")
        # --- END FIX ---

    def export_all_links(self):
        db_path, _ = QFileDialog.getOpenFileName(self, "Select Database File to Export From", str(self.data_dir), "SQLite Database (*.sqlite *.db)")
        if not db_path:
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Links As", str(self.data_dir), "Text Files (*.txt)")
        if not save_path:
            return

        database_actions.export_all_links(db_path, save_path, self)

    def request_new_identity_thread(self):
        is_scraping = self.scraper_thread and self.scraper_thread.isRunning()
        if is_scraping:
            self.pause_event.set()
        
        self.new_identity_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        # Run in a new thread
        threading.Thread(target=self._new_identity_worker, daemon=True).start()

    def _new_identity_worker(self):
        self.tor_manager.request_new_identity()
        time.sleep(5)  
        self.pause_event.clear()
        self.resume_controls.emit()

    def start_scraping_thread(self, rescrape_mode=False, rescrape_page_data_mode=False):
        if not self.entries['db_file'].text():
            QMessageBox.critical(self, "Error", "A 'Database File' must be selected first.")
            return
        
        try:
            batch_size = int(self.entries['batch_size'].text())
            if batch_size <= 0:
                QMessageBox.critical(self, "Error", "Concurrent Requests must be a positive number.")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Concurrent Requests must be a valid number.")
            return

        self.save_parameters()

        urls = []
        if hasattr(self, 'url_file_path') and self.url_file_path and os.path.exists(self.url_file_path):
            try:
                with open(self.url_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                urls = extract_urls_from_text(content)
                logging.info(f"Extracted {len(urls)} unique URLs from {os.path.basename(self.url_file_path)}.")
            except Exception as e:
                logging.error(f"Failed to read or parse URL file: {e}")
                QMessageBox.critical(self, "Error", f"Failed to read URL file: {e}")
                return
        
        keywords = None
        if self.keyword_checkbox.isChecked():
            if not hasattr(self, 'keyword_file_path') or not self.keyword_file_path or not os.path.exists(self.keyword_file_path):
                QMessageBox.critical(self, "Error", "Keyword Search is checked, but no valid keyword file is selected.")
                return
            try:
                with open(self.keyword_file_path, 'r', encoding='utf-8') as f:
                    keywords = [line.strip() for line in f if line.strip()]
                if not keywords:
                    QMessageBox.warning(self, "Warning", "Keyword file is empty.")
                    keywords = None
                else:
                    logging.info(f"Loaded {len(keywords)} keywords from {os.path.basename(self.keyword_file_path)}.")
            except Exception as e:
                logging.error(f"Failed to read or parse keyword file: {e}")
                QMessageBox.critical(self, "Error", f"Failed to read keyword file: {e}")
                return

        self.start_button.setEnabled(False)
        self.rescape_action.setEnabled(False)
        self.rescrape_data_action.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        self.stop_event.clear()
        self.pause_event.clear()
        
        with self.active_tasks_lock:
            self.active_tasks_dict.clear()
        
        save_all_page_data = self.save_page_data_checkbox.isChecked()
        args = argparse.Namespace(
            urls=urls, 
            db_file=self.entries['db_file'].text(), 
            batch_size=batch_size,
            save_all_page_data=save_all_page_data
        )
        
        onion_only_mode = self.onion_only_checkbox.isChecked()
        top_level_only_mode = self.top_level_checkbox.isChecked()
        titles_only_mode = self.titles_only_checkbox.isChecked()
        
        self.scraper_thread = ScraperWorker(
            args, self.stop_event, self.pause_event, 
            self.active_tasks_dict, self.active_tasks_lock, 
            rescrape_mode, top_level_only_mode, onion_only_mode, 
            titles_only_mode, keywords, save_all_page_data,
            rescrape_page_data_mode
        )
        self.scraper_thread.finished.connect(self.on_scraping_finished)
        self.scraper_thread.start()

    def stop_scraping(self):
        logging.warning("[WARN] Stop button clicked. Requesting scraper to stop...")
        self.stop_event.set()
        self.pause_event.clear() 
        # Crucially, stop_button is re-enabled in on_scraping_finished
        self.stop_button.setEnabled(False)

    def on_scraping_finished(self):
        # --- FIX 3: Ensure controls are re-enabled after thread finishes ---
        self.start_button.setEnabled(True)
        self.rescape_action.setEnabled(True)
        self.rescrape_data_action.setEnabled(True)
        self.stop_button.setEnabled(False)
        # --- END FIX ---