---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260904-HOTFIX-ARCH-BOUNDARY-PIN-LINE-DRIFT
phase: open
date: 2026-09-04
tags: [testing]
---

# TCK-20260904-HOTFIX-ARCH-BOUNDARY-PIN-LINE-DRIFT

## Title
Fix stale exact-line-number pin in domains->observability import-boundary test after TCK-20260904-SETTLEMENT-CULTURE-READ shifted line numbers

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
CI's "Architecture / docs / static" job started failing on the M4 batch branch
(`m4-institutions-economic-signals-implementation`) after `TCK-20260904-SETTLEMENT-CULTURE-READ`
landed: `tests/architecture/test_phase18_import_boundaries.py::test_domains_do_not_import_observability_outside_pinned_exceptions`
fails with `src/domains/campaigns/orchestrator.py:434 imports from src.observability
(src.observability.events) but is not one of the pinned grandfathered exceptions`.

Root cause confirmed directly: the test's `_DOMAINS_OBSERVABILITY_PINNED` dict pins this
exception to an exact line number, `("src/domains/campaigns/orchestrator.py", 418)`. That pin
was accurate before this session's M4 batch started. `TCK-20260904-SETTLEMENT-CULTURE-READ`
added a new method (`describe_settlement_personality`) earlier in the same file, which shifted
the pre-existing `from src.observability.events import SimulationEvent` lazy import (inside
`_record_event`-shaped helper) down from line 418 to line 434. The import itself is unchanged
and still correctly guarded/lazy — only its line number moved. This is the same "hardcoded
baseline drifts when this session's own legitimate change shifts line numbers" class of bug
documented for parity-ledger citations elsewhere in this session's work, applied here to an
architecture test's pinned-line dict instead of a parity YAML file.

Confirmed via local reproduction of CI's exact command
(`pytest tests/architecture tests/docs tests/integrity tests/static tests/refactor -m "not slow and not extra_slow" --tb=short -q`):
1 failed, 193 passed, 2 skipped, 1 deselected, 2 xfailed — the one failure is exactly this line-drift.

## Scope
- Update `tests/architecture/test_phase18_import_boundaries.py`'s `_DOMAINS_OBSERVABILITY_PINNED`
  dict: change the key `("src/domains/campaigns/orchestrator.py", 418)` to
  `("src/domains/campaigns/orchestrator.py", 434)`, matching the import's real current line.
- Confirm the sibling pin `("src/domains/campaigns/narrative_ledger.py", 71)` is still accurate
  (already directly verified — it is; not touched).
- Re-run the exact CI command locally to confirm the job goes green.

## Out of Scope
- Any change to `src/domains/campaigns/orchestrator.py` itself — the import is correct as-is,
  only its line number changed as a side effect of unrelated new code being added earlier in
  the file.
- Making the pin dict line-number-independent (e.g. matching by import statement content instead
  of exact line) — a real, reasonable future improvement to reduce this drift class recurring,
  but out of scope for this narrow hotfix; the test's own module docstring states line-exactness
  is intentional ("Expanding this set requires updating both this test and
  docs/audits/D14_coupling_depth.md's Coupling Inventory together -- not a silent addition").
- `docs/audits/D14_coupling_depth.md` — checked directly; it does not cite line numbers for this
  entry, only file paths, so it needs no update for this line-only drift.

## Acceptance Criteria
- `_DOMAINS_OBSERVABILITY_PINNED`'s `orchestrator.py` key uses line 434, matching the real
  current import location.
- `pytest tests/architecture tests/docs tests/integrity tests/static tests/refactor -m "not slow and not extra_slow" -q`
  passes with 0 failures.
- No other file changed.

## Related Tickets
- TCK-20260904-SETTLEMENT-CULTURE-READ (the ticket whose diff caused the line shift)

## Related Docs
- docs/audits/D14_coupling_depth.md (checked, no update needed — confirmed no line-number citation there)

## Related Stored Artifacts
None (hotfix tier, no staging artifacts required).

## Related Code Areas
- tests/architecture/test_phase18_import_boundaries.py
- src/domains/campaigns/orchestrator.py (read-only reference, not modified)

## Assumptions / Open Questions
None — root cause and fix are fully confirmed via direct source inspection and local CI-command
reproduction.

## Implementation Notes
Changed `_DOMAINS_OBSERVABILITY_PINNED`'s `("src/domains/campaigns/orchestrator.py", 418)` key to
`("src/domains/campaigns/orchestrator.py", 434)` in
`tests/architecture/test_phase18_import_boundaries.py`. Directly confirmed via `Read` that the
`from src.observability.events import SimulationEvent` lazy import at line 434 is byte-identical
to what was previously at line 418 — the import statement itself, its guarding docstring, and its
call site are all unchanged; only `TCK-20260904-SETTLEMENT-CULTURE-READ`'s new
`describe_settlement_personality` method (added earlier in the file) shifted subsequent line
numbers by 16. Confirmed the sibling pin (`narrative_ledger.py`, line 71) is still accurate —
not touched, no drift there. Confirmed `docs/audits/D14_coupling_depth.md` cites no line numbers
for this entry, so it needs no update.

## Test Summary
Ran CI's exact command:
`pytest tests/architecture tests/docs tests/integrity tests/static tests/refactor -m "not slow and not extra_slow" --tb=short -q`
via `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`.
- Before fix: 1 failed, 193 passed, 2 skipped, 1 deselected, 2 xfailed —
  `test_domains_do_not_import_observability_outside_pinned_exceptions` failing exactly as
  diagnosed.
- After fix: 194 passed, 2 skipped, 1 deselected, 2 xfailed — 0 failures.

## Files Changed
- `tests/architecture/test_phase18_import_boundaries.py` — updated one pinned line number
  (418 → 434) in `_DOMAINS_OBSERVABILITY_PINNED`.

## Completion Summary
Fixed a CI regression this session's own `TCK-20260904-SETTLEMENT-CULTURE-READ` work caused:
adding a new method earlier in `src/domains/campaigns/orchestrator.py` shifted a pre-existing,
still-correct, lazily-guarded `SimulationEvent` import from line 418 to line 434, and
`tests/architecture/test_phase18_import_boundaries.py`'s exact-line-number pin didn't move with
it. This is the same "hardcoded baseline drifts when a legitimate change shifts line numbers"
class of bug this session has repeatedly hit and fixed in parity-ledger YAML citations, now
confirmed to also apply to this architecture test's pinned-line dict. No production code was
touched — only the test's own pin was corrected to match reality, verified by re-running CI's
exact command locally (194 passed, 0 failed) before and after.
