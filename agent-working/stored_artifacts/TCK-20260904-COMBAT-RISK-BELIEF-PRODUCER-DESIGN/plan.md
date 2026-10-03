---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN
artifact_type: plan
date: 2026-09-08
tags: [content]
---

# Plan — TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN

Implements the **ratified Option 2** (migrate `combat_risk` onto the real `BeliefEntry` system).

## Step 1 — Producer: `src/domains/combat_engagement/phase.py`

Add a module-level, clearly-labelled threshold mapping derived from the existing evaluator's own
constants (see investigation.md finding #3), then write the belief from the single existing
`CombatEngagementDecisionService.evaluate()` result:

- `_COMBAT_RISK_BELIEF_ID = "combat_risk"` — must equal the consumer's lookup key, since
  `merge_dict` keys by `item.id`.
- `_death_risk_to_level(death_risk) -> RiskLevel` using the 0.20 / 0.40 / 0.80 cutoffs.
- Build `BeliefEntry(id="combat_risk", subject="combat_risk", claim=<level>.value,
  certainty=<death_risk>, source="observation", created_tick=state.tick,
  last_refreshed_tick=state.tick)`.
  - `certainty` carries the raw float that produced the level — real information, not padding.
  - `source="observation"` matches the precedent's vocabulary for directly-perceived facts.
- Attach to the `StrategicUpdate`: fresh one if `PostureIntentResolver.resolve()` returned `None`,
  else `dataclasses.replace()` appending to the existing `beliefs_add_or_update`.

Scope guard: do **not** change target-evaluation breadth (the existing `break`), posture logic, or
the risk formula.

## Step 2 — Consumer: `src/domains/cooperation/evaluators.py`

Replace the `.get("level", ...)` dict read with a real `BeliefEntry` attribute read:

```python
combat_belief = entity.strategic.beliefs.get("combat_risk")
risk_level = RiskLevel.NORMAL
if combat_belief is not None:
    claim = getattr(combat_belief, "claim", None)
    if claim is not None:
        try:
            risk_level = RiskLevel(claim)
        except ValueError:
            risk_level = RiskLevel.NORMAL
```

Defensive `try/except` because `beliefs` is generically typed — a malformed/foreign entry under
this key must degrade to `NORMAL`, never raise inside Phase 7.

## Step 3 — Update the 5 existing tests

Replace each `{"level": RiskLevel.HIGH}` construction with a real
`BeliefEntry(id="combat_risk", subject="combat_risk", claim=RiskLevel.HIGH.value, certainty=...)`.
Test *intent* is unchanged in every case (still "this entity perceives HIGH combat risk"); only the
construction shape changes, per the ticket's own Scope.

- `tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py:27`
- `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py:65`
- `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py:36,82`
- `tests/perf/test_phase7_social_cooperation_budget.py:34`

## Step 4 — New tests

1. `_death_risk_to_level` boundary coverage at each cutoff (0.20/0.40/0.80 and just above/below),
   including the `near_death` 0.9 case landing in `EXTREME`.
2. Producer emits a real `BeliefEntry` under key `"combat_risk"` through a real
   `CombatEngagementPhase.apply()` call (not a hand-built update).
3. Consumer parses a real `BeliefEntry` claim back to `RiskLevel` and still raises
   `combat_support_needed`; plus the defensive fallback case (garbage claim → `NORMAL`, no raise).
4. **End-to-end (ticket AC #4)**: a real multi-tick engine run where the producer writes the belief
   and `HelpNeedEvaluator.evaluate()` subsequently returns `combat_support_needed` — proving the
   full path fires outside hand-constructed unit fixtures.

## Step 5 — Verify

Scoped pytest over cooperation + combat_engagement + strategic suites, then the AC-#4 real-run
proof. Update parity ledger if a real behavior contract changed (checked in Parity phase).

## Acceptance-criteria map

| AC | Covered by |
|---|---|
| Design confirmed with design-authority input | Ratified by real user via `AskUserQuestion`, recorded in ticket Implementation Notes |
| Real producer writes the belief in a live path | Step 1 + Step 4.2 |
| 5 existing tests pass / updated in step | Step 3 |
| `HelpNeedEvaluator` fires in a real run | Step 4.4 |
