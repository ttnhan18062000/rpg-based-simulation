"""Deterministic code/test symbol index over graphify-out/graph.json.

Indexes only Part A (AST-derived, non-LLM) graphify relations into per-symbol records.
An edge is admitted only if BOTH (a) its `relation` is in PART_A_ALLOWLIST and (b) its own
`confidence_score` field equals the float `1.0` (exact equality). The `confidence` string
field is never read in the admission path. Live `graphify-out/graph.json` data proves the
two fields disagree on real edges (5 `inherits` edges carry `confidence="EXTRACTED"` but
`confidence_score=0.5`), and a relation-type-name-only filter would wrongly admit 45.1% of
the naive Part A edge set (34,616 of 76,829 edges) as "deterministic" when it is not -- see
`staging_artifacts/TCK-20260729-DETERMINISTIC-CODE-INDEX/investigation.md`. Reintroducing a
relation-name-only filter anywhere in this module silently reintroduces that bug.

Scope decisions (full rationale in this ticket's plan.md "Resolved Decisions"):

- PART_A_ALLOWLIST is the Phase 2 decision doc's 14-relation Part A table PLUS `method` and
  `inherits` (both structurally AST-derived and 100%/99.3% deterministic in the live graph;
  their inclusion was explicitly invited by this ticket's own Assumptions section). It
  deliberately EXCLUDES `references` and `re_exports` -- both are 100% per-edge
  deterministic in the live graph too, but neither appears in the ticket's or the decision
  doc's documented Part A table, and the ticket never asked to resolve them; a future
  ticket may add them. Do not add them here without a new ticket.
- `docstring` is populated by ast-parsing the real `.py` source file named in a node's
  `source_file` field -- graph nodes carry no docstring field of their own (only
  `language`/`kind`/`mcp_kind` metadata keys exist in this repo's graph data). Falls back
  to the explicit `DOCSTRING_GAP` sentinel (never `None`/`""`) when the source can't be
  read/parsed or the symbol can't be found in it.
- `associated_tests` is a minimal glob mapping: the top-level `src/<module>/` directory
  segment (e.g. `src/observability/understanding/domain/quest.py` -> module `observability`)
  is mapped to `tests/unit/<module>/**/test_*.py`, mirroring
  `.claude/agents/test-scoper.md`'s documented `src/<module>/` -> `tests/unit/<module>/`
  convention (which is single-top-level-segment, matching its own Test Directory Map).
  Falls back to the explicit `ASSOCIATED_TESTS_GAP` sentinel (never `[]`/`None`/`""`) when
  no test file matches or the symbol is outside `src/`.
- `owned_component` is the raw graphify community integer already computed on every code
  node (`node["community"]`), not a resolved human-readable community label -- resolving a
  label was never asked for by any acceptance criterion.
- This module is standalone: it is not imported by, and does not import,
  `tools/knowledge_search.py`'s corpus/`cmd_build`/`cmd_query` pipeline, and is not wired
  into any `.claude/workflows/*.js` file. It is invoked manually via the `build`/`query`
  CLI subcommands below.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path, PurePosixPath
from typing import Iterator

# Phase 2 decision doc's documented Part A table (14 relations) plus `method` and
# `inherits` (Resolved Decision 5 -- both are structurally AST-derived, non-LLM relations
# absent from the decision doc's table only because that table was evidenced against an
# older graphifyy version). Deliberately excludes `references` and `re_exports` (Resolved
# Decision 4) even though both are 100% per-edge deterministic in the live graph -- neither
# is in the ticket's or decision doc's documented allowlist and the ticket never asked to
# resolve them. See staging_artifacts/TCK-20260729-DETERMINISTIC-CODE-INDEX/plan.md.
PART_A_ALLOWLIST: frozenset[str] = frozenset(
    {
        "imports",
        "imports_from",
        "calls",
        "contains",
        "defines",
        "uses",
        "uses_static_prop",
        "references_constant",
        "bound_to",
        "listened_by",
        "includes",
        "uses_component",
        "binds_method",
        "rationale_for",
        "method",
        "inherits",
    }
)

DOCSTRING_GAP = "UNRESOLVED_GAP:no_docstring_found"
ASSOCIATED_TESTS_GAP = "UNRESOLVED_GAP:no_test_mapping_found"

DEFAULT_REPO_ROOT = Path(__file__).resolve().parent.parent


def load_graph(graph_path: Path) -> dict:
    with open(graph_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_admitted_edges(graph_data: dict) -> Iterator[dict]:
    for edge in graph_data["links"]:
        if edge.get("relation") in PART_A_ALLOWLIST and edge.get("confidence_score") == 1.0:
            yield edge


def _module_from_source_file(source_file: str) -> str:
    path = PurePosixPath(source_file)
    if path.suffix:
        path = path.with_suffix("")
    return ".".join(path.parts)


def _normalize_symbol_label(label: str) -> str:
    normalized = label.strip()
    if normalized.startswith("."):
        normalized = normalized[1:]
    if normalized.endswith("()"):
        normalized = normalized[:-2]
    return normalized


def _parse_line_number(source_location: str) -> int | None:
    if not source_location:
        return None
    text = source_location[1:] if source_location.startswith("L") else source_location
    try:
        return int(text)
    except ValueError:
        return None


def _extract_docstring(
    source_file: str, source_location: str, symbol_label: str, repo_root: Path
) -> str:
    if not source_file.endswith(".py"):
        return DOCSTRING_GAP

    try:
        source_text = (repo_root / source_file).read_text(encoding="utf-8")
    except OSError:
        return DOCSTRING_GAP

    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return DOCSTRING_GAP

    normalized_label = _normalize_symbol_label(symbol_label)
    candidates = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name == normalized_label
    ]
    if not candidates:
        return DOCSTRING_GAP

    target_line = _parse_line_number(source_location)
    if len(candidates) > 1 and target_line is not None:
        match = min(candidates, key=lambda node: abs(node.lineno - target_line))
    else:
        match = candidates[0]

    docstring = ast.get_docstring(match)
    return docstring if docstring else DOCSTRING_GAP


def _associated_tests_for_module(source_file: str, repo_root: Path) -> list[str] | str:
    parts = PurePosixPath(source_file).parts
    if len(parts) < 2 or parts[0] != "src":
        return ASSOCIATED_TESTS_GAP

    module = parts[1]
    test_dir = repo_root / "tests" / "unit" / module
    matches = sorted(
        path.relative_to(repo_root).as_posix() for path in test_dir.glob("**/test_*.py")
    )
    return matches if matches else ASSOCIATED_TESTS_GAP


def build_records(graph_data: dict, admitted_edges: list[dict], repo_root: Path) -> list[dict]:
    node_by_id = {node["id"]: node for node in graph_data["nodes"]}

    node_ids: set[str] = set()
    for edge in admitted_edges:
        node_ids.add(edge["source"])
        node_ids.add(edge["target"])

    records = []
    for node_id in node_ids:
        node = node_by_id[node_id]
        records.append(
            {
                "id": node_id,
                "module": _module_from_source_file(node["source_file"]),
                "symbol": node["label"],
                "docstring": _extract_docstring(
                    node["source_file"], node["source_location"], node["label"], repo_root
                ),
                "owned_component": node["community"],
                "associated_tests": _associated_tests_for_module(node["source_file"], repo_root),
            }
        )

    records.sort(key=lambda record: record["id"])
    return records


def write_index(records: list[dict], output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, sort_keys=True, ensure_ascii=True, indent=2)


def build_index(graph_path: Path, output_path: Path | None, repo_root: Path) -> list[dict]:
    graph_data = load_graph(graph_path)
    admitted_edges = list(iter_admitted_edges(graph_data))
    records = build_records(graph_data, admitted_edges, repo_root)
    if output_path is not None:
        write_index(records, output_path)
    return records


def _build_adjacency(admitted_edges: list[dict]) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {}
    for edge in admitted_edges:
        source, target = edge["source"], edge["target"]
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)
    return adjacency


def query_by_path(
    records: list[dict],
    admitted_edges: list[dict],
    graph_data: dict,
    src_path: str,
    *,
    hops: int = 2,
    architectural_traversal: bool = False,
) -> list[dict]:
    node_by_id = {node["id"]: node for node in graph_data["nodes"]}
    seed_ids = {
        node["id"] for node in graph_data["nodes"] if node.get("source_file") == src_path
    }
    if not seed_ids:
        return []

    if architectural_traversal:
        seed_communities = {node_by_id[node_id]["community"] for node_id in seed_ids}
        return [record for record in records if record["owned_component"] in seed_communities]

    adjacency = _build_adjacency(admitted_edges)
    visited = set(seed_ids)
    frontier = set(seed_ids)
    for _ in range(hops):
        next_frontier: set[str] = set()
        for node_id in frontier:
            next_frontier |= adjacency.get(node_id, set())
        next_frontier -= visited
        if not next_frontier:
            break
        visited |= next_frontier
        frontier = next_frontier

    return [record for record in records if record["id"] in visited]


def _cmd_build(args: argparse.Namespace) -> None:
    records = build_index(Path(args.graph), Path(args.output), Path(args.repo_root))
    print(json.dumps({"record_count": len(records), "output": args.output}, sort_keys=True))


def _cmd_query(args: argparse.Namespace) -> None:
    repo_root = Path(args.repo_root)
    graph_data = load_graph(Path(args.graph))
    admitted_edges = list(iter_admitted_edges(graph_data))
    records = build_records(graph_data, admitted_edges, repo_root)
    result = query_by_path(
        records,
        admitted_edges,
        graph_data,
        args.path,
        hops=args.hops,
        architectural_traversal=args.architectural_traversal,
    )
    print(json.dumps(result, sort_keys=True, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="code_test_index")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--graph", required=True)
    build_parser.add_argument("--output", required=True)
    build_parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    build_parser.set_defaults(func=_cmd_build)

    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("--graph", required=True)
    query_parser.add_argument("--path", required=True)
    query_parser.add_argument("--hops", type=int, default=2)
    query_parser.add_argument("--architectural-traversal", action="store_true")
    query_parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    query_parser.set_defaults(func=_cmd_query)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
