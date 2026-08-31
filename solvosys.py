"""
Solvosys Desktop Edition - Entry Point
=======================================

Routes between two modes based on the _SOLVOSYS_STREAMLIT environment variable:

  1. Launcher mode (default):
     Starts the desktop launcher which manages the application lifecycle.

  2. Streamlit mode (child process):
     Runs the Streamlit ML application directly.
     This mode is activated when the parent launcher process spawns
     this executable as a subprocess with _SOLVOSYS_STREAMLIT=1.

     This indirection is CRITICAL for PyInstaller: when frozen,
     sys.executable points to the .exe itself, not to python.exe.
     Without this routing, the launcher would recursively spawn
     itself infinitely, opening a new browser tab each time.

Usage:
    python solvosys.py
"""

import os
import sys

if os.environ.get("_SOLVOSYS_STREAMLIT") == "1":
    # ── Child Process: Run Streamlit ──────────────────────
    # The parent launcher set these environment variables and
    # spawned this executable. Run Streamlit directly.

    app_path = os.environ["_SOLVOSYS_APP_PATH"]
    port = os.environ["_SOLVOSYS_PORT"]

    sys.argv = [
        "streamlit", "run",
        app_path,
        f"--server.port={port}",
        "--server.headless=true",
        "--global.developmentMode=false",
    ]

    from streamlit.web import cli as stcli
    stcli.main()

else:
    # ── Launcher Mode ────────────────────────────────────
    from desktop.launcher import main
    main()
