"""
Solvosys Desktop Edition
========================

Desktop launcher package for the Solvosys Machine Learning Workbench.

This package contains all desktop-specific infrastructure:
- launcher.py    — Application lifecycle management
- resources.py   — Path resolution (source and PyInstaller)
- ui_launcher.py — Abstracted UI launch (browser / PyWebView)
- logger.py      — Logging configuration

The ML application (backend/) is completely independent of this package.
"""

APP_NAME = "Solvosys"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "Machine Learning Workbench"
