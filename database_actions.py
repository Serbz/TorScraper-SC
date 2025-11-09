"""
Handles database query and export actions requested from the GUI.
Also hosts the DbViewer dialog, centralizing database interaction components.
"""

import logging
import os
import csv
import sqlite3
import time 
import shutil
import traceback
from pathlib import Path

from PySide6.QtWidgets import (QApplication, QMessageBox, QFileDialog, QDialog, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, 
                               QMenu, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QInputDialog)
from PySide6.QtCore import (Qt, QAbstractTableModel, QModelIndex, Signal)
from PySide6.QtGui import (QFont, QAction, QColor) 

# Import necessary dependencies for DbViewer to function
from database import DatabaseManager 
# --- FIX: Import constants from utils. DbWorker import DEFERRED ---
from utils import MODE_PAGINATE, MODE_PULL_TOP_LEVEL, MODE_PULL_KEYWORDS 
# --- END FIX ---


class DbViewer(QDialog):
    """
    A paginated dialog window to view the contents of a SQLite database file.
    It uses DbWorker for non-blocking data loading.
    """
    data_ready = Signal(int, list, list) # Custom signal for data

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_read_only = file_path.endswith("_TOP.sqlite") or file_path.endswith("_KW.sqlite")
        self.mode = MODE_PAGINATE # DbViewer is always in paginate mode
        
        self.limit = 50 # <-- FIX: Changed default pagination limit from 500 to 50
        self.offset = 0
        self.total_rows = 0
        self.data_worker = None
        self.column_names = []
        self.id_column_index = -1
        
        self.setup_ui()
        self.load_data_chunk(reset_offset=True) # Initial load

    def setup_ui(self):
        self.setGeometry(200, 200, 1000, 700)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        layout = QVBoxLayout(self)

        # --- Table Viewer ---
        self.table_viewer = QTableWidget()
        self.table_viewer.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_viewer.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_viewer.verticalHeader().setVisible(False)
        self.table_viewer.setFont(QFont("Courier"))
        self.table_viewer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_viewer.customContextMenuRequested.connect(self.open_context_menu)
        layout.addWidget(self.table_viewer)

        # --- Navigation and Status Bar ---
        nav_layout = QHBoxLayout()
        self.page_label = QLabel("Loading...")
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.export_button = QPushButton("Export All")
        
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)
        self.export_button.clicked.connect(self.export_view)

        nav_layout.addWidget(self.page_label)
        nav_layout.addStretch(1)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch(1)
        nav_layout.addWidget(self.export_button)
        layout.addLayout(nav_layout)
        
        # Connect the custom signal to the data handler slot
        self.data_ready.connect(self.on_data_ready)

    def load_data_chunk(self, reset_offset=False):
        """Initializes and runs the DbWorker thread to load the paginated data chunk."""
        if self.data_worker and self.data_worker.isRunning():
            return 
            
        if reset_offset:
            self.offset = 0

        # --- FIX: Deferred import of DbWorker to break the circular dependency ---
        try:
            # We import DbWorker from gui_components here, after gui_components
            # has already imported database_actions, successfully breaking the cycle.
            from gui_components import DbWorker
        except ImportError as e:
            logging.critical(f"FATAL: DbWorker could not be imported: {e}")
            if self.mode == MODE_PAGINATE:
                self.data_ready.emit(0, ['Error'], [[f"DB Worker Import Error: {e}"]])
            return
        # --- END FIX ---
        
        # Use DbWorker in PAGINATE mode
        self.data_worker = DbWorker(self.file_path, mode=MODE_PAGINATE, offset=self.offset, limit=self.limit)
        # Connect the worker's signal to *this* instance's custom signal
        self.data_worker.data_ready.connect(self.data_ready) 
        self.data_worker.start()
        
        # Show loading state
        self.table_viewer.setRowCount(1)
        self.table_viewer.setColumnCount(1)
        self.table_viewer.setItem(0, 0, QTableWidgetItem("Loading page data..."))
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)

    def on_data_ready(self, total_rows, column_names, rows_data):
        """Slot to handle the result from the DbDataWorker thread."""
        self.total_rows = total_rows
        
        if column_names:
            self.column_names = column_names
            try:
                # Assuming the primary key 'id' is present
                self.id_column_index = self.column_names.index('id') 
            except ValueError:
                self.id_column_index = -1
                logging.warning("No 'id' column found in database. Modify/Delete actions will be disabled.")
                
            self.table_viewer.setColumnCount(len(self.column_names))
            self.table_viewer.setHorizontalHeaderLabels(self.column_names)

        self.populate_table(rows_data)
        self.update_nav_buttons()
        
        # Clean up worker after use
        if hasattr(self, 'data_worker') and self.data_worker:
            self.data_worker.quit()
            self.data_worker.wait()
            del self.data_worker
            self.data_worker = None

    def prev_page(self):
        self.offset = max(0, self.offset - self.limit)
        self.load_data_chunk()

    def next_page(self):
        self.offset += self.limit
        self.load_data_chunk()

    def export_view(self):
        """Exports all data from the CURRENTLY VIEWED FILE to a new file."""
        if self.table_viewer.rowCount() == 0 or (self.table_viewer.rowCount() == 1 and self.table_viewer.item(0,0).text().startswith("Loading")):
            QMessageBox.warning(self, "Export Error", "No data to export.")
            return
            
        file_filter = "CSV Files (*.csv);;SQLite Database (*.sqlite);;Text Files (*.txt)"
        path, selected_filter = QFileDialog.getSaveFileName(self, f"Export {os.path.basename(self.file_path)} As", "", file_filter)
        if not path:
            return

        def is_sqlite_file(p):
            return p.lower().endswith((".sqlite", ".db"))

        try:
            if "SQLite Database" in selected_filter and is_sqlite_file(self.file_path):
                # Fastest way: raw file copy
                shutil.copy2(self.file_path, path)
            else: 
                export_format = 'csv' if "CSV Files" in selected_filter else 'txt'
                export_full_db_to_file(self.file_path, path, export_format, self)
                
            QMessageBox.information(self, "Success", f"Successfully exported all rows to {os.path.basename(path)}.")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"An error occurred while saving the file:\n{e}")


    def populate_table(self, rows_data):
        """Clears and repopulates the QTableWidget with rows."""
        self.table_viewer.setUpdatesEnabled(False)
        self.table_viewer.setRowCount(0) 
        
        if not rows_data and self.total_rows == 0:
            self.table_viewer.setRowCount(1)
            self.table_viewer.setColumnCount(1)
            self.table_viewer.setItem(0, 0, QTableWidgetItem("No data found."))
            self.table_viewer.setUpdatesEnabled(True)
            return
            
        self.table_viewer.setRowCount(len(rows_data))
        for row_idx, row_data in enumerate(rows_data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(cell_data)
                self.table_viewer.setItem(row_idx, col_idx, item)
        self.resize_columns()
        self.table_viewer.setUpdatesEnabled(True) 

    def resize_columns(self):
        """Sets resize modes for table columns."""
        header = self.table_viewer.horizontalHeader()
        if not self.column_names: return
        
        for i in range(len(self.column_names)):
            col_name = self.column_names[i]
            if col_name in ('id', 'scraped'):
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            elif col_name == 'url':
                header.setSectionResizeMode(i, QHeaderView.Interactive)
                self.table_viewer.setColumnWidth(i, 250)
            # --- FIX (Request 3): page_data is now truncated, so it can be stretched ---
            elif col_name in ('title', 'keyword_match', 'page_data'):
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            # --- END FIX ---
            else:
                header.setSectionResizeMode(i, QHeaderView.Interactive)

    def update_nav_buttons(self):
        self.prev_button.setEnabled(self.offset > 0)
        self.next_button.setEnabled(self.offset + self.limit < self.total_rows)
        self.export_button.setEnabled(self.total_rows > 0)
        start_row = self.offset + 1
        end_row = min(self.offset + self.limit, self.total_rows)
        self.page_label.setText(f"Showing rows {start_row}-{end_row} of {self.total_rows}")
        
    def open_context_menu(self, position):
        menu = QMenu()
        
        item = self.table_viewer.itemAt(position)
        
        copy_row_action = QAction("Copy contents of row to clipboard", self)
        copy_row_action.triggered.connect(self.copy_row)
        menu.addAction(copy_row_action)

        copy_cell_action = QAction("Copy contents of cell to clipboard", self)
        copy_cell_action.triggered.connect(self.copy_cell)
        menu.addAction(copy_cell_action)

        menu.addSeparator()

        set_null_action = QAction("Set NULL", self)
        set_null_action.triggered.connect(self.set_cell_null)
        menu.addAction(set_null_action)

        delete_row_action = QAction("Delete row", self)
        delete_row_action.triggered.connect(self.delete_row)
        menu.addAction(delete_row_action)

        if not item:
            copy_row_action.setEnabled(False)
            copy_cell_action.setEnabled(False)
            set_null_action.setEnabled(False)
            delete_row_action.setEnabled(False)
        else:
            can_modify = self.id_column_index != -1 and not self.is_read_only
            set_null_action.setEnabled(can_modify)
            delete_row_action.setEnabled(can_modify)
            
            col_name = self.column_names[item.column()]
            if col_name in ('id', 'url'):
                set_null_action.setEnabled(False)
        
        menu.exec(self.table_viewer.viewport().mapToGlobal(position))

    # --- FIX (Request 3): Helper to get full data from DB ---
    def _get_full_db_value(self, row_id, column_name):
        """Queries the DB for a single full, untruncated value."""
        try:
            conn = sqlite3.connect(self.file_path)
            cursor = conn.cursor()
            # Use f-string for column name (safe) and parameter for row_id (safe)
            cursor.execute(f'SELECT "{column_name}" FROM links WHERE id = ?', (row_id,))
            result = cursor.fetchone()
            conn.close()
            if result:
                return str(result[0] if result[0] is not None else "NULL")
        except Exception as e:
            logging.error(f"Failed to query full data for copy: {e}")
        return None

    def copy_row(self):
        """Copies the full row, querying DB for untruncated page_data."""
        current_row = self.table_viewer.currentRow()
        if current_row < 0 or self.id_column_index == -1:
            return
        
        id_item = self.table_viewer.item(current_row, self.id_column_index)
        if not id_item: return
        row_id = id_item.text()
        
        row_data = []
        for col in range(self.table_viewer.columnCount()):
            col_name = self.column_names[col]
            
            # --- FIX (Request 3): Query DB for full page_data ---
            if col_name == 'page_data':
                full_data = self._get_full_db_value(row_id, 'page_data')
                row_data.append(full_data if full_data is not None else "NULL")
            # --- END FIX ---
            else:
                item = self.table_viewer.item(current_row, col)
                row_data.append(item.text() if item else "NULL")
        
        QApplication.clipboard().setText(" | ".join(row_data))
        logging.info(f"Copied full row {current_row} to clipboard.")

    def copy_cell(self):
        """Copies the full cell, querying DB for untruncated page_data."""
        item = self.table_viewer.currentItem()
        if not item or self.id_column_index == -1:
            return

        col_name = self.column_names[item.column()]

        # --- FIX (Request 3): Query DB for full page_data ---
        if col_name == 'page_data':
            current_row = item.row()
            id_item = self.table_viewer.item(current_row, self.id_column_index)
            if not id_item: return
            row_id = id_item.text()
            
            full_data = self._get_full_db_value(row_id, 'page_data')
            if full_data is not None:
                QApplication.clipboard().setText(full_data)
                logging.info("Copied full page_data cell to clipboard.")
            return
        # --- END FIX ---

        # Default copy for all other cells
        QApplication.clipboard().setText(item.text())
        logging.info("Copied cell to clipboard.")

    def set_cell_null(self):
        if self.is_read_only:
            QMessageBox.warning(self, "Action Denied", "Cannot modify this derived database file.")
            return

        item = self.table_viewer.currentItem()
        if not item or self.id_column_index == -1:
            return
            
        current_row = item.row()
        current_col = item.column()
        col_name = self.column_names[current_col]
        
        # --- FIX: Prevent setting page_data to NULL if it's truncated ---
        # (This is a safety check, though a user might want to)
        if col_name == 'page_data' and item.text().endswith('...'):
            QMessageBox.information(self, "Action Info", "Setting NULL on a truncated 'page_data' column is disabled to prevent data loss.\n\nYou can delete the row instead.")
            return
        # --- END FIX ---
        
        id_item = self.table_viewer.item(current_row, self.id_column_index)
        if not id_item:
            logging.error("Could not find ID item for row.")
            return

        row_id = id_item.text()

        reply = QMessageBox.warning(self, "Confirm Set NULL",
                                    f"Are you sure you want to set column '{col_name}' to NULL for row ID {row_id}?\n\nThis cannot be undone.",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.No:
            return

        try:
            conn = sqlite3.connect(self.file_path)
            conn.execute(f"UPDATE links SET {col_name} = NULL WHERE id = ?", (row_id,))
            conn.commit()
            conn.close()
            item.setText("NULL")
            logging.info(f"Set {col_name} to NULL for ID {row_id}")
        except Exception as e:
            logging.error(f"Failed to set cell to NULL: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update database: {e}")

    def delete_row(self):
        if self.is_read_only:
            QMessageBox.warning(self, "Action Denied", "Cannot delete rows from this derived database file.")
            return
            
        current_row = self.table_viewer.currentRow()
        if current_row < 0 or self.id_column_index == -1:
            return

        id_item = self.table_viewer.item(current_row, self.id_column_index)
        if not id_item:
            logging.error("Could not find ID item for row.")
            return
        
        row_id = id_item.text()

        reply = QMessageBox.warning(self, "Confirm Delete",
                                    f"Are you sure you want to permanently delete row ID {row_id}?\n\nThis cannot be undone.",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.No:
            return

        try:
            conn = sqlite3.connect(self.file_path)
            conn.execute("DELETE FROM links WHERE id = ?", (row_id,))
            conn.commit()
            conn.close()
            
            self.table_viewer.removeRow(current_row)
            self.total_rows -= 1
            self.update_nav_buttons()
            logging.info(f"Deleted row ID {row_id}")
        except Exception as e:
            logging.error(f"Failed to delete row: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete row from database: {e}")
        
def open_db_viewer_dialog(file_path, title=None, parent_window=None):
    """
    Launches a dedicated DbViewer dialog for the given file path.
    Uses a centralized function for all DB viewing across the application.
    """
    if not file_path or not os.path.exists(file_path):
        QMessageBox.critical(parent_window, "Error", "Database file not found or path is empty.")
        return None

    try:
        # Create a new instance of the DbViewer
        viewer = DbViewer(file_path, parent=parent_window)
        if title:
            viewer.setWindowTitle(title)
        
        # This function manages the lifecycle of the viewer instance
        viewer.show()
        return viewer
    
    except Exception as e:
        logging.error(f"Failed to launch centralized DB Viewer for {file_path}: {e}\n{traceback.format_exc()}")
        QMessageBox.critical(parent_window, "DB Viewer Error", f"Failed to launch DB Viewer:\n{e}")
        return None

def export_all_links(source_db_path, save_path, parent_window=None):
    """Exports all links from the selected database to a text file."""
    logging.info(f"Starting export of all links from '{source_db_path}' to '{save_path}'...")
    try:
        # DatabaseManager is still used here for simple, synchronous data access
        db = DatabaseManager(source_db_path)
        all_urls = db.get_all_links()
        db.close()

        if not all_urls:
            QMessageBox.information(parent_window, "Export Complete", "The selected database contains no links to export.")
            logging.info("Export finished: No links found in the database.")
            return

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_urls))

        count = len(all_urls)
        del all_urls

        QMessageBox.information(parent_window, "Success", f"Successfully exported {count} links to\n{os.path.basename(save_path)}.")
        logging.info(f"Successfully exported {count} links.")

    except Exception as e:
        logging.error(f"Failed to export links: {e}")
        QMessageBox.critical(parent_window, "Error", f"An error occurred during the export process: {e}")

def export_keyword_matches_to_file(source_db_path, save_path, keywords, threshold, export_format='csv', parent_window=None):
    """
    STUB: This function is not called by the main GUI flow but remains for potential 
    future use if the export logic relied on pre-calculation.
    """
    QMessageBox.information(parent_window, "Export Complete", "Export not implemented for keyword filter. Please export from the generated _KW.sqlite file.")

def export_full_db_to_file(source_db_path, path, export_format, parent_window):
    """
    Exports all data from a single DB file to the specified format. 
    Used by DbViewer's "Export All" button if not using raw file copy.
    """
    try:
        conn = sqlite3.connect(source_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(links);")
        columns = [info[1] for info in cursor.fetchall()]

        cursor.execute("SELECT * FROM links;")
        rows = cursor.fetchall()
        
        # Convert rows to lists of values
        rows_data = []
        for row in rows:
            rows_data.append(tuple(row[col] for col in columns))

        if export_format == 'csv':
            _write_rows_to_csv(path, columns, rows_data)
        elif export_format == 'txt':
            _write_rows_to_txt(path, columns, rows_data)
            
        conn.close()
        return True

    except Exception as e:
        logging.error(f"Failed to export full DB to file: {e}")
        QMessageBox.critical(parent_window, "Export Error", f"An error occurred during export: {e}")
        return False
        
def _write_rows_to_txt(path, columns, rows):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(" | ".join(columns) + "\n")
        for row in rows:
            f.write(" | ".join([str(x) if x is not None else "NULL" for x in row]) + "\n")

def _write_rows_to_csv(path, columns, rows):
    # This must match the aggressive sanitization logic used in DbViewer export
    with open(path, 'w', newline='', encoding='utf-8') as f:
        # Use QUOTE_NONE for maximum manual control over content.
        writer = csv.writer(f, quoting=csv.QUOTE_NONE, escapechar='\\')
        writer.writerow(columns)
        
        for row in rows:
            sanitized_row = []
            for item in row:
                cell_data = str(item) if item is not None else ""
                
                if cell_data.upper() == "NULL": cell_data = ""
                cell_data = cell_data.replace('\n', ' ').replace('\r', ' ')
                cell_data = cell_data.replace('"', '')
                cell_data = cell_data.replace("'", "")
                cell_data = cell_data.replace(',', ' ')
                
                sanitized_row.append(cell_data.strip())
            
            writer.writerow(sanitized_row)

def _write_rows_to_sqlite(path, columns, rows):
    if os.path.exists(path):
        os.remove(path)
        
    conn = sqlite3.connect(path)
    with conn:
        cursor = conn.cursor()
        col_defs = ", ".join([f'"{col}" TEXT' for col in columns])
        cursor.execute(f"CREATE TABLE links ({col_defs})")
        
        placeholders = ", ".join(["?"] * len(columns))
        cursor.executemany(f"INSERT INTO links VALUES ({placeholders})", rows)
    conn.close()
