"""Simple Flask-like HTTP server for the engineering dashboard."""
import http.server
import os

PORT = 8080
HTML_FILE = os.path.join(os.path.dirname(__file__), "index.html")


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(HTML_FILE, "rb") as f:
                self.wfile.write(f.read())
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress request logging


if __name__ == "__main__":
    server = http.server.HTTPServer(("", PORT), DashboardHandler)
    print(f"Dashboard server running on http://localhost:{PORT}")
    server.serve_forever()
