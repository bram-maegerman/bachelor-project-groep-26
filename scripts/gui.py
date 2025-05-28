import webview, subprocess, os, threading, json, base64
from pathlib import Path

class API:
    def __init__(self):
        self._files_dir = Path(__file__).parent.parent/"files"
        self._window_loaded = threading.Event()
        self._latest_run = set()

    def page_loaded(self):
        self._window_loaded.set()

    def get_all_files(self):
        result = dict()
        for sub_dir in os.listdir(self._files_dir):
            sub_dir_name = self._files_dir/sub_dir
            if os.path.isdir(sub_dir_name):
                sub_result = []
                for file in os.listdir(sub_dir_name):
                    if file.endswith("_LOG.txt"):
                        file_name = f"{sub_dir_name}/{file.removesuffix('_LOG.txt')}"
                        sub_result.append(file_name)
                result [str(sub_dir_name)] = sub_result
        return result

    def open_file_dialog(self):
        # Use the window created by webview
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
        file_path = key+"_LOG.txt"
        with open(file_path, "r") as f:
            return f.read()
        
    def read_pdf_as_data_url(self, path):
        path = Path(path.replace("/", os.sep)).resolve()
        print(f"Resolved path: {path}")

        if not path.exists():
            print("PDF not found!")
            return None

        with open(path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            return f'data:application/pdf;base64,{encoded}'

api = API()

def maximize_window():
    window = webview.windows[0]
    window.restore()
    window.maximize()

webview.create_window("Scan-Checker", "../gui/index.html", js_api=api)
webview.start(maximize_window, debug=True)
