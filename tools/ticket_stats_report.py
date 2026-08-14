#!/usr/bin/env python3
"""
Export a ticket-corpus statistics report over completed tickets (tickets/done/).

Built for TCK-20260718-TICKET-CORPUS-REPORT, closing four pillars docs/guides/ticket_reporting.md
named as known-wanted but never scoped ("Other candidate pillars (not built)"): ticket
velocity/throughput, tier/type/priority distribution, layer distribution, artifact completeness.
Mirrors tools/tag_report.py's exact shape (computation/rendering split, --json flag, dedicated
test file, `make` target) — that module is the direct precedent, read it first if this one is
unclear.

Scoped to tickets/done/ only, matching tag_report.py's own scope choice — velocity/distribution
over *completed* work is the natural reading of "reporting," and this keeps the scope convention
consistent with its precedent rather than inventing a new one.

Reuses (never reimplements):
- tools/validate_frontmatter.py::extract_frontmatter for ticket frontmatter (layer).
- tools/generate_registry.py::parse_body_section/_strip_frontmatter for body-section fields
  (tier, ticket_type, priority) — docs/REGISTRY.yaml is NOT a sufficient data source alone (its
  ticket entries have no layer, no priority, no body status — confirmed directly), so this tool
  parses ticket files the same way tools/ticket_field_values.py/ingest.py already do.
- tools/ticket_field_values.py's TIER_VALUES/PRIORITY_VALUES for canonical cross-referencing.
- tools/layer_registry.py::layer_values() for canonical layer cross-referencing.
- tools/agent-monitoring/generate_retro.py::iso_week() for ISO-week grouping — already proven,
  not reimplemented a second time.

Usage:
  python3 tools/ticket_stats_report.py
  python3 tools/ticket_stats_report.py --root . --json reports/ticket_stats_report.json
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"
for _p in (_TOOLS_DIR, _MONITORING_TOOLS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from validate_frontmatter import extract_frontmatter  # noqa: E402
from generate_registry import parse_body_section, _strip_frontmatter  # noqa: E402
from ticket_field_values import TIER_VALUES, PRIORITY_VALUES  # noqa: E402
from layer_registry import layer_values  # noqa: E402
from generate_retro import iso_week  # noqa: E402

_REQUIRED_ARTIFACT_FILES = ("investigation.md", "plan.md", "test_plan.md")


# ---------------------------------------------------------------------------
# Ticket collection
# ---------------------------------------------------------------------------


def collect_done_tickets(root: Path):
    """Walk tickets/done/ recursively for ticket markdown files.

    Returns (included, skip_reasons) — included is a list of dicts with ticket_id/layer/tier/
    ticket_type/priority/date; skip_reasons is a Counter keyed by skip reason. No tag-taxonomy
    date gate (unlike tag_report.py's collect_completed_tickets) — Tier/Type/Priority/Layer
    distribution is not tag-taxonomy-gated, every ticket with parseable frontmatter counts.
    """
    done_dir = root / "tickets" / "done"
    included = []
    skip_reasons: Counter = Counter()

    if not done_dir.is_dir():
        return included, skip_reasons

    for md_file in sorted(done_dir.rglob("*.md")):
        if md_file.name == "SEQUENCE.md":
            skip_reasons["sequence_index_file"] += 1
            continue

        text = md_file.read_text(encoding="utf-8")
        try:
            fm = extract_frontmatter(text)
        except ValueError:
            skip_reasons["unparseable_frontmatter"] += 1
            continue
        if fm is None:
            skip_reasons["no_frontmatter_legacy_format"] += 1
            continue

        ticket_id = fm.get("ticket_id") or md_file.stem
        body = _strip_frontmatter(text)

        included.append({
            "ticket_id": ticket_id,
            "layer": fm.get("layer") or None,
            "tier": parse_body_section(body, "Tier") or None,
            "ticket_type": parse_body_section(body, "Type") or None,
            "priority": parse_body_section(body, "Priority") or None,
            "date": fm.get("date") or None,
        })

    return included, skip_reasons


# ---------------------------------------------------------------------------
# Velocity / throughput
# ---------------------------------------------------------------------------


def compute_velocity(root: Path) -> dict:
    """Ticket closures per day and per ISO week, from tickets/working_log.csv's timestamp
    column. Malformed/unparseable timestamp rows are counted separately, never silently dropped
    or crashed on (mirrors this project's tolerant-legacy-data convention elsewhere)."""
    log_path = root / "tickets" / "working_log.csv"
    by_day: Counter = Counter()
    by_week: Counter = Counter()
    unparseable = 0

    if not log_path.exists():
        return {"by_day": {}, "by_week": {}, "unparseable_rows": 0}

    lines = log_path.read_text(encoding="utf-8").splitlines()
    for line in lines[1:]:  # skip header
        if not line.strip():
            continue
        ts = line.split(",", 1)[0].strip()
        if not ts:
            unparseable += 1
            continue
        day = ts[:10]  # YYYY-MM-DD prefix of an ISO8601 timestamp
        week = iso_week(ts)
        if week == "unknown":
            unparseable += 1
            continue
        by_day[day] += 1
        by_week[week] += 1

    return {
        "by_day": dict(sorted(by_day.items())),
        "by_week": dict(sorted(by_week.items())),
        "unparseable_rows": unparseable,
    }


# ---------------------------------------------------------------------------
# Distribution
# ---------------------------------------------------------------------------


def compute_distribution(included: list) -> dict:
    """Counter-based distribution over tier/ticket_type/priority/layer, plus a layer-by-tier
    cross-tab. None values (missing body section / missing frontmatter field) are counted under
    the literal key "unknown" — a real, visible data-quality signal, never silently dropped."""
    tier_counts: Counter = Counter()
    type_counts: Counter = Counter()
    priority_counts: Counter = Counter()
    layer_counts: Counter = Counter()
    layer_by_tier: dict = defaultdict(lambda: defaultdict(int))

    for t in included:
        tier = t["tier"] or "unknown"
        ticket_type = t["ticket_type"] or "unknown"
        priority = t["priority"] or "unknown"
        layer = t["layer"] or "unknown"

        tier_counts[tier] += 1
        type_counts[ticket_type] += 1
        priority_counts[priority] += 1
        layer_counts[layer] += 1
        layer_by_tier[layer][tier] += 1

    return {
        "tier": dict(tier_counts),
        "ticket_type": dict(type_counts),
        "priority": dict(priority_counts),
        "layer": dict(layer_counts),
        "layer_by_tier": {layer: dict(tiers) for layer, tiers in layer_by_tier.items()},
    }


# ---------------------------------------------------------------------------
# Artifact completeness
# ---------------------------------------------------------------------------


def compute_artifact_completeness(included: list, root: Path) -> dict:
    """For standard/epic tickets only (hotfix tickets have no staging-artifact requirement per
    CLAUDE.md's Workflow Rule): whether stored_artifacts/{ticket_id}/ exists with all 3 required
    files, non-empty."""
    complete = []
    incomplete = []

    for t in included:
        if t["tier"] not in ("standard", "epic"):
            continue
        artifacts_dir = root / "stored_artifacts" / t["ticket_id"]
        missing = []
        for fname in _REQUIRED_ARTIFACT_FILES:
            fpath = artifacts_dir / fname
            if not fpath.exists() or fpath.stat().st_size == 0:
                missing.append(fname)
        if missing:
            incomplete.append({"ticket_id": t["ticket_id"], "missing": missing})
        else:
            complete.append(t["ticket_id"])

    total = len(complete) + len(incomplete)
    return {
        "complete_count": len(complete),
        "incomplete_count": len(incomplete),
        "total_checked": total,
        "incomplete": incomplete,
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def print_report(included, skip_reasons, velocity, distribution, artifact_completeness) -> None:
    scanned = len(included) + sum(skip_reasons.values())
    print(f"Ticket stats report: {scanned} ticket file(s) scanned under tickets/done/")
    print(f"  included: {len(included)}")
    if skip_reasons:
        print("  skipped:")
        for reason, count in sorted(skip_reasons.items()):
            print(f"    {reason}: {count}")

    print(f"\nVelocity: {velocity['unparseable_rows']} unparseable working_log rows")
    print(f"  Recent days: {list(velocity['by_day'].items())[-5:]}")
    print(f"  Recent weeks: {list(velocity['by_week'].items())[-3:]}")

    print("\nTier distribution:")
    for tier, count in sorted(distribution["tier"].items(), key=lambda kv: -kv[1]):
        marker = "" if tier in TIER_VALUES else "  <-- non-canonical"
        print(f"  {tier:<12} {count:>5}{marker}")

    print("\nPriority distribution:")
    for priority, count in sorted(distribution["priority"].items(), key=lambda kv: -kv[1]):
        marker = "" if priority in PRIORITY_VALUES else "  <-- non-canonical"
        print(f"  {priority:<12} {count:>5}{marker}")

    print("\nLayer distribution:")
    canonical_layers = layer_values()
    for layer, count in sorted(distribution["layer"].items(), key=lambda kv: -kv[1]):
        marker = "" if layer in canonical_layers else "  <-- non-canonical"
        print(f"  {layer:<16} {count:>5}{marker}")

    print(
        f"\nArtifact completeness (standard/epic only): "
        f"{artifact_completeness['complete_count']}/{artifact_completeness['total_checked']} complete"
    )
    if artifact_completeness["incomplete"]:
        print("  Incomplete:")
        for entry in artifact_completeness["incomplete"][:10]:
            print(f"    {entry['ticket_id']}: missing {entry['missing']}")


def build_json_report(included, skip_reasons, velocity, distribution, artifact_completeness) -> dict:
    scanned = len(included) + sum(skip_reasons.values())
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scanned_files": scanned,
        "included_tickets": len(included),
        "skipped": dict(sorted(skip_reasons.items())),
        "velocity": velocity,
        "distribution": distribution,
        "artifact_completeness": artifact_completeness,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a ticket-corpus statistics report over completed tickets (tickets/done/)."
    )
    parser.add_argument("--root", default=".", help="Project root directory (default: current directory)")
    parser.add_argument("--json", default=None, help="Optional path to write a structured JSON report")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    included, skip_reasons = collect_done_tickets(root)
    velocity = compute_velocity(root)
    distribution = compute_distribution(included)
    artifact_completeness = compute_artifact_completeness(included, root)

    print_report(included, skip_reasons, velocity, distribution, artifact_completeness)

    if args.json:
        json_path = Path(args.json)
        if not json_path.is_absolute():
            json_path = root / json_path
        json_path.parent.mkdir(parents=True, exist_ok=True)
        report = build_json_report(included, skip_reasons, velocity, distribution, artifact_completeness)
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote JSON report to {json_path}")


if __name__ == "__main__":
    main()
