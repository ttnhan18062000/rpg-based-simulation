#!/usr/bin/env python3
"""Batched PR/AI change-impact report generator over one or more source paths.

Item 4 of `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`, built for
`TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR` on top of
`tools/code_health_impact.py::build_impact_report()`. This is a
**discovery/triage aid, not a certified coverage oracle** — every signal
below is a best-effort heuristic and is presented as such; false
positives/negatives are acceptable, silently presenting them as certain is
not.

**Design decision — no dependency on `tools/codebase_health_snapshot.py`**:
this module renders exclusively from `chi.build_impact_report()`'s existing
per-path output, batched across one or more target paths. It has no import
of, and no dependency on, `tools/codebase_health_snapshot.py`'s
repo-wide-aggregate snapshot/scorecard mechanism — that mechanism has no
per-path join key to integrate against, and the source audit's own "built on
top of Phase 3's impact model" phrasing (`docs/audits/D24_codebase_health_observatory.md`
§M item 11) refers to the Phase 3 impact command
(`tools/code_health_impact.py`), not the Phase 4 historical-snapshot
mechanism. See `TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR` and the epic
(`TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`) for the full
resolved reasoning.
"""

import argparse
import json
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import code_health_impact as chi  # noqa: E402

FRAMING_NOTE = (
    "discovery/triage aid, not a certified coverage oracle — verify before "
    "treating any of the below as complete."
)


def build_pr_impact_report(
    repo_root: Path,
    target_paths: list,
    depth: int = chi.DEFAULT_AFFECTED_DEPTH,
    graph: dict | None = None,
    graph_path: Path = chi.DEFAULT_GRAPH_PATH,
    registry_entries: list | None = None,
    affected_runner=chi.run_graphify_affected,
) -> dict:
    if graph is None:
        graph = chi.load_graph(graph_path)
    if registry_entries is None:
        registry_entries = chi.load_registry_entries(repo_root / "docs" / "REGISTRY.yaml")

    entries = []
    for target_path in target_paths:
        try:
            report = chi.build_impact_report(
                repo_root,
                target_path,
                depth=depth,
                graph=graph,
                graph_path=graph_path,
                registry_entries=registry_entries,
                affected_runner=affected_runner,
            )
            entries.append({
                "target_path": target_path,
                "status": "ok",
                "report": report,
                "error": None,
            })
        except Exception as exc:
            entries.append({
                "target_path": target_path,
                "status": "failed",
                "report": None,
                "error": str(exc),
            })

    return {
        "target_paths": list(target_paths),
        "entries": entries,
        "framing_note": FRAMING_NOTE,
    }


def format_pr_impact_report(report: dict, max_dependents_shown: int = 40) -> str:
    lines = []
    for entry in report["entries"]:
        lines.append(f"## {entry['target_path']}")
        if entry["status"] == "failed":
            lines.append(f"**Failed:** {entry['error']}")
            lines.append("")
            continue

        item = entry["report"]
        lines.append(f"- **target_path:** {item['target_path']}")
        lines.append(f"- **subsystem:** {item['subsystem']}")

        dependents = item["dependents"]
        if item["dependents_degraded"]:
            lines.append(
                f"- **dependents:** (none resolvable — {item['dependents_degradation_reason']})"
            )
        elif dependents:
            shown = dependents[:max_dependents_shown]
            suffix = (
                f" (+{len(dependents) - max_dependents_shown} more)"
                if len(dependents) > max_dependents_shown
                else ""
            )
            lines.append(f"- **dependents:** {', '.join(shown)}{suffix}")
            lines.append(f"  ({len(dependents)} total)")
        else:
            lines.append("- **dependents:** (none found)")

        if item["unresolved_symbols"] and not item["dependents_degraded"]:
            lines.append(
                f"  note: {len(item['unresolved_symbols'])} symbol(s) skipped "
                f"(ambiguous node match): {', '.join(item['unresolved_symbols'])}"
            )

        lines.append(f"- **dependents_degraded:** {item['dependents_degraded']}")
        lines.append(
            f"- **dependents_degradation_reason:** "
            f"{item['dependents_degradation_reason'] if item['dependents_degradation_reason'] else '(none)'}"
        )

        if item["resolved_symbols"]:
            lines.append(f"- **resolved_symbols:** {', '.join(item['resolved_symbols'])}")
        else:
            lines.append("- **resolved_symbols:** (none found)")

        if item["unresolved_symbols"]:
            lines.append(f"- **unresolved_symbols:** {', '.join(item['unresolved_symbols'])}")
        else:
            lines.append("- **unresolved_symbols:** (none)")

        if item["required_tests"]:
            lines.append(f"- **required_tests:** {', '.join(item['required_tests'])}")
        else:
            lines.append("- **required_tests:** (none found via registry or naming convention — verify coverage manually)")
        lines.append(f"- **required_tests_registry_hit_count:** {item['required_tests_registry_hit_count']}")

        if item["architecture_rules"]:
            lines.append(f"- **architecture_rules:** {', '.join(item['architecture_rules'])}")
        else:
            lines.append("- **architecture_rules:** (none plausibly relevant by subsystem heuristic)")

        lines.append(f"- **churn_lines_changed:** {item['churn_lines_changed']:,}")
        lines.append(f"- **edge_degree:** {item['edge_degree']:,}")
        lines.append(f"- **criticality_tier:** {item['criticality_tier']}")
        lines.append("")

    lines.append(f"_{report['framing_note']}_")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target_paths", nargs="+",
        help="One or more repo-relative source paths, e.g. src/engine/pipeline.py",
    )
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--depth", type=int, default=chi.DEFAULT_AFFECTED_DEPTH)
    parser.add_argument("--graph", type=Path, default=chi.DEFAULT_GRAPH_PATH)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args(argv)

    report = build_pr_impact_report(
        args.repo_root, args.target_paths, depth=args.depth, graph_path=args.graph,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_pr_impact_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
