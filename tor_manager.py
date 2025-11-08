"""
Handles all Tor process management and control port communication.
"""

import os
import sys
import logging
import subprocess
import threading
import time
import socket
import binascii
from pathlib import Path
import traceback # Added for error logging

from PySide6.QtCore import QObject, Signal

class TorManager(QObject):
    """Manages the Tor subprocess and control port."""
    tor_ready = Signal()
    
    def __init__(self, script_dir):
        super().__init__()
        self.script_dir = script_dir
        self.tor_process = None
        self.tor_bootstrapped = threading.Event()
        
    def get_tor_auth_cookie_path(self):
        """Finds the path to the Tor control auth cookie."""
        return self.script_dir / "tor" / "tor_data" / "control_auth_cookie"

    def kill_existing_tor_processes(self):
        logging.info("Checking for and terminating existing Tor processes...")
        try:
            if sys.platform == "win32":
                subprocess.run(['taskkill', '/F', '/IM', 'tor.exe'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(['pkill', '-f', 'tor'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info("Finished check for existing Tor processes.")
        except Exception as e:
            logging.warning(f"Could not attempt to kill Tor processes (this may be fine): {e}")

    def ensure_local_torrc(self, overwrite_auto=False):
        """
        Checks for the local torrc file and creates/overwrites it.
        Returns True on success, False on failure or user cancellation.
        """
        logging.info("Checking and configuring local torrc file...")
        
        tor_dir_path = self.script_dir / "tor"
        tor_data_path = tor_dir_path / "tor_data"
        geoip_file_path = tor_dir_path / "Data" / "geoip"
        geoip6_file_path = tor_dir_path / "Data" / "geoip6"
        log_file_path = tor_data_path / "tor_log.txt"
        torrc_path = tor_dir_path / "torrc"
        
        data_dir_str = str(tor_data_path.resolve()).replace('\\', '/')
        geoip_str = str(geoip_file_path.resolve()).replace('\\', '/')
        geoip6_str = str(geoip6_file_path.resolve()).replace('\\', '/')
        log_str = str(log_file_path.resolve()).replace('\\', '/')

        torrc_content = f"""DataDirectory {data_dir_str}
GeoIPFile {geoip_str}
GeoIPv6File {geoip6_str}
SocksPort 9100
SocksPort 9101
SocksPort 9102
SocksPort 9103
SocksPort 9104
SocksPort 9105
SocksPort 9106
ControlPort 9051
CookieAuthentication 1
Log info file {log_str}
"""
        # --- This logic requires a parent window, so we'll simplify it ---
        # --- We will rely on the `overwrite_torrc_auto` flag from config ---
        
        try:
            should_write_file = False
            if overwrite_auto:
                should_write_file = True
            elif not torrc_path.exists():
                logging.info(f"torrc not found at {torrc_path}. Creating it.")
                should_write_file = True
            
            # For this refactor, we remove the interactive prompt.
            # The user can delete 'torrc' to have it recreated.
            # Or, we can add the prompt back in gui_main.py
            
            # Simple logic: if auto-overwrite is on, do it. If file doesn't exist, create it.
            if overwrite_auto or not torrc_path.exists():
                tor_data_path.mkdir(parents=True, exist_ok=True)
                torrc_path.write_text(torrc_content)
                logging.info(f"[SUCCESS] Configured torrc file at: {torrc_path}")
            else:
                logging.info(f"Using existing torrc file at: {torrc_path}")

            if not geoip_file_path.exists() or not geoip6_file_path.exists():
                logging.critical(f"[FATAL] Tor GeoIP files not found in {tor_dir_path / 'Data'}")
                return False # Fatal error

            return True
            
        except Exception as e:
            logging.critical(f"[FATAL] Failed to write torrc file: {e}. Check permissions.")
            return False

    def launch_monitoring_tools(self):
        """Launches the Tor subprocess and monitors it for bootstrap."""
        threading.Thread(target=self._launch_tools_thread, daemon=True).start()

    def _launch_tools_thread(self):
        try:
            tor_dir = self.script_dir / "tor"
            tor_exe_path = tor_dir / "tor.exe"
            torrc_path = tor_dir / "torrc" 
            
            if not tor_exe_path.exists():
                logging.critical(f"[FATAL] 'tor.exe' not found at expected path: {tor_exe_path}")
                return
            if not torrc_path.exists():
                logging.critical(f"[FATAL] 'torrc' not found at: {torrc_path}.")
                return

        except Exception as e:
            logging.critical(f"[FATAL] Error determining script/tor path: {e}")
            return
        
        logging.info(f"[INFO] Launching integrated Tor process from: {tor_exe_path}")
        logging.info(f"[INFO] Using local config file: {torrc_path}")
        try:
            self.tor_process = subprocess.Popen(
                [str(tor_exe_path), "-f", str(torrc_path)], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL, 
                text=True, 
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            logging.info(f"[INFO] Tor process launched (PID: {self.tor_process.pid}).")
            
            logging.info("[INFO] Now monitoring Control Port 9051 for bootstrap status...")
            bootstrap_timeout = 120 # 120 seconds
            
            for i in range(bootstrap_timeout):
                time.sleep(1) # Wait 1 second between checks
                
                try:
                    with socket.create_connection(("127.0.0.1", 9051), timeout=1) as s:
                        auth_reply = self._authenticate_tor(s)
                        if b"250 OK" not in auth_reply:
                            logging.warning(f"Tor auth failed: {auth_reply.decode().strip()}. Retrying...")
                            continue
                            
                        s.sendall(b'GETINFO status/bootstrap-phase\r\n')
                        status_reply = s.recv(1024).decode()
                        
                        if "PROGRESS=100" in status_reply:
                            logging.info("[SUCCESS] Tor has fully bootstrapped.")
                            self.tor_bootstrapped.set()
                            self.tor_ready.emit() # Signal the main thread
                            return # Exit thread
                        else:
                            progress_line = [line for line in status_reply.split('\n') if "BOOTSTRAP PROGRESS=" in line]
                            if progress_line:
                                progress = progress_line[0].split('SUMMARY=')[-1].strip().replace('"', '')
                                logging.info(f"[Tor Bootstrap] {progress}")
                            else:
                                logging.info(f"Waiting for Tor... (status: {status_reply.strip()})")

                except socket.error:
                    if i % 10 == 0: 
                        logging.info("Waiting for Tor control port to open...")
                    continue
            
            logging.warning(f"[WARN] Timed out after {bootstrap_timeout}s waiting for Tor to bootstrap.")
            if self.tor_process:
                self.tor_process.terminate()

        except Exception as e:
            logging.error(f"[ERROR] Error launching Tor process: {e}")
            logging.error(traceback.format_exc())

    def _authenticate_tor(self, sock):
        """Helper function to send auth command to Tor control port."""
        cookie_path = self.get_tor_auth_cookie_path()
        auth_command = b'AUTHENTICATE ""\r\n'  

        if cookie_path and os.path.exists(cookie_path):
            try:
                with open(cookie_path, 'rb') as f:
                    cookie = f.read()
                    hex_cookie = binascii.hexlify(cookie)
                    auth_command = b'AUTHENTICATE ' + hex_cookie + b'\r\n'
            except Exception as e:
                logging.warning(f"Could not read Tor auth cookie: {e}. Falling back.")
        
        sock.sendall(auth_command)
        return sock.recv(1024)

    def request_new_identity(self):
        """Connects to Tor control port and requests a new identity."""
        try:
            with socket.create_connection(("127.0.0.1", 9051), timeout=10) as s:
                auth_reply = self._authenticate_tor(s)
                if b"250 OK" not in auth_reply:
                    logging.error(f"Tor authentication failed: {auth_reply.decode().strip()}")
                    return
                
                logging.info("Requesting new Tor identity (SIGNAL NEWNYM)...")
                s.sendall(b'SIGNAL NEWNYM\r\n')
                newnym_reply = s.recv(1024)
                if b"250 OK" in newnym_reply:
                    logging.info("[SUCCESS] New Tor identity acquired.")
                else:
                    logging.warning(f"NEWNYM signal failed: {newnym_reply.decode().strip()}")
        except Exception as e:
            logging.error(f"Could not connect to Tor control port (9051): {e}")

    def terminate_tor(self):
        """Terminates the Tor subprocess if it's running."""
        if self.tor_process:
            logging.info("[INFO] Terminating Tor process...")
            self.tor_process.terminate()
            self.tor_process = None