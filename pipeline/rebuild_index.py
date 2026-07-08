#!/usr/bin/env python3
"""Rebuild data/_index.json from actual data/*.json files."""

from __future__ import annotations

from lib.common import rebuild_index, setup_logging

log = setup_logging("rebuild_index")


def main() -> None:
    path = rebuild_index()
    log.info("重建索引完成: %s", path)


if __name__ == "__main__":
    main()
