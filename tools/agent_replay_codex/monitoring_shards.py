"""Shard-aware access to all 3 agent-monitoring sources (runs/events/tools)
(TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION).

TCK-20260903-MONITORING-DATA-MIGRATION retired the per-source top-level files
(agent-monitoring/{runs,events,tools}.jsonl) and the prior tools-only
agent-monitoring/tools/tools-YYYY-Www.jsonl shard directory in favor of one unified layout:
agent-monitoring/data/<week>/<source>.jsonl for every one of the 3 sources
("runs.jsonl" | "events.jsonl" | "tools.jsonl"), plus an agent-monitoring/data/unknown-week/
fallback bucket for rows whose week bucket could not be derived. The codex-runtime-activation
containment/rollback/provenance guardrails in this subsystem (tools/agent_codex_*,
tools/agent_replay_codex/, and their tests) treat each of the 3 sources as one logical monitoring
stream, both against the real repo (sharded per week) and against synthetic scratch trees these
packages' own tests/fixtures build directly (a single literal <source>.jsonl file — e.g.
tools/agent_codex_pilot_executor/simulation.py's _seed_monitoring). This module is the one place
that dual-shape logic lives, reused by every filesystem-based and tree-snapshot-based reader in
this subsystem instead of being duplicated at each site.

Every glob here is sorted() and never filters out the unknown-week fallback bucket, matching the
migration's own convention (tools/agent-monitoring/manifest.py, generate_retro.py, validate.py).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

_DATA_DIR_NAME = "data"
_TREE_DATA_DIR_PREFIX = "agent-monitoring/data/"


def source_paths(agent_monitoring_dir: Path, source: str) -> list[Path]:
    """Sorted, existing paths making up one monitoring source ('runs.jsonl' | 'events.jsonl' |
    'tools.jsonl').

    Real-repo shape: agent_monitoring_dir/data/<week>/<source> for every week folder (including
    the 'unknown-week' fallback bucket), sorted lexicographically by full path (weeks sort before
    'unknown-week' since '2' < 'u'). Scratch/legacy shape: a single agent_monitoring_dir/<source>
    file, still built directly by this subsystem's own synthetic fixtures (e.g.
    tools/agent_codex_pilot_executor/simulation.py::_seed_monitoring).
    """
    data_dir = agent_monitoring_dir / _DATA_DIR_NAME
    if data_dir.is_dir():
        return sorted(data_dir.glob(f"*/{source}"))
    single = agent_monitoring_dir / source
    return [single] if single.exists() else []


def read_source_bytes(agent_monitoring_dir: Path, source: str) -> bytes:
    """Concatenated bytes of every file making up one monitoring source, in sorted-path order."""
    return b"".join(path.read_bytes() for path in source_paths(agent_monitoring_dir, source))


def hash_source(agent_monitoring_dir: Path, source: str) -> str:
    """sha256 hex digest over the concatenated source bytes."""
    return hashlib.sha256(read_source_bytes(agent_monitoring_dir, source)).hexdigest()


def resolve_tree_lines(tree: dict[str, bytes], name: str) -> list[bytes]:
    """Resolve one monitoring source's lines from a flat {relative_path: bytes} tree snapshot
    (e.g. tools/agent_codex_realrepo_pilot_harness/proofs.py's capture_tree() output), tolerating
    both tree shapes.

    Real-repo shape: a tree captured from the real repo carries agent-monitoring/data/<week>/<name>
    keys for every week (sorted by full key, matching source_paths' ordering). Scratch shape: a
    synthetic tree built directly by a test or fixture (never through the real weekly migration)
    carries a single literal agent-monitoring/<name> key.
    """
    shard_keys = sorted(
        key for key in tree
        if key.startswith(_TREE_DATA_DIR_PREFIX) and key.endswith(f"/{name}")
    )
    if shard_keys:
        content = b"".join(tree[key] for key in shard_keys)
        return content.splitlines(keepends=True)
    return tree.get(f"agent-monitoring/{name}", b"").splitlines(keepends=True)
