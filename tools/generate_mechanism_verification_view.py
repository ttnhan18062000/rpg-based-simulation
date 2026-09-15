#!/usr/bin/env python3
"""
Render docs/brainstorm/mechanisms.yaml's verification axis as a plain markdown table.

TCK-20260915-MECHANISM-VERIFICATION-AXIS (child of TCK-20260915-EPIC-MECHANISM-REGISTRY, depends
on TCK-20260915-MECHANISM-REGISTRY-FOUNDATION). Scope item 3: "A verification view — rendered
section listing every mechanism with instrument, verdict, date." One row per mechanism, including
unverified ones rendered explicitly (Acceptance Criteria #1/#2) — see
tools/mechanism_registry.py::build_verification_view() for the actual row-building logic; this
script only loads the real registry and writes the rendering.

Markdown, not HTML, matches this repo's lowest-maintenance generated-doc convention (see
tools/generate_brainstorm_idea_index.py's own JSON precedent for the "generated, regenerate with
make" pattern; markdown chosen over JSON here specifically because Scope item 3 asks for a
*rendered* view a human reads directly, not a data file another tool consumes — that integration,
into the atlas/capabilities pages themselves, is TCK-20260915-ARTIFACT-STATE-CONVERGENCE's own job,
not this ticket's).

Usage:
  python3 tools/generate_mechanism_verification_view.py               # writes the real output
  python3 tools/generate_mechanism_verification_view.py --check       # exit 1 if output is stale
  python3 tools/generate_mechanism_verification_view.py --output PATH # write elsewhere (tests)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"
_DEFAULT_OUTPUT = _REPO_ROOT / "docs" / "brainstorm" / "mechanism_verification_view.md"

sys.path.insert(0, str(_REPO_ROOT / "tools"))
from mechanism_registry import build_verification_view, verification_records_from_registry  # noqa: E402


def render(data: dict) -> str:
    mechanisms = data.get("mechanisms", []) or []
    records = verification_records_from_registry(data)
    rows = build_verification_view(records, mechanisms)

    verified_count = sum(1 for r in rows if r["verified"])
    lines = [
        "# Mechanism Verification View",
        "",
        f"Generated from `docs/brainstorm/mechanisms.yaml` — regenerate with "
        f"`make mechanism-verification-view`. Do not hand-edit.",
        "",
        f"{verified_count} of {len(rows)} mechanisms have a recorded verdict. The remaining "
        f"{len(rows) - verified_count} are rendered explicitly as `unverified` below, not "
        f"omitted — a mechanism with no verdict is not the same as a mechanism known to work.",
        "",
        "**Static vs runtime evidence, grouped separately below**: `code_trace` proves what the "
        "code *says* (reachable, called, a field never written) and can never establish that "
        "reachable code has its claimed runtime effect. `census`/`scenario`/`corpus_run` prove "
        "what the simulation actually *does*. A `code_trace` row is not equivalent evidence to a "
        "runtime-confirmed row.",
        "",
        "| Mechanism | Layer | State | Evidence | Instrument | Verdict | Date | Note |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        evidence = "unverified" if not r["verified"] else (
            "runtime" if r["instrument"] in {"census", "scenario", "corpus_run"} else "static"
        )
        instrument = r["instrument"] or "—"
        date = r["date"] or "—"
        note = (r["note"] or "—").replace("\n", " ").strip()
        lines.append(
            f"| `{r['id']}` | {r['layer']} | {r['state']} | {evidence} | {instrument} | "
            f"{r['verdict']} | {date} | {note} |"
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
                  "run `make mechanism-verification-view`")
            return 1
        print(f"OK: {args.output} is up to date")
        return 0

    args.output.write_text(content, encoding="utf-8")
    n_mechanisms = len(data.get("mechanisms", []) or [])
    print(f"Wrote {args.output} ({n_mechanisms} mechanisms)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
