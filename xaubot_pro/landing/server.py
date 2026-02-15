"""XAUBOT Pro - Landing Page Web Server
Run: python server.py
Serves on port 80 (or 8080 if 80 is blocked)
"""
import http.server
import socketserver
import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/index.html'
        return super().do_GET()

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")

def run(port=80):
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"XAUBOT Pro landing page running on http://0.0.0.0:{port}")
            httpd.serve_forever()
    except OSError:
        if port == 80:
            print(f"Port 80 in use, trying 8080...")
            run(8080)
        else:
            print(f"Port {port} also in use!")
            sys.exit(1)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    run(port)
