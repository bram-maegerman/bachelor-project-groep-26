import webview, subprocess, os
from pathlib import Path

class API:
    def __init__(self):
        self.path = Path(__file__).parent.parent/"files"
        self._files = self.__init_files()

    def __init_files(self):
        result = dict()
        for file in os.listdir(self.path):
            if file is not os.path.isdir(self.path/file):
                if file.endswith("_LOG.txt"): 
                    file_name = file.removesuffix("_LOG.txt")
                    result[file_name] = file
        return result
    
    def open_file_dialog(self):
        # Use the window created by webview
        window = webview.windows[0]
        result = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True)
        return result if result else []

    def run_script_on_files(self, files: list):
        results = []

        for file_path in files:
            result = subprocess.run(
                ["python", "scripts/multi_main.py", file_path],
                capture_output=True,
                text=True
            )
            output = result.stdout.strip()
            success = result.returncode == 0
            results.append({
            "file": file_path,
            "success": success,
            "stdout": output,
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
            })

        if success:
            if output.endswith("_LOG.txt"):
                file_name = output.removesuffix("_LOG.txt")
                self._files[file_name] = output

        return results
    
    def get_files(self):
        return list(self._files.keys())

    def get_log(self, key):
        file_path = self.path/self._files[key]
        with open(file_path, "r") as f:
            return f.read() 

api = API()

def maximize_window():
    window = webview.windows[0]
    window.restore()
    window.maximize()

webview.create_window("Scan-Checker", "../gui/index.html", js_api=api)
webview.start(maximize_window, debug=True)
