import webview, subprocess

class API:
    def open_file_dialog(self):
        # Use the window created by webview
        window = webview.windows[0]
        result = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True)
        return result if result else []
    
    def run_script_on_files(self, files:list):
        result = subprocess.run(["python", "../backend/pipeline.py", *files])
        return result.returncode
        
api = API()

def maximize_window():
    window = webview.windows[0]
    window.restore()
    window.maximize()

webview.create_window("Scan-Checker", "../gui/index.html", js_api=api)
webview.start(maximize_window)
