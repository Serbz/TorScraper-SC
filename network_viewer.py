"""
Contains the QDialog class for the Network Activity Viewer.
Uses scapy and psutil to monitor per-process network I/O.
"""

import psutil
import time
import logging
import threading
import sys
import os
from collections import deque # <-- FIX: Import deque

# --- FIX: Removed top-level Scapy import block ---
# Imports will be done inside functions to avoid NameError
# if the top-level import fails.

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                               QAbstractItemView, QHeaderView, QLabel, QGroupBox,
                               QSizePolicy, QGridLayout, QPushButton, QHBoxLayout,
                               QMenu) # <-- FIX (Request 5): Import QMenu
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QBrush, QColor, QAction # <-- FIX (Request 5): Import QAction
from PySide6.QtWidgets import QApplication # <-- FIX (Request 5): Import QApplication

def format_rate(b):
    """Helper to format bytes into KB/s, MB/s etc."""
    if b < 1024: return f"{b} B/s"
    b /= 1024.0
    if b < 1024: return f"{b:.1f} KB/s"
    b /= 1024.0
    return f"{b:.1f} MB/s"

# --- NEW: Function to format total bytes (B/KB/MB/GB/TB) ---
def format_total_size(b):
    """Helper to format total bytes, scaling up to TB."""
    if b < 1024: return f"{b} B"
    b /= 1024.0
    if b < 1024: return f"{b:.2f} KB"
    b /= 1024.0
    if b < 1024: return f"{b:.2f} MB"
    b /= 1024.0
    if b < 1024: return f"{b:.2f} GB"
    b /= 1024.0
    return f"{b:.2f} TB"
# --- END NEW ---

# --- REMOVED (Request 1): abbreviate_site function is no longer needed ---

class NetworkActivityViewer(QDialog):
    """A dialog to show active scraper tasks and Tor network I/O."""
    def __init__(self, active_tasks_dict, active_tasks_lock, tor_pid, parent=None):
        super().__init__(parent)
        self.active_tasks_dict = active_tasks_dict
        self.active_tasks_lock = active_tasks_lock
        self.tor_pid = tor_pid
        self.running = True

        self.setWindowTitle("Network Activity")
        # --- FIX (Request 3): Double default width ---
        self.setGeometry(300, 300, 1400, 800) 
        # --- END FIX ---
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        # --- I/O tracking ---
        self.upload_bytes = 0
        self.download_bytes = 0
        self.upload_lock = threading.Lock()
        self.download_lock = threading.Lock()
        
        # --- NEW: Session total counters ---
        self.session_total_upload = 0
        self.session_total_download = 0
        
        self.tor_ports = set() # For established connections to internet
        self.socks_ports = {9100, 9101, 9102, 9103, 9104, 9105, 9106} # For local proxy

        # --- Brushes for row coloring ---
        self.green_brush = QBrush(QColor(20, 120, 20)) # Dark Green
        self.dark_brush = QBrush(QColor(40, 40, 40)) # Dark Grey
        self.white_text_brush = QBrush(QColor(255, 255, 255)) # White
        self.red_brush = QBrush(QColor(150, 20, 20)) # Dark Red
        
        # --- FIX (Request 1): Create separate headers for each table ---
        self.active_column_headers = ["Worker", "Site", "Bytes"]
        self.finished_column_headers = ["Worker", "Site", "Title", "Bytes"]
        # --- END FIX ---
        
        # --- FIX: Create persistent list for last 50 finished tasks ---
        self.finished_tasks_list = deque(maxlen=50)
        # --- END FIX ---

        self.setup_ui()

        # --- Start port updater and sniffer threads ---
        self.port_updater_thread = threading.Thread(target=self.port_update_loop, daemon=True)
        self.port_updater_thread.start()
        
        self.sniffer_thread = threading.Thread(target=self.start_sniffer, daemon=True)
        self.sniffer_thread.start()

        # --- Timer to update GUI ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(1000) # Update every 1 second

    def update_tor_ports(self):
        """
        Updates the set of *outgoing established* ports currently used by the Tor PID.
        """
        new_ports = set()
        try:
            p = psutil.Process(self.tor_pid)
            conns = p.connections(kind='inet')
            for c in conns:
                if c.status == psutil.CONN_ESTABLISHED or c.status == psutil.CONN_CLOSE_WAIT:
                    new_ports.add(c.laddr.port)
        except psutil.NoSuchProcess:
            logging.warning("Tor process not found during port scan. Stopping network threads.")
            self.running = False
        except Exception as e:
            logging.error(f"Error updating Tor ports: {e}")
        
        if self.tor_ports != new_ports:
            logging.debug(f"Updated Tor high-ports list: {new_ports}")
        self.tor_ports = new_ports

    def port_update_loop(self):
        """Continuously updates the Tor port list in a background thread."""
        while self.running:
            self.update_tor_ports()
            time.sleep(2) # Refresh port list every 2 seconds

    def packet_callback(self, packet):
        """Scapy callback for each sniffed packet."""
        try:
            import scapy.all as scapy

            if not (packet.haslayer(scapy.IP) and (packet.haslayer(scapy.TCP) or packet.haslayer(scapy.UDP))):
                return

            proto = scapy.TCP if packet.haslayer(scapy.TCP) else scapy.UDP
            
            if packet[proto].dport in self.socks_ports:
                with self.upload_lock:
                    self.upload_bytes += len(packet)
            elif packet[proto].sport in self.socks_ports:
                with self.download_lock:
                    self.download_bytes += len(packet)
            elif packet[proto].sport in self.tor_ports:
                with self.upload_lock:
                    self.upload_bytes += len(packet)
            elif packet[proto].dport in self.tor_ports:
                with self.download_lock:
                    self.download_bytes += len(packet)
                    
        except Exception as e:
            logging.debug(f"Packet callback error: {e}")

    def start_sniffer(self):
        """Starts the scapy packet sniffer."""
        try:
            import scapy.all as scapy
            
            interfaces_to_sniff = None
            if sys.platform == "win32":
                try:
                    from scapy.arch.windows import get_windows_if_list
                    ifs = get_windows_if_list()
                    interfaces_to_sniff = [iface['guid'] for iface in ifs if iface.get('npcap', False)]
                    if not interfaces_to_sniff:
                        logging.error("No Npcap interfaces found by scapy. Sniffing on default.")
                        interfaces_to_sniff = None 
                    else:
                        logging.info(f"Scapy sniffing on interfaces: {interfaces_to_sniff}")
                except Exception as e:
                    logging.error(f"Error detecting Npcap interfaces: {e}. Sniffing on default.")
            
            logging.info("Starting scapy network sniffer...")
            scapy.sniff(iface=interfaces_to_sniff, prn=self.packet_callback, store=0, stop_filter=lambda p: not self.running)
            logging.info("Scapy network sniffer stopped.")
        except NameError as e:
            logging.critical(f"Scapy sniffer failed to start. A NameError occurred (scapy not found?): {e}")
        except Exception as e:
            logging.critical(f"Scapy sniffer failed to start. Is Npcap installed and running? Error: {e}")
            

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # --- FIX (Request 4): Create a horizontal layout for two tables ---
        tables_layout = QHBoxLayout()
        
        # --- Active Tasks Table ---
        active_group = QGroupBox("Active Scrape Tasks")
        active_layout = QVBoxLayout()
        self.active_table = QTableWidget()
        # --- FIX (Request 1): Setup active table with its specific headers ---
        self.setup_table_widget(self.active_table, self.active_column_headers) 
        active_layout.addWidget(self.active_table)
        active_group.setLayout(active_layout)
        
        # --- Finished Tasks Table ---
        finished_group = QGroupBox("Finished Tasks (Last 50)")
        finished_layout = QVBoxLayout()
        self.finished_table = QTableWidget()
        # --- FIX (Request 1): Setup finished table with its specific headers ---
        self.setup_table_widget(self.finished_table, self.finished_column_headers) 
        finished_layout.addWidget(self.finished_table)
        finished_group.setLayout(finished_layout)
        # --- END FIX ---

        # --- FIX: Set stretch factors for a 40/60 split ---
        tables_layout.addWidget(active_group, 4) # 40%
        tables_layout.addWidget(finished_group, 6) # 60%
        # --- END FIX ---
        
        layout.addLayout(tables_layout) # Add tables layout
        # --- END FIX ---

        # --- Tor Process I/O Stats (Merged Group) ---
        stats_group = QGroupBox("Tor Process I/O")
        stats_layout = QGridLayout() # Use grid layout for side-by-side stats

        # Labels for current rate
        self.total_download_label = QLabel("Download Rate: Calculating...")
        self.total_upload_label = QLabel("Upload Rate: Calculating...")
        self.total_active_label = QLabel("Active Tasks: 0")
        
        # Labels for session total
        self.session_download_label = QLabel("Total Download: 0 B")
        self.session_upload_label = QLabel("Total Upload: 0 B")
        
        font = self.total_download_label.font()
        font.setPointSize(12)
        self.total_download_label.setFont(font)
        self.total_upload_label.setFont(font)
        self.total_active_label.setFont(font)
        self.session_download_label.setFont(font)
        self.session_upload_label.setFont(font)

        # Layout the widgets:
        # Row 0: Active Tasks (Spans 2 columns)
        stats_layout.addWidget(self.total_active_label, 0, 0, 1, 2)
        
        # Row 1: Download Rate | Total Download
        stats_layout.addWidget(self.total_download_label, 1, 0)
        stats_layout.addWidget(self.session_download_label, 1, 1)

        # Row 2: Upload Rate | Total Upload
        stats_layout.addWidget(self.total_upload_label, 2, 0)
        stats_layout.addWidget(self.session_upload_label, 2, 1)
        
        # Add some stretch between the columns
        stats_layout.setColumnStretch(0, 1)
        stats_layout.setColumnStretch(1, 1) 

        stats_group.setLayout(stats_layout)
        
        # --- FIX (Request 4): Add Reset Button ---
        button_layout = QHBoxLayout()
        self.reset_button = QPushButton("Reset Session Stats")
        self.reset_button.clicked.connect(self.reset_stats)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        
        layout.addWidget(stats_group)
        layout.addLayout(button_layout)
        # --- END FIX ---
        
        # Set stretch factors
        layout.setStretchFactor(tables_layout, 1) # Tables take up most space
        layout.setStretchFactor(stats_group, 0) # Stats group is fixed size

    # --- FIX (Request 1): Helper to init tables ---
    def setup_table_widget(self, table, headers):
        """Applies standard settings to a QTableWidget."""
        table.setColumnCount(len(headers)) 
        table.setHorizontalHeaderLabels(headers) 

        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        
        # --- FIX: Dynamic column resizing ---
        if len(headers) == 3: # Active table
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # Worker
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Site
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) # Bytes
        else: # Finished table
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # Worker
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Site
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Title
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # Bytes
        # --- END FIX ---
        
        table.setWordWrap(False)
        
        # --- FIX (Request 5): Add context menu ---
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.open_context_menu)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # --- END FIX ---
    # --- END FIX ---

    # --- FIX (Request 4): New slot to reset stats ---
    def reset_stats(self):
        """Resets session counters and clears the active tasks view."""
        logging.info("Resetting network activity stats...")
        
        # Reset session counters
        self.session_total_download = 0
        self.session_total_upload = 0
        
        # Clear rate counters
        with self.upload_lock:
            self.upload_bytes = 0
        with self.download_lock:
            self.download_bytes = 0
            
        # Clear active tasks dictionary and tables
        with self.active_tasks_lock:
            self.active_tasks_dict.clear()
        
        # --- FIX: Clear persistent finished list ---
        self.finished_tasks_list.clear()
        # --- END FIX ---
        
        self.active_table.setRowCount(0)
        self.finished_table.setRowCount(0)
        
        # Force immediate GUI update
        self.update_gui()
    # --- END FIX ---

    def update_gui(self):
        """Updates the GUI labels and table every second (called by QTimer)."""
        
        # --- 1. Update I/O Stats ---
        with self.upload_lock:
            current_upload = self.upload_bytes
            self.upload_bytes = 0
        
        with self.download_lock:
            current_download = self.download_bytes
            self.download_bytes = 0
        
        # Update rate labels (Current Rate)
        self.total_download_label.setText(f"Download Rate: {format_rate(current_upload)}")
        self.total_upload_label.setText(f"Upload Rate: {format_rate(current_upload)}")
        
        # Update total session labels
        self.session_total_download += current_download
        self.session_total_upload += current_upload
        self.session_download_label.setText(f"Total Download: {format_total_size(self.session_total_download)}")
        self.session_upload_label.setText(f"Total Upload: {format_total_size(self.session_total_upload)}")
        
        # --- 2. Update Active Tasks Table ---
        
        # --- FIX: New logic to move finished tasks ---
        active_tasks = []
        tasks_to_move = [] # Store task_ids to move
        
        with self.active_tasks_lock:
            # First pass: find active tasks and tasks to move
            for task_id, task_data in self.active_tasks_dict.items():
                if task_data.get('finished_at'):
                    tasks_to_move.append(task_id)
                else:
                    active_tasks.append(task_data)

            # Second pass: move the finished tasks
            for task_id in tasks_to_move:
                task_data = self.active_tasks_dict.pop(task_id) # Remove from active dict
                self.finished_tasks_list.appendleft(task_data) # Add to front of finished deque
        # --- END FIX ---
        
        self.total_active_label.setText(f"Active Tasks: {len(active_tasks)}")
        
        # --- Populate Active Table ---
        self.active_table.setUpdatesEnabled(False)
        self.active_table.setRowCount(len(active_tasks))
        for row, task_data in enumerate(active_tasks):
            worker_id = task_data.get('worker_id', 'N/A')
            # --- FIX (Request 1): Use full URL, not 'site' ---
            site = task_data.get('url', 'N/A') 
            bytes_val = task_data.get('bytes', 0)
            
            worker_item = QTableWidgetItem(worker_id)
            site_item = QTableWidgetItem(site)
            bytes_item = QTableWidgetItem(f"{bytes_val:,} B")

            # Set colors for active items
            for item in (worker_item, site_item, bytes_item):
                item.setBackground(self.dark_brush)
                item.setForeground(self.white_text_brush)
                
            self.active_table.setItem(row, 0, worker_item)
            self.active_table.setItem(row, 1, site_item)
            self.active_table.setItem(row, 2, bytes_item)
        self.active_table.setUpdatesEnabled(True)

        # --- Populate Finished Table ---
        self.finished_table.setUpdatesEnabled(False)
        # --- FIX: Use self.finished_tasks_list ---
        self.finished_table.setRowCount(len(self.finished_tasks_list))
        for row, task_data in enumerate(self.finished_tasks_list):
        # --- END FIX ---
            worker_id = task_data.get('worker_id', 'N/A')
            site = task_data.get('url', 'N/A') # Use full URL
            title = task_data.get('title', 'N/A')
            bytes_val = task_data.get('bytes', 0)
            
            worker_item = QTableWidgetItem(worker_id)
            site_item = QTableWidgetItem(site)
            title_item = QTableWidgetItem(title)
            bytes_item = QTableWidgetItem(f"{bytes_val:,} B")

            # Set colors for finished items
            status = task_data.get('status', 2) # 1 = success, 2 = fail
            brush_to_use = self.green_brush if status == 1 else self.red_brush
            
            for item in (worker_item, site_item, title_item, bytes_item):
                item.setBackground(brush_to_use)
                item.setForeground(self.white_text_brush)

            self.finished_table.setItem(row, 0, worker_item)
            self.finished_table.setItem(row, 1, site_item)
            self.finished_table.setItem(row, 2, title_item)
            self.finished_table.setItem(row, 3, bytes_item)
        self.finished_table.setUpdatesEnabled(True)
        
        if not self.running:
            self.total_active_label.setText(f"Active Tasks: 0 (Tor process ended)")
            self.total_download_label.setText("Download Rate: N/A")
            self.total_upload_label.setText("Upload Rate: N/A")

    # --- FIX (Request 5): Context menu functions ---
    def open_context_menu(self, position):
        """Generates the right-click menu for both tables."""
        
        # Find which table sent the signal
        table = self.sender()
        if not isinstance(table, QTableWidget):
            return
            
        menu = QMenu()
        item = table.itemAt(position)
        
        copy_row_action = QAction("Copy contents of row to clipboard", self)
        copy_row_action.triggered.connect(lambda: self.copy_row(table))
        menu.addAction(copy_row_action)

        copy_cell_action = QAction("Copy contents of cell to clipboard", self)
        copy_cell_action.triggered.connect(lambda: self.copy_cell(table))
        menu.addAction(copy_cell_action)

        if not item:
            copy_row_action.setEnabled(False)
            copy_cell_action.setEnabled(False)
        
        menu.exec(table.viewport().mapToGlobal(position))

    def copy_row(self, table):
        """Copies the full row from the specified table."""
        current_row = table.currentRow()
        if current_row < 0:
            return
        
        row_data = []
        for col in range(table.columnCount()):
            item = table.item(current_row, col)
            row_data.append(item.text() if item else "NULL")
        
        QApplication.clipboard().setText(" | ".join(row_data))
        logging.info(f"Copied network monitor row {current_row} to clipboard.")

    def copy_cell(self, table):
        """Copies the full cell from the specified table."""
        item = table.currentItem()
        if not item:
            return

        QApplication.clipboard().setText(item.text())
        logging.info("Copied network monitor cell to clipboard.")
    # --- END FIX ---

    def closeEvent(self, event):
        """Stop threads when the window is closed."""
        self.running = False # Signal threads to stop
        self.timer.stop()
        event.accept()
