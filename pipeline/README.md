# TechRadar Pipeline

## Runtime

The daily pipeline is a local Python + Claude CLI job.

Required:
- Python virtualenv at `pipeline/.venv`
- Dependencies from `pipeline/requirements.txt`
- Claude CLI available on `PATH`, normally `~/.local/bin/claude`
- A working Claude CLI login/session for `claude -p`

`pull_score.py` uses `claude -p` for grouping, scoring, and Chinese summaries. Installing the Python `anthropic` package alone is not enough for scoring.

## Common Commands

```bash
pipeline/.venv/bin/python pipeline/rebuild_index.py
PYTHONPATH=pipeline pipeline/.venv/bin/python -m unittest pipeline.tests.test_pipeline_safety
bash schedule/run_daily.sh
```

## Daily Behavior

`schedule/run_daily.sh` records each step into `data/run_status.json`.

Most source failures are non-blocking because RSS and market APIs can be flaky. `pull_score.py` is critical: if scoring fails, the script skips automatic `git push` to avoid publishing mixed data where raw files are fresh but `digest.json` is stale.

`pipeline/rebuild_index.py` rebuilds `data/_index.json` from actual files on disk, so removed sources do not stay in the index forever.

## Local Config API

`pipeline/api_server.py` serves `GET/POST /api/config` on `localhost:8766` for `web/devlog.html`.

Security boundaries:
- Only configured origins are allowed by CORS.
- If `TECHRADAR_CONFIG_TOKEN` is set, POST requests must include `X-TechRadar-Token`.
- Payloads are schema-validated before writing `config/user-config.json`.

