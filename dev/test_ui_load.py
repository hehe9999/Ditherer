import sys
import traceback

sys.path.insert(0, ".")
try:
    from ui_loader import load_ui_file

    widgets = load_ui_file("ui.ui")
    print("SUCCESS: loaded widgets:", list(widgets.keys()))
except Exception as e:
    print("ERROR:", repr(e))
    traceback.print_exc()
