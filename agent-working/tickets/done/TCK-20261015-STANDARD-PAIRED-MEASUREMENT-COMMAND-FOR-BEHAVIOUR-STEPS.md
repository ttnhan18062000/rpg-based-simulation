---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS
phase: done
date: 2026-10-15
tags: []
---

# TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS

## Title
One standard command measures a behaviour step as a paired run (base arm vs new arm), so every M0 step is measured the same way and the base-vs-base spread (SE and floor for the cumulative watch table) comes from the same tool.

## Status
DONE

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
- Counter definitions confirmed by rpg-planner (2026-10-15). The owner's D76 floor (1 people death per seed per world, more deaths only stops, fewer is report-only) was built in, replacing the placeholder.
- Pre-check refusals have no typed record at this commit: the table says "not measured".
- The tool sits in `tools/rpg_measure/` (rpg_gate_run.py is in testing's tools/test_architecture/; it is imported, not edited).
- The knowledge index and graphify graph were absent in this worktree at filing time; context was gathered by direct reads.

## Implementation Notes
- Counters (run ledger, non-authoritative observer, keys `measure|kind_group|person`): `flee_ticks`/`flee_episodes` (MovementMode RETREAT), `pursuit_ticks`/`pursuit_episodes` (PURSUE, INTERCEPT), `steps|<terrain entered>`, `perceiving_ticks`/`perceived_hostiles` from `perceived_hostiles` every 10 ticks, `perception_samples` in the tally.
- Tool: `python -m tools.rpg_measure.paired --base <rev> --new <rev> --step ... --div ... [--terrain] [--jobs 2] [--floor-per-seed 1] [--self-check seed42|full|off] [--headline <counter prefix>] [--neutral] [--clean-cache] [--out file]`. Arms are `git archive` trees under `$RPG_MEASURE_CACHE` (default /mnt/data/scratch-rpg-measure); results cached by commit + child-script hash + ticks; a base arm older than the counters reports them n/a.
- People = base arm tick-0 keeps_coin roster by id, read on the same ids in both arms; added ids listed apart; roster mismatch named.
- Verdict per world (owner's D76 ruling): SE = SD(per-seed new-base)/sqrt(n seeds); STOP when more people deaths by > 2 SE AND > floor (1 per seed, total = seed count); fewer past both is REPORT-ONLY; SD 0 not special-cased. Extinctions: STOP / base-state / recovered. Watch-table rows are emitted per world.
- A cumulative run takes `--base` pinned to the pre-M0 commit (rpg-planner names it at the first cumulative check).
- Follow-up (rpg-planner, 2026-10-16, same ticket): a pre-M0 base (STOP base 903239fbe, and a REPORT-ONLY reading against c3f6202b9) predates the determinism fix, so its manifest has no typed audit_mode/signals_zeroed. `--legacy-base` / `--legacy-new` accept such an arm only when the child verified its kernel was built with audit_mode and no_frame_pacing, the manifest never recorded live signals, and a full base-vs-base repeat (all worlds x seeds) is byte-identical (`--self-check full` is required); the header then says "legacy base, audit proven by repeat". `--report-only` suppresses STOP (verdicts and extinctions) and labels the output and the watch rows report-only.

## Test Summary
tests/unit/observability/test_run_ledger_behaviour.py (7), tests/unit/tools/test_rpg_measure.py (11), tests/unit/observability and tools sweep 1174 passed; health 0 new / 0 worse; lint-imports 17 kept / 0 broken.
Proofs: `--neutral` (base 1a19b9b41 vs the counters commit, 3 worlds, seed 42, 1000 ticks): IDENTICAL x3. Base-vs-base (commit 63b98e76b, 3 worlds x seeds 42-46 x 5000 ticks, full 15-run repeat): byte-identical final and start hashes, fates and counters (spread 0); table in the stored artifacts. Unmeasured: a real pair with a changed arm (the first use is the next behaviour step).

## Files Changed
src/observability/run_ledger.py; tools/rpg_measure/{__init__,arm_child,stats,paired}.py; tests/unit/observability/test_run_ledger_behaviour.py, tests/unit/tools/test_rpg_measure.py.

## Completion Summary
The standard paired-measurement command exists and is proven neutral and deterministic: ledger counters for flee, pursuit, steps by terrain and sampled perception (hash-neutral, proved by `--neutral`), and `tools/rpg_measure` with the owner's D76 floor, SE from per-seed differences, extinction check, people-by-id like-for-like, arm cache, forced audit_mode with a base-vs-base self-check, host-independence refusal and watch-table rows. Not built: pre-check refusal counts (no typed record), the measure-once-at-fold mode and the cumulative table (designer proposals pending). Branch rpg-paired-measure, not pushed.
