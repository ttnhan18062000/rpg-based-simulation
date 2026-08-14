#!/usr/bin/env python3
"""Read-only per-skill Skill-tool invocation counts, from real tools.jsonl
(TCK-20260805-SKILL-USAGE-METRIC).

Distinct from generate_retro.py's compute_retro_metrics()'s tag_breakdown_skill section, which
answers a different question (tag-driven gate-hit counts for the weekly retro). This module
answers "how many times was each skill actually invoked" — a raw per-skill count with no tag or
gate involved.

build_skill_usage_section is now defined in generate_retro.py (relocated by
TCK-20260810-SKILL-USAGE-RETRO-TRACKING to resolve a circular-import constraint: this module
already imports DEFAULT_TOOLS_FILE/load_jsonl FROM generate_retro.py, so generate_retro.py could
not import build_skill_usage_section back from here without creating a two-file cycle) and
re-imported here so this module's CLI stays byte-identical. generate_retro.py itself is never
modified or duplicated here; its loader helpers are imported and reused, per
retrieval_baseline_metrics.py's own precedent.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_retro import DEFAULT_TOOLS_FILE, build_skill_usage_section, load_jsonl  # noqa: E402
from manifest import _assert_safe_output_path  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None, help="optional path to also write the JSON output to")
    args = parser.parse_args()

    tools = load_jsonl(DEFAULT_TOOLS_FILE)
    report = build_skill_usage_section(tools)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"

    if args.output is not None:
        _assert_safe_output_path(args.output)
        args.output.write_text(output)

    sys.stdout.write(output)


if __name__ == "__main__":
    main()
