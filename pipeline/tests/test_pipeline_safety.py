from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lib import common
import api_server
import pull_score

ROOT = Path(__file__).resolve().parents[2]


class IndexTests(unittest.TestCase):
    def test_update_index_prunes_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            original_data_dir = common.DATA_DIR
            try:
                common.DATA_DIR = data_dir
                (data_dir / "present.json").write_text('{"items":[{},{}]}', encoding="utf-8")
                (data_dir / "new.json").write_text('{"items":[{},{},{}]}', encoding="utf-8")
                (data_dir / "_index.json").write_text(
                    json.dumps(
                        {
                            "updated": "",
                            "files": {
                                "present": "present.json",
                                "stale": "missing.json",
                            },
                            "stats": {
                                "per_file": {
                                    "present": 2,
                                    "stale": 9,
                                },
                                "total_items": 11,
                                "last_run_status": "ok",
                                "errors": [],
                            },
                        }
                    ),
                    encoding="utf-8",
                )

                common.update_index("new", "new.json", 3)

                idx = json.loads((data_dir / "_index.json").read_text(encoding="utf-8"))
                self.assertNotIn("stale", idx["files"])
                self.assertNotIn("stale", idx["stats"]["per_file"])
                self.assertEqual(idx["stats"]["total_items"], 5)
            finally:
                common.DATA_DIR = original_data_dir


class ConfigValidationTests(unittest.TestCase):
    def test_validate_config_rejects_unexpected_fields_and_bad_urls(self) -> None:
        payload = {
            "stocks": [{"ticker": "NVDA", "name": "NVIDIA", "region": "US", "currency": "USD", "extra": "x"}],
            "sources": [{"name": "Bad", "url": "file:///tmp/bad", "category": "news", "cap": 10}],
        }

        with self.assertRaises(ValueError):
            api_server.validate_config(payload)

    def test_validate_config_normalizes_valid_payload(self) -> None:
        payload = {
            "stocks": [{"ticker": "nvda", "name": "NVIDIA", "region": "US", "currency": "USD"}],
            "sources": [{"name": "Feed", "url": "https://example.com/rss", "category": "news", "cap": "5"}],
        }

        normalized = api_server.validate_config(payload)

        self.assertEqual(normalized["stocks"][0]["ticker"], "NVDA")
        self.assertEqual(normalized["sources"][0]["id"], "feed")
        self.assertEqual(normalized["sources"][0]["cap"], 5)


class StaticSafetyTests(unittest.TestCase):
    def test_devlog_save_and_delete_handlers_are_defensive(self) -> None:
        html = (ROOT / "web" / "devlog.html").read_text(encoding="utf-8")

        self.assertIn("if (!r.ok)", html)
        self.assertIn("const removed = cfg.stocks[i]", html)
        self.assertIn("const removed = cfg.sources[i]", html)
        self.assertIn("escapeHtml", html)

    def test_daily_script_records_status_and_blocks_push_on_score_failure(self) -> None:
        script = (ROOT / "schedule" / "run_daily.sh").read_text(encoding="utf-8")

        self.assertIn("run_status.json", script)
        self.assertIn("CRITICAL_FAILED", script)
        self.assertIn("pull_score.py\" \"critical", script)


class ScoreFallbackTests(unittest.TestCase):
    def test_fallback_score_produces_digest_items_without_claude(self) -> None:
        items = [
            {
                "_id": "Techmeme_0",
                "_source": "Techmeme",
                "title": "OpenAI releases new multimodal AI model",
                "url": "https://example.com/openai",
                "summary": "The model&nbsp;improves reasoning and coding.",
                "time": "1h",
                "published_at": "2026-07-08T01:00:00+00:00",
                "tags": [],
            },
            {
                "_id": "Techmeme_1",
                "_source": "Techmeme",
                "title": "Movie studio reports box office results",
                "url": "https://example.com/movie",
                "summary": "No AI relevance.",
                "time": "1h",
                "published_at": "2026-07-08T01:00:00+00:00",
                "tags": [],
            },
        ]

        enriched = pull_score.fallback_enrich(items)

        self.assertGreaterEqual(enriched[0]["relevance_score"], 0.7)
        self.assertEqual(enriched[0]["_id"], "Techmeme_0")
        self.assertTrue(enriched[0]["fallback"])
        self.assertIn("summary_cn", enriched[0])
        self.assertNotIn("&nbsp;", enriched[0]["summary_cn"])


if __name__ == "__main__":
    unittest.main()
