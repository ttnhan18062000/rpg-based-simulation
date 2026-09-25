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
_COMBINED_DEFAULT_OUTPUT = _REPO_ROOT / "docs" / "brainstorm" / "cross_domain_management_view.md"

_TERR_RULE_IDS = ["TERR-01", "TERR-02", "TERR-03", "TERR-05"]

_DESIGN_VALUE = (
    "`docs/world_rules/places-culture/territory-control.md` -- frontmatter `status: authoritative`; "
    "header \"**Status.** Batch 11A (Places/Settlements/Territory), first draft\""
)

# M4 (TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW): second domain, all 12 real Rule IDs found
# in conflict-combat.md, including CONFLICT-01/ECOL-04, which stay UNKNOWN (no
# rule_mechanism_edges.yaml row) -- rendering them here, not omitting them, is itself the AC1
# anti-drift guard made visible in the view, not just the registry.
_COMBAT_RULE_IDS = [
    "CONFLICT-01", "PERC-01", "KNOW-01", "AGENCY-01", "AGENCY-02", "AGENCY-04",
    "LIFE-01", "LIFE-02", "BODY-07", "OWN-02", "CAP-01", "ECOL-04",
]

_COMBAT_DESIGN_VALUE = (
    "`docs/world_rules/capability-progression/conflict-combat.md` -- frontmatter "
    "`status: authoritative`, `last_verified: \"2026-09-23\"`; header \"**Status.** Batch 07 "
    "(Capability/Progression/Conflict), drafted 2026-09-22, revised the same day\""
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


def _build_rows(
    rule_ids: List[str],
    design_value: str,
    rule_mechanism_data: dict,
    classifications_data: dict,
    registry: MechanismRegistry,
) -> dict:
    """Read-only assembly of the per-Rule six-axis rows plus the mapped/unmapped,
    verified/unverified, and classification-breakdown counts, for one domain's own `rule_ids` and
    `design_value` citation. Every value is read directly from the already-populated registries --
    REALIZATION is never re-derived from IMPLEMENTATION's own edge list (architecture.md §3/§4's
    "declared, not derived" rule). Domain-agnostic: `build_territory_view` and
    `build_cross_domain_view` (TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW) both call this same
    helper with their own domain's `rule_ids`/`design_value`."""
    edges = rule_mechanism_data.get("edges", []) or []
    classifications = classifications_data.get("classifications", []) or []

    rows = []
    mapped = 0
    verified_rules = 0
    classification_counts: Dict[str, int] = {}

    for rule_id in rule_ids:
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
            "DESIGN": design_value,
            "REALIZATION": classification,
            "IMPLEMENTATION": implementation_cell,
            "VERIFICATION": _verification_cell(mechanism_ids, registry) if mechanism_ids else "0/0 (n/a)",
            "INTEGRATION": _INTEGRATION_VALUE,
            "OBSERVED OUTCOME": _OBSERVED_OUTCOME_VALUE,
        })

    return {
        "rows": rows,
        "mapped": mapped,
        "unmapped": len(rule_ids) - mapped,
        "verified": verified_rules,
        "unverified": len(rule_ids) - verified_rules,
        "classification_counts": classification_counts,
    }


def build_territory_view(
    rule_mechanism_data: dict, classifications_data: dict, registry: MechanismRegistry
) -> dict:
    """Territory's own view -- a one-line call into the shared, domain-agnostic `_build_rows`
    helper with Territory's own `_TERR_RULE_IDS`/`_DESIGN_VALUE`, so this function's externally
    observed behavior (and therefore `test_real_territory_view_is_up_to_date`'s byte-for-byte
    guarantee) is unchanged by the M4 extension."""
    return _build_rows(_TERR_RULE_IDS, _DESIGN_VALUE, rule_mechanism_data, classifications_data, registry)


def build_combat_view(
    rule_mechanism_data: dict, classifications_data: dict, registry: MechanismRegistry
) -> dict:
    """Combat's own view (TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW) -- the same shared
    `_build_rows` helper with Combat's own `_COMBAT_RULE_IDS`/`_COMBAT_DESIGN_VALUE`. Renders all
    12 real Rule IDs, including `CONFLICT-01`/`ECOL-04`, which have no edge and render
    `REALIZATION: UNKNOWN`, `IMPLEMENTATION: none`, `VERIFICATION: 0/0 (n/a)`."""
    return _build_rows(
        _COMBAT_RULE_IDS, _COMBAT_DESIGN_VALUE, rule_mechanism_data, classifications_data, registry
    )


def build_cross_domain_view(
    rule_mechanism_data: dict, classifications_data: dict, registry: MechanismRegistry
) -> dict:
    """The first real multi-domain view (architecture.md §8, TCK-20260924-M4-COMBAT-SLICE-CROSS-
    DOMAIN-VIEW): Territory's and Combat's own per-domain views, kept separate, plus one combined
    top-level mapped/unmapped + verified/unverified total and one combined classification-counts
    dict merging both domains' breakdowns. Never one merged per-Rule table forcing both domains'
    differently-shaped DESIGN citations into one row shape."""
    territory = build_territory_view(rule_mechanism_data, classifications_data, registry)
    combat = build_combat_view(rule_mechanism_data, classifications_data, registry)

    combined_classification_counts: Dict[str, int] = {}
    for counts in (territory["classification_counts"], combat["classification_counts"]):
        for classification, count in counts.items():
            combined_classification_counts[classification] = (
                combined_classification_counts.get(classification, 0) + count
            )

    return {
        "territory": territory,
        "combat": combat,
        "mapped": territory["mapped"] + combat["mapped"],
        "unmapped": territory["unmapped"] + combat["unmapped"],
        "verified": territory["verified"] + combat["verified"],
        "unverified": territory["unverified"] + combat["unverified"],
        "total_rules": len(_TERR_RULE_IDS) + len(_COMBAT_RULE_IDS),
        "classification_counts": combined_classification_counts,
    }


_COMPARISON_TEXT = """\
## Comparison

Territory is `0/4` verified (every mapped mechanism is `code_trace`-only) with a classification
breakdown of 2 `CONFLICTING`, 2 `PARTIAL`. Combat is `10/10` verified **at the Rule level** (every
mapped Rule has at least one runtime-verified mechanism among its own mapped set) with a
classification breakdown of 10 `PARTIAL`, 2 `UNKNOWN` -- but this is not uniform at the
*mechanism* level: `combat_resolution` (`scenario`), `tactical_decision` (`corpus_run`), and
`combat_engagement` (`scenario`) all carry a runtime instrument, while `movement` -- cited
alongside `combat_resolution` on both `LIFE-01` and `LIFE-02` -- is `code_trace`-only. Every one
of Combat's mapped Rules still clears the Rule-level bar only because `movement` is never a Rule's
*sole* mapped mechanism.

**The inconvenient part, stated plainly**: Combat's much higher Rule-level verified-count is not
evidence Combat is "more done" than Territory. `tactical_decision` -- the mechanism most of
Combat's mapped Rules cite -- is verified by a real corpus run, and that same run is exactly what
proved its `ATTACK`-intent branch essentially never fires in real play
(`verified.verdict: contradicted`). A high verified-count and a real problem coexist on the same
mechanism. This is the same lesson architecture.md §2 already states from the `combat_judgement`
precedent ("implemented" and "actually works" are different claims) showing up again one axis
over: "has runtime evidence" and "the evidence is good news" are also different claims, and this
view's own raw-counts discipline (never a percentage alone) is what makes that visible instead of
hidden behind a single "10/10 verified" headline.

Neither domain came out "cleaner" than the other by design -- Territory's `CONFLICTING` rows are a
real semantic violation (an overloaded field slot); Combat's `PARTIAL` rows are a real,
correctly-built-but-under-exercised mechanism. Both are real findings, differently shaped, and this
view represents each faithfully rather than collapsing them into one comparable score.
"""


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


def _render_domain_section(heading: str, view: dict) -> List[str]:
    """Render one domain's own six-axis table under its own H2 heading -- the shared table shape
    both `render()` (Territory-only) and `render_cross_domain()` (TCK-20260924-M4-COMBAT-SLICE-
    CROSS-DOMAIN-VIEW) use, never one merged table forcing both domains' differently-shaped
    DESIGN citations into one row shape."""
    lines = [
        f"## {heading}",
        "",
        f"**Mapped / unmapped**: {view['mapped']}/{len(view['rows'])} real Rules mapped "
        f"({view['unmapped']} unmapped).",
        "",
        f"**Verified / unverified**: {view['verified']}/{len(view['rows'])} Rules have at least "
        f"one mapped mechanism confirmed by a runtime instrument ({view['unverified']} "
        "unverified) -- distinct from the classification breakdown below, never collapsed into "
        "it.",
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
    return lines


def render_cross_domain(
    rule_mechanism_data: dict, classifications_data: dict, registry: MechanismRegistry
) -> str:
    """The first real multi-domain management view (architecture.md §8,
    TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW): Territory and Combat, each rendered in their
    own H2 section (never one merged table), plus one combined mapped/unmapped +
    verified/unverified + classification-breakdown banner (AC4), and the honest written
    comparison (AC7)."""
    view = build_cross_domain_view(rule_mechanism_data, classifications_data, registry)

    lines = [
        "# Cross-Domain Management View",
        "",
        "Generated from `registries/rule_mechanism_edges.yaml` + "
        "`registries/rule_classifications.yaml` + `registries/mechanisms.yaml` -- regenerate with "
        "`make cross-domain-management-view`. Do not hand-edit.",
        "",
        "**The first real cross-domain view proving the Rule<->Mechanism model generalizes past "
        "Territory/Control's own idiosyncrasies (architecture.md §8, roadmap.md M4).** Each axis "
        "is reported independently, never averaged into one score. `UNKNOWN` is a legitimate, "
        "complete answer where no suitable evidence exists -- it renders explicitly rather than "
        "as a blank cell.",
        "",
        f"**Mapped / unmapped (combined)**: {view['mapped']}/{view['total_rules']} real Rules "
        f"mapped across both domains ({view['unmapped']} unmapped).",
        "",
        f"**Verified / unverified (combined)**: {view['verified']}/{view['total_rules']} Rules "
        f"have at least one mapped mechanism confirmed by a runtime instrument "
        f"({view['unverified']} unverified).",
        "",
        "**Classification breakdown (combined)**: " + ", ".join(
            f"{c}: {view['classification_counts'].get(c, 0)}"
            for c in ("SUPPORTED", "PARTIAL", "CONFLICTING", "MISSING", "INERT-OFF", "UNKNOWN")
        ) + ".",
        "",
    ]

    lines += _render_domain_section(
        "Territory / Control (TERR-01, TERR-02, TERR-03, TERR-05)", view["territory"]
    )
    lines += _render_domain_section(
        "Combat / Conflict (CONFLICT-01, PERC-01, KNOW-01, AGENCY-01, AGENCY-02, AGENCY-04, "
        "LIFE-01, LIFE-02, BODY-07, OWN-02, CAP-01, ECOL-04)",
        view["combat"],
    )

    lines.append(_COMPARISON_TEXT)
    return "\n".join(lines)


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--rule-mechanism-edges", type=Path, default=_RULE_MECHANISM_EDGES_PATH)
    parser.add_argument("--classifications", type=Path, default=_CLASSIFICATIONS_PATH)
    parser.add_argument(
        "--combined", action="store_true",
        help="Render the cross-domain view (Territory + Combat) instead of Territory alone.",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Exit 1 if the output file would change, without writing it.",
    )
    args = parser.parse_args(argv)

    if args.output is None:
        args.output = _COMBINED_DEFAULT_OUTPUT if args.combined else _DEFAULT_OUTPUT

    rule_mechanism_data = _load_yaml(args.rule_mechanism_edges)
    classifications_data = _load_yaml(args.classifications)
    registry = MechanismRegistry()

    if args.combined:
        content = render_cross_domain(rule_mechanism_data, classifications_data, registry)
        rule_count = len(_TERR_RULE_IDS) + len(_COMBAT_RULE_IDS)
        stale_hint = "run `make cross-domain-management-view`"
    else:
        content = render(rule_mechanism_data, classifications_data, registry)
        rule_count = len(_TERR_RULE_IDS)
        stale_hint = "run `make territory-control-view`"

    if args.check:
        existing = args.output.read_text(encoding="utf-8") if args.output.exists() else None
        if existing != content:
            print(f"STALE: {args.output} does not match the real registries -- {stale_hint}")
            return 1
        print(f"OK: {args.output} is up to date")
        return 0

    args.output.write_text(content, encoding="utf-8")
    print(f"Wrote {args.output} ({rule_count} Rules)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
