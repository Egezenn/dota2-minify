# ui.app

## `Api()`

*No documentation available.*

<details open><summary>Source</summary>

```python
class Api:
    def __init__(self) -> None:
        self.window: Any = None
        self._is_patching: bool = False
        self._logs: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

        output.register_listener(self._on_output_log)

    def set_window(self, window: Any) -> None:
        self.window = window

    def _on_output_log(self, text: str, msg_type: str | None) -> None:
        log_entry = {
            "text": text,
            "type": msg_type or "info",
            "timestamp": time.strftime("%H:%M:%S"),
        }
        with self._lock:
            self._logs.append(log_entry)

        if self.window:
            try:
                js_str = json.dumps(log_entry)
                self.window.evaluate_js(f"window.onLogReceived && window.onLogReceived({js_str});")
            except Exception:
                pass

    def start_patch(self) -> Dict[str, Any]:
        if self._is_patching:
            return {"status": "already_running"}

        self._is_patching = True
        if self.window:
            try:
                self.window.evaluate_js("window.onPatchStatusChange && window.onPatchStatusChange(true);")
            except Exception:
                pass

        def run_patch_thread() -> None:
            try:
                output.add_text("Starting patch process...", msg_type="info")
                patch.patcher()
                output.add_text("Patch operation completed.", msg_type="success")
            except Exception as e:
                output.add_text(f"Patch failed: {e}", msg_type="error")
            finally:
                self._is_patching = False
                if self.window:
                    try:
                        self.window.evaluate_js("window.onPatchStatusChange && window.onPatchStatusChange(false);")
                    except Exception:
                        pass

        threading.Thread(target=run_patch_thread, daemon=True).start()
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

    def get_mods(self) -> List[Dict[str, Any]]:
        mods_shared.scan_mods()
        mod_list = mods_shared.visually_available_mods or mods_shared.mods_alphabetical
        return [{"name": mod, "enabled": mods_shared.get_state(mod)} for mod in mod_list]

    def set_mods(self, data: Dict[str, bool]) -> bool:
        try:
            for mod_name, enabled in data.items():
                mods_shared.set_state(mod_name, bool(enabled))
            return True
        except Exception:
            return False

    def get_localization(self, lang: str = "EN") -> Dict[str, str]:
        if not lang:
            lang = config.get("locale", "EN")
        return localization.get_for_locale(lang)
```

</details>

## `launch_ui()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def launch_ui() -> None:
    localization.load_headless()
    utils.setup_system()
    browsers.initialize()
    helper.bulk_exec_script("initial", False)

    ui_dir = os.path.dirname(os.path.abspath(__file__))
    dist_index = os.path.join(ui_dir, "web", "dist", "index.html")

    url = dist_index

    dev_port = 5173
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        res = sock.connect_ex(("127.0.0.1", dev_port))
        sock.close()
        if res == 0:
            url = f"http://localhost:{dev_port}"
    except Exception:
        pass

    api = Api()
    window = webview.create_window(
        title="Dota 2 Minify",
        url=url,
        js_api=api,
        width=960,
        height=680,
        min_size=(700, 500),
        resizable=True,
    )
    api.set_window(window)
    webview.start()
```

</details>
