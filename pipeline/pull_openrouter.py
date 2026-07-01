#!/usr/bin/env python3
"""OpenRouter 模型使用榜单。

数据源：openrouter.ai/api/frontend/v1/rankings/models（前端 API，返回近一周
每模型每日 token 用量）。聚合整窗 token 算份额%，用首日 vs 末日排名差算升降。
输出：data/rankings_openrouter.json（schema §3.2）。
"""

from __future__ import annotations

from collections import defaultdict

from lib.common import get_session, retry, write_json, update_index, setup_logging

log = setup_logging("openrouter")

API = "https://openrouter.ai/api/frontend/v1/rankings/models"
TOP_N = 15


@retry
def fetch() -> list[dict]:
    s = get_session()
    s.headers.update({"Accept": "application/json"})
    r = s.get(API, timeout=20)
    r.raise_for_status()
    return r.json()["data"]


def prettify(permaslug: str) -> str:
    """deepseek/deepseek-v4-flash-20260423 -> DeepSeek: Deepseek V4 Flash"""
    slug = permaslug.split(":")[0]
    vendor, _, rest = slug.partition("/")
    # 去掉结尾的日期版本号 -YYYYMMDD
    parts = rest.split("-")
    if parts and parts[-1].isdigit() and len(parts[-1]) == 8:
        parts = parts[:-1]
    name = " ".join(p.capitalize() for p in parts)
    return f"{vendor.capitalize()}: {name}"


def fmt_tokens(n: int) -> str:
    """token 数转人类可读：14.2B / 386M / 1.2K（只是显示格式，不改数值口径）。"""
    for unit, base in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if n >= base:
            return f"{n / base:.1f}{unit}"
    return str(n)


def build() -> dict:
    """纯透传：用 OpenRouter 自己最新一天的 token 用量 + 它自己的排序，
    不算份额、不算周环比、不生成任何派生指标。"""
    rows = fetch()
    # 该 API 只有最新一天是稠密数据，直接取那天
    last_day = max(r["date"][:10] for r in rows)
    day_rows = [r for r in rows if r["date"][:10] == last_day]

    agg = defaultdict(int)
    for r in day_rows:
        agg[r["model_permaslug"]] += r.get("total_completion_tokens", 0) + r.get("total_prompt_tokens", 0)
    ranked = sorted(agg.items(), key=lambda x: -x[1])[:TOP_N]

    items = [
        {"rank": i, "name": prettify(slug), "value": fmt_tokens(tok)}
        for i, (slug, tok) in enumerate(ranked, start=1)
    ]
    return {
        "key": "openrouter",
        "title": "OpenRouter 模型使用榜（按 token 用量）",
        "freq": "daily",
        "updated": last_day,
        "url": "https://openrouter.ai/rankings",
        "items": items,
    }


def main() -> None:
    try:
        payload = build()
        write_json("rankings_openrouter.json", payload)
        update_index("rankings_openrouter", "rankings_openrouter.json", len(payload["items"]))
        log.info("OpenRouter OK: %d 个模型, 日期 %s", len(payload["items"]), payload["updated"])
    except Exception as e:
        log.error("OpenRouter 失败: %s", e)
        update_index("rankings_openrouter", "rankings_openrouter.json", 0,
                     status="error", error=str(e))
        raise


if __name__ == "__main__":
    main()
