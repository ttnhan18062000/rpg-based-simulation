---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260824-HOTFIX-FINALIZE-INCOMPLETE-LINE-DRIFT
phase: done
date: 2026-08-24
tags: [testing, ai]
---

# TCK-20260824-HOTFIX-FINALIZE-INCOMPLETE-LINE-DRIFT

## Title
Update FINALIZE_INCOMPLETE call-site line-number baseline after TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE's own +23-line diff to implement-ticket.js

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`'s own real, legitimate `.claude/workflows/implement-ticket.js` diff (+23 lines, adding the per-session-scoped sidecar write to `writeSidecar()` and the Scope-phase resume branch) shifted every line after the edit point downward, including the two `FINALIZE_INCOMPLETE` terminal-status call sites two tests hardcode by exact line number. CI's "Agent orchestration / codex / replay" job failed on the resulting PR (#68) with `assert [1546, 1558] == [1529, 1541]`. This is a known, already-documented recurring drift pattern in this exact repo — the immediately-prior merged PR (#66, `TCK-20260824-PARITY-NEXT-ID-LOOKUP`) hit and fixed the identical class of failure for the identical two tests after its own +22-line diff to the same file (that PR's own commit message: "Test phase found and fixed a real regression: this ticket's +22-line diff shifted FINALIZE_INCOMPLETE's call-site line numbers..."). This ticket applies the same fix again: update the two hardcoded `[1529, 1541]` literals to the real current `[1546, 1558]`, verified directly against the live file, not guessed.

## Scope
- Update `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py:69`'s hardcoded `[1529, 1541]` to the real, live-verified `[1546, 1558]`.
- Update `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py:101`'s identical hardcoded literal to match.
- Verify both real call sites in `.claude/workflows/implement-ticket.js` are genuinely at lines 1546 and 1558 (the `await writeMonitoring('FINALIZE_INCOMPLETE')` call sites) before writing the new literals — confirmed via direct `grep -n` against the live file, not assumed from the CI log alone.

## Out of Scope
- Any change to `.claude/workflows/implement-ticket.js` itself — this ticket only updates the two tests' stale baseline; the shift is a legitimate, already-landed side effect of `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`'s real diff, not a defect to fix in the workflow file.
- Redesigning these two tests to be line-number-independent (e.g. matching by containing-function name instead of literal line number) — a real, discussable structural improvement, but out of scope for a hotfix whose job is to restore a passing CI, not to change the tests' own design philosophy. Flagged here for a future ticket if this recurring drift pattern (now seen at least twice) is judged worth addressing structurally.

## Acceptance Criteria
- [x] `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py::test_terminal_status_conformance_finalize_incomplete_appears_once_on_both_sides` passes against the real current `implement-ticket.js`.
- [x] `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py::test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count` passes against the real current `implement-ticket.js`.
- [x] No file other than the two test files above is modified by this ticket.
- [x] The full `agent_orchestration_claude_adapter` + `agent_orchestration` test directories re-run clean (not just the 2 previously-failing tests in isolation), confirming no other test in that surface hardcodes a now-stale line number this same diff might have also shifted.

## Related Tickets
- TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE (the diff that caused this drift)
- TCK-20260824-PARITY-NEXT-ID-LOOKUP (the immediately-prior ticket that hit and fixed the identical drift pattern for the identical two tests)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix — no staging artifacts).

## Related Code Areas
- `.claude/workflows/implement-ticket.js` (read-only reference; not modified by this ticket)
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py`

## Assumptions / Open Questions
None remaining — real current line numbers independently confirmed via `grep -n "FINALIZE_INCOMPLETE" .claude/workflows/implement-ticket.js` against the live worktree file before editing either test.

## Implementation Notes
Confirmed real current call sites via `grep -n "FINALIZE_INCOMPLETE" .claude/workflows/implement-ticket.js`: lines 1546 and 1558 (both `await writeMonitoring('FINALIZE_INCOMPLETE')` calls), matching exactly what CI's own failure output reported (`[1546, 1558]`) — not a coincidence, confirms the diagnosis. Updated both test files' hardcoded `[1529, 1541]` literal to `[1546, 1558]`. No other file touched.

## Test Summary
`pytest tests/agent_orchestration_claude_adapter tests/agent_orchestration -m "not slow and not extra_slow" -q` — all pass (0 failed), including both previously-failing tests. Full CI-equivalent scope for the failing job (`tests/agent_codex_live_transport tests/agent_codex_pilot_executor tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_orchestration tests/agent_codex_posttool_adapter tests/agent_codex_realrepo_pilot_harness tests/agent_codex_runtime_shadow tests/agent_orchestration tests/agent_orchestration_claude_adapter tests/agent_orchestration_codex_adapter tests/agent_replay tests/agent_replay_codex -m "not slow and not extra_slow"`) re-run in full, matching the CI job's own exact scope.

## Files Changed
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py`

## Completion Summary
Updated the two tests' hardcoded `FINALIZE_INCOMPLETE` call-site line-number baseline from the now-stale `[1529, 1541]` to the real, live-verified `[1546, 1558]`, restoring the exact expected class of drift `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`'s own legitimate +23-line diff to `.claude/workflows/implement-ticket.js` caused — the same drift pattern the immediately-prior `TCK-20260824-PARITY-NEXT-ID-LOOKUP` ticket already hit and fixed once for these identical two tests. No source/workflow file touched; fix is test-only.
