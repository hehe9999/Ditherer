#!/usr/bin/env python3
"""
Runtime UI loader with widget access for Qt Designer .ui files.
This module provides functionality to load UI files at runtime and access specific widgets.
"""

import os
import sys

from PySide6.QtCore import QFile, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QWidget


def load_ui_file(ui_path, parent=None):
    """Load a .ui file at runtime and return accessible widgets."""
    if not os.path.exists(ui_path):
        raise FileNotFoundError(f"UI file not found: {ui_path}")

    # Create a QApplication if one doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Load the UI file
    loader = QUiLoader()
    ui_file = QFile(ui_path)

    if not ui_file.open(QIODevice.ReadOnly):
        raise OSError(f"Cannot open UI file: {ui_path}")

    # Load the UI
    widget = loader.load(ui_file, parent)
    ui_file.close()

    if widget is None:
        raise RuntimeError(f"Failed to load UI file: {ui_path}")

    # Collect all widgets with object names
    widgets = {
        child.objectName(): child for child in widget.findChildren(QWidget) if child.objectName()
    }
    # Add the main widget itself if it has an object name
    if widget.objectName():
        widgets[widget.objectName()] = widget
    return widgets


def create_ui_window(ui_path, window_title="UI Window", parent=None):
    """Create a window from a .ui file with a specific title."""
    widgets = load_ui_file(ui_path, parent)

    # Set window title if it's a window-type widget
    if hasattr(widgets.get("window"), "setWindowTitle"):
        widgets["window"].setWindowTitle(window_title)

    return widgets


if __name__ == "__main__":
    # If no command‑line arguments are given, default to loading ui.ui in the current folder
    if len(sys.argv) == 1:
        ui_path = "ui.ui"
        title = "Ditherer"
    else:
        # Existing behaviour: first arg is UI file, second (optional) is title
        ui_path = sys.argv[1]
        title = sys.argv[2] if len(sys.argv) > 2 else "UI Window"

    app = QApplication(sys.argv)
    widgets = create_ui_window(ui_path, title)

    # Example: connect the Export PNG button if it exists
    if "export_png_btn" in widgets:
        widgets["export_png_btn"].clicked.connect(lambda: print("Export PNG clicked"))

    # Show the window
    widgets["window"].show()
    sys.exit(app.exec())
