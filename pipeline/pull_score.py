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
from lib.user_config import load as load_user_config
from lib.paywall import is_paywalled
from lib.companies import all_monitor_names

log = setup_logging("score")

SCOPE = """
核心关注范围（0.70–1.0）：
- AI 模型：大模型发布/更新/排名/能力突破（LLM、多模态、代码、推理）
- AI Agent：自主 Agent、工作流自动化、MCP/工具调用、多 Agent 框架
- AI 产品：消费级/企业级 AI 产品发布、重大功能更新、用户增长数据
- 行业与商业：AI 公司融资/并购/IPO、AI 战略、监管政策、商业模式
- 算力与供应链：芯片（英伟达/AMD/国产）、算力基础设施、机器人/具身智能
- AI 落地：AI 改变具体行业（医疗/金融/制造/教育/游戏/交通）有数据支撑的报道

边缘相关（0.30–0.69，信息量决定高低）：
- AI 相关但事件影响面小的社区讨论、学术论文（无突破性）
- 科技大公司的非 AI 核心业务动态

严格低分（≤ 0.20，必须执行）：
- 与 AI 产业链无直接关联的内容，无论该媒体/信源有多权威
- 纯商业/政治/版权/法律纠纷（即使科技公司参与，若与AI无关则低分）
- 纯生活科技、消费电子、游戏（非AI驱动）
- 重复/空洞/标题党内容
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
DIGEST_MIN_SCORE = 0.45  # 低于此分值只进 archive，不进主面板

FALLBACK_SOURCE_BOOST = {
    "Techmeme": 0.08,
    "量子位": 0.08,
    "VentureBeat": 0.06,
    "The Verge": 0.05,
    "SemiAnalysis": 0.08,
    "Latent Space": 0.06,
    "Interconnects": 0.06,
    "McKinsey": 0.05,
    "腾讯研究院": 0.05,
}

# ── AI 关键词预筛（送 Claude 之前过滤明显无关内容）─────────────────────────
# 这些信源本身就是 AI 专属，所有条目直接通过，无需关键词检查
_AI_DEDICATED = {
    "TLDR AI", "Import AI", "Latent Space", "SemiAnalysis",
    "arXiv AI", "Product Hunt", "VentureBeat", "The Verge",
    "Techmeme", "Benedict Evans", "The Batch",
    # P1 企业动态（Google News 搜索已限定为 AI 公司相关）
    "智谱AI", "月之暗面", "百度AI", "字节豆包", "MiniMax",
    "Mistral", "Runway", "Cohere",
    # 微信头部 AI 媒体（无官方 RSS，走 Google News 捕获转载）
    "新智元", "机器之心",
    # P3 分析机构（专注 AI 深度分析）
    "ARK Invest", "Interconnects", "Ahead of AI",
    # 中文研究机构
    "腾讯研究院",
    # 国际战略研究机构
    "McKinsey",
}

# 运行时合并统一公司总表 + 用户自定义公司/信源名（绕过关键词预筛）
_user_cfg = load_user_config()
_AI_DEDICATED = _AI_DEDICATED | all_monitor_names() \
                               | {s["name"] for s in _user_cfg.get("stocks", [])} \
                               | {s["name"] for s in _user_cfg.get("sources", [])}
# 关键词（标题或摘要含任意一个即通过，小写匹配）
_AI_KW = {
    # 英文：技术/公司/概念
    "ai", "llm", "gpt", "claude", "gemini", "openai", "anthropic", "deepmind",
    "mistral", "meta ai", "llama", "chatgpt", "copilot", "sora", "midjourney",
    "stable diffusion", "neural", "deep learning", "machine learning",
    "transformer", "diffusion", "agi", "benchmark", "reasoning", "inference",
    "multimodal", "agent", "autonomous", "robot", "chip", "gpu", "nvidia",
    "amd", "tpu", "npu", "semiconductor", "datacenter", "compute",
    # 中文：技术/公司/概念
    "人工智能", "大模型", "语言模型", "机器学习", "深度学习", "神经网络",
    "芯片", "算力", "推理", "训练", "多模态", "智能体", "自动驾驶",
    "机器人", "具身智能", "英伟达", "英特尔", "华为昇腾",
    "百度文心", "文心一言", "阿里通义", "通义千问", "腾讯混元",
    "智谱", "kimi", "月之暗面", "商汤", "旷视", "科大讯飞",
    "字节豆包", "豆包", "零一万物", "minimax", "阶跃星辰",
    "开源模型", "闭源", "基座模型", "多智能体", "提示词",
}


def _is_ai_related(source_label: str, title: str, summary: str) -> bool:
    """AI 专属信源直接通过；其余信源要求标题或摘要含 AI 关键词。"""
    if source_label in _AI_DEDICATED:
        return True
    text = (title + " " + summary).lower()
    return any(kw in text for kw in _AI_KW)


def load_news_items() -> list[dict]:
    # 动态加载 data/ 下所有新闻/社区/研究类 JSON（非 digest/stocks/rankings/index）
    SKIP = {"digest.json", "stocks.json", "_index.json", "pinned.json", "archive.json",
            "filings.json",
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
            title   = item.get("title", "")
            summary = item.get("summary", "")
            if not _is_ai_related(label, title, summary):
                continue  # 预筛：非 AI 相关内容不送 Claude
            items.append({
                "_id":          f"{label}_{i}",
                "_source":      label,
                "title":        title,
                "url":          item.get("url", ""),
                "summary":      summary,
                "time":         item.get("time", ""),
                "published_at": item.get("published_at", ""),
                "tags":         item.get("tags", []),
            })
    log.info("过滤掉 %d 条超过 %d 天的旧条目，预筛后 %d 条 AI 相关", skipped_old, NEWS_MAX_AGE_DAYS, len(items))
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


def review_candidates(candidates: list[dict]) -> list[dict]:
    """第二轮 Claude 审核：对候选条目做 AI 相关性 + 质量把关，返回过滤后的列表。

    这是质量门（quality gate）：防止低价值/非AI内容进入主面板。
    如果 Claude 调用失败则降级返回原列表（不阻断管线）。
    """
    if not candidates:
        return candidates

    lines = []
    for item in candidates:
        text = (item.get("summary_cn") or item.get("title", ""))[:80]
        lines.append(
            f'[{item["_id"]}] {text} | {item.get("category","")} | {item.get("_source","")}'
        )

    prompt = f"""你是 AI 行业简报编辑，负责最终质量把关。

以下是已评分的候选条目，请审核并告诉我**需要删除**哪些。

删除标准（满足任意一条即删除）：
1. 与 AI 产业链无直接关联——即便来自知名媒体，若内容不涉及 AI 技术/产品/投资/芯片/机器人，必须删除
2. 质量低下：信息量为零的水文、标题党、重复炒冷饭
3. 过度重复：同一事件已有更完整的条目（保留信息更全的那条）

候选条目（格式：[ID] 摘要 | 分类 | 信源）：
{chr(10).join(lines)}

返回 JSON：{{"remove": ["id1", "id2", ...]}}
若全部保留则返回 {{"remove": []}}
不要有其他文字。"""

    try:
        log.info("第二轮审核：对 %d 条候选调用 claude -p...", len(candidates))
        raw = call_claude(prompt)
        s = raw.find("{")
        e = raw.rfind("}") + 1
        if s == -1 or e == 0:
            log.warning("review 响应格式异常，跳过过滤")
            return candidates
        result     = json.loads(raw[s:e])
        remove_ids = set(result.get("remove", []))
        kept       = [x for x in candidates if x["_id"] not in remove_ids]
        log.info("review 完成：删除 %d 条，保留 %d 条", len(remove_ids), len(kept))
        return kept
    except Exception as ex:
        log.warning("review 调用失败，跳过此步骤: %s", ex)
        return candidates  # 降级：不阻断管线


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
    # 清理付费墙历史遗留（is_paywalled 兼容旧数据）
    arch_items = [x for x in arch_items
                  if not is_paywalled(x.get("title", ""), x.get("url", ""))]

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

    write_json("archive.json", {"updated": now.isoformat(), "items": arch_items})
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
    # 清理付费墙历史遗留
    pin_items = [x for x in pin_items
                 if not is_paywalled(x.get("title", ""), x.get("url", ""))]

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
    write_json("pinned.json", {"updated": now.isoformat(), "items": pin_items})
    update_index("pinned", "pinned.json", len(pin_items))
    log.info("pinned.json: 共 %d 条（本次新增 %d 条）", len(pin_items), added)


def build_prompt(items: list[dict]) -> str:
    lines = []
    for item in items:
        text = item["title"]
        if item.get("summary"):
            text += f"（{item['summary'][:100]}）"
        lines.append(f'[{item["_id"]}|{item["_source"]}] {text}')

    return f"""你是 AI 行业情报分析师，负责为 Coldless AI Radar 筛选和整理每日情报。
以下条目来自多个中英文信源，格式：[ID|来源] 标题（摘要）

**第一步：按事件归组**
同一事件在不同信源可能以不同语言/角度出现，需识别并归为一组。
跨语言合并示例：Techmeme 英文报道某模型发布，量子位也有同一事件的中文报道 → 归一组。

**第二步：每组输出一个 JSON 对象**

字段说明：
- id: 该组代表条目的 ID（选信息最全/最权威的那条）
- sources: 覆盖该事件的所有信源列表，如 ["Techmeme", "量子位"]
- source_count: 信源数量（整数）
- relevance_score: 0.0-1.0，严格按照下方关注范围打分（不含多源加权）
- category: 从以下选一个：{CATEGORIES}
- summary_cn: 1-2 句中文摘要，直接说事，不用"该文章"开头；综合多信源信息写

评分规则（严格执行）：
{SCOPE}

⚠️ 评分纪律：与 AI 产业链无关的内容（即便来自权威媒体）必须评分 ≤ 0.20，不可因为该媒体权威就打高分。

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


def fallback_category(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()
    if any(k in text for k in ("funding", "raises", "ipo", "acquisition", "merger", "融资", "并购", "上市")):
        return "融资并购"
    if any(k in text for k in ("gpu", "chip", "semiconductor", "datacenter", "nvidia", "amd", "算力", "芯片", "光模块")):
        return "算力供应链"
    if any(k in text for k in ("paper", "research", "benchmark", "arxiv", "论文", "研究", "基准")):
        return "研究技术"
    if any(k in text for k in ("model", "llm", "gpt", "claude", "gemini", "llama", "deepseek", "qwen", "大模型", "模型")):
        return "模型发布"
    if any(k in text for k in ("agent", "workflow", "mcp", "智能体", "工作流")):
        return "AI Agent"
    if any(k in text for k in ("product", "app", "launch", "feature", "copilot", "产品", "发布", "功能")):
        return "产品动态"
    if any(k in text for k in ("hn", "reddit", "github", "社区", "开源")):
        return "社区信号"
    return "行业动态"


def fallback_score(item: dict) -> float:
    title = item.get("title", "")
    summary = item.get("summary", "")
    text = f" {title} {summary} ".lower()
    score = 0.25
    if _is_ai_related(item.get("_source", ""), title, summary):
        score = 0.55
    strong_terms = {
        "openai", "anthropic", "claude", "gemini", "deepseek", "llama", "qwen",
        "agent", "gpu", "nvidia", "funding", "ipo", "benchmark", "reasoning",
        "大模型", "智能体", "算力", "芯片", "融资", "推理", "多模态",
    }
    score += min(0.24, 0.04 * sum(1 for k in strong_terms if k in text))
    score += FALLBACK_SOURCE_BOOST.get(item.get("_source", ""), 0)
    return round(min(0.92, score), 2)


def fallback_summary_cn(item: dict) -> str:
    summary = (item.get("summary") or "").strip()
    title = (item.get("title") or "").strip()
    text = summary or title
    if not text:
        return "本条来自备用本地打分路径，原始信源未提供摘要。"
    return text[:180]


def fallback_enrich(items: list[dict]) -> list[dict]:
    """Local deterministic scorer used when claude -p is unavailable."""
    enriched = []
    seen_urls = set()
    for item in items:
        url = item.get("url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        score = fallback_score(item)
        enriched.append({
            "_id": item.get("_id", ""),
            "_source": item.get("_source", ""),
            "title": item.get("title", ""),
            "url": url,
            "time": item.get("time", ""),
            "published_at": item.get("published_at", ""),
            "sources": [item.get("_source", "")] if item.get("_source") else [],
            "source_count": 1,
            "relevance_score": score,
            "category": fallback_category(item.get("title", ""), item.get("summary", "")),
            "summary_cn": fallback_summary_cn(item),
            "fallback": True,
        })
    enriched.sort(key=lambda x: x["relevance_score"], reverse=True)
    return enriched


def main() -> None:
    items     = load_news_items()
    id_map    = {item["_id"]: item for item in items}
    log.info("加载 %d 条（共 %d 个信源）", len(items), len({x['_source'] for x in items}))

    used_fallback = False
    try:
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
    except Exception as e:
        used_fallback = True
        log.warning("claude -p 不可用，启用本地 fallback 打分: %s", e)
        enriched = fallback_enrich(items)

    enriched.sort(key=lambda x: x["relevance_score"], reverse=True)

    # 付费墙/无法完整打开的信源即无效信源，全链路剔除（digest/archive/pinned 统一入口）
    before = len(enriched)
    enriched = [e for e in enriched
                if not is_paywalled(e.get("title", ""), e.get("url", ""))]
    if before != len(enriched):
        log.info("付费墙过滤：剔除 %d 条", before - len(enriched))

    # archive + pinned 拿全量（不限流，全部历史可查）
    update_archive(enriched)
    update_pinned(enriched)

    # digest（主面板三个 Tab）：分数门槛 → 信源限流 → 质量审核
    candidates   = [x for x in enriched if x["relevance_score"] >= DIGEST_MIN_SCORE]
    capped       = apply_source_cap(candidates)
    digest_items = capped if used_fallback else review_candidates(capped)   # 第二轮 Claude 质量把关
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
            "fallback":       used_fallback,
        },
        "items": digest_items,
    }
    write_json("digest.json", payload)
    update_index("digest", "digest.json", len(digest_items))
    log.info(
        "digest.json 完成：%d 条（去重自 %d，限流前 %d，审核前 %d）| 高相关 %d / 中 %d / 低 %d | 多信源 %d",
        len(digest_items), len(items), len(candidates), len(capped), high, mid, low, multi_src,
    )


if __name__ == "__main__":
    main()
