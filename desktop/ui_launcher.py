"""
UI Launcher Abstraction
=======================

Provides a single entry point for opening the application UI.

Launch modes:
    - Development: Opens the user's default web browser.
    - Production:  Opens a native PyWebView desktop window.
"""

import sys
import webbrowser
from typing import Callable, Optional
from desktop.logger import get_logger

log = get_logger()

# Guard flag: ensures the UI is launched at most once per process.
_browser_opened = False


def launch_ui(url: str, wait_callback: Optional[Callable[[], bool]] = None) -> None:
    """
    Launch the application UI.

    Args:
        url: The local URL where the Streamlit server is running.
        wait_callback: A function that blocks until Streamlit is healthy.
                       Returns True if healthy, False if timed out.
                       Only used in Production (frozen) mode for the splash screen.
    """
    global _browser_opened

    if _browser_opened:
        log.warning("launch_ui() called again but UI was already launched. Ignoring.")
        return

    is_frozen = getattr(sys, "frozen", False)
    import os
    is_debug = os.environ.get("SOLVOSYS_DEBUG") == "1"

    if is_frozen and not is_debug:
        from desktop.window_manager import DesktopWindow
        
        log.info("Launching Native Desktop UI")
        _browser_opened = True
        
        window = DesktopWindow("Solvosys")
        
        # This will BLOCK the main thread until the window is closed.
        window.start_with_splash(target_url=url, wait_callback=wait_callback)
    else:
        log.info("Launching Browser UI: %s", url)
        
        if wait_callback:
            if not wait_callback():
                log.error("Failed to connect to internal AI Engine.")
                return

        webbrowser.open(url)
        _browser_opened = True
