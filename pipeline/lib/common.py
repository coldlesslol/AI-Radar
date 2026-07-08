"""TechRadar 数据管道公共库。

所有 puller 统一调用这里的 write_json / get_session / setup_logging / @retry，
保证 schema 落盘一致、网络行为一致（含代理）、日志一致、失败自动重试。
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from tenacity import (
    retry as _retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# 路径锚点：pipeline/lib/common.py -> 上两级 = 12-TechRadar/
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
LOG_DIR = ROOT / "logs"

# 加载 12-TechRadar/pipeline/.env（代理、API key 等；不入 git）
load_dotenv(ROOT / "pipeline" / ".env")

DEFAULT_TIMEOUT = 20
DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 TechRadarBot/0.1"
)


def setup_logging(name: str) -> logging.Logger:
    """控制台 + logs/pipeline.log 双写。"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:  # 防重复加 handler
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    fh = logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger


def get_session() -> requests.Session:
    """统一 session：默认 UA、超时基线，按 .env 里的 HTTP(S)_PROXY 自动走代理。

    代理来源（任一即可）：环境变量 HTTPS_PROXY / HTTP_PROXY。
    没配就直连。
    """
    s = requests.Session()
    s.headers.update({"User-Agent": DEFAULT_UA})
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    if http_proxy or https_proxy:
        s.proxies.update({"http": http_proxy, "https": https_proxy})
    return s


# 网络类失败自动重试：3 次，指数退避 2/4/8s
retry = _retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True,
)


def now_iso(tz_offset_hours: int = 8) -> str:
    """带时区的 ISO 时间戳，默认 +08:00。"""
    from datetime import timedelta

    tz = timezone(timedelta(hours=tz_offset_hours))
    return datetime.now(tz).isoformat(timespec="seconds")


def write_json(filename: str, payload: dict[str, Any]) -> Path:
    """原子写入 data/<filename>，UTF-8、不转义中文、缩进 2。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    tmp = path.with_suffix(path.suffix + ".tmp")
    # allow_nan=False：NaN/Infinity 不是合法 JSON，会让前端 JSON.parse 崩溃。
    # 宁可在此处抛错（保留旧的好数据、该步跳过），也不写出会拖垮线上的坏 JSON。
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    tmp.replace(path)  # 原子替换，避免半截文件被 artifact 读到
    return path


def payload_item_count(payload: dict[str, Any]) -> int:
    """Estimate displayable item count for a data payload."""
    total = 0
    for key in ("items", "stocks", "indices", "private"):
        value = payload.get(key)
        if isinstance(value, list):
            total += len(value)
    return total


def _prune_missing_index_entries(idx: dict[str, Any]) -> None:
    """Remove index entries whose data files no longer exist."""
    files = idx.setdefault("files", {})
    per_file = idx.setdefault("stats", {}).setdefault("per_file", {})
    stale_keys = [
        key for key, filename in files.items()
        if not (DATA_DIR / filename).exists()
    ]
    for key in stale_keys:
        files.pop(key, None)
        per_file.pop(key, None)


def rebuild_index(status: str = "ok", error: str | None = None) -> Path:
    """Rebuild data/_index.json from actual JSON files on disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    index_path = DATA_DIR / "_index.json"
    old_errors = []
    if index_path.exists():
        try:
            old_errors = json.loads(index_path.read_text(encoding="utf-8")).get("stats", {}).get("errors", [])
        except Exception:
            old_errors = []

    files: dict[str, str] = {}
    per_file: dict[str, int] = {}
    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name == "_index.json":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        key = path.stem
        files[key] = path.name
        per_file[key] = payload_item_count(payload)

    errors = list(old_errors)
    if error:
        errors.append({"file": "_index", "error": error, "at": now_iso()})

    idx = {
        "updated": now_iso(),
        "files": files,
        "stats": {
            "total_items": sum(per_file.values()),
            "last_run_status": status,
            "errors": errors,
            "per_file": per_file,
        },
    }
    return write_json("_index.json", idx)


def update_index(file_key: str, filename: str, item_count: int,
                 status: str = "ok", error: str | None = None) -> None:
    """增量更新 data/_index.json（artifact 的单一总索引）。"""
    index_path = DATA_DIR / "_index.json"
    if index_path.exists():
        idx = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        idx = {"updated": "", "files": {}, "stats": {"total_items": 0,
                "last_run_status": "ok", "errors": []}}

    idx["files"][file_key] = filename
    idx["updated"] = now_iso()
    idx.setdefault("stats", {}).setdefault("per_file", {})[file_key] = item_count
    _prune_missing_index_entries(idx)
    idx["stats"]["total_items"] = sum(idx["stats"]["per_file"].values())
    idx["stats"]["last_run_status"] = status
    errors = idx["stats"].setdefault("errors", [])
    if error:
        errors.append({"file": file_key, "error": error, "at": now_iso()})

    write_json("_index.json", idx)
