---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-MUTATION-BASELINE-V3-SUPERSET-SELECTION
phase: done
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-MUTATION-BASELINE-V3-SUPERSET-SELECTION

## Title
Record mutation baseline v3 for src/core/conservation.py on a selection that contains v1's and v2's, superseding v2

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Optional scope from the mutation-baseline v2 work, shipped with the test-architecture closure (the user's "finalize a feature completely" rule, relayed by test-architecture-reviewer, approved 2026-10-03): add `tests/unit/content/test_resolvers.py` and `tests/unit/quest/test_quest_rewards.py` (both in v1's selection, both recorded as known exclusions in v2) to the selection so the baseline selection contains v1's and v2's, re-run with the pinned `mutmut` 2.5.1 from a scratch copy, and record a new baseline that supersedes v2. This also resets the staleness clock.

## Scope
- `tests/mutation/baselines/src_core_conservation_v3.json`: a new record with `supersedes: src_core_conservation_v2.json`, the curated additions and their reason, the 11-file selection and its hash, run provenance, the reproduction command, and the survivors.
- The run: `mutmut` 2.5.1 (`pip --target` in a scratch directory), a scratch copy of `c0980e27a` made with `git archive`, outside the repo, started detached with `setsid`, cleared `.mutmut-cache`.
- Compare the survivors one by one with v2's.
- Roadmap watch item (e): updated to v3's staleness date.

## Out of Scope
- Changing the target, the rule, or any test; adding `mutmut` as a project dependency (the dependency source belongs to another team); any other target; any survivor classification or fix.
- Editing v1 or v2 (kept unchanged as history).

## Acceptance Criteria
1. v3's selection is a superset of v1's and v2's, recorded with `curated_additions`, its reason and its hash.
2. The run's provenance is complete (tool version, scratch copy, source SHA, times, command) and the target `sha256` equals v2's.
3. The survivors are compared with v2's one by one and the result is stated.
4. The core-RPG report reads v3 as fresh and v2 as superseded; `tests/unit/tools/test_mutation_baseline_records.py` passes.
5. No score comparison across baselines is claimed.

## Related Tickets
TCK-20260929-CONSERVATION-MUTATION-BASELINE, TCK-20261001-TEST-LANE-ROUTING-COST-VIEW-BASELINE-V2, TCK-20261003-EPIC-B-ROWS-279-288-AND-CLOSURE-READINESS-AUDIT

## Related Docs
docs/plans/test_architecture/roadmap.md (section 6 watch item e)

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- tests/mutation/baselines/
- tools/test_architecture/mutation_selection.py (read only)

## Assumptions / Open Questions
- Route: hand-orchestrated hotfix.
- `src/core/conservation.py` has not changed since v2 (`sha256` `bb5484eb...`), so the positive control is reused on the same three equality checks as v2.

## Implementation Notes
Run 2026-10-03T06:02:25Z to 06:10:27Z (482 s), 11 test files (229 tests), 177 mutants: 152 killed, 25 survived. The 25 survivors have the same ids and the same diffs as v2's (checked with `mutmut show`). On this target the two added files killed no additional mutant; that is an observation about these two files here, not proof they are redundant. The core-RPG report (`--as-of 2026-10-03`) shows v3 fresh and v1 and v2 superseded. v3 goes stale 30 days after its run (about 2026-11-02) or when the target or selection changes.

## Test Summary
`tests/unit/tools/test_mutation_baseline_records.py` (7 passed), `test_core_rpg_report.py` and `test_mutation_selection.py` (48 passed).

## Files Changed
tests/mutation/baselines/src_core_conservation_v3.json; docs/plans/test_architecture/roadmap.md (watch item e); docs/REGISTRY.yaml.

## Completion Summary
Baseline v3 recorded: same 177/152/25 and the same 25 survivors as v2 on a larger selection, so the two added files add no kills on this target. v2 is superseded and v3 resets the staleness clock to about 2026-11-02. The mutation caveat that `mutmut` is not a project dependency stays.
