#!/usr/bin/env python3
"""
Render registries/mechanisms.yaml's declared system membership as a per-system rollup.

TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW (child 3 of
TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP). Shows what each system actually contains without
reading all 93 mechanisms individually -- the epic's own stated need -- while holding to its two
known constraints: COUNTS, never a single summary badge (`docs/plans/mechanism_tier_model_
initiative.md` §5), and every system's rate shown next to the whole-registry baseline, never in
isolation (`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION`'s own finding: a raw
per-system percentage looked informative until checked against baseline and found statistically
indistinguishable from it). See `tools/mechanism_registry/registry.py::build_system_rollup()` for
the actual counting logic; this script only loads the real registry and writes the rendering.

Usage:
  python3 tools/mechanism_registry/generate_mechanism_system_rollup_view.py               # writes the real output
  python3 tools/mechanism_registry/generate_mechanism_system_rollup_view.py --check       # exit 1 if output is stale
  python3 tools/mechanism_registry/generate_mechanism_system_rollup_view.py --output PATH # write elsewhere (tests)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REGISTRY_PATH = _REPO_ROOT / "registries" / "mechanisms.yaml"
_DEFAULT_OUTPUT = _REPO_ROOT / "docs" / "brainstorm" / "mechanism_system_rollup_view.md"

sys.path.insert(0, str(_REPO_ROOT / "tools" / "mechanism_registry"))
from registry import build_system_rollup, VALID_STATES  # noqa: E402

_STATE_ORDER = ["done", "partial", "gap", "orphan", "gated", "skeleton"]
assert set(_STATE_ORDER) == set(VALID_STATES)


def _pct(rate: float) -> str:
    return f"{rate * 100:.1f}%"


def _pt_delta(rate: float, baseline_rate: float) -> str:
    delta = (rate - baseline_rate) * 100
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.1f}pt"


def _row(label: str, stats: dict, baseline: dict) -> str:
    state_cells = " | ".join(str(stats["state_counts"][s]) for s in _STATE_ORDER)
    if stats["count"] == 0:
        # A 0-member group's "0%" is not a real rate to compare against baseline -- rendering a
        # delta here would misrepresent "no members" as "worse than baseline."
        bound_cell = "0/0 (n/a)"
        verified_cell = "0/0 (n/a)"
    else:
        bound_cell = (
            f"{stats['bound']}/{stats['count']} ({_pct(stats['bound_rate'])}, "
            f"{_pt_delta(stats['bound_rate'], baseline['bound_rate'])} vs baseline)"
        )
        verified_cell = (
            f"{stats['verified']}/{stats['count']} ({_pct(stats['verified_rate'])}, "
            f"{_pt_delta(stats['verified_rate'], baseline['verified_rate'])} vs baseline) "
            f"[{stats['runtime_verified']} runtime, {stats['static_verified']} static]"
        )
    return f"| `{label}` | {stats['count']} | {bound_cell} | {verified_cell} | {state_cells} |"


def render(data: dict) -> str:
    rollup = build_system_rollup(data)
    baseline = rollup["baseline"]

    lines = [
        "# Mechanism System Rollup View",
        "",
        "Generated from `registries/mechanisms.yaml` + `registries/system_registry.jsonl` — "
        "regenerate with `make mechanism-system-rollup-view`. Do not hand-edit.",
        "",
        "**What features the simulation actually has, and which are loose versus deep, without "
        "reading all 93 mechanisms individually** — declared system membership "
        "(`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION`), never derived from `depends_on` "
        "or any other edge.",
        "",
        "**Counts only, never a single summary status.** A badge reading \"combat: partial\" would "
        "conceal that most members are unverified — the verification axis exists so that "
        "unverified renders visibly rather than being summarised away; a badge here would rebuild "
        "that failure one tier higher.",
        "",
        "**Every rate is shown against the whole-registry baseline, never in isolation** — a raw "
        "per-system percentage looked informative in this program's own value investigation until "
        "checked against baseline and found statistically indistinguishable from it. The baseline "
        "below is computed live from the current registry, not a fixed snapshot.",
        "",
        f"**Baseline (all {baseline['count']} mechanisms)**: "
        f"{baseline['bound']} bound ({_pct(baseline['bound_rate'])}), "
        f"{baseline['verified']} verified ({_pct(baseline['verified_rate'])} — "
        f"{baseline['runtime_verified']} runtime, {baseline['static_verified']} static), "
        f"{baseline['unverified']} unverified. State breakdown: " + ", ".join(
            f"{s} {baseline['state_counts'][s]}" for s in _STATE_ORDER
        ) + ".",
        "",
        "| System | Mechanisms | Bound (vs baseline) | Verified (vs baseline) | done | partial | "
        "gap | orphan | gated | skeleton |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for row in rollup["systems"]:
        lines.append(_row(row["system"], row, baseline))

    lines.append(_row("unassigned", rollup["unassigned"], baseline))
    lines.append("")
    lines.append(
        f"`unassigned` mechanism count is {rollup['unassigned']['count']} — a mechanism with no "
        "declared system renders here explicitly rather than being silently dropped, same "
        "discipline as `mechanisms_by_system()`'s own `\"unassigned\"` key."
    )
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--registry", type=Path, default=_REGISTRY_PATH)
    parser.add_argument(
        "--check", action="store_true",
        help="Exit 1 if the output file would change, without writing it.",
    )
    args = parser.parse_args(argv)

    with open(args.registry, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    content = render(data)

    if args.check:
        existing = args.output.read_text(encoding="utf-8") if args.output.exists() else None
        if existing != content:
            print(f"STALE: {args.output} does not match the real registry -- "
                  "run `make mechanism-system-rollup-view`")
            return 1
        print(f"OK: {args.output} is up to date")
        return 0

    args.output.write_text(content, encoding="utf-8")
    n_systems = len(data.get("mechanisms", []) or [])
    print(f"Wrote {args.output} ({n_systems} mechanisms)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
