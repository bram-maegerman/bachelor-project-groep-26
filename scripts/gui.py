import webview, subprocess, os, threading, json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"

class API:
    def __init__(self):
        self._files_dir = Path(__file__).parent.parent / "files"
        self._window_loaded = threading.Event()
        self._latest_run = set()
        self._init_config()  # Ensure config file exists with defaults
        self.export_path = self._load_export_path()
        self.log_level = self._load_log_level()

    def _init_config(self):
        if not CONFIG_FILE.exists():
            default_config = {
                "export_path": "",
                "log_level": 1
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(default_config, f, indent=2)

    def _load_config(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as f:
                try:
                    data = json.load(f)
                    return data
                except json.JSONDecodeError:
                    # In case of corrupted JSON, reset to default
                    self._init_config()
                    return {"export_path": "", "log_level": 1}
        else:
            self._init_config()
            return {"export_path": "", "log_level": 1}

    def _save_config(self, data):
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _load_export_path(self):
        data = self._load_config()
        return data.get("export_path", "")

    def _save_export_path(self, path: str):
        data = self._load_config()
        data["export_path"] = path
        self._save_config(data)

    def _load_log_level(self):
        data = self._load_config()
        return data.get("log_level", 1)

    def _save_log_level(self, level: int):
        data = self._load_config()
        data["log_level"] = level
        self._save_config(data)

    def choose_export_path(self):
        window = webview.windows[0]
        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            self.export_path = result[0]
            self._save_export_path(self.export_path)
            return self.export_path
        return ""

    def get_export_path(self):
        return self.export_path

    def set_log_level(self, level: int):
        self.log_level = level
        self._save_log_level(level)

    def get_log_level(self):
        return self.log_level

    def page_loaded(self):
        self._window_loaded.set()

    def get_all_files(self):
        result = dict()
        for sub_dir in os.listdir(self._files_dir):
            sub_dir_name = self._files_dir / sub_dir
            if os.path.isdir(sub_dir_name):
                sub_result = []
                for file in os.listdir(sub_dir_name):
                    if file.endswith("_LOG.txt"):
                        file_name = f"{sub_dir_name}/{file.removesuffix('_LOG.txt')}"
                        sub_result.append(file_name)
                result[str(sub_dir_name)] = sub_result
        return result

    def open_file_dialog(self):
        window = webview.windows[0]
        result = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True)
        return result if result else []

    def run_overview(self):
        webview.windows[0].evaluate_js(f"renderOverview({json.dumps(self.get_all_files())})")

    def run_last(self):
        webview.windows[0].evaluate_js(f"renderLastRun({list(self._latest_run)})")

    def run_script_on_files(self, files: list):
        for file_path in files:
            result = subprocess.run(
                ["python", "scripts/main.py", file_path],
                capture_output=True,
                text=True
            )
            output = result.stdout.strip()
            success = result.returncode == 0
            if success:
                if output.endswith("_LOG.txt"):
                    file_name = output.removesuffix("_LOG.txt")
                    self._latest_run.add(file_name)
        return

    def get_log(self, key):
        file_path = key + "_LOG.txt"
        with open(file_path, "r") as f:
            return f.read()

api = API()

def maximize_window():
    window = webview.windows[0]
    window.restore()
    window.maximize()

webview.create_window("Scan-Checker", "../gui/index.html", js_api=api)
webview.start(maximize_window, debug=True)
