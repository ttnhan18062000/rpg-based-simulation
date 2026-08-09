---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE

## Context
Direct follow-up to `TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE` (DONE, same session), whose
own fix made real hostile pairs genuinely reachable for the first time. This ticket investigates
why, even after that fix, every observed real attack-legality check still fails on
`ReasonCode.OUT_OF_RANGE`.

## Methodology
Same live-instrumented, real 2000-tick `Kernel.tick_once()` corpus methodology as the parent
ticket. Probe scripts lived in the scratchpad.

## Finding 1: chase-relevant tactical decisions are genuinely rare, not just non-convergent
Instrumented every real `INTERCEPTING`/`KITING`/`PURSUIT_BLOCKED_KITE`/bare-`PURSUE` decision
branch across a full 2000-tick run: **11 total** in `dungeon_crawl`, **2 total** in
`urban_political`. This is consistent with (not contradicting) the parent ticket's own legality-
check counts (26+3+2). Distances sampled at these decision points range 2-12 with no clear
monotonic trend visible across the sparse sample (one traced entity pair: distance 3 at tick 368,
distance 12 at tick 879 — the gap **widened**, not narrowed, over ~500 ticks).

## Finding 2: `evaluate_entity_intent` itself is cadence-gated for idle, project-less entities
`src/engine/domain/cognition.py::CognitionDomain.execute_brain()` — the real, sole caller of
`TacticalDecisionSystem.evaluate_entity_intent()` — has two real early-exits:
```python
is_idle = entity.task.work_kind == "IDLE"
has_project = bool(entity.strategic.current_project_id)
is_cadence_tick = should_run(state.tick, entity.id, cad_val)  # cad_val = 10 (SystemCadence.strategic_intelligence)

if not has_project and is_idle and not is_cadence_tick and not force:
     return {entity.id: EntityUpdate(entity_id=entity.id)}   # tactical eval skipped entirely
...
if not neighbors and not has_project and is_idle and not force and not is_cadence_tick:
     return {entity.id: EntityUpdate(entity_id=entity.id)}   # tactical eval skipped entirely
```
`SystemCadence.strategic_intelligence` defaults to `10` — an idle entity with no active strategic
project only gets a chance to notice a nearby hostile once every ~10 ticks (staggered by
`entity_id`, not globally synchronized). This is a real, deliberate performance optimization
(avoiding an "all entities re-evaluate every tick" spike), not a bug in itself — but it directly
explains why `evaluate_entity_intent` call volume for `bandit_company`/etc. (400-1000 calls per
2000 ticks, not 2000×N) is far below "every tick." Once an entity actually starts pursuing
(`task.work_kind_set="ENTITY_MOVE"`, no longer `"IDLE"`), this specific gate should stop applying
on subsequent ticks — `is_idle` becomes `False`.

## Finding 3 (real, but not yet conclusively linked): `find_intercept_position`'s prediction can
diverge if the target's own movement direction changes between the pursuer's re-evaluations
`src/engine/positioning.py::PositioningService.find_intercept_position()` (reached via
`tactical.py`'s "5.4 Intercept Logic", `dist_to_target > 3 and target.navigation.target`) predicts
a point 2 tiles ahead of the target along the target's *current* movement vector toward *its own*
navigation goal — not the target's actual current position. If the target (a wandering, non-
combat-aware entity) changes its own destination between the pursuer's re-evaluations, the
predicted intercept point changes too, and — combined with Finding 2's staggered re-evaluation
cadence — the pursuer could be steering toward a stale, already-wrong prediction for several ticks
before its next chance to re-aim. This is a plausible, real contributing mechanism, consistent
with the one traced widening-distance sample, but **not independently confirmed** with direct
before/after instrumentation of the intercept-point's own tick-to-tick stability — a real
limitation of this investigation, disclosed honestly per the Uncertainty Rule rather than assumed.

## What this rules out
- Not readiness (`readiness=100.0` in every sampled legality check, confirmed by the parent
  ticket).
- Not the identity-resolution bug (already fixed; this ticket's own findings are downstream of
  that fix).
- Not a crash or dead code path — `evaluate_entity_intent`/`find_intercept_position` both execute
  normally and return real, well-formed updates.

## Recommendation
This ticket's own real chase-volume (11/2 total decisions across 4000 combined ticks) is too
sparse to draw a fully conclusive mechanism from black-box corpus probing alone. Two real,
plausible, non-exclusive contributing factors are identified (cadence-gated initial detection;
intercept-prediction instability against a non-combat-aware wandering target) but neither is
proven as *the* sole cause with the same confidence level as the parent ticket's identity-
resolution bug. Recommend: **do not force a speculative fix here.** The most productive next
step is a dedicated, narrower instrumentation pass — tracking a single real pursuing entity's
`navigation.target`/`movement_mode`/distance-to-real-target tuple on *every* tick (not just
tactical-decision ticks) across a real chase, to distinguish cadence-gap-starvation from
intercept-prediction divergence with direct evidence. Leaving this open as a real, disclosed,
partially-investigated finding rather than closing with an unproven claim.

## Docs Requiring Update
None — no fix landed in this ticket; the parent ticket's own `D21_entity_lifecycle_foundation_
layers.md` update already references this ticket by ID for the newly-surfaced bottleneck.
