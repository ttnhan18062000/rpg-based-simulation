---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260804-AGENT-DEF-GAP-FIXES
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# Test Plan — TCK-20260804-AGENT-DEF-GAP-FIXES

**Updated after Plan's Step 3 redesign** (architecture-review caught the original Step 3 design
targeting the wrong root cause; the corrected design is a real code fix, not prose-only — this
test_plan.md's original framing below predates that correction and is retained struck-through in
spirit but superseded by the table below). Two distinct verification classes now apply: manual
re-read for the `.claude/agents/*.md` prose fixes (Steps 1/2, same conclusion as both sibling
SKILL.md tickets — no pytest coverage exists for agent-instruction prose), and real pytest
regression coverage for the `done_checker_static.py` parser fix (Step 3/4).

## Regression Surface

`tests/tools/test_done_checker_static.py`'s existing `_DOCS_NONE_PHRASES`-dependent tests
(notably `test_parse_docs_none_variants`) must continue passing unweakened — the new
`_is_none_section()` helper wraps the existing exact-match fast path, never replaces it.

## New Tests Required (per AC)

| Check | Type | What it verifies |
|---|---|---|
| Manual re-read of `planner.md` post-edit | manual | The 3 new sub-instructions (cite file:line for behavioral/schema claims, enumerate concurrent writers, cross-check AC-vs-Steps) are present, concrete, and checkable — not vague "be careful" language. |
| Manual re-read of `implementer.md` post-edit | manual | The before-returning checklist covers: `## Completion Summary` filled, `## Files Changed` filled, AC checkboxes checked-if-satisfied, `## Status` field current — matching the fresh-evidence pattern counts (6 AC / 5 Status / 4 Completion-Summary-gap). |
| `test_parse_docs_none_with_trailing_rationale_prose` | pytest | Reproduces the real observed failure mode: `"None. <trailing rationale>"` is correctly treated as none (no docs/ paths required). |
| `test_parse_docs_none_prefix_with_later_bullet_still_parses` | pytest | The false-PASS guard: a "None of the..." opening followed by a real `- \`docs/x.md\`` bullet still extracts the real path, not silently swallowed as "none." |
| `test_docs_coverage_none_with_trailing_rationale_passes` | pytest, integration | End-to-end via `check_docs_to_update_coverage()`: the trailing-rationale case reaches PASS, not the pre-fix FAIL. |
| `test_docs_coverage_none_prefix_but_real_bullet_still_required` | pytest, integration | End-to-end: the false-PASS guard holds through the full coverage-check path, not just the parse-level helper. |
| Citation-accuracy check | manual | Any line-range or function-name citation in the new instructions is verified against real, current source. |
| **Deferred re-query (the real verification for Steps 1/2)** | data | Re-run this investigation's exact query (Review/Verify `status='failed'` events, grouped by month, via `agent-monitoring-index/monitoring.db`) after several weeks of real runs post-Implement. Expect: Review failure rate trending down from the 15.2%/rising pattern; Verify failure rate's AC-checkbox/Status-field/Completion-Summary-gap sub-patterns specifically declining. |
| **Immediate check for Step 3** | data | Since the parser fix is deterministic (not behavior-change-dependent), re-query for `phase='Verify'`, `status='failed'` events since 2026-08-05 whose evidence mentions "Docs Requiring Update"/"none-phrase" — expect 0 immediately, no weeks-long accumulation needed. |

## Anti-Drift Test Guards

- The deferred re-query must use the SAME classification methodology as this investigation (manual
  read of `summary` text, categorized by pattern) — a future re-check should not silently swap to a
  coarser "any failure" metric that would wash out whether the SPECIFIC targeted patterns improved.
- Do not claim success from a short-window (days) re-check — the whole point of a deferred check is
  giving enough real runs to accumulate; a same-day re-check after Implement would only reflect 0-1
  new samples, not a real trend.
- If the deferred re-query later shows no improvement, that is a valid, reportable outcome (the
  persistent-file fix didn't work, prompt-only reminders may already have been sufficient, or a
  different mechanism is needed) — not something to route around or reframe as success.
