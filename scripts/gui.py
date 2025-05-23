import webview, subprocess, os, threading
from pathlib import Path

class API:
    def __init__(self):
        self._files_dir = Path(__file__).parent.parent/"files"
        self._files = self.__init_files()
        self._window_loaded = threading.Event()
        self._latest_run = []

    def page_loaded(self):
        self._window_loaded.set()

    def __init_files(self):
        result = dict()
        for sub_dir in os.listdir(self._files_dir):
            sub_dir_name = self._files_dir/sub_dir
            if os.path.isdir(sub_dir_name):
                for file in os.listdir(sub_dir_name):
                    if file.endswith("_LOG.txt"): 
                        file_name = f"{sub_dir_name}/{file.removesuffix('_LOG.txt')}"
                        result[file_name] = file
        return result
    
    def open_file_dialog(self):
        # Use the window created by webview
        window = webview.windows[0]
        result = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True)
        return result if result else []
    
    def get_run_files(self):
        pass

    def run_overview(self):
        webview.windows[0].evaluate_js(f"renderLastRun({self._latest_run})")



    def run_script_on_files(self, files: list):
        for file_path in files:
            result = subprocess.run(
                ["python", "scripts/multi_main.py", file_path],
                capture_output=True,
                text=True
            )
            output = result.stdout.strip()
            success = result.returncode == 0
            if success:
                if output.endswith("_LOG.txt"):
                    file_name = output.removesuffix("_LOG.txt")
                    self._files[file_name] = output
                    self._latest_run.append(file_name)

        webview.windows[0].evaluate_js('window.location.href = "run-overview.html";')
        self._window_loaded.wait()
        webview.windows[0].evaluate_js(f"renderLastRun({self._latest_run})")

    def get_files(self):
        return list(self._files.keys())

    def get_log(self, key):
        file_path = self._files_dir/self._files[key]
        with open(file_path, "r") as f:
            return f.read() 

api = API()

def maximize_window():
    window = webview.windows[0]
    window.restore()
    window.maximize()

webview.create_window("Scan-Checker", "../gui/index.html", js_api=api)
webview.start(maximize_window, debug=True)
