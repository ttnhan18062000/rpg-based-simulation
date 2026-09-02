"""Shard-aware access to the 'tools' agent-monitoring source
(TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS).

TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC retired the single
agent-monitoring/tools.jsonl file in favor of weekly shards under
agent-monitoring/tools/tools-YYYY-Www.jsonl (plus a tools-unknown-week.jsonl fallback bucket for
rows whose week bucket could not be derived). The codex-runtime-activation
containment/rollback/provenance guardrails in this subsystem (tools/agent_codex_*,
tools/agent_replay_codex/, and their tests) still treat 'tools' as one logical monitoring source,
both against the real repo (sharded) and against synthetic scratch trees these packages' own
tests/fixtures build directly (a single literal tools.jsonl file — e.g.
tools/agent_codex_pilot_executor/simulation.py's _seed_monitoring). This module is the one place
that dual-shape logic lives, reused by every filesystem-based and tree-snapshot-based reader in
this subsystem instead of being duplicated at each site.

Every glob here is sorted() and never filters out tools-unknown-week.jsonl, matching the
migration's own convention (tools/agent-monitoring/manifest.py, generate_retro.py, validate.py).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

_TOOLS_SHARD_GLOB = "tools-*.jsonl"
_TREE_SHARD_DIR_PREFIX = "agent-monitoring/tools/"


def tools_source_paths(agent_monitoring_dir: Path) -> list[Path]:
    """Sorted, existing paths making up the 'tools' monitoring source.

    Real-repo shape: agent_monitoring_dir/tools/tools-*.jsonl (weekly shards). Scratch/legacy
    shape: a single agent_monitoring_dir/tools.jsonl file, still built directly by this
    subsystem's own synthetic fixtures.
    """
    shard_dir = agent_monitoring_dir / "tools"
    if shard_dir.is_dir():
        return sorted(shard_dir.glob(_TOOLS_SHARD_GLOB))
    single = agent_monitoring_dir / "tools.jsonl"
    return [single] if single.exists() else []


def read_tools_source_bytes(agent_monitoring_dir: Path) -> bytes:
    """Concatenated bytes of every 'tools' source file, in sorted-path order."""
    return b"".join(path.read_bytes() for path in tools_source_paths(agent_monitoring_dir))


def hash_tools_source(agent_monitoring_dir: Path) -> str:
    """sha256 hex digest over the concatenated 'tools' source bytes."""
    return hashlib.sha256(read_tools_source_bytes(agent_monitoring_dir)).hexdigest()


def resolve_tree_lines(tree: dict[str, bytes], name: str) -> list[bytes]:
    """Resolve one monitoring source's lines from a flat {relative_path: bytes} tree snapshot
    (e.g. tools/agent_codex_realrepo_pilot_harness/proofs.py's capture_tree() output), tolerating
    both tree shapes.

    Only 'tools.jsonl' is ever sharded: a tree captured from the real repo carries
    agent-monitoring/tools/tools-*.jsonl keys; a synthetic scratch tree built directly by a test
    or fixture (never through the real weekly-sharding migration) still carries a single literal
    agent-monitoring/tools.jsonl key. runs.jsonl/events.jsonl are always single-file in both
    shapes.
    """
    if name == "tools.jsonl":
        shard_keys = sorted(
            key
            for key in tree
            if key.startswith(_TREE_SHARD_DIR_PREFIX)
            and key.endswith(".jsonl")
            and Path(key).name.startswith("tools-")
        )
        if shard_keys:
            content = b"".join(tree[key] for key in shard_keys)
            return content.splitlines(keepends=True)
    return tree.get(f"agent-monitoring/{name}", b"").splitlines(keepends=True)
