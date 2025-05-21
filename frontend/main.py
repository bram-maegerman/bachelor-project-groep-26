import webview

class API:
    def greet(self):
        return "Hello from backend!"

api = API()
webview.create_window("Scan-Checker", "gui/index.html", js_api=api)
webview.start(debug=True)
