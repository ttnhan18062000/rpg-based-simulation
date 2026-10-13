---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION
phase: open
date: 2026-10-13
tags: [testing, regression, simulation-quality]
---

# TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION

## Title
The grade regression tests and the re-anchor tool read a pillar's "no-data" status, so a pillar with too few events is neither a fake score nor a silent pass. A pillar missing from a report becomes a failure, not grade C.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
TCK-20261014-POST-536-PROGRESSION-FLOOR-AND-INFORMATION-SPIKE-IN-200T-GRADE-ANCHORS (rpg) traced the 27 grade-anchor rows held out of the #531 re-anchor:

- **PROGRESSION -0.1569 = -8/51** is a constant. It means "nothing happened but the plateau penalty", because there are no `xp_granted` events in the first 200t. 23 of the 81 committed anchors pin it.
- **INFORMATION** counts one event per strategic update while an entity holds a vague lead, so it measures dwell time, not happenings.

rpg fixes both:

- **(a)** The INFORMATION event fires on the transition only. No harness change is needed.
- **(b)** A pillar with fewer than `min_events` events reports `no-data`. rpg holds (b)'s merge until THIS ticket is ready, so they land together.

The shape was agreed between testing-planner and rpg-planner on 2026-10-13.

Found during the design: `tests/simulation_quality/test_grade_regression.py` (~L435 and ~L476) reads `actual_grades.get(pillar, "C")`. A pillar missing from a report reads as C and passes against a C anchor. That is a silent pass today, independent of (b).

### Agreed report shape (rpg emits it)
- Every pillar is always present in `quality_report.json`: `{"status": "ok"|"no-data", "grade": <GRADE_ORDER letter>|null, "normalized_score": <float>|null, "event_count": n, "min_events": k, "reason"?: "below_min_events"}`.
  - On no-data, grade and score are null, never a placeholder.
  - `min_events` comes from one typed per-pillar table in the scoring contract module, default 3. rpg-implementer-2 names the file and symbol.
- Overall: computed only over `status: ok` pillars, with `pillars_scored` and `pillars_no_data` beside it. If fewer than half of the pillars are scored, the overall is `{"status": "no-data", "grade": null, ..., "reason": "too_few_pillars_scored"}`.

### Agreed anchor shape (written by simq_reanchor only)
A no-data pillar anchor is `{"status": "no-data", "reason": "below_min_events", "min_events": k}` with no grade or score. An ok anchor keeps `{grade, score}`; an explicit `status: ok` is allowed.

## Scope
1. **Missing pillar fails.** Remove the `.get(pillar, "C")` default and every similar default (search the SimQ tests for others). A pillar present in the anchor but missing from the report is a test failure that names the pillar.
2. **Four-way comparison** in `test_grade_regression.py` (fast and long-run) and in every `test_corpus_diversity.py` guard that reads `_anchor(...)`:
   - anchor ok / live ok: the existing band and score checks, unchanged.
   - anchor no-data / live no-data with the same `min_events`: pass, "still no-data". A different `min_events` fails: "threshold changed: re-anchor under a ruling".
   - anchor ok / live no-data: fail, "pillar lost its data".
   - anchor no-data / live ok: fail, "pillar gained data: re-anchor under a ruling".
   - A live pillar with `status: no-data` but a non-null grade or score, or `status: ok` with a null grade or score, is a contract failure.
3. **Overall:** compared only when the anchor's and the live report's no-data pillar sets are equal. Otherwise fail with "not comparable: re-anchor". An overall `status: no-data` follows the same four-way rule.
4. **Visibility:** the test output (the assertion message or a session summary) lists the no-data pillars per key, so no-data can't grow unseen.
5. **`simq_reanchor.py`:**
   - writes the no-data anchor shape from no-data run rows;
   - treats a status change (ok to no-data or back) as a moved row in the table, with columns for status before and after;
   - the pair-identity check includes status and `min_events`;
   - the ruling table shows status transitions.
6. **Fixture schema test** (`test_grade_anchors_*` schema guard, ~L546): accept the two shapes, and reject anything else (e.g. a no-data anchor carrying a grade).
7. **Docs:** the `docs/simulation_quality/quality_scoring_contract.md` §11.3 grade-anchor section, and the re-anchor how-to in the test docstring.

## Out of Scope
- The scorer changes (a) and (b), the `min_events` table and the overall aggregation: rpg.
- Re-anchoring the 27 held rows and the 23 on the -8/51 constant: that runs after (a) and (b) are on main, under its own rpg ruling. The re-anchor is a follow-up step of this epic, not this ticket.
- Changing any band or score tolerance.

## Acceptance Criteria
- [ ] AC1: no `.get(<pillar>, <default grade>)` or equivalent remains in the SimQ tests. A test proves that a pillar missing from the report fails, naming the pillar.
- [ ] AC2: the four-way comparison and the contract-failure cases have unit tests on synthetic reports and anchors (all 4 cells, the `min_events` change, and both malformed shapes).
- [ ] AC3: the overall is compared only on equal no-data sets, and an overall no-data follows the four-way rule. Both are tested.
- [ ] AC4: `simq_reanchor.py` writes the no-data anchor shape and records status transitions as moved rows in both tables. Tested.
- [ ] AC5: the fixture schema guard accepts the two shapes and rejects the others.
- [ ] AC6: it works against today's reports, which have no `status` field. A pillar without `status` is read as ok only when it has a numeric grade and score, so the existing anchors and CI are unchanged until (b) lands.
- [ ] AC7: it is merged before or together with rpg's (b). The ticket records the rpg PR it pairs with.
- [ ] AC8: no tolerance, band or override is relaxed (baseline_change_policy.md rules 6 and 8).

## Related Tickets
- TCK-20261014-POST-536-PROGRESSION-FLOOR-AND-INFORMATION-SPIKE-IN-200T-GRADE-ANCHORS (rpg; the (a) and (b) fixes)
- TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE (#531; the re-anchor that held the 27 rows)

## Related Docs
- docs/plans/test_architecture/reference/baseline_change_policy.md
- docs/simulation_quality/quality_scoring_contract.md §11.3
- agent-working/stored_artifacts/TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE/reanchor_provenance.md (on #531)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE/ (#531: ruling_table.tsv, exclude.tsv)

## Related Code Areas
- tests/simulation_quality/test_grade_regression.py
- tests/unit/worldassembly/test_corpus_diversity.py
- tools/test_architecture/simq_reanchor.py
- tests/simulation_quality/fixtures/grade_anchors.json (shape only; values are written by the tool)

## Assumptions / Open Questions
- This needs #531 merged first: it builds on #531's `simq_reanchor.py` and the fixture-reading `_anchor`.
- The file and symbol for `min_events` come from rpg-implementer-2. The harness reads `min_events` from the report, not from src.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
