# Standard library imports
import os
import sys


def resource_path(relative_path: str) -> str:
    """Resolve a bundled data file whether running from source or a PyInstaller
    onefile build.

    PyInstaller unpacks bundled data to a temp dir exposed as sys._MEIPASS; in
    a normal source checkout we resolve relative to the project root (this
    file's parent directory).
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)
