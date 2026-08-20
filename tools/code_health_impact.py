#!/usr/bin/env python3
"""`code-health impact <path>` — change-impact triage for a single source path.

Item 2 of `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`, built for
`TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND` on top of the design in
`docs/audits/D24_codebase_health_observatory.md` §L. This is a **discovery/
triage aid, not a certified coverage oracle** — every signal below is a
best-effort heuristic and is presented as such; false positives/negatives are
acceptable, silently presenting them as certain is not.

**Dependents lookup** does NOT hand-roll a BFS/DFS over `graphify-out/graph.json`
— `graphify affected "<symbol>" --depth N` already implements exactly that
reverse traversal. What this module adds is the piece `affected` itself does
not do: resolving a *file path* to the symbol/class node(s) `graph.json`
records as `contains`-linked from that file's own node (a graph.json lookup,
not a traversal), invoking `affected` once per resolved symbol (it has no
`--json` flag — its plain-text output is parsed here), and aggregating the
per-symbol results back to file-level dependents.

Two independent, real degradation modes exist and are both handled by
returning a clearly-labeled empty/partial result rather than crashing:

1. **Zero resolvable symbols** — a target path with no `contains` edges from
   its file node (e.g. a pure-constants module, or a path the graph never
   indexed). No `affected` calls are made at all.
2. **"No unique node match"** — even a symbol genuinely `contains`-linked
   from the file node can be ambiguous to `affected` itself, because the AST
   extractor sometimes creates a second, separate node instance with the same
   label in a citing file instead of resolving back to the canonical
   definition node (confirmed live: `graphify affected "MovementMode"` on
   `src/core/movement_modes.py` — a file that unambiguously `contains`
   exactly one symbol, `MovementMode` — still reports "No unique node match",
   because 5 different node ids across the graph share that exact label).
   Each symbol is tried independently; only symbols that individually hit
   this are skipped, not the whole file.

**Required-tests lookup** combines two signals, per plan.md step 4: (a)
`docs/REGISTRY.yaml`'s `related_code_areas` field, resolving bare symbol
names/filenames (not full paths — confirmed ~47% of non-empty entries are
this shape) via the graph's own label index rather than literal path
matching; (b) the `src/` → `tests/unit/` naming convention already documented
in `.claude/agents/test-scoper.md`'s Test Directory Map, reused here rather
than reinvented.

**Criticality tier** extends (does not duplicate)
`tools/codebase_health_baseline.py::compute_churn_lines_changed()` with an
optional `target_pathspec` parameter, combined with graph edge-degree
(in-edges + out-edges, summed across every node whose `source_file` is the
target path) for centrality. The high/medium/low bucket cutoffs below are
grounded in this repo's own real observed spread at the time of writing
(`src/engine/pipeline.py`: churn 6323 / degree 501; `src/engine/kernel.py`:
churn 1681 / degree 1410; `src/observability/reporter.py`: churn 20 /
degree 12) — they are round-number heuristic buckets over that spread, not a
statistically derived model.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from codebase_health_baseline import compute_churn_lines_changed  # noqa: E402

DEFAULT_GRAPH_PATH = _REPO_ROOT / "graphify-out" / "graph.json"
DEFAULT_REGISTRY_PATH = _REPO_ROOT / "docs" / "REGISTRY.yaml"
ARCHITECTURE_TESTS_DIR = _REPO_ROOT / "tests" / "architecture"
DEFAULT_AFFECTED_DEPTH = 2

_AFFECTED_LINE_RE = re.compile(r"^- .+? \[[a-z_]+\] (\S+):L\d+$")
_NO_MATCH_MARKER = "No unique node match"
_LINE_SUFFIX_RE = re.compile(r":\d+(-\d+)?$")

# Heuristic subsystem-prefix -> architecture test file map (plan.md step 3:
# "list plausibly relevant ones, not perfect precision"). Grounded in each
# file's own docstring/imports/literal path scans, not guessed blind — see
# investigation notes for TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND.
ARCHITECTURE_RULE_PATH_PREFIXES = {
    "test_adventure_route_score_max_unchanged.py": (
        "src/domains/adventure",
        "src/systems/strategic_systems/intelligence.py",
    ),
    "test_api_read_model_guard.py": ("src/api",),
    "test_capability_references.py": (
        "docs/engine/capability_registry.yaml",
        "src/engine",
    ),
    "test_committed_intention_arbiter_byte_identical_guard.py": (
        "src/cognition",
        "src/strategy",
        "src/domains/adventure",
    ),
    "test_decision_trace_hot_path_no_io.py": ("src/observability",),
    "test_docker_compose_dependency_hygiene.py": ("docker-compose",),
    "test_enum_migration_report.py": ("src/",),
    "test_fallback_retirement_gate.py": (
        "docs/guidelines/fallback_retirement_criteria.md",
    ),
    "test_guild_action_dormancy.py": ("src/town/guild.py", "src/quests"),
    "test_legacy_enum_usage_boundaries.py": ("src/",),
    "test_no_new_hardcoded_gameplay_truth.py": ("src/",),
    "test_no_old_structural_content_paths.py": (
        "src/content",
        "src/worldbuilding",
        "src/worldmodules",
    ),
    "test_phase18_cognition_migration_linter.py": (
        "src/cognition",
        "src/core/state.py",
    ),
    "test_phase18_import_boundaries.py": (
        "src/core",
        "src/domains",
        "src/observability",
        "src/systems",
    ),
    "test_phase19_hot_path_safety_contract.py": ("src/engine", "src/observability"),
    "test_phase19_observability_boundaries.py": ("src/engine", "src/observability"),
    "test_phase_domain_permissions.py": ("src/engine", "src/domains"),
}

# Criticality tier bucket cutoffs — see module docstring for the real data
# these were grounded against.
CHURN_HIGH_THRESHOLD = 1000
CHURN_MEDIUM_THRESHOLD = 100
EDGE_DEGREE_HIGH_THRESHOLD = 300
EDGE_DEGREE_MEDIUM_THRESHOLD = 50


def load_graph(graph_path: Path = DEFAULT_GRAPH_PATH) -> dict:
    with open(graph_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def find_file_node(graph: dict, target_path: str) -> dict | None:
    """Return the node graph.json records as *the file itself* for target_path.

    This is a lookup (source_file + label == basename + source_location L1),
    not a traversal — the file node is where `contains` edges to its defined
    symbols originate.
    """
    basename = Path(target_path).name
    for node in graph.get("nodes", []):
        if (
            node.get("source_file") == target_path
            and node.get("label") == basename
            and node.get("file_type") == "code"
        ):
            return node
    return None


def resolve_defined_symbols(graph: dict, file_node: dict | None) -> list:
    """Symbol/class labels the file node `contains` — i.e. defined in this file."""
    if file_node is None:
        return []
    nodes_by_id = {n["id"]: n for n in graph.get("nodes", [])}
    symbols = []
    for link in graph.get("links", []):
        if link.get("relation") == "contains" and link.get("source") == file_node["id"]:
            target_node = nodes_by_id.get(link.get("target"))
            if target_node is not None:
                symbols.append(target_node["label"])
    return symbols


def run_graphify_affected(symbol: str, depth: int, graph_path: Path) -> str:
    result = subprocess.run(
        ["graphify", "affected", symbol, "--depth", str(depth), "--graph", str(graph_path)],
        capture_output=True, text=True,
    )
    return result.stdout


def parse_affected_output(output: str) -> set:
    """Extract dependent file paths from `graphify affected`'s plain-text output.

    Returns an empty set both when there are genuinely zero affected nodes and
    when the symbol hit "No unique node match" — callers distinguish the two
    via the raw output text, since both are legitimate empty results here.
    """
    if _NO_MATCH_MARKER in output:
        return set()
    dependents = set()
    for line in output.splitlines():
        line = line.strip()
        match = _AFFECTED_LINE_RE.match(line)
        if match:
            dependents.add(match.group(1))
    return dependents


def find_dependents(
    graph: dict,
    target_path: str,
    depth: int = DEFAULT_AFFECTED_DEPTH,
    graph_path: Path = DEFAULT_GRAPH_PATH,
    affected_runner=run_graphify_affected,
) -> dict:
    file_node = find_file_node(graph, target_path)
    symbols = resolve_defined_symbols(graph, file_node)

    if not symbols:
        return {
            "dependents": set(),
            "resolved_symbols": [],
            "unresolved_symbols": [],
            "degraded": True,
            "degradation_reason": (
                f"No symbols found `contains`-linked from {target_path}'s file "
                "node in graphify-out/graph.json (e.g. a constants-only module, "
                "or a path the graph never indexed) — dependents cannot be "
                "computed for this path."
            ),
        }

    dependents = set()
    unresolved_symbols = []
    for symbol in symbols:
        output = affected_runner(symbol, depth, graph_path)
        symbol_dependents = parse_affected_output(output)
        if not symbol_dependents and _NO_MATCH_MARKER in output:
            unresolved_symbols.append(symbol)
            continue
        dependents |= symbol_dependents

    dependents.discard(target_path)
    degraded = len(unresolved_symbols) == len(symbols)
    degradation_reason = None
    if degraded:
        degradation_reason = (
            f"All {len(symbols)} resolved symbol(s) for {target_path} hit "
            "'No unique node match' in `graphify affected` (label collisions "
            "elsewhere in the graph) — dependents could not be computed."
        )

    return {
        "dependents": dependents,
        "resolved_symbols": symbols,
        "unresolved_symbols": unresolved_symbols,
        "degraded": degraded,
        "degradation_reason": degradation_reason,
    }


def match_architecture_rules(target_path: str) -> list:
    matched = [
        filename
        for filename, prefixes in ARCHITECTURE_RULE_PATH_PREFIXES.items()
        if any(target_path.startswith(prefix) for prefix in prefixes)
    ]
    return sorted(matched)


def build_label_index(graph: dict) -> dict:
    """label -> set of source_file paths defining/using a node with that label.

    Used to resolve bare symbol names in `related_code_areas` entries (per
    investigation.md: not every entry is a clean resolvable path).
    """
    index: dict = {}
    for node in graph.get("nodes", []):
        label = node.get("label")
        source_file = node.get("source_file")
        if not label or not source_file:
            continue
        index.setdefault(label, set()).add(source_file)
        stripped = label[:-2] if label.endswith("()") else label
        if stripped != label:
            index.setdefault(stripped, set()).add(source_file)
    return index


def build_basename_index(graph: dict) -> dict:
    """basename (e.g. 'foo.py') -> set of full source_file paths with that name."""
    index: dict = {}
    for node in graph.get("nodes", []):
        source_file = node.get("source_file")
        if not source_file:
            continue
        index.setdefault(Path(source_file).name, set()).add(source_file)
    return index


def normalize_registry_value(value: str) -> str:
    """Strip a `::Symbol` suffix and a trailing `:123` / `:123-456` line ref."""
    value = value.split("::")[0]
    value = _LINE_SUFFIX_RE.sub("", value)
    return value.strip()


def resolve_registry_value_paths(value: str, label_index: dict, basename_index: dict) -> set:
    normalized = normalize_registry_value(value)
    if "/" in normalized:
        return {normalized}
    if not normalized:
        return set()
    stripped = normalized[:-2] if normalized.endswith("()") else normalized
    resolved = set(label_index.get(normalized, set())) | set(label_index.get(stripped, set()))
    if not resolved and "." in normalized:
        resolved = set(basename_index.get(normalized, set()))
    return resolved


def registry_entry_matches_target(
    related_code_areas: list, target_path: str, label_index: dict, basename_index: dict
) -> bool:
    for raw_value in related_code_areas:
        normalized = normalize_registry_value(raw_value)
        if normalized.endswith("/"):
            if target_path.startswith(normalized):
                return True
            continue
        resolved_paths = resolve_registry_value_paths(raw_value, label_index, basename_index)
        if target_path in resolved_paths:
            return True
    return False


def required_tests_from_registry(
    registry_entries: list, target_path: str, label_index: dict, basename_index: dict
) -> set:
    required_tests = set()
    for entry in registry_entries:
        related_code_areas = entry.get("related_code_areas") or []
        if not related_code_areas:
            continue
        if not registry_entry_matches_target(related_code_areas, target_path, label_index, basename_index):
            continue
        for raw_value in related_code_areas:
            normalized = normalize_registry_value(raw_value)
            if normalized.startswith("tests/"):
                required_tests.add(normalized)
    return required_tests


def load_registry_entries(registry_path: Path = DEFAULT_REGISTRY_PATH) -> list:
    if not registry_path.exists():
        return []
    with open(registry_path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or []
    return data if isinstance(data, list) else []


def required_tests_from_naming_convention(target_path: str, repo_root: Path = _REPO_ROOT) -> list:
    """`src/` -> `tests/unit/` mapping per `.claude/agents/test-scoper.md`'s
    Test Directory Map — reused here, not reinvented. Only paths that exist
    on disk are returned (unresolvable/no-coverage is left to the caller to
    note, not fabricated as a suggested directory)."""
    parts = Path(target_path).parts
    if not parts:
        return []

    candidates = []
    if parts[0] == "src" and len(parts) >= 2:
        if parts[1] == "domains" and len(parts) >= 3:
            candidates.append(f"tests/unit/domains/{parts[2]}/")
        else:
            candidates.append(f"tests/unit/{parts[1]}/")
        candidates.append(f"tests/integration/{parts[1]}/")
    elif parts[0] == "tools" and len(parts) >= 2:
        if len(parts) > 2:
            candidates.append(f"tests/{parts[1]}/")
        candidates.append("tests/tools/")

    return [c for c in candidates if (repo_root / c).is_dir()]


def compute_edge_degree(graph: dict, target_path: str) -> int:
    """in-edges + out-edges summed across every node whose source_file is
    target_path — the file's full footprint in the graph, not just its own
    file-level node (which typically has just one `contains` edge)."""
    node_ids = {n["id"] for n in graph.get("nodes", []) if n.get("source_file") == target_path}
    if not node_ids:
        return 0
    degree = 0
    for link in graph.get("links", []):
        if link.get("source") in node_ids:
            degree += 1
        if link.get("target") in node_ids:
            degree += 1
    return degree


def compute_criticality_tier(churn: int, edge_degree: int) -> str:
    if churn >= CHURN_HIGH_THRESHOLD or edge_degree >= EDGE_DEGREE_HIGH_THRESHOLD:
        return "high"
    if churn >= CHURN_MEDIUM_THRESHOLD or edge_degree >= EDGE_DEGREE_MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def sort_dependents_src_first(dependents: set, target_path: str = "") -> list:
    """Sort dependents by relevance tier, then alphabetically within each tier:
    (0) same src/ subsystem as the target, (1) other src/ paths, (2) everything
    else (tests, scripts, experiments).

    For a widely-used file, `graphify affected`'s dependent set is dominated by
    hundreds of test files and src/ files from unrelated subsystems, which bury
    the tightly-coupled, architecturally-relevant dependents a triage aid needs
    to surface first — e.g. plain alphabetical (or even plain src/-first) sort
    puts `src/actions/*.py`, `src/ai/*.py` etc. ahead of `src/engine/kernel.py`
    for a `src/engine/pipeline.py` target, pushing kernel.py past a truncated
    display's cutoff even though it is exactly the dependent this tool's own
    acceptance criteria call out. Same-subsystem-first fixes that without
    discarding the full data (still available via `dependents_result`/JSON, not
    truncated) — only the human-readable summary's ordering changes.
    """
    target_subsystem_prefix = "/".join(Path(target_path).parts[:2]) + "/" if target_path else None

    def sort_key(path: str) -> tuple:
        if target_subsystem_prefix and path.startswith(target_subsystem_prefix):
            tier = 0
        elif path.startswith("src/"):
            tier = 1
        else:
            tier = 2
        return (tier, path)

    return sorted(dependents, key=sort_key)


def derive_subsystem(target_path: str) -> str:
    parts = Path(target_path).parts
    if len(parts) >= 2 and parts[0] in ("src", "tools", "tests"):
        return parts[1].replace("_", " ").title()
    return parts[0].replace("_", " ").title() if parts else target_path


def build_impact_report(
    repo_root: Path,
    target_path: str,
    depth: int = DEFAULT_AFFECTED_DEPTH,
    graph: dict | None = None,
    graph_path: Path = DEFAULT_GRAPH_PATH,
    registry_entries: list | None = None,
    affected_runner=run_graphify_affected,
) -> dict:
    if graph is None:
        graph = load_graph(graph_path)
    if registry_entries is None:
        registry_entries = load_registry_entries(repo_root / "docs" / "REGISTRY.yaml")

    dependents_result = find_dependents(
        graph, target_path, depth=depth, graph_path=graph_path, affected_runner=affected_runner
    )

    label_index = build_label_index(graph)
    basename_index = build_basename_index(graph)
    registry_tests = required_tests_from_registry(registry_entries, target_path, label_index, basename_index)
    naming_tests = required_tests_from_naming_convention(target_path, repo_root)
    required_tests = sorted(registry_tests | set(naming_tests))

    architecture_rules = match_architecture_rules(target_path)

    churn = compute_churn_lines_changed(repo_root, target_pathspec=target_path)
    edge_degree = compute_edge_degree(graph, target_path)
    tier = compute_criticality_tier(churn, edge_degree)

    return {
        "target_path": target_path,
        "subsystem": derive_subsystem(target_path),
        "dependents": sort_dependents_src_first(dependents_result["dependents"], target_path),
        "dependents_degraded": dependents_result["degraded"],
        "dependents_degradation_reason": dependents_result["degradation_reason"],
        "resolved_symbols": dependents_result["resolved_symbols"],
        "unresolved_symbols": dependents_result["unresolved_symbols"],
        "required_tests": required_tests,
        "required_tests_registry_hit_count": len(registry_tests),
        "architecture_rules": architecture_rules,
        "churn_lines_changed": churn,
        "edge_degree": edge_degree,
        "criticality_tier": tier,
    }


def format_impact_report(report: dict, max_dependents_shown: int = 40) -> str:
    lines = [
        f"Change-Impact Report: {report['target_path']}",
        "=" * 74,
        f"Subsystem:            {report['subsystem']}",
    ]

    dependents = report["dependents"]
    if report["dependents_degraded"]:
        lines.append(f"Direct dependents:    (none resolvable — {report['dependents_degradation_reason']})")
    elif dependents:
        shown = dependents[:max_dependents_shown]
        suffix = f" (+{len(dependents) - max_dependents_shown} more)" if len(dependents) > max_dependents_shown else ""
        lines.append(f"Direct dependents:    {', '.join(shown)}{suffix}")
        lines.append(f"                      ({len(dependents)} total, via graphify affected --depth 2)")
    else:
        lines.append("Direct dependents:    (none found)")

    if report["unresolved_symbols"] and not report["dependents_degraded"]:
        lines.append(
            f"                      note: {len(report['unresolved_symbols'])} symbol(s) "
            f"skipped (ambiguous node match): {', '.join(report['unresolved_symbols'])}"
        )

    if report["required_tests"]:
        lines.append(f"Required tests:       {', '.join(report['required_tests'])}")
    else:
        lines.append("Required tests:       (none found via registry or naming convention — verify coverage manually)")

    if report["architecture_rules"]:
        lines.append(f"Architecture rules:   {', '.join(report['architecture_rules'])}")
    else:
        lines.append("Architecture rules:   (none plausibly relevant by subsystem heuristic)")

    lines.append(
        f"Criticality tier:     {report['criticality_tier']} "
        f"(churn={report['churn_lines_changed']:,} lines changed [this path, full history], "
        f"edge_degree={report['edge_degree']:,})"
    )
    lines.append(
        "Note:                 discovery/triage aid, not a certified coverage "
        "oracle — verify before treating any of the above as complete."
    )
    lines.append("=" * 74)
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_path", help="Repo-relative source path, e.g. src/engine/pipeline.py")
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--depth", type=int, default=DEFAULT_AFFECTED_DEPTH)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH_PATH)
    args = parser.parse_args(argv)

    report = build_impact_report(args.repo_root, args.target_path, depth=args.depth, graph_path=args.graph)
    print(format_impact_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
