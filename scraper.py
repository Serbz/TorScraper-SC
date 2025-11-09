"""
Contains the core asynchronous web scraping logic.
"""

import logging
import random
import asyncio
import traceback
import time 
import warnings
import re # <-- Import re at top level
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from curl_cffi.requests import AsyncSession
# --- FIX: Import specific errors to suppress them from GUI ---
from curl_cffi.requests.exceptions import ProxyError
from curl_cffi.curl import CurlError
# --- END FIX ---

from utils import PROXIES, HEADERS, is_junk_url
from database import DatabaseManager

# Suppress the XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# --- Efficiency Suggestion: Filter out common non-HTML file extensions ---
NON_HTML_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf', '.zip', '.rar', 
    '.exe', '.css', '.js', '.mp3', '.mp4', '.avi', '.mkv', '.mov',
    '.iso', '.dmg', '.tar', '.gz', '.7z', '.xml', '.rss'
}

async def get_data(url, task_id, worker_id, active_tasks_dict, active_tasks_lock): # <-- Added worker_id
    """Asynchronously fetches the content of a URL using a random proxy."""
    chosen_proxy = random.choice(PROXIES)
    logging.info(f"[{worker_id}] Fetching: {url} | Proxy: {chosen_proxy}")

    try:
        site_name = urlparse(url).netloc
    except Exception:
        site_name = url
    
    with active_tasks_lock:
        # Add new fields for bytes and finish time
        active_tasks_dict[task_id] = {
            "worker_id": worker_id, # <-- STORE WORKER ID
            "url": url, 
            "site": site_name, 
            "bytes": 0,
            "title": "Pending...", # <-- FIX (Request 2): Add title field
            "finished_at": None
        }

    try:
        async with AsyncSession() as session:
            response = await session.get(url, timeout=60, headers=HEADERS, proxy=chosen_proxy)
            if response.status_code == 200:
                logging.info(f"[{worker_id}] [SUCCESS] Fetched: {url}")
                data = response.content # Get bytes
                with active_tasks_lock:
                    if task_id in active_tasks_dict:
                        active_tasks_dict[task_id]['bytes'] = len(data)
                return data # Return bytes
            else:
                logging.warning(f"[{worker_id}] [FAIL] Failed to fetch {url} | Status: {response.status_code}")
    except Exception as e:
        # --- FIX: Log common network errors to DEBUG (file only) ---
        if isinstance(e, (ProxyError, CurlError)):
            # This is an expected network failure (e.g., site is down).
            # Log it at DEBUG level so it goes to the file but not the GUI.
            logging.debug(f"[{worker_id}] [NETWORK FAIL] Fetching {url}: {e}")
        elif not isinstance(e, asyncio.CancelledError):
            # This is an unexpected error.
            logging.error(f"[{worker_id}] [ERROR] Fetching {url}: {e}")
        # --- END FIX ---
        raise # Re-raise the exception to be handled by the worker
    
    finally:
        with active_tasks_lock:
            if task_id in active_tasks_dict:
                # Mark as finished instead of deleting
                active_tasks_dict[task_id]['finished_at'] = time.time()
                # --- FIX (Request 2): Set failed title ---
                if active_tasks_dict[task_id]['title'] == "Pending...":
                     active_tasks_dict[task_id]['title'] = "Scrape Failed"
                # --- END FIX ---
    
    return None 

def parse_page_content(html_content, base_url, onion_only_mode=False, titles_only_mode=False, keywords=None):
    """
    Parses HTML to find the page title, all absolute links, page text, and a matching keyword.
    Returns: (found_links_list, title_string, page_text_string, matching_keyword_string)
    """
    soup = BeautifulSoup(html_content, 'lxml')

    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else "No Title Found"

    if titles_only_mode:
        logging.info(f"Parsed Title Only: '{title}' from {base_url}")
        return [], title, "", None # Return empty values for other fields
    
    page_text = soup.get_text(separator=' ', strip=True)
    matching_keyword = None

    # --- FIX (Request 1): Handle REGEX: prefix ---
    if keywords:
            try:
                page_text_lower = page_text.lower()
                # Pad the whole document with spaces for reliable whole-word matching
                page_text_padded = f" {page_text_lower} " 
                
                unique_matches_found = set()
                
                for keyword in keywords:
                    if keyword.startswith("REGEX: "):
                        # This is a regular expression
                        try:
                            # Get the regex pattern (remove "REGEX: ")
                            pattern = keyword[7:].strip()
                            # Run re.search on the *original* case-sensitive text
                            if re.search(pattern, page_text, re.IGNORECASE): 
                                unique_matches_found.add(keyword) # Add the full "REGEX: ..." string
                                logging.info(f"[KEYWORD HIT] Regex '{pattern}' matched at {base_url}")
                        except re.error as e:
                            logging.warning(f"Invalid regex in keyword file: '{keyword}'. Error: {e}")
                    
                    else:
                        # This is a plain text keyword
                        keyword_lower = keyword.lower()
                        
                        if ' ' in keyword_lower:
                            # Multi-word: search as-is
                            padded_search_term = keyword_lower
                        else:
                            # Single word: use word boundary logic
                            padded_search_term = f" {keyword_lower} " 

                        if padded_search_term in page_text_padded:
                            unique_matches_found.add(keyword) # Store the original cased keyword
                            logging.info(f"[KEYWORD HIT] Found '{keyword}' at {base_url}")
                
                if unique_matches_found:
                    # Store keywords alphabetically for consistency
                    matching_keyword = ", ".join(sorted(list(unique_matches_found)))
                else:
                    matching_keyword = None

            except Exception as e:
                logging.error(f"Error during keyword search at {base_url}: {e}")
    # --- END FIX ---

    found_links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        absolute_link = urljoin(base_url, href).rstrip('/')
        
        # --- FIX: Add junk filter ---
        # Note: This is redundant if database.py is also filtering,
        # but provides defense-in-depth.
        if is_junk_url(absolute_link):
            continue
        # --- END FIX ---
        
        parsed_link = urlparse(absolute_link)
        
        if any(parsed_link.path.lower().endswith(ext) for ext in NON_HTML_EXTENSIONS):
            continue
        
        if parsed_link.scheme in ['http', 'https']:
            if onion_only_mode:
                if parsed_link.netloc.endswith('.onion'):
                    found_links.add(absolute_link)
            else:
                found_links.add(absolute_link)

    logging.info(f"Parsed {base_url} | Title: '{title}' | Found {len(found_links)} new links.")
    return list(found_links), title, page_text, matching_keyword


async def scraper_worker_task(worker_id, queue, stop_event, pause_event, 
                            active_tasks_dict, active_tasks_lock, 
                            onion_only_mode, titles_only_mode, 
                            keywords, save_page_data_mode, # <-- Changed
                            top_level_only_mode):
    """
    A worker (consumer) that pulls a (db, url, task_id) tuple from the 
    queue and processes it.
    """
    while not stop_event.is_set():
        # --- FIX: Status defaults to 2 (fail) ---
        status = 2 # Assume fail
        # --- END FIX ---
        
        # --- FIX: Need url and db handle in finally block ---
        url = None
        db = None
        task_id = None
        # --- END FIX ---
        
        # --- FIX: Define variables for DB update ---
        new_links = []
        title_to_save = "Scrape Failed"
        keyword_match_to_save = None
        page_data_to_save = None
        # --- END FIX ---
            
        try:
            # --- 1. Check for Pause Event ---
            if pause_event.is_set():
                logging.info(f"[{worker_id}] Paused...")
                while pause_event.is_set():
                    if stop_event.is_set(): break
                    await asyncio.sleep(0.5)
                if stop_event.is_set(): break
                logging.info(f"[{worker_id}] Resuming...")

            # --- 2. Get Work from Queue ---
            try:
                # Wait 1 second for an item, then re-check stop/pause
                db, url, task_id = await asyncio.wait_for(queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue # Loop back to check stop/pause
            
            
            try:
                # --- 3. Process the URL ---
                result = await get_data(url, task_id, worker_id, active_tasks_dict, active_tasks_lock)
                
                if stop_event.is_set():
                    logging.warning(f"[{worker_id}] Stop requested. Discarding result for {url}. DB not updated.")
                    continue 
                    
                # --- This block is now only for SUCCESSFUL fetches ---
                if isinstance(result, bytes): # Fetch success
                    try:
                        # Decode content
                        html_content = result.decode('utf-8', errors='ignore')
                        
                        # Parse content
                        new_links, title, page_text, matching_keyword = parse_page_content(
                            html_content, url, onion_only_mode, titles_only_mode, keywords
                        )
                        
                        logging.info(f"[{worker_id}] Parsed Title: '{title}' from {url}")
                        
                        title_to_save = title
                        keyword_match_to_save = matching_keyword
                        
                        # --- FIX (Request 2): Update title in active dict ---
                        with active_tasks_lock:
                            if task_id in active_tasks_dict:
                                active_tasks_dict[task_id]['title'] = title_to_save
                        # --- END FIX ---
                        
                        # --- Updated Save Page Data Logic ---
                        if save_page_data_mode == "All":
                            page_data_to_save = page_text 
                        elif save_page_data_mode == "Keyword Match" and matching_keyword:
                            page_data_to_save = page_text
                        # If mode is "None", page_data_to_save remains None
                        # --- End Updated Logic ---
                        
                        # --- BUG FIX: titles_only_mode must also set status=1 ---
                        if titles_only_mode:
                            # db.update_titles_batch([(title_to_save, url)]) # <-- OLD
                            status = 1 # Mark as success
                            # We still `continue` to skip the main DB logic
                            # The 'finally' block will now handle the DB update
                        else:
                            status = 1 # Full scrape success
                        # --- END BUG FIX ---
                    
                    except Exception as e:
                        logging.error(f"[{worker_id}] Error parsing content from {url}: {e}")
                        # status remains 2, title remains "Scrape Failed"
                
                # Note: If result is None (e.g., 404), status remains 2
                # and title_to_save remains "Scrape Failed", which is correct.

            except asyncio.CancelledError:
                logging.info(f"[{worker_id}] Task for {url} was cancelled.")
                # Re-raise to be caught by outer loop and exit
                raise
            except Exception as e:
                # --- FIX: Log common network errors to DEBUG (file only) ---
                # Check if the exception is a common, expected network error.
                # We want to log these to the file (DEBUG) but not flood the GUI (ERROR).
                if isinstance(e, (ProxyError, CurlError)):
                    # Log at DEBUG level: file_handler will see this, gui_handler will NOT.
                    logging.debug(f"[{worker_id}] Network error for {url}: {e}\n{traceback.format_exc()}")
                else:
                    # This is an unexpected error (e.g., parsing, logic), log it to the GUI.
                    logging.error(f"[{worker_id}] Error in worker processing {url}: {e}\n{traceback.format_exc()}")
                # --- END FIX ---
                
                # Status is already 2 (fail), title is "Scrape Failed"
                # We will now fall through to the finally block to update the DB
            finally:
                # --- 5. Signal Task Completion & DB Update ---
                
                # Don't update DB if stop was requested
                if stop_event.is_set():
                    logging.warning(f"[{worker_id}] Stop requested. Final DB update for {url} skipped.")
                # --- FIX: This block now correctly handles all cases ---
                else:
                    try:
                        if db and url: # Ensure we have a DB and URL to update
                            
                            # --- BUG FIX: titles_only_mode now updates status ---
                            if titles_only_mode:
                                # This now correctly updates status AND title
                                db.update_status_and_title_batch([(status, title_to_save, url)])
                            # --- END BUG FIX ---
                            
                            else:
                                # This is the main update for full-scrape mode (success or fail)
                                db.update_links_batch([(status, title_to_save, keyword_match_to_save, page_data_to_save, url)])
                            
                            # Add new links (only happens on status=1 and not titles_only)
                            if status == 1 and new_links and not titles_only_mode:
                                db.add_links(new_links, add_top_level_too=top_level_only_mode)
                                
                    except Exception as e:
                        logging.error(f"[{worker_id}] CRITICAL: Failed to update DB for {url}: {e}")
                # --- END FIX ---

                with active_tasks_lock:
                    if task_id in active_tasks_dict:
                        active_tasks_dict[task_id]['status'] = status
                
                if db: # db might be None if queue.get() times out
                    queue.task_done()

        except asyncio.CancelledError:
            logging.info(f"[{worker_id}] Worker shutting down.")
            break # Exit the main while loop
        except Exception as e:
            logging.error(f"[{worker_id}] Critical worker error: {e}")
            await asyncio.sleep(0.1) 


async def scraper_main_producer(queue, args, stop_event, 
                              rescrape_mode=False, top_level_only_mode=False, 
                              onion_only_mode=False, titles_only_mode=False, keywords=None,
                              save_page_data_mode="Keyword Match", # <-- Changed
                              rescrape_page_data_mode=False): 
    """
    The main async function (PRODUCER) for the scraper logic.
    It finds links and adds them to the queue for the workers.
    """
    db = DatabaseManager(args.db_file)
    
    # --- Log startup modes ---
    if top_level_only_mode:
        logging.info("[INFO] Starting in TOP-LEVEL-ONLY scrape mode.")
    if rescrape_mode:
        logging.info("[INFO] Starting in RESCRAPE mode.")
    if rescrape_page_data_mode: 
        logging.info("[INFO] Starting in RESCRAPE FOR PAGE DATA mode.")
    if onion_only_mode:
        logging.info("[INFO] Starting in ONION-ONLY scrape mode.")
    if titles_only_mode:
        logging.info("[INFO] Starting in TITLES-ONLY scrape mode.")
    if keywords:
        logging.info(f"[INFO] Starting with {len(keywords)} keywords.")
    
    logging.info(f"[INFO] Save Page Data mode: {save_page_data_mode}") # <-- Changed

    processed_in_this_run = set()

    try:
        if rescrape_mode:
            failed_links = db.get_failed_links()
            if not failed_links:
                logging.info("[INFO] No failed links found to rescrape.")
            else:
                logging.info(f"Found {len(failed_links)} failed links. Adding to queue...")
                # --- FIX: Removed db.reset_failed_links() ---
                # We will not reset the links to 0. The worker will
                # pull a '2' and update it to '1' or keep it '2'.
                # logging.info(f"Found {len(failed_links)} failed links. Resetting and retrying...")
                # db.reset_failed_links() # <-- REMOVED
                # --- END FIX ---
                links_to_process = failed_links
                
                if onion_only_mode:
                    links_to_process = [link for link in failed_links if urlparse(link).netloc.endswith('.onion')]
                
                logging.info(f"--- Adding {len(links_to_process)} failed links to queue ---")
                for url in links_to_process:
                    if stop_event.is_set(): break
                    if url not in processed_in_this_run:
                        # --- FIX: Add junk filter ---
                        if is_junk_url(url):
                            logging.warning(f"Skipping junk URL (rescrape): {url}")
                            continue
                        # --- END FIX ---
                        task_id = f"{url}_{random.randint(10000, 99999)}"
                        # --- REVAMP: Use non-blocking queue.put ---
                        while not stop_event.is_set():
                            try:
                                queue.put_nowait((db, url, task_id))
                                processed_in_this_run.add(url)
                                break # Put successful, move to next url
                            except asyncio.QueueFull:
                                await asyncio.sleep(0.5) # Poll
                        # --- END REVAMP ---
        
        elif rescrape_page_data_mode:
            links_missing_data = db.get_links_missing_page_data()
            if not links_missing_data:
                logging.info("[INFO] No links found missing page data.")
            else:
                logging.info(f"Found {len(links_missing_data)} links missing page data. Resetting and retrying...")
                db.reset_links_missing_page_data()
                links_to_process = links_missing_data
                if onion_only_mode:
                    links_to_process = [link for link in links_missing_data if urlparse(link).netloc.endswith('.onion')]
                
                logging.info(f"--- Adding {len(links_to_process)} links missing data to queue ---")
                for url in links_to_process:
                    if stop_event.is_set(): break
                    if url not in processed_in_this_run:
                        # --- FIX: Add junk filter ---
                        if is_junk_url(url):
                            logging.warning(f"Skipping junk URL (rescrape data): {url}")
                            continue
                        # --- END FIX ---
                        task_id = f"{url}_{random.randint(10000, 99999)}"
                        # --- REVAMP: Use non-blocking queue.put ---
                        while not stop_event.is_set():
                            try:
                                queue.put_nowait((db, url, task_id))
                                processed_in_this_run.add(url)
                                break # Put successful, move to next url
                            except asyncio.QueueFull:
                                await asyncio.sleep(0.5) # Poll
                        # --- END REVAMP ---

        else: # Normal or top-level scraping mode
            if args.urls:
                logging.info(f"[INFO] Adding/updating {len(args.urls)} starting URLs from file into database...")
                db.add_links(args.urls, add_top_level_too=top_level_only_mode)

            iteration_count = 0
            while not stop_event.is_set():
                iteration_count += 1
                
                if stop_event.is_set(): break
                
                if titles_only_mode:
                    links_for_this_depth = db.get_unscraped_links_missing_titles()
                else:
                    links_for_this_depth = db.get_unscraped_links()

                if onion_only_mode:
                    links_for_this_depth = [link for link in links_for_this_depth if urlparse(link).netloc.endswith('.onion')]
                    logging.info(f"[INFO] Filtered to {len(links_for_this_depth)} .onion links for this iteration.")

                links_for_this_depth = [l for l in links_for_this_depth if l not in processed_in_this_run]

                if not links_for_this_depth:
                    logging.info(f"[INFO] No new unscraped links found. Scrape complete.")
                    break
                    
                links_to_process = []
                if top_level_only_mode:
                    top_level_targets = {get_top_level_url(link) for link in links_for_this_depth}
                    top_level_targets.discard(None)
                    db.add_links(list(top_level_targets)) 
                    all_unscraped_urls = set(db.get_unscraped_links())
                    links_to_process = [url for url in top_level_targets if url in all_unscraped_urls and url not in processed_in_this_run]
                    logging.info(f"\n--- Starting Top-Level Iteration {iteration_count} --- (Processing {len(links_to_process)} unique domains)")
                else:
                    links_to_process = links_for_this_depth
                    logging.info(f"\n--- Starting Depth Iteration {iteration_count} --- (Processing {len(links_to_process)} links)")

                if not links_to_process:
                    logging.info("[INFO] All potential links for this iteration have been processed. Scrape complete.")
                    break
                
                logging.info(f"--- Iteration {iteration_count}: Adding {len(links_to_process)} new links to queue ---")
                
                for url in links_to_process:
                    if stop_event.is_set(): break
                    
                    # --- FIX: Add junk filter ---
                    if is_junk_url(url):
                        logging.warning(f"Skipping junk URL (new scrape): {url}")
                        processed_in_this_run.add(url) # Add to set so we don't re-check
                        continue
                    # --- END FIX ---
                    
                    task_id = f"{url}_{random.randint(10000, 99999)}"
                    # --- REVAMP: Use non-blocking queue.put ---
                    while not stop_event.is_set():
                        try:
                            queue.put_nowait((db, url, task_id))
                            processed_in_this_run.add(url)
                            break # Put successful, move to next url
                        except asyncio.QueueFull:
                            await asyncio.sleep(0.5) # Poll
                    # --- END REVAMP ---
                
                if stop_event.is_set(): break

                # --- FIX: Replaced await queue.join() with a polling loop ---
                # This allows the producer to check the stop_event frequently
                # instead of blocking until the entire queue is drained.
                logging.info(f"--- Iteration {iteration_count} links queued. Waiting for queue to drain... ---")
                while not queue.empty():
                    if stop_event.is_set():
                        logging.warning("Stop detected during queue drain. Breaking producer loop.")
                        break
                    await asyncio.sleep(1) # Poll every second
                
                if stop_event.is_set(): break
                # await queue.join() # <-- REMOVED BLOCKING CALL
                # --- END FIX ---

                logging.info(f"--- Iteration {iteration_count} queue drained. Checking for new links. ---")
                
                if titles_only_mode:
                    logging.info("[INFO] Titles-Only mode complete. Stopping producer.")
                    break 
            
    except asyncio.CancelledError:
        logging.info("Producer task was cancelled.")
    except Exception as e:
        logging.error(f"Error in scraper producer: {e}\n{traceback.format_exc()}")
    finally:
        total_links = db.get_total_link_count()
        logging.info(f"\n[INFO] Producer has finished. Total unique links in database: {total_links}")
        db.close()
