#!/usr/bin/env python3
"""Apply frontmatter to all live docs/ markdown files (excludes archive, superpowers, specs)."""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Uniform directories — all files get identical classification
# ---------------------------------------------------------------------------

UNIFORM_MAP = {
    "docs/mechanics":    dict(status="authoritative", authority="P0", layer="mechanics",    audience="developer", last_verified="2026-06-06"),
    "docs/core":         dict(status="authoritative", authority="P0", layer="core",         audience="developer", last_verified="2026-06-06"),
    "docs/architecture": dict(status="active",        authority="P1", layer="architecture", audience="developer"),
    "docs/systems":      dict(status="active",        authority="P1", layer="systems",      audience="developer"),
    "docs/strategy":     dict(status="active",        authority="P1", layer="strategy",     audience="developer"),
    "docs/compliance":   dict(status="active",        authority="P1", layer="compliance",   audience="developer"),
    "docs/ai":           dict(status="active",        authority="P1", layer="ai",           audience="developer"),
    "docs/guidelines":   dict(status="active",        authority="P1", layer="guidelines",   audience="developer"),
    "docs/testing":      dict(status="active",        authority="P1", layer="testing",      audience="developer"),
}

# ---------------------------------------------------------------------------
# Engine heuristic — historical pattern
# Matches: phase packages, milestone test matrices, replacement/legacy ledger
# docs, sweep/inventory/freeze docs, and other ephemeral build artifacts.
# ---------------------------------------------------------------------------

ENGINE_HISTORICAL_PAT = re.compile(
    r"(phase\d|phase_\d"
    r"|attach_gate"
    r"|m[0-9a-f]+_test_matrix|m[0-9a-f]+_work_model_matrix"
    r"|m[0-9a-f]+_retention_matrix|m[0-9a-f]+_degradation_matrix"
    r"|m[0-9a-f]+_replay_mode_matrix|m[0-9a-f]+_operational_controls_matrix"
    r"|m[0-9a-f]+_worker_bounds_matrix|m[0-9a-f]+_certification_matrix"
    r"|_matrix"
    r"|backlog|closure|entry_package|exit_package|proof_bundle"
    r"|readiness|ratification|baseline|freeze|gap_report|gap_audit"
    r"|inventory|scope_audit|pipeline_scope|support_boundary"
    r"|non_preserved|preserved|cutover|legacy|replacement"
    r"|unsupported|remaining|sweep|src_v2|differential"
    r"|progression_recovery|truth_package|resource_intelligence"
    r"|town_resolution|retirement_manifest|boundary_notes"
    r"|governance_reconciliation)",
    re.IGNORECASE,
)


def classify_engine(filename: str) -> dict:
    if ENGINE_HISTORICAL_PAT.search(filename):
        return dict(status="historical", authority="P2", layer="engine", audience="developer")
    return dict(status="active", authority="P1", layer="engine", audience="developer")


# ---------------------------------------------------------------------------
# Combat heuristic
# ACTIVE: m7 files and the overhaul spec
# HISTORICAL: m1–m6 rulebooks and all test matrices
# ---------------------------------------------------------------------------

def classify_combat(filename: str) -> dict:
    stem = filename.lower()
    if "m7" in stem or "overhaul_spec" in stem:
        return dict(status="active", authority="P1", layer="combat", audience="developer")
    if re.search(r"m[1-6]", stem) or "matrix" in stem:
        return dict(status="historical", authority="P2", layer="combat", audience="developer")
    return dict(status="active", authority="P1", layer="combat", audience="developer")


# ---------------------------------------------------------------------------
# Observability heuristic
# ACTIVE: named operational docs (hard_law_monitor, how_to_run_simulation,
#         loki_label_policy, prometheus_metrics)
# HISTORICAL: phase_N.md, phase_N_usage.md, phase_14_agentic_lab.md
# ---------------------------------------------------------------------------

_OBSERVABILITY_ACTIVE = {
    "hard_law_monitor",
    "how_to_run_simulation",
    "loki_label_policy",
    "prometheus_metrics",
}


def classify_observability(filename: str) -> dict:
    stem = Path(filename).stem.lower().replace("-", "_")
    if stem in _OBSERVABILITY_ACTIVE:
        return dict(status="active", authority="P1", layer="observability", audience="developer")
    return dict(status="historical", authority="P2", layer="observability", audience="developer")


# ---------------------------------------------------------------------------
# Performance heuristic
# ACTIVE: optimization_architecture, optimization_invariants, perf_baseline_policy
# HISTORICAL: date-prefixed reports (2026-05-*) and performance-report-*.md
# ---------------------------------------------------------------------------

_PERFORMANCE_ACTIVE = {
    "optimization_architecture",
    "optimization_invariants",
    "perf_baseline_policy",
}


def classify_performance(filename: str) -> dict:
    stem = Path(filename).stem.lower().replace("-", "_")
    if stem in _PERFORMANCE_ACTIVE:
        return dict(status="active", authority="P1", layer="performance", audience="developer")
    return dict(status="historical", authority="P2", layer="performance", audience="developer")


# ---------------------------------------------------------------------------
# Test coverage — all historical phase coverage reports
# ---------------------------------------------------------------------------

def classify_test_coverage(_filename: str) -> dict:
    return dict(status="historical", authority="P2", layer="testing", audience="developer")


# ---------------------------------------------------------------------------
# Heuristic directory dispatch
# ---------------------------------------------------------------------------

HEURISTIC_FNS = {
    "docs/engine":        classify_engine,
    "docs/combat":        classify_combat,
    "docs/observability": classify_observability,
    "docs/performance":   classify_performance,
    "docs/test_coverage": classify_test_coverage,
}

# ---------------------------------------------------------------------------
# Loose files at docs/ root
# ---------------------------------------------------------------------------

LOOSE_FILES = {
    "docs/README.md":                     dict(status="active", authority="P1", layer="misc",        audience="developer"),
    "docs/optimization_audit_ledger.md":  dict(status="active", authority="P1", layer="performance", audience="developer"),
}

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------


def has_frontmatter(content: str) -> bool:
    return content.startswith("---")


def build_frontmatter(fields: dict) -> str:
    lines = ["---"]
    # Emit in canonical field order; last_verified only for authoritative
    for key in ("status", "layer", "authority", "audience"):
        if key in fields:
            lines.append(f"{key}: {fields[key]}")
    if fields.get("status") == "authoritative" and "last_verified" in fields:
        lines.append(f"last_verified: {fields['last_verified']}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def get_fields(path: Path) -> dict:
    path_str = str(path)
    # Loose files take highest priority
    if path_str in LOOSE_FILES:
        return LOOSE_FILES[path_str]
    # Uniform dirs
    for prefix, fields in UNIFORM_MAP.items():
        if path_str.startswith(prefix + "/") or path_str == prefix:
            return fields
    # Heuristic dirs
    for prefix, fn in HEURISTIC_FNS.items():
        if path_str.startswith(prefix + "/") or path_str == prefix:
            return fn(path.name)
    # Fallback
    return dict(status="active", authority="P1", layer="misc", audience="developer")


def process_file(path: Path, fields: dict) -> str:
    """Read, check, and conditionally prepend frontmatter. Returns 'modified' or 'skipped'."""
    content = path.read_text(encoding="utf-8", errors="replace")
    if has_frontmatter(content):
        return "skipped"
    fm = build_frontmatter(fields)
    path.write_text(fm + "\n" + content, encoding="utf-8")
    return "modified"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    modified = 0
    skipped = 0
    processed: set[Path] = set()

    all_targets = list(UNIFORM_MAP.keys()) + list(HEURISTIC_FNS.keys())

    for target in all_targets:
        p = Path(target)
        if not p.exists():
            print(f"WARNING: {target} does not exist, skipping")
            continue
        for md in sorted(p.rglob("*.md")):
            # Never touch archive, superpowers, or specs subtrees
            parts = md.parts
            if any(x in parts for x in ("archive", "superpowers", "specs")):
                continue
            # Skip baselines/ under observability (JSON baselines, no .md expected but guard anyway)
            if "baselines" in parts:
                continue
            if md in processed:
                continue
            processed.add(md)
            fields = get_fields(md)
            result = process_file(md, fields)
            if result == "modified":
                modified += 1
            else:
                skipped += 1

    for loose_str, fields in LOOSE_FILES.items():
        lp = Path(loose_str)
        if not lp.exists():
            print(f"WARNING: {loose_str} does not exist, skipping")
            continue
        if lp in processed:
            continue
        processed.add(lp)
        result = process_file(lp, fields)
        if result == "modified":
            modified += 1
        else:
            skipped += 1

    print(f"Done: {modified} files modified, {skipped} files skipped (already had frontmatter)")


if __name__ == "__main__":
    main()
