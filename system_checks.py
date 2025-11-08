"""
Handles system-level checks, like Npcap installation.
"""

import os
import sys
import logging
import requests
import subprocess
import shutil
from pathlib import Path

from PySide6.QtWidgets import QMessageBox, QProgressDialog
from PySide6.QtCore import Qt

def is_npcap_found():
    """
    Checks if Npcap is installed by looking for its core DLL files
    in the System32 directory.
    """
    if os.name != 'nt':
        return True # Not on Windows, not needed
    
    system32_path = Path(os.environ["WINDIR"]) / "System32"
    wpcap_path = system32_path / "wpcap.dll"
    packet_dll_path = system32_path / "Packet.dll"
    
    if wpcap_path.exists() and packet_dll_path.exists():
        logging.info(f"Found Npcap/WinPcap files: {wpcap_path} and {packet_dll_path}")
        return True
    
    logging.warning("Npcap/WinPcap core DLLs not found in System32. Npcap is not installed.")
    return False

def check_and_install_npcap(script_dir, parent_window=None):
    """
    Checks for Npcap driver. If not found, downloads and runs the installer.
    Returns True if Npcap is present or installed, False if cancelled or restart is pending.
    """
    if is_npcap_found():
        logging.info("Npcap check passed. Network monitoring enabled.")
        return True

    # Npcap not found, must install
    logging.warning("Npcap not found. Prompting user for installation.")
    reply = QMessageBox.warning(parent_window, "Npcap Driver Required",
                                "To monitor network speed for the Tor process, the 'Npcap' driver is required.\n\n"
                                "Click OK to download and launch the Npcap installer (v1.79).\n\n"
                                "Please close this application if you do not want to install Npcap.",
                                QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
    
    if reply == QMessageBox.Cancel:
        return False

    temp_dir = script_dir / "Temp"
    temp_dir.mkdir(exist_ok=True)
    installer_path = temp_dir / "npcap-1.79-installer.exe"
    installer_url = "https://npcap.com/dist/npcap-1.79.exe"

    try:
        # --- Download Npcap ---
        logging.info(f"Downloading Npcap from {installer_url}...")
        progress = QProgressDialog("Downloading Npcap installer...", "Cancel", 0, 0, parent_window)
        progress.setWindowTitle("Downloading...")
        progress.setWindowModality(Qt.WindowModal)
        
        with requests.get(installer_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            progress.setMaximum(total_size)
            
            with open(installer_path, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if progress.wasCanceled():
                        raise Exception("Download cancelled by user.")
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress.setValue(downloaded)
        progress.setValue(total_size)
        logging.info("Npcap download complete.")

        # --- Run Installer ---
        logging.info(f"Launching Npcap installer: {installer_path}")
        process = subprocess.Popen([installer_path])
        
        # --- Wait for User ---
        msg_box = QMessageBox(parent_window)
        msg_box.setWindowTitle("Installation")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText("The Npcap installer has been launched.\n\n"
                        "1. Please complete the installation (default settings are fine).\n"
                        "2. Click 'OK' on *this* dialog box *only after* the installation is finished.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

        # --- Cleanup ---
        logging.info("User confirmed Npcap installation. Cleaning up Temp folder.")
        shutil.rmtree(temp_dir)

        # --- Force restart ---
        logging.info("Npcap installation finished. Prompting for application restart.")
        QMessageBox.information(parent_window, "Restart Required",
                                  "Installation complete. The application must now restart to detect the new Npcap driver.\n\n"
                                  "Please click OK to restart the application.")
        
        # Tell the main app to reload
        os.execv(sys.executable, ['python'] + sys.argv)
        return False # Stop current execution

    except Exception as e:
        logging.error(f"Failed to download or install Npcap: {e}")
        QMessageBox.critical(parent_window, "Npcap Installation Failed", f"An error occurred: {e}")
        try:
            shutil.rmtree(temp_dir) 
        except Exception:
            pass
        return False