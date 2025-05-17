import subprocess
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = Path(__file__).resolve().parent.parent
ENTRY_POINT = "ditherer_gui.py"


class RestartOnChange(FileSystemEventHandler):
    def __init__(self):
        self.proc = None
        self.run_gui()

    def run_gui(self):
        if self.proc:
            self.proc.terminate()
        print(f"Launching {ENTRY_POINT}...")
        self.proc = subprocess.Popen(["python", ENTRY_POINT])

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(f"Detected change in {event.src_path}, restarting GUI...")
            self.run_gui()


if __name__ == "__main__":
    observer = Observer()
    handler = RestartOnChange()
    observer.schedule(handler, str(WATCH_DIR), recursive=True)
    observer.start()
    print("Watching for changes...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping watcher...")
        observer.stop()
        if handler.proc:
            handler.proc.terminate()
    observer.join()
