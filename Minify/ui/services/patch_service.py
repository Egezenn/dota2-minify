import json
import threading
import time
from typing import Any, Dict, List

import patch
from core import output


class PatchService:
    def __init__(self) -> None:
        self._window: Any = None
        self._is_patching: bool = False
        self._logs: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

        output.register_listener(self._on_output_log)
        output.register_download_listener(self._on_download_progress)

    def set_window(self, window: Any) -> None:
        self._window = window

    def _on_download_progress(self, data: Dict[str, Any]) -> None:
        if self._window:
            try:
                js_str = json.dumps(data)
                self._window.evaluate_js(f"window.onDownloadProgress && window.onDownloadProgress({js_str});")
            except Exception:
                pass

    def _on_output_log(self, text: str, msg_type: str | None) -> None:
        if msg_type == "clear":
            with self._lock:
                self._logs.clear()
            if self._window:
                try:
                    self._window.evaluate_js("window.onLogReceived && window.onLogReceived({text: '', type: 'clear'});")
                except Exception:
                    pass
            return

        log_entry = {
            "text": text,
            "type": msg_type or "info",
            "timestamp": time.strftime("%H:%M:%S"),
        }
        with self._lock:
            self._logs.append(log_entry)

        if self._window:
            try:
                js_str = json.dumps(log_entry)
                self._window.evaluate_js(f"window.onLogReceived && window.onLogReceived({js_str});")
            except Exception:
                pass

    def start_patch(self) -> Dict[str, Any]:
        if self._is_patching:
            return {"status": "already_running"}

        self._is_patching = True
        if self._window:
            try:
                self._window.evaluate_js("window.onPatchStatusChange && window.onPatchStatusChange(true);")
            except Exception:
                pass

        def run_patch_thread() -> None:
            try:
                patch.patcher()
            except Exception as e:
                output.add_text(f"Patch failed: {e}", msg_type="error")
            finally:
                self._is_patching = False
                if self._window:
                    try:
                        self._window.evaluate_js("window.onPatchStatusChange && window.onPatchStatusChange(false);")
                    except Exception:
                        pass

        threading.Thread(target=run_patch_thread, daemon=True).start()
        return {"status": "started"}

    def start_uninstall(self, remove_everything: bool = False) -> Dict[str, Any]:
        if self._is_patching:
            return {"status": "already_running"}

        self._is_patching = True
        if self._window:
            try:
                self._window.evaluate_js("window.onPatchStatusChange && window.onPatchStatusChange(true);")
            except Exception:
                pass

        def run_uninstall_thread() -> None:
            try:
                if remove_everything:
                    patch.unins.wipe()
                else:
                    patch.unins.uninstall()
            except Exception as e:
                output.add_text(f"Uninstall failed: {e}", msg_type="error")
            finally:
                self._is_patching = False
                if self._window:
                    try:
                        self._window.evaluate_js("window.onPatchStatusChange && window.onPatchStatusChange(false);")
                    except Exception:
                        pass

        threading.Thread(target=run_uninstall_thread, daemon=True).start()
        return {"status": "started"}

    def is_patching(self) -> bool:
        return self._is_patching

    def get_logs(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._logs)

    def clear_logs(self) -> bool:
        with self._lock:
            self._logs.clear()
        return True
