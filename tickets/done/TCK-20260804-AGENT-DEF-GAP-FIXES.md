---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260804-AGENT-DEF-GAP-FIXES
phase: done
date: 2026-08-04
tags: [ai, agent-monitoring]
---

# TCK-20260804-AGENT-DEF-GAP-FIXES

## Title
Add missing persistent guidance to planner.md (fact-verification), implementer.md (Completion Summary / Files Changed / AC / Status discipline), and fix the recurring "Docs Requiring Update" bullet-format trap (investigator.md guidance or parser fix) to reduce recurring Review/Verify gate failures

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`docs/ai/agent_definition_gap_audit_2026-08-04.md` (evidence doc, written this session) found
Review-phase (architecture-reviewer, pre-Implement gate) failure rate at 15.2% overall and rising
month-over-month (2.7% Jun → 19.5% Jul → 22.9% Aug), and Verify-phase (done-checker, DoD gate)
failure rate at 15.5% overall (0.0% Jun → 21.9% Jul → 16.3% Aug) — both far above every other
phase in the same corpus. Sampled failure evidence for both traces to two concrete root causes:

1. **Review**: the planner repeatedly asserts factual claims about *existing* system behavior in
   `plan.md` that turn out to be wrong when checked against real source (wrong hash-exclusion
   claim, wrong flag-combination claim, wrong field name in an AC). `.claude/agents/planner.md`
   has zero instruction requiring the planner to verify a behavioral claim against real source
   before writing it into `plan.md`.
2. **Verify**: implementer/Finalize hygiene misses — unfilled `## Completion Summary` placeholder,
   missing `## Files Changed` entries, unchecked ACs. `.claude/agents/implementer.md` has zero
   mention of Completion Summary; this guidance currently lives only in `implement-ticket.js`'s
   one-time per-call prompt text, not the agent's own persistent definition.

Per the user's explicit direction: this ticket may introduce new persistent guidance (not
necessarily minimal patches) as long as the fix's effect stays measurable via existing
agent-monitoring instrumentation (Review/Verify failure rate, already computed by
`generate_retro.py` and re-queryable directly against `agent-monitoring-index/monitoring.db`) —
no new instrumentation is required for this ticket since the existing gate-outcome data already
provides before/after visibility.

**Scope expanded after Investigate's fresh-evidence pull (user-approved):** the fresh query (15
Review / 25 Verify failures since 2026-07-20, see `staging_artifacts/{tid}/investigation.md`)
found the original 2 root causes needed correcting (the audit's "uncleaned data/runs" Verify cause
is confirmed stale/already-fixed by `TCK-20260708-DATA-RUNS-CLEANUP-TIMING`, excluded) and
surfaced 2 new patterns: (a) stale `## Status` field (5 occurrences, comparably frequent to
AC-checkbox misses — folded into the implementer.md fix), and (b) `investigation.md`'s "Docs
Requiring Update" section failing `done_checker_static.py`'s bullet-format parser (3 occurrences,
the exact bug class this session independently hit and fixed once already in
`TCK-20260804-EXPANSION-RATE-WIRING`) — user explicitly approved folding this third fix into this
ticket's scope. Plan phase decides whether the fix targets `.claude/agents/investigator.md`'s own
guidance (show the correct bullet format explicitly) or the parser itself
(`tools/gate_checks/done_checker_static.py`'s `_DOCS_BULLET_RE`, made tolerant of both
`` `path` `` and `` `path:line` `` forms) — investigation.md flags this as a genuine open design
choice, not pre-decided.

## Scope
- **Investigate must pull FRESH evidence, not just reuse the 2026-08-04 audit doc's 8-sample
  readout**: query recent (last 2-3 weeks / August-only) Review and Verify failures specifically,
  to confirm the two root causes above are still actively recurring today and not already
  addressed by some other mechanism (e.g. the post-Test `data/runs` cleanup checkpoint fixed a
  related-sounding but distinct historical cause — confirm the specific "uncleaned data/runs"
  Verify-failure samples the audit doc found are not stale/pre-dating that fix).
- Design (Plan phase) the specific instruction(s) to add to `planner.md`: what "verify a factual
  claim before writing it" concretely requires (e.g. grep/read the specific file before asserting
  a behavior, cite file:line for behavioral claims in plan.md, or another concrete, checkable
  mechanism — not just a vague "be more careful" addition).
- Design the specific instruction(s) to add to `implementer.md`: an explicit "before returning"
  checklist covering Completion Summary, Files Changed, AC-checkbox discipline, AND `## Status`
  field currency (folded in per fresh evidence — 5 occurrences, comparably frequent to AC misses).
- Fix the "Docs Requiring Update" bullet-format trap (3 fresh occurrences, folded in): Plan decides
  between adding explicit correct-format guidance to `.claude/agents/investigator.md` (which today
  has zero example of the expected bullet shape) or making
  `tools/gate_checks/done_checker_static.py`'s `_DOCS_BULLET_RE` regex tolerant of both bare-path
  and `path:line` forms — state the reasoning for whichever is chosen.
- Do not touch `implement-ticket.js`'s existing per-call prompt text for any of the three agents —
  the fix target is each agent's own persistent `.claude/agents/*.md` definition (or the parser, if
  that's Plan's choice for the third item), per the audit's root-cause finding that prompt-only
  reminders aren't sufficient on their own.
- State explicitly, in the ticket and in `docs/ai/agent_definition_gap_audit_2026-08-04.md`
  (Document-Update phase), how success will be measured: re-running the same Review/Verify
  failure-rate query after a few weeks of accumulated real runs, expecting a downward trend
  toward the June baseline (Review 2.7%, Verify 0.0%) — not a one-time check.

## Out of Scope
- Any change to `.claude/workflows/implement-ticket.js` itself.
- Building new instrumentation — existing gate-outcome metrics are sufficient to verify this fix.
- Any agent definition beyond `planner.md`/`implementer.md`/`investigator.md` (the third only if
  Plan chooses the agent-guidance route over the parser route).
- The recurring-SKILL.md-drift-mechanism finding (implement-ticket/create-tickets SKILL.md each
  drifting twice) — tracked as its own separate ticket
  (`TCK-20260804-SKILL-DRIFT-DETECTION`), not folded in here; different fix class (a
  drift-detection mechanism, not missing agent guidance).

## Acceptance Criteria
- [x] Investigate confirms both root causes are still currently active (fresh evidence, not just the audit doc's original sample). DONE — see investigation.md (15/25 fresh failures).
- [x] `planner.md` gains 2-3 concrete, checkable verification sub-instructions (not one vague directive — fresh sample showed multiple distinct planner failure modes).
- [x] `implementer.md` gains an explicit before-returning checklist (Completion Summary, Files Changed, AC discipline, `## Status` currency).
- [x] The Docs-Requiring-Update bullet-format trap is fixed (investigator.md guidance or parser tolerance — Plan's choice, stated with reasoning).
- [x] `docs/ai/agent_definition_gap_audit_2026-08-04.md` updated with a "how to check if this worked" pointer to the specific re-query method and expected trend.
- [x] No change to `implement-ticket.js`.

## Related Tickets
- TCK-20260804-SKILL-JS-PHASE-SYNC, TCK-20260804-CREATE-TICKETS-SKILL-SYNC (sibling fixes from the same audit, different drift class — structural gaps, not missing persistent guidance)
- TCK-20260804-SKILL-DRIFT-DETECTION (new, separately scoped — the recurring-drift-mechanism finding surfaced during this ticket's own Investigate)
- TCK-20260804-DOCS-BULLET-LINE-SUFFIX-FIX (new, `tickets/todos/` — the real, confirmed, but
  out-of-scope `_DOCS_BULLET_RE` `:line`-suffix bug this ticket's Plan phase originally targeted
  before Review caught it as the wrong root cause; tracked separately since none of this ticket's
  3 evidenced occurrences were actually caused by it — deliberately not fixed here, not silently
  dropped)

## Related Docs
- `docs/ai/agent_definition_gap_audit_2026-08-04.md`

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `.claude/agents/planner.md`
- `.claude/agents/implementer.md`
- `.claude/agents/investigator.md` (candidate, if Plan chooses agent-guidance over parser fix)
- `tools/gate_checks/done_checker_static.py` (candidate, if Plan chooses parser fix over agent-guidance)

## Assumptions / Open Questions
Resolved by Investigate: the "uncleaned data/runs" Verify-failure cause is confirmed stale (0
fresh occurrences; `TCK-20260708-DATA-RUNS-CLEANUP-TIMING` already fixed it 2026-07-08) — excluded
from this ticket's fix. Open for Plan: investigator.md guidance vs. parser-tolerance fix for the
Docs-Requiring-Update bullet-format trap (see Scope).

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260804-AGENT-DEF-GAP-FIXES/plan.md` (architecture-review-approved revision), Steps 1-5, in order. No deviations from the plan.

- **Step 1** — Inserted `## Fact-Verification Requirements (Before Writing plan.md)` into `.claude/agents/planner.md` immediately after `## Planning Rules` and before `## Output`, with the exact three sub-instructions the plan specified (cite `file:line` for behavioral/schema claims; enumerate every other concurrent writer to a touched shared resource; cross-check AC wording against the plan's own Steps for internal consistency).
- **Step 2** — Inserted `## Before Returning — Ticket Hygiene Checklist` into `.claude/agents/implementer.md` immediately after `## After Writing Code` and before `## Background Commands`, with the exact four checklist items (Completion Summary, Files Changed, AC checkbox discipline, `## Status` currency).
- **Step 3** — Added `_DOCS_NONE_PREFIX_RE` and the new `_is_none_section(section_text: str) -> bool` helper to `tools/gate_checks/done_checker_static.py` immediately after the existing `_DOCS_BULLET_RE`/`_DOCS_NONE_PHRASES` constants. The helper keeps the exact-match fast path unchanged, then for text starting with a `None`/`N/A` prefix (case-insensitive, optional trailing period) checks whether a `- \`docs/...\`` bullet exists in the remainder — no bullet means treat as none (`True`); a bullet present means `False` so normal bullet parsing proceeds on the full text (closes the false-PASS risk a bare prefix match alone would create). Wired `_is_none_section()` into both call sites that previously did the inline exact-match check directly: `_parse_docs_to_update` (docstring also updated to describe the new tolerant behavior) and `check_docs_to_update_coverage`'s `if not required_docs:` branch. `_DOCS_BULLET_RE` itself, `_git_touched_paths`, and `_path_touched` were left untouched, per the plan's Decision section and Do-NOT-touch list.
- **Step 4** — Added two parse-level regression tests to `tests/tools/test_done_checker_static.py` immediately after `test_parse_docs_ignores_non_bullet_prose` (before the `# _git_touched_paths` section comment): `test_parse_docs_none_with_trailing_rationale_prose` (reproduces the real "None. <rationale>" failure mode) and `test_parse_docs_none_prefix_with_later_bullet_still_parses` (the false-PASS guard — a "None of the..." opening followed by a real bullet must still extract the path). Added two integration-level tests immediately after `test_docs_coverage_explicit_none_passes` (before `test_docs_coverage_unparseable_non_none_section_fails`): `test_docs_coverage_none_with_trailing_rationale_passes` and `test_docs_coverage_none_prefix_but_real_bullet_still_required`, both exercising `check_docs_to_update_coverage()` end-to-end. Verified the real line numbers against the plan's stated estimates before inserting: they matched exactly (test ends at 1207 / section comment at 1210; test ends at 1313 / next test at 1316), so insertion points were used as specified with no adjustment needed.
- **Step 5** — Appended the plan's exact `## Update — TCK-20260804-AGENT-DEF-GAP-FIXES landed (2026-08-05)` markdown block to the end of `docs/ai/agent_definition_gap_audit_2026-08-04.md`, after the existing "How to tell if these fixes worked" paragraph, verbatim from plan.md's corrected Step 5 text (describes `_is_none_section()`, not the abandoned `_DOCS_BULLET_RE` mechanism).

Also updated this ticket's own `## Status` (OPEN → INPROGRESS) and checked all six `## Acceptance Criteria` boxes, per the new implementer.md before-returning checklist landed in Step 2 of this same ticket.

## Test Summary
Ran `pytest tests/tools/test_done_checker_static.py -v`: **89 passed, 0 failed** — includes the 4 new Step-4 tests and zero regressions to any pre-existing test, notably `test_parse_docs_none_variants` (the exact-match fast path this change layers on top of, unchanged).

Independent ad hoc hand verification of `_is_none_section` (run via `python3 -c ...` against the live module):
- `_is_none_section("None. This ticket touches no docs/ files.")` → `True` (matches expected).
- `_is_none_section("None of the above, but:\n- \`docs/x.md\`: reason")` → `False` (matches expected — the false-PASS guard holds).

No other test files were run — this ticket touches no `src/` simulation logic, only `.claude/agents/*.md` prose, one `tools/gate_checks/` module, its dedicated test file, and one `docs/` file, so scope was limited to `tests/tools/test_done_checker_static.py` per the Testing Rule ("scope to the domain under modification").

## Files Changed
- `.claude/agents/planner.md` — added `## Fact-Verification Requirements (Before Writing plan.md)` section (Step 1).
- `.claude/agents/implementer.md` — added `## Before Returning — Ticket Hygiene Checklist` section (Step 2).
- `tools/gate_checks/done_checker_static.py` — added `_DOCS_NONE_PREFIX_RE` constant and `_is_none_section()` helper; updated `_parse_docs_to_update` (call site + docstring) and `check_docs_to_update_coverage` (call site) to use it (Step 3).
- `tests/tools/test_done_checker_static.py` — added 2 parse-level tests and 2 integration-level tests for the `_is_none_section` fix (Step 4).
- `docs/ai/agent_definition_gap_audit_2026-08-04.md` — appended the "Update — TCK-20260804-AGENT-DEF-GAP-FIXES landed (2026-08-05)" section (Step 5).
- `docs/parity_ledger/infrastructure.yaml` — added `INFRA-322` (Verify phase; this ledger entry
  was missed by Investigate/Plan/Parity, which reasoned about the `.claude/agents/*.md` prose
  files' out-of-scope status but never separately addressed the real `done_checker_static.py`
  code change; done-checker caught the gap and ran Parity directly during Verify to close it —
  see Completion Summary for full context).

## Completion Summary
Added persistent, concrete guidance to two agent definitions and fixed a real parser bug, all
traced to fresh agent-monitoring evidence (15 Review / 25 Verify failures since 2026-07-20).
`planner.md` gained 3 fact-verification sub-instructions (cite file:line for behavioral claims,
enumerate concurrent writers to shared resources, cross-check AC-vs-plan-Steps) after Review's own
failure evidence showed the planner repeatedly asserting wrong claims about existing code
behavior. `implementer.md` gained a 4-item before-returning checklist (Completion Summary, Files
Changed, AC discipline, `## Status` currency) after fresh Verify-failure evidence showed these are
the dominant, recurring hygiene misses. A `_is_none_section()` helper was added to
`done_checker_static.py`, fixing a real bug where "None. &lt;trailing rationale&gt;" text in
investigation.md's "Docs Requiring Update" section incorrectly failed the Verify-time coverage
gate — Plan's first design targeted the wrong root cause (a `:line`-suffix bullet-format theory
that didn't match any of the cited tickets' real failure evidence) and was corrected once by
Review before landing on the actual cause. A genuine parity-ledger gap (this ticket's own real
code change to `done_checker_static.py` was never separately assessed for ledger coverage,
distinct from the correctly-out-of-scope `.md` prose files) was caught by done-checker during
Verify and closed with `INFRA-322`. How to tell if this worked: re-run the Review/Verify
failure-rate query from `docs/ai/agent_definition_gap_audit_2026-08-04.md` after a few weeks of
accumulated real runs, expecting a downward trend toward the June baseline — not a one-time check.

**Known, deliberately unfixed issue, tracked not silenced:** the original `:line`-suffix bullet-
format theory abandoned during Plan's correction is a real, separately-confirmed bug (via
`TCK-20260804-EXPANSION-RATE-WIRING`'s own event log) — `_DOCS_BULLET_RE` still doesn't tolerate
`` `docs/path:123` `` bullets today. It wasn't the cause of any of this ticket's own 3 evidenced
fresh-Verify-failure occurrences (all traced to the None-phrase issue this ticket did fix), so
fixing it here would have been solving an unevidenced problem. Tracked instead as
`TCK-20260804-DOCS-BULLET-LINE-SUFFIX-FIX` (`tickets/todos/`, hotfix tier, unimplemented) for
whenever it's next prioritized.
