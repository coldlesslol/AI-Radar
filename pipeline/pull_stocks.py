#!/usr/bin/env python3
"""股票数据（yfinance）。

15 只 AI 核心标的（美 13 + A 2）+ 2 家私有公司 + 5 大盘指数。
30 天历史收盘 + 当日涨跌。输出 data/stocks.json。
"""

from __future__ import annotations

import yfinance as yf

from lib.common import write_json, update_index, setup_logging, now_iso

log = setup_logging("stocks")

# ── AI 核心标的（可交易，15 只，5 per row × 3 rows）──────────────────────────
# (ticker, 显示名, 区域, 币种)
TICKERS = [
    # US（10）
    ("NVDA",      "NVIDIA",    "US", "USD"),
    ("MSFT",      "Microsoft", "US", "USD"),
    ("GOOGL",     "Alphabet",  "US", "USD"),
    ("AMZN",      "Amazon",    "US", "USD"),
    ("META",      "Meta",      "US", "USD"),
    ("AMD",       "AMD",       "US", "USD"),
    ("AVGO",      "Broadcom",  "US", "USD"),
    ("TSLA",      "Tesla",     "US", "USD"),
    ("ARM",       "ARM",       "US", "USD"),
    ("ORCL",      "Oracle",    "US", "USD"),
    # A 股（3）
    ("688256.SS", "寒武纪",    "CN", "CNY"),
    ("300308.SZ", "中际旭创",  "CN", "CNY"),
    ("002261.SZ", "拓维信息",  "CN", "CNY"),
    # 港股（2）
    ("0020.HK",   "商汤-W",   "HK", "HKD"),
    ("9988.HK",   "阿里巴巴", "HK", "HKD"),
]

# ── 私有公司（未上市，静态信息，不拉价格）──────────────────────────────────
PRIVATE = [
    {"ticker": "SpaceX",  "name": "SpaceX",  "region": "US", "note": "私有·未上市",
     "url": "https://www.spacex.com"},
    {"ticker": "智谱AI", "name": "智谱AI", "region": "CN", "note": "私有·未上市",
     "url": "https://www.zhipuai.cn"},
]

# ── 大盘指数（5 只，单独一行）──────────────────────────────────────────────
INDEX_TICKERS = [
    ("^GSPC",     "S&P 500",  "US", "USD"),
    ("QQQ",       "QQQ",      "US", "USD"),
    ("000001.SS", "上证综指", "CN", "CNY"),
    ("000300.SS", "沪深300",  "CN", "CNY"),
    ("^HSI",      "恒生指数", "HK", "HKD"),
]


def pull_one(ticker: str, name: str, region: str, currency: str) -> dict | None:
    hist = yf.Ticker(ticker).history(period="30d")
    if hist.empty:
        log.warning("%s (%s) 无数据", name, ticker)
        return None
    closes = [round(float(c), 2) for c in hist["Close"].tolist()]
    return {
        "ticker": ticker,
        "name": name,
        "region": region,
        "currency": currency,
        "price": closes[-1],
        "history_30d": closes,
        "url": f"https://finance.yahoo.com/quote/{ticker}",
    }


def main() -> None:
    stocks, indices, errors = [], [], []

    for ticker, name, region, currency in TICKERS:
        try:
            row = pull_one(ticker, name, region, currency)
            if row:
                stocks.append(row)
                log.info("%s OK: %s %s", name, row["price"], currency)
            else:
                errors.append(ticker)
        except Exception as e:
            errors.append(ticker)
            log.error("%s (%s) 失败: %s", name, ticker, e)

    for ticker, name, region, currency in INDEX_TICKERS:
        try:
            row = pull_one(ticker, name, region, currency)
            if row:
                indices.append(row)
                log.info("[指数] %s OK: %s", name, row["price"])
            else:
                errors.append(ticker)
        except Exception as e:
            errors.append(ticker)
            log.error("[指数] %s 失败: %s", name, e)

    payload = {
        "updated": now_iso(),
        "stocks":  stocks,
        "private": PRIVATE,
        "indices": indices,
    }
    write_json("stocks.json", payload)
    status = "ok" if not errors else "partial"
    update_index("stocks", "stocks.json", len(stocks) + len(indices),
                 status=status, error=(",".join(errors) if errors else None))
    log.info("股票汇总: 标的 %d / %d, 指数 %d / %d, 失败 %s",
             len(stocks), len(TICKERS), len(indices), len(INDEX_TICKERS), errors or "无")


if __name__ == "__main__":
    main()
