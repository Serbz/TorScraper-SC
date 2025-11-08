# Tor Scraper Application

************************************************************************************************************************

******************* YOU MUST DOWNLOAD TOR AND PUT IT IN A FOLDER CALLED TOR IN THE SCRIPT DIRECTORY ********************

******* https://archive.torproject.org/tor-package-archive/torbrowser/15.0/tor-expert-bundle-windows-x86_64-15.0.tar.gz *******

************************************************************************************************************************



A powerful, multi-threaded web scraping tool with a graphical user interface (GUI) built using PySide6. This application uses **Tor** for network anonymity and features real-time **network activity monitoring** powered by Scapy and Npcap.

---

## Features

* **Tor Integration**: Manages a local Tor process, ensuring network requests are routed for anonymity. Supports signaling a **New Tor Identity** (NEWNYM).

* **Asynchronous Scraping**: Utilizes `asyncio` and `curl_cffi` for fast, concurrent fetching of URLs using a multi-worker, producer-consumer model.

* **Network Activity Viewer**: A dedicated dialog for real-time monitoring of active scrape tasks and the Tor process's total and current network I/O (Download/Upload Rate).

* **Database Management**: Stores all scraped data (URL, Title, Status, Page Data, Keyword Matches) in a **SQLite database**.

* **Advanced Scraping Modes**:

  * **Rescrape Failed** / **Rescrape Missing Data**.

  * **Top-Level Only** (scrapes only the initial domains, not internal links).

  * **Titles Only** (quickly fetches titles without full scraping).

  * **Onion-Only** filtering.

* **Keyword Search**: Supports searching for custom keywords and pulling results into a temporary database based on a configurable match **threshold**.

---

## Requirements & Setup (Critical)

This application has specific system requirements, especially on Windows, due to its deep integration with network monitoring tools.

### Python & Dependencies

The application includes an **auto-installer** that will attempt to install all required Python libraries (e.g., `PySide6`, `scapy`, `curl_cffi`, `lxml`) if they are missing.

### Windows-Specific Requirements

1. **Administrator Privileges**: The application will attempt to relaunch itself with **Administrator rights** on startup. This is **MANDATORY** for the network monitoring feature to work correctly.

2. **Npcap Driver**: The `scapy` library requires the **Npcap** driver to intercept network traffic.

   * The application will automatically check for this driver on launch.

   * If Npcap is not found, the application will prompt the user to **download and install** it before continuing.

> **Note**: If Npcap is installed, the application will enforce a **restart** to ensure the new driver is correctly loaded and detected by Scapy.

---

## Usage

### 1. Launch & Initial Setup

1. Run the main script (`main.py`). The application will perform dependency checks and attempt to relaunch as **Administrator**.

2. The application will automatically configure and launch the internal **Tor process**. Wait for the **Tor Status** in the logs to confirm **full bootstrap** before proceeding.

3. If this is the first run, ensure **Npcap** is installed as prompted.

### 2. Configure Parameters

| Parameter | Description |
| ----- | ----- |
| **Database File** | **MANDATORY**. Select or create the SQLite file (.sqlite or .db) to store all scraped results. |
| **URL File** | *Optional*. A .txt file containing starting URLs for the scraper. |
| **Keyword File** | *Optional*. A .txt file containing keywords (one per line) used for keyword-based saving and searching. |
| **Concurrent Requests** | The number of simultaneous connections (workers) to run. Default is 150. |
| **Checkbox Modes** | Toggle options like `Only scrape .onion links`, `Scrape Top-Level URLs Only`, `Scrape Titles Only`, and `Save page data`. |

### 3. Start & Monitor Scraping

1. Click **"Start Scraping"**.

2. Click **"Network Activity"** to open the real-time monitor. This view shows:

   * The status and byte count of **Active Scrape Tasks**.

   * The current I/O Rate and **Total Session I/O** of the Tor process.

3. If scraping performance drops, click **"New Tor Identity"** to acquire a fresh Tor circuit.

### 4. Database Actions (Menu)

Access the **DB Actions** menu for utility functions:

* **View DB File**: Opens a paginated viewer for any selected database file.

* **Pull Keyword Matches**: Prompts for a keyword file and a **minimum match threshold**. It then processes the database and displays matching rows in a separate viewer.

* **Pull Top Level URLs**: Creates a new database containing *only* the top-level domain URLs from the source database.

* **Export Links from DB**: Exports all URLs from a selected database into a plain text file.

---

## Important Notes

* **Keyword Matching**: The matching logic is case-insensitive. For single words (e.g., `bitcoin`), the scraper enforces **whole-word matching** (i.e., it won't match `bitcoiner`). For multi-word phrases, it searches for the phrase as-is.

* **Database Viewer**: The built-in `DbViewer` is a low-memory, **paginated** tool designed for viewing large result sets. It also includes right-click options to **Copy** cell/row data, **Set NULL**, or **Delete** rows.

* **Restart/Relaunch**: The **"Reload Script"** button provides a quick way to save parameters and relaunch the application.
