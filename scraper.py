"""
Contains the core asynchronous web scraping logic.
"""

import logging
import random
import asyncio
import traceback
import time 
import warnings
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from curl_cffi.requests import AsyncSession

from utils import PROXIES, HEADERS
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
        # Don't log CancelledError as an error
        if not isinstance(e, asyncio.CancelledError):
            logging.error(f"[{worker_id}] [ERROR] Fetching {url}: {e}")
        raise # Re-raise the exception to be handled by the worker
    
    finally:
        with active_tasks_lock:
            if task_id in active_tasks_dict:
                # Mark as finished instead of deleting
                active_tasks_dict[task_id]['finished_at'] = time.time()
    
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
    page_text_lower = "" 
    matching_keyword = None

    if keywords:
            try:
                # 1. Prepare and Pad Page Text (Only once!)
                page_text_lower = page_text.lower()
                # Pad the whole document with spaces for reliable whole-word matching
                page_text_padded = f" {page_text_lower} " 
                
                unique_matches_found = set()
                
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    
                    # 2. Determine Search Term
                    # If keyword contains a space (multi-word), search for it as-is.
                    if ' ' in keyword_lower:
                        padded_search_term = keyword_lower
                    # If it's a single word, pad it with spaces for whole-word matching.
                    else:
                        padded_search_term = f" {keyword_lower} " 

                    # 3. Perform Search
                    if padded_search_term in page_text_padded:
                        unique_matches_found.add(keyword) # Store the original, un-padded keyword (e.g., "AI")
                        logging.info(f"[KEYWORD HIT] Found '{keyword}' at {base_url}")
                
                # 4. Join all unique matches into a single, comma-separated string for storage
                if unique_matches_found:
                    # Store keywords alphabetically for consistency
                    matching_keyword = ", ".join(sorted(list(unique_matches_found)))
                else:
                    matching_keyword = None

            except Exception as e:
                logging.error(f"Error during keyword search at {base_url}: {e}")

            found_links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        absolute_link = urljoin(base_url, href).rstrip('/')
        parsed_link = urlparse(absolute_link)
        
        # --- Efficiency Suggestion: Filter links before adding ---
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
                            keywords, save_all_page_data,
                            top_level_only_mode):
    """
    A worker (consumer) that pulls a (db, url, task_id) tuple from the 
    queue and processes it.
    """
    while not stop_event.is_set():
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
            
            # --- MODIFIED: Added try/finally to guarantee task_done() ---
            try:
                # --- 3. Process the URL ---
                result = await get_data(url, task_id, worker_id, active_tasks_dict, active_tasks_lock)
                
                # --- STOP FIX: Check event *after* await ---
                if stop_event.is_set():
                    logging.warning(f"[{worker_id}] Stop requested. Discarding result for {url}. DB not updated.")
                    continue # Skips to finally, DB is not touched
                    
                new_links = []
                title_to_save = "Scrape Failed"
                status = 2 # Assume fail
                keyword_match_to_save = None
                page_data_to_save = None

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
                        
                        # Decide whether to save page data
                        if save_all_page_data:
                            page_data_to_save = page_text 
                        elif matching_keyword:
                            page_data_to_save = page_text 
                        
                        if titles_only_mode:
                            # Special case: Only update title, don't change status or add links
                            db.update_titles_batch([(title_to_save, url)])
                            continue # Skips to finally
                        else:
                            status = 1 # Full scrape success
                    
                    except Exception as e:
                        logging.error(f"[{worker_id}] Error parsing content from {url}: {e}")
                        # status remains 2, title remains "Scrape Failed"

                # --- STOP FIX: Check event *before* DB write ---
                if stop_event.is_set():
                    logging.warning(f"[{worker_id}] Stop requested. Discarding DB update for {url}.")
                    continue # Skips to finally, DB is not touched

                # --- 4. Update Database ---
                if titles_only_mode:
                    # This block is now only for title-only mode success
                    db.update_titles_batch([(title_to_save, url)])
                else:
                    # This block is for full scrape (success or fail)
                    db.update_links_batch([(status, title_to_save, keyword_match_to_save, page_data_to_save, url)])
                
                if status == 1 and new_links and not titles_only_mode:
                    db.add_links(new_links, add_top_level_too=top_level_only_mode)

            except asyncio.CancelledError:
                logging.info(f"[{worker_id}] Task for {url} was cancelled.")
                # Do not update DB, just let finally run.
            except Exception as e:
                logging.error(f"[{worker_id}] Error in worker processing {url}: {e}\n{traceback.format_exc()}")
                # Do not update DB, just let finally run.
            finally:
                # --- 5. Signal Task Completion ---
                # This *must* be called for every item, or queue.join() will hang.
                queue.task_done()
            # --- END MODIFIED ---

        except asyncio.CancelledError:
            logging.info(f"[{worker_id}] Worker shutting down.")
            break # Exit the main while loop
        except Exception as e:
            # This is a critical error outside the item processing loop
            logging.error(f"[{worker_id}] Critical worker error: {e}")
            await asyncio.sleep(0.1) 


async def scraper_main_producer(queue, args, stop_event, 
                              rescrape_mode=False, top_level_only_mode=False, 
                              onion_only_mode=False, titles_only_mode=False, keywords=None,
                              rescrape_page_data_mode=False): # Added new mode
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
    if rescrape_page_data_mode: # New log
        logging.info("[INFO] Starting in RESCRAPE FOR PAGE DATA mode.")
    if onion_only_mode:
        logging.info("[INFO] Starting in ONION-ONLY scrape mode.")
    if titles_only_mode:
        logging.info("[INFO] Starting in TITLES-ONLY scrape mode.")
    if keywords:
        logging.info(f"[INFO] Starting with {len(keywords)} keywords.")
    if args.save_all_page_data: # Accessing via args
        logging.info("[INFO] 'Save all page data' is ENABLED.")

    # Keep track of URLs we've *added* to the queue to avoid duplicates
    # in a single run (e.g., if link appears in DB multiple times)
    processed_in_this_run = set()

    try:
        if rescrape_mode:
            failed_links = db.get_failed_links()
            if not failed_links:
                logging.info("[INFO] No failed links found to rescrape.")
            else:
                logging.info(f"Found {len(failed_links)} failed links. Resetting and retrying...")
                db.reset_failed_links()
                links_to_process = failed_links
                if onion_only_mode:
                    links_to_process = [link for link in failed_links if urlparse(link).netloc.endswith('.onion')]
                
                logging.info(f"--- Adding {len(links_to_process)} failed links to queue ---")
                for url in links_to_process:
                    if stop_event.is_set(): break
                    if url not in processed_in_this_run:
                        task_id = f"{url}_{random.randint(10000, 99999)}"
                        await queue.put((db, url, task_id))
                        processed_in_this_run.add(url)
        
        # --- NEW MODE ---
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
                        task_id = f"{url}_{random.randint(10000, 99999)}"
                        await queue.put((db, url, task_id))
                        processed_in_this_run.add(url)
        # --- END NEW MODE ---

        else: # Normal or top-level scraping mode
            if args.urls:
                logging.info(f"[INFO] Adding/updating {len(args.urls)} starting URLs from file into database...")
                db.add_links(args.urls, add_top_level_too=top_level_only_mode)

            iteration_count = 0
            while not stop_event.is_set():
                iteration_count += 1
                
                # Producer doesn't need to check pause_event, workers do.
                if stop_event.is_set(): break
                
                if titles_only_mode:
                    links_for_this_depth = db.get_unscraped_links_missing_titles()
                else:
                    links_for_this_depth = db.get_unscraped_links()

                if onion_only_mode:
                    links_for_this_depth = [link for link in links_for_this_depth if urlparse(link).netloc.endswith('.onion')]
                    logging.info(f"[INFO] Filtered to {len(links_for_this_depth)} .onion links for this iteration.")

                # Filter out links already processed in this run
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
                    # Filter against all unscraped and already processed
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
                    task_id = f"{url}_{random.randint(10000, 99999)}"
                    await queue.put((db, url, task_id))
                    processed_in_this_run.add(url)
                
                if stop_event.is_set(): break

                # Wait for the queue to drain before finding new links
                logging.info(f"--- Iteration {iteration_count} links queued. Waiting for queue to drain... ---")
                await queue.join()
                
                if stop_event.is_set(): break

                logging.info(f"--- Iteration {iteration_count} queue drained. Checking for new links. ---")
                
                if titles_only_mode:
                    logging.info("[INFO] Titles-Only mode complete. Stopping producer.")
                    break # Titles only mode doesn't loop
                
                # Check for links again in the next loop
            
    except Exception as e:
        logging.error(f"Error in scraper producer: {e}\n{traceback.format_exc()}")
    finally:
        total_links = db.get_total_link_count()
        logging.info(f"\n[INFO] Producer has finished. Total unique links in database: {total_links}")
        db.close()