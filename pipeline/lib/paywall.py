"""付费墙/无法完整打开的信源过滤。

规则（用户定）：凡是无法完整打开的信源即无效信源。付费墙链接是死胡同，
即使内容有价值也应丢弃——同一事件通常有免费信源变体（如新浪/证券时报），
在采集端丢掉付费墙变体，事件仍能经免费变体进入管线并拿到可打开的链接。

判定两条线：
1. URL 域名命中已知付费墙域名（适用于直连 RSS 源）。
2. Google News 标题尾部 " - 来源" 或来源名命中付费墙名单（Google News 链接
   是不可靠解析的跳转，域名藏在后面，只能靠标题里的来源名判断）。
"""
from __future__ import annotations

# 硬付费墙域名（近乎全站付费，命中即丢）。
# 只列"硬墙"：几乎每篇都要付费的站，对其"能否读全"的答案可靠为否。
# 刻意不含"计费墙/多数免费"的站（MIT TR / NYT / Seeking Alpha 等）——
# 那类站误杀免费内容，且 MIT TR 是我们自己订阅接入的源。
PAYWALL_DOMAINS = {
    "caixin.com",          # 财新
    "wsj.com",             # 华尔街日报
    "ft.com",              # 金融时报
    "bloomberg.com",       # 彭博
    "theinformation.com",  # The Information
    "nikkei.com",          # 日经
    "economist.com",       # 经济学人
    "barrons.com",         # Barron's
}

# 付费墙来源名（小写匹配，用于 Google News 标题尾部 "- 来源" / sources 列表）
PAYWALL_SOURCE_NAMES = {
    "财新", "caixin",
    "华尔街日报", "wall street journal", "wsj",
    "金融时报", "financial times",
    "彭博", "bloomberg",
    "the information",
    "日经", "nikkei",
    "经济学人", "the economist",
    "barron", "巴伦",
}


def _title_source(title: str) -> str:
    """Google News 标题形如 '标题 - 来源'，取尾部来源名（小写）。"""
    if title and " - " in title:
        return title.rsplit(" - ", 1)[-1].strip().lower()
    return ""


def is_paywalled(title: str = "", url: str = "", sources: list | None = None) -> bool:
    """判定一条内容是否属于无法完整打开的付费墙信源。"""
    u = (url or "").lower()
    if any(d in u for d in PAYWALL_DOMAINS):
        return True
    src = _title_source(title)
    if src and any(p in src for p in PAYWALL_SOURCE_NAMES):
        return True
    for s in (sources or []):
        sl = str(s).strip().lower()
        if any(p in sl for p in PAYWALL_SOURCE_NAMES):
            return True
    return False
