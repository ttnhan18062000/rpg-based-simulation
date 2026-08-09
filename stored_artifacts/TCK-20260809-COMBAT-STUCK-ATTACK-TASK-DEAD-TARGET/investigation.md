---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET

## Methodology
Real, live-instrumented probes against a real 2000-tick `dungeon_crawl_seed42`
`Kernel.tick_once()` loop — monkey-patched `LegalityServiceV2.verify_attack_legality` to capture
tick, attacker/target IDs, attacker readiness, and real call-site stack traces on every real
`TARGET_INCAPACITATED` failure. Probe scripts lived in scratchpad, not the repo.

## Re-confirmed: real, substantial volume, one stuck (attacker, dead-target) pair per run
`TARGET_INCAPACITATED` fires at real volume (128, 144, and 62 occurrences across 3 separate
clean re-runs — the 62-occurrence run's own real distinct pair was `(8, 15)`, the two
128/144-occurrence runs both isolated to the same `(8, 20)` pair). In every observed run, the
volume comes from a **single, real (attacker, dead-target) pair repeating for hundreds of real
ticks** — not many different pairs, and not simultaneous multi-attacker pileup as originally
guessed when this ticket was filed (a real correction, disclosed here, not silently substituted).
Real tick span for the isolated `(8, 15)` case: ticks 819-999 (a 180-tick real window), firing
every real 6 ticks, twice per firing (explained below).

## Root cause, fully confirmed via direct source read + live evidence
1. `tactical.py`'s deliberate `ATTACK` emission (line ~657-671) sets `task.work_kind_set=
   "ENTITY_ACT"` with a payload including a real `target_id`.
2. `src/engine/pipeline_phases/actions.py::route()`'s own failure-handling (lines 131, 148, 195)
   preserves the **entire original payload** on any legality/readiness failure —
   `payload_set={**payload, "outcome": "FAILURE", "reason": reason_value}` — `target_id` and
   `action: "ATTACK"` are never cleared. The file's own established "reset to idle" pattern
   (`is_survival and outcome == "SUCCESS"` → `payload_set={}`, line 192-193) is scoped to
   `EAT`/`REST`/`SLEEP` success only — `ATTACK` failure has no equivalent reset.
3. `src/engine/scheduler.py::select_work()`'s own real gate:
   `is_idle_act = (work_kind == "ENTITY_ACT" and not ent.task.payload)`. Because the payload is
   never actually empty (it still carries `target_id`), `is_idle_act` is always `False`, so
   `is_brain` is `False` — the entity's `ATTACK` task is **not gated by the tactical-brain
   cadence at all** (`SystemCadence.strategic_intelligence`, the sibling
   `TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE` ticket's own real finding) once emitted, only by
   the scheduler's own separate readiness gate (`if not is_brain and ent.combat.readiness <
   100.0: continue`, `scheduler.py` line 73).
4. **Why readiness reaches 100.0 again every ~5-6 real ticks, explaining the observed
   periodicity** (not a contradiction of the stuck-task theory, as first suspected): every
   sampled failure shows `attacker.combat.readiness == 100.0` at the moment of dispatch — because
   `combat_actions.py::execute_attack()`'s own real illegal-target branch applies a real
   `readiness_delta=-50.0` penalty on every failed attempt (confirmed source read, line ~50).
   Regenerating from 50 back to 100 at the real default `readiness_speed=10.0/tick` takes 5 real
   ticks — closely matching the observed ~6-tick real gap (off-by-one from tick-processing
   order). The scheduler's own readiness gate re-admits the stuck task the moment readiness
   recovers, the task fails again (same stale `target_id`, still dead), readiness drops again,
   repeat — a real, self-sustaining cycle with no natural termination point observed within this
   ticket's own real sample windows (180+ real ticks in the isolated case, likely longer;
   eventual termination — e.g. via some other real hostile appearing and forcing a fresh brain
   decision through a different code path — was not confirmed and is not required to justify the
   fix below).

## Real, disclosed, secondary finding — NOT a bug, confirmed legitimate architecture
Each real failure fires from **2 distinct real call sites within the same tick**:
(1) `Kernel._phase_collection()` → `ConcurrentExecutionAdapter.execute()` →
`default_simulation_worker` → `execute_action` (the Kernel's own real, parallel-worker Collection
phase, per `docs/engine/contracts/kernel.md`'s own 6-phase loop); (2)
`AuthoritativeApplyPipeline._route_action_intent()` → `actions.py::route()` → `execute_action`
(the separate 32-phase refinement pipeline's own `action_routing` phase, per
`docs/engine/contracts/authoritative_pipeline.md`). `actions.py::route()`'s own docstring
confirms this is intentional, not duplicate/wasted work: "Critical law: If actor A kills target T
earlier in this refinement pass, actor B must see T as incapacitated later in the same pass" —
the second pass exists specifically to re-validate same-tick ordering effects the first,
speculative/parallel pass could not see. **Not investigated further** (exact `readiness_delta`
merge-summation arithmetic across the two passes was not traced) — this ticket's own fix (below)
eliminates the stuck-task condition regardless of the exact double-pass cost accounting, making
that further trace unnecessary to justify the real fix.

## What this rules out
- Not readiness-blocked in the sense of "readiness too low to retry" — the opposite: readiness
  fully recovers between attempts, which is *why* the stuck task keeps getting re-admitted.
- Not the brain-cadence gate (`SystemCadence.strategic_intelligence`) — confirmed the stuck
  `ATTACK` task bypasses that gate entirely, a distinct mechanism from the sibling pursuit-
  tracking ticket's own finding.
- Not literal simultaneous multi-attacker pileup — a real correction to this ticket's own
  originally-guessed framing.

## Real fix candidate (for Plan phase)
Extend `actions.py::route()`'s own existing `is_survival`-style reset-to-idle pattern to `ATTACK`
specifically when the failure reason is `TARGET_INCAPACITATED` — an unrecoverable failure (the
target is dead/inactive; retrying can never succeed, unlike `INSUFFICIENT_READINESS` which
naturally resolves via regen, or `OUT_OF_RANGE` which may resolve via a fresh pursuit decision).
Clearing the payload (`payload_set={}`) makes the entity `is_idle_act`-eligible again, routing it
back through the real brain-cadence gate on its next scheduled opportunity instead of retrying
the same dead target indefinitely.

## Docs Requiring Update
- `docs/mechanics/02_combat_laws.md` §7 (Action Legality & the Readiness Gate) — no change to
  the documented law itself (readiness mechanics are unchanged); a note may be added about the
  real task-reset behavior once implemented.
