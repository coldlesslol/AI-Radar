#!/usr/bin/env python3
"""Local config API server — port 8766.

Serves GET/POST /api/config so devlog.html can read and write
config/user-config.json without touching code.

Run:  pipeline/.venv/bin/python pipeline/api_server.py
"""
from __future__ import annotations

import json
import os
import pathlib
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

CONFIG_PATH = pathlib.Path(__file__).parent.parent / "config" / "user-config.json"
PORT = 8766

DEFAULT_ALLOWED_ORIGINS = {
    "null",  # file:// local previews
    "http://localhost:8766",
    "http://127.0.0.1:8766",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://coldlesslol.github.io",
}
ALLOWED_ORIGINS = DEFAULT_ALLOWED_ORIGINS | {
    x.strip() for x in os.getenv("TECHRADAR_ALLOWED_ORIGINS", "").split(",") if x.strip()
}
CONFIG_TOKEN = os.getenv("TECHRADAR_CONFIG_TOKEN", "")

STOCK_KEYS = {"ticker", "name", "region", "currency", "cik"}
SOURCE_KEYS = {"id", "name", "url", "category", "cap"}
REGIONS = {"US", "CN", "HK"}
CURRENCIES = {"USD", "CNY", "HKD"}
SOURCE_CATEGORIES = {"news", "research", "company", "newsletter", "analysis"}
TICKER_RE = re.compile(r"^[A-Z0-9.^=-]{1,24}$")
CIK_RE = re.compile(r"^[0-9]{1,10}$")


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "source"


def _valid_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_config(payload: dict) -> dict:
    """Validate and normalize config/user-config.json payloads."""
    if not isinstance(payload, dict):
        raise ValueError("config must be an object")
    unknown_top = set(payload) - {"stocks", "sources"}
    if unknown_top:
        raise ValueError(f"unknown top-level keys: {', '.join(sorted(unknown_top))}")

    stocks = payload.get("stocks", [])
    sources = payload.get("sources", [])
    if not isinstance(stocks, list) or not isinstance(sources, list):
        raise ValueError("stocks and sources must be arrays")

    normalized_stocks = []
    for i, row in enumerate(stocks):
        if not isinstance(row, dict):
            raise ValueError(f"stocks[{i}] must be an object")
        unknown = set(row) - STOCK_KEYS
        if unknown:
            raise ValueError(f"stocks[{i}] unknown keys: {', '.join(sorted(unknown))}")
        ticker = str(row.get("ticker", "")).strip().upper()
        name = str(row.get("name", "")).strip()
        region = str(row.get("region", "US")).strip().upper()
        currency = str(row.get("currency", "USD")).strip().upper()
        if not TICKER_RE.match(ticker):
            raise ValueError(f"stocks[{i}].ticker is invalid")
        if not name:
            raise ValueError(f"stocks[{i}].name is required")
        if region not in REGIONS:
            raise ValueError(f"stocks[{i}].region is invalid")
        if currency not in CURRENCIES:
            raise ValueError(f"stocks[{i}].currency is invalid")
        item = {"ticker": ticker, "name": name, "region": region, "currency": currency}
        cik = str(row.get("cik", "")).strip()
        if cik:
            if not CIK_RE.match(cik):
                raise ValueError(f"stocks[{i}].cik is invalid")
            item["cik"] = cik.zfill(10)
        normalized_stocks.append(item)

    normalized_sources = []
    for i, row in enumerate(sources):
        if not isinstance(row, dict):
            raise ValueError(f"sources[{i}] must be an object")
        unknown = set(row) - SOURCE_KEYS
        if unknown:
            raise ValueError(f"sources[{i}] unknown keys: {', '.join(sorted(unknown))}")
        name = str(row.get("name", "")).strip()
        url = str(row.get("url", "")).strip()
        category = str(row.get("category", "news")).strip().lower()
        if not name:
            raise ValueError(f"sources[{i}].name is required")
        if not _valid_http_url(url):
            raise ValueError(f"sources[{i}].url must be http(s)")
        if category not in SOURCE_CATEGORIES:
            raise ValueError(f"sources[{i}].category is invalid")
        try:
            cap = int(row.get("cap", 10))
        except (TypeError, ValueError):
            raise ValueError(f"sources[{i}].cap must be an integer") from None
        if cap < 1 or cap > 100:
            raise ValueError(f"sources[{i}].cap must be between 1 and 100")
        normalized_sources.append({
            "id": str(row.get("id") or _slug(name)).strip(),
            "name": name,
            "url": url,
            "category": category,
            "cap": cap,
        })

    return {"stocks": normalized_stocks, "sources": normalized_sources}


def origin_allowed(origin: str | None) -> bool:
    return origin is None or origin in ALLOWED_ORIGINS


class Handler(BaseHTTPRequestHandler):
    def _cors(self, code: int = 200, content_type: str = "application/json") -> None:
        origin = self.headers.get("Origin")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        if origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin or "null")
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-TechRadar-Token")
        self.end_headers()

    def _json(self, code: int, payload: dict) -> None:
        self._cors(code)
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode())

    def _check_origin(self) -> bool:
        if origin_allowed(self.headers.get("Origin")):
            return True
        self._json(403, {"error": "origin not allowed"})
        return False

    def _check_token(self) -> bool:
        if not CONFIG_TOKEN:
            return True
        if self.headers.get("X-TechRadar-Token") == CONFIG_TOKEN:
            return True
        self._json(401, {"error": "invalid token"})
        return False

    def do_OPTIONS(self):
        if not self._check_origin():
            return
        self._cors()

    def do_GET(self):
        if not self._check_origin():
            return
        if self.path != "/api/config":
            self._json(404, {"error": "not found"}); return
        data = CONFIG_PATH.read_text(encoding="utf-8") if CONFIG_PATH.exists() else '{"stocks":[],"sources":[]}'
        self._cors()
        self.wfile.write(data.encode())

    def do_POST(self):
        if not self._check_origin() or not self._check_token():
            return
        if self.path != "/api/config":
            self._json(404, {"error": "not found"}); return
        length = int(self.headers.get("Content-Length", 0))
        if length > 65536:
            self._json(413, {"error": "payload too large"}); return
        body = self.rfile.read(length).decode("utf-8")
        try:
            parsed = validate_config(json.loads(body))
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid json"}); return
        except ValueError as e:
            self._json(400, {"error": str(e)}); return
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
        self._json(200, {"ok": True})

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    server = HTTPServer(("localhost", PORT), Handler)
    print(f"Config API  →  http://localhost:{PORT}/api/config")
    print("Ctrl-C to stop.")
    server.serve_forever()
