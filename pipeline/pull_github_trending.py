#!/usr/bin/env python3
"""GitHub Trending AI 仓库爬取。

爬取 github.com/trending?since=daily，过滤 AI/ML 相关仓库，取 Top 15。
输出 data/github_trending.json。
"""

from __future__ import annotations
import re

from lib.common import get_session, retry, write_json, update_index, setup_logging, now_iso

log = setup_logging("github_trending")

URL = "https://github.com/trending?since=daily"

AI_KEYWORDS = {
    "llm", " ai ", "gpt", "model", "transformer", "diffusion", "agent", "rag",
    "neural", "deep learning", "machine learning", "chatbot", "embedding",
    "inference", "fine-tun", "lora", "vllm", "ollama", "stable diffusion",
    "multimodal", "vision", "nlp", "bert", "claude", "gemini", "mistral",
    "llama", "deepseek", "qwen", "mcp", "langchain", "hugging", "pytorch",
    "tensorflow", "jax", "cuda", "triton", "openai", "anthropic", "generative",
    "language model", "text-to", "image-to", "speech", "tokeniz",
}

AI_LANGUAGES = {"Jupyter Notebook", "CUDA", "MLIR"}


def is_ai(full_name: str, desc: str, lang: str | None) -> bool:
    text = f" {full_name} {desc} ".lower()
    return any(kw in text for kw in AI_KEYWORDS) or lang in AI_LANGUAGES


@retry
def fetch_html() -> str:
    s = get_session()
    r = s.get(URL, timeout=20)
    r.raise_for_status()
    return r.text


def parse(html: str) -> list[dict]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    repos = []
    for article in soup.select("article.Box-row"):
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        path = h2.get("href", "").strip("/")
        if path.count("/") != 1:
            continue

        desc_el = article.select_one("p")
        desc = desc_el.get_text(strip=True) if desc_el else ""

        lang_el = article.select_one('[itemprop="programmingLanguage"]')
        lang = lang_el.get_text(strip=True) if lang_el else None

        stars_today = 0
        for el in article.select("span.d-inline-block"):
            t = el.get_text(" ", strip=True)
            if "star" in t.lower():
                m = re.search(r"([\d,]+)", t)
                if m:
                    stars_today = int(m.group(1).replace(",", ""))

        total_stars = 0
        star_link = article.select_one('a[href$="/stargazers"]')
        if star_link:
            m = re.search(r"([\d,]+)", star_link.get_text())
            if m:
                total_stars = int(m.group(1).replace(",", ""))

        repos.append({
            "full_name": path,
            "description": desc,
            "language": lang,
            "stars": total_stars,
            "stars_today": stars_today,
            "url": f"https://github.com/{path}",
        })
    return repos


def main() -> None:
    html = fetch_html()
    all_repos = parse(html)
    log.info("获取 %d 个 trending 仓库", len(all_repos))

    ai_repos = [r for r in all_repos if is_ai(r["full_name"], r["description"], r["language"])]
    log.info("AI 相关 %d 个", len(ai_repos))

    items = []
    for i, r in enumerate(ai_repos[:15], start=1):
        items.append({**r, "rank": i})

    payload = {
        "key": "github_trending",
        "title": "GitHub Trending AI",
        "freq": "daily",
        "updated": now_iso(),
        "url": "https://github.com/trending?since=daily",
        "total_trending": len(all_repos),
        "items": items,
    }
    write_json("github_trending.json", payload)
    update_index("github_trending", "github_trending.json", len(items))
    log.info("github_trending.json 完成：%d 条", len(items))


if __name__ == "__main__":
    main()
