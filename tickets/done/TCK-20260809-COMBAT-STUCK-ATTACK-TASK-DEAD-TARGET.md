---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET

## Title
An entity's `ATTACK` task persists and re-dispatches every tick against the same `target_id` —
including one already dead — with no self-correcting reset, bypassing the tactical-brain cadence
gate entirely

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Direct follow-up to the user's own combat-continuation request. Originally scoped as
"multi-attacker pileup on an already-dead target" (a guess from a real but small sample of 62
`ReasonCode.TARGET_INCAPACITATED` legality failures observed during
`TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`'s own real corpus re-verification). Re-verified with
a dedicated live probe before filing — the real finding is more precise and more significant than
the original guess, and is disclosed as a correction, not silently substituted.

**Real, confirmed finding**: `TARGET_INCAPACITATED` fires at real, substantial volume (128 and
144 occurrences across 2 separate clean 2000-tick `dungeon_crawl` re-runs — run-to-run variable
like every other real combat signal in this corpus, but consistently large, not a one-off). Stack-
trace capture on the real failing call confirms the source: `SimulationDomainLogic.execute_action`
→ the real `ATTACK` action dispatch path (not an opportunity attack — `is_opportunity_attack=False`
in every sampled failure), repeatedly targeting the same already-dead entity (`target.combat.alive
== False`, `target.lifecycle.active == False`).

**Root cause, traced through the real scheduling/action-resolution pipeline** (not assumed):
1. `tactical.py`'s deliberate `ATTACK` emission sets `task.work_kind_set="ENTITY_ACT"` with a
   payload including `target_id` (line ~657-671).
2. `src/engine/pipeline_phases/actions.py`'s own legality/readiness failure handling
   (lines 131, 148) preserves the **entire original payload** on failure —
   `payload_set={**payload, "outcome": "FAILURE", "reason": reason_value}` — `target_id` and
   `action: "ATTACK"` are never cleared. This mirrors the file's own established
   "reset to idle on success" pattern (`is_survival and outcome == "SUCCESS"` →
   `payload_set={}`, line 192-193), but that reset is scoped to `EAT`/`REST`/`SLEEP` only —
   `ATTACK` has no equivalent failure-triggered reset.
3. `src/engine/scheduler.py`'s own `select_work()` (lines 56-95) determines whether an entity's
   next dispatch goes through the brain-cadence gate: `is_idle_act = (work_kind == "ENTITY_ACT"
   and not ent.task.payload)`. Because the payload is never actually empty (it still carries the
   stale `target_id`), `is_idle_act` is always `False` here, so `is_brain` is `False`, so the
   `should_run(tick, entity_id, cadence.strategic_intelligence)` cadence check
   (`TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`'s own real cadence finding) **never applies at
   all** to a stuck `ATTACK` task — it is dispatched as `ENTITY_ACT` unconditionally, every
   single tick, with the identical stale payload, until something else (not yet identified —
   e.g. a hostile-list change reaching the entity through an unrelated code path) eventually
   forces a fresh brain decision.

This is the same general *class* of staleness bug as the sibling `PURSUIT-PER-TICK-TRACE` fix
(a real decision going stale between brain re-evaluations), but structurally distinct and
arguably worse: the pursuit-target fix concerned a *movement* target going stale for up to ~10
ticks between cadence-gated re-evaluations; this bug means a failed `ATTACK` decision is retried
**every tick with no cadence gate at all** once the target is no longer legally attackable,
wasting a real work-item dispatch every tick for an unknown, possibly unbounded duration.

## Scope
1. **Investigate**: confirm the exact mechanism that eventually clears the stuck task (if any —
   determine whether it's bounded by something real, e.g. a hostile-list-driven interrupt, or
   whether it can persist indefinitely for an isolated entity with no other hostiles nearby to
   trigger a fresh decision). Confirm whether this bug affects only the `TARGET_INCAPACITATED`
   failure mode or also `INSUFFICIENT_READINESS`/`OUT_OF_RANGE`/other legality failures on a
   *live* target (i.e. whether an entity can get stuck retrying a legal-but-currently-blocked
   attack for many ticks too, not just a dead-target case).
2. **Plan**: design the real, minimal reset — likely extending the existing `is_survival`-style
   "reset to idle on failure" pattern to `ATTACK` specifically when the failure reason is
   `TARGET_INCAPACITATED` (an unrecoverable failure — the target is gone, retrying is never
   going to succeed), while leaving `INSUFFICIENT_READINESS`/`OUT_OF_RANGE` failures un-reset if
   Investigate confirms those are expected to legitimately retry (readiness naturally regens;
   range may close via a fresh brain-driven pursuit decision).
3. **Implement**: the minimal fix.

## Out of Scope
- The brain-cadence mechanism itself (`SystemCadence.strategic_intelligence`) — untouched, same
  precedent as the sibling pursuit-tracking ticket.
- Any change to `resolve_attack`/`calculate_damage`/combat resolution logic itself.
- Building a general "task staleness" framework across all action types — scoped to the real,
  confirmed `ATTACK`/`TARGET_INCAPACITATED` case first; broader generalization is a future,
  separate question if Investigate finds the same pattern recurring elsewhere.

## Acceptance Criteria
- [x] investigation.md re-confirms the real mechanism and quantifies its real scope — confirmed
      unbounded in the observed sample (180+ real ticks, no natural end observed); confirmed
      only `TARGET_INCAPACITATED` is affected (`INSUFFICIENT_READINESS`/`OUT_OF_RANGE` naturally
      resolve via the existing readiness gate)
- [x] A concrete, minimal fix is designed and implemented
- [x] Real corpus re-verification: **confirmed, dramatic drop** — `TARGET_INCAPACITATED` volume
      fell from 128-144 (pre-fix) to exactly 4 per run (post-fix, matching the expected,
      legitimate 2-pass-architecture cost with the stuck-task condition eliminated) — a genuine
      ~35x real reduction, consistent across 3 clean re-runs
- [x] Scoped pytest passes — 206 passed, 1 pre-existing unrelated failure

## Related Tickets
- TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE (DONE, same session — the sibling staleness fix for
  movement targets; this ticket is the same class of bug for the `ATTACK` action itself)
- TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE, TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX,
  TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX (DONE, same session — the combat-volume
  investigation chain this ticket continues)

## Related Docs
- `docs/mechanics/02_combat_laws.md` §7 (Action Legality & the Readiness Gate)
- `docs/engine/contracts/combat_contract.md` §1 (Combat Legality Rules)

## Related Stored Artifacts
None yet — will be created at
`staging_artifacts/TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET/` during implementation.

## Related Code Areas
- `src/engine/pipeline_phases/actions.py` (the real failure-handling site, lines 121-216)
- `src/engine/scheduler.py` (`select_work()`, the real `is_idle_act`/cadence-gate interaction)
- `src/engine/tactical.py` (the real `ATTACK` emission site, for reference)

## Assumptions / Open Questions
- Whether the stuck-task condition is ever self-correcting for an isolated entity with no other
  hostiles nearby — left to Investigate, per the Uncertainty Rule.

## Implementation Notes
- `src/engine/pipeline_phases/actions.py::route()` — extended the existing `is_survival`-style
  reset-to-idle pattern: `payload_set={}` now also fires when `action == "ATTACK"` and the
  failure `reason_value == ReasonCode.TARGET_INCAPACITATED.value` — an unrecoverable failure
  (the target is dead/inactive; retrying the same `target_id` can never succeed).
- Confirmed via live per-tick trace that readiness staying at `100.0` on every observed failure
  was *not* a contradiction of the stuck-task theory — `combat_actions.py::execute_attack()`'s
  own real `-50.0` illegal-target readiness penalty regenerates back to 100 in ~5 real ticks
  (default `readiness_speed=10.0/tick`), closely matching the observed ~6-tick real repetition
  interval — a self-sustaining cycle with no natural end.
- Confirmed, disclosed, and deliberately left untouched: a real, legitimate 2-pass architecture
  (`Kernel._phase_collection()`'s own parallel-worker Collection phase, then
  `AuthoritativeApplyPipeline._route_action_intent()`'s own same-tick refinement pass) means each
  real attack attempt is legitimately checked twice per tick by design —
  `actions.py::route()`'s own docstring explicitly documents this same-tick-ordering law ("If
  actor A kills target T earlier in this refinement pass, actor B must see T as incapacitated
  later in the same pass"). Not a bug; the post-fix `TARGET_INCAPACITATED` count of exactly 4
  per run (2 distinct pairs × 2 real dispatches each) matches this expected cost precisely.
- `INSUFFICIENT_READINESS`/`OUT_OF_RANGE` deliberately NOT reset — both are real, recoverable
  conditions (readiness regens naturally; range may close via a fresh pursuit decision), unlike
  a dead target which can never become legal again. Resetting on every failure reason would have
  been a larger, unjustified behavior change beyond this ticket's own confirmed evidence.
- Original ticket framing ("multi-attacker pileup on an already-dead target") corrected during
  investigation to the real, more precise mechanism (a single stuck attacker/dead-target pair
  repeating for hundreds of ticks) — disclosed as a correction in investigation.md, not silently
  substituted.

## Test Summary
- 5 new unit tests in `tests/unit/actions/test_action_routing_task_reset.py`: dead-target reset,
  incapacitated-but-alive-target reset (confirms the fix isn't narrowly tied to `combat.alive`
  specifically), `INSUFFICIENT_READINESS`/`OUT_OF_RANGE` preserved unchanged, missing-action
  short-circuit unaffected — all pass.
- Full scoped re-run: `tests/unit/actions/ tests/unit/combat/ tests/unit/tactical/
  tests/unit/movement/ tests/unit/kernel/` — 206 passed, 1 pre-existing unrelated failure
  (`test_normal_move_triggers_oa`).
- Real corpus re-verification (2000-tick live `Kernel.tick_once()` loop, `dungeon_crawl_seed42`,
  corpus-default flags, 3 clean re-runs): `TARGET_INCAPACITATED` volume dropped from 128/144
  (pre-fix, one stuck pair repeating 180+ ticks) to exactly 4 per run (post-fix, 2 distinct pairs
  × 2 legitimate same-tick dispatches each) — a genuine, consistent ~35x real reduction across
  all 3 re-runs.

## Files Changed
- `src/engine/pipeline_phases/actions.py` — the real task-reset fix.
- `tests/unit/actions/test_action_routing_task_reset.py` — 5 new tests (new file/directory).
- `docs/mechanics/02_combat_laws.md` §7 — documented the new task-reset behavior.
- `docs/parity_ledger/combat_movement.yaml` — COMB-307.

## Completion Summary
Fixed the first of the user's own 3 requested combat follow-ups. Traced "multi-attacker pileup
on an already-dead target" to its real, more precise mechanism: a single entity's `ATTACK` task,
once emitted against a target that subsequently died, was never cleared — it bypassed the
tactical-brain-cadence gate entirely and got re-dispatched every tick readiness recovered from
its own real illegal-target penalty, repeating for 180+ real ticks against the same corpse with
no natural end. Extended the codebase's own existing survival-action reset-to-idle pattern to
this specific, unrecoverable failure case, deliberately leaving recoverable failures
(`INSUFFICIENT_READINESS`/`OUT_OF_RANGE`) untouched. Real corpus re-verification confirms a
genuine ~35x reduction in wasted attack attempts, consistent across repeated runs. Also
discovered and confirmed as legitimate (not a bug) a real 2-pass same-tick action-resolution
architecture that explains the exact post-fix residual count.
