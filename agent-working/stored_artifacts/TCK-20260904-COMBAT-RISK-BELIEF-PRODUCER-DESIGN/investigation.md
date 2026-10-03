---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN
artifact_type: investigation
date: 2026-09-08
tags: [content]
---

# Investigation — TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN

A prior investigation-only fork produced the design-options analysis recorded in the ticket's own
`## Implementation Notes` (2026-09-08). That work is **not repeated here** — it was independently
verified by the orchestrating session. This document records only what the *implementation* pass
re-confirmed and newly found.

## Re-confirmation of the prior findings (2026-09-08, implementation pass)

- `grep -rn "combat_risk" src/ tests/` — still exactly 6 hits: 1 consumer read
  (`src/domains/cooperation/evaluators.py:47`) + 5 test constructions. Zero production producers.
  Unchanged.
- `BeliefEntry` (`src/systems/strategic_systems/belief.py:23`) real schema confirmed:
  `id, subject, claim, certainty=0.5, source="observation", source_entity_id=None,
  created_tick=0, last_refreshed_tick=0, contradictions=0`. Frozen dataclass, slots.
- Write path confirmed: `StrategicUpdate.beliefs_add_or_update` → `merge_dict()`
  (`src/engine/patches.py:442-450`) → `res[item.id] = item`. **The dict key is `item.id`.**
- Production-caller precedent confirmed: `BeliefCycleSystem.process_rumor()` /
  `.process_observation()` (`belief.py:101,134`) are the only two real `BeliefEntry(...)`
  constructions in `src/`.
- `RiskLevel` (`src/core/strategic.py:209`) is a **`str` Enum** with values exactly
  `"LOW"/"NORMAL"/"HIGH"/"EXTREME"` — so a `RiskLevel` round-trips losslessly through
  `BeliefEntry.claim: str`.

## New finding #1 — the `.id` must literally be `"combat_risk"`

Because `merge_dict` keys by `item.id`, and the consumer reads
`entity.strategic.beliefs.get("combat_risk")`, the producer's `BeliefEntry.id` must be the literal
string `"combat_risk"`. This is a **stable-key** belief (each tick's write replaces the previous
one in place), unlike the rumor/observation precedent which uses tick-suffixed ids to accumulate
history. Stable-key is correct here: `combat_risk` is a *current* assessment, not an append-only
log, and a tick-suffixed id would grow the beliefs dict without bound every tick an actor is near
a hostile.

## New finding #2 — `CombatEngagementPhase.apply()` evaluates exactly ONE target, not three

`src/domains/combat_engagement/phase.py:68` computes `targets_to_evaluate = targets[:3]`, but the
loop body ends with `break  # evaluate first target only` (line 94). So despite the `[:3]` slice,
**only the first target is ever evaluated** per actor per tick.

This corrects the prior investigation's phrasing ("max `death_risk` across all targets evaluated").
The real available signal is the `death_risk` of the single evaluation that already happens.
Deliberately **not** changed: evaluating all 3 would triple `CombatEngagementDecisionService.evaluate()`
cost in a phase whose own comments call out staying "strictly within strategic budget", and
changing engagement-evaluation breadth is out of this ticket's scope (its Out of Scope forbids
touching adjacent mechanisms). Using the single existing evaluation costs **zero** extra work.

## New finding #3 — real threshold precedent exists in the same evaluator (no invented numbers)

The directive required an evidenced starting point rather than invented cutoffs. Two real anchors
exist inside `EngagementRiskEvaluator.evaluate()` itself (`risk_evaluator.py:55-110`):

1. **`death_risk > 0.8` is already this codebase's own "critical" boundary** — line ~108:
   `if death_risk > 0.8 and emotional_bias < 0.3: acceptable = False;
   reasons.append("hp_critical_safety_lock")`. A real, shipped severe-safety-lock cutoff.
2. **`near_death` forces `death_risk = max(0.9, ...)`** (line ~67) — i.e. the near-death case is
   deliberately placed *above* that 0.8 lock.

The formula itself supplies the remaining anchors:
`death_risk = clamp((1.0 / power_ratio) * 0.4, 0.0, 1.0)` where
`power_ratio = self_power / opponent_power`. Therefore:

| `power_ratio` | meaning | `death_risk` |
|---|---|---|
| 2.0 | actor twice as strong | **0.20** |
| 1.0 | evenly matched | **0.40** |
| 0.5 | opponent twice as strong | 0.80 |

This yields a mapping derived entirely from existing constants, not invented:

| `death_risk` | `RiskLevel` | derivation |
|---|---|---|
| `<= 0.20` | `LOW` | actor at least 2x stronger |
| `<= 0.40` | `NORMAL` | up to and including evenly matched |
| `<= 0.80` | `HIGH` | opponent stronger, but below the codebase's own critical lock |
| `> 0.80` | `EXTREME` | matches the existing `hp_critical_safety_lock` cutoff; `near_death`'s 0.9 floor lands here |

## New finding #4 — `PostureIntentResolver.resolve()` may return `strat_upd = None`

`resolve()` returns `Tuple[Optional[ActionIntent], Optional[StrategicUpdate]]` — `strat` stays
`None` for postures that don't produce one. The producer must handle both branches (construct a
fresh `StrategicUpdate` when `None`, else `dataclasses.replace(...)` appending to the existing
`beliefs_add_or_update` list) rather than assuming a `StrategicUpdate` always exists.

## Consumer contract change required by the ratified decision

`HelpNeedEvaluator.evaluate()` line 47-50 currently does:

```python
combat_belief = entity.strategic.beliefs.get("combat_risk")
risk_level = RiskLevel.NORMAL
if combat_belief:
    risk_level = combat_belief.get("level", RiskLevel.NORMAL)
```

`BeliefEntry` is a frozen slots dataclass with **no `.get()`** — so this must become a real
attribute read of `.claim`, parsed back into `RiskLevel`, with a defensive fallback to
`RiskLevel.NORMAL` for any unparseable/absent claim (the `beliefs` dict is generically typed, so a
malformed entry must degrade rather than raise).
