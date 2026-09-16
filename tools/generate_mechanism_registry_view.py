#!/usr/bin/env python3
"""
Render docs/brainstorm/mechanisms.yaml as a single complete markdown table: every mechanism in the
registry, priority and verification together.

TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW. Answers "what matters most, and do we know it
works" in one read -- neither existing view does both: mechanism_verification_view.md has every
mechanism but no priority; mechanism_priority_view.md has priority but only the unverified subset,
truncated at 25. This is a third view, not a replacement for either -- both stay, each still the
right answer to its own narrower question (see tools/mechanism_registry.py::all_mechanisms_combined_view's own
docstring).

This view is the first to run against a node set TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS
confirmed complete for src/domains/ and src/systems/ (75 -> 86 mechanisms; src/engine/, src/core/,
src/ai/ were out of that pass's scope). Every prior published figure computed against the old
75-mechanism set -- the 67-unverified count, the priority ranking, the 26-hub dependency count --
was computed against a node set later found to be missing 11 real mechanisms and should be treated
as superseded by whatever this view (and the other two, regenerated since) now says.

Deliberately NOT truncated -- completeness is this view's entire purpose; a truncated "complete"
view would hide foundational mechanisms again, for a new reason, after
TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION just fixed exactly that failure mode once.

Usage:
  python3 tools/generate_mechanism_registry_view.py               # writes the real output
  python3 tools/generate_mechanism_registry_view.py --check        # exit 1 if output is stale
  python3 tools/generate_mechanism_registry_view.py --output PATH  # write elsewhere (tests)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"
_DEFAULT_OUTPUT = _REPO_ROOT / "docs" / "brainstorm" / "mechanism_registry_view.md"

sys.path.insert(0, str(_REPO_ROOT / "tools"))
from mechanism_registry import all_mechanisms_combined_view  # noqa: E402


def render(data: dict) -> str:
    rows = all_mechanisms_combined_view(data)
    total = len(rows)
    runtime_count = sum(1 for r in rows if r["evidence"] == "runtime")
    static_count = sum(1 for r in rows if r["evidence"] == "static")
    unverified_count = sum(1 for r in rows if r["evidence"] == "unverified")

    lines = [
        "# Mechanism Registry View — Complete",
        "",
        "Generated from `docs/brainstorm/mechanisms.yaml` — regenerate with "
        "`make mechanism-registry-view`. Do not hand-edit.",
        "",
        f"All {total} mechanisms, one row each, sorted by priority (`layer weight × transitive "
        "dependent-count`) descending. Deliberately not truncated — see "
        "`docs/brainstorm/mechanism_priority_view.md` for the focused, unverified-only, top-25 "
        "\"verify next\" ranking, and `docs/brainstorm/mechanism_verification_view.md` for the "
        "full verification ledger with notes. This view exists to answer a third, different "
        "question: what matters most, and do we know it works, in a single read.",
        "",
        "**Node-set note**: this is the first view generated after "
        "`TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS` confirmed the registry's own node "
        "set was incomplete (75 mechanisms, atlas-only seed) and registered 11 real mechanisms "
        "the original seed never carded (now 86, for `src/domains/`/`src/systems/` — "
        "`src/engine/`/`src/core/`/`src/ai/` remain out of that pass's scope). Any earlier figure "
        "computed against the 75-mechanism set — the prior unverified count, priority ranking, or "
        "dependency-hub count — was computed against a node set later found to be missing 11 real "
        "mechanisms and should be treated as superseded by this view.",
        "",
        f"**{runtime_count} runtime-verified, {static_count} static (`code_trace`)-verified, "
        f"{unverified_count} unverified** — of {total} total.",
        "",
        "| Mechanism | Layer | State | Evidence | Verdict | Priority | Transitive Dependents |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        verdict = r["verdict"] or "unverified"
        lines.append(
            f"| `{r['id']}` | {r['layer']} | {r['state']} | {r['evidence']} | {verdict} | "
            f"{r['priority']} | {r['transitive_dependent_count']} |"
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
                  "run `make mechanism-registry-view`")
            return 1
        print(f"OK: {args.output} is up to date")
        return 0

    args.output.write_text(content, encoding="utf-8")
    n_mechanisms = len(data.get("mechanisms", []) or [])
    print(f"Wrote {args.output} ({n_mechanisms} mechanisms)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
