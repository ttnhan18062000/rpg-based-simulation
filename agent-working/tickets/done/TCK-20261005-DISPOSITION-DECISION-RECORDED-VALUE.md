---
status: historical
layer: ticket
authority: P2
audience: agent
ticket_id: TCK-20261005-DISPOSITION-DECISION-RECORDED-VALUE
phase: done
date: 2026-10-05
tags: [ai, process-improvement]
---

# TCK-20261005-DISPOSITION-DECISION-RECORDED-VALUE

## Title
Add `DECISION-RECORDED` to the `## Disposition` values so a decision-only ticket has a clean DONE path

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
rpg-feature-planning (rpg-planner) reported that a ticket whose correct outcome is a recorded owner decision, with no code and no test change, has no clean closure path. Three instances over about three weeks: `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`, `TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN` (masked by an incidental registry edit) and `TCK-20261003-APPRAISAL-READS-REPUTATION-WITHOUT-A-KNOWLEDGE-GATE`.

Finding: the mechanism the report asks about already exists (`### Closing a ticket with no implementation (## Disposition)` in `docs/guides/delivery_process.md`; values in `tools/ticket_field_values.py:58`). It does not fit this case because none of the five values (`STALE-PREMISE`, `NO-MECHANISM`, `DUPLICATE`, `SUPERSEDED`, `WONT-DO`) says "the behaviour is intended and the owner decided it". Forcing one of them is the "token fit" the report fears. Recommendation: add a sixth value, `DECISION-RECORDED`, with the same evidence rule, and a line stating that `Files Changed` reads `none — decision-only`.

## Scope
1. Add `DECISION-RECORDED` to the Disposition value set in `tools/ticket_field_values.py` and wherever else the set is enumerated (`done_checker_static.py` consumer, `tests/tools/test_ticket_field_values.py`, `tests/tools/test_done_checker_static.py`).
2. In `## Disposition Rationale` for this value, the cited evidence must name the decision: who decided and when (a dated owner message, a decision-doc line, or a commit SHA). Reuse the existing evidence check; do not add a new one unless the existing check cannot express it.
3. Update the `delivery_process.md` Disposition section: list the new value, and add the convention that a decision-only ticket's `Files Changed` reads `none — decision-only`.
4. Measure, do not guess: run `done_checker_static.py` against a fixture decision-only ticket and record which of its conditions pass or fail without the new value (the report left this unmeasured).

## Out of Scope
- Changing what counts as an attributed `src/` change.
- Retroactively re-closing the three named tickets.

## Acceptance Criteria
1. A ticket with `## Disposition` = `DECISION-RECORDED` and a rationale citing a dated decision passes `migration_complete` with no staging artifacts.
2. The same ticket with an uncited rationale, or with an attributed `src/` change, fails and names which.
3. The five existing values behave exactly as before (existing tests unchanged).
4. The guide lists six values and states the `Files Changed` convention.
5. Investigation records the measured per-condition result from Scope item 4.

## Related Tickets
- TCK-20261003-APPRAISAL-READS-REPUTATION-WITHOUT-A-KNOWLEDGE-GATE
- TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED
- TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN

## Related Docs
- docs/guides/delivery_process.md

## Related Stored Artifacts
- none yet

## Related Code Areas
- tools/ticket_field_values.py
- tools/gate_checks/done_checker_static.py
- tests/tools/test_ticket_field_values.py
- tests/tools/test_done_checker_static.py

## Assumptions / Open Questions
- Assumption: the Disposition value set is the only enumeration; verify by grep for the five values in `tools/` before editing.
- Open: whether the owner prefers a sixth value or the narrower convention-only answer (a guide line, no code). Recommendation is the sixth value, since a convention alone leaves `migration_complete` demanding staging artifacts.

## Implementation Notes
- Added `DECISION-RECORDED` to `DISPOSITION_VALUES` in `tools/ticket_field_values.py`. It is the only enumeration (grep of `tools/` for the five values found just that set; `planning_doc_staleness_check.py` mentions the values in a docstring only). The existing evidence check is reused unchanged: a decision-doc `file:line`, the recording commit SHA, or a fenced block quoting the dated owner message; the guide says the rationale must name who decided and when.
- `docs/guides/delivery_process.md` Disposition section lists six values and states `## Files Changed` reads `none — decision-only`.
- **Measured (Scope item 4)** with `done_checker_static.py --ticket-id` on a fixture decision-only ticket in a scratch git repo: at **hotfix** tier `migration_complete` is `NA — hotfix tier — no migration expected`, so the gap only bites standard/epic tickets; with `## Disposition` = `DECISION-RECORDED` plus a SHA-citing rationale, `migration_complete` is `PASS — disposition closure (DECISION-RECORDED): no staging artifacts expected`. The fixture's `working_log_exactly_one_row` and `registry_entry_regenerated` conditions FAIL in both variants because the scratch repo has no log row or REGISTRY.yaml; they are fixture artifacts, not part of this question. Without a Disposition at standard tier, `migration_complete` demands the staging artifacts (existing test `test_ticket_without_disposition_still_fails_migration_when_artifacts_missing`).
- **Follow-up from design/rpg-planner review (same PR):** (1) the precheck `staging_artifacts_complete` also failed for a decision-only standard ticket (and, pre-existing, for the five old values); `check_staging_artifacts_complete` now returns NA when `_disposition_migration_result` is PASS, so both staging-demanding conditions honour a valid Disposition, tested with both run. An invalid Disposition still fails it. (2) `DECISION-RECORDED` now has an extra rule, `check_decision_recorded_rationale`: the rationale must carry an ISO date and cannot rest on a bare `src/`/`tests/` `file:line`; a SHA, doc `file:line` or fenced owner-message quote still satisfies it. Whether the cited record is really the decision (and who decided) stays a reviewer's call; the checker cannot verify a SHA's meaning.
- Decision on the open question: sixth value, per the ticket's recommendation (a convention alone leaves `migration_complete` demanding staging artifacts).

## Test Summary
`tests/tools/test_ticket_field_values.py` + `tests/tools/test_done_checker_static.py` (the disposition, decision and guide tests): 196 pass over both files. New: value set pinned at six; cited vs uncited `DECISION-RECORDED` rationale; `migration_complete` passes without staging artifacts, fails on an uncited rationale, fails on an attributed `src/` change; guide test now requires `DECISION-RECORDED`. The five old values' tests are unchanged.

## Files Changed
- tools/ticket_field_values.py
- docs/guides/delivery_process.md
- tests/tools/test_ticket_field_values.py
- tests/tools/test_done_checker_static.py

## Completion Summary
`DECISION-RECORDED` is a sixth Disposition value with the same evidence rule; a decision-only standard/epic ticket now closes with no staging artifacts. Hotfix tickets never needed it.
