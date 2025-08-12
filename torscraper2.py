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
from urllib.parse import urljoin, urlparse

# --- Library Installation ---
def install_package(package_name, import_name=None):
    """Tries to import a package, installing it if it fails."""
    if import_name is None:
        import_name = package_name
    try:
        __import__(import_name)
    except ImportError:
        logging.warning(f"Library '{import_name}' not found. Attempting to install '{package_name}'...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install '{package_name}'. Please install it manually using 'pip install {package_name}'.")
            logging.error(f"Error: {e}")
            sys.exit(1)

# --- Main Imports ---
install_package('numpy')
install_package('beautifulsoup4', 'bs4')
install_package('curl_cffi')
install_package('asyncio')
install_package('PySide6')


import numpy as np
import asyncio
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QGroupBox, QLabel, QLineEdit, 
                               QPushButton, QTextEdit, QMessageBox, QFileDialog, QDialog)
from PySide6.QtCore import QObject, Signal, QThread, Qt
from PySide6.QtGui import QColor, QTextCursor

# --- Database Manager ---
class DatabaseManager:
    """Handles all SQLite database operations."""
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        """Creates the 'links' table if it doesn't exist."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    scraped INTEGER DEFAULT 0
                )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS url_index ON links (url)")

    def add_links(self, links):
        """Adds a list of new links to the database, ignoring duplicates."""
        with self.conn:
            self.conn.executemany("INSERT OR IGNORE INTO links (url) VALUES (?)", [(link,) for link in links])

    def get_unscraped_links(self, limit=100):
        """Gets a batch of unscraped links."""
        with self.conn:
            cursor = self.conn.execute("SELECT url FROM links WHERE scraped = 0 LIMIT ?", (limit,))
            return [row[0] for row in cursor.fetchall()]

    def mark_as_scraped(self, url):
        """Marks a specific URL as scraped."""
        with self.conn:
            self.conn.execute("UPDATE links SET scraped = 1 WHERE url = ?", (url,))

    def get_total_link_count(self):
        """Gets the total number of unique links in the database."""
        with self.conn:
            return self.conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]

    def close(self):
        self.conn.close()

# --- Scraper Core Logic ---

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

async def get_data(url):
    """Asynchronously fetches the content of a URL."""
    chosen_proxy = random.choice(PROXIES)
    logging.debug(f"Attempting to fetch {url} using proxy {chosen_proxy}")
    try:
        async with AsyncSession() as session:
            response = await session.get(url, timeout=60, headers=HEADERS, proxy=chosen_proxy, impersonate="chrome110")
            if response.status_code == 200:
                logging.info(f"[SUCCESS] Fetched: {url}")
                return response.text
            else:
                logging.warning(f"[FAIL] Failed to fetch {url} | Status: {response.status_code}")
    except Exception as e:
        logging.error(f"[ERROR] Fetching {url}: {e}")
    return None

def scrape_http_links(html_content, base_url):
    """Parses HTML content to find all unique absolute HTTP/HTTPS links."""
    soup = BeautifulSoup(html_content, 'html.parser')
    found_links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        absolute_link = urljoin(base_url, href)
        parsed_link = urlparse(absolute_link)
        if parsed_link.scheme in ['http', 'https']:
            found_links.add(absolute_link)
    logging.info(f"[INFO] Found {len(found_links)} unique links on {base_url}")
    return list(found_links)

async def scraper_main(args, stop_event):
    """The main async function for the scraper logic using SQLite."""
    db = DatabaseManager(args.db_file)
    
    if args.urls:
        logging.info(f"[INFO] Adding starting URLs to database...")
        db.add_links(args.urls)

    for i in range(args.count):
        if stop_event.is_set():
            logging.warning("[WARN] Stop requested. Halting scraping.")
            break

        current_batch = db.get_unscraped_links(limit=100) # Scrape in batches of 100
        if not current_batch:
            logging.info("[INFO] No new links to scrape. Iteration finished.")
            break
        logging.info(f"\n--- Iteration {i + 1} / {args.count} --- (Scraping {len(current_batch)} links)")
        
        tasks = [get_data(url) for url in current_batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for url, result in zip(current_batch, results):
            if stop_event.is_set():
                logging.warning("[WARN] Stop requested during result processing.")
                break
            
            db.mark_as_scraped(url)
            if isinstance(result, str):
                new_links = scrape_http_links(result, url)
                if new_links:
                    db.add_links(new_links)
            elif result is not None:
                logging.error(f"[ERROR] Processing result for {url}: {result}")
    
    total_links = db.get_total_link_count()
    logging.info(f"\n[INFO] Scraping complete. Total unique links in database: {total_links}")
    db.close()
    logging.info("[INFO] Done!")

# --- PySide6 GUI Application ---

class DbViewer(QDialog):
    """A simple dialog window to view the contents of a SQLite database file."""
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Viewing: {os.path.basename(file_path)}")
        self.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout(self)
        self.text_viewer = QTextEdit()
        self.text_viewer.setReadOnly(True)
        layout.addWidget(self.text_viewer)
        
        self.load_data(file_path)

    def load_data(self, file_path):
        try:
            db = DatabaseManager(file_path)
            links = db.conn.execute("SELECT url FROM links ORDER BY id").fetchall()
            content = "\n".join([link[0] for link in links])
            self.text_viewer.setText(content)
            db.close()
        except Exception as e:
            self.text_viewer.setText(f"Error loading database file:\n\n{e}")


class QLogHandler(logging.Handler, QObject):
    log_received = Signal(object)
    def __init__(self):
        super().__init__()
        QObject.__init__(self)
    def emit(self, record):
        self.log_received.emit(record)

class ScraperWorker(QThread):
    def __init__(self, args, stop_event):
        super().__init__()
        self.args = args
        self.stop_event = stop_event
    def run(self):
        try:
            asyncio.run(scraper_main(self.args, self.stop_event))
        except Exception as e:
            logging.error(f"[ERROR] Scraper thread error: {e}\n{traceback.format_exc()}")

class ScraperApp(QMainWindow):
    CONFIG_FILE = "scraper_config.json"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Scraper GUI")
        self.setGeometry(100, 100, 850, 650)
        self.tor_process = None
        self.nyx_process = None
        self.tor_bootstrapped = threading.Event()
        self.stop_event = threading.Event()
        self.db_viewer = None # To hold a reference to the viewer window

        self.setup_ui()
        self.setup_logging()
        self.load_parameters()
        self.launch_monitoring_tools()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        param_group = QGroupBox("Parameters")
        param_layout = QVBoxLayout()
        self.entries = {}
        
        # Database File
        db_layout = QHBoxLayout()
        db_btn = QPushButton("Database File:"); db_btn.setFixedWidth(100)
        db_btn.clicked.connect(self.select_db_file)
        self.entries['db_file'] = QLineEdit(); self.entries['db_file'].setReadOnly(True)
        db_layout.addWidget(db_btn); db_layout.addWidget(self.entries['db_file'])
        param_layout.addLayout(db_layout)

        # URLs Entry
        url_layout = QHBoxLayout()
        url_label = QLabel("Add URLs (csv):"); url_label.setFixedWidth(100)
        self.entries['urls'] = QLineEdit()
        url_layout.addWidget(url_label); url_layout.addWidget(self.entries['urls'])
        param_layout.addLayout(url_layout)

        # Count Entry
        count_layout = QHBoxLayout()
        count_label = QLabel("Iterations:"); count_label.setFixedWidth(100)
        self.entries['count'] = QLineEdit(); self.entries['count'].setText("1")
        count_layout.addWidget(count_label); count_layout.addWidget(self.entries['count'])
        param_layout.addLayout(count_layout)
        
        param_group.setLayout(param_layout)

        start_button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Scraping")
        self.start_button.clicked.connect(self.start_scraping_thread)
        self.stop_button = QPushButton("Stop Scraping")
        self.stop_button.clicked.connect(self.stop_scraping)
        self.stop_button.setEnabled(False)
        start_button_layout.addStretch()
        start_button_layout.addWidget(self.start_button)
        start_button_layout.addWidget(self.stop_button)
        start_button_layout.addStretch()

        log_panes_layout = QHBoxLayout()
        log_group = QGroupBox("Log"); log_layout = QVBoxLayout()
        self.log_viewer = QTextEdit(); self.log_viewer.setReadOnly(True)
        log_layout.addWidget(self.log_viewer); log_group.setLayout(log_layout)
        error_log_group = QGroupBox("Errors"); error_log_layout = QVBoxLayout()
        self.error_viewer = QTextEdit(); self.error_viewer.setReadOnly(True)
        error_log_layout.addWidget(self.error_viewer); error_log_group.setLayout(error_log_layout)
        log_panes_layout.addWidget(log_group, 3); log_panes_layout.addWidget(error_log_group, 1)

        bottom_button_layout = QHBoxLayout()
        self.view_db_button = QPushButton("View DB File")
        self.view_db_button.clicked.connect(self.open_db_viewer)
        self.reload_button = QPushButton("Reload Script")
        self.reload_button.clicked.connect(self.reload_script)
        bottom_button_layout.addStretch()
        bottom_button_layout.addWidget(self.view_db_button)
        bottom_button_layout.addWidget(self.reload_button)

        main_layout.addWidget(param_group)
        main_layout.addLayout(start_button_layout)
        main_layout.addLayout(log_panes_layout)
        main_layout.addLayout(bottom_button_layout)

    def open_db_viewer(self):
        """Opens a file dialog to select and view a SQLite database file."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Database File to View", "", "SQLite Database (*.sqlite *.db)")
        if path:
            self.db_viewer = DbViewer(path, self)
            self.db_viewer.show()

    def select_db_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Select Database File", "", "SQLite Database (*.sqlite *.db)")
        if path:
            self.entries['db_file'].setText(path)

    def append_log_message(self, record):
        color_map = {'INFO': QColor('green'), 'WARNING': QColor('orange'), 'ERROR': QColor('red'), 'DEBUG': QColor('grey')}
        color = color_map.get(record.levelname, QColor('green'))
        log_widget = self.error_viewer if record.levelno >= logging.WARNING else self.log_viewer
        cursor = log_widget.textCursor()
        cursor.movePosition(QTextCursor.End)
        char_format = cursor.charFormat()
        char_format.setForeground(color)
        cursor.setCharFormat(char_format)
        cursor.insertText(self.gui_handler.format(record).strip() + '\n')
        log_widget.moveCursor(QTextCursor.End)

    def setup_logging(self):
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        log_file = "scraper_debug.log"
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        if logger.hasHandlers(): logger.handlers.clear()
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
        self.gui_handler = QLogHandler()
        self.gui_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self.gui_handler.setLevel(logging.INFO)
        self.gui_handler.log_received.connect(self.append_log_message)
        logger.addHandler(self.gui_handler)

    def save_parameters(self):
        params_to_save = {name: widget.text() for name, widget in self.entries.items()}
        try:
            with open(self.CONFIG_FILE, 'w') as f: json.dump(params_to_save, f, indent=4)
            logging.info("[INFO] Parameters saved.")
        except Exception as e: logging.error(f"[ERROR] Error saving parameters: {e}")

    def load_parameters(self):
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f: saved_params = json.load(f)
                for name, value in saved_params.items():
                    if name in self.entries: self.entries[name].setText(value)
                logging.info("[INFO] Parameters loaded from previous session.")
        except Exception as e: logging.error(f"[ERROR] Error loading parameters: {e}")

    def reload_script(self):
        logging.warning("[WARN] Reloading script...")
        self.on_closing(reloading=True)
        time.sleep(0.5)
        os.execv(sys.executable, ['python'] + sys.argv)

    def closeEvent(self, event):
        self.on_closing(); event.accept()

    def on_closing(self, reloading=False):
        self.save_parameters()
        if self.nyx_process is not None:
            logging.info("[INFO] Terminating Nyx process...")
            if sys.platform == "win32":
                subprocess.Popen(['taskkill', '/F', '/T', '/FI', 'WINDOWTITLE eq Nyx Monitor*'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            else: self.nyx_process.terminate()
        if self.tor_process:
            logging.info("[INFO] Terminating Tor process...")
            self.tor_process.terminate()
        if not reloading: QApplication.quit()

    def start_scraping_thread(self):
        if not self.entries['db_file'].text():
            QMessageBox.critical(self, "Error", "A 'Database File' must be selected.")
            return
        self.save_parameters()
        self.start_button.setEnabled(False); self.start_button.setText("Scraping...")
        self.stop_button.setEnabled(True)
        self.stop_event.clear()
        urls = [url.strip() for url in self.entries['urls'].text().split(',') if url.strip()]
        args = argparse.Namespace(urls=urls, db_file=self.entries['db_file'].text(), count=int(self.entries['count'].text() or 1))
        self.scraper_thread = ScraperWorker(args, self.stop_event)
        self.scraper_thread.finished.connect(self.on_scraping_finished)
        self.scraper_thread.start()

    def stop_scraping(self):
        logging.warning("[WARN] Stop button clicked. Requesting scraper to stop...")
        self.stop_event.set()
        self.stop_button.setEnabled(False)

    def on_scraping_finished(self):
        self.start_button.setEnabled(True); self.start_button.setText("Start Scraping")
        self.stop_button.setEnabled(False)

    def redirect_process_output(self, process):
        for line in iter(process.stdout.readline, ''):
            clean_line = line.strip()
            if "for reason resolve failed" in clean_line:
                logging.warning(f"[Tor Process] {clean_line}")
            else:
                logging.info(f"[Tor Process] {clean_line}")
            
            if "Bootstrapped 100% (done): Done" in clean_line:
                logging.info("[SUCCESS] Tor has fully bootstrapped.")
                self.tor_bootstrapped.set()
        process.stdout.close()

    def launch_monitoring_tools(self):
        threading.Thread(target=self._launch_tools_thread, daemon=True).start()

    def _launch_tools_thread(self):
        logging.info("[INFO] Launching monitoring tools...")
        try:
            logging.info("   Launching integrated Tor process...")
            self.tor_process = subprocess.Popen(['tor'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            threading.Thread(target=self.redirect_process_output, args=(self.tor_process,), daemon=True).start()
            if self.tor_bootstrapped.wait(timeout=120):
                logging.info("[SUCCESS] Tor is ready.")
                if sys.platform == "win32":
                    logging.info("   Launching Nyx in a new terminal...")
                    self.nyx_process = subprocess.Popen('start "Nyx Monitor" cmd /k nyx', shell=True)
                elif sys.platform == "darwin":
                    logging.info("   Launching Nyx in a new terminal...")
                    self.nyx_process = subprocess.Popen(['osascript', '-e', 'tell app "Terminal" to do script "nyx"'])
                else:
                    logging.info("   Launching Nyx in a new terminal...")
                    try: self.nyx_process = subprocess.Popen(['gnome-terminal', '--', 'nyx'])
                    except FileNotFoundError: self.nyx_process = subprocess.Popen(['xterm', '-e', 'nyx'])
            else: logging.warning("[WARN] Timed out waiting for Tor to bootstrap. Nyx will not be launched.")
        except Exception as e:
            logging.error(f"[ERROR] Error launching monitoring tools: {e}")
            logging.error("   Please ensure 'tor' and 'nyx' are in your system's PATH.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScraperApp()
    window.show()
    sys.exit(app.exec())
