"""
Handles database query and export actions requested from the GUI.
"""

import logging
import os
import csv
import sqlite3
import time 
import shutil
from pathlib import Path
from PySide6.QtWidgets import QMessageBox
from database import DatabaseManager

def pull_top_level_urls(source_db_path, new_db_path, parent_window=None):
    """Pulls all top-level URLs into a new database file."""
    if not source_db_path:
        QMessageBox.critical(parent_window, "Error", "A 'Database File' must be selected first.")
        return False 

    if os.path.exists(new_db_path):
        try:
            os.remove(new_db_path)
            logging.info(f"Removed existing file: {new_db_path}")
        except Exception as e:
            logging.error(f"Failed to remove existing file: {e}")
            QMessageBox.critical(parent_window, "Error", f"Failed to overwrite existing file: {e}")
            return False 
    
    logging.info(f"Starting pull of top-level URLs from '{source_db_path}' to '{new_db_path}'...")
    try:
        db = DatabaseManager(source_db_path)
        count = db.pull_top_level_to_new_db(new_db_path)
        db.close()
        
        if count > 0:
            QMessageBox.information(parent_window, "Success", f"Successfully copied {count} top-level URLs to\n{os.path.basename(new_db_path)}.")
            return True 
        elif count == 0:
            QMessageBox.information(parent_window, "Complete", "No top-level URLs were found in the source database.")
            return True 
        else: 
             QMessageBox.critical(parent_window, "Error", "An error occurred while creating the new database. Check logs for details.")
             return False 
    except Exception as e:
        logging.error(f"Failed to pull top-level URLs: {e}")
        QMessageBox.critical(parent_window, "Error", f"An error occurred: {e}")
        return False 

def export_all_links(source_db_path, save_path, parent_window=None):
    """Exports all links from the selected database to a text file."""
    logging.info(f"Starting export of all links from '{source_db_path}' to '{save_path}'...")
    try:
        db = DatabaseManager(source_db_path)
        all_urls = db.get_all_links()
        db.close()

        if not all_urls:
            QMessageBox.information(parent_window, "Export Complete", "The selected database contains no links to export.")
            logging.info("Export finished: No links found in the database.")
            return

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_urls))

        QMessageBox.information(parent_window, "Success", f"Successfully exported {len(all_urls)} links to\n{os.path.basename(save_path)}.")
        logging.info(f"Successfully exported {len(all_urls)} links.")

    except Exception as e:
        logging.error(f"Failed to export links: {e}")
        QMessageBox.critical(parent_window, "Error", f"An error occurred during the export process: {e}")

def pull_keyword_matches_to_temp_db(source_db_path, script_dir, keywords, threshold, parent_window=None):
    """
    Pulls all rows that meet the keyword match threshold into a new temporary DB file 
    in a dedicated temp folder and returns the path to that file.
    """
    temp_dir = script_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        db = DatabaseManager(source_db_path)
        
        # --- MODIFIED: CALL NEW DB MANAGER METHOD ---
        columns, rows = db.get_keyword_matches_by_threshold(keywords, threshold)
        db.close()
        # --- END MODIFIED ---
        
        if not rows:
            QMessageBox.information(parent_window, "No Matches", 
                                    f"No links were found that match at least {threshold} unique keywords.")
            return None
            
        # Create a new temp DB file
        temp_db_path = temp_dir / f"keyword_matches_{int(time.time())}.sqlite"
        logging.info(f"Creating temporary keyword DB at: {temp_db_path}")
        
        # --- WRITE TEMP DB ---
        conn = sqlite3.connect(temp_db_path)
        with conn:
            cursor = conn.cursor()
            # Create table
            col_defs = ", ".join([f'"{col}" TEXT' for col in columns])
            cursor.execute(f"CREATE TABLE links ({col_defs})")
            
            # Insert data
            placeholders = ", ".join(["?"] * len(columns))
            cursor.executemany(f"INSERT INTO links VALUES ({placeholders})", rows)
        conn.close()
        # --- END WRITE TEMP DB ---
        
        del rows
        return str(temp_db_path)

    except Exception as e:
        logging.error(f"Failed to pull keyword matches: {e}")
        QMessageBox.critical(parent_window, "Error", f"An error occurred while pulling keyword matches: {e}")
        return None