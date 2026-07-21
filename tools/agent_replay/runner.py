"""Replay runner for the `implement-ticket` workflow's Scope -> Investigate -> Plan -> Review slice.

Built for TCK-20260721-CODEX-REPLAY-PROOF. `replay_slice()` re-executes the deterministic half of
`.claude/workflows/implement-ticket.js`'s Scope/Plan/Review gate branches against a loaded fixture
(see `tools/agent_replay/fixture_envelope.py`), calling the SAME real, already-tested Python
functions the live orchestrator calls (`tag_registry.check_tags_registered`,
`gate_checks.plan_gate_static.plan_has_unresolved_questions_heading`) — imported read-only, never
modified. The outer branch-sequencing decisions themselves (which `implement-ticket.js` line ranges
they mirror) have no separate importable module to call, so they are hand-mirrored here, 1-3 lines
each, following the exact `classifyChecklistFailure` "kept in sync by hand" precedent
`implement-ticket.js` itself already documents:

  - Scope conflicts block (`implement-ticket.js` around line 369):
    `if (ticketInfo.conflicts.length > 0) return CONFLICTS_DETECTED`
  - Scope tag-check branch (line 381): `if (unregisteredTags.length > 0) return TAGS_NOT_REGISTERED`
  - Plan unresolved-questions branch (line 517): `if (hasUnresolvedQuestions) return NEEDS_HUMAN_INPUT`
  - Review verdict branch (line 576): `if (review.verdict !== 'APPROVED') return <verdict>`

Unconditional containment law (see docs/ai/replay_fixture_spec.md, which names the four forbidden
scripts under tools/agent-monitoring/ in full): this module must never subprocess or import any of
those four scripts, under any condition. `_fake_write_monitoring` and `_fake_hook_boundary` are
pure in-memory no-ops standing in for those call sites — they perform no I/O to
`agent-monitoring/*.jsonl` or any `.claude/` sidecar file. This file deliberately never spells out
those four scripts' literal filenames anywhere in its own source (not even in a comment) — see
tests/agent_replay/test_runner_no_forbidden_calls.py's whole-file string-constant scan, which
checks every string literal in this package, not just call-argument-scoped ones.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from .fixture_envelope import FixtureEnvelope

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.plan_gate_static import plan_has_unresolved_questions_heading  # noqa: E402
from tag_registry import check_tags_registered  # noqa: E402


@dataclass(frozen=True)
class ReplayOutcome:
    final_status: str
    phases_completed: list[str] = field(default_factory=list)


def _fake_write_monitoring(final_status: str) -> dict:
    """In-memory stand-in for implement-ticket.js's writeMonitoring(). Performs no I/O to
    agent-monitoring/runs.jsonl, agent-monitoring/events.jsonl, or any .claude/ sidecar file —
    ever, regardless of cwd."""
    return {"status": "fake-recorded", "final_status": final_status}


def _fake_hook_boundary(event_name: str) -> None:
    """In-memory stand-in for the pre/post-tool-hook sidecar boundary. No-op — writes nothing."""
    return None


def replay_slice(fixture: FixtureEnvelope) -> ReplayOutcome:
    """Re-execute the Scope -> Investigate -> Plan -> Review slice against a loaded fixture.

    Stops at the first non-`ok` transition and returns that phase's outcome as `final_status`,
    calling `_fake_write_monitoring` exactly once — mirroring the real orchestrator's
    one-writeMonitoring-call-per-early-return shape.
    """
    phases_completed: list[str] = []

    for entry in fixture.phases:
        _fake_hook_boundary(f"{entry.phase}:start")

        if entry.phase == "Scope":
            conflicts = entry.input.get("conflicts", [])
            if conflicts:
                _fake_write_monitoring("CONFLICTS_DETECTED")
                return ReplayOutcome(final_status="CONFLICTS_DETECTED", phases_completed=phases_completed)
            unregistered_tags = check_tags_registered(entry.input.get("tags", []))
            if unregistered_tags:
                _fake_write_monitoring("TAGS_NOT_REGISTERED")
                return ReplayOutcome(final_status="TAGS_NOT_REGISTERED", phases_completed=phases_completed)

        elif entry.phase == "Investigate":
            pass  # no deterministic gate check exists at this phase in the real orchestrator

        elif entry.phase == "Plan":
            plan_path = entry.input["plan_path"]
            if plan_has_unresolved_questions_heading(plan_path):
                _fake_write_monitoring("NEEDS_HUMAN_INPUT")
                return ReplayOutcome(final_status="NEEDS_HUMAN_INPUT", phases_completed=phases_completed)

        elif entry.phase == "Review":
            verdict = entry.output.get("verdict")
            if verdict != "APPROVED":
                _fake_write_monitoring(verdict)
                return ReplayOutcome(final_status=verdict, phases_completed=phases_completed)

        phases_completed.append(entry.phase)

    _fake_write_monitoring("ok")
    return ReplayOutcome(final_status="ok", phases_completed=phases_completed)
