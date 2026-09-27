"""Single source of truth for "which files could hold real <kind> data" across every naming shape
this repo's monitoring shards have used (TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION).

Mirrors `monitoring_batch_identifier.py`'s write-side consolidation, for the read side --
`TCK-20260925-MONITORING-STALE-READ-PATH-SWEEP` found and fixed 12 independent, narrow glob
call sites across 11 files that had never been widened from the bare per-week canonical shape
(`data/<week>/<kind>.jsonl`) to also match the per-identifier shape (`data/<week>/<id>.<kind>.jsonl`
-- per-ticket, historically; per-PR/branch, since `TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX`),
and explicitly deferred consolidating them into one function. This module is that consolidation.

Lives here rather than in `monitoring_batch_identifier.py` -- that module's own scope is narrowly
"what identifier does this one write/read belong to" (git-branch/PR resolution with its own
detached-HEAD/sidecar fallback chain), unrelated to glob mechanics. This module's callers span a
much wider footprint (`tools/gate_checks/`, `tools/agent_replay_codex/`, `tools/agent-monitoring/`
itself, and `src/api/agent_ops_dashboard/`, which already reaches across into `tools/` for exactly
this reason) -- a new, narrowly-scoped sibling module matches that existing precedent rather than
deepening `monitoring_batch_identifier.py`'s own more specific responsibility.

`data_root`/`week_dir` must always be a real, resolvable `Path` -- never assume the caller's
current working directory is the repo root (see `record_events.py`'s own historical `Path(".")`
hazard, fixed by migrating onto this module rather than ported forward).
"""
from __future__ import annotations

from pathlib import Path


def per_identifier_shard_paths(week_dir: Path, kind: str) -> list[Path]:
    """Every per-identifier `<id>.<kind>.jsonl` file in one week directory, excluding the bare
    canonical file -- the narrower question a consolidator needs (which files to fold INTO the
    canonical file, never the canonical file itself), not the full read picture `shard_paths()`
    answers below."""
    return sorted(week_dir.glob(f"*.{kind}.jsonl"))


def shard_paths(data_root: Path, kind: str) -> list[Path]:
    """Every path that could hold real `<kind>` data across every week directory under
    `data_root`: the bare per-week canonical file (`<week>/<kind>.jsonl`) and every per-identifier
    file (`<week>/<id>.<kind>.jsonl`, via `per_identifier_shard_paths()` -- one glob call, not a
    second independent expression). Sorted for determinism. Returns an empty list if `data_root`
    doesn't exist; never raises."""
    if not data_root.exists():
        return []
    return sorted(data_root.glob(f"*/{kind}.jsonl")) + [
        path
        for week_dir in sorted(p for p in data_root.iterdir() if p.is_dir())
        for path in per_identifier_shard_paths(week_dir, kind)
    ]
