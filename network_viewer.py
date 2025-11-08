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

# --- FIX: Removed top-level Scapy import block ---
# Imports will be done inside functions to avoid NameError
# if the top-level import fails.

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                               QAbstractItemView, QHeaderView, QLabel, QGroupBox,
                               QSizePolicy, QGridLayout)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QBrush, QColor 

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

def abbreviate_site(site_name, max_len=40):
    """Abbreviates a long site name."""
    if len(site_name) <= max_len:
        return site_name
    half = (max_len - 3) // 2
    return site_name[:half] + "..." + site_name[-half:]

class NetworkActivityViewer(QDialog):
    """A dialog to show active scraper tasks and Tor network I/O."""
    def __init__(self, active_tasks_dict, active_tasks_lock, tor_pid, parent=None):
        super().__init__(parent)
        self.active_tasks_dict = active_tasks_dict
        self.active_tasks_lock = active_tasks_lock
        self.tor_pid = tor_pid
        self.running = True

        self.setWindowTitle("Network Activity")
        self.setGeometry(300, 300, 700, 800) 
        
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

        # --- Active Tasks Table ---
        tasks_group = QGroupBox("Active Scrape Tasks")
        tasks_layout = QVBoxLayout()
        self.tasks_table = QTableWidget()
        
        self.tasks_table.setColumnCount(3) 
        self.tasks_table.setHorizontalHeaderLabels(["Worker", "Site", "Bytes"]) 

        self.tasks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tasks_table.verticalHeader().setVisible(False)
        self.tasks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # Worker
        self.tasks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Site
        self.tasks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) # Bytes
        self.tasks_table.setWordWrap(False)
        
        tasks_layout.addWidget(self.tasks_table)
        tasks_group.setLayout(tasks_layout)
        layout.addWidget(tasks_group) # Add table, let it stretch

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
        layout.addWidget(stats_group)
        
        # Set stretch factors
        layout.setStretchFactor(tasks_group, 1) # Table takes up most space
        layout.setStretchFactor(stats_group, 0) # Stats group is fixed size


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
        self.total_download_label.setText(f"Download Rate: {format_rate(current_download)}")
        self.total_upload_label.setText(f"Upload Rate: {format_rate(current_upload)}")
        
        # Update total session labels
        self.session_total_download += current_download
        self.session_total_upload += current_upload
        self.session_download_label.setText(f"Total Download: {format_total_size(self.session_total_download)}")
        self.session_upload_label.setText(f"Total Upload: {format_total_size(self.session_total_upload)}")
        
        # --- 2. Update Active Tasks Table ---
        now = time.time()
        tasks_to_remove = []
        total_active_tasks = 0
        
        with self.active_tasks_lock:
            self.tasks_table.setRowCount(len(self.active_tasks_dict)) # Set max size
            row = 0
            
            for task_id, task_data in list(self.active_tasks_dict.items()):
                worker_id = task_data.get('worker_id', 'N/A')
                site = task_data.get('site', 'N/A')
                bytes_val = task_data.get('bytes', 0)
                finished_at = task_data.get('finished_at')

                worker_item = QTableWidgetItem(worker_id)
                site_item = QTableWidgetItem(abbreviate_site(site))
                bytes_item = QTableWidgetItem(f"{bytes_val:,} B")
                
                if finished_at:
                    if now - finished_at > 2.0:
                        tasks_to_remove.append(task_id)
                        continue 
                    else:
                        worker_item.setBackground(self.green_brush)
                        worker_item.setForeground(self.white_text_brush)
                        site_item.setBackground(self.green_brush)
                        site_item.setForeground(self.white_text_brush)
                        bytes_item.setBackground(self.green_brush)
                        bytes_item.setForeground(self.white_text_brush)
                else:
                    total_active_tasks += 1
                    worker_item.setBackground(self.dark_brush)
                    worker_item.setForeground(self.white_text_brush)
                    site_item.setBackground(self.dark_brush)
                    site_item.setForeground(self.white_text_brush)
                    bytes_item.setBackground(self.dark_brush)
                    bytes_item.setForeground(self.white_text_brush)
                
                self.tasks_table.setItem(row, 0, worker_item)
                self.tasks_table.setItem(row, 1, site_item)
                self.tasks_table.setItem(row, 2, bytes_item)
                row += 1
            
            self.tasks_table.setRowCount(row)
            
            for task_id in tasks_to_remove:
                if task_id in self.active_tasks_dict:
                    del self.active_tasks_dict[task_id]

        self.total_active_label.setText(f"Active Tasks: {total_active_tasks}")
        
        if not self.running:
            self.total_active_label.setText(f"Active Tasks: 0 (Tor process ended)")
            self.total_download_label.setText("Download Rate: N/A")
            self.total_upload_label.setText("Upload Rate: N/A")

    def closeEvent(self, event):
        """Stop threads when the window is closed."""
        self.running = False # Signal threads to stop
        self.timer.stop()
        event.accept()