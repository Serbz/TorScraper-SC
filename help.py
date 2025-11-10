"""
Contains the HelpDialog QDialog class for the application.
"""

import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, 
                               QDialogButtonBox)
from PySide6.QtCore import Qt

class HelpDialog(QDialog):
    """
    A simple, non-blocking dialog to display help information.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setGeometry(300, 300, 600, 500)

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.set_help_text()
        layout.addWidget(self.text_edit)

        # OK Button
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def set_help_text(self):
        """Sets the content of the help text viewer."""
        
        help_text = """
        <h2>Tor Scraper GUI Help</h2>
        
        <h3>Parameters</h3>
        <ul>
            <li><b>Database File:</b> The SQLite file to save all scraped data.</li>
            <li><b>URL File:</b> A .txt file containing a list of starting URLs to begin a scrape.</li>
            <li><b>Keyword File:</b> A .txt file containing keywords (one per line) to search for.</li>
            <li><b>Concurrent Requests:</b> The number of parallel workers to use for scraping.</li>
            <li><b>Only scrape .onion links:</b> If checked, workers will ignore any non-.onion links.</li>
            <li><b>Keyword Search:</b> If checked, the scraper will search the text of each page for keywords from the file.</li>
            <li><b>Scrape Top-Level URLs Only:</b> If checked, the scraper will only scrape base domains (e.g., http://example.com) and not deep links.</li>
            <li><b>Scrape Titles Only:</b> A special mode to quickly get titles for unscraped links.</li>
            <li><b>Save page data:</b> If checked, the full text of every page is saved. If unchecked, data is only saved if a keyword matches.</li>
        </ul>

        <h3>Keyword File Regex</h3>
        <p>You can use regular expressions in your keyword file by prefixing the line with <b>REGEX: </b> (note the space).</p>
        <p>Example: <code>REGEX: \s\w+\d{2}\w+\s</code></p>
        <p>If a regex match is found, the full regex string will be stored in the <code>keyword_match</code> column.</p>
        
        <h3>Scrapes Menu</h3>
        <ul>
            <li><b>Rescrape Failed:</b> Re-queues all links marked as 'failed' (status 2) for another attempt.</li>
            <li><b>Rescrape for page data:</b> Re-queues all *successful* links that are missing page data. Useful if you ran a scrape with "Save page data" un-checked and now want to fill in the data.</li>
        </ul>

        <h3>DB Actions Menu</h3>
        <ul>
            <li><b>View DB File:</b> Opens any SQLite file in the paginated database viewer.</li>
            <li><b>Pull Keyword Matches:</b> Filters the *current* database file for links that match your keywords by a certain threshold. This queries the <code>keyword_match</code> column.</li>
            <li><b>Pull Top Level URLs:</b> Creates a new database containing only the top-level domains from the current database.</li>
            <li><b>Export Links from DB:</b> Exports all URLs from a selected database to a .txt file.</li>
        </ul>
        
        <h3>Database Viewer</h3>
        <p>You can right-click on rows to copy cell data, copy the full row, or delete the row from the database (if not read-only).</p>
        <p><b>Copying Full Page Data:</b> If you copy a cell or row containing truncated page data, the *full, untruncated* page data will be copied to your clipboard.</p>
        """
        self.text_edit.setHtml(help_text)