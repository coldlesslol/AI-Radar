"""Shared loader for config/user-config.json."""
from __future__ import annotations
import json
import pathlib

_CONFIG_PATH = pathlib.Path(__file__).parent.parent.parent / "config" / "user-config.json"


def load() -> dict:
    if _CONFIG_PATH.exists():
        try:
            return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"stocks": [], "sources": []}
