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

`data_root`/`week_dir` is supplied by the caller and used as-is -- this module does not itself
resolve a relative root against the repo, so a CWD-relative `data_root` behaves exactly as CWD-
relative as it always would, silently returning `[]` from an unexpected CWD. Some real call sites
(`manifest.py`, `bash_command_mix.py`, `ingest.py`) anchor their own default to
`Path(__file__).resolve()...`; others (`record_events.py`, `done_checker_static.py`'s own several
`data_root: Path = Path("agent-monitoring/data")` defaults) deliberately stay CWD-relative, matching
this project's established convention that every real entry point (hooks, CLI scripts, pytest) runs
with CWD already at the repo root -- and, for `record_events.py` specifically, matching that
file's own test suite's `monkeypatch.chdir(tmp_path)`-based isolation strategy, which a `__file__`-
anchored absolute root would break. An earlier version of the `record_events.py` migration wrongly
claimed switching its literal from `Path(".").glob(...)` to `Path("agent-monitoring/data")` fixed
CWD-independence; it didn't (the two are behaviorally identical) -- corrected after review.
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
    second independent expression). Deterministic order -- canonical files first (sorted), then
    per-identifier files by week then filename -- not a single global sort across both groups, so
    a consumer that needs "canonical file last" or similar must not assume this is one flat sorted
    list. Returns an empty list if `data_root` doesn't exist or isn't a directory; never raises."""
    if not data_root.is_dir():
        return []
    return sorted(data_root.glob(f"*/{kind}.jsonl")) + [
        path
        for week_dir in sorted(p for p in data_root.iterdir() if p.is_dir())
        for path in per_identifier_shard_paths(week_dir, kind)
    ]
