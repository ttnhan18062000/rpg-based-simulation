---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-CONSERVATION-MUTATION-BASELINE
phase: done
date: 2026-09-29
tags: [testing]
---

# TCK-20260929-CONSERVATION-MUTATION-BASELINE

## Title
Record the mutation baseline for `src/core/conservation.py` as a tracked record

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Epic A criterion A.5 (effectiveness half): a mutation record for one declared target, with full
provenance. Target confirmed by rpg-feature-planning (2026-09-29) as the real atomic conservation law,
stable since 2026-07-02; economy shims and `src/core/inventory.py` excluded with reasons recorded.
Recorded as a data record with no tooling built; classified hotfix because it adds one measured data
file and a shape test, no behaviour.

## Scope
- One JSON record per declared target under `tests/mutation/baselines/` (precedent: `tests/perf/baselines/`;
  not `reports/*`, which is gitignored, and not `docs/`, which would pull it into frontmatter/REGISTRY rules).
- A shape/consistency test (`tests/mutation/test_mutation_baseline_records.py`).

## Out of Scope
- Killing survivors (needs written-down expected conservation behaviour, i.e. RPG logic): sent to rpg-feature-planning as information.
- The report layer that reads the record and computes staleness (Epic A batch 2).
- Adding mutmut as a project dependency; any CI job; classifying equivalent mutants.

## Acceptance Criteria
1. The record holds target path + sha256, source SHA, UTC start, runtime, tool/version/install, selected tests + count, killed/survived/timeout/suspicious counts, `equivalent: not-classified`, and every survivor with id, file:line and diff.
2. The record's counts and survivor list are internally consistent (test-enforced).
3. The run is marked real-target, with the confirmation and exclusions recorded.

## Related Tickets
- `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY`

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §4.7

## Related Stored Artifacts
None.

## Related Code Areas
`tests/mutation/`; `src/core/conservation.py` (read-only).

## Assumptions / Open Questions
- mutmut 3.x cannot run here (its trampoline rejects `src.`-prefixed module paths); 2.5.1 was used from a private install.
- Equivalent mutants are unclassified; all survivors are unreviewed.

## Implementation Notes
Ran in a scratch copy of the tree (mutmut 2.x mutates in place); no tracked source changed.

## Test Summary
`pytest tests/mutation`: 3 passed. Run: 177 mutants, 60 killed, 117 survived, 0 timeout, 0 suspicious, in 5m41s over 165 tests.

## Files Changed
`tests/mutation/baselines/src_core_conservation.json`; `tests/mutation/test_mutation_baseline_records.py`; `tests/mutation/__init__.py`.

## Completion Summary
Record written and test-guarded. 7 of 117 survivors fall in three material categories (accepted flag flipped on OUT_OF_STOCK/TARGET_LOCKED, LOOT delta sign, CORPSE reservation key), listed first for review and sent to rpg-feature-planning. Gate note: bare done_checker_static reports known false positives tracked in TCK-20260929-DONE-CHECKER-POST-CLOSURE-FALSE-FAILS; `--part finalize` is the correct post-closure check.
