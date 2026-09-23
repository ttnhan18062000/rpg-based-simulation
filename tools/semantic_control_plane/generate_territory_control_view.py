#!/usr/bin/env python3
"""
Render the Territory/Control Rules (TERR-01, TERR-02, TERR-03, TERR-05) against
docs/plans/simulation_semantic_control_plane/architecture.md §8's six management-view axes:
DESIGN, REALIZATION, IMPLEMENTATION, VERIFICATION, INTEGRATION, OBSERVED OUTCOME.

TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE. Mirrors
tools/mechanism_registry/generate_mechanism_system_rollup_view.py's own conventions exactly: a
"Generated from ... -- regenerate with `make ...`. Do not hand-edit." banner, counts never a
single collapsed badge, and `--output`/`--check` CLI flags. Reads
registries/rule_mechanism_edges.yaml + registries/rule_classifications.yaml (via
tools.semantic_control_plane.registry, imported not reimplemented) and registries/mechanisms.yaml
(via tools.mechanism_registry.registry.MechanismRegistry, imported not reimplemented).

Each axis is reported independently, never averaged into one score (architecture.md §8). UNKNOWN
is a legitimate, complete answer where no suitable evidence exists -- it renders explicitly rather
than as a blank cell.

Usage:
  python3 tools/semantic_control_plane/generate_territory_control_view.py               # writes the real output
  python3 tools/semantic_control_plane/generate_territory_control_view.py --check       # exit 1 if output is stale
  python3 tools/semantic_control_plane/generate_territory_control_view.py --output PATH # write elsewhere (tests)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.mechanism_registry.registry import MechanismRegistry, RUNTIME_INSTRUMENTS  # noqa: E402

_RULE_MECHANISM_EDGES_PATH = _REPO_ROOT / "registries" / "rule_mechanism_edges.yaml"
_CLASSIFICATIONS_PATH = _REPO_ROOT / "registries" / "rule_classifications.yaml"
_DEFAULT_OUTPUT = _REPO_ROOT / "docs" / "brainstorm" / "territory_control_management_view.md"

_TERR_RULE_IDS = ["TERR-01", "TERR-02", "TERR-03", "TERR-05"]

_DESIGN_VALUE = (
    "`docs/world_rules/places-culture/territory-control.md` -- frontmatter `status: authoritative`; "
    "header \"**Status.** Batch 11A (Places/Settlements/Territory), first draft\""
)

_SIX_AXES = [
    "DESIGN", "REALIZATION", "IMPLEMENTATION", "VERIFICATION", "INTEGRATION", "OBSERVED OUTCOME",
]

_INTEGRATION_VALUE = (
    "UNKNOWN -- no `registries/mechanism_causal_edges.yaml` row exists among this Rule's mapped "
    "mechanisms; see the schema-friction note in that file's own header"
)
_OBSERVED_OUTCOME_VALUE = "UNKNOWN -- no runtime evidence currently exists"


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _edges_for_rule(rule_id: str, edges: List[dict]) -> List[dict]:
    return [e for e in edges if e.get("rule_id") == rule_id]


def _classification_for_rule(rule_id: str, classifications: List[dict]) -> str:
    for record in classifications:
        if record.get("rule_id") == rule_id:
            return record["classification"]
    return "UNKNOWN"


def _verification_cell(mechanism_ids: List[str], registry: MechanismRegistry) -> str:
    total = len(mechanism_ids)
    runtime_count = 0
    for mid in mechanism_ids:
        verification = registry.get_verification(mid)
        if verification and verification.get("instrument") in RUNTIME_INSTRUMENTS:
            runtime_count += 1
    code_trace_count = total - runtime_count
    return f"{code_trace_count}/{total} code_trace, {runtime_count}/{total} runtime"


def build_territory_view(
    rule_mechanism_data: dict, classifications_data: dict, registry: MechanismRegistry
) -> dict:
    """Read-only assembly of the per-Rule six-axis rows plus the mapped/unmapped,
    verified/unverified, and classification-breakdown counts. Every value is read directly from
    the already-populated registries -- REALIZATION is never re-derived from IMPLEMENTATION's own
    edge list (architecture.md §3/§4's "declared, not derived" rule)."""
    edges = rule_mechanism_data.get("edges", []) or []
    classifications = classifications_data.get("classifications", []) or []

    rows = []
    mapped = 0
    verified_rules = 0
    classification_counts: Dict[str, int] = {}

    for rule_id in _TERR_RULE_IDS:
        rule_edges = _edges_for_rule(rule_id, edges)
        mechanism_ids = sorted({e["mechanism_id"] for e in rule_edges})
        classification = _classification_for_rule(rule_id, classifications)
        classification_counts[classification] = classification_counts.get(classification, 0) + 1

        if mechanism_ids:
            mapped += 1

        has_runtime_verification = any(
            (registry.get_verification(mid) or {}).get("instrument") in RUNTIME_INSTRUMENTS
            for mid in mechanism_ids
        )
        if has_runtime_verification:
            verified_rules += 1

        implementation_cell = ", ".join(
            f"`{mid}` ({e['edge_type']})"
            for mid, e in sorted(
                {e["mechanism_id"]: e for e in rule_edges}.items()
            )
        ) or "none"

        rows.append({
            "rule_id": rule_id,
            "DESIGN": _DESIGN_VALUE,
            "REALIZATION": classification,
            "IMPLEMENTATION": implementation_cell,
            "VERIFICATION": _verification_cell(mechanism_ids, registry) if mechanism_ids else "0/0 (n/a)",
            "INTEGRATION": _INTEGRATION_VALUE,
            "OBSERVED OUTCOME": _OBSERVED_OUTCOME_VALUE,
        })

    return {
        "rows": rows,
        "mapped": mapped,
        "unmapped": len(_TERR_RULE_IDS) - mapped,
        "verified": verified_rules,
        "unverified": len(_TERR_RULE_IDS) - verified_rules,
        "classification_counts": classification_counts,
    }


def render(rule_mechanism_data: dict, classifications_data: dict, registry: MechanismRegistry) -> str:
    view = build_territory_view(rule_mechanism_data, classifications_data, registry)

    lines = [
        "# Territory Control Management View",
        "",
        "Generated from `registries/rule_mechanism_edges.yaml` + "
        "`registries/rule_classifications.yaml` + `registries/mechanisms.yaml` -- regenerate with "
        "`make territory-control-view`. Do not hand-edit.",
        "",
        "**Territory/Control Rules (TERR-01, TERR-02, TERR-03, TERR-05) rendered across "
        "architecture.md §8's six management-view axes.** Each axis is reported independently, "
        "never averaged into one score. `UNKNOWN` is a legitimate, complete answer where no "
        "suitable evidence exists -- it renders explicitly rather than as a blank cell.",
        "",
        f"**Mapped / unmapped**: {view['mapped']}/{len(_TERR_RULE_IDS)} real TERR Rules mapped "
        f"({view['unmapped']} unmapped). TERR-04 is excluded -- it is a stale citation, not a "
        "real Rule ID (see the ticket's own Findings).",
        "",
        f"**Verified / unverified**: {view['verified']}/{len(_TERR_RULE_IDS)} Rules have at "
        f"least one mapped mechanism confirmed by a runtime instrument "
        f"({view['unverified']} unverified) -- distinct from the classification breakdown below, "
        "never collapsed into it.",
        "",
        "**Classification breakdown**: " + ", ".join(
            f"{c}: {view['classification_counts'].get(c, 0)}"
            for c in ("SUPPORTED", "PARTIAL", "CONFLICTING", "MISSING", "INERT-OFF", "UNKNOWN")
        ) + ".",
        "",
        "| Rule | " + " | ".join(_SIX_AXES) + " |",
        "|---|" + "---|" * len(_SIX_AXES),
    ]

    for row in view["rows"]:
        lines.append(
            f"| `{row['rule_id']}` | " + " | ".join(row[axis] for axis in _SIX_AXES) + " |"
        )

    lines.append("")
    return "\n".join(lines)


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--rule-mechanism-edges", type=Path, default=_RULE_MECHANISM_EDGES_PATH)
    parser.add_argument("--classifications", type=Path, default=_CLASSIFICATIONS_PATH)
    parser.add_argument(
        "--check", action="store_true",
        help="Exit 1 if the output file would change, without writing it.",
    )
    args = parser.parse_args(argv)

    rule_mechanism_data = _load_yaml(args.rule_mechanism_edges)
    classifications_data = _load_yaml(args.classifications)
    registry = MechanismRegistry()

    content = render(rule_mechanism_data, classifications_data, registry)

    if args.check:
        existing = args.output.read_text(encoding="utf-8") if args.output.exists() else None
        if existing != content:
            print(f"STALE: {args.output} does not match the real registries -- "
                  "run `make territory-control-view`")
            return 1
        print(f"OK: {args.output} is up to date")
        return 0

    args.output.write_text(content, encoding="utf-8")
    print(f"Wrote {args.output} ({len(_TERR_RULE_IDS)} Rules)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
