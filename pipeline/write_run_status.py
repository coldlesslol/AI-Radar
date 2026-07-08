#!/usr/bin/env python3
"""Write data/run_status.json from run_daily.sh step results."""

from __future__ import annotations

import sys
from pathlib import Path

from lib.common import now_iso, update_index, write_json


def _read_steps(path: Path) -> list[dict]:
    steps = []
    if not path.exists():
        return steps
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        key, script, criticality, status, rc = line.split("\t")
        steps.append({
            "key": key,
            "script": script,
            "criticality": criticality,
            "status": status,
            "return_code": int(rc),
        })
    return steps


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: write_run_status.py <status.tsv> <push_status> <critical_failed>")

    status_file = Path(sys.argv[1])
    push_status = sys.argv[2]
    critical_failed = sys.argv[3] == "1"
    steps = _read_steps(status_file)
    failed = [s for s in steps if s["status"] != "ok"]
    payload = {
        "updated": now_iso(),
        "status": "error" if critical_failed else ("partial" if failed else "ok"),
        "critical_failed": critical_failed,
        "push_status": push_status,
        "steps": steps,
        "failed_steps": failed,
    }
    write_json("run_status.json", payload)
    update_index("run_status", "run_status.json", len(steps), status=payload["status"])


if __name__ == "__main__":
    main()
