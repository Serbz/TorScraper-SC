"""
This script contains and executes the PowerShell installer for 'nyx'.

The installer script (contained in PS1_SCRIPT_CONTENT) will:
1. pip install 'nyx' and 'windows-curses'.
2. Find the Python site-packages directory.
3. Apply several string-replacement patches to the nyx source code
   to make it compatible with Windows (fixing os.getuid and os.uname errors).
"""

import subprocess
import os
import sys
from pathlib import Path
import logging

# This is the PowerShell script content from nyx_install.ps1
PS1_SCRIPT_CONTENT = r"""
<#
.SYNOPSIS
    Installs and patches the 'nyx' Tor monitor to run on Windows.
.DESCRIPTION
    This script performs the following actions:
    1. Installs 'nyx' and the required 'windows-curses' via pip.
    2. Dynamically finds the Python 'site-packages' directory using the 'sysconfig' module.
    3. Applies three separate code patches to 'nyx' source files to fix
       Windows-specific AttributeErrors (os.getuid, os.uname).
#>
param()

Write-Host "--- Nyx Windows Installer & Patcher (v2) ---" -ForegroundColor Yellow

# -----------------------------------------------------------------
# Step 1: Install required Python packages
# -----------------------------------------------------------------
Write-Host "[Step 1] Installing 'nyx' and 'windows-curses' via pip..."
pip install nyx windows-curses
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip installation failed. Please check your Python/pip setup. Aborting."
    return
}

# -----------------------------------------------------------------
# Step 2: Find the Python 'site-packages' directory (Robust Method)
# -----------------------------------------------------------------
Write-Host "[Step 2] Finding Python site-packages directory..."
$SitePackages = (python -c "import sysconfig; print(sysconfig.get_path('purelib'))" 2>$null)

if (-not $SitePackages -or $LASTEXITCODE -ne 0) {
    Write-Error "Could not determine site-packages directory. Is Python installed and in your PATH? Aborting."
    return
}
Write-Host "Found site-packages at: $SitePackages" -ForegroundColor Cyan

# -----------------------------------------------------------------
# Step 3: Apply all required code patches
# -----------------------------------------------------------------
Write-Host "[Step 3] Applying Windows compatibility patches..."

try {
    # --- Patch 1: nyx\starter.py (fixes os.getuid) ---
    $FileToPatch = Join-Path $SitePackages "nyx\starter.py"
    if (Test-Path $FileToPatch) {
        Write-Host "Patching $FileToPatch (os.getuid)..."
        (Get-Content $FileToPatch -Raw) -replace 'elif os\.getuid\(\) == 0:', '# elif os.getuid() == 0:' | Set-Content $FileToPatch -NoNewline
    } else {
        Write-Warning "File not found: $FileToPatch. Skipping patch."
    }

    # --- Patch 2: nyx\panel\header.py (fixes os.uname for hostname/platform) ---
    $FileToPatch = Join-Path $SitePackages "nyx\panel\header.py"
    if (Test-Path $FileToPatch) {
        Write-Host "Patching $FileToPatch (os.uname)..."
        $Content = Get-Content $FileToPatch -Raw
        
        # Add required imports to the top of the file if not already present
        if ($Content -notmatch "import socket") {
            $Content = "import socket`n" + $Content
        }
        if ($Content -notmatch "import platform") {
            $Content = "import platform`n" + $Content
        }
        
        # Fix hostname line
        $Content = $Content -replace "'hostname': os\.uname\(\)\[1\],", "'hostname': socket.gethostname(),"
        
        # Fix platform line
        $Content = $Content -replace "'platform': '%s %s' % \(os\.uname\(\)\[0\], os\.uname\(\)\[2\]\),", "'platform': '%s %s' % (platform.system(), platform.release()),"
        
        $Content | Set-Content $FileToPatch -NoNewline
    } else {
        Write-Warning "File not found: $FileToPatch. Skipping patch."
    }

    # --- Patch 3: nyx\log.py (fixes os.uname in event listener) ---
    $FileToPatch = Join-Path $SitePackages "nyx\log.py"
    if (Test-Path $FileToPatch) {
        Write-Host "Patching $FileToPatch (os.uname in logger)..."
        $Content = Get-Content $FileToPatch -Raw
        
        # Add required import to the top of the file if not already present
        if ($Content -notmatch "import platform") {
            $Content = "import platform`n" + $Content
        }
        
        # Fix system info line
        $Content = $Content -replace "exc_info\.system = '%s %s' % \(os\.uname\(\)\[0\], os\.uname\(\)\[2\]\)", "exc_info.system = '%s %s' % (platform.system(), platform.release())"
        
        $Content | Set-Content $FileToPatch -NoNewline
    } else {
        Write-Warning "File not found: $FileToPatch. Skipping patch."
    }

} catch {
    Write-Error "An error occurred during the patching process: $_"
    return
}

Write-Host "--- Patching Complete! ---" -ForegroundColor Green
Write-Host "Nyx has been installed and patched for Windows."
Write-Host "You should now be able to run 'nyx' (in a new terminal, if Tor is running)."
"""

def get_script_dir():
    """Gets the script's directory, handling frozen executables."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    # This assumes RunNyx.py is in the same dir as the main script
    return Path(__file__).parent

def install_nyx():
    """
    Saves the PS1 script to a temp file and executes it in a new
    PowerShell console window.
    """
    try:
        SCRIPT_DIR = get_script_dir()
        temp_dir = SCRIPT_DIR / "Temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        script_path = temp_dir / "nyx_install_patcher.ps1"
        script_path.write_text(PS1_SCRIPT_CONTENT)
        
        logging.info(f"Wrote Nyx installer to {script_path}")
        
        # Command to launch PowerShell, bypass execution policy, and run the file
        cmd = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', str(script_path)]
        
        # Run the command in a new console window
        logging.info(f"Executing: {' '.join(cmd)}")
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        
    except Exception as e:
        logging.error(f"Failed to create or run Nyx installer script: {e}")
        raise # Re-raise to be caught by the GUI

if __name__ == "__main__":
    # Allows the script to be run manually for testing
    print("This script is intended to be imported by the main application.")
    print("To test the installer, running install_nyx() now...")
    install_nyx()
    print("Installer launched in new window. Press Enter to exit this test.")
    input()
