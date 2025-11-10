"""
Contains the DatabaseManager class for handling all SQLite operations.
"""

import sqlite3
import logging
from utils import get_top_level_url, is_junk_url
import re 
import os
import shutil
import traceback

# --- NEW: Custom SQLite REGEXP function ---
def sqlite_regexp(expression, item):
    """
    Implements a custom REGEXP function for SQLite.
    Required for complex text matching in SQL queries.
    """
    if item is None:
        return False
    try:
        # Use re imported at the top of the module
        return re.search(expression, item, re.IGNORECASE) is not None
    except re.error:
        # If the regex is invalid, return False
        return False
# --- END NEW ---

class DatabaseManager:
    """Handles all SQLite database operations."""
    def __init__(self, db_path):
        self.db_path = db_path
        # Connect to the database, allowing the connection object to be shared across threads
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        
        # --- FIX: Register REGEXP function on connection object ---
        self.conn.create_function("REGEXP", 2, sqlite_regexp)
        # --- END FIX ---
        
        self.create_table()
        self.upgrade_table() # Add new columns if they don't exist

    def create_table(self):
        """Creates the 'links' table if it doesn't exist with the full schema."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    scraped INTEGER DEFAULT 0, -- 0: unscraped, 1: success, 2: failed
                    title TEXT,
                    keyword_match TEXT,
                    page_data TEXT
                )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS url_index ON links (url)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS scraped_index ON links (scraped)")

    def upgrade_table(self):
        """Adds new columns to an existing database if they are missing."""
        try:
            with self.conn:
                self.conn.execute("SELECT keyword_match FROM links LIMIT 1")
        except sqlite3.OperationalError:
            logging.warning("Upgrading database: Adding 'keyword_match' column...")
            with self.conn:
                self.conn.execute("ALTER TABLE links ADD COLUMN keyword_match TEXT")

        try:
            with self.conn:
                self.conn.execute("SELECT page_data FROM links LIMIT 1")
        except sqlite3.OperationalError:
            logging.warning("Upgrading database: Adding 'page_data' column...")
            with self.conn:
                self.conn.execute("ALTER TABLE links ADD COLUMN page_data TEXT")

    # --- FIX: Helper function to build correct schema string ---
    def _build_create_table_schema(self, columns_to_insert):
        """Builds a CREATE TABLE schema string with correct types."""
        schema_parts = ["id INTEGER PRIMARY KEY"]
        for col in columns_to_insert:
            if col == 'scraped':
                # This ensures the 'scraped' column is created correctly
                schema_parts.append("scraped INTEGER DEFAULT 0")
            elif col == 'url':
                schema_parts.append("url TEXT UNIQUE NOT NULL")
            else:
                schema_parts.append(f'"{col}" TEXT')
        return ", ".join(schema_parts)
    # --- END FIX ---

    # --- UPDATED VALIDATION HELPER ---
    def _get_and_validate_links(self, query):
        """
        Helper to run a query, check for NULLs on critical columns, 
        and return a valid list of URLs.
        """
        links = []
        try:
            # Use row_factory to access columns by name
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.execute(query)
            
            for row in cursor.fetchall():
                valid_row = True
                
                # --- NEW VALIDATION (Your Request) ---
                if row['id'] is None:
                    logging.error(f"[DATA INTEGRITY ERROR] Database contains a row with a NULL id. URL: {row['url']}")
                    valid_row = False
                
                if not row['url']: # Checks for None or empty string
                    logging.error(f"[DATA INTEGRITY ERROR] Database contains a row with a NULL or empty URL. ID: {row['id']}")
                    valid_row = False
                    
                if row['scraped'] is None:
                    # This will catch any old DBs that haven't been fixed.
                    logging.error(f"[DATA INTEGRITY ERROR] Database contains a row with a NULL 'scraped' value. URL: {row['url']}. (Run the SQL fix script)")
                    valid_row = False # Don't scrape it, it's in a bad state
                
                if valid_row:
                    links.append(row['url'])
            
            # Reset row_factory to default
            self.conn.row_factory = None
            return links
        
        except sqlite3.OperationalError as e:
            # This happens if a column (like 'scraped') doesn't exist.
            logging.error(f"A database query failed, this may be an old DB version. Error: {e}")
            self.conn.row_factory = None
            return []
        except Exception as e:
            logging.error(f"An unexpected error occurred during link validation: {e}")
            self.conn.row_factory = None
            return []
    # --- END UPDATED HELPER ---

    def get_unscraped_links(self):
        """Gets all unscraped links (status 0)."""
        # --- FIX: Use new validator. Only check for 0. ---
        return self._get_and_validate_links("SELECT id, url, scraped FROM links WHERE scraped = 0")
            
    def get_all_links(self):
        """Gets all links from the database."""
        # --- FIX: Use new validator. ---
        return self._get_and_validate_links("SELECT id, url, scraped FROM links")

    def get_unscraped_links_missing_titles(self):
        """Gets all unscraped links (status 0) that are missing a valid title."""
        # --- FIX: Use new validator. Only check for 0. ---
        return self._get_and_validate_links("""
            SELECT id, url, scraped FROM links 
            WHERE scraped = 0
            AND (title IS NULL OR title = 'No Title Found' OR title = 'Scrape Failed' OR title = '')
        """)

    def get_failed_links(self):
        """Gets all failed links (status 2)."""
        # --- FIX: Use new validator. ---
        return self._get_and_validate_links("SELECT id, url, scraped FROM links WHERE scraped = 2")

    def get_links_missing_page_data(self):
        """Gets all *non-failed* links that are missing page data."""
        # --- FIX: Use new validator. ---
        return self._get_and_validate_links("SELECT id, url, scraped FROM links WHERE scraped != 2 AND (page_data IS NULL OR page_data = '')")

    def get_keyword_matches(self):
        """Gets all columns for rows that have a keyword match."""
        with self.conn:
            # Reset row_factory in case _get_and_validate_links failed
            self.conn.row_factory = None
            cursor = self.conn.execute("SELECT * FROM links WHERE keyword_match IS NOT NULL AND keyword_match != ''")
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return columns, rows

    def get_initial_keyword_match_count(self, keywords):
        """
        Gets the total count of links matching at least one keyword in the 
        keyword_match column. (Simplified COUNT for streaming setup).
        """
        if not keywords: return 0 

        # --- MODIFIED: Separate all 3 keyword types ---
        input_keywords_plain = {k.strip().lower() for k in keywords if not k.startswith("REGEX: ")}
        input_assert_regex = []
        input_find_regex = []

        for k in keywords:
            if k.startswith("REGEX: "):
                try:
                    pattern_str = k[7:].strip()
                    compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                    if pattern_str.startswith("(?="):
                        input_assert_regex.append((k, compiled_pattern))
                    else:
                        input_find_regex.append((k, compiled_pattern))
                except re.error:
                    pass # Ignore invalid regex
        # --- END MODIFIED ---

        sql_query_parts = []
        sql_query_values = []
        
        # --- MODIFIED: Use LIKE for "Plain" and "Assert" ---
        # 1. Add plain keywords (searches for the literal word)
        for k in input_keywords_plain:
            sql_query_parts.append("keyword_match LIKE ?")
            sql_query_values.append(f"%{k}%") # Use LIKE
            
        # 2. Add "Assert" regex (searches for the literal "REGEX: (?=...)" string)
        for original_string, pattern in input_assert_regex:
            sql_query_parts.append("keyword_match LIKE ?")
            sql_query_values.append(f"%{original_string}%") # Use LIKE
            
        # 3. Add "Find" regex (executes the pattern against the stored words)
        for original_string, pattern in input_find_regex:
            sql_query_parts.append("keyword_match REGEXP ?")
            sql_query_values.append(pattern.pattern) # Use REGEXP
        # --- END MODIFIED ---

        if not sql_query_parts:
            return 0
            
        sql_filter = " OR ".join(sql_query_parts)
        count_query = f"SELECT COUNT(*) FROM links WHERE keyword_match IS NOT NULL AND keyword_match != '' AND ({sql_filter})"
        
        with self.conn:
            self.conn.row_factory = None # Ensure default
            self.conn.create_function("REGEXP", 2, sqlite_regexp) 
            cursor = self.conn.execute(count_query, sql_query_values)
            return cursor.fetchone()[0]

    def filter_links_by_keyword_threshold_to_new_db(self, new_db_path, keywords, threshold, progress_signal=None, total_rows_to_check=-1): 
        """
        Pulls links whose keyword_match column contains at least 'threshold' 
        unique keywords from the provided 'keywords' list.
        """
        if not keywords:
            return 0 

        # --- MODIFIED: Separate all 3 keyword types for counting ---
        input_keywords_plain = {k.strip().lower() for k in keywords if not k.startswith("REGEX: ")}
        
        input_assert_regex = [] # Holds ("REGEX: (?=...)", re.compile(...))
        input_find_regex = []   # Holds ("REGEX: \s...", re.compile(...))
        
        for k in keywords:
            if k.startswith("REGEX: "):
                try:
                    pattern_str = k[7:].strip()
                    compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                    
                    if pattern_str.startswith("(?="):
                        input_assert_regex.append((k, compiled_pattern))
                    else:
                        input_find_regex.append((k, compiled_pattern))
                        
                except re.error as e:
                    logging.warning(f"Invalid regex in keyword file (skipping): '{k}'. Error: {e}")
        # --- END MODIFIED ---

        # --- MODIFIED: Build SQL query to find all candidates ---
        sql_query_parts = []
        sql_query_values = []
        
        # --- MODIFIED: Use LIKE for "Plain" and "Assert" ---
        # 1. Add plain keywords (searches for the literal word)
        for k in input_keywords_plain:
            sql_query_parts.append("keyword_match LIKE ?")
            sql_query_values.append(f"%{k}%") # Use LIKE
            
        # 2. Add "Assert" regex (searches for the literal "REGEX: (?=...)" string)
        for original_string, pattern in input_assert_regex:
            sql_query_parts.append("keyword_match LIKE ?")
            sql_query_values.append(f"%{original_string}%") # Use LIKE
            
        # 3. Add "Find" regex (executes the pattern against the stored words)
        for original_string, pattern in input_find_regex:
            sql_query_parts.append("keyword_match REGEXP ?")
            sql_query_values.append(pattern.pattern) # Use REGEXP
        # --- END MODIFIED ---
        
        if not sql_query_parts:
            logging.warning("No valid keywords found for filtering.")
            return 0

        sql_filter = " OR ".join(sql_query_parts)
        initial_query = f"SELECT * FROM links WHERE keyword_match IS NOT NULL AND keyword_match != '' AND ({sql_filter})"

        if os.path.exists(new_db_path): 
            os.remove(new_db_path)
            
        new_conn = sqlite3.connect(new_db_path)
        inserted_count = 0
        rows_processed = 0 
        batch_size = 500
        insert_batch = []
        
        if total_rows_to_check == -1:
            try:
                temp_conn = sqlite3.connect(self.db_path)
                temp_conn.create_function("REGEXP", 2, sqlite_regexp)
                cursor = temp_conn.execute(f"SELECT COUNT(*) FROM links WHERE keyword_match IS NOT NULL AND keyword_match != '' AND ({sql_filter})", sql_query_values)
                total_rows_to_check = cursor.fetchone()[0]
                temp_conn.close()
                logging.info(f"Calculated {total_rows_to_check} candidate rows for keyword pull.")
            except Exception as e:
                logging.error(f"Failed to get keyword match count: {e}")
                total_rows_to_check = 0
            
            if total_rows_to_check == 0:
                if progress_signal: progress_signal.emit(100)
                return 0
            
            if progress_signal:
                logging.info(f"Total count calculated: {total_rows_to_check}. Starting streaming...")
                progress_signal.emit(0) 

        try:
            temp_conn = sqlite3.connect(self.db_path)
            temp_conn.row_factory = sqlite3.Row 
            temp_conn.create_function("REGEXP", 2, sqlite_regexp)
            cursor = temp_conn.cursor()
            
            logging.debug(f"Executing keyword pull query: {initial_query}")
            logging.debug(f"With values: {sql_query_values}")
            cursor.execute(initial_query, sql_query_values)
            
            original_columns = [description[0] for description in cursor.description]
            columns_to_insert = [col for col in original_columns if col.lower() != 'id']
            
            with new_conn:
                # --- FIX: Create table with correct schema ---
                schema_string = self._build_create_table_schema(columns_to_insert)
                new_conn.execute(f"CREATE TABLE links ({schema_string})")
                # --- END FIX ---
                
                placeholders = ", ".join(["?"] * len(columns_to_insert))
                insert_sql = f"INSERT INTO links ({', '.join(columns_to_insert)}) VALUES ({placeholders})"
            
            for row in cursor:
                row_tuple = tuple(row[col] for col in columns_to_insert)
                keyword_match_string = row['keyword_match']
                
                # --- MODIFIED: New counting logic ---
                unique_match_count = 0
                if keyword_match_string:
                    # --- THIS IS THE FIX ---
                    # Split by the new unique delimiter
                    stored_matches_set_lower = {k.strip().lower() for k in keyword_match_string.split(" _!|!_ ")}
                    stored_matches_original_case = {k.strip() for k in keyword_match_string.split(" _!|!_ ")}
                    # --- END FIX ---

                    # 1. Count plain keyword matches
                    common_plain_matches = stored_matches_set_lower.intersection(input_keywords_plain)
                    unique_match_count += len(common_plain_matches)
                    
                    # 2. Count "Assert" regex matches
                    # Check if any of the stored items are the "Assert" regex patterns
                    for input_regex_str, _ in input_assert_regex:
                        if input_regex_str in stored_matches_original_case: # Must use original case
                            unique_match_count += 1
                                
                    # 3. Count "Find" regex matches
                    # Check if any "Find" regex *pattern* matches any *stored word*
                    stored_words_only = {k for k in stored_matches_original_case if not k.startswith("REGEX: ")}
                    
                    if stored_words_only:
                        for _, find_pattern in input_find_regex:
                            # Check if this pattern matches *any* of the stored words
                            for word in stored_words_only:
                                # --- THIS IS THE FIX: Use re.search, not re.fullmatch ---
                                if find_pattern.search(word): 
                                    unique_match_count += 1
                                    # This pattern is matched, break to avoid double-counting
                                    # (e.g., if "street" and "house" both match \s\w{5}\s)
                                    break 
                # --- END MODIFIED COUNTING ---
                
                rows_processed += 1
                if progress_signal and total_rows_to_check > 0 and rows_processed % 20 == 0: 
                    percentage = int((rows_processed / total_rows_to_check) * 100)
                    progress_signal.emit(percentage)
                
                if unique_match_count >= threshold:
                    insert_batch.append(row_tuple)
                    
                    if len(insert_batch) >= batch_size:
                        with new_conn:
                            new_conn.executemany(insert_sql, insert_batch)
                        inserted_count += len(insert_batch)
                        insert_batch = [] 

            if insert_batch:
                with new_conn:
                    new_conn.executemany(insert_sql, insert_batch)
                inserted_count += len(insert_batch)

        except Exception as e:
            logging.error(f"Error during streaming keyword matching: {e}\n{traceback.format_exc()}")
            return -1
        finally:
            if 'temp_conn' in locals():
                temp_conn.close()
            if 'new_conn' in locals():
                new_conn.close()

        if progress_signal:
            progress_signal.emit(100)

        logging.info(f"Found and saved {inserted_count} links meeting the threshold of {threshold} unique matches to {new_db_path}.")
        return inserted_count
        
    def add_links(self, links, add_top_level_too=False):
        normalized_links_input = {link.rstrip('/') for link in links if not is_junk_url(link)}

        links_to_add = []
        if add_top_level_too:
            processed_links = set()
            for link in normalized_links_input:
                if link not in processed_links:
                    links_to_add.append((link,))
                    processed_links.add(link)
                top_level = get_top_level_url(link) 
                if top_level and top_level not in processed_links:
                     links_to_add.append((top_level,))
                     processed_links.add(top_level)
        else:
            links_to_add = [(link,) for link in normalized_links_input]

        if links_to_add:
            with self.conn:
                self.conn.row_factory = None # Ensure default
                self.conn.executemany("INSERT OR IGNORE INTO links (url) VALUES (?)", links_to_add)

    def update_links_batch(self, update_data):
        if not update_data:
            return
        with self.conn:
            self.conn.row_factory = None # Ensure default
            self.conn.executemany("UPDATE links SET scraped = ?, title = ?, keyword_match = ?, page_data = ? WHERE url = ?", update_data)
            
    def update_titles_batch(self, update_data):
        if not update_data:
            return
        with self.conn:
            self.conn.row_factory = None # Ensure default
            self.conn.executemany("UPDATE links SET title = ? WHERE url = ?", update_data)

    # --- NEW FUNCTION TO FIX THE BUG ---
    def update_status_and_title_batch(self, update_data):
        """Updates only the scraped status and title for a batch of URLs."""
        if not update_data:
            return
        with self.conn:
            self.conn.row_factory = None # Ensure default
            self.conn.executemany("UPDATE links SET scraped = ?, title = ? WHERE url = ?", update_data)
    # --- END NEW FUNCTION ---

    def reset_failed_links(self):
        with self.conn:
            self.conn.row_factory = None # Ensure default
            self.conn.execute("UPDATE links SET scraped = 0 WHERE scraped = 2")

    def reset_links_missing_page_data(self):
        with self.conn:
            self.conn.row_factory = None # Ensure default
            self.conn.execute("UPDATE links SET scraped = 0 WHERE scraped != 2 AND (page_data IS NULL OR page_data = '')")

    def get_total_link_count(self):
        with self.conn:
            self.conn.row_factory = None # Ensure default
            return self.conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]

    def pull_top_level_to_new_db(self, new_db_path, progress_signal=None, total_rows_to_check=-1): 
        COLUMNS_TO_INSERT = ['url', 'scraped', 'title', 'keyword_match', 'page_data']
        
        inserted_count = 0
        rows_processed = 0 
        batch_size = 500
        insert_batch = []
        
        if os.path.exists(new_db_path):
            os.remove(new_db_path)

        new_conn = sqlite3.connect(new_db_path)
        
        if total_rows_to_check == -1:
            temp_db_mgr = DatabaseManager(self.db_path)
            total_rows_to_check = temp_db_mgr.get_total_link_count()
            temp_db_mgr.close()
            
            if total_rows_to_check == 0:
                if progress_signal: progress_signal.emit(100)
                return 0
            
            if progress_signal:
                logging.info(f"Total count calculated: {total_rows_to_check}. Starting streaming...")
                progress_signal.emit(0) 
        
        try:
            temp_conn = sqlite3.connect(self.db_path)
            temp_conn.row_factory = sqlite3.Row 
            cursor = temp_conn.cursor()
            
            cursor.execute("SELECT * FROM links")
            
            columns = [desc[0].lower() for desc in cursor.description]
            column_indices = {name: columns.index(name) for name in COLUMNS_TO_INSERT if name in columns}
            url_index = column_indices.get('url')
            
            if url_index is None:
                logging.error("Database table missing 'url' column. Cannot pull top-level URLs.")
                return -1

            with new_conn:
                # --- FIX: Create table with correct schema ---
                schema_string = self._build_create_table_schema(columns_to_insert)
                new_conn.execute(f"CREATE TABLE links ({schema_string})")
                # --- END FIX ---
                
                placeholders = ", ".join(["?"] * len(columns_to_insert))
                insert_sql = f"INSERT OR IGNORE INTO links ({', '.join(COLUMNS_TO_INSERT)}) VALUES ({placeholders})"

            for row in cursor:
                url = row[url_index]
                
                if url and get_top_level_url(url) == url:
                    new_row_tuple = tuple(row[column_indices.get(col)] if col in column_indices else None for col in COLUMNS_TO_INSERT)
                    insert_batch.append(new_row_tuple)
                    
                rows_processed += 1
                if progress_signal and total_rows_to_check > 0 and rows_processed % 20 == 0:
                    percentage = int((rows_processed / total_rows_to_check) * 100)
                    progress_signal.emit(percentage)

                if len(insert_batch) >= batch_size:
                    with new_conn:
                        new_conn.executemany(insert_sql, insert_batch)
                    inserted_count += len(insert_batch)
                    insert_batch = []
            
            if insert_batch:
                with new_conn:
                    new_conn.executemany(insert_sql, insert_batch)
                inserted_count += len(insert_batch)

        except Exception as e:
            logging.error(f"Error during streaming top-level URL pull: {e}\n{traceback.format_exc()}")
            return -1
        finally:
            if 'temp_conn' in locals():
                temp_conn.close()
            if 'new_conn' in locals():
                new_conn.close()

        if progress_signal:
            progress_signal.emit(100)
            
        logging.info(f"Successfully pulled {inserted_count} top-level URLs to {new_db_path}")
        return inserted_count

    def close(self):
        """Closes the database connection."""
        self.conn.close()
