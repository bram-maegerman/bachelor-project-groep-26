import webview, subprocess, os, threading, json, base64
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"

class API:
    def __init__(self):
        self._files_dir = Path(__file__).parent.parent / "files"
        self._window_loaded = threading.Event()
        self._latest_run = set()
        self._init_config()  # Ensure config file exists with defaults
        self.projects, self.log_level = self._load_config()
        self.next_run = []
        self.next_export_path = None

    def _init_config(self):
        if not CONFIG_FILE.exists():
            default_config = {
                "projects": {},
                "log_level": 1
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(default_config, f, indent=2)

    def _load_config(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as f:
                try:
                    data = json.load(f)
                    return (data.get("projects", {}), data.get("log_level", 1))
                except json.JSONDecodeError:
                    # In case of corrupted JSON, reset to default
                    self._init_config()
                    return ({}, 1)
        else:
            self._init_config()
            return ({}, 1)

    def _save_config(self):
        data = {
            "projects": self.projects,
            "log_level": self.log_level
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _save_projects(self, paths: list):
        self.projects = paths
        self._save_config()

    def choose_folder(self):
        window = webview.windows[0]
        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            return result[0]
        else:
            return ""

    def set_log_level(self, log_level: int):
        self.log_level = log_level
        self._save_config()

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
            pathname = paths[name]
            projects = self.get_files_for_project(name)
            del paths[name]
            if os.path.exists(pathname):
                # empty the directory
                for file in projects:
                    try:
                        os.remove(file + '_LOG.txt')
                    except Exception as e:
                        print(f"Error removing file '{file}': {e}")
            else:
                print(f"Path '{pathname}' does not exist, cannot remove files.")
            self._save_projects(paths)
        except KeyError:
            print(f"Project '{name}' not found.")
            return

    def edit_project(self, name: str, new_name: str, new_path: str):
        if not name or not new_name or not new_path:
            print("Project name, new name, and new path cannot be empty.")
            return
        if not os.path.exists(new_path):
            print(f"Path '{new_path}' does not exist.")
            return
        if name not in self.projects:
            print(f"Project '{name}' does not exist.")
            return
        if not os.path.isabs(new_path):
            print(f"Path '{new_path}' must be an absolute path.")
            return
        if not os.path.isdir(new_path):
            print(f"Path '{new_path}' is not a directory.")
            return

        paths = self.projects
        del paths[name]
        paths[new_name] = new_path
        self._save_projects(paths)

    def get_export_path(self, project: str):
        if project not in self.projects:
            print(f"Project '{project}' not found.")
            return None
        return self.projects[project]

    def get_projects(self):
        return self.projects

    def get_log_level(self):
        return self.log_level

    def set_log_level(self, level: int):
        self.log_level = level
        self._save_config()

    def get_files_for_project(self, project: str):
        projects = self.projects
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

        projects: dict = self.projects

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

    def set_export_path(self, path: str):
        if not path:
            print("Export path cannot be empty.")
            return
        if not os.path.exists(path):
            print(f"Export path '{path}' does not exist.")
            return
        if not os.path.isabs(path):
            print(f"Export path '{path}' must be an absolute path.")
            return
        self.next_export_path = path

    def open_file(self, file_path: str):
        file_path = Path(file_path.replace("/", os.sep)).resolve()
        if not file_path.exists():
            print(f"File '{file_path}' does not exist.")
            return
        if not file_path.is_file():
            print(f"Path '{file_path}' is not a file.")
            return

        # open the file with like the file explorer
        if os.name == 'nt':  # Windows
            os.startfile(file_path)

    def run_script_on_files(self):
        file_paths = [Path(x) for x in self.next_run]
        formatted_files = ["/".join(p.parts[-4:]) for p in file_paths]

        if not formatted_files:
            print("No files to process.")
            return

        if not self.next_export_path:
            print("No export path set.")
            return

        # Ensure the export path exists
        export_path = Path(self.next_export_path)
        if not export_path.exists():
            print(f"Export path '{self.next_export_path}' does not exist.")
            return

        webview.windows[0].evaluate_js(f"loadFilesInTable({formatted_files})")

        self._latest_run = set()

        for index, file_path in enumerate(self.next_run):
            current_file = formatted_files[index]
            # Updates table of files to see which one is processing a.t.m.
            webview.windows[0].evaluate_js(f"setFileInProgress({json.dumps(current_file)})")

            process_result = subprocess.Popen(
                ["python", "scripts/main.py", file_path, export_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            log_file_location = ""
            for line in process_result.stdout:
                stripped = line.strip()
                if stripped and stripped[0].isdigit():
                    webview.windows[0].evaluate_js(f"updatePercentage({json.dumps(stripped)})")
                log_file_location = stripped

            process_result.wait()

            print(log_file_location)
            webview.windows[0].evaluate_js(f"startCompressing({json.dumps(current_file)})")

            compress_result = subprocess.run(
                ["python", "scripts/compression.py", str(file_path), str(log_file_location)],
                capture_output=True,
                text=True
            )

            success = process_result.returncode == 0
            # Updates table with the result of the current file
            result_object = {
                "file": current_file,
                "success": success,
            }
            webview.windows[0].evaluate_js(f"updateResult({json.dumps(result_object)})")

            if success:
                if log_file_location.endswith("_LOG.txt"):
                    file_name = log_file_location.removesuffix("_LOG.txt")
                    self._latest_run.add(file_name)

        webview.windows[0].evaluate_js(f"finished()")
        return

    def get_log(self, key):
        file_path = key + "_LOG.txt" #TODO revisit this
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
                if ")[I" in line or ")[S" in line:
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

    def change_manual_check_status(self, path, checkedBool):
        with open(path, 'r') as file:
            lines = file.readlines()

        for i, line in enumerate(lines):
            if line.strip().startswith('manually_checked='):
                lines[i] = f'manually_checked={"true" if checkedBool else "false"}\n'
                break

        with open(path, 'w') as file:
            file.writelines(lines)

api = API()

def maximize_window():
    window = webview.windows[0]
    window.restore()
    window.maximize()

def find_file(filename, search_path):
    for root, _, files in os.walk(search_path):
        if filename in files:
            return os.path.join(root, filename)
    return None

current_file = Path(__file__)
homepage = find_file("homepage.html", current_file.parent.parent)

if homepage:
    webview.create_window("Scan-Checker", homepage, js_api=api)
    webview.start(maximize_window, debug=True)
else:
    print("Couldn't find homepage.")