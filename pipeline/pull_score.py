#!/usr/bin/env python3
"""Claude Code 打分 + 跨源去重 + 中文摘要层（走 claude -p，使用付费账号）。

逻辑：
1. 把所有条目发给 Claude，让它按"事件"归组（同一事件的多信源条目合并）
2. 每组出一条代表条目，带 sources（来源列表）和 source_count
3. source_count >= 2 的条目，relevance_score 额外加权（多源 = 更重要）
4. 按加权后的 relevance_score 降序写入 data/digest.json

输出字段（每条）：
  sources        list  覆盖该事件的信源列表，如 ["Techmeme", "HN"]
  source_count   int   信源数量
  relevance_score float 加权后相关度（0.0-1.0）
  category       str   模型发布 / 融资并购 / 产品动态 / 研究技术 / 行业动态 / 算力供应链 / 社区信号
  summary_cn     str   1-2 句中文摘要
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone, timedelta

from lib.common import DATA_DIR, now_iso, setup_logging, write_json, update_index

log = setup_logging("score")

SCOPE = """
关注范围（高分区）：
- AI 模型：大模型发布/更新/排名/能力突破（LLM、多模态、代码、推理）
- AI Agent：自主 Agent、工作流自动化、MCP/工具调用、多 Agent 框架
- AI 产品：消费级/企业级 AI 产品发布、重大功能更新、用户增长数据
- 行业与商业：AI 公司融资/并购/IPO、AI 战略、监管政策、商业模式
- 算力与供应链：芯片（英伟达/AMD/国产）、算力基础设施、机器人/具身智能、能源
- 行业+AI 应用：AI 改变具体行业（医疗/金融/制造/教育/游戏/交通等）

低分区（不删除，保留全量）：
- 与 AI 无关的科技新闻（版权纠纷、政治事件、人事变动等）
- 纯技术社区话题（数据库版本、老编程语言、硬件怀旧等）
""".strip()

CATEGORIES = "模型发布 / 融资并购 / 产品动态 / 研究技术 / 行业动态 / 算力供应链 / 社区信号"

# 每增加一个额外信源，relevance_score 加这么多（最高不超过 1.0）
MULTI_SOURCE_BOOST = 0.08
NEWS_MAX_AGE_DAYS  = 7    # 超过 7 天的条目不送 Claude 打分
PIN_THRESHOLD      = 0.88  # ≥ 此分值自动加入 pinned.json
PIN_DAYS           = 14    # 置顶条目保留天数
ARCHIVE_MAX_DAYS   = 30   # archive.json 保留最近 30 天
ARCHIVE_MAX_ITEMS  = 400  # 条目上限

# digest.json（主面板三个 Tab）的过滤规则
SOURCE_CAP       = 3     # 每个信源最多进 digest 3 条（按评分取最高的）
DIGEST_MIN_SCORE = 0.40  # 低于此分值只进 archive，不进主面板


def load_news_items() -> list[dict]:
    # 动态加载 data/ 下所有新闻/社区/研究类 JSON（非 digest/stocks/rankings/index）
    SKIP = {"digest.json", "stocks.json", "_index.json", "pinned.json", "archive.json",
            "rankings_openrouter.json", "github_trending.json", "huggingface_trending.json"}
    cutoff = datetime.now(timezone.utc) - timedelta(days=NEWS_MAX_AGE_DAYS)
    items = []
    skipped_old = 0
    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name in SKIP:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning("跳过 %s: %s", path.name, e)
            continue
        if "items" not in data:
            continue
        label = data.get("source", path.stem)
        for i, item in enumerate(data.get("items", [])):
            pub = item.get("published_at", "")
            if pub:
                try:
                    dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                    if dt < cutoff:
                        skipped_old += 1
                        continue
                except Exception:
                    pass
            items.append({
                "_id":          f"{label}_{i}",
                "_source":      label,
                "title":        item.get("title", ""),
                "url":          item.get("url", ""),
                "summary":      item.get("summary", ""),
                "time":         item.get("time", ""),
                "published_at": item.get("published_at", ""),
                "tags":         item.get("tags", []),
            })
    log.info("过滤掉 %d 条超过 %d 天的旧条目", skipped_old, NEWS_MAX_AGE_DAYS)
    return items


def apply_source_cap(enriched: list[dict]) -> list[dict]:
    """信源限流：每个信源最多保留 SOURCE_CAP 条（enriched 须已按 relevance_score 降序）。"""
    counts: dict[str, int] = {}
    selected = []
    for item in enriched:
        src = item.get("_source", "")
        if counts.get(src, 0) < SOURCE_CAP:
            selected.append(item)
            counts[src] = counts.get(src, 0) + 1
    log.info(
        "信源限流：保留 %d 条（过滤掉 %d 条低优先级）| 各源上限 %d",
        len(selected), len(enriched) - len(selected), SOURCE_CAP,
    )
    return selected


def update_archive(enriched: list[dict]) -> None:
    """把本次所有评分条目追加到 data/archive.json（30 天滚动窗口，URL 去重）。"""
    archive_path = DATA_DIR / "archive.json"
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=ARCHIVE_MAX_DAYS)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    try:
        existing = json.loads(archive_path.read_text(encoding="utf-8"))
        arch_items = existing.get("items", [])
    except Exception:
        arch_items = []

    # 剔除超过 30 天的旧条目
    arch_items = [
        x for x in arch_items
        if (x.get("published_at") or x.get("first_seen_at", ""))[:10] >= cutoff_str
    ]

    existing_urls = {x["url"] for x in arch_items}
    added = 0
    for e in enriched:
        if e.get("url") and e["url"] not in existing_urls:
            arch_items.append({
                "title":           e["title"],
                "summary_cn":      e.get("summary_cn", ""),
                "url":             e["url"],
                "sources":         e.get("sources", []),
                "source_count":    e.get("source_count", 1),
                "relevance_score": e["relevance_score"],
                "category":        e.get("category", ""),
                "published_at":    e.get("published_at", ""),
                "first_seen_at":   now.isoformat(),
            })
            existing_urls.add(e["url"])
            added += 1

    arch_items.sort(
        key=lambda x: (x.get("published_at") or x.get("first_seen_at", "")),
        reverse=True,
    )
    arch_items = arch_items[:ARCHIVE_MAX_ITEMS]

    archive_path.write_text(
        json.dumps({"updated": now.isoformat(), "items": arch_items}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    update_index("archive", "archive.json", len(arch_items))
    log.info("archive.json: 共 %d 条（本次新增 %d 条）", len(arch_items), added)


def update_pinned(enriched: list[dict]) -> None:
    """把高分条目（≥ PIN_THRESHOLD）写入 data/pinned.json，保留 PIN_DAYS 天。"""
    pinned_path = DATA_DIR / "pinned.json"
    now = datetime.now(timezone.utc)

    try:
        existing = json.loads(pinned_path.read_text(encoding="utf-8"))
        pin_items = existing.get("items", [])
    except Exception:
        pin_items = []

    # 剔除已过期
    pin_items = [
        x for x in pin_items
        if datetime.fromisoformat(x["expires_at"].replace("Z", "+00:00")) > now
    ]

    existing_urls = {x["url"] for x in pin_items}
    added = 0
    for e in enriched:
        if e.get("relevance_score", 0) >= PIN_THRESHOLD and e.get("url") and e["url"] not in existing_urls:
            pin_items.append({
                "title":           e["title"],
                "url":             e["url"],
                "summary_cn":      e.get("summary_cn", ""),
                "sources":         e.get("sources", []),
                "relevance_score": e["relevance_score"],
                "category":        e.get("category", ""),
                "pinned_at":       now.isoformat(),
                "expires_at":      (now + timedelta(days=PIN_DAYS)).isoformat(),
                "auto":            True,
            })
            existing_urls.add(e["url"])
            added += 1

    pin_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    pinned_path.write_text(
        json.dumps({"updated": now.isoformat(), "items": pin_items}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info("pinned.json: 共 %d 条（本次新增 %d 条）", len(pin_items), added)


def build_prompt(items: list[dict]) -> str:
    lines = []
    for item in items:
        text = item["title"]
        if item.get("summary"):
            text += f"（{item['summary'][:100]}）"
        lines.append(f'[{item["_id"]}|{item["_source"]}] {text}')

    return f"""你是 AI 行业情报分析师。以下是今日来自 Techmeme、量子位、HN 三个信源的新闻条目。
格式：[ID|来源] 标题（摘要）

**第一步：按事件归组**
同一事件在不同信源可能以不同语言/角度出现，需识别并归为一组。
例：Techmeme 英文报道某模型发布，HN 也有该模型的讨论帖 → 同一事件。

**第二步：每组输出一个 JSON 对象**

字段说明：
- id: 该组代表条目的 ID（选信息最全的那条）
- sources: 覆盖该事件的所有信源列表，如 ["Techmeme", "HN"]
- source_count: 信源数量（整数）
- relevance_score: 0.0-1.0，与关注范围的基础相关度（不含多源加权，那步由程序做）
- category: 从以下选一个：{CATEGORIES}
- summary_cn: 1-2 句中文摘要，直接说事，不用"该文章"开头；若跨语言合并，综合两边信息写

关注范围：
{SCOPE}

条目列表：
{chr(10).join(lines)}

返回 JSON 数组，每个事件一个对象，不要有其他文字："""


def call_claude(prompt: str) -> str:
    claude_bin = shutil.which("claude") or "/Users/coldlessmacbook/.local/bin/claude"
    result = subprocess.run(
        [claude_bin, "-p", prompt],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude -p 失败 (rc={result.returncode}):\n{result.stderr[:500]}")
    return result.stdout.strip()


def parse_groups(raw: str) -> list[dict]:
    start = raw.find("[")
    end   = raw.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"返回格式异常，找不到 JSON 数组:\n{raw[:300]}")
    return json.loads(raw[start:end])


def apply_boost(groups: list[dict]) -> list[dict]:
    """多源加权：每增加一个额外信源加 MULTI_SOURCE_BOOST，上限 1.0。"""
    for g in groups:
        base  = g.get("relevance_score", 0.5)
        extra = max(0, g.get("source_count", 1) - 1) * MULTI_SOURCE_BOOST
        g["relevance_score"] = round(min(1.0, base + extra), 2)
    return groups


def main() -> None:
    items     = load_news_items()
    id_map    = {item["_id"]: item for item in items}
    log.info("加载 %d 条（共 %d 个信源）", len(items), len({x['_source'] for x in items}))

    prompt = build_prompt(items)
    log.info("调用 claude -p 归组 + 打分...")
    raw = call_claude(prompt)
    log.info("收到响应 %d chars", len(raw))

    groups = parse_groups(raw)
    log.info("归组后 %d 个独立事件（原 %d 条）", len(groups), len(items))

    groups = apply_boost(groups)

    # 补全原始字段（title / url / time 等）从 id_map 取
    enriched = []
    for g in groups:
        base = id_map.get(g["id"], {})
        enriched.append({
            # 原始字段
            "_id":          g["id"],
            "_source":      base.get("_source", ""),
            "title":        base.get("title", ""),
            "url":          base.get("url", ""),
            "time":         base.get("time", ""),
            "published_at": base.get("published_at", ""),
            # 归组字段
            "sources":      g.get("sources", [base.get("_source", "")]),
            "source_count": g.get("source_count", 1),
            # 打分字段
            "relevance_score": g["relevance_score"],
            "category":        g.get("category", "行业动态"),
            "summary_cn":      g.get("summary_cn", base.get("summary", "")),
        })

    enriched.sort(key=lambda x: x["relevance_score"], reverse=True)

    # archive + pinned 拿全量（不限流，全部历史可查）
    update_archive(enriched)
    update_pinned(enriched)

    # digest（主面板三个 Tab）：分数门槛 + 信源限流，结果固定为当次评分
    candidates   = [x for x in enriched if x["relevance_score"] >= DIGEST_MIN_SCORE]
    digest_items = apply_source_cap(candidates)
    digest_items.sort(key=lambda x: x["relevance_score"], reverse=True)

    high      = sum(1 for x in digest_items if x["relevance_score"] >= 0.8)
    mid       = sum(1 for x in digest_items if 0.5 <= x["relevance_score"] < 0.8)
    low       = sum(1 for x in digest_items if x["relevance_score"] < 0.5)
    multi_src = sum(1 for x in digest_items if x["source_count"] >= 2)

    payload = {
        "updated":      now_iso(),
        "total":        len(digest_items),
        "deduped_from": len(items),
        "stats": {
            "high_relevance": high,
            "mid_relevance":  mid,
            "low_relevance":  low,
            "multi_source":   multi_src,
        },
        "items": digest_items,
    }
    write_json("digest.json", payload)
    update_index("digest", "digest.json", len(digest_items))
    log.info(
        "digest.json 完成：%d 条（去重自 %d，限流前 %d）| 高相关 %d / 中 %d / 低 %d | 多信源 %d",
        len(digest_items), len(items), len(candidates), high, mid, low, multi_src,
    )


if __name__ == "__main__":
    main()
