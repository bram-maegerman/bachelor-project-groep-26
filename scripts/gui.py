import webview, subprocess, os, threading, json, base64
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"

class API:
    def __init__(self):
        self._files_dir = Path(__file__).parent.parent / "files"
        self._window_loaded = threading.Event()
        self._latest_run = set()
        self._init_config()  # Ensure config file exists with defaults
        self.export_paths = self._load_export_paths()
        self.log_level = self._load_log_level()
        self.next_run = []

    def _init_config(self):
        if not CONFIG_FILE.exists():
            default_config = {
                "export_paths": [],
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
                    return {"export_paths": [], "log_level": 1}
        else:
            self._init_config()
            return {"export_paths": [], "log_level": 1}

    def _save_config(self, data):
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _load_export_paths(self):
        data = self._load_config()
        return data.get("export_paths", [])

    def _save_export_paths(self, paths: list):
        data = self._load_config()
        data["export_paths"] = paths
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
            return result[0]
        else:
            return self.export_paths

    def set_settings(self, export_paths: list, log_level: int):
        self.export_paths = export_paths
        self.log_level = log_level
        self._save_export_paths(export_paths)
        self._save_log_level(log_level)

    def get_settings(self):
        return {
            "export_paths": self._load_export_paths(),
            "log_level": self._load_log_level()
        }

    def add_export_path(self, name: str, path: str):
        paths = self._load_export_paths()
        paths.append({"name": name, "path": path})
        self._save_export_paths(paths)

    def remove_export_path(self, name: str):
        paths = self._load_export_paths()
        paths = [p for p in paths if p["name"] != name]
        self._save_export_paths(paths)

    def get_export_paths(self):
        return self._load_export_paths()

    def set_log_level(self, level: int):
        self.log_level = level
        self._save_log_level(level)

    def get_log_level(self):
        return self.log_level

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

    def set_next(self, files: list):
        self.next_run = files

    def run_script_on_files(self):
        # Load all files from current run in a table
        webview.windows[0].evaluate_js(f"loadFilesInTable({self.next_run})")

        self._latest_run = set()

        # Load latest settings from json file
        export_path = self._load_export_path()

        for file_path in self.next_run:
            # Updates table of files to see which one is processing a.t.m.
            webview.windows[0].evaluate_js(f"setFileInProgress({json.dumps(file_path)})")

            result = subprocess.run(
                ["python", "scripts/main.py", file_path, export_path],
                capture_output=True,
                text=True
            )
            success = result.returncode == 0

            # Updates table with the result of the current file
            result_object = {
                "file": file_path,
                "success": success,
            }
            webview.windows[0].evaluate_js(f"updateResult({json.dumps(result_object)})")

            output = result.stdout.strip()
            if success:
                if output.endswith("_LOG.txt"):
                    file_name = output.removesuffix("_LOG.txt")
                    self._latest_run.add(file_name)

        webview.windows[0].evaluate_js(f"finished()")
        return

    def get_log(self, key):
        file_path = key + "_LOG.txt"
        if not os.path.exists(file_path):
            return "Log file not found."

        with open(file_path, "r") as f:
            text = f.read()

        summary_index = text.find("\n\n")


        log_lines = text[:summary_index]
        summary_block = text[summary_index:].split("\n")

        # Filter log_lines based on log_level
        filtered_logs = []
        for line in log_lines.split("\n"):
            if ")[W" in line:
                filtered_logs.append(line)
            if self.log_level == 2:
                if ")[I" in line:
                    filtered_logs.append(line)
            if self.log_level == 3:
                if ")[S" in line:
                    filtered_logs.append(line)

        filtered_logs.extend(summary_block)
        return "\n".join(filtered_logs)



    def read_pdf_as_data_url(self, path):
        path = Path(path.replace("/", os.sep)).resolve()

        if not path.exists():
            return None

        with open(path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            return f'data:application/pdf;base64,{encoded}'

api = API()

def maximize_window():
    window = webview.windows[0]
    window.restore()
    window.maximize()

webview.create_window("Scan-Checker", "../gui/homepage.html", js_api=api)
webview.start(maximize_window, debug=True)
