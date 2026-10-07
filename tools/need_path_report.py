#!/usr/bin/env python3
"""Advisory SURV-06 need-path report over the world corpus (per world and kind). Never fails the build.

    python3 tools/need_path_report.py [world_id ...]
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv: list[str]) -> int:
    from src.content.repository import CatalogRepository
    from src.engine.need_paths import need_path_report
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    catalog = CatalogRepository("data/content")
    catalog.load_all()
    repo = WorldRepository("data/worlds")
    worlds = argv or sorted(os.listdir("data/worlds"))
    out = {}
    for world_id in worlds:
        try:
            spec, ctx = repo.load_world_with_context(world_id)
            state, _ = WorldCompiler.compile(spec, seed=42, context=ctx)
        except Exception as exc:  # advisory: report and continue
            out[world_id] = {"error": str(exc)[:200]}
            continue
        out[world_id] = need_path_report(state, catalog)
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
