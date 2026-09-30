"""AEROTWIN REACT DASHBOARD FRONTEND SERVER
Serves the React Ground Control Station application on http://localhost:3000
Connected to Python REST API Backend on http://localhost:8000
"""

import sys
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent

class ReactFrontendHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

def run_frontend_server(port=3000):
    server_address = ("", port)
    httpd = ThreadingHTTPServer(server_address, ReactFrontendHandler)
    httpd.daemon_threads = True
    print(f"Aerotwin React Dashboard running on http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_frontend_server(3000)

