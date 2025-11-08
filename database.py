"""
Contains the DatabaseManager class for handling all SQLite operations.
"""

import sqlite3
import logging
from utils import get_top_level_url

class DatabaseManager:
    """Handles all SQLite database operations."""
    def __init__(self, db_path):
        self.db_path = db_path
        # Connect to the database, allowing the connection object to be shared across threads
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
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
            # --- ADDED: Index on 'scraped' column for fast lookups ---
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

    def add_links(self, links, add_top_level_too=False):
        """
        Adds a list of new links to the database, ignoring duplicates.
        Optionally adds their top-level counterparts as well.
        """
        # Normalize all incoming links by removing trailing slashes and duplicates
        normalized_links_input = {link.rstrip('/') for link in links}

        links_to_add = []
        if add_top_level_too:
            processed_links = set()
            for link in normalized_links_input:
                # Add the full link if it hasn't been processed in this batch
                if link not in processed_links:
                    links_to_add.append((link,))
                    processed_links.add(link)
                # Extract and add the top-level link if it's valid and not already processed
                top_level = get_top_level_url(link) # this will also be normalized
                if top_level and top_level not in processed_links:
                     links_to_add.append((top_level,))
                     processed_links.add(top_level)
        else:
            # If not adding top-level, just prepare the original links
            links_to_add = [(link,) for link in normalized_links_input]

        if links_to_add:
            with self.conn:
                # INSERT OR IGNORE gracefully handles duplicates; they are simply not inserted
                self.conn.executemany("INSERT OR IGNORE INTO links (url) VALUES (?)", links_to_add)

    def get_unscraped_links(self):
        """Gets all unscraped links (status 0)."""
        with self.conn:
            cursor = self.conn.execute("SELECT url FROM links WHERE scraped = 0")
            return [row[0] for row in cursor.fetchall()]
            
    def get_all_links(self):
        """Gets all links from the database."""
        with self.conn:
            cursor = self.conn.execute("SELECT url FROM links")
            return [row[0] for row in cursor.fetchall()]

    def get_unscraped_links_missing_titles(self):
        """Gets all unscraped links (status 0) that are missing a valid title."""
        with self.conn:
            cursor = self.conn.execute("SELECT url FROM links WHERE scraped = 0 AND (title IS NULL OR title = 'No Title Found' OR title = 'Scrape Failed' OR title = '')")
            return [row[0] for row in cursor.fetchall()]

    def get_failed_links(self):
        """Gets all failed links (status 2)."""
        with self.conn:
            cursor = self.conn.execute("SELECT url FROM links WHERE scraped = 2")
            return [row[0] for row in cursor.fetchall()]

    def get_links_missing_page_data(self):
        """Gets all *non-failed* links that are missing page data."""
        with self.conn:
            cursor = self.conn.execute("SELECT url FROM links WHERE scraped != 2 AND (page_data IS NULL OR page_data = '')")
            return [row[0] for row in cursor.fetchall()]

    def get_keyword_matches(self):
        """Gets all columns for rows that have a keyword match."""
        # This function is retained but not used for threshold check.
        with self.conn:
            cursor = self.conn.execute("SELECT * FROM links WHERE keyword_match IS NOT NULL AND keyword_match != ''")
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return columns, rows

# --- database.py: inside DatabaseManager class ---

    def get_keyword_matches_by_threshold(self, keywords, threshold):
        """
        Gets all columns for rows whose page_data contains at least 'threshold' 
        unique keywords from the provided 'keywords' list.
        """
        if not keywords:
            return [], [] 

        with self.conn:
            # Fetch all rows that have page data
            cursor = self.conn.execute("SELECT * FROM links WHERE page_data IS NOT NULL AND page_data != ''")
            initial_rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]

        if not initial_rows:
            return columns, []

        # --- MODIFIED: Prepare search terms exactly like in scraper.py ---
        # Map original keyword to the search term (padded or non-padded)
        search_terms_map = {} 
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if ' ' in keyword_lower:
                search_term = keyword_lower
            else:
                search_term = f" {keyword_lower} " 
            search_terms_map[keyword] = search_term 
        # --- END MODIFIED ---

        # Find the index of the 'page_data' column
        try:
            page_data_index = columns.index('page_data')
        except ValueError:
            logging.error("Database table missing 'page_data' column. Cannot perform threshold check.")
            return columns, []

        filtered_rows = []
        for row_tuple in initial_rows:
            page_data = row_tuple[page_data_index]
            
            if not page_data:
                continue

            page_data_lower = str(page_data).lower()
            # Pad the page data for reliable matching (crucial consistency!)
            page_data_padded = f" {page_data_lower} " 
            
            unique_matches = set()
            
            for original_keyword, search_term in search_terms_map.items():
                if search_term in page_data_padded:
                    unique_matches.add(original_keyword)
            
            # Apply the threshold
            if len(unique_matches) >= threshold:
                filtered_rows.append(row_tuple)

        logging.info(f"Found {len(filtered_rows)} links meeting the threshold of {threshold} unique matches.")
        return columns, filtered_rows
        
        
    def update_links_batch(self, update_data):
        """
        Updates a batch of links with status, title, keyword, and page data.
        Expects a list of tuples: [(status, title, keyword_match, page_data, url), ...]
        """
        if not update_data:
            return
        with self.conn:
            self.conn.executemany("UPDATE links SET scraped = ?, title = ?, keyword_match = ?, page_data = ? WHERE url = ?", update_data)
            
    def update_titles_batch(self, update_data):
        """
        Updates only the titles for a batch of links, leaving the scraped status unchanged.
        Expects a list of tuples: [(title, url), ...]
        """
        if not update_data:
            return
        with self.conn:
            self.conn.executemany("UPDATE links SET title = ? WHERE url = ?", update_data)

    def reset_failed_links(self):
        """Resets all failed links back to unscraped (status 0) for a retry."""
        with self.conn:
            self.conn.execute("UPDATE links SET scraped = 0 WHERE scraped = 2")

    def reset_links_missing_page_data(self):
        """Resets all non-failed links missing page data back to unscraped (status 0)."""
        with self.conn:
            self.conn.execute("UPDATE links SET scraped = 0 WHERE scraped != 2 AND (page_data IS NULL OR page_data = '')")

    def get_total_link_count(self):
        """Gets the total number of unique links in the database."""
        with self.conn:
            return self.conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]

    def pull_top_level_to_new_db(self, new_db_path):
        """Pulls all top-level URLs into a new database file, handling schema differences."""
        all_links_rows = []
        source_column_names = []
        with self.conn:
            cursor = self.conn.execute("SELECT * FROM links")
            all_links_rows = cursor.fetchall()
            # Get column names from the source database
            source_column_names = [desc[0].lower() for desc in cursor.description]

        top_level_rows_to_insert = []
        for row_tuple in all_links_rows:
            # Create a dictionary for easy, safe access by column name
            row_dict = dict(zip(source_column_names, row_tuple))
            url = row_dict.get('url')
            
            # Check if it's a top-level URL
            if url and get_top_level_url(url) == url:
                # Build a new tuple for insertion, explicitly mapping columns
                # This safely handles source DBs that don't have the new columns
                new_row_tuple = (
                    row_dict.get('id'),
                    row_dict.get('url'),
                    row_dict.get('scraped', 0),
                    row_dict.get('title'),
                    row_dict.get('keyword_match'), # Will be None if column doesn't exist in source
                    row_dict.get('page_data')      # Will be None if column doesn't exist in source
                )
                top_level_rows_to_insert.append(new_row_tuple)

        if not top_level_rows_to_insert:
            logging.info("No top-level URLs found to pull.")
            return 0 # Indicate that no URLs were found

        try:
            new_conn = sqlite3.connect(new_db_path)
            with new_conn:
                # Create the new table with the full, current schema
                new_conn.execute("""
                    CREATE TABLE IF NOT EXISTS links (
                        id INTEGER PRIMARY KEY, url TEXT UNIQUE NOT NULL,
                        scraped INTEGER DEFAULT 0, title TEXT,
                        keyword_match TEXT, page_data TEXT )""")
                # Insert the prepared tuples
                new_conn.executemany("INSERT OR IGNORE INTO links (id, url, scraped, title, keyword_match, page_data) VALUES (?, ?, ?, ?, ?, ?)", top_level_rows_to_insert)
            new_conn.close()
            logging.info(f"Successfully pulled {len(top_level_rows_to_insert)} top-level URLs to {new_db_path}")
            return len(top_level_rows_to_insert)
        except Exception as e:
            logging.error(f"Failed to create top-level DB: {e}")
            return -1 # Indicate an error occurred

    def close(self):
        """Closes the database connection."""
        self.conn.close()