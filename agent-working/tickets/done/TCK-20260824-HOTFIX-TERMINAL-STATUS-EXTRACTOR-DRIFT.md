---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260824-HOTFIX-TERMINAL-STATUS-EXTRACTOR-DRIFT
phase: done
date: 2026-08-24
tags: [testing, bug]
---

# TCK-20260824-HOTFIX-TERMINAL-STATUS-EXTRACTOR-DRIFT

## Title
Fix hardcoded `FINALIZE_INCOMPLETE` call-site baseline drift in `test_terminal_status_extractor.py` (sibling of the fix already applied to `test_terminal_status_conformance.py`)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI on PR #64, job "Agent orchestration / codex / replay", is currently red:
`tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py::test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count`
asserts (line 101) `by_value["FINALIZE_INCOMPLETE"]["call_sites"] == [1498, 1510]`. The real,
current value — independently re-confirmed in this scoping session by calling the live extractor
directly (`tools.agent_orchestration_claude_adapter.terminal_status_extractor.extract_all_terminal_statuses`
against `.claude/workflows/implement-ticket.js`) — is `[1507, 1519]`.

This is the exact same +9-line hardcoded-baseline drift already fixed once this session in a
sibling test file: `TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT`'s own Deviation note (see its
"Files Changed" / "Deviation from original scope" sections) fixed the identical
`[1498, 1510]` → `[1507, 1519]` assertion in
`tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py:69`, caused directly
by that ticket's own +9-line diff to `implement-ticket.js` landing above the `FINALIZE_INCOMPLETE`
call sites. That ticket's own test-scoper mapping ran the conformance test file but missed this
second, sibling test file, which asserts the identical fact (the `FINALIZE_INCOMPLETE` call-site
line-number pair) via a different call path: `test_terminal_status_extractor.py` calls
`extract_all_terminal_statuses()` directly, while `test_terminal_status_conformance.py` exercises
it via the higher-level conformance check. Both hardcode the same call-site pair for the same
reason and drifted identically from the same root diff.

Local repro (the exact command the "Agent orchestration / codex / replay" CI job runs):
`.venv/bin/python3 -m pytest tests/agent_codex_live_transport tests/agent_codex_pilot_executor
tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_orchestration
tests/agent_codex_posttool_adapter tests/agent_codex_realrepo_pilot_harness
tests/agent_codex_runtime_shadow tests/agent_orchestration tests/agent_orchestration_claude_adapter
tests/agent_orchestration_codex_adapter tests/agent_replay tests/agent_replay_codex -m "not slow
and not extra_slow" --tb=short -q` → 1 failed, 384 passed, 5 skipped. The single failure is exactly
this baseline assertion.

This is the third occurrence of this exact drift pattern this cycle: `TCK-20260817-HOTFIX-TERMINAL-STATUS-STALE-LINE-NUMBERS`
and `TCK-20260818-HOTFIX-TERMINAL-STATUS-CONTRACT-DRIFT` both previously fixed the same class of
stale-line-number drift across these same two test files.

## Scope
- Update the single hardcoded assertion at
  `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py:101` from
  `by_value["FINALIZE_INCOMPLETE"]["call_sites"] == [1498, 1510]` to
  `== [1507, 1519]`.
- Before editing, re-verify the real current value directly via the live extractor
  (`extract_all_terminal_statuses(Path(".claude/workflows/implement-ticket.js"))`) rather than
  trusting this ticket's own citation of `[1507, 1519]` as gospel — the file may have drifted again
  between this scoping session and implementation.
- Re-run the exact CI repro command (see Request Summary) to confirm the full scoped test set is
  green after the fix.

## Out of Scope
- Any change to `.claude/workflows/implement-ticket.js` itself — the call sites are correct as-is;
  only the test's hardcoded expectation is stale.
- Any change to `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py` —
  already fixed by `TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT`; re-verify it's still green as a
  sanity check but do not re-edit it absent a new, independently-confirmed drift.
- Any change to the terminal-status vocabulary itself (adding/removing a literal, verdict-derived,
  or bypass status) — this ticket is a pure baseline-number correction, not a contract change.
- Re-architecting the hardcoded-line-number test pattern (e.g. switching to a line-number-agnostic
  assertion) to prevent future recurrences of this drift class — worth a future process ticket, but
  out of scope here; this ticket fixes the current red CI only.
- `TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT`'s own scope (the `conflicts`/`related_context`
  schema split) — already done; not reopened by this ticket.

## Acceptance Criteria
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py:101` asserts
  `by_value["FINALIZE_INCOMPLETE"]["call_sites"] == [1507, 1519]` (or whatever value is
  independently re-confirmed live at implementation time, if it has drifted again).
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py` passes in full,
  locally.
- The full CI-job repro command (see Request Summary / Scope) passes with 0 failed (385 passed, 5
  skipped, or the then-current equivalent counts).
- No other assertion in the file is modified beyond the one stale baseline.

## Related Tickets
- `TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT` (done) — the sibling ticket whose own +9-line diff
  to `.claude/workflows/implement-ticket.js` caused this drift, and which already fixed the
  identical assertion in the sibling conformance test file but missed this one.
- `TCK-20260817-HOTFIX-TERMINAL-STATUS-STALE-LINE-NUMBERS` (done) — prior occurrence of the same
  drift class across both of these same test files.
- `TCK-20260818-HOTFIX-TERMINAL-STATUS-CONTRACT-DRIFT` (done) — registered `TEST_SCOPE_COVERAGE_FAILED`
  as a genuine new terminal status and fixed the count/line-number drift it caused, same two files.
- `TCK-20260824-HOTFIX-STAGING-DIR-SCOPE-GAP` (done) — sibling same-day hotfix from the same retro
  note as `TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT`; not directly related to this drift but
  shares the same day/branch context.

## Related Docs
None with direct constraints — this is a pure test-baseline correction with no Mechanics Bible or
Engine Contract implications. `docs/parity_ledger/infrastructure.yaml` (~line 7720) documents the
prior 2026-08-xx round of stale-literal fixes across these same test files as background/precedent
only; no new parity divergence is introduced by this fix.

## Related Stored Artifacts
None found covering this exact drift. Hotfix tier — no staging artifacts will be created for this
ticket.

## Related Code Areas
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py` (line 101 — the
  single assertion to update)
- `tools/agent_orchestration_claude_adapter/terminal_status_extractor.py` (read-only reference —
  the live extractor used to re-verify the correct value; not modified)
- `.claude/workflows/implement-ticket.js` (read-only reference — the source file whose line numbers
  are being asserted against; not modified)

## Assumptions / Open Questions
- Assumes the real current value is `[1507, 1519]` as independently re-confirmed via the live
  extractor during this scoping session (2026-08-24) — but the implementer must re-verify this
  again directly before editing, since the file may drift further between scoping and
  implementation (explicitly flagged as a risk in the request itself).
- Assumes `layer: ai` is correct — matches all three prior terminal-status-drift tickets
  (`TCK-20260817-...`, `TCK-20260818-...`, `TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT`), all of
  which used this same layer for edits to this same test-file pair.
- Assumes tags `[testing, bug]` are correct — exact match to `TCK-20260817-HOTFIX-TERMINAL-STATUS-STALE-LINE-NUMBERS`'s
  tags for the identical class of fix; both tags are already registered in `registries/tag_registry.jsonl`.
- Assumes Priority P1 is correct per the request's explicit framing (a real, currently-red CI job
  blocking PR #64, not a background process-friction item) — higher urgency than the two related
  same-day P2 process tickets.
- Assumes no other test file in the repo hardcodes this same call-site pair beyond these two
  (`test_terminal_status_extractor.py`, `test_terminal_status_conformance.py`) — not independently
  re-verified with a repo-wide search in this scoping pass; if the implementer finds a third
  sibling assertion, it is in-scope to fix under this same ticket since it would be the same drift
  class from the same root cause.

## Implementation Notes
Re-verified the real current value directly via
`extract_all_terminal_statuses(Path('.claude/workflows/implement-ticket.js'))` immediately before
editing (independently confirmed `[1507, 1519]`, matching the ticket's own citation — no further
drift since scoping). Updated the single hardcoded assertion at
`tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py:101` from
`[1498, 1510]` to `[1507, 1519]`. No other line in this file changed.

## Test Summary
Ran the exact "Agent orchestration / codex / replay" CI job command locally:
`pytest tests/agent_codex_live_transport tests/agent_codex_pilot_executor
tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_orchestration
tests/agent_codex_posttool_adapter tests/agent_codex_realrepo_pilot_harness
tests/agent_codex_runtime_shadow tests/agent_orchestration tests/agent_orchestration_claude_adapter
tests/agent_orchestration_codex_adapter tests/agent_replay tests/agent_replay_codex
-m "not slow and not extra_slow" --tb=short -q`. Before fix: 1 failed, 384 passed, 5 skipped
(the target assertion). After fix: 385 passed, 5 skipped, 0 failed.

## Files Changed
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py` — updated the
  hardcoded `FINALIZE_INCOMPLETE` call-site baseline (`[1498, 1510]` → `[1507, 1519]`), the
  sibling assertion `TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT` missed when fixing the
  identical drift in `test_terminal_status_conformance.py`.
- `tickets/inprogress/TCK-20260824-HOTFIX-TERMINAL-STATUS-EXTRACTOR-DRIFT.md` — this file.

## Completion Summary
Fixed the real CI failure on PR #64's "Agent orchestration / codex / replay" job: a second
hardcoded `FINALIZE_INCOMPLETE` call-site baseline (`test_terminal_status_extractor.py`, sibling
of the one already fixed in `test_terminal_status_conformance.py` by
`TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT`) had drifted `[1498, 1510]` → `[1507, 1519]` from
that same ticket's own diff. Updated to the independently-re-verified real value. Full CI-job-
matched local test command now passes 385/385 (5 pre-existing unrelated skips), where it
previously failed 1/385.
