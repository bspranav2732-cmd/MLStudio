"""
Resource Manager
================

Resolves file paths for assets, backend modules, and configuration files.
Works identically whether running from:
- Python source (development)
- PyInstaller frozen executable (production)

Usage:
    from desktop.resources import get_base_dir, get_asset, get_backend_path

    logo = get_asset("assets/icons/logo.png")
    backend = get_backend_path()
"""

import sys
from pathlib import Path


def get_base_dir() -> Path:
    """
    Return the project root directory.

    When running from source:
        Returns the parent of the `desktop/` package directory.

    When frozen by PyInstaller:
        Returns `sys._MEIPASS` (the temporary extraction directory
        where PyInstaller unpacks bundled data files).
    """
    if getattr(sys, "frozen", False):
        # PyInstaller sets sys._MEIPASS to the temp extraction dir
        return Path(sys._MEIPASS)
    else:
        # Running from source: this file is at <project>/desktop/resources.py
        return Path(__file__).resolve().parent.parent


def get_asset(relative_path: str) -> Path:
    """
    Resolve an asset path relative to the project root.

    Args:
        relative_path: Path relative to the project root,
                       e.g. "assets/icons/logo.png"

    Returns:
        Absolute Path to the resource.
    """
    return get_base_dir() / relative_path


def get_backend_path() -> Path:
    """Return the absolute path to the backend/ directory."""
    return get_base_dir() / "backend"


def get_app_entry() -> Path:
    """Return the absolute path to backend/app.py."""
    return get_backend_path() / "app.py"


def get_streamlit_config_dir() -> Path:
    """Return the absolute path to the .streamlit/ config directory."""
    return get_base_dir() / ".streamlit"


def get_logs_dir() -> Path:
    """
    Return the absolute path to the logs/ directory.
    Creates the directory if it does not exist.
    """
    logs_dir = get_base_dir() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir
