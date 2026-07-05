"""统一公司总表 —— 投资标的、财报、企业新闻监控的单一基准。

原则（用户定，2026-07-05）：投资标的 = 财报链接 = 企业信源监控名单，
三者同一套；在标的基础上再补充"关注·未持仓"的其他企业。

每条字段：
  name      显示名
  ticker    有则拉股价（yfinance）；无则不进股价面板
  region    US / CN / HK —— 决定新闻 locale、财报回退方式
  currency  股价币种
  cik       有则拉 SEC 财报（美股）；CN/HK 无 CIK，财报回退到交易所/雅虎财务页
  news      Google News 监控搜索词（locale 由 region 决定）
  target    True=投资标的（带股价/财报）；False=关注·未持仓（只做新闻监控）

AI_MEDIA 是"媒体"不是公司（无股价无财报），单列，不混进企业信源。
"""
from __future__ import annotations

COMPANIES: list[dict] = [
    # ── 投资标的 · 美股（11）──────────────────────────────────────────────
    {"name": "NVIDIA",    "ticker": "NVDA",  "region": "US", "currency": "USD", "cik": "0001045810", "news": "NVIDIA AI GPU",        "target": True},
    {"name": "Microsoft", "ticker": "MSFT",  "region": "US", "currency": "USD", "cik": "0000789019", "news": "Microsoft AI Copilot", "target": True},
    {"name": "Alphabet",  "ticker": "GOOGL", "region": "US", "currency": "USD", "cik": "0001652044", "news": "Google Gemini AI",      "target": True},
    {"name": "Amazon",    "ticker": "AMZN",  "region": "US", "currency": "USD", "cik": "0001018724", "news": "Amazon AWS Bedrock AI", "target": True},
    {"name": "Meta",      "ticker": "META",  "region": "US", "currency": "USD", "cik": "0001326801", "news": "Meta AI Llama",         "target": True},
    {"name": "AMD",       "ticker": "AMD",   "region": "US", "currency": "USD", "cik": "0000002488", "news": "AMD AI GPU MI300",      "target": True},
    {"name": "Broadcom",  "ticker": "AVGO",  "region": "US", "currency": "USD", "cik": "0001730168", "news": "Broadcom AI chip",      "target": True},
    {"name": "Tesla",     "ticker": "TSLA",  "region": "US", "currency": "USD", "cik": "0001318605", "news": "Tesla AI FSD robot",    "target": True},
    {"name": "ARM",       "ticker": "ARM",   "region": "US", "currency": "USD", "cik": "0001973239", "news": "Arm AI chip",           "target": True},
    {"name": "Oracle",    "ticker": "ORCL",  "region": "US", "currency": "USD", "cik": "0001341439", "news": "Oracle AI cloud",       "target": True},
    {"name": "SpaceX",    "ticker": "SPCX",  "region": "US", "currency": "USD", "cik": None,         "news": "SpaceX Starlink",       "target": True},
    # ── 投资标的 · A 股（3）──────────────────────────────────────────────
    {"name": "寒武纪",    "ticker": "688256.SS", "region": "CN", "currency": "CNY", "cik": None, "news": "寒武纪 AI芯片",       "target": True},
    {"name": "中际旭创",  "ticker": "300308.SZ", "region": "CN", "currency": "CNY", "cik": None, "news": "中际旭创 光模块 AI",  "target": True},
    {"name": "拓维信息",  "ticker": "002261.SZ", "region": "CN", "currency": "CNY", "cik": None, "news": "拓维信息 昇腾 AI",    "target": True},
    # ── 投资标的 · 港股（5）──────────────────────────────────────────────
    {"name": "商汤",      "ticker": "0020.HK", "region": "HK", "currency": "HKD", "cik": None, "news": "商汤科技 AI 大模型",  "target": True},
    {"name": "阿里巴巴",  "ticker": "9988.HK", "region": "HK", "currency": "HKD", "cik": None, "news": "阿里巴巴 通义 AI",    "target": True},
    {"name": "腾讯",      "ticker": "0700.HK", "region": "HK", "currency": "HKD", "cik": None, "news": "腾讯 混元 AI",        "target": True},
    {"name": "智谱AI",    "ticker": "2513.HK", "region": "HK", "currency": "HKD", "cik": None, "news": "智谱AI GLM",          "target": True},
    {"name": "MiniMax",   "ticker": "0100.HK", "region": "HK", "currency": "HKD", "cik": None, "news": "MiniMax AI 海螺",     "target": True},

    # ── 关注 · 未持仓（只做新闻监控，无股价/财报）──────────────────────────
    {"name": "月之暗面",  "region": "CN", "news": "月之暗面 Kimi",          "target": False},
    {"name": "百度AI",    "region": "CN", "news": "百度 文心 ERNIE Bot",    "target": False},
    {"name": "字节豆包",  "region": "CN", "news": "字节跳动 豆包 AI",       "target": False},
    {"name": "DeepSeek",  "region": "CN", "news": "DeepSeek 深度求索",      "target": False},
    {"name": "Mistral",   "region": "US", "news": "Mistral AI model",       "target": False},
    {"name": "Runway",    "region": "US", "news": "Runway AI video",        "target": False},
    {"name": "Cohere",    "region": "US", "news": "Cohere AI enterprise",   "target": False},
]

# AI 媒体（媒体，非公司 —— 无股价/财报，走 Google News 捕获转载）
AI_MEDIA: list[dict] = [
    {"name": "新智元",   "region": "CN", "news": "新智元 AI"},
    {"name": "机器之心", "region": "CN", "news": "机器之心 AI"},
]


def google_news_url(query: str, region: str) -> str:
    """按区域生成 Google News RSS 搜索 URL。"""
    q = query.replace(" ", "+")
    if region == "CN" or region == "HK":
        return f"https://news.google.com/rss/search?q={q}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def all_monitor_names() -> set[str]:
    """所有企业 + AI 媒体的显示名（供打分层绕过关键词预筛）。"""
    return {c["name"] for c in COMPANIES} | {m["name"] for m in AI_MEDIA}


def tradeable() -> list[dict]:
    """有 ticker 的标的（拉股价）。"""
    return [c for c in COMPANIES if c.get("ticker")]


def with_cik() -> list[dict]:
    """有 SEC CIK 的标的（拉 10-K/10-Q）。"""
    return [c for c in COMPANIES if c.get("cik")]
