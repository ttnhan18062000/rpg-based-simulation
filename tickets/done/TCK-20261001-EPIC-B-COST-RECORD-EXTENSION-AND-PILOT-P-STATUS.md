---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261001-EPIC-B-COST-RECORD-EXTENSION-AND-PILOT-P-STATUS
phase: done
date: 2026-10-01
tags: [testing]
---

# TCK-20261001-EPIC-B-COST-RECORD-EXTENSION-AND-PILOT-P-STATUS

## Title
Extend the Epic B scenario-lane cost record to PRs #272-#276, record pilot P as blocked/inconclusive, and record the Epic D CI-gap limits

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Records only, no product code. Requested through test-architecture-reviewer (plan approved by them 2026-10-01): add the PRs merged since #275 to Epic B's criterion 4 cost record, fix the attribution of the e75ff2e77 failure, record pilot P's status in the pilot report, and restate the Epic D CI-gap closure with its limits.

## Scope
- Epic B cost record: rows for #272, #273, #274, #276 (final heads, full 40-character SHA queries), one fixed routing vocabulary, a header note that routing counts are recomputed locally, Perf wall time labelled as including non-scenario work.
- e75ff2e77 attribution: my own earlier report plus fix `248372a26`; only the failing job and step names confirmed.
- Pilot report: capability row 8 (pilot P blocked/inconclusive, no settled progression ticket yet, dated planner confirmation) and a cost-record update in the CI addendum.
- Epic D limit (4) and the INDEX row updated to the 6-PR record, without any claim that all gaps are closed.

- Folded in after review (same PR, per the user's request relayed by the reviewer): a #278 row (earlier head `343a88093`, run 36890190328, both Scenario lane and Perf skipped, only tickets/docs/monitoring paths changed) recorded as the first **docs-only skip**; the record is then 7 PRs and the docs-only skip leaves the unobserved list. The src/progression trigger stays unobserved.

## Out of Scope
- Mutation baseline v2 curated additions (the user's call, not asked).
- Launching pilot P, any product code, any `progression.yaml` id, promoting the lane.
- #277 (still open when written).

## Acceptance Criteria
1. Four new rows match the Actions runs and jobs API for the named head SHAs; #274 and #276 are recorded as skipped with Perf as the executing job, never as docs-only skips.
2. Every row carries a routing category (real trigger match / tests-only fail-open / skipped, Perf covers it); src/progression trigger and docs-only skip stay in the unobserved list.
3. Pilot report row 8 says blocked/inconclusive (no settled progression ticket yet; no candidate currently identified), with one clause noting the surface-stability merge gate was satisfied by #276; no oracle id is assumed.
4. Epic D text contains no "all gaps closed" claim; all four epics stay `phase: open` in tickets/todos/test-architecture/.

## Related Tickets
TCK-20261001-EPIC-B-SCENARIO-LANE-COST-RECORD, TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION, TCK-20260929-EPIC-CORE-RPG-TEST-PILOT, TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS

## Related Docs
docs/testing/core_rpg_test_pilot_2026-09-30.md, docs/plans/test_architecture/roadmap.md (§6)

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- tickets/todos/test-architecture/
- docs/testing/

## Assumptions / Open Questions
- Route: hand-orchestrated hotfix.
- Test counts and CI step summaries were not retrievable (run logs blocked); counts recorded as "not recorded".
- Only final heads of #272-#276 are recorded; earlier heads are not enumerated.

## Implementation Notes
Runs: #272 `ff60cc2b8` run 36816354840 (lane success 46 s), #273 `e67f7ad03` run 36827697928 (lane success 52 s), #274 `8822eecf5` run 36844103080 (lane skipped, Perf success 131 s, `Makefile` matches `PERF_RE`), #276 `e6edcb70d` run 36867926153 (lane skipped, Perf success 144 s). `tests/tools/` has been a trigger class since #267, so #272 is a real trigger match, and #273 is the first row routed by a changed `tests/mechanic_scenarios/` file.

## Test Summary
Text only. Frontmatter and registry checks run after the edit.

## Files Changed
tickets/todos/test-architecture/TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION.md; tickets/todos/test-architecture/TCK-20260929-EPIC-CORE-RPG-TEST-PILOT.md; tickets/todos/test-architecture/INDEX.md; docs/testing/core_rpg_test_pilot_2026-09-30.md; docs/REGISTRY.yaml.

## Completion Summary
Cost record is at 7 of about 10 PRs: lane ran and succeeded on four (#271, #272, #273, #275), was skipped on two because Perf covered the scenario tests (#274, #276), and was skipped on one as a docs-only skip (#278, an earlier head, later heads not enumerated). The src/progression trigger remains unobserved; criterion 4 stays open. Pilot P is recorded as blocked/inconclusive (no settled progression ticket yet; no candidate currently identified); the earlier surface-stability merge gate was satisfied by #276 (`786f9ee9b`). Epic D limits restated with no "all gaps closed" claim.
