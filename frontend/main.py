import webview
import subprocess
import threading

class API:
    def __init__(self):
        self.window = None  # Will be assigned later

    def run_script_live(self):
        def stream_output():
            proc = subprocess.Popen(
                ['python', '../backend/main.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for line in proc.stdout:
                escaped = line.replace('\\', '\\\\').replace("'", "\\'")
                self.window.evaluate_js(f"appendOutput('{escaped}')")
            proc.stdout.close()
            proc.wait()

        threading.Thread(target=stream_output, daemon=True).start()

api = API()

# This function is called once the window is ready
def on_loaded():
    api.window = webview.windows[0]  # Assign window reference
    # Optionally do any init logic here

if __name__ == '__main__':
    webview.create_window("Live Output Example", "gui/index.html", js_api=api)
    webview.start(on_loaded, gui='qt', debug=True)
