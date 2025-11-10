"""
Main entry point for the Tor Scraper application.

This script performs the following steps:
1. Imports and runs the library installer from utils.py.
2. Checks for Administrator privileges and relaunches if necessary.
3. After ensuring libraries/privileges, it imports the main GUI components.
4. Initializes and runs the PySide6 QApplication.
"""

import sys
import logging
import subprocess
import os
import ctypes # Added for admin check
import asyncio

# --- 1. Library Installation ---
# Import the installer and SCRIPT_DIR first.
# SCRIPT_DIR is needed early to set the working directory.
try:
    from utils import install_package, SCRIPT_DIR
except ImportError as e:
    print(f"Failed to import 'utils.py'. Ensure all script files are in the same directory.")
    print(f"Error: {e}")
    sys.exit(1)

def run_installers():
    """
    Runs all package installers.
    Returns True if a restart is required, False otherwise.
    """
    # List of all packages to check
    packages = [
        ('numpy', 'numpy'),
        ('beautifulsoup4', 'bs4'),
        ('lxml', 'lxml'),
        ('curl_cffi', 'curl_cffi'),
        ('asyncio', 'asyncio'),
        ('PySide6', 'PySide6'),
        ('psutil', 'psutil'),
        ('scapy', 'scapy'),
        ('pyuac', 'pyuac'),
        ('requests', 'requests'),
    ]
    
    restart_needed = False
    for pkg, import_name in packages:
        if install_package(pkg, import_name):
            # install_package returns True if an install occurred
            restart_needed = True
    return restart_needed

# --- 2. Admin Privilege Check (Windows-Only) ---

def is_admin():
    """Checks if the script is running with administrator privileges."""
    if os.name == 'nt':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    else:
        # Assume admin/root on non-Windows
        return os.geteuid() == 0

def run_as_admin():
    """Shows a dialog and relaunches the script as admin."""
    # We must import PySide6 *after* installation
    from PySide6.QtWidgets import QApplication, QMessageBox
    
    # We need a dummy QApplication to show the dialog
    app_admin_check = QApplication.instance() or QApplication(sys.argv)
    
    msg_box = QMessageBox()
    msg_box.setWindowTitle("Administrator Privileges Required")
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setText("This application requires Administrator privileges to monitor network traffic.\n\n"
                    "It will now attempt to restart with the required permissions.")
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec()
    app_admin_check.quit()

    # Relaunch using pyuac
    try:
        import pyuac
        pyuac.runAsAdmin()
    except Exception as e:
        # Fallback if pyuac fails
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    
    # Exit the current non-admin instance
    sys.exit(0)


# --- 3. Main Application Imports ---
# Imports are deferred until after install check

# --- 4. Main Execution ---
if __name__ == "__main__":
    
    # --- FIX for "ValueError: too many file descriptors" ---
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    # --- END FIX ---
    #
    # --- FIX for OpenType font warnings ---
    # This tells Qt to not log font database warnings.
    os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.text.font.db=false"
    # --- END FIX ---
    
    # --- MODIFIED INSTALLER LOGIC ---
    # We need a QApplication to show a message box.
    # We *must* import it *after* checking/installing PySide6
    
    if run_installers():
        # Temporarily import QApplication/QMessageBox *only* to show the restart message
        from PySide6.QtWidgets import QApplication, QMessageBox
        app = QApplication(sys.argv)
        QMessageBox.information(
            None, 
            "Libraries Installed",
            "Required libraries were successfully installed.\n\nThe application must restart to continue."
        )
        # Relaunch the script
        os.execv(sys.executable, ['python'] + sys.argv)
        sys.exit(0) # Exit current process
    # --- END MODIFIED LOGIC ---

    # If we're here, no restart was needed.
    # Now we can safely import everything else.
    
    from PySide6.QtWidgets import QApplication
    from gui_main import ScraperApp

    app = QApplication(sys.argv)
    
    # Check for admin rights *before* initializing the main app
    if os.name == 'nt' and not is_admin():
        run_as_admin()
        
    # If we are here, we are running as admin (or on non-Windows)
    
    # Set CWD for the script itself (for frozen exec)
    os.chdir(SCRIPT_DIR)
    
    # Initialize and run the application
    window = ScraperApp()
    window.show()
    sys.exit(app.exec())
