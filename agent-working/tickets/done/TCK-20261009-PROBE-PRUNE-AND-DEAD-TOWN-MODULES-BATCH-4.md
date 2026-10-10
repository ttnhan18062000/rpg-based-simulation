---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20261009-PROBE-PRUNE-AND-DEAD-TOWN-MODULES-BATCH-4
phase: done
date: 2026-10-09
tags: [documentation, registry]
---

# TCK-20261009-PROBE-PRUNE-AND-DEAD-TOWN-MODULES-BATCH-4

## Title
Prune raw probe output from stored artifacts (keep scripts plus one summary table per probes directory) and delete the dead `src/town/inn.py` and `src/town/home.py`

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Batch 4 of the material-economy chain, queued since batch 2. `agent-working/stored_artifacts/**/probes` held 432 files (5.95 MB): 171 raw `.out` files and 65 `.jsonl` files that only reproduce what the scripts regenerate. `InnAction` and `HomeAction` had no caller since batch 2 moved bed, meal and sale to action time (`building_services.py`).

## Scope
- Delete raw probe output that no document or ticket cites by path; keep scripts, READMEs and tables.
- Condense four directories whose only results were raw rows into one table each: the three decision-32 summaries, the decision-36 summary (the citation in its investigation now points to the table), the entity-move probe rows and the conflict-04 trace rows.
- Delete `src/town/inn.py`, `src/town/home.py`, their test `tests/unit/world/test_recovery_class_hall.py`, their 8 code-health ratchet rows; update `docs/simulation/town_contract.md` (Home Rest) and the pinned mechanism-registry counts (323 to 321 files, 236 to 234 unbound).
- Carry rpg-planner's commit binding batch 2's modules to `town_services` in `mechanisms.yaml`.

## Out of Scope
- Changing any simulation behaviour.
- Pruning anything a document cites by path (the 25 cited raw files and the 24-world contamination rows stay).

## Acceptance Criteria
- [x] Probes directory size reported before and after.
- [x] No citation of a removed file remains (checked with `git grep` over the whole repo, excluding monitoring data).
- [x] Mechanism registry tests, ratchet and import-linter pass.

## Related Tickets
- TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02

## Related Docs
- `docs/simulation/town_contract.md`

## Related Stored Artifacts
- The pruned `probes` directories.

## Related Code Areas
- `src/town/inn.py`, `src/town/home.py` (deleted)

## Assumptions / Open Questions
- The unreachable-code audit snapshot `docs/audits/unreachable_code_inventory.json` is a dated record and still lists the two classes.

## Implementation Notes
`agent-working/stored_artifacts` (apparent size): 49,722,623 bytes before, 44,725,318 after (-4,997,305). Probes directories: 432 files / 5,951,246 bytes before, 208 files / 1,015,488 bytes after (includes the 4 new tables). Also the batch-2 probes now carry the arm7 trace scripts and one summary table.

## Test Summary
Mechanism registry tests (101), architecture, docs and world unit tests.

## Files Changed
See the PR.

## Completion Summary
Done in the batch-4 PR.
