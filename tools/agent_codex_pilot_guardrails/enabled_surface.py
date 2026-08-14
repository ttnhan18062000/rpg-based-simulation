"""Enabled hook-event/writer-function evidenced-subset guard
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 3).

Restricts the pilot's enabled surface to only the hook events and writer functions already
proven safe by CODEX-GUIDANCE-FIXTURE-CAPTURE (Phase 2, the only hook event ever fixture-captured
for Codex is PostToolUse) and MONITORING-WRITER-UNIFICATION (Phase 3, the only proven writer is
tools/agent-monitoring/writer.py's write_line/write_lines pair). Sourced from the investigation's
direct-read trace, not re-derived at runtime, since no existing file declares the *evidenced* (as
opposed to *schema-valid*) subset in one place.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from .errors import EnabledSurfaceExceedsEvidenceError

EVIDENCED_HOOK_EVENTS: frozenset[str] = frozenset({"PostToolUse"})
EVIDENCED_WRITER_FUNCTIONS: frozenset[str] = frozenset({"write_line", "write_lines"})

_HOOK_EVENTS_YAML_PATH = (
    Path(__file__).resolve().parent.parent.parent / "agent-orchestration" / "hook-events.yaml"
)


def assert_evidenced_events_are_schema_valid(
    hook_events_yaml_path: Path = _HOOK_EVENTS_YAML_PATH,
) -> None:
    """Cross-check EVIDENCED_HOOK_EVENTS against the broader schema-declared vocabulary in
    agent-orchestration/hook-events.yaml (which also includes PreToolUse, never fixture-captured
    for Codex) — without conflating "schema-valid" with "evidenced."
    """
    with open(hook_events_yaml_path, "r", encoding="utf-8") as f:
        contract = yaml.safe_load(f)
    schema_valid_ids = {entry["id"] for entry in contract["hook_types"]}
    missing = EVIDENCED_HOOK_EVENTS - schema_valid_ids
    if missing:
        raise EnabledSurfaceExceedsEvidenceError(
            f"EVIDENCED_HOOK_EVENTS contains ids not declared in {hook_events_yaml_path}: {missing}"
        )


def assert_enabled_surface_subset(
    enabled_hook_events: frozenset[str], enabled_writer_names: frozenset[str]
) -> None:
    """Raise EnabledSurfaceExceedsEvidenceError unless both arguments are subsets of the
    corresponding evidenced constant."""
    if not enabled_hook_events <= EVIDENCED_HOOK_EVENTS:
        raise EnabledSurfaceExceedsEvidenceError(
            f"enabled_hook_events {sorted(enabled_hook_events)} exceeds evidenced set "
            f"{sorted(EVIDENCED_HOOK_EVENTS)}"
        )
    if not enabled_writer_names <= EVIDENCED_WRITER_FUNCTIONS:
        raise EnabledSurfaceExceedsEvidenceError(
            f"enabled_writer_names {sorted(enabled_writer_names)} exceeds evidenced set "
            f"{sorted(EVIDENCED_WRITER_FUNCTIONS)}"
        )
