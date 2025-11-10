"""
Contains PySide6 components for the GUI, including:
- QThreads for background tasks (DbWorker, ScraperWorker)
- Custom QObjects for logging (QLogHandler)
- Re-usable dialogs (TextEditorDialog, DataViewerDialog)
"""

import os
import sqlite3
import traceback
import logging
import asyncio
import time 
import sys
import csv 
import shutil
from urllib.parse import urlparse 

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGroupBox, QLabel, QLineEdit,
                               QPushButton, QTextEdit, QMessageBox, QFileDialog, QDialog, QCheckBox,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMenu,
                               QTableView, QDialogButtonBox) 
from PySide6.QtCore import (QObject, Signal, QThread, Qt, QAbstractTableModel, 
                            QModelIndex) 
from PySide6.QtGui import QColor, QTextCursor, QFont, QAction

from scraper import scraper_main_producer, scraper_worker_task
# Import DatabaseManager to be used only inside DbWorker for execution
from database import DatabaseManager 
from database_actions import DbViewer # Import DbViewer from its new home
from utils import MODE_PAGINATE, MODE_PULL_TOP_LEVEL, MODE_PULL_KEYWORDS 

# --- NEW: Text Editor Dialog (Request 2) ---

class TextEditorDialog(QDialog):
    """
    A simple dialog for editing a text file (URL or Keyword list).
    """
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        
        if self.file_path:
            self.setWindowTitle(f"Editing: {os.path.basename(self.file_path)}")
        else:
            self.setWindowTitle("New File")
            
        self.setGeometry(250, 250, 500, 600)
        
        layout = QVBoxLayout(self)
        
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Courier", 10))
        self.text_edit.setAcceptRichText(False)
        layout.addWidget(self.text_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        button_box.accepted.connect(self.save_file)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.load_file_content()

    def load_file_content(self):
        """Loads text from self.file_path into the text editor."""
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.text_edit.setPlainText(f.read())
                logging.info(f"Loaded {self.file_path} into editor.")
            except Exception as e:
                logging.error(f"Failed to load file {self.file_path}: {e}")
                QMessageBox.critical(self, "Load Error", f"Failed to load file:\n{e}")

    def save_file(self):
        """Saves the content of the text editor back to the file."""
        if not self.file_path:
            # If file path is blank, open a "Save As" dialog
            path, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "Text Files (*.txt)")
            if not path:
                return # User cancelled
            self.file_path = path
            
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.text_edit.toPlainText())
            logging.info(f"Saved changes to {self.file_path}")
            self.accept() # Close the dialog on success
        except Exception as e:
            logging.error(f"Failed to save file {self.file_path}: {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{e}")
            
# --- END Text Editor Dialog ---


# --- GUI Worker Threads ---

class DbWorker(QThread):
    data_ready = Signal(int, list, list) 
    file_action_complete = Signal(int, str, int, object) 
    progress_update = Signal(int) # Signal to report percentage progress

    def __init__(self, file_path, mode, offset=0, limit=200, keywords=None, threshold=1, total_rows_to_check=0, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.mode = mode
        self.offset = offset
        self.limit = limit
        self.keywords = keywords
        self.threshold = threshold
        self.total_rows_to_check = total_rows_to_check # Stores the count determined in gui_main

    def run(self):
            try:
                # FIX: Send initial "Calculating" signal before running blocking operation
                self.progress_update.emit(-1)
                # END FIX
                
                db = DatabaseManager(self.file_path)
                if self.mode == MODE_PAGINATE:
                    self._run_paginate_query(db)
                elif self.mode == MODE_PULL_TOP_LEVEL:
                    self._run_pull_top_level(db)
                elif self.mode == MODE_PULL_KEYWORDS:
                    self._run_pull_keywords(db)
            except Exception as e:
                logging.error(f"[DB Worker ERROR] Mode {self.mode} failed for {self.file_path}: {e}\n{traceback.format_exc()}")
                if self.mode != MODE_PAGINATE:
                    self.file_action_complete.emit(self.mode, self.file_path, -1, None)
                else:
                    self.data_ready.emit(0, ['Error'], [[f"Database error: {e}"]])
            finally:
                if 'db' in locals():
                    db.close()
                    
    def _run_paginate_query(self, db):
        """
        Pagination logic for live view.
        Fetches all columns but truncates page_data for GUI speed. (Request 3)
        """
        total_rows = 0
        columns = []
        rows_data = []
        
        conn = db.conn 
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        table_name = 'links'
        
        # --- FIX: Select ALL columns, including page_data ---
        cursor.execute(f"PRAGMA table_info({table_name});")
        all_columns = [info[1] for info in cursor.fetchall()]
        
        columns_to_select = all_columns
        select_clause = ", ".join([f'"{c}"' for c in columns_to_select])
        columns = columns_to_select
        # --- END FIX ---
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        total_rows = cursor.fetchone()[0]

        if total_rows > 0:
            cursor.execute("SELECT {} FROM {} LIMIT ? OFFSET ?;".format(select_clause, table_name), (self.limit, self.offset))
            rows = cursor.fetchall()
            
            for row in rows:
                row_data = []
                for col_name in columns_to_select:
                    value = row[col_name]
                    
                    # --- FIX (Request 3): Truncate page_data to prevent GUI lag ---
                    if col_name == 'page_data' and value is not None:
                        str_value = str(value).replace('\n', ' ').replace('\r', ' ')
                        if len(str_value) > 100:
                            row_data.append(str_value[:100] + '...')
                        else:
                            row_data.append(str_value)
                    # --- END FIX ---
                    else:
                        row_data.append(str(value if value is not None else 'NULL'))
                
                rows_data.append(row_data)

        self.data_ready.emit(total_rows, columns, rows_data)

    def _run_pull_keywords(self, db):
        """Pulls keyword matches and writes them to a new file (memory efficient)."""
        base_name, ext = os.path.splitext(self.file_path)
        new_db_path = f"{base_name}_KW{ext}"
        
        count = db.filter_links_by_keyword_threshold_to_new_db(
            new_db_path, 
            self.keywords, 
            self.threshold,
            self.progress_update, 
            self.total_rows_to_check
        )
        
        self.file_action_complete.emit(self.mode, new_db_path, count, self.threshold)

    def _run_pull_top_level(self, db):
        """Pulls top level URLs and writes them to a new file."""
        base_name, ext = os.path.splitext(self.file_path)
        new_db_path = f"{base_name}_TOP{ext}"
        
        count = db.pull_top_level_to_new_db(
            new_db_path,
            self.progress_update, 
            self.total_rows_to_check
        )
        
        self.file_action_complete.emit(self.mode, new_db_path, count, None)


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
        import csv 
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
        import sqlite3
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
    """
    A QThread to run the asyncio scraper logic without blocking the GUI.
    
    This thread's *only* job is to create and run an asyncio event loop.
    The main GUI thread can then schedule a forceful shutdown on this loop.
    """
    finished = Signal()
    
    def __init__(self, args, stop_event, pause_event, 
                 active_tasks_dict, active_tasks_lock, 
                 rescrape_mode=False, top_level_only_mode=False, 
                 onion_only_mode=False, titles_only_mode=False, keywords=None, 
                 save_page_data_mode="Keyword Match", # <-- Changed
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
        self.save_page_data_mode = save_page_data_mode # <-- Changed
        self.rescrape_page_data_mode = rescrape_page_data_mode 
        
        # --- REVAMP: Attributes to hold the loop and tasks ---
        self.loop = None
        self.producer_task = None
        self.worker_tasks = []
        # --- END REVAMP ---
    
    async def _shutdown_tasks(self):
        """
        A coroutine that forcefully cancels all running tasks and stops the loop.
        This is designed to be called thread-safe from the GUI.
        """
        logging.warning("Forceful shutdown initiated. Cancelling all tasks...")
        
        if self.producer_task:
            self.producer_task.cancel()
            
        for task in self.worker_tasks:
            task.cancel()
            
        # Wait for all tasks to acknowledge cancellation
        all_tasks = self.worker_tasks + [self.producer_task]
        await asyncio.gather(*[t for t in all_tasks if t], return_exceptions=True)
        
        if self.loop:
            self.loop.stop()
        logging.warning("Event loop stopped.")

    def stop_now(self):
        """
        Public, thread-safe method for the GUI to call.
        It schedules the _shutdown_tasks coroutine on the running event loop.
        """
        if self.loop and self.loop.is_running():
            logging.info("Scheduling forceful shutdown from main thread...")
            asyncio.run_coroutine_threadsafe(self._shutdown_tasks(), self.loop)
        else:
            logging.warning("Stop_now called, but loop is not running.")

    def run(self):
        """
        This is the entry point for the QThread.
        It sets up and runs the asyncio event loop.
        """
        try:
            # --- REVAMP: Create and manage the loop directly ---
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            concurrency = self.args.batch_size
            queue = asyncio.Queue(maxsize=concurrency * 2)
            
            # --- MODIFIED: Get db_path to pass to workers ---
            db_path = self.args.db_file
            # --- END MODIFIED ---
            
            # Create worker tasks
            for i in range(concurrency):
                worker_id = f"Worker-{i+1}" 
                task = self.loop.create_task(scraper_worker_task(
                    worker_id, queue, self.stop_event, self.pause_event, 
                    self.active_tasks_dict, self.active_tasks_lock,
                    self.onion_only_mode, self.titles_only_mode,
                    self.keywords, self.save_page_data_mode, # <-- Pass mode string
                    self.top_level_only_mode,
                    db_path  # <-- MODIFIED: Pass db_path
                ))
                self.worker_tasks.append(task)
            
            # Create producer task
            self.producer_task = self.loop.create_task(scraper_main_producer(
                queue, self.args, self.stop_event,
                self.rescrape_mode, self.top_level_only_mode,
                self.onion_only_mode, self.titles_only_mode,
                self.keywords, 
                self.save_page_data_mode, # <-- Pass mode string
                self.rescrape_page_data_mode 
            ))
            
            # Run the loop until stop() is called
            logging.info("Scraper event loop started.")
            self.loop.run_forever()
            
            # --- END REVAMP ---

        except Exception as e:
            logging.error(f"[ERROR] Scraper thread error: {e}\n{traceback.format_exc()}")
        finally:
            if self.loop:
                self.loop.close()
            logging.info("Scraper thread finished. Emitting finished signal.")
            self.finished.emit()
