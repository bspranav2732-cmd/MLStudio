"""
Window Manager
==============
Abstracts the PyWebView window logic for Solvosys Desktop.
"""

import webview
import threading
from typing import Callable

_SPLASH_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Solvosys</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f0f2f6;
            color: #31333F;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }
        .container {
            text-align: center;
        }
        h1 {
            font-size: 3rem;
            margin: 0;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }
        h2 {
            font-size: 1.25rem;
            font-weight: 400;
            color: #555;
            margin-top: 0.5rem;
            margin-bottom: 2rem;
        }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255, 75, 75, 0.2);
            border-left-color: #ff4b4b;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        .loading-text {
            margin-top: 1.5rem;
            font-size: 1rem;
            color: #777;
        }
        .version {
            position: absolute;
            bottom: 2rem;
            font-size: 0.85rem;
            color: #999;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Solvosys</h1>
        <h2>Machine Learning Workbench</h2>
        <div class="spinner"></div>
        <div class="loading-text">Initializing AI Engine...</div>
    </div>
    <div class="version">Version 1.0.0</div>
</body>
</html>
"""


class DesktopWindow:
    def __init__(self, title: str = "Solvosys"):
        self.title = title
        self._window = None

    def start_with_splash(self, target_url: str, wait_callback: Callable[[], bool]):
        """
        Displays the splash screen and spawns a background thread to wait
        for the Streamlit server. Once healthy, navigates to the target_url.
        
        This call BLOCKS the main thread until the window is closed by the user.
        """
        self._window = webview.create_window(
            self.title,
            html=_SPLASH_HTML,
            width=1400,
            height=900,
            resizable=True,
            min_size=(1024, 680)
        )

        def _monitor():
            if wait_callback():
                self.show_app(target_url)
            else:
                self.show_error("Failed to connect to the internal AI Engine. Please check the logs.")

        # Start the wait callback in a background thread so we don't block the UI loop
        threading.Thread(target=_monitor, daemon=True).start()

        # Start the PyWebView UI loop on the main thread
        webview.start()

    def show_app(self, url: str):
        """Transition the window to the actual application."""
        if self._window:
            self._window.load_url(url)

    def show_error(self, message: str):
        """Display an error message in the window."""
        error_html = f"""
        <html>
        <body style="font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #fff; color: #ff4b4b;">
            <div style="text-align: center;">
                <h2>Startup Error</h2>
                <p>{message}</p>
            </div>
        </body>
        </html>
        """
        if self._window:
            self._window.load_html(error_html)

    def close(self):
        """Close the desktop window."""
        if self._window:
            self._window.destroy()
