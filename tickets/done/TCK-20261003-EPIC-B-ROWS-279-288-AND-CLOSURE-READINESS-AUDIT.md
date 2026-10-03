---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-EPIC-B-ROWS-279-288-AND-CLOSURE-READINESS-AUDIT
phase: done
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-EPIC-B-ROWS-279-288-AND-CLOSURE-READINESS-AUDIT

## Title
Extend the Epic B scenario-lane cost record to PRs #279-#288, record the scenario-lane cost sharing, and add a closure-readiness audit for test-architecture Epics A-D

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Records and audit only, no product code and no status change to any epic. Requested through test-architecture-reviewer (plan approved 2026-10-03, base `origin/main` c0980e27a): (1) cost-record rows for each PR merged since the last row (#279-#288), by final head, verified by full SHA through the runs and jobs API; (2) check whether a test already asserts that `scenario_lane_paths` classifies a `src/progression/**` path as a trigger; (3) share the cost summary with the feature teams and record the date; (4) a closure-readiness table in `INDEX.md` for every criterion of Epics A-D.

## Scope
- Epic B cost record: 10 rows (#279-#288), a 2026-10-03 update paragraph with current totals (18 PRs, 23 rows; lane ran on 7 PRs, 34-52 s), the "~10 relevant PRs" statement made plainly (not satisfied if it means the lane ran), the new-job-layout marking per run, and the cost-sharing record.
- Routing evidence: report the existing test, add none.
- `INDEX.md`: the closure-readiness audit and a "what closes the folder" line; row 2's status column updated to the current record.
- Two documentation defects found by the audit and fixed in the same change (reviewer's direction): `docs/guides/testing.md`'s own triage list replaced by a pointer to `docs/testing/regression_policy.md` §13 (the guide's non-triage text is kept), and the dead `README.md:112` taxonomy link repointed to `docs/testing/test_taxonomy.md`.

## Out of Scope
- Adding a routing test, changing any epic's status text or criterion status, closing any epic.
- Re-running A3's combined-suite and random-order checks (recorded as not re-run, with the last evidence cited).
- Any change to the workflow, `scenario_lane_paths.py`, or other agents' tickets.

## Acceptance Criteria
1. Every new row matches the Actions runs and jobs API for its full head SHA; each query returned exactly one `Tests` run.
2. The record says plainly that the lane ran on 7 PRs and the `src/progression/**`-only trigger is unobserved in CI; #279 is recorded as Perf-covered, not as that case.
3. The routing test is cited (`tests/unit/tools/test_scenario_lane_paths.py::test_src_progression_only_routes_to_the_dedicated_job`) and described as rule-level, not CI-observed.
4. The share date is recorded only after the sends succeeded, and says sent, no reply recorded.
5. The audit changes no epic status text; every classified criterion has an evidence pointer; unverified items are marked so.
6. `docs/guides/testing.md` carries no triage list of its own and links §13; `README.md` links an existing taxonomy file; B1 and C3 are classed after those fixes.

## Related Tickets
TCK-20261002-EPIC-C-CRITERION-2-PROTOCOL-AND-RUN-2-BLOCKED, TCK-20261001-EPIC-B-COST-RECORD-EXTENSION-AND-PILOT-P-STATUS, TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION, TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY, TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING, TCK-20260929-EPIC-CORE-RPG-TEST-PILOT

## Related Docs
docs/testing/regression_policy.md, docs/testing/core_rpg_test_pilot_2026-09-30.md, docs/testing/test_taxonomy.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- tickets/todos/test-architecture/
- tools/test_architecture/scenario_lane_paths.py (read only)

## Assumptions / Open Questions
- Route: hand-orchestrated hotfix. The evidence for the audit's A1-A6, B1-B3, B5, C3 and D1-D5 was gathered by a read-only subagent; I spot-checked its dead-link, parallel-triage-list and escaped-defect-tag claims. B4, C1, C2, C4 and C5 were checked by me.
- `search_docs` was down; GitHub TLS was intermittent (a first collection pass failed and was re-run).
- Routing counts are recomputed locally on each PR's full paginated file list.
- This branch is held unpushed until PR #289 (the `agent-working/` folder move) lands, then merged with `origin/main` and path-rewritten.

## Implementation Notes
Runs: #279 36900341228, #280 36964376584, #281 36965381697, #282 36995844110, #283 37090371235, #284 36996812878, #285 37090840973, #286 37032971448, #287 37039518014, #288 37044570153 (all `Tests`, conclusion success, one per head). Only #283, #285 and #288 contain the split `Tools` jobs.

## Test Summary
Text only (docs and README edits are links and a pointer). Frontmatter and registry checks run after the edit; the audit's scoped test runs are listed in `INDEX.md` evidence pointers.

## Files Changed
tickets/todos/test-architecture/TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION.md; tickets/todos/test-architecture/INDEX.md; docs/guides/testing.md; README.md; docs/REGISTRY.yaml.

## Completion Summary
Epic B's record is 18 PRs and 23 rows (#271-#288): the lane ran on 7 PRs (34-52 s), Perf covered 6, and 6 are docs-only skips. The "about 10 lane runs" reading is not met and the `src/progression/**`-only trigger is unobserved in CI; a rule-level test exists. The cost summary was shared on 2026-10-03. `INDEX.md` carries a closure-readiness audit (21 criteria: 10 MET, 8 MET-with-caveat, 2 NOT MET, 1 NOT EXERCISED; no epic status text changed): blockers are B4, C2 and C4. The audit's two documentation findings (the guide's parallel triage list, the dead README link) were fixed in the same change.
