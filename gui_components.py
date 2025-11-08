"""
Contains PySide6 components for the GUI, including:
- QThreads for background tasks (DbDataWorker, ScraperWorker)
- QDialogs for modal windows (DbViewer)
- Custom QObjects for logging (QLogHandler)
"""

import os
import sqlite3
import traceback
import logging
import asyncio
import time 
import sys
import csv 
from urllib.parse import urlparse 

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGroupBox, QLabel, QLineEdit,
                               QPushButton, QTextEdit, QMessageBox, QFileDialog, QDialog, QCheckBox,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMenu,
                               QTableView) 
from PySide6.QtCore import (QObject, Signal, QThread, Qt, QAbstractTableModel, 
                            QModelIndex) 
from PySide6.QtGui import QColor, QTextCursor, QFont, QAction

from scraper import scraper_main_producer, scraper_worker_task

# --- GUI Worker Threads & Components ---

class DbDataWorker(QThread):
    """
    Worker thread to get total row count and first page of data from DB
    without freezing the GUI.
    """
    data_ready = Signal(int, list, list)  # Emits (total_rows, column_names_list, rows_data_list)

    def __init__(self, file_path, limit):
        super().__init__()
        self.file_path = file_path
        self.limit = limit

    def run(self):
        total_rows = 0
        columns = []
        rows_data = []
        try:
            conn = sqlite3.connect(self.file_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            table_name = 'links'

            # Get table header
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [info[1] for info in cursor.fetchall()]

            # Get total row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            result = cursor.fetchone()
            if result:
                total_rows = result[0]

            if total_rows > 0:
                # Get first chunk of rows
                cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET 0;", (self.limit,))
                rows = cursor.fetchall()
                for row in rows:
                    row_data = [str(row[col] if row[col] is not None else 'NULL') for col in columns]
                    rows_data.append(row_data)
            
            conn.close()
        except Exception as e:
            logging.error(f"DB Worker Error: {e}")
            columns = ['Error']
            rows_data = [[f"Error loading database file: {e}"]]
            total_rows = 0

        self.data_ready.emit(total_rows, columns, rows_data)

class DbViewer(QDialog):
    """A simple dialog window to view the contents of a SQLite database file with pagination."""
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.offset = 0
        self.limit = 200  # Show 200 rows per page
        self.total_rows = 0
        self.column_names = [] # Store column names
        self.id_column_index = -1 # Store index of 'id' column

        self.setWindowTitle(f"Viewing: {os.path.basename(file_path)}")
        self.setGeometry(200, 200, 800, 600)
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        layout = QVBoxLayout(self)
        
        self.table_viewer = QTableWidget()
        self.table_viewer.setFont(QFont("Courier"))
        self.table_viewer.setWordWrap(False) 
        self.table_viewer.setEditTriggers(QAbstractItemView.NoEditTriggers) 
        self.table_viewer.setSelectionBehavior(QAbstractItemView.SelectRows) 
        self.table_viewer.verticalHeader().setVisible(False) 
        
        self.table_viewer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_viewer.customContextMenuRequested.connect(self.open_context_menu)
        
        layout.addWidget(self.table_viewer)

        # --- Navigation Controls ---
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("<< Previous")
        self.prev_button.clicked.connect(self.prev_page)
        self.export_button = QPushButton("Export View")
        self.export_button.clicked.connect(self.export_view)
        self.next_button = QPushButton("Next >>")
        self.next_button.clicked.connect(self.next_page)
        self.page_label = QLabel("Page: N/A")
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.export_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)
        layout.addLayout(nav_layout)

        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.table_viewer.setRowCount(1)
        self.table_viewer.setColumnCount(1)
        self.table_viewer.setItem(0, 0, QTableWidgetItem("Loading database information..."))

        self.data_worker = DbDataWorker(self.file_path, self.limit)
        self.data_worker.data_ready.connect(self.on_data_ready)
        self.data_worker.start()

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
            can_modify = self.id_column_index != -1
            set_null_action.setEnabled(can_modify)
            delete_row_action.setEnabled(can_modify)
            
            col_name = self.column_names[item.column()]
            if col_name in ('id', 'url'):
                set_null_action.setEnabled(False)
        
        menu.exec(self.table_viewer.viewport().mapToGlobal(position))

    def copy_row(self):
        current_row = self.table_viewer.currentRow()
        if current_row < 0:
            return
        
        row_data = []
        for col in range(self.table_viewer.columnCount()):
            item = self.table_viewer.item(current_row, col)
            row_data.append(item.text() if item else "NULL")
        
        QApplication.clipboard().setText(" | ".join(row_data))
        logging.info(f"Copied row {current_row} to clipboard.")

    def copy_cell(self):
        item = self.table_viewer.currentItem()
        if not item:
            return
        
        QApplication.clipboard().setText(item.text())
        logging.info("Copied cell to clipboard.")

    def set_cell_null(self):
        item = self.table_viewer.currentItem()
        if not item or self.id_column_index == -1:
            return
            
        current_row = item.row()
        current_col = item.column()
        col_name = self.column_names[current_col]
        
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

    def on_data_ready(self, total_rows, column_names, rows_data):
        """Slot to handle the result from the DbDataWorker thread."""
        self.total_rows = total_rows
        self.column_names = column_names
        
        try:
            self.id_column_index = self.column_names.index('id')
        except ValueError:
            self.id_column_index = -1
            logging.warning("No 'id' column found in database. Modify/Delete actions will be disabled.")
            
        self.table_viewer.setColumnCount(len(self.column_names))
        self.table_viewer.setHorizontalHeaderLabels(self.column_names)
        
        self.populate_table(rows_data)
        self.update_nav_buttons()

    def populate_table(self, rows_data):
        """Clears and repopulates the QTableWidget with rows."""
        self.table_viewer.setUpdatesEnabled(False)
        self.table_viewer.setRowCount(0) 
        
        if not rows_data and self.total_rows == 0:
            self.table_viewer.setRowCount(1)
            self.table_viewer.setItem(0, 0, QTableWidgetItem("Database is empty."))
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
        for i in range(len(self.column_names)):
            col_name = self.column_names[i]
            if col_name in ('id', 'scraped'):
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            elif col_name == 'url':
                header.setSectionResizeMode(i, QHeaderView.Interactive)
                self.table_viewer.setColumnWidth(i, 250)
            elif col_name in ('title', 'keyword_match', 'page_data'):
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.Interactive)

    def prev_page(self):
        self.offset = max(0, self.offset - self.limit)
        self.load_data_chunk()

    def next_page(self):
        self.offset += self.limit
        self.load_data_chunk()

    def export_view(self):
        """Exports the current table view to a text file."""
        if self.table_viewer.rowCount() == 0 or (self.table_viewer.rowCount() == 1 and self.table_viewer.item(0,0).text().startswith("Loading")):
            QMessageBox.warning(self, "Export Error", "No data to export.")
            return

        # --- FIX 1: Add CSV and SQLite options ---
        file_filter = "CSV Files (*.csv);;SQLite Database (*.sqlite);;Text Files (*.txt)"
        path, selected_filter = QFileDialog.getSaveFileName(self, "Save View As", "", file_filter)
        if not path:
            return

        try:
            if "CSV Files" in selected_filter:
                self._export_to_csv_from_table(path)
            elif "SQLite Database" in selected_filter:
                self._export_to_sqlite_from_table(path)
            else: # Text file or fallback
                self._export_to_txt_from_table(path)
            
            QMessageBox.information(self, "Success", f"Successfully exported view to {os.path.basename(path)}.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"An error occurred while saving the file:\n{e}")

    def _export_to_txt_from_table(self, path):
        """Exports visible table data to a plain text file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(" | ".join(self.column_names) + "\n")
            for row in range(self.table_viewer.rowCount()):
                row_data = []
                for col in range(self.table_viewer.columnCount()):
                    item = self.table_viewer.item(row, col)
                    row_data.append(item.text() if item else 'NULL')
                f.write(" | ".join(row_data) + "\n")

    def _export_to_csv_from_table(self, path):
            """Exports visible table data to CSV with aggressive sanitization."""
            
            # NOTE: Using QUOTE_NONE requires every cell to be manually sanitized
            # to ensure commas/newlines are removed, otherwise the CSV structure breaks.
            with open(path, 'w', newline='', encoding='utf-8') as f:
                # Use QUOTE_NONE for maximum manual control over content.
                # Delimiter is comma by default.
                writer = csv.writer(f, quoting=csv.QUOTE_NONE, escapechar='\\')
                writer.writerow(self.column_names)
                
                for row_idx in range(self.table_viewer.rowCount()):
                    row_data = []
                    for col_idx in range(self.table_viewer.columnCount()):
                        item = self.table_viewer.item(row_idx, col_idx)
                        cell_data = item.text() if item else ""
                        
                        # --- AGGRESSIVE SANITIZATION ON ALL FIELDS ---
                        # 1. Convert "NULL" text back to empty string for clean export
                        if cell_data.upper() == "NULL":
                            cell_data = ""
                            
                        # 2. Remove newlines (CRLF/LF)
                        cell_data = cell_data.replace('\n', ' ')
                        cell_data = cell_data.replace('\r', ' ')
                        
                        # 3. Remove quotes (both single and double)
                        cell_data = cell_data.replace('"', '')
                        cell_data = cell_data.replace("'", "")
                        
                        # 4. Remove internal commas to prevent CSV structure breakage
                        # This is done on ALL fields to prevent quoting issues.
                        cell_data = cell_data.replace(',', ' ')
                        
                        row_data.append(cell_data.strip())
                    
                    # Write the sanitized row
                    writer.writerow(row_data)
                    
    def _export_to_sqlite_from_table(self, path):
        """Exports visible table data to a new SQLite database."""
        if os.path.exists(path):
            os.remove(path)
            
        conn = sqlite3.connect(path)
        with conn:
            cursor = conn.cursor()
            col_defs = ", ".join([f'"{col}" TEXT' for col in self.column_names])
            cursor.execute(f"CREATE TABLE links ({col_defs})")
            
            placeholders = ", ".join(["?"] * len(self.column_names))
            
            rows_to_insert = []
            for row_idx in range(self.table_viewer.rowCount()):
                row_data = []
                for col_idx in range(self.table_viewer.columnCount()):
                    item = self.table_viewer.item(row_idx, col_idx)
                    row_data.append(item.text() if item else None)
                rows_to_insert.append(tuple(row_data))
                
            cursor.executemany(f"INSERT INTO links VALUES ({placeholders})", rows_to_insert)
        conn.close()

    def update_nav_buttons(self):
        self.prev_button.setEnabled(self.offset > 0)
        self.next_button.setEnabled(self.offset + self.limit < self.total_rows)
        self.export_button.setEnabled(self.total_rows > 0)
        start_row = self.offset + 1
        end_row = min(self.offset + self.limit, self.total_rows)
        self.page_label.setText(f"Showing rows {start_row}-{end_row} of {self.total_rows}")

    def load_data_chunk(self):
        """Loads and displays a chunk of data from the database for Next/Previous clicks."""
        rows_data = []
        try:
            conn = sqlite3.connect(self.file_path)
            conn.row_factory = sqlite3.Row 
            cursor = conn.cursor()
            table_name = 'links'

            if not self.column_names:
                cursor.execute(f"PRAGMA table_info({table_name});")
                self.column_names = [info[1] for info in cursor.fetchall()]
                try:
                    self.id_column_index = self.column_names.index('id')
                except ValueError:
                    self.id_column_index = -1
                self.table_viewer.setColumnCount(len(self.column_names))
                self.table_viewer.setHorizontalHeaderLabels(self.column_names)

            cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?;", (self.limit, self.offset))
            rows = cursor.fetchall()
            for row in rows:
                row_data = [str(row[col] if row[col] is not None else 'NULL') for col in self.column_names]
                rows_data.append(row_data)

            conn.close()
            self.populate_table(rows_data)
            self.update_nav_buttons()

        except Exception as e:
            self.table_viewer.setRowCount(1)
            self.table_viewer.setItem(0, 0, QTableWidgetItem(f"Error loading database file:\n\n{e}"))
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.export_button.setEnabled(False)


# --- REFACTORED: DataViewerDialog (for Keyword Matches) ---

class DataTableModel(QAbstractTableModel):
    """
    A custom QAbstractTableModel to efficiently handle large datasets
    for display in a QTableView.
    """
    def __init__(self, data, headers):
        super().__init__()
        self._data = data
        self._headers = headers

    def data(self, index, role):
        if not index.isValid():
            return None 
            
        value = self.data_for_index(index)

        if role == Qt.DisplayRole:
            return str(value)
        
        if role == Qt.UserRole:
            return value

        return None 
        
    def data_for_index(self, index):
        """Safe data accessor."""
        try:
            return self.clean_value(self._data[index.row()][index.column()])
        except IndexError:
            return None 
            
    def clean_value(self, value):
        """Returns 'NULL' for None, otherwise the value."""
        return value if value is not None else "NULL"

    def rowCount(self, index=QModelIndex()):
        return len(self._data)

    def columnCount(self, index=QModelIndex()):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._headers[section])
            if orientation == Qt.Vertical:
                return str(section + 1)
        return None 

    def get_row_data(self, row_index):
        """Returns all data for a specific row as a list of strings."""
        if 0 <= row_index < self.rowCount():
            return [str(self.clean_value(self._data[row_index][col])) for col in range(self.columnCount())]
        return []

    def get_cell_data(self, row_index, col_index):
        """Returns the data for a specific cell as a string."""
        if 0 <= row_index < self.rowCount() and 0 <= col_index < self.columnCount():
            return str(self.clean_value(self._data[row_index][col_index]))
        return ""


class DataViewerDialog(QDialog):
    """
    A simple dialog to display a list of columns and rows, with no pagination.
    Uses QTableView and a custom model for high performance.
    
    NOTE: This is no longer used for keyword matches due to memory constraints.
    It is kept here for reference or future use of small result sets.
    """
    def __init__(self, column_names, rows_data, parent=None):
        super().__init__(parent)
        self.column_names = column_names
        self.rows_data = rows_data

        self.setGeometry(250, 250, 800, 600)
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        layout = QVBoxLayout(self)
        
        self.table_viewer = QTableView()
        self.table_viewer.setFont(QFont("Courier"))
        self.table_viewer.setWordWrap(False)
        self.table_viewer.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_viewer.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_viewer.verticalHeader().setVisible(False)
        self.table_viewer.setSortingEnabled(True) 
        
        self.model = DataTableModel(self.rows_data, self.column_names)
        self.table_viewer.setModel(self.model)
        
        self.table_viewer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_viewer.customContextMenuRequested.connect(self.open_context_menu)
        
        layout.addWidget(self.table_viewer)
        
        bottom_layout = QHBoxLayout()
        self.status_label = QLabel(f"Showing {len(rows_data)} results.")
        self.export_button = QPushButton("Export View")
        self.export_button.clicked.connect(self.export_results)
        
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.export_button)
        
        layout.addLayout(bottom_layout)

        self.resize_columns()

    def resize_columns(self):
        """Sets resize modes for table columns."""
        header = self.table_viewer.horizontalHeader()
        for i in range(len(self.column_names)):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
            
            col_name = self.column_names[i]
            if col_name in ('id', 'scraped'):
                self.table_viewer.setColumnWidth(i, 80)
            elif col_name == 'url':
                self.table_viewer.setColumnWidth(i, 250)
            elif col_name in ('title', 'keyword_match'):
                self.table_viewer.setColumnWidth(i, 200)
            elif col_name == 'page_data':
                 self.table_viewer.setColumnWidth(i, 300)

    def export_results(self):
        """Exports the view to CSV or SQLite."""
        # This dialog is now primarily for small result sets, keeping the functionality simple.
        file_filter = "CSV Files (*.csv);;SQLite Database (*.sqlite);;Text Files (*.txt)"
        path, selected_filter = QFileDialog.getSaveFileName(self, "Export Results", "", file_filter)
        
        if not path:
            return
            
        try:
            if "CSV Files" in selected_filter:
                self.export_to_csv(path)
            elif "SQLite Database" in selected_filter:
                self.export_to_sqlite(path)
            else:
                self.export_to_txt(path)
            
            QMessageBox.information(self, "Export Success", f"Successfully exported results to {os.path.basename(path)}")
            logging.info(f"Exported results to {path}")
            
        except Exception as e:
            logging.error(f"Failed to export results: {e}")
            QMessageBox.critical(self, "Export Error", f"An error occurred: {e}")

    def export_to_txt(self, path):
        """Exports data to a plain text file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(" | ".join(self.column_names) + "\n")
            for row in self.rows_data:
                f.write(" | ".join([str(x) if x is not None else "NULL" for x in row]) + "\n")

    def export_to_csv(self, path):
        """Exports data to CSV with sanitization."""
        try:
            page_data_index = self.column_names.index('page_data')
        except ValueError:
            page_data_index = -1

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(self.column_names)
            
            for row in self.rows_data:
                sanitized_row = list(row)
                
                if page_data_index != -1 and sanitized_row[page_data_index] is not None:
                    cell_data = str(sanitized_row[page_data_index])
                    # Aggressive sanitization: remove quotes, newlines, and commas
                    cell_data = cell_data.replace('\n', ' ').replace('\r', ' ')
                    cell_data = cell_data.replace('"', "'")
                    cell_data = cell_data.replace(',', ' ') 
                    
                    sanitized_row[page_data_index] = cell_data
                    
                final_row = [str(x) if x is not None else "" for x in sanitized_row]
                writer.writerow(final_row)

    def export_to_sqlite(self, path):
        if os.path.exists(path):
            os.remove(path)
            
        conn = sqlite3.connect(path)
        with conn:
            cursor = conn.cursor()
            
            col_defs = ", ".join([f'"{col}" TEXT' for col in self.column_names])
            cursor.execute(f"CREATE TABLE links ({col_defs})")
            
            placeholders = ", ".join(["?"] * len(self.column_names))
            cursor.executemany(f"INSERT INTO links VALUES ({placeholders})", self.rows_data)
            
        conn.close()

    def open_context_menu(self, position):
        menu = QMenu()
        index = self.table_viewer.indexAt(position)
        
        copy_row_action = QAction("Copy contents of row to clipboard", self)
        copy_row_action.triggered.connect(self.copy_row)
        menu.addAction(copy_row_action)

        copy_cell_action = QAction("Copy contents of cell to clipboard", self)
        copy_cell_action.triggered.connect(self.copy_cell)
        menu.addAction(copy_cell_action)

        if not index.isValid():
            copy_row_action.setEnabled(False)
            copy_cell_action.setEnabled(False)

        menu.exec(self.table_viewer.viewport().mapToGlobal(position))

    def copy_row(self):
        selected_indexes = self.table_viewer.selectionModel().selectedRows()
        if not selected_indexes:
            return
        
        row_index = selected_indexes[0].row()
        row_data = self.model.get_row_data(row_index)
        QApplication.clipboard().setText(" | ".join(row_data))
        logging.info(f"Copied row {row_index} to clipboard.")

    def copy_cell(self):
        current_index = self.table_viewer.currentIndex()
        if not current_index.isValid():
            return
        
        cell_data = self.model.get_cell_data(current_index.row(), current_index.column())
        QApplication.clipboard().setText(cell_data)
        logging.info("Copied cell to clipboard.")

class QLogHandler(logging.Handler, QObject):
    """A custom logging handler that emits a Qt signal for each log record."""
    log_received = Signal(object)
    def __init__(self):
        super().__init__()
        QObject.__init__(self)
    def emit(self, record):
        self.log_received.emit(record)

class ScraperWorker(QThread):
    """A QThread to run the asyncio scraper logic without blocking the GUI."""
    def __init__(self, args, stop_event, pause_event, 
                 active_tasks_dict, active_tasks_lock, 
                 rescrape_mode=False, top_level_only_mode=False, 
                 onion_only_mode=False, titles_only_mode=False, keywords=None, save_all_page_data=False,
                 rescrape_page_data_mode=False): 
        super().__init__()
        self.args = args
        self.stop_event = stop_event
        self.pause_event = pause_event
        self.active_tasks_dict = active_tasks_dict 
        self.active_tasks_lock = active_tasks_lock 
        self.rescrape_mode = rescrape_mode
        self.top_level_only_mode = top_level_only_mode
        self.onion_only_mode = onion_only_mode
        self.titles_only_mode = titles_only_mode
        self.keywords = keywords
        self.save_all_page_data = save_all_page_data
        self.rescrape_page_data_mode = rescrape_page_data_mode 
    
    async def run_async_logic(self):
        """Sets up the producer-consumer model and runs it."""
        
        concurrency = self.args.batch_size
        queue = asyncio.Queue(maxsize=concurrency * 2)
        
        worker_tasks = []
        for i in range(concurrency):
            worker_id = f"Worker-{i+1}" 
            worker_tasks.append(asyncio.create_task(scraper_worker_task(
                worker_id, queue, self.stop_event, self.pause_event, 
                self.active_tasks_dict, self.active_tasks_lock,
                self.onion_only_mode, self.titles_only_mode,
                self.keywords, self.save_all_page_data,
                self.top_level_only_mode 
            )))
            
        producer_task = asyncio.create_task(scraper_main_producer(
            queue, self.args, self.stop_event,
            self.rescrape_mode, self.top_level_only_mode,
            self.onion_only_mode, self.titles_only_mode,
            self.keywords, 
            self.rescrape_page_data_mode 
        ))

        try:
            await producer_task
            
            # --- FIX 2: Check stop_event before waiting for queue (Necessary for fast stop) ---
            if self.stop_event.is_set():
                logging.warning("Stop requested. Bypassing queue.join() to cancel workers.")
            else:
                logging.info("Producer finished. Waiting for workers to drain queue...")
                # Only wait a short time before cancelling if stop is requested, 
                # though the logic below handles the main bottleneck.
                await queue.join()
                logging.info("Queue empty. All tasks processed.")
            # --- END FIX ---

        except Exception as e:
            logging.error(f"Error in async manager: {e}\n{traceback.format_exc()}")
        
        finally:
            # --- FAST SHUTDOWN FIX: Prevent blocking on cancelled network calls ---
            logging.info("Cancelling worker tasks...")
            for task in worker_tasks:
                task.cancel() # Aggressively cancel tasks
            
            if self.stop_event.is_set():
                # Wait a maximum of 5 seconds for tasks to acknowledge cancellation.
                # This prevents blocking for the full 60-second network timeouts.
                logging.warning("Fast stop initiated. Waiting 5s max for tasks to wrap up.")
                await asyncio.wait(worker_tasks, timeout=5.0)
            else:
                # Normal shutdown, wait indefinitely for clean exit
                await asyncio.gather(*worker_tasks, return_exceptions=True)

            logging.info("Scraper workers shut down complete. Emitting finished signal.")
            # Signal the GUI thread that we are finished
            self.finished.emit() # Ensure this signal is the last thing sent
            

    def run(self):
        try:
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            # We don't use self.finished.emit() here, only in the finally block of run_async_logic
            asyncio.run(self.run_async_logic())
        except Exception as e:
            logging.error(f"[ERROR] Scraper thread error: {e}\n{traceback.format_exc()}")
            self.finished.emit() # Ensure signal is sent on catastrophic failure