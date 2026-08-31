"""
Solvosys Desktop Launcher
=========================

Application lifecycle manager for Solvosys.

Responsibilities:
    1. Acquire a singleton lock (prevent duplicate instances).
    2. Find a free port (starting from 8501).
    3. Start the Streamlit server.
    4. Wait until the server is healthy.
    5. Launch the UI (browser or future PyWebView) exactly once.
    6. Monitor the server.
    7. Shut down cleanly on exit.

Launch modes:
    - Source (development):  Streamlit runs as a child subprocess via
                             `python.exe solvosys.py` with _SOLVOSYS_STREAMLIT=1.
    - Frozen (PyInstaller):  Streamlit runs in-process on a daemon thread via
                             `streamlit.web.bootstrap.run()`. There is no standalone
                             Python interpreter inside a PyInstaller bundle, so a
                             subprocess approach is impossible.

This module does NOT import any ML code.
It only manages the application process lifecycle.

Usage:
    python -m desktop.launcher
    python solvosys.py
"""

import os
import sys
import time
import socket
import signal
import tempfile
import atexit
import threading
import subprocess
import urllib.request
import urllib.error

from desktop import APP_NAME, APP_VERSION, APP_SUBTITLE
from desktop.resources import get_base_dir, get_app_entry, get_backend_path
from desktop.ui_launcher import launch_ui
from desktop.logger import get_logger

log = get_logger()

# ── Configuration ─────────────────────────────────────────

_PORT_START = 8501          # First port to try
_PORT_RANGE = 20            # Maximum ports to scan (8501-8520)
_HEALTH_TIMEOUT = 60        # Seconds to wait for server readiness
_HEALTH_INTERVAL = 0.5      # Seconds between health checks


# ── Singleton Lock ────────────────────────────────────────

_lock_file_handle = None
_LOCK_PATH = os.path.join(tempfile.gettempdir(), "solvosys_launcher.lock")


def _acquire_singleton_lock() -> bool:
    """
    Acquire an exclusive file lock to prevent duplicate launcher instances.

    Uses msvcrt on Windows for a non-blocking exclusive lock.
    Returns True if the lock was acquired, False if another instance holds it.
    """
    global _lock_file_handle
    try:
        _lock_file_handle = open(_LOCK_PATH, "w")
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(_lock_file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(_lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_file_handle.write(str(os.getpid()))
        _lock_file_handle.flush()
        return True
    except (IOError, OSError):
        log.warning("Could not acquire singleton lock. Another instance may be running.")
        return False


def _release_singleton_lock() -> None:
    """Release the singleton file lock and remove the lock file."""
    global _lock_file_handle
    if _lock_file_handle:
        try:
            _lock_file_handle.close()
        except Exception:
            pass
        _lock_file_handle = None
    try:
        os.remove(_LOCK_PATH)
    except OSError:
        pass


# ── Port Selection ────────────────────────────────────────

def _find_free_port() -> int:
    """
    Find a free port using OS assignment to guarantee zero conflicts.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        log.debug("OS assigned free port: %d", port)
        return port


# ── Health Check ──────────────────────────────────────────

def _wait_for_server(port: int, server=None) -> bool:
    """
    Block until the Streamlit server responds on the given port.

    Polls the Streamlit health endpoint every _HEALTH_INTERVAL seconds.
    Returns True when the server is ready, or False on timeout.
    """
    url = f"http://127.0.0.1:{port}/_stcore/health"
    deadline = time.time() + _HEALTH_TIMEOUT

    log.info("Waiting for server on port %d...", port)

    while time.time() < deadline:
        if server and not server.is_running():
            log.error("Server stopped unexpectedly during startup.")
            return False

        try:
            response = urllib.request.urlopen(url, timeout=2)
            if response.status == 200:
                log.info("Server is ready.")
                return True
        except (urllib.error.URLError, ConnectionError, OSError):
            pass
        time.sleep(_HEALTH_INTERVAL)

    log.error("Server did not respond within %d seconds.", _HEALTH_TIMEOUT)
    return False


# ── Server Handle ─────────────────────────────────────────

class _ServerHandle:
    """
    Unified interface for managing the Streamlit server regardless
    of whether it runs as a subprocess (source) or a thread (frozen).
    """

    def __init__(self, *, process=None, thread=None):
        self._process = process
        self._thread = thread

    @property
    def mode(self) -> str:
        return "subprocess" if self._process else "in-process"

    @property
    def pid(self) -> int:
        if self._process:
            return self._process.pid
        return os.getpid()

    def is_running(self) -> bool:
        if self._process:
            return self._process.poll() is None
        if self._thread:
            return self._thread.is_alive()
        return False

    def wait(self) -> None:
        """Block until the server stops."""
        if self._process:
            self._process.wait()
        elif self._thread:
            # Daemon thread: loop with timeout so KeyboardInterrupt can fire.
            while self._thread.is_alive():
                self._thread.join(timeout=1.0)

    def shutdown(self) -> None:
        """Terminate the server gracefully."""
        if self._process:
            if self._process.poll() is not None:
                log.info("Server process already exited (code: %d).",
                         self._process.returncode)
                return
            log.info("Shutting down server (PID: %d)...", self._process.pid)
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
                log.info("Server shut down cleanly.")
            except subprocess.TimeoutExpired:
                log.warning("Server did not stop gracefully. Killing process.")
                self._process.kill()
                self._process.wait()
                log.info("Server process killed.")
        else:
            # In-process daemon thread: dies when the main thread exits.
            log.info("In-process server will stop with main process.")

    @property
    def exit_code(self) -> int:
        if self._process and self._process.returncode is not None:
            return self._process.returncode
        return 0


# ── Server Launch ─────────────────────────────────────────

def _start_server(port: int) -> _ServerHandle:
    """
    Start the Streamlit server and return a unified handle.
    """
    app_path = str(get_app_entry())
    is_frozen = getattr(sys, "frozen", False)

    log.info("Starting Streamlit...")
    log.debug("  App path:  %s", app_path)
    log.debug("  Port:      %d", port)
    log.debug("  Frozen:    %s", is_frozen)
    log.debug("  Executable: %s", sys.executable)

    return _start_server_subprocess(app_path, port)


def _start_server_subprocess(app_path: str, port: int) -> _ServerHandle:
    """
    Start Streamlit as a child subprocess.

    Uses sys.executable (python.exe in source, Solvosys.exe when frozen) to spawn
    a child process with the _SOLVOSYS_STREAMLIT=1 environment variable.
    The entry point detects this variable and runs Streamlit directly in the
    main thread of the child process, bypassing the launcher loop.
    """
    env = os.environ.copy()
    env["_SOLVOSYS_STREAMLIT"] = "1"
    env["_SOLVOSYS_APP_PATH"] = app_path
    env["_SOLVOSYS_PORT"] = str(port)

    if getattr(sys, "frozen", False):
        # When frozen, sys.executable is Solvosys.exe, which automatically runs
        # the embedded solvosys.py script.
        cmd = [sys.executable]
    else:
        # In source mode, sys.executable is python.exe, so we must point it
        # to solvosys.py.
        entry_script = str(get_base_dir() / "solvosys.py")
        cmd = [sys.executable, entry_script]

    log.info("Starting Streamlit subprocess: %s", " ".join(cmd))

    process = subprocess.Popen(
        cmd,
        cwd=str(get_backend_path()),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    log.info("Streamlit process started (PID: %d).", process.pid)
    return _ServerHandle(process=process)


# ── Main Entry Point ─────────────────────────────────────

def main() -> None:
    """
    Launch Solvosys Desktop Edition.

    Steps:
        0. Acquire singleton lock.
        1. Log startup banner.
        2. Find a free port.
        3. Start the Streamlit server.
        4. Wait for the server to become healthy.
        5. Launch the UI (browser) exactly once.
        6. Wait for the server to exit or Ctrl+C.
        7. Release lock and clean up.
    """
    # ── Step 0: Singleton check ───────────────────────────
    if not _acquire_singleton_lock():
        log.error("Another Solvosys launcher is already running. Exiting.")
        print("Solvosys is already running.")
        sys.exit(0)

    atexit.register(_release_singleton_lock)

    log.info("=" * 50)
    log.info("%s v%s - %s", APP_NAME, APP_VERSION, APP_SUBTITLE)
    log.info("=" * 50)

    # FUTURE: Splash Screen
    # Show a lightweight splash window here (Tkinter or PyWebView)
    # before the server starts. Dismiss it after _wait_for_server().

    # FUTURE: Auto-Update Checker
    # Check for updates here before launching the server.

    # FUTURE: Recent Projects
    # Show a project picker dialog here.

    # ── Step 1: Find a free port ──────────────────────────
    try:
        port = _find_free_port()
    except RuntimeError as e:
        log.error(str(e))
        _release_singleton_lock()
        sys.exit(1)

    log.info("Selected port: %d", port)

    # ── Step 2: Start the Streamlit server ────────────────
    server = _start_server(port)

    # Register signal handlers for clean shutdown
    def _signal_handler(signum, frame):
        log.info("Received signal %d. Initiating shutdown.", signum)
        server.shutdown()
        _release_singleton_lock()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # ── Step 3: Launch the UI & Wait for server readiness ───
    # We pass the health check as a callback to launch_ui.
    # In PyWebView mode, this allows the UI to show a splash screen while
    # the server starts in the background. In Browser mode, it simply blocks.
    url = f"http://127.0.0.1:{port}"
    log.info("Opening UI...")
    
    def _health_check():
        try:
            return _wait_for_server(port, server)
        except Exception as e:
            log.exception("Unexpected error during health check: %s", e)
            return False

    launch_ui(url, wait_callback=_health_check)
    log.info("UI finished.")

    # FUTURE: Version / About Dialog
    # FUTURE: Run on Supercomputer

    # ── Step 4: Monitor server ────────────────────────────
    log.info("Solvosys is running. Press Ctrl+C to stop.")

    if getattr(sys, "frozen", False):
        # Native window closed, shut down cleanly
        log.info("Native window closed. Shutting down Streamlit...")
        server.shutdown()
    else:
        try:
            server.wait()
            log.info("Server exited (code: %d).", server.exit_code)
        except KeyboardInterrupt:
            log.info("Keyboard interrupt received.")
            server.shutdown()

    _release_singleton_lock()
    log.info("Solvosys session ended.")


if __name__ == "__main__":
    main()
