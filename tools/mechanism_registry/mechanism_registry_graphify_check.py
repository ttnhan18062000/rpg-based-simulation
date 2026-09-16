#!/usr/bin/env python3
"""
Report-only graphify cross-check for docs/brainstorm/mechanisms.yaml's `depends_on` edges.

TCK-20260915-MECHANISM-REGISTRY-FOUNDATION Scope item 5: "flag any declared depends_on edge with
no supporting call/import path as suspicious. Report, never fail: graphify's graph is advisory
here."

Per staging_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md's own feasibility
finding: a bare "does *any* path exist" check is unreliable at this codebase's scale -- unrelated
services route through near-universal hub types (EntityState, StateUpdate) within a handful of
hops, so a naive reachability check would essentially never flag anything. This script is the
deliberately conservative first version that finding recommends:

  - Loads graphify-out/graph.json directly (not `graphify path` per edge -- 105k+ edges is too
    many for repeated subprocess calls).
  - Only counts edges whose `relation` implies a real call/import/use -- never `contains` (a file
    containing a symbol is not evidence of a cross-mechanism dependency).
  - Matches each mechanism id to graph nodes via a conservative token-subset heuristic (mechanism
    ids are snake_case registry ids, not code symbol names, so this is inherently approximate) --
    a mechanism id with no plausible node match is reported as `no_match`, not `FAIL`.
  - Bounded-hop BFS (default 3 hops) between the two mechanisms' matched nodes.
  - **Never fails the build.** Always exits 0; prints a report. This is advisory output, not a gate.

This intentionally does NOT implement the hub-node-exclusion refinement investigation.md flags as
future work (excluding/down-weighting near-universal types like EntityState so a path routed
through one doesn't count as "supported") -- shipping the conservative version now beats not
shipping the report-only check Scope item 5 asks for; a noisy `suspicious` bucket in practice is
the signal that refinement is worth building next, not a reason to withhold this first pass.

Usage:
  python3 tools/mechanism_registry/mechanism_registry_graphify_check.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REGISTRY_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"
_GRAPH_PATH = _REPO_ROOT / "graphify-out" / "graph.json"

# Relations that plausibly represent a real call/import/use relationship. Deliberately excludes
# "contains" (investigation.md's own confirmed false-positive source), "method" (structural, not
# cross-symbol), "inherits"/"re_exports"/"rationale_for" (not a runtime dependency signal).
_REAL_RELATIONS = frozenset({"uses", "calls", "imports", "imports_from", "references"})

_MAX_HOPS = 3
_MAX_MATCHED_NODES_PER_MECHANISM = 5


def _load_registry() -> dict:
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_graph() -> dict:
    with open(_GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _match_nodes(mechanism_id: str, nodes: List[dict]) -> List[str]:
    """Best-effort match: a node whose label (lowercased, non-alnum stripped) contains every
    underscore-separated token of the mechanism id. Prefers non-test source files, capped to
    avoid an unbounded BFS fan-out for a generic id."""
    tokens = [t for t in mechanism_id.split("_") if t]
    matches = []
    for node in nodes:
        label = (node.get("label") or "").lower()
        if all(tok in label for tok in tokens):
            matches.append(node)
    # Prefer non-test, src/-rooted matches first.
    matches.sort(key=lambda n: (0 if (n.get("source_file") or "").startswith("src/") else 1,
                                 "test" in (n.get("source_file") or "").lower()))
    return [m["id"] for m in matches[:_MAX_MATCHED_NODES_PER_MECHANISM]]


def _build_adjacency(links: List[dict]) -> Dict[str, Set[str]]:
    adj: Dict[str, Set[str]] = defaultdict(set)
    for link in links:
        if link.get("relation") in _REAL_RELATIONS:
            adj[link["source"]].add(link["target"])
            # Treat as undirected for reachability purposes -- a "uses" edge either direction is
            # still real evidence two symbols are connected, and dependency direction in the
            # registry doesn't necessarily match the code's own caller/callee direction.
            adj[link["target"]].add(link["source"])
    return adj


def _bfs_reachable(start_ids: List[str], goal_ids: Set[str], adj: Dict[str, Set[str]], max_hops: int) -> bool:
    if not start_ids or not goal_ids:
        return False
    visited = set(start_ids)
    frontier = deque((s, 0) for s in start_ids)
    while frontier:
        node, depth = frontier.popleft()
        if node in goal_ids:
            return True
        if depth >= max_hops:
            continue
        for neighbor in adj.get(node, ()):
            if neighbor not in visited:
                visited.add(neighbor)
                frontier.append((neighbor, depth + 1))
    return False


def check(registry: Optional[dict] = None, graph: Optional[dict] = None) -> dict:
    """Returns {"supported": [...], "suspicious": [...], "no_match": [...], "graph_unavailable":
    bool} of (from_id, to_id) pairs. Never raises for a business-logic finding -- only a
    structurally malformed input.

    `graphify-out/` is gitignored (not committed) -- it exists locally wherever `graphify update`
    has been run, but not on a fresh CI checkout. Scope item 5's own contract is "Report, never
    fail: graphify's 35k-node graph is advisory here" -- a missing graph is exactly the kind of
    thing this check must survive, not crash on. When the graph file can't be found, this returns
    empty buckets with `graph_unavailable: True` rather than raising, so `main()` can report the
    graph was skipped instead of treating a normal, expected local/CI difference as a failure.
    """
    registry = registry if registry is not None else _load_registry()
    if graph is None:
        try:
            graph = _load_graph()
        except FileNotFoundError:
            return {"supported": [], "suspicious": [], "no_match": [], "graph_unavailable": True}

    nodes = graph.get("nodes", [])
    adj = _build_adjacency(graph.get("links", []))

    node_cache: Dict[str, List[str]] = {}

    def matched(mech_id: str) -> List[str]:
        if mech_id not in node_cache:
            node_cache[mech_id] = _match_nodes(mech_id, nodes)
        return node_cache[mech_id]

    result = {"supported": [], "suspicious": [], "no_match": [], "graph_unavailable": False}
    for mechanism in registry.get("mechanisms", []):
        mech_id = mechanism.get("id")
        for dep_id in mechanism.get("depends_on") or []:
            from_nodes = matched(mech_id)
            to_nodes = matched(dep_id)
            if not from_nodes or not to_nodes:
                result["no_match"].append((mech_id, dep_id))
                continue
            if _bfs_reachable(from_nodes, set(to_nodes), adj, _MAX_HOPS):
                result["supported"].append((mech_id, dep_id))
            else:
                result["suspicious"].append((mech_id, dep_id))
    return result


def main() -> int:
    result = check()
    if result.get("graph_unavailable"):
        print("Graphify cross-check (report-only, never fails): SKIPPED -- "
              f"{_GRAPH_PATH} not found. graphify-out/ is gitignored, not committed; run "
              "`graphify update .` locally to populate it. Not present on a fresh CI checkout, "
              "which is expected, not a failure.")
        return 0
    total = len(result["supported"]) + len(result["suspicious"]) + len(result["no_match"])
    print(f"Graphify cross-check (report-only, never fails): {total} depends_on edges checked")
    print(f"  supported:  {len(result['supported'])}")
    print(f"  suspicious: {len(result['suspicious'])}")
    print(f"  no_match:   {len(result['no_match'])}")
    if result["suspicious"]:
        print("\nSuspicious edges (no supporting call/import path found within "
              f"{_MAX_HOPS} hops):")
        for from_id, to_id in result["suspicious"]:
            print(f"  {from_id} -> {to_id}")
    if result["no_match"]:
        print("\nNo graph-node match found (not itself a defect signal -- mechanism ids are "
              "hand-authored, graph nodes are code symbols):")
        for from_id, to_id in result["no_match"]:
            print(f"  {from_id} -> {to_id}")
    return 0  # Always 0 -- this check never fails the build.


if __name__ == "__main__":
    sys.exit(main())
