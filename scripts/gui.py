import webview, subprocess, json, threading

class API:
    def __init__(self):
        self.window_loaded = threading.Event()

    def page_loaded(self):
        self.window_loaded.set()

    def open_file_dialog(self):
        # Use the window created by webview
        window = webview.windows[0]
        result = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True)
        return result if result else []

    def run_script_on_files(self, files: list):
        results = []

        webview.windows[0].evaluate_js('window.location.href = "progress.html";')
        self.window_loaded.wait()
        webview.windows[0].evaluate_js(f"loadFilesInTable({files})")

        for file_path in files:
            webview.windows[0].evaluate_js(f"setFileInProgress({json.dumps(file_path)})")
            result = subprocess.run(
                ["python", "scripts/multi_main.py", file_path],
                capture_output=True,
                text=True
            )
            result_object = {
                "file": file_path,
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
            results.append(result_object)
            webview.windows[0].evaluate_js(f"updateResult({json.dumps(result_object)})")

        return results

api = API()

def maximize_window():
    window = webview.windows[0]
    window.restore()
    window.maximize()

webview.create_window("Scan-Checker", "../gui/index.html", js_api=api)
webview.start(maximize_window, debug=True)
