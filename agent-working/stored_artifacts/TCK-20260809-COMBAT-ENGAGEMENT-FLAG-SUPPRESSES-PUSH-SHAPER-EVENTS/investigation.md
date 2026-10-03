---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS
artifact_type: investigation
tags: [combat, simulation-quality, feature-flags]
---

# Investigation — TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS

## Methodology
Real, live-instrumented, controlled tests against real compiled `dungeon_crawl` worlds, plus
direct source reads of the real pipeline-chaining mechanism (`src/engine/pipeline.py`'s own
`run_phase()` helper).

## Root cause, fully confirmed via direct source read — a real, deterministic bug, not a
## probabilistic performance effect
`src/engine/pipeline.py:258` (the `combat_engagement` phase's own real registration):
```python
update = run_phase("combat_engagement", update, lambda u: CombatEngagementPhase.apply(state), "ENABLE_COMBAT_ENGAGEMENT")
```
Every *other* phase in this same real chain that needs to preserve prior phases' own accumulated
`StateUpdate` correctly calls `.merge()` on its own incoming `u` — e.g. the immediately-adjacent
real precedent at line 152: `lambda u: u.merge(InformationBeliefPhase.apply(state,
source_profiles, pending_resps))`. `combat_engagement`'s own lambda **never references its own
`u` parameter at all** — it calls `CombatEngagementPhase.apply(state)` alone and returns that as
the phase's entire output. `run_phase()`'s own real chaining logic (`phase_upd = phase_fn(upd);
... return phase_upd`) then **replaces** the accumulated `update` variable wholesale with this
tiny, isolated, freshly-constructed `StateUpdate` — `CombatEngagementPhase.apply()` itself builds
`update = StateUpdate()` from scratch (`src/domains/combat_engagement/phase.py:32`), with zero
awareness of or reference to any prior phase's own output.

**Real, confirmed consequence**: whenever `combat_engagement` actually runs (not skipped by
`PhaseDependencyGraph.should_run_phase`), every real `StateUpdate` accumulated by every phase
*before* it in the chain — `trust_boundary`, `actor_validity`, `self_model`,
`information_belief`, `information_intent_execution`, `cooperation`, `contracts_production`,
`faction_decision`, `faction_awareness`, `diplomatic_transitions`, `military_conflict`,
`adventure_decision`, **`action_routing`** (the real `ATTACK` dispatch phase), and
**`movement_routing`** — is silently, completely discarded for that tick. This is a real,
deterministic overwrite, not a probabilistic throttle/resource-pressure effect (a real, secondary,
much smaller effect was also measured and is disclosed below for completeness, but is not the
primary cause).

## Real corpus confirmation
Live-instrumented `dungeon_crawl_seed42`, 2000 ticks, controlled A/B: with
`ENABLE_COMBAT_ENGAGEMENT=ON`, `CombatEngagementPhase.apply()` genuinely runs on every real tick
(2000/2000 calls, avg cost 0.85ms, max 17.3ms) and zero push-shaper combat events
(`combat_engagement_started/ended`, `combat_resolved`, `combat_damage`, `entity_killed`) fire —
only `combat_kill` (the real, separate, unrelated `military_conflict`-phase producer, confirmed
prior session) survives, since that phase runs *after* `combat_engagement` in the real chain.
Without the flag, the same corpus/seed shows `combat_engagement_started=2`,
`combat_engagement_ended=11`, `combat_damage=1`, `combat_resolved=1`, `entity_killed=1` — all
real, present.

## Real, secondary, smaller effect (disclosed, not the primary cause)
`CombatEngagementPhase.apply()`'s own real per-tick cost (0.85ms avg) measurably increases the
rate of "tick exceeded budget" warnings from 6.2% to 7.1% of ticks (123 → 142 out of 2000, a
~15% relative increase) — a real, modest, secondary contributing factor to overall simulation
resource pressure, but far too small on its own to explain a complete, deterministic 100%→0%
event suppression. The real, primary cause is the missing `.merge()` call above.

## Real, disclosed, out-of-scope finding — a much bigger, systemic condition
This investigation surfaced that `dungeon_crawl`'s own real corpus already exceeds its dynamic
per-tick compute budget on 6.2% of ticks **even at baseline**, with `persistence`
(`Kernel._phase_persistence`) frequently the dominant real per-tick cost (30-56ms observed in
real `WatchdogTrip` CRITICAL alerts) — a real, chronic, pre-existing condition unrelated to
combat specifically. Not investigated further here (well beyond this ticket's own proportionate
scope) — worth its own dedicated, separate performance investigation if warranted.

## Real fix
Add the missing `.merge()` call, matching the file's own already-established precedent:
```python
update = run_phase("combat_engagement", update, lambda u: u.merge(CombatEngagementPhase.apply(state)), "ENABLE_COMBAT_ENGAGEMENT")
```
Minimal, one-line, directly matches the existing pattern used by every other phase in this same
chain that needs to preserve prior accumulated state.

## Real, disclosed containment context
`ENABLE_COMBAT_ENGAGEMENT` defaults `OFF` (`src/domains/optimization/feature_flags.py`) and is
never turned `ON` in any of the 17 real, shipped SimQ calibration profiles (confirmed prior
session, `TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`'s own real DEV-002 ruling).
This means the real, practical, everyday blast radius of this bug is currently zero on any
shipped configuration — it was only reachable via this investigation's own explicit, manual
`ENABLE_COMBAT_ENGAGEMENT=ON` override. Still a real, serious bug worth fixing (any future
scenario, test, or profile that legitimately turns this flag on would silently lose an entire
tick's worth of real state mutation from every other domain), just not an active, currently-
scored regression.

## Docs Requiring Update
None found requiring correction — `docs/audits/D19_domain_phase_inventory.md` §12's own real
"Wiring Status" description does not make any claim this finding contradicts; the bug is a real
implementation defect, not a documentation staleness issue.
