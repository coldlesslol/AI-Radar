#!/usr/bin/env python3
"""HuggingFace Trending 模型。

使用 HuggingFace 公开 API，获取 trending 模型 Top 15。
无需 token。输出 data/huggingface_trending.json。
"""

from __future__ import annotations

from lib.common import get_session, retry, write_json, update_index, setup_logging, now_iso

log = setup_logging("huggingface")

MODELS_API = "https://huggingface.co/api/models"

PIPELINE_LABELS = {
    "text-generation": "文本生成",
    "text2text-generation": "文本生成",
    "question-answering": "问答",
    "image-to-text": "图文",
    "text-to-image": "文生图",
    "automatic-speech-recognition": "语音识别",
    "image-classification": "图像分类",
    "object-detection": "目标检测",
    "feature-extraction": "向量提取",
    "fill-mask": "填词",
    "zero-shot-classification": "零样本",
    "token-classification": "序列标注",
    "sentence-similarity": "文本相似",
    "video-classification": "视频分类",
    "text-to-speech": "文字转语音",
    "visual-question-answering": "视觉问答",
    "image-segmentation": "图像分割",
    "depth-estimation": "深度估计",
}


@retry
def fetch_models(limit: int = 20) -> list[dict]:
    s = get_session()
    r = s.get(
        MODELS_API,
        params={"sort": "likes7d", "direction": -1, "limit": limit},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def main() -> None:
    raw = fetch_models(20)
    log.info("获取 %d 个 trending 模型", len(raw))

    items = []
    for i, m in enumerate(raw[:15], start=1):
        model_id = m.get("modelId") or m.get("id", "")
        author, _, name = model_id.partition("/")
        if not name:
            name, author = author, ""

        pipeline_tag = m.get("pipeline_tag", "") or ""
        label = PIPELINE_LABELS.get(pipeline_tag, pipeline_tag.replace("-", " ")) if pipeline_tag else ""

        items.append({
            "rank": i,
            "model_id": model_id,
            "author": author,
            "name": name or model_id,
            "pipeline_tag": pipeline_tag,
            "pipeline_label": label,
            "likes": m.get("likes", 0),
            "downloads": m.get("downloads", 0),
            "url": f"https://huggingface.co/{model_id}",
        })

    payload = {
        "key": "huggingface_trending",
        "title": "HuggingFace Trending 模型",
        "freq": "daily",
        "updated": now_iso(),
        "url": "https://huggingface.co/models?sort=trending",
        "items": items,
    }
    write_json("huggingface_trending.json", payload)
    update_index("huggingface_trending", "huggingface_trending.json", len(items))
    log.info("huggingface_trending.json 完成：%d 模型", len(items))


if __name__ == "__main__":
    main()
