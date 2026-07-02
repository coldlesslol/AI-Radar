#!/usr/bin/env python3
"""通用 RSS 拉取器（配置驱动）。

一个脚本吃多个 RSS 源，每个源输出一份 data/<out>.json（schema §3.1）。
量子位用官方源 www.qbitai.com/feed（比公共 RSSHub 稳，已实测）。
"""

from __future__ import annotations

import html as html_mod
import re
from datetime import datetime, timezone, timedelta

import feedparser

from lib.common import get_session, retry, write_json, update_index, setup_logging, now_iso

log = setup_logging("rss")

MAX_AGE_DAYS = 7  # 超过此天数的条目直接跳过

# 配置表：(输出键, 输出文件, 显示名, layer, url, max_items)
FEEDS = [
    # ── 扫描层 ──────────────────────────────────────────────────────────────
    ("news_techmeme",    "news_techmeme.json",    "Techmeme",   "news",      "https://www.techmeme.com/feed.xml",                              30),
    ("news_qbitai",      "news_qbitai.json",      "量子位",      "news",      "https://www.qbitai.com/feed",                                    30),
    # 机器之心已切换 SPA，无可用 RSS feed，暂停
    ("news_36kr",        "news_36kr.json",        "36氪",        "news",      "https://36kr.com/feed",                                          30),
    ("news_leiphone",    "news_leiphone.json",    "雷峰网",      "news",      "https://www.leiphone.com/feed",                                  30),
    ("news_venturebeat", "news_venturebeat.json", "VentureBeat", "news",     "https://venturebeat.com/category/ai/feed/",                      30),
    ("news_verge_ai",    "news_verge_ai.json",    "The Verge",   "news",     "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", 30),
    # ── 社区 ─────────────────────────────────────────────────────────────────
    ("community_hn",     "community_hn.json",     "HN",          "community", "https://hnrss.org/frontpage",                                    30),
    ("community_reddit", "community_reddit.json", "Reddit ML",   "community", "https://www.reddit.com/r/MachineLearning/.rss",                  20),
    # ── Newsletter ───────────────────────────────────────────────────────────
    ("news_tldr_ai",     "news_tldr_ai.json",     "TLDR AI",     "newsletter","https://tldr.tech/api/rss/ai",                                   20),
    ("news_import_ai",   "news_import_ai.json",   "Import AI",   "newsletter","https://importai.substack.com/feed",                             10),
    ("news_latent",      "news_latent.json",      "Latent Space","newsletter","https://www.latent.space/feed",                                   10),
    ("news_semianalysis","news_semianalysis.json","SemiAnalysis", "newsletter","https://www.semianalysis.com/feed",                              10),
    # ── 产品发布 ─────────────────────────────────────────────────────────────
    ("news_producthunt", "news_producthunt.json", "Product Hunt","news",      "https://www.producthunt.com/feed?category=artificial-intelligence", 20),
    # ── 研究 ─────────────────────────────────────────────────────────────────
    ("research_arxiv",   "research_arxiv.json",   "arXiv AI",    "research",  "https://arxiv.org/rss/cs.AI",                                    20),
]

DEFAULT_MAX = 30
_TAG_RE  = re.compile(r"<[^>]+>")
_HREF_RE = re.compile(r'<a\s[^>]*href=["\']([^"\']+)["\']', re.IGNORECASE)


def strip_html(text: str, limit: int = 200) -> str:
    text = _TAG_RE.sub("", text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text[:limit]


def techmeme_source_url(entry) -> str:
    """从 Techmeme RSS summary 里提取原始文章 URL（第一个 <a href>）。"""
    summary = entry.get("summary", "") or entry.get("content", [{}])[0].get("value", "")
    m = _HREF_RE.search(summary)
    if m:
        url = m.group(1)
        if not url.startswith("https://www.techmeme.com"):
            return url
    return entry.get("link", "")


def rel_time(parsed) -> str:
    """published_parsed -> 相对时间 '2h' / '3d'。"""
    if not parsed:
        return ""
    dt = datetime(*parsed[:6], tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    secs = max(delta.total_seconds(), 0)
    if secs < 3600:
        return f"{int(secs // 60)}m"
    if secs < 86400:
        return f"{int(secs // 3600)}h"
    return f"{int(secs // 86400)}d"


def iso_time(parsed) -> str:
    if not parsed:
        return ""
    return datetime(*parsed[:6], tzinfo=timezone.utc).isoformat()


@retry
def fetch_raw(url: str) -> bytes:
    s = get_session()
    r = s.get(url, timeout=20)
    r.raise_for_status()
    return r.content


def pull_one(key: str, out: str, source: str, layer: str, url: str, max_items: int = DEFAULT_MAX) -> int:
    raw = fetch_raw(url)
    feed = feedparser.parse(raw)
    is_techmeme = "techmeme.com" in url
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    items = []
    skipped_old = 0
    for e in feed.entries[:max_items * 3]:  # 多取一些，补上被过滤掉的
        if len(items) >= max_items:
            break
        parsed = e.get("published_parsed") or e.get("updated_parsed")
        if parsed:
            dt = datetime(*parsed[:6], tzinfo=timezone.utc)
            if dt < cutoff:
                skipped_old += 1
                continue
        article_url = techmeme_source_url(e) if is_techmeme else e.get("link", "")
        items.append({
            "title": html_mod.unescape(e.get("title", "").strip()),
            "url": article_url,
            "summary": strip_html(e.get("summary", "")),
            "source": source,
            "time": rel_time(parsed),
            "tags": [],
            "published_at": iso_time(parsed),
        })
    payload = {
        "source": source,
        "layer": layer,
        "updated": now_iso(),
        "items": items,
    }
    write_json(out, payload)
    update_index(key, out, len(items))
    log.info("%s OK: %d 条（跳过 %d 条过期）", source, len(items), skipped_old)
    return len(items)


def main() -> None:
    ok, fail = 0, 0
    for key, out, source, layer, url, *rest in FEEDS:
        max_items = rest[0] if rest else DEFAULT_MAX
        try:
            pull_one(key, out, source, layer, url, max_items)
            ok += 1
        except Exception as e:
            fail += 1
            log.error("%s 失败: %s", source, e)
            update_index(key, out, 0, status="error", error=str(e))
    log.info("RSS 汇总: 成功 %d, 失败 %d", ok, fail)


if __name__ == "__main__":
    main()
