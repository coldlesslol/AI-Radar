#!/usr/bin/env python3
"""SEC EDGAR 财报链接拉取器（P2）。

从 EDGAR submissions API 获取 10-K / 10-Q 最新归档，
写出 data/filings.json 供前端渲染直链。
不需要 API key，EDGAR 公开接口，免费使用。
"""

from __future__ import annotations

import time
from lib.common import get_session, retry, write_json, setup_logging, now_iso
from lib.user_config import load as load_user_config
from lib.companies import with_cik, tradeable

log = setup_logging("filings")

EDGAR_BASE = "https://data.sec.gov/submissions"
EDGAR_VIEWER = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form}&dateb=&owner=include&count=1&search_text="

# 美股 SEC 财报：从统一公司总表派生（有 CIK 的标的）
COMPANIES = [(c["ticker"], c["name"], c["cik"]) for c in with_cik()]

FORMS_WANTED = {"10-K", "10-Q"}


@retry
def fetch_submissions(cik: str) -> dict:
    s = get_session()
    url = f"{EDGAR_BASE}/CIK{cik}.json"
    r = s.get(url, timeout=20, headers={"User-Agent": "TechRadar/1.0 coldlesscao@gmail.com"})
    r.raise_for_status()
    return r.json()


def latest_filing(data: dict, ticker: str, company: str) -> list[dict]:
    """从 submissions 响应提取最近一份 10-K 和一份 10-Q。"""
    filings = data.get("filings", {}).get("recent", {})
    forms   = filings.get("form", [])
    dates   = filings.get("filingDate", [])
    accnos  = filings.get("accessionNumber", [])
    cik_raw = str(data.get("cik", "")).zfill(10)

    seen = set()
    results = []
    for form, date, acc in zip(forms, dates, accnos):
        if form not in FORMS_WANTED:
            continue
        if form in seen:
            continue
        seen.add(form)
        acc_clean = acc.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/full-index/{date[:4]}/QTR{_quarter(date)}/{acc_clean}-index.htm"
        results.append({
            "ticker":  ticker,
            "company": company,
            "form":    form,
            "date":    date,
            "url":     f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_raw}&type={form}&dateb=&owner=include&count=1",
        })
        if len(seen) == len(FORMS_WANTED):
            break
    return results


def _quarter(date_str: str) -> int:
    month = int(date_str[5:7])
    return (month - 1) // 3 + 1


def main() -> None:
    items = []
    user_cfg = load_user_config()
    user_companies = [(s["ticker"], s["name"], s["cik"])
                      for s in user_cfg.get("stocks", []) if s.get("cik")]
    all_companies = COMPANIES + user_companies

    for ticker, company, cik in all_companies:
        try:
            data = fetch_submissions(cik)
            filings = latest_filing(data, ticker, company)
            items.extend(filings)
            log.info("%s: 获取 %d 条财报", ticker, len(filings))
        except Exception as e:
            log.error("%s 失败: %s", ticker, e)
        time.sleep(0.5)  # EDGAR 建议 ≤10 req/s

    # A股/港股标的：无 SEC 备案，给雅虎财务报表页作为财报入口（每个标的都有财报）
    for c in tradeable():
        if c.get("cik") or c["region"] not in ("CN", "HK"):
            continue
        items.append({
            "ticker":  c["ticker"],
            "company": c["name"],
            "form":    "财务报表",
            "date":    "",
            "url":     f"https://finance.yahoo.com/quote/{c['ticker']}/financials",
        })
        log.info("%s: 财务报表页（%s）", c["ticker"], c["region"])

    payload = {
        "updated": now_iso(),
        "items":   sorted(items, key=lambda x: x["date"], reverse=True),
    }
    write_json("filings.json", payload)
    log.info("filings.json 写出 %d 条", len(items))


if __name__ == "__main__":
    main()
