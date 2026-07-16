#!/usr/bin/env python3
"""
PySide6 GUI for Ditherer.

Loads the Qt Designer layout (ui.ui) at runtime and wires it to the same
backend (exporter/dither/media) that the old customtkinter GUI used.
Run with:  python gui_qt.py
"""

# Standard library imports
import os
import sys

# Third-party imports
import cv2
from PIL import Image
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLayout,
    QMainWindow,
    QMessageBox,
)

# Local imports
from ui_loader import load_ui_file
from media.image_utils import load_image, resize_to_fit
from media.state import media_state
from media.video_utils import load_video
from exporter import export_image, export_video, cancel_export, reset_cancel_flag
from resources import resource_path

UI_PATH = resource_path("ui.ui")

IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"]
VIDEO_EXTENSIONS = [".mkv", ".mp4", ".webm"]


class ExportWorker(QObject):
    """Runs a blocking export function in a background thread.

    Qt widgets can only be touched from the GUI thread, so the worker emits
    signals that the main window connects to for progress / completion.
    """

    progress = Signal(float)  # 0.0 - 1.0
    finished = Signal()
    error = Signal(str)

    def __init__(self, fn, kwargs):
        super().__init__()
        self._fn = fn
        self._kwargs = kwargs

    def run(self):
        try:
            # Inject our thread-safe progress emitter.
            self._kwargs["progress_callback"] = self.progress.emit
            self._fn(**self._kwargs)
        except RuntimeError as exc:
            # Raised by exporter.check_cancel() when the user cancels.
            self.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - surface any export failure
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class DithererWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load widgets from the .ui file and adopt its central widget so this
        # QMainWindow owns the whole designed layout.
        widgets = load_ui_file(UI_PATH)
        self._ui = widgets["window"]
        self.setCentralWidget(self._ui.centralWidget())
        self.setWindowTitle(self._ui.windowTitle() or "Ditherer")
        self.setMinimumSize(self._ui.minimumSize())
        self.resize(self._ui.size())
        self.w = widgets  # keep a handle to every named widget

        # Runtime state
        self.loaded_image = None  # PIL.Image currently displayed
        self._thread = None
        self._worker = None
        self._export_video_default_text = self.w["export_video_btn"].text()

        self._connect_signals()
        self._refresh_algorithm_options()
        self._update_algorithm_visibility()
        self._update_export_buttons()

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------
    def _connect_signals(self):
        w = self.w
        w["load_media_btn"].clicked.connect(self.load_media)
        w["algo_combo"].currentTextChanged.connect(self._on_algorithm_changed)
        w["export_png_btn"].clicked.connect(lambda: self._export_image("png"))
        w["export_jpg_btn"].clicked.connect(lambda: self._export_image("jpeg"))
        w["export_video_btn"].clicked.connect(self._export_video_or_cancel)

        # Video state drives which algorithms/exports are available.
        media_state.on_video_state_change = self._on_video_state_change

    # ------------------------------------------------------------------
    # Media loading
    # ------------------------------------------------------------------
    def load_media(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Media",
            "",
            "Media Files (*.png *.jpg *.jpeg *.mp4 *.mkv *.webm)",
        )
        if not path:
            return

        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            media_state.is_video = False
            self.loaded_image = load_image(path)
        elif ext in VIDEO_EXTENSIONS:
            load_video(path)
            ret, frame = media_state.cap.read()
            if not ret:
                QMessageBox.critical(self, "Error", "Could not read video file.")
                return
            self.loaded_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            QMessageBox.critical(self, "Unsupported File Type", f"Cannot load: {ext}")
            return

        self._update_image()
        self._update_export_buttons()

    def _update_image(self):
        if self.loaded_image is None:
            return
        label = self.w["image_preview"]
        target_w = max(label.width(), 1)
        target_h = max(label.height(), 1)
        resized = resize_to_fit(self.loaded_image, target_w, target_h)
        self.w["image_preview"].setPixmap(self._pil_to_pixmap(resized))

    @staticmethod
    def _pil_to_pixmap(pil_image):
        img = pil_image.convert("RGB")
        data = img.tobytes("raw", "RGB")
        qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg.copy())

    def resizeEvent(self, event):  # noqa: N802 - Qt override
        super().resizeEvent(event)
        self._update_image()

    def closeEvent(self, event):  # noqa: N802 - Qt override
        # Cancel and wait for any running export so the worker thread is torn
        # down cleanly (avoids a crash if the window closes mid-export).
        if self._thread is not None and self._thread.isRunning():
            cancel_export()
            self._thread.quit()
            self._thread.wait()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Algorithm / video state driven visibility
    # ------------------------------------------------------------------
    def _on_video_state_change(self):
        self._refresh_algorithm_options()
        self._update_algorithm_visibility()
        self._update_export_buttons()

    def _refresh_algorithm_options(self):
        """Drunk is only available for video (matches old GUI behavior)."""
        combo = self.w["algo_combo"]
        current = combo.currentText()
        options = ["Bayer", "Floyd-Steinberg"]
        if media_state.is_video:
            options.append("Drunk")

        combo.blockSignals(True)
        combo.clear()
        combo.addItems(options)
        if current in options:
            combo.setCurrentText(current)
        combo.blockSignals(False)

    def _on_algorithm_changed(self, _text):
        self._update_algorithm_visibility()

    def _update_algorithm_visibility(self):
        algo = self.w["algo_combo"].currentText()

        bayer = algo == "Bayer"
        fs = algo == "Floyd-Steinberg"
        drunk_sel = algo == "Drunk"

        # Drunk reuses the Floyd-Steinberg weights plus its own extra settings.
        self._set_row_visible("bayer_label", "matrix_frame", bayer)
        self._set_row_visible("fs_label", "fs_settings_subcontainer", fs or drunk_sel)
        self._set_row_visible("drunk_label", "drunk_settings_container", drunk_sel)
        # Video settings only make sense once a video is loaded.
        self._set_row_visible(
            "video_label", "video_settings_container", media_state.is_video
        )

    def _set_row_visible(self, label_name, field_name, visible):
        for name in (label_name, field_name):
            self._set_named_visible(name, visible)

    def _set_named_visible(self, name, visible):
        """Toggle a widget by object name, or every widget in a named layout.

        ui_loader only collects widgets, so QLayout containers (e.g.
        fs_settings_subcontainer) are resolved here via findChild and their
        child widgets are toggled individually.
        """
        widget = self.w.get(name)
        if widget is not None:
            widget.setVisible(visible)
            return
        layout = self.centralWidget().findChild(QLayout, name)
        if layout is not None:
            self._set_layout_visible(layout, visible)

    def _set_layout_visible(self, layout, visible):
        """Recursively toggle every widget in a layout and its sub-layouts."""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            child = item.widget()
            if child is not None:
                child.setVisible(visible)
            elif item.layout() is not None:
                self._set_layout_visible(item.layout(), visible)

    # ------------------------------------------------------------------
    # Export button availability
    # ------------------------------------------------------------------
    def _update_export_buttons(self):
        has_media = self.loaded_image is not None
        is_video = media_state.is_video

        self.w["export_png_btn"].setVisible(has_media and not is_video)
        self.w["export_jpg_btn"].setVisible(has_media and not is_video)
        self.w["export_video_btn"].setVisible(has_media and is_video)

    # ------------------------------------------------------------------
    # Settings collectors
    # ------------------------------------------------------------------
    def _fs_weights(self):
        # fs_dither(image, scale, r, dl, d, dr)
        return [
            self.w["rsliderfs"].value(),
            self.w["dlsliderfs"].value(),
            self.w["dsliderfs"].value(),
            self.w["drsliderfs"].value(),
        ]

    def _common_kwargs(self):
        return {
            "algorithm": self.w["algo_combo"].currentText(),
            "matrix_selection": self.w["matrix_combo"].currentText(),
            "grayscale_enabled": self.w["grayscale_box"].isChecked(),
            "downscale": self.w["downscale_slider"].value(),
            "fs_weights": self._fs_weights(),
        }

    def _drunk_settings(self):
        """Extra Drunk-mode controls (see ui.ui drunk_settings_container).

        Excludes drunkenness_level, which is passed separately as the dedicated
        export_video/drunk parameter.
        """
        return {
            "frames_per_shift": self.w["frame_slider"].value(),
            "randomness_enabled": self.w["random_check"].isChecked(),
            "randomness": self.w["random_slider"].value(),
            "constant_variability": self.w["variability_check"].isChecked(),
            "per_weight": self.w["perweight_check"].isChecked(),
            "integer_wrapping": self.w["wrapping_check"].isChecked(),
        }

    def _video_settings(self):
        """Encoder choice and size constraint (see ui.ui video_settings_container)."""
        return {
            "encoder": self.w["encoder_combo"].currentText(),
            "size_constraint_mb": self.w["size_spin"].value(),
        }

    # ------------------------------------------------------------------
    # Exports
    # ------------------------------------------------------------------
    def _export_image(self, fmt):
        if self.loaded_image is None:
            return
        filt = "PNG files (*.png)" if fmt == "png" else "JPG files (*.jpg)"
        out_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", filt)
        if not out_path:
            return

        kwargs = self._common_kwargs()
        kwargs.update(
            loaded_image=self.loaded_image,
            format=fmt,
            image_output_path=out_path,
            update_callback=None,
        )
        self._run_export(export_image, kwargs, is_video=False)

    def _export_video_or_cancel(self):
        # While an export is running, this button acts as Cancel.
        if self._thread is not None and self._thread.isRunning():
            cancel_export()
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Video", "", "MP4 files (*.mp4)"
        )
        if not out_path:
            return

        algo = self.w["algo_combo"].currentText()
        kwargs = self._common_kwargs()
        kwargs.update(
            media_state=media_state,
            drunkenness_level=(
                self.w["constant_slider"].value() if algo == "Drunk" else None
            ),
            drunk_settings=self._drunk_settings() if algo == "Drunk" else None,
            video_output_path=out_path,
            update_callback=None,
            enable_printing=False,
            **self._video_settings(),
        )
        self._run_export(export_video, kwargs, is_video=True)

    def _run_export(self, fn, kwargs, is_video):
        from PySide6.QtCore import QThread

        reset_cancel_flag()
        self.w["progress_bar"].setValue(0)

        self._thread = QThread()
        self._worker = ExportWorker(fn, kwargs)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.error.connect(self._on_export_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        # Reset UI and drop references only once the thread has fully stopped,
        # so we never GC a live QThread/worker (avoids a native crash).
        self._thread.finished.connect(self._on_export_finished)
        self._thread.finished.connect(self._thread.deleteLater)

        if is_video:
            self.w["export_video_btn"].setText("Cancel")

        self._set_controls_enabled(False, keep_video_btn=is_video)
        self._thread.start()

    def _on_progress(self, value):
        self.w["progress_bar"].setValue(int(value * 100))

    def _on_export_error(self, message):
        # "Export cancelled." is an expected, non-fatal message.
        if message != "Export cancelled.":
            QMessageBox.critical(self, "Export Error", message)

    def _on_export_finished(self):
        self.w["export_video_btn"].setText(self._export_video_default_text)
        self._set_controls_enabled(True)
        self._update_export_buttons()
        self.w["progress_bar"].setValue(0)
        self._thread = None
        self._worker = None

    def _set_controls_enabled(self, enabled, keep_video_btn=False):
        for name in (
            "load_media_btn",
            "export_png_btn",
            "export_jpg_btn",
            "algo_combo",
        ):
            widget = self.w.get(name)
            if widget is not None:
                widget.setEnabled(enabled)
        if not keep_video_btn:
            self.w["export_video_btn"].setEnabled(enabled)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DithererWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
