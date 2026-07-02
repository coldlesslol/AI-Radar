#!/usr/bin/env python3
"""Local config API server — port 8766.

Serves GET/POST /api/config so devlog.html can read and write
config/user-config.json without touching code.

Run:  pipeline/.venv/bin/python pipeline/api_server.py
"""
from __future__ import annotations

import json
import pathlib
from http.server import BaseHTTPRequestHandler, HTTPServer

CONFIG_PATH = pathlib.Path(__file__).parent.parent / "config" / "user-config.json"
PORT = 8766

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


class Handler(BaseHTTPRequestHandler):
    def _cors(self, code: int = 200, content_type: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        for k, v in CORS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_OPTIONS(self):
        self._cors()

    def do_GET(self):
        if self.path != "/api/config":
            self._cors(404); self.wfile.write(b'{"error":"not found"}'); return
        data = CONFIG_PATH.read_text(encoding="utf-8") if CONFIG_PATH.exists() else '{"stocks":[],"sources":[]}'
        self._cors()
        self.wfile.write(data.encode())

    def do_POST(self):
        if self.path != "/api/config":
            self._cors(404); self.wfile.write(b'{"error":"not found"}'); return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            self._cors(400); self.wfile.write(b'{"error":"invalid json"}'); return
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
        self._cors()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    server = HTTPServer(("localhost", PORT), Handler)
    print(f"Config API  →  http://localhost:{PORT}/api/config")
    print("Ctrl-C to stop.")
    server.serve_forever()
