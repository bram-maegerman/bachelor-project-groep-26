import webview, subprocess, os, threading, json, base64
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"

class API:
    def __init__(self):
        self._files_dir = Path(__file__).parent.parent / "files"
        self._window_loaded = threading.Event()
        self._latest_run = set()
        self._init_config()  # Ensure config file exists with defaults
        self.projects: dict = self._load_projects()
        self.log_level = self._load_log_level()
        self.next_run = []

    def _init_config(self):
        if not CONFIG_FILE.exists():
            default_config = {
                "projects": [],
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
                    return {"projects": [], "log_level": 1}
        else:
            self._init_config()
            return {"projects": [], "log_level": 1}

    def _save_config(self, data):
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _save_projects(self, paths: list):
        data = self._load_config()
        data["projects"] = paths
        self._save_config(data)

    def _load_log_level(self):
        data = self._load_config()
        return data.get("log_level", 1)

    def _save_log_level(self, level: int):
        data = self._load_config()
        data["log_level"] = level
        self._save_config(data)

    def choose_folder(self):
        window = webview.windows[0]
        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            return result[0]
        else:
            return ""

    def set_settings(self, log_level: int):
        self.log_level = log_level
        self._save_log_level(log_level)

    def get_settings(self):
        return {
            "projects": self._load_projects(),
            "log_level": self._load_log_level()
        }

    def add_project(self, name: str, path: str):
        if not name or not path:
            print("Project name and path cannot be empty.")
            return
        if not os.path.exists(path):
            print(f"Path '{path}' does not exist.")
            return
        if name in self.projects:
            print(f"Project '{name}' already exists.")
            return
        if not os.path.isabs(path):
            print(f"Path '{path}' must be an absolute path.")
            return
        if not os.path.isdir(path):
            print(f"Path '{path}' is not a directory.")
            return
        paths = self.projects
        paths[name] = path
        self._save_projects(paths)

    def remove_project(self, name: str):
        paths = self.projects
        try:
            del paths[name]
        except KeyError:
            print(f"Project '{name}' not found.")
            return

        #TODO: add code to remove all files related to this project

        self._save_projects(paths)

    def get_projects(self):
        return self.projects

    def set_projects(self, path: str):
        self._selected_projects = path

    def set_log_level(self, level: int):
        self.log_level = level
        self._save_log_level(level)

    def get_log_level(self):
        return self.log_level

    def _load_projects(self):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("projects", dict())

    def get_files_for_project(self, project: str):
        projects = self._load_projects()
        if project not in projects:
            print(f"Project '{project}' not found.")
            return []

        project_path = projects[project]
        if not os.path.exists(project_path):
            print(f"Project path '{project_path}' does not exist.")
            return []

        files = []
        for root, _, filenames in os.walk(project_path):
            for filename in filenames:
                if filename.endswith("_LOG.txt"):
                    file_path_without_suffix = os.path.join(root, filename).removesuffix("_LOG.txt")
                    files.append(file_path_without_suffix)
        return files

    def get_all_files(self):
        result = dict()

        projects: dict = self._load_projects()

        for project in projects.keys():
            base_path = Path(projects[project])

            if not base_path.exists():
                continue

            for sub_dir in base_path.iterdir():
                if sub_dir.is_dir():
                    sub_result = []
                    for file in sub_dir.iterdir():
                        if file.name.endswith("_LOG.txt"):
                            file_path_without_suffix = str(file).removesuffix("_LOG.txt")
                            sub_result.append(file_path_without_suffix)

                    if sub_result:
                        result[f"{project}_{sub_dir.name}"] = sub_result
        return result


    def open_file_dialog(self):
        window = webview.windows[0]
        result = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True)
        return result if result else []

    def run_overview(self):
        webview.windows[0].evaluate_js(f"renderOverview({json.dumps(self.get_all_files())})")

    def run_last(self):
        webview.windows[0].evaluate_js(f"loadLastRunFiles({list(self._latest_run)})")

    def project_overview(self, project: str):
        files = self.get_files_for_project(project)
        if not files:
            print(f"No files found for project '{project}'.")
            return
        # Convert file paths to a JSON-compatible format
        files = [str(Path(file).resolve()) for file in files]
        webview.windows[0].evaluate_js(f"renderProjectOverview({json.dumps(files)})")

    def set_next(self, files: list):
        self.next_run = files

    def run_script_on_files(self):
        # Load all files from current run in a table
        webview.windows[0].evaluate_js(f"loadFilesInTable({self.next_run})")

        self._latest_run = set()

        # Load latest settings from json file
        projects = self._selected_projects or self._load_projects()

        for file_path in self.next_run:
            # Updates table of files to see which one is processing a.t.m.
            webview.windows[0].evaluate_js(f"setFileInProgress({json.dumps(file_path)})")

            result = subprocess.run(
                ["python", "scripts/main.py", file_path, projects],
                capture_output=True,
                text=True
            )

            log_file_location = result.stdout.strip()

            subprocess.run(
                ["python", "scripts/compression.py", str(file_path), str(log_file_location)],
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

webview.create_window("Scan-Checker", "../gui/projects.html", js_api=api)
webview.start(maximize_window, debug=True)
