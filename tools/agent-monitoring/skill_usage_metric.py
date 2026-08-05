#!/usr/bin/env python3
"""Read-only per-skill Skill-tool invocation counts, from real tools.jsonl
(TCK-20260805-SKILL-USAGE-METRIC).

Distinct from generate_retro.py's compute_retro_metrics()'s tag_breakdown_skill section, which
answers a different question (tag-driven gate-hit counts for the weekly retro). This module
answers "how many times was each skill actually invoked" — a raw per-skill count with no tag or
gate involved. generate_retro.py itself is never modified or duplicated here; its loader helpers
are imported and reused, per retrieval_baseline_metrics.py's own precedent.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_retro import DEFAULT_TOOLS_FILE, load_jsonl  # noqa: E402
from manifest import _assert_safe_output_path  # noqa: E402

# tools.jsonl's `input_summary` field is a Python-dict-repr string (e.g. "{'skill': 'graphify', ...}"),
# not JSON — confirmed by direct inspection this session. json.loads() on this field raises
# json.JSONDecodeError; regex extraction is the only correct approach.
_SKILL_NAME_RE = re.compile(r"'skill':\s*'([^']*)'")


def build_skill_usage_section(tools: list) -> dict:
    per_skill: dict = defaultdict(int)
    per_skill_per_run: dict = defaultdict(lambda: defaultdict(int))
    total = 0
    unparseable = 0

    for record in tools:
        if record.get("tool") != "Skill":
            continue
        total += 1
        # tools.jsonl records issued outside any workflow run carry run_id=None (legacy_reader.py's
        # "interactive_null" shape) — grouped under a literal "unattributed" key rather than None,
        # since a None dict key breaks json.dumps(sort_keys=True)'s key comparison against the str
        # keys of real runs (same convention as retrieval_baseline_metrics.py's search_count section).
        run_id = record.get("run_id") or "unattributed"
        match = _SKILL_NAME_RE.search(record.get("input_summary", ""))
        if match:
            skill_name = match.group(1)
            per_skill[skill_name] += 1
            per_skill_per_run[skill_name][run_id] += 1
        else:
            unparseable += 1

    return {
        "total_skill_invocations": total,
        "unparseable": unparseable,
        "per_skill": dict(per_skill),
        "per_skill_per_run": {k: dict(v) for k, v in per_skill_per_run.items()},
        "derivation": (
            "Derived from tools.jsonl's literal `tool` field, filtered to `tool == 'Skill'`, "
            "with the skill name extracted from `input_summary` via regex "
            r"(r\"'skill':\s*'([^']*)'\") — never json.loads(), since input_summary is a Python "
            "dict-repr string, not JSON. Records where the regex finds no match are counted under "
            "`unparseable`, never silently dropped. `unattributed` covers Skill invocations with "
            "no run_id (interactive, outside any workflow run). Distinct from generate_retro.py's "
            "tag_breakdown_skill aggregate — this is a raw per-skill invocation count, not a "
            "tag-driven gate-hit count."
        ),
    }


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
