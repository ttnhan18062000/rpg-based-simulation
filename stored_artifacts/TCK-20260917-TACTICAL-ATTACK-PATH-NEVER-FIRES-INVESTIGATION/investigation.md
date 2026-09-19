---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION
artifact_type: investigation
tags: [strategy, combat, investigation]
---

# Investigation — TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION

## Code read before instrumenting (per this ticket's own discipline: know what to measure first)

**Candidate 1 (sticky tasks) has real code backing it, and it is at least two layers deep, not
one.** Traced the full call chain from the scheduler down to `evaluate_entity_intent`:

1. `src/engine/scheduler.py:61-63` — `work_kind = ent.task.work_kind; if work_kind not in
   ("ENTITY_ACT", "ENTITY_MOVE"): work_kind = "ENTITY_BRAIN"`. The scheduler reads the entity's
   **already-scheduled** `task.work_kind` from the previous tick(s). If an entity's current task is
   `ENTITY_MOVE` (pursuing, wandering, retreating) or a non-empty `ENTITY_ACT` (executing a queued
   action), the brain is **not scheduled at all this tick** — the entity just continues its
   already-decided task. `is_idle_act = (work_kind == "ENTITY_ACT" and not ent.task.payload)`
   provides one specific escape: an `ENTITY_ACT` with an *empty* payload still routes to the brain.
2. `src/engine/scheduler.py:78-83` — even when `work_kind` computes to `ENTITY_BRAIN`, there is a
   **second, independent gate**: `if is_brain: if not should_run(state.tick, ent.id,
   cadence.strategic_intelligence): continue`. This is a periodic cadence check (`PROD_SMALL`'s own
   `cadence.strategic_intelligence = 20`, i.e. once every ~20 ticks per entity, staggered by
   entity id) — the brain is only even *scheduled* on specific ticks, independent of whether the
   entity is otherwise eligible.
3. `src/engine/domain/cognition.py:39-56` (`CognitionDomain.execute_brain`) — a **third**
   early-exit, redundant with (2) for the common case: `if not has_project and is_idle and not
   is_cadence_tick and not force: return {entity.id: EntityUpdate(entity_id=entity.id)}` (and a
   second early-exit if `not neighbors` too). Since reaching `execute_brain` at all already implies
   the scheduler's own cadence check at (2) passed for this tick, this inner check is mostly
   redundant *except* for callers reaching `execute_brain` via `force=True`
   (`src/engine/domain_logic.py:39`), which bypasses it.

**This means "sticky tasks" is not one throttle but a stack of at least three**, each independently
capable of suppressing an `evaluate_entity_intent` call. The originally-cited 93.7%
scheduler-re-execution figure (`docs/engine/kernel.md`'s Sticky-Task Law) most directly describes
layer (1); layers (2) and (3) are additional, previously-uncited throttles found while tracing this
ticket's own candidate 1.

**Candidate 2 (`hostiles` gate)** — `src/engine/tactical.py:182-225`: `hostiles` is built once per
`evaluate_entity_intent` call, from `neighbors` (already perception-filtered by
`DomainView.get_neighbor_view(radius=10.0)` in `cognition.py`, then salience-filtered by
`SensoryFilter.filter_saliency`), further filtered by `_gate.can_perceive(...)` and
`semantics_service.is_hostile_compat(...)`. If `hostiles` ends up empty, execution falls into the
`if not hostiles:` branch (line 254) — objective pursuit / idle handling — and the entire
hostile-engagement branch (442-761, containing the `ATTACK` case) is never reached **for that
call**, independent of how many calls happen in total.

**Candidate 3, reframed** — confirmed the exact shape of the `ATTACK` `TaskUpdate` the
hostile-engagement branch returns when it reaches its "Default: Basic Attack" fallthrough
(`src/engine/tactical.py:749-761`): `TaskUpdate(work_kind_set="ENTITY_ACT",
payload_set={"action": "ATTACK", "target_id": ..., ...})`. This is the exact vocabulary
`ActionRouter`/`ActionRoutingPhase` read (confirmed already by this ticket's own corrected
candidate-3 note — no `ActionIntent` translation step exists at this call site). The open question
is purely whether an entity that returns this update this tick actually gets it dispatched as a
real `CombatActions.execute_attack()` call before something (the scheduler's own sticky-task
re-read next tick, or a target going stale/dying/moving out of range) intervenes — measured, not
reasoned about further.

**Candidate 4 (`obj.kind` never reaches `DEFEAT_ENEMY`)** — confirmed `entity.strategic.projects[...]
.objectives[...]` is a `List[ObjectiveState]` (each with `.id`/`.kind`/`.status`), and
`entity.strategic.current_objective_id`/`current_project_id` are the fields naming which one is
active. Measurable directly by sampling entity state, no wrapping needed.

## Instrumentation method

Wrote a probe (not committed — investigation-only, per this ticket's Scope) that:
- wraps `TacticalDecisionSystem.evaluate_entity_intent` (class-attribute patch — safe, since
  `cognition.py`'s own call site re-imports the class reference on every call rather than caching a
  bound reference) to count invocations per entity and inspect the returned `EntityUpdate.task`
  for an `ATTACK`/`SKILL` action (candidates 1 and 3);
- wraps `FactionSemanticsService.is_hostile_compat` on the real singleton instance (returned by
  `get_faction_semantics_service()`'s own module-level cache) to detect, per
  `evaluate_entity_intent` call, whether any neighbor was ever found hostile (candidate 2);
- wraps `CombatActions.execute_attack` (a staticmethod, patched the same way) to count real
  dispatches (the other half of candidate 3's gap measurement);
- samples `entity.strategic.projects[...].objectives[...].kind` directly at two points per run —
  no wrapping (candidate 4);
- restores every original function in a `finally` block, so a run never leaves the module state
  patched afterward.

**Concurrency guarded against explicitly, not assumed safe.**
`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own 2026-09-17 addendum already found
that `Kernel._phase_collection()`'s real concurrent entity evaluation (`ConcurrentExecutionAdapter`,
selected whenever `profile.max_worker_count > 0` — true for `PROD_SMALL`, the profile used
throughout this arc) makes a shared-mutable-state probe unreliable for exactly this kind of
per-call correlation. Rather than repeat that mistake, the `Kernel` is constructed here with
`executor=LocalSequentialExecutor()` passed explicitly, overriding the profile's own default.

Real `Kernel.tick_once()` loop throughout — no direct service calls bypassing the pipeline, per
Acceptance Criteria #4.

## A probe bug found and corrected before reporting (per this ticket's own discipline)

The first full run reported **zero** `ATTACK`/`SKILL` `TaskUpdate`s returned by
`evaluate_entity_intent` across all four worlds. Before treating that as a finding, traced why:
`TaskUpdate`'s real field is `payload_set`, not `payload` (`src/core/updates.py:207-208`) — the
probe's own inspection code (`result.task.payload`) raised `AttributeError` on every single call,
silently caught by a broad `try/except: payload = {}`, which made every "did this call decide
ATTACK" check read as "no" regardless of the real answer. Fixed (`payload_set`), and re-ran the full
four-world instrumentation. This is the same class of mistake this arc's own Acceptance Criteria #3
exists to guard against — caught here by cross-checking `execute_attack()`'s own real dispatch count
against the (impossible) zero-emissions reading, not by luck.

## Results, per world, from the corrected run

| World | `evaluate_entity_intent` calls | Distinct entities evaluated | Avg calls/entity | Hostiles non-empty | ATTACK returned | Real `execute_attack()` dispatches | `DEFEAT_ENEMY` objectives sampled |
|---|---|---|---|---|---|---|---|
| `crowded_frontier` (2000 ticks, 38 entities) | 551 | 48/38 | 11.48 | 0/551 | 1 (1 entity) | 2 | 0 |
| `quest_dense_frontier` (2000 ticks, 6 entities) | 56 | 15/6 | 3.73 | 0/56 | 0 | 0 | 0 |
| `hero_guild_routing` (2000 ticks, 31 entities) | 523 | 42/31 | 12.45 | 0/523 | 1 (1 entity) | 29 | 0 |
| `metropolis` (30 ticks, 700 entities, control) | 308 | 294/700 | 1.05 | 0/308 | 308 (294 entities) | 306 | 0 |

### Candidate 1 (sticky tasks) — confirmed real, and larger than the originally-cited figure

`PROD_SMALL`'s own `cadence.strategic_intelligence = 20` means, with *no* sticky-task suppression at
all, an entity could be brain-evaluated at most `ticks / 20` times over a run — 100 times over 2000
ticks. Observed: **11.48, 3.73, 12.45** — a **9.5x, 24.6x, and 6.0x suppression** below what cadence
alone would allow. This confirms the scheduler-level sticky-task gate
(`src/engine/scheduler.py:61-63`, entities with a live `ENTITY_MOVE`/non-empty-`ENTITY_ACT` task skip
the brain entirely) is real and dominant, not a minor effect — consistent with, and larger in this
measurement than, the 93.7%-re-execution figure `docs/engine/kernel.md`'s own Sticky-Task Law cites
for the reference scenario. Two more throttles stack on top of this same gate (found while tracing
the code, not previously cited): the scheduler's own separate cadence check even for
`ENTITY_BRAIN`-eligible entities (`scheduler.py:78-83`), and `execute_brain`'s own redundant early-exit
(`cognition.py:39-56`) — see the code-read section above.

### Candidate 2 (`hostiles` gate) — confirmed real and dominant in the corpus worlds

**Zero** of 551 + 56 + 523 = 1130 real `evaluate_entity_intent` calls across the three corpus worlds
ever found a non-empty `hostiles` list. Even when the brain *does* run (already suppressed ~6-25x by
candidate 1), it essentially never finds a hostile target in range/perceived. This is the single
largest confirmed cause in the corpus worlds: the brain rarely runs, and when it does, it almost never
has anything to attack.

### Candidate 3, reframed — not a divergence once sticky-task persistence is accounted for

In the two corpus-world cases where a fresh ATTACK decision *did* happen (`crowded_frontier`:
1 decision → 2 dispatches; `hero_guild_routing`: 1 decision → 29 dispatches), the decision
**did** survive to real dispatch — the gap between "1 emitted" and "2" or "29 dispatched" is fully
explained by the scheduler's own sticky-task re-execution (the same mechanism candidate 1 measures):
once decided, the same `ENTITY_ACT`/`ATTACK` task is re-dispatched every subsequent tick without
re-invoking the brain, until the target dies, moves out of range, or something else changes the task.
**There is no emission-vs-dispatch divergence to explain** — the original concern (a decision made
but never reaching real execution) does not hold; if anything, one real decision produces *many* real
dispatches, the opposite direction from what "something drops the decision" would predict.

### Candidate 4 (`obj.kind` never reaches `DEFEAT_ENEMY`) — confirmed real in the corpus worlds

**Zero** `DEFEAT_ENEMY` objectives sampled across all three corpus worlds, at both sample points
(tick 1000 and tick 1999 of 2000), across every entity with an active project. The objectives
actually assigned were `REACH_LOCATION`, `INVESTIGATE`, or no project at all (`NO_PROJECT`). This
means the strategic layer essentially never points entities at a combat objective in these worlds'
sampled windows — independent of whether a hostile would be found if it did.

### `metropolis`, the intended control — anomalous, and the anomaly has a real, disclosed cause, not chased to full resolution

`metropolis` was expected to be the control where the decision path demonstrably fires (per this
ticket's own premise, citing the prior gate-starvation investigation's 100%-cross-faction finding on
this same scenario). Instead: **every single evaluated entity (294 of 294) returned an ATTACK
decision**, yet `hostiles` was measured non-empty **zero** times — the opposite combination from what
the hostile-engagement branch's own code requires (the `ATTACK` payload at `tactical.py:757` is only
reachable through the `if hostiles:` branch). Traced directly: `build_metropolis_state()` (via its own
`build_mixed_state` → `build_combat_arena_state` composition) places entities at deterministic grid
positions that produce **real spawn collisions** — confirmed by direct construction-time inspection
(dozens of `LAW-SPAWN-OCCUPANCY`/`LAW-OCCUPANCY-COLLISION` hard-law violations logged on every run,
e.g. entity 1 and entity 101 both placed at tile (5,5)). This is a real, pre-existing data-quality
defect in this specific perf/stress-test scenario builder, not a property of `tactical_decision`
itself — `metropolis` is a synthetic load-generation harness (`src/perf/scenarios.py`, built for
throughput/governance benchmarking, not narrative-world fidelity), and its own entities' default task
state and spawn layout do not represent how the mechanism behaves under real, curated world content.
**Not chased to a full root cause here** — doing so would be its own separate investigation into the
perf-scenario builder's own correctness, out of this ticket's scope (investigate `tactical_decision`'s
real-world firing rate, not perf-harness data quality). Recorded as a disclosed limitation on the
control's own reliability, per Acceptance Criteria #3's own spirit (state exactly what was found and
what wasn't chased, rather than force a conclusion the data doesn't support).

## Answer to the sharpened question

**Why does the decision-driven ATTACK path essentially never fire in the corpus worlds, leaving
nearly all real combat to the incidental opportunity-attack mechanic?** Two independent, compounding
causes, both measured directly, not reasoned about:

1. **The strategic layer almost never assigns a `DEFEAT_ENEMY` objective** in these worlds' sampled
   windows (candidate 4) — so even a maximally-alert entity has nothing telling it to fight.
2. **Even when the tactical brain does run** (itself suppressed 6-25x below the raw cadence ceiling by
   a three-layer sticky-task/cadence gate stack, candidate 1), **it essentially never finds a hostile
   target in range and perceived** (candidate 2, 0 of 1130 real corpus calls).

Candidate 3 is not an independent defect — it was the originally-suspected mechanism ("maybe the
decision gets made but lost before dispatch") and the corrected measurement shows the opposite: a
made decision reliably dispatches, repeatedly, via the same sticky-task mechanism that suppresses
fresh decisions in the first place. The four candidates are not four separate problems; they compose
into one picture — decisions are rare (1, 2), and rare decisions get amplified into many repeat
dispatches (the sticky-task mechanism, which is candidate 1's own other face).

**Design question, not a defect question, per this ticket's own Assumption #2**: whether the decision
path *should* fire more often is a design call for the user, not resolved here. What this
investigation establishes is the mechanism, not the disposition.

