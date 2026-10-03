---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-DESIGN-PATTERNS-DOC-CURRENCY-DRIFT
phase: done
date: 2026-08-17
tags: [testing, bug]
---

# TCK-20260817-HOTFIX-DESIGN-PATTERNS-DOC-CURRENCY-DRIFT

## Title
Fix 2 stale checks in `test_design_patterns_currency.py` — a V1-symbol list that never absorbed
`GoalScorer`'s revival, and a broken-link check tripped by an intentional historical reference

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Part of a batch of 7 tickets fixing genuinely pre-existing CI failures. Two failures in
`tests/docs/test_design_patterns_currency.py`, both traced to the same root migration event not
being fully reconciled with this test file:

1. `test_v1_symbols_not_in_primary_sections` — `AssertionError: V1 symbol 'GoalScorer' found in
   primary (non-legacy) section`. Root cause (confirmed via investigation): `GoalScorer` was
   archived as V1-only when this test was authored (`6e25d4f2`, TCK-20260626-FIX-DESIGN-PATTERNS),
   but was deliberately **revived** as the current V2 tier-5 extension point in `29d78798`
   ("Simulation quality (#20)", 2026-08-14) — `AdventureDecisionPhase` was deleted and
   `AdventureGoalScorer`/`SocialContractGoalScorer`/`RegionStabilizationGoalScorer` (all live in
   `src/ai/goals/`) were built as `GoalScorer` subclasses. `docs/guidelines/design_patterns.md`
   correctly documents this in its primary section — the doc is accurate; the test's own
   `v1_symbols` list was simply never updated in the same commit. Confirmed `GoalEvaluator` and
   `GOAL_REGISTRY` (the other 2 symbols in the same list) genuinely remain V1-only/dead — only
   `GoalScorer` (and its own `src/ai/goals/` module path, now home to the live `GoalScorer`
   protocol) needs removing from the list.
2. `test_no_broken_src_links_in_doc` — the doc's own prose intentionally cites the now-deleted
   `src/domains/adventure/phase.py` as historical context ("Formerly also `AdventureDecisionPhase`
   ... deleted by TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE"), but the test's regex
   (`` `(src/[^`]+\.py)` ``) can't distinguish an intentional "this used to exist" reference from a
   live citation, so it fails the same way it would for a genuine stale link.

## Scope
- `tests/docs/test_design_patterns_currency.py:26` — remove `"GoalScorer"` and `"src/ai/goals/"`
  from `v1_symbols`, keep `"GoalEvaluator"` and `"GOAL_REGISTRY"`. Update the module docstring
  (currently says the guard "Ensures the doc does not present V1 GoalScorer/src/ai/goals/ as the V2
  extension point" — now factually wrong, since `GoalScorer` genuinely IS the current V2 extension
  point) to reflect the real remaining scope.
- `docs/guidelines/design_patterns.md` — reformat the one intentional historical reference to
  `src/domains/adventure/phase.py` so it's no longer backtick-wrapped in a way the broken-link
  regex matches, while keeping it clearly readable as a real path reference (already applied:
  removed the backticks around that one deleted-file path, keeping the surrounding sentence's
  meaning unchanged).

## Out of Scope
- Any other of the 7 CI failures in this batch (each has its own ticket).
- Any further changes to `docs/guidelines/design_patterns.md`'s own content/architecture guidance —
  only the one formatting change needed to stop tripping the broken-link check.

## Acceptance Criteria
- [x] `test_v1_symbols_not_in_primary_sections` passes — `GoalScorer` correctly no longer treated
      as V1-only; `GoalEvaluator`/`GOAL_REGISTRY` still correctly guarded as legacy-only.
- [x] `test_no_broken_src_links_in_doc` passes.
- [x] No other test in `tests/docs/test_design_patterns_currency.py` regresses.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
- `docs/guidelines/design_patterns.md`

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tests/docs/test_design_patterns_currency.py`

## Implementation Notes
Removed `"GoalScorer"` and `"src/ai/goals/"` from `v1_symbols`, keeping `"GoalEvaluator"` and
`"GOAL_REGISTRY"` (confirmed still genuinely V1-only/dead, only appearing in the doc's Legacy
Patterns section). Updated the module docstring and the test's own docstring to reflect the real,
narrowed scope. Reformatted `design_patterns.md`'s one intentional historical reference to the
deleted `src/domains/adventure/phase.py` by removing the backticks around that specific path, so
the broken-src-link regex (which matches any backtick-wrapped `src/....py` path) no longer flags an
intentional "this file used to exist" reference as a live citation — the sentence's meaning and
readability are unchanged.

## Test Summary
- `pytest tests/docs/test_design_patterns_currency.py -v`: 5 passed (all tests in the file, no
  regressions).
- `python3 tools/validate_frontmatter.py docs/guidelines/design_patterns.md`: clean.

## Files Changed
- `tests/docs/test_design_patterns_currency.py` — narrowed `v1_symbols`, updated docstrings.
- `docs/guidelines/design_patterns.md` — removed backticks around one intentional
  historical dead-file reference.

## Completion Summary
Fixed both stale checks: the V1-symbol list now correctly excludes `GoalScorer`, which was
deliberately revived as the current V2 tier-5 extension point (the doc's own primary-section prose
was already accurate; only the test's list was stale), and the broken-link check no longer trips on
an intentional, clearly-labeled historical reference to a deleted file. No architecture guidance
content changed — only test-list scope and one formatting detail.
