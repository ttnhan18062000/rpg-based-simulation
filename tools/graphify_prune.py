"""Prune a graphify graph of nodes whose source file is gone (TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES).

`graphify update .` never drops a node whose `source_file` was deleted, so the graph only grows. This removes those
nodes, every link touching them, and their ids from hyperedge member lists, then reports the graph's size. Run it
from the MAIN checkout right after `graphify update .`; it refuses to write through a symlinked `graphify-out`
(a worktree's read-only view of the shared graph). Report-only conditions never fail the step (exit 0).

    python3 tools/graphify_prune.py [--graph graphify-out/graph.json] [--root DIR] [--dry-run] [--warn-mb 150]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_WARN_MB = 150


def _missing(node: dict, root: Path) -> bool:
    """A node is stale only when it names a string `source_file` that no longer exists under `root`."""
    src = node.get("source_file")
    return isinstance(src, str) and bool(src) and not (root / src).exists()


def prune(data: dict, root: Path) -> dict[str, int]:
    """Mutate `data` in place; returns the counts removed."""
    gone = {n["id"] for n in data.get("nodes", []) if isinstance(n, dict) and "id" in n and _missing(n, root)}
    counts = {"nodes": len(gone), "links": 0, "hyperedges": 0}
    if not gone:
        return counts
    data["nodes"] = [n for n in data["nodes"] if not (isinstance(n, dict) and n.get("id") in gone)]
    before = len(data.get("links", []))
    data["links"] = [e for e in data.get("links", []) if e.get("source") not in gone and e.get("target") not in gone]
    counts["links"] = before - len(data["links"])
    holders = [data] + ([data["graph"]] if isinstance(data.get("graph"), dict) else [])
    for holder in holders:
        dropped = 0
        kept = []
        for h in holder.get("hyperedges", []) or []:
            members = [m for m in h.get("nodes", []) if m not in gone]
            if len(members) < 2 <= len(h.get("nodes", [])):
                dropped += 1
                continue
            h["nodes"] = members
            kept.append(h)
        if "hyperedges" in holder:
            holder["hyperedges"] = kept
        counts["hyperedges"] = max(counts["hyperedges"], dropped)  # the same hyperedges may be listed in both places
    return counts


def _through_symlink(graph: Path) -> bool:
    """The graph file or its `graphify-out` directory is a symlink (a parent further up, such as `~/Working`, is fine)."""
    return graph.is_symlink() or graph.parent.is_symlink()


def _write_atomic(path: Path, data: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--graph", default="graphify-out/graph.json")
    ap.add_argument("--root", help="directory `source_file` is relative to (default: the parent of the graph's directory)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--warn-mb", type=float, default=DEFAULT_WARN_MB)
    a = ap.parse_args(argv)
    graph = Path(a.graph)
    if not graph.is_file():
        print(f"graphify_prune: no graph at {graph}; nothing to do")
        return 0
    root = Path(a.root) if a.root else graph.resolve().parent.parent
    try:
        data = json.loads(graph.read_text(encoding="utf-8"))
        counts = prune(data, root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"graphify_prune: could not read or prune {graph}: {exc}; graph left untouched")
        return 0
    removed = counts["nodes"] or counts["links"]
    if removed and a.dry_run:
        print("graphify_prune: dry run, nothing written")
    elif removed and _through_symlink(graph.absolute()):
        print("graphify_prune: graph is reached through a symlink (a worktree's view of the shared graph); "
              "not writing. Run this from the main checkout.")
    elif removed:
        _write_atomic(graph, data)
    verb = "would remove" if (a.dry_run or (removed and _through_symlink(graph.absolute()))) else "removed"
    print(f"graphify_prune: {verb} {counts['nodes']} nodes, {counts['links']} links, {counts['hyperedges']} hyperedges")
    size_mb = graph.stat().st_size / 1e6
    print(f"graphify_prune: {graph} {size_mb:.1f} MB (as on disk), {len(data['nodes'])} nodes, {len(data['links'])} links after pruning")
    if size_mb > a.warn_mb:
        print(f"graphify_prune: WARNING graph is above {a.warn_mb:g} MB; a query will be slow and memory-hungry "
              "(check .graphifyignore for bulky untracked folders)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
