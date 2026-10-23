---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1
phase: open
date: 2026-10-14
tags: [testing, regression, simulation-quality]
---

# TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1

## Title
One SimQ grade-anchor re-anchor, taken on baseline v1. Testing runs the mechanics, and rpg-planner rules on every moved row. The four anchor-family tickets fold into it, and it owns the anchor known-reds until it lands.

## Status
OPEN (ready to dispatch 2026-10-23: v1 is on main)

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
#531 (TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE) re-anchored under audit_mode and held 27 pairs. Another 23 committed anchors pin the PROGRESSION -8/51 plateau constant. #557 (TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION) made the harness read no-data pillars. rpg fixes (a), the INFORMATION transition-only fix, and (b), TCK-20261014-PILLARS-REPORT-NO-DATA-BELOW-A-MINIMUM-EVENT-COUNT, are on rpg-next.

Agreed by testing-planner and rpg-planner on 2026-10-14:
- There is ONE re-anchor. rpg-planner owns the ruling, and testing runs `tools/test_architecture/simq_reanchor.py`.
- On 2026-10-14 the designer moved the timing: the re-anchor is taken ON baseline v1, the authored world after all M0 pre-v1 steps and the dependency window. That avoids a second re-anchor, because 6 more measured behaviour steps and the dependency upgrades still come before v1. rpg-planner's guess is about 1-1.5 weeks.

**Update 2026-10-14 (testing-planner + rpg-planner ruling), after slow run 38532053464:** the
first scheduled slow run with audit_mode anchors (7fa1fc7bc, success) turned 14 corpus-diversity
anchors that had been known red green. They are in the NARRATIVE and SOCIAL "step-change" families
and the 1000t cognition anchors, and #390 lists them as FIXED. rpg-planner ruled this fits host-speed
noise in the earlier unaudited runs (cause: TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR),
not real behaviour shifts. So:
- The moved-row list in Scope 2-3 is ONLY rows that are red or moved under audit_mode. A row
  that is green under audit_mode is not ruled as a moved row.
- Scope 5: no bisect or rebaseline work on the family tickets. A family ticket whose anchors keep
  passing in scheduled slow runs closes as "host-speed noise (TCK-20261014-UNAUDITED-RUNS-...)",
  by the green-count rule and through its owner, possibly before this ticket lands. Only a family
  that still has rows red under audit_mode folds in here with a pointer to the ruling table.
  AC4 is read that way.
- NARRATIVE is retired as a grade under D77, so the NARRATIVE family's anchors go with the SimQ
  rebuild after v1 (TCK-20261014-SIMQ-PILLARS-COMPUTED-FROM-TYPED-RECORDS-WITH-SEED-SPREAD-D77).
- One green run is one data point. No known-red entry is removed on its strength alone.

## Scope
1. When rpg-planner says baseline v1 is on main, run two isolated audit_mode runs per key on one SHA for every anchored key, the 200t and the 1000t keys alike, as in #531. Any pair that isn't identical is refused and becomes an rpg determinism finding.
2. Produce the moved-rows table and the ruling table with `simq_reanchor.py`, including the status transitions to and from no-data. Send both to rpg-planner BEFORE any commit.
3. rpg-planner rules row by row. Every moved row gets a cause attributed. A row whose cause is a neutral PR, or is unexplained, stays held under its own fix ticket. No row is accepted wholesale.
4. Commit the ruled anchors with provenance (baseline_change_policy.md rules 5, 9, 10 and 12).
5. Fold in and close, each with a pointer to the ruling table:
   - TCK-20260912-CORPUS-DIVERSITY-NARRATIVE-PILLAR-POST-REFRESH-DRIFT
   - TCK-20261007-SIMQ-SOCIAL-ANCHOR-FAMILY-STEP-RISE-BISECT-THEN-REBASELINE
   - TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE
   - TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE
   Their bisect ACs are superseded by the per-row cause in step 3.
6. Known reds: until this lands, the `tests.unit.worldassembly.test_corpus_diversity*` catch-all and the anchor-family entries in `tools/test_architecture/slow_known_reds.yaml` point at THIS ticket. When the re-anchor lands, they are retired or repointed in the same PR.

## Out of Scope
- The ruling on the values: rpg-planner.
- CORPUS-DIVERSITY AC3, the frontier_marches 200t teardown ERROR. It is not an anchor value. If it still reproduces, it stays a separate item.
- The population_stability entries. They stay on TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2.
- Changing any tolerance, band or override (policy rules 6 and 8).

## Acceptance Criteria
- [ ] AC1: every anchored key, 200t and 1000t, has two identical isolated audit_mode runs on one baseline-v1 SHA. Non-identical pairs are listed and routed to rpg-planner.
- [ ] AC2: rpg-planner has ruled on the moved-rows and ruling tables, with a cause for each moved row, before the commit. Held rows each name a fix ticket.
- [ ] AC3: the anchors are committed with provenance, and `SCORE_TOLERANCE_OVERRIDES` is still empty.
- [ ] AC4: the four family tickets are closed with pointers. The catch-all and the family known-reds are retired or repointed in the same PR.
- [ ] AC5: the first scheduled slow run after the merge has no anchor red outside the held rows.
- [ ] AC6: the expiry guard holds. If baseline v1 has not landed by 2026-10-31, testing-planner re-dates the 2026-11-04 catch-all under an rpg ruling, citing this ticket, rather than letting it expire silently.

## Related Tickets
- TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE (#531)
- TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION (#557)
- TCK-20261014-POST-536-PROGRESSION-FLOOR-AND-INFORMATION-SPIKE-IN-200T-GRADE-ANCHORS (rpg; fix (a))
- TCK-20261014-PILLARS-REPORT-NO-DATA-BELOW-A-MINIMUM-EVENT-COUNT (rpg; fix (b))
- The four family tickets in Scope 5

## Related Docs
- docs/plans/test_architecture/reference/baseline_change_policy.md
- docs/simulation_quality/quality_scoring_contract.md §11.3

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE/ (ruling_table.tsv, exclude.tsv, reanchor_provenance.md)

## Related Code Areas
- tools/test_architecture/simq_reanchor.py
- tools/test_architecture/simq_pillar_compare.py
- tests/simulation_quality/fixtures/grade_anchors.json
- tools/test_architecture/slow_known_reds.yaml

## Assumptions / Open Questions
- Baseline v1's SHA is announced by rpg-planner. The runs wait for main, so the anchors match what CI runs.
- **2026-10-23, agreed with rpg-planner:**
  - **SHA:** the v1 simulation code is e8df8b96da891304d8a4d8afade5e6d63182cf22 (gate run 39799337778 GREEN). #725 (the record PR) adds only baselines, docs and tickets, with no src/content/config change. Run the pairs on #725's MERGE sha, which rpg-planner sends when it merges and whose src is identical to e8df8b96d. PIN that sha in a dedicated worktree (`git worktree add --detach <path> <sha>`), so no post-v1 src PR (#529 first) can enter the runs.
  - **Producer:** the committed `tools/test_architecture/simq_audit_rows.py`: every anchored key x2, isolated audit_mode, `--workers 1`, deleting only its own run ids. That's about 81 keys x2 at about 1 min per pair, roughly 1.5 h.
  - **Host order:** THESE PAIRS FIRST. Then rpg's `make evaluate-full` (TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE, due 10-30). Never both at once. Tell rpg-planner when the last process exits.
  - **Tables:** the moved-rows and ruling tables go to rpg-planner BEFORE any commit, and rpg rules each moved row (with the designer where a Bible meaning is touched).
  - **Expiry:** if the sha isn't on main by 10-29, rpg-planner says so that day, which triggers AC6.
  - **v1 SHA = 341f700d0** (#725 merged 2026-10-23). Checked by testing-planner: `git diff e8df8b96d 341f700d0` touches no src/, content/ or config/ files. Under tests/ it changes only the behavioral_5k baseline, rpg_gate_v1.json, tests/helpers/world_build.py and session-tool tests. Before the run, confirm simq_audit_rows / calibrate_simq do not import tests/helpers/world_build.py; if they do, tell testing-planner. Pin it with `git worktree add --detach <scratch path> 341f700d0` and run everything from there.
  - **Sidecar:** rpg's calibration writes the existing calibrate_simq `quality_report.run_determinism.json` (run id + audit_mode + signals_zeroed). No new format. test_grade_regression's live side keeps refusing a missing sidecar.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
