---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS
phase: open
date: 2026-10-15
tags: []
---

# TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS

## Title
One standard command measures a behaviour step as a paired run (base arm vs new arm), so every M0 step is measured the same way and the base-vs-base spread (SE and floor for the cumulative watch table) comes from the same tool.

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Each behaviour step (diet, route, cover, level-keeps-kind, ...) has been measured with a hand-written, per-step probe. rpg-planner asked for one command (brief to rpg-implementer-2, 2026-10-15) so the paired table is the same every time and the cumulative watch table (D76) has a defined SE and floor.

## Scope
- A tool under `tools/test_architecture/` (base: `rpg_gate_run.build_kernel`, `/tmp/paired_cod.py`) taking `--base <rev> --new <rev>` and running frontier_living_world, urban_political, crowded_frontier (+ highland_traverse with `--terrain`), seeds 42-46, 5000 ticks. No shorter tick option for behaviour steps.
- audit_mode FORCED and recorded in the header, with a base-vs-base self-check arm; refuse a pair whose manifests are not host-independent (`require_host_independent_runs`; `audit_mode` and `signals_zeroed` into the header). Explicit PYTHONHASHSEED.
- People = a typed set that is the same in both arms: entities present at tick 0 whose species keeps coin (`is_person`) in the BASE arm, matched by entity id; reported like-for-like. Anything born later is listed apart as "added". The arm roster at tick 0 is compared and a mismatch is reported in the header, never silently pooled (the keeps_coin problem of the diet table).
- Table: deaths and alive by kind group with cause (read from `lifecycle.death_record`, never reconstructed), people deaths per seed, steps / move episodes / pre-check refusals by terrain, flee / pursuit / perception counters, a slot for the step's headline metric, extinctions per world, base-vs-base spread (SE, floor).
- Typed counters (hash-neutral, outside the canonical state): added to the run ledger observer; definitions in the Implementation Notes, confirmed by rpg-planner.
- Arm results cached by commit hash (step N child arm = step N+1 parent arm). Summary tables only; run data cleaned by run id after each pair (`done_checker_static.py --clean-data-runs`).
- `--neutral`: byte-identical state-hash check on 3 worlds at 1 seed.
- Builds so a measure-once-at-fold mode and a cumulative watch table are possible (designer proposals 1, 3, 7a are with the user; not built here).

## Out of Scope
- Changing any simulation behaviour or any gate threshold.
- Recording baseline v1 (testing's harness job).
- The cumulative watch table itself (rpg-planner keeps it).
- Wiring `require_host_independent_runs` into the older comparators (testing, simq).

## Acceptance Criteria
1. `--neutral` on the current tip against itself: identical hashes, 3 worlds, seed 42.
2. A base-vs-base run of 3 worlds x 5 seeds is identical on every table cell (spread 0), and the tool writes SE and floor.
3. A pair whose manifests lack `signals_zeroed: true` is refused with the run names.
4. The people set is identical in both arms or the table is like-for-like with the mismatch named; a test pins both.
5. Counters are zero-effect on the state hash (proved by the `--neutral` check and a unit test), and have unit tests.
6. Cache: a second pair sharing an arm re-runs only the new arm.
7. No run data left behind (cleaned by run id).

## Related Tickets
- TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH (cause source)
- TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR (`require_host_independent_runs`)
- TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS (run ledger, kind_group)

## Related Docs
- docs/guidelines/intentional_divergences.md (2.127 diet: like-for-like table)
- .claude/handover/drafts/M0-CUMULATIVE-WATCH-TABLE.md (D76)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH/probes/ (death_proof.py, driver)

## Related Code Areas
- tools/test_architecture/rpg_gate_run.py, src/observability/run_ledger.py, src/ai/goals/kind_group.py, src/observability/reporting/run_determinism.py, src/core/movement_modes.py

## Assumptions / Open Questions
- Counter definitions (flee, pursuit, perception) await rpg-planner's confirmation; a definition that touches Lane A or C code is forwarded by the planner.
- The knowledge index and graphify graph were absent in this worktree at filing time; context was gathered by direct reads.

## Implementation Notes
(to be filled)

## Test Summary
(to be filled)

## Files Changed
(to be filled)

## Completion Summary
(to be filled)
