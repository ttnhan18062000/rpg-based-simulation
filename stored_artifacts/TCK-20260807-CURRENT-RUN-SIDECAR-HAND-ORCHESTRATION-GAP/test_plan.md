---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP
artifact_type: test_plan
tags: [agent-monitoring, process-improvement, hooks]
---

# Test Plan — TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP

## Scope of verification

This is a `.claude/settings.json` hook-configuration change plus a skill-doc prose change — no new Python module. Per investigation.md, the two precedent PreToolUse hooks (grep-nudge, context-search-nudge) have no dedicated pytest coverage; this ticket's new hook inherits the same status, not a gap to invent new infrastructure for.

## Verification steps

1. **JSON validity**: `python3 -m json.tool .claude/settings.json` must succeed after the edit (a malformed hooks block would silently break ALL hooks, not just the new one — real regression risk).
2. **Manual real-kernel-adjacent check** (the ticket's own AC #3, "a fresh hand-orchestrated ticket run... shows non-null run_id/seq"): this session's own remaining 4 tickets (PARITY-WRITE-SAFETY-METRIC-RESCOPE, DOC-UPDATER-FIRST-ATTEMPT-BLOCKED-RATE, SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP, SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION) are the real-world test: the sidecar is being written manually and correctly at each phase transition throughout this session per the existing memory-note discipline, so `tools.jsonl` rows for those runs should show non-null `run_id`. Additionally, confirm the new hook's own `additionalContext` string is syntactically valid JSON by running the shell snippet standalone against a synthetic `tool_input` payload.
3. **No existing test regression**: `pytest tests/tools/test_post_tool_hook.py tests/tools/test_codex_hook_payload_fixture.py -q` — confirms the unrelated existing hook-adjacent tests still pass (nothing in this change touches `post_tool_hook.py` itself, but it's the closest existing scoped test surface).
4. **Skill-doc conformance**: `pytest tests/tools/test_workflow_meta_conformance.py -q` — confirms the SKILL.md edit (adding an explicit writeSidecar row) doesn't break the existing `check_skill_doc_covers_meta_phases()` check.

## Out of scope for testing

- No new unit tests for the hook's shell logic (matches precedent — see investigation.md).
- No backfill verification (ticket explicitly forbids backfilling historical null rows).
