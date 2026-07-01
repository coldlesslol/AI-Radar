#!/usr/bin/env python3
"""股票数据（yfinance）。

12 只 AI 相关标的：美股 8 + A 股 3 + 港股 1。
30 天历史收盘 + 当日涨跌。输出 data/stocks.json（schema §3.3）。
"""

from __future__ import annotations

import yfinance as yf

from lib.common import write_json, update_index, setup_logging, now_iso

log = setup_logging("stocks")

# (ticker, 显示名, 区域, 币种)
TICKERS = [
    ("NVDA", "NVIDIA", "US", "USD"),
    ("MSFT", "Microsoft", "US", "USD"),
    ("GOOGL", "Alphabet", "US", "USD"),
    ("AMZN", "Amazon", "US", "USD"),
    ("META", "Meta", "US", "USD"),
    ("AMD", "AMD", "US", "USD"),
    ("AVGO", "Broadcom", "US", "USD"),
    ("TSLA", "Tesla", "US", "USD"),
    ("688256.SS", "寒武纪", "CN", "CNY"),
    ("300308.SZ", "中际旭创", "CN", "CNY"),
    ("002261.SZ", "拓维信息", "CN", "CNY"),
    ("0020.HK", "商汤-W", "HK", "HKD"),
]


def pull_one(ticker: str, name: str, region: str, currency: str) -> dict | None:
    hist = yf.Ticker(ticker).history(period="30d")
    if hist.empty:
        log.warning("%s (%s) 无数据", name, ticker)
        return None
    # 只搬运：原始收盘序列 + 最新收盘价，不计算涨跌幅（折线本身即趋势）
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
    stocks, errors = [], []
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

    payload = {"updated": now_iso(), "stocks": stocks}
    write_json("stocks.json", payload)
    status = "ok" if not errors else "partial"
    update_index("stocks", "stocks.json", len(stocks),
                 status=status, error=(",".join(errors) if errors else None))
    log.info("股票汇总: 成功 %d / %d, 失败 %s", len(stocks), len(TICKERS), errors or "无")


if __name__ == "__main__":
    main()
