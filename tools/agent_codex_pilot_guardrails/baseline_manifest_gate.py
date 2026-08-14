"""Pre/post baseline-manifest fail-closed gate (TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 4).

Wraps tools/agent-monitoring/manifest.py's capture_lines/assert_prefix_preserved unmodified —
loaded via importlib.util.spec_from_file_location (mirroring
tools/agent_replay_codex/containment.py's own precedent) since tools/agent-monitoring has a
hyphen in its directory name and cannot be imported via a dotted path.

assert_prefix_preserved, not a naive whole-file hash-diff, is the correct interpretation of AC #4's
"fails closed if any pre-existing line's hash changes": a legitimate pilot run appends new lines to
agent-monitoring/*.jsonl between the pre- and post-snapshot, which necessarily changes any naive
whole-file SHA-256 (manifest.py's build_manifest() hash field) even when nothing pre-existing was
touched — a literal whole-file-hash-equality gate would falsely reject every successful pilot run.
assert_prefix_preserved is therefore not a looser substitute for "hash changes" but the stricter,
mechanically correct implementation of the AC's intent (reject rewrite/reorder/deletion of
anything pre-existing; tolerate only new appended lines).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from .errors import PilotManifestDriftError

_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "agent-monitoring" / "manifest.py"
_MANIFEST_SPEC = importlib.util.spec_from_file_location(
    "agent_codex_pilot_guardrails_baseline_manifest", _MANIFEST_PATH
)
_manifest = importlib.util.module_from_spec(_MANIFEST_SPEC)
_MANIFEST_SPEC.loader.exec_module(_manifest)


def capture_pilot_baseline(agent_monitoring_dir: Path) -> dict[str, list[str]]:
    return _manifest.capture_lines(agent_monitoring_dir)


def assert_pilot_baseline_preserved(pre: dict[str, list[str]], post: dict[str, list[str]]) -> None:
    try:
        _manifest.assert_prefix_preserved(pre, post)
    except AssertionError as exc:
        raise PilotManifestDriftError(str(exc)) from exc
