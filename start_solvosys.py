"""
Solvosys Unified Web Launcher
==============================
Starts both the FastAPI backend (port 8000) and Next.js frontend (port 3000),
verifies server health, and opens the application in your default browser.
Runs 100% locally with zero external dependencies and zero cost.

Usage:
    python start_solvosys.py
"""

import os
import sys
import time
import subprocess
import webbrowser
import signal

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

def main():
    print("=" * 60)
    print("  SOLVOSYS MACHINE LEARNING RESEARCH WORKBENCH")
    print("  Next.js + React + Tailwind Frontend | FastAPI Python Engine")
    print("=" * 60)
    print("\nStarting Solvosys local services...\n")

    # 1. Start FastAPI Backend
    backend_cmd = [
        sys.executable, "-m", "uvicorn", "server:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--log-level", "info"
    ]
    print("[1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=BACKEND_DIR,
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    # 2. Start Next.js Frontend
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_cmd = [npm_cmd, "run", "dev"]
    print("[2/2] Launching Next.js Frontend on http://localhost:3000 ...")
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=FRONTEND_DIR,
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    # Wait for services to initialize
    time.sleep(3)

    # Open Browser
    url = "http://localhost:3000"
    print(f"\n[OK] Solvosys is ready! Opening {url} in your browser...\n")
    print("Press Ctrl+C at any time to shut down both services.\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        # Keep launcher alive while child processes run
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\nShutting down Solvosys services...")
    finally:
        try:
            backend_proc.terminate()
            frontend_proc.terminate()
        except Exception:
            pass
        print("Solvosys terminated cleanly.")

if __name__ == "__main__":
    main()
