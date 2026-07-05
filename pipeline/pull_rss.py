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
from lib.user_config import load as load_user_config
from lib.paywall import is_paywalled
from lib.companies import COMPANIES, AI_MEDIA, google_news_url

log = setup_logging("rss")

MAX_AGE_DAYS = 7         # 新闻/社区默认时间窗口
ANALYSIS_MAX_AGE = 30   # 研报/Newsletter：低频发布，放宽到 30 天

# 配置表：(输出键, 输出文件, 显示名, layer, url, max_items)
FEEDS = [
    # ── 扫描层：国际 ──────────────────────────────────────────────────────────
    ("news_techmeme",    "news_techmeme.json",    "Techmeme",      "news",       "https://www.techmeme.com/feed.xml",                                    20),
    ("news_venturebeat", "news_venturebeat.json", "VentureBeat",   "news",       "https://venturebeat.com/category/ai/feed/",                           20),
    ("news_verge_ai",    "news_verge_ai.json",    "The Verge",     "news",       "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",    20),
    ("news_ars",         "news_ars.json",         "Ars Technica",  "news",       "https://arstechnica.com/ai/feed/",                                     15),
    ("news_mit_tr",      "news_mit_tr.json",      "MIT Tech Review","news",      "https://www.technologyreview.com/feed/",                               15),
    # ── 扫描层：国内 ──────────────────────────────────────────────────────────
    ("news_qbitai",      "news_qbitai.json",      "量子位",         "news",       "https://www.qbitai.com/feed",                                          20),
    # 机器之心已切换 SPA，无可用 RSS feed，暂停
    ("news_36kr",        "news_36kr.json",        "36氪",           "news",       "https://36kr.com/feed",                                                20),
    ("news_leiphone",    "news_leiphone.json",    "雷峰网",         "news",       "https://www.leiphone.com/feed",                                        20),
    ("news_tmtpost",     "news_tmtpost.json",     "钛媒体",         "news",       "https://www.tmtpost.com/feed",                                         15),
    # 极客公园：SSL 握手失败（EOF），暂停，待确认可用 RSS URL
    # ("news_geekpark", "news_geekpark.json", "极客公园", "news", "https://www.geekpark.net/rss", 15),
    # ── 社区 ─────────────────────────────────────────────────────────────────
    ("community_hn",     "community_hn.json",     "HN",            "community",  "https://hnrss.org/frontpage",                                          25),
    ("community_reddit", "community_reddit.json", "Reddit ML",     "community",  "https://www.reddit.com/r/MachineLearning/.rss",                        15),
    # ── Newsletter ───────────────────────────────────────────────────────────
    ("news_tldr_ai",     "news_tldr_ai.json",     "TLDR AI",       "newsletter", "https://tldr.tech/api/rss/ai",                                         20),
    ("news_import_ai",   "news_import_ai.json",   "Import AI",     "newsletter", "https://importai.substack.com/feed",                                   10),
    ("news_latent",      "news_latent.json",       "Latent Space",  "newsletter", "https://www.latent.space/feed",                                        10),
    ("news_semianalysis","news_semianalysis.json","SemiAnalysis",   "newsletter", "https://www.semianalysis.com/feed",                                    10),
    ("news_benedict",    "news_benedict.json",    "Benedict Evans", "newsletter", "https://www.ben-evans.com/benedictevans?format=rss",                   5),
    # The Batch：deeplearning.ai 官方 RSS URL 待确认（404），暂停
    # ("news_batch", "news_batch.json", "The Batch", "newsletter", "https://www.deeplearning.ai/the-batch/feed/", 5),
    # ── 产品发布 ─────────────────────────────────────────────────────────────
    ("news_producthunt", "news_producthunt.json", "Product Hunt",  "news",       "https://www.producthunt.com/feed?category=artificial-intelligence",    15),
    # ── 研究 ─────────────────────────────────────────────────────────────────
    ("research_arxiv",   "research_arxiv.json",   "arXiv AI",      "research",   "https://arxiv.org/rss/cs.AI",                                          20),
    # ── 企业监控 + AI 媒体：不在此硬编码，由 _registry_feeds() 从统一公司总表
    #    （lib/companies.py）动态生成，与股价/财报同一套基准。──────────────────
    # ── P3 分析机构（免费高质量 AI 研究）─────────────────────────────────────
    # ARK Invest：官方 /articles/feed/ 返回 404，暂停，待确认可用 RSS URL
    # ("analysis_ark",    "analysis_ark.json",     "ARK Invest",     "analysis",   "https://ark-invest.com/articles/feed/",                                5),
    ("analysis_inter",  "analysis_inter.json",   "Interconnects",  "analysis",   "https://www.interconnects.ai/feed",                                                            5),
    ("analysis_raschka","analysis_raschka.json", "Ahead of AI",    "analysis",   "https://magazine.sebastianraschka.com/feed",                                                   5),
    # 中文研究机构
    ("analysis_tisi",      "analysis_tisi.json",      "腾讯研究院",      "analysis",   "https://www.tisi.org/feed",                                                               8),
    # 国际战略研究机构（公开免费研报）
    ("analysis_mckinsey",  "analysis_mckinsey.json",  "McKinsey",        "analysis",   "https://www.mckinsey.com/insights/rss",                                                   10),
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
    age_days = ANALYSIS_MAX_AGE if layer in ("analysis", "newsletter") else MAX_AGE_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=age_days)
    items = []
    skipped_old = 0
    skipped_paywall = 0
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
        title = html_mod.unescape(e.get("title", "").strip())
        # 付费墙/无法完整打开的信源即无效信源，采集端丢弃（同一事件多经免费变体进入）
        if is_paywalled(title, article_url):
            skipped_paywall += 1
            continue
        items.append({
            "title": title,
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
    log.info("%s OK: %d 条（跳过 %d 过期 / %d 付费墙）", source, len(items), skipped_old, skipped_paywall)
    return len(items)


def _user_feeds() -> list[tuple]:
    """从 user-config.json 动态生成额外 feed 条目。"""
    user_cfg = load_user_config()
    feeds = []
    # 用户自定义信源
    for s in user_cfg.get("sources", []):
        sid = s.get("id") or s["name"].lower().replace(" ", "_")
        feeds.append((
            f"user_{sid}", f"user_{sid}.json",
            s["name"], s.get("category", "news"),
            s["url"], s.get("cap", 10),
        ))
    # 用户新增股票 → 自动生成 Google News RSS
    for s in user_cfg.get("stocks", []):
        name = s["name"]
        region = s.get("region", "US")
        safe_id = s.get("ticker", name).replace(".", "_").lower()
        if region == "CN":
            url = f"https://news.google.com/rss/search?q={name}+AI&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
        else:
            url = f"https://news.google.com/rss/search?q={name}+AI&hl=en-US&gl=US&ceid=US:en"
        feeds.append((f"company_user_{safe_id}", f"company_user_{safe_id}.json", name, "company", url, 6))
    return feeds


def _slug(name: str) -> str:
    return re.sub(r"[^\w]+", "_", name).strip("_").lower()


def _registry_feeds() -> list[tuple]:
    """从统一公司总表（lib/companies.py）动态生成企业监控 + AI 媒体 feed，
    确保每个投资标的都有企业新闻监控（与股价/财报同一套基准）。"""
    feeds = []
    for c in COMPANIES:
        sid = _slug(c["name"])
        url = google_news_url(c["news"], c.get("region", "US"))
        feeds.append((f"company_{sid}", f"company_{sid}.json", c["name"], "company", url, 6))
    for m in AI_MEDIA:
        sid = _slug(m["name"])
        url = google_news_url(m["news"], m.get("region", "CN"))
        feeds.append((f"media_{sid}", f"media_{sid}.json", m["name"], "media", url, 6))
    return feeds


def main() -> None:
    ok, fail = 0, 0
    all_feeds = FEEDS + _registry_feeds() + _user_feeds()
    for key, out, source, layer, url, *rest in all_feeds:
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
