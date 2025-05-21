import webview

class API:
    def greet(self):
        return "Hello from backend!"

    def open_file_dialog(self):
        # Use the window created by webview
        window = webview.windows[0]
        result = window.create_file_dialog(webview.OPEN_DIALOG)
        return result[0] if result else None
        
api = API()
webview.create_window("Scan-Checker", "gui/test.html", js_api=api)
webview.start(debug=True)
