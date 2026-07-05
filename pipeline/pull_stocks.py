#!/usr/bin/env python3
"""股票数据（yfinance）。

15 只 AI 核心标的（美 13 + A 2）+ 2 家私有公司 + 5 大盘指数。
30 天历史收盘 + 当日涨跌。输出 data/stocks.json。
"""

from __future__ import annotations

import time

import yfinance as yf

from lib.common import write_json, update_index, setup_logging, now_iso
from lib.user_config import load as load_user_config
from lib.companies import tradeable

log = setup_logging("stocks")

# ── AI 核心标的：从统一公司总表（lib/companies.py）派生，与财报/新闻同一套 ──
TICKERS = [(c["ticker"], c["name"], c["region"], c["currency"]) for c in tradeable()]

PRIVATE: list[dict] = []

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
    # 剔除 NaN：yfinance 偶返 NaN 收盘（休市/数据缺口），NaN 不是合法 JSON，
    # 会让前端 JSON.parse 崩溃、整个股票面板挂掉（2026-07-05 沪深300 踩此坑）。
    closes = [round(float(c), 2) for c in hist["Close"].tolist() if c == c]
    if not closes:
        log.warning("%s (%s) 收盘价全为 NaN，跳过", name, ticker)
        return None
    return {
        "ticker": ticker,
        "name": name,
        "region": region,
        "currency": currency,
        "price": closes[-1],
        "history_30d": closes,
        "url": f"https://finance.yahoo.com/quote/{ticker}",
    }


def pull_batch(tickers: list, label: str) -> tuple[list, list]:
    """拉一组标的，失败的重试最多 3 轮（yfinance 偶发限流/瞬时失败，
    否则每天都会随机少一两只）。返回 (成功行, 失败 ticker)。"""
    rows, pending = [], list(tickers)
    for attempt in range(3):
        still = []
        for ticker, name, region, currency in pending:
            try:
                row = pull_one(ticker, name, region, currency)
                if row:
                    rows.append(row)
                    log.info("%s%s OK: %s %s", label, name, row["price"], currency)
                else:
                    still.append((ticker, name, region, currency))
            except Exception as e:
                still.append((ticker, name, region, currency))
                log.warning("%s%s (%s) 第%d次失败: %s", label, name, ticker, attempt + 1, e)
        pending = still
        if not pending:
            break
        if attempt < 2:
            log.info("%s重试 %d 只失败标的...", label, len(pending))
            time.sleep(3)
    return rows, [t[0] for t in pending]


def main() -> None:
    user_cfg = load_user_config()
    user_tickers = [(s["ticker"], s["name"], s["region"], s["currency"])
                    for s in user_cfg.get("stocks", []) if s.get("ticker")]
    all_tickers = TICKERS + user_tickers

    stocks, err_s = pull_batch(all_tickers, "")
    indices, err_i = pull_batch(INDEX_TICKERS, "[指数] ")
    errors = err_s + err_i

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
