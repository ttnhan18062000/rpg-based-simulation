---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN
phase: open
date: 2026-09-04
tags: [content]
---

# TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN

## Title
Design and wire a real producer for entity.strategic.beliefs["combat_risk"] -- a tested consumer with
no production writer

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ` investigated `src/domains/cooperation/evaluators.py:47`'s
`entity.strategic.beliefs.get("combat_risk")` read and found it is **not dead code** — it's a real,
deliberately designed, tested consumer with no production producer. Confirmed via direct grep: 5 test
files (`tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py`,
`tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`,
`tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py` (x2),
`tests/perf/test_phase7_social_cooperation_budget.py`) manually construct
`entity.strategic.beliefs["combat_risk"] = {"level": RiskLevel.HIGH}` to exercise
`HelpNeedEvaluator.evaluate()`'s HIGH/EXTREME-risk branch — proving the consumer contract is real and
intentional, not leftover cruft. No code anywhere in `src/` writes this key in a live gameplay path;
only tests construct it artificially.

Checked the two most obvious candidate existing signals as a possible reused producer — neither fits
directly:
- `src/systems/strategic_systems/belief.py::estimate_threat()` — also has zero real callers anywhere,
  and models **regional** danger (concerns/leads about a region), not an entity's own personal
  in-combat risk. A different concept, not a drop-in producer.
- No other existing "combat danger assessment" computation was found.

## Scope
- Design what should actually determine an entity's `combat_risk` level (`LOW`/`NORMAL`/`HIGH`/
  `EXTREME`) — candidate signals include recent HP loss/trend, nearby hostile entity count/strength,
  active combat engagement duration, or some combination. This needs real design-authority input, not
  an invented formula — deliberately not decided in this ticket.
- Once designed, implement the producer and wire it into whichever phase should compute it (likely
  strategic cognition or combat-adjacent, given `HelpNeedEvaluator` already runs in Phase 7
  cooperation).
- Confirm the 5 existing tests' manually-constructed `combat_risk` dict shape (`{"level": RiskLevel}`)
  matches whatever the real producer emits — do not silently change the consumer contract without
  updating those tests in the same ticket.

## Out of Scope
- `src/systems/strategic_systems/belief.py::estimate_threat()`'s own separate zero-caller status — a
  distinct finding (regional threat, not personal combat risk), not part of this ticket unless design
  review decides to actually reuse/extend it.
- Any other `StrategicComponent.beliefs` key or the `BeliefEntry`/`KnowledgeFact` reconciliation
  question — already decided separately (`TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION`).

## Acceptance Criteria
- [ ] Real combat-risk-assessment design confirmed with design-authority input, not invented
      unilaterally.
- [ ] A real producer writes `entity.strategic.beliefs["combat_risk"]` in a live gameplay path.
- [ ] All 5 existing tests that manually construct this belief still pass (or are updated in step with
      a confirmed, deliberate contract change).
- [ ] `HelpNeedEvaluator.evaluate()`'s combat-support-need logic is verified to actually fire in a real
      simulation run at least once, not just in hand-constructed unit tests.

## Related Tickets
- TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ (the investigation that found this gap)

## Related Docs
None yet.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/domains/cooperation/evaluators.py` (`HelpNeedEvaluator.evaluate()`)
- `src/core/strategic.py` (`RiskLevel`)
- `src/systems/strategic_systems/belief.py` (`estimate_threat()`, checked but not a direct fit)

## Assumptions / Open Questions
- What real signal(s) should determine `combat_risk` level is the central open design question this
  ticket must resolve before implementation — deliberately not decided here.

## Implementation Notes

### Investigation, 2026-09-08 (orchestrator-directed fork — design options only, no code written, no decision made here)

**Findings re-confirmed, still accurate.** `grep -rn "combat_risk" src/ tests/` finds exactly the
same 6 hits the ticket already cites: one consumer read
(`src/domains/cooperation/evaluators.py:47`, `combat_belief.get("level", RiskLevel.NORMAL)`) and 5
tests manually constructing `entity.strategic.beliefs["combat_risk"] = {"level": RiskLevel.HIGH}`.
Zero real producers anywhere. `estimate_threat()` (`src/systems/strategic_systems/belief.py`) is
still a poor fit — regional, not personal, still zero real callers of that specific function.

**New finding #1 — `HelpNeedEvaluator.evaluate()` already reads `entity.combat.hp`/`.max_hp`
directly in a separate branch** (`# 2. Low HP creates healer/protection need`). This means
`combat_risk` is meant to capture something *beyond* current HP — most plausibly ambient/impending
threat exposure (how dangerous is my current surroundings), not a restatement of health state
already checked elsewhere in the same function.

**New finding #2 — a real, already-computed, already-live signal exists that fits exactly:**
`CombatEngagementPhase.apply()` (`src/domains/combat_engagement/phase.py`, Phase 4, runs every
tick) already queries nearby hostiles via a real spatial grid
(`grid.query_radius(actor.navigation.position, 10.0)`, capped at 3 targets) and, for each one,
calls `CombatEngagementDecisionService.evaluate()` → `EngagementRiskEvaluator.evaluate()`, which
computes a real `EngagementRiskEvaluation.death_risk` float in `[0.0, 1.0]`
(`src/domains/combat_engagement/risk_evaluator.py:63-67`) per (actor, target) pair — including a
`>= 0.9` override when the actor has a `near_death` condition. This is genuinely the same concept
`combat_risk` is meant to represent (personal danger from nearby hostiles), already computed with
zero new spatial query or new state needed — just not currently written anywhere.

**New finding #3 — a real write-path complication, not previously flagged in the ticket.** The
generic typed belief-write mechanism (`StrategicUpdate.beliefs_add_or_update`, merged via
`merge_dict()` in `src/engine/patches.py:442-450`) requires each item to be an object with a real
`.id` attribute used as the dict key. Every real production caller
(`src/systems/strategic_systems/belief.py`, `src/systems/strategic_systems/intelligence.py`,
`src/systems/social_systems/guilds.py`) puts a `BeliefEntry` (`id, subject, claim, certainty,
source, ...` — no `level` field, no `.get()` method) through this path. The 5 existing tests'
`{"level": RiskLevel.HIGH}` plain-dict shape is **not** `BeliefEntry`-compatible — `combat_risk`'s
real consumer contract is a separate, bespoke mini-schema that doesn't fit the generic typed
belief-update path at all. Any real producer needs its own dedicated write path, not
`beliefs_add_or_update`.

**Two real candidate approaches, not decided here:**

1. **Minimal (matches existing test contract, recommended as the lower-risk default)**: add a new
   dedicated `StrategicUpdate` field (e.g. `combat_risk_set: Optional[Dict[str, Any]]`, applied as a
   direct assignment in `patches.py` — the same shape as other single-value `_set` fields already on
   `StrategicUpdate`, not routed through `beliefs_add_or_update`/`merge_dict`). Write it from
   `CombatEngagementPhase.apply()`: take the max `death_risk` across all targets evaluated for an
   actor this tick, map it to `RiskLevel` via real thresholds (e.g. `<0.2` LOW, `0.2-0.5` NORMAL,
   `0.5-0.8` HIGH, `>0.8` EXTREME — exact cutoffs need real tuning, not invented here), write
   `{"level": mapped_level}`. Preserves the 5 existing tests and the consumer's `.get("level", ...)`
   call completely unchanged — zero contract change.
2. **Architecturally cleaner, bigger, real contract change**: migrate `combat_risk` onto the real
   `BeliefEntry` system (e.g. `claim` carries the risk level as a string). Fixes the
   generic-belief-schema inconsistency this investigation surfaced, but requires changing
   `HelpNeedEvaluator.evaluate()`'s own read (`.get("level", ...)` → a `BeliefEntry` lookup +
   `claim`/`certainty` interpretation) and updating all 5 existing tests' construction pattern in the
   same ticket, per this ticket's own Scope. Bigger, more invasive, needs explicit sign-off since it
   deliberately changes an existing tested contract rather than just filling a producer gap.

**Recommendation, not a decision**: Option 1, wired into `CombatEngagementPhase.apply()` using
`death_risk`. It reuses a real, already-computed, already-live-every-tick signal with zero new
spatial query or state, requires no test changes, and directly represents "personal danger from
nearby hostiles" — the gap `HelpNeedEvaluator`'s separate HP-based branch doesn't already cover.
Real threshold tuning (the 4 cutoff values) still needs a real decision or at minimum a documented,
evidenced starting point — not invented unilaterally by whoever implements this.

**Decision NOT made here per this fork's directive** — brought back to the orchestrator/user.

### Decision, 2026-09-08 (real user decision, via `AskUserQuestion`, orchestrator-initiated)
**Option 2 — migrate `combat_risk` onto the real `BeliefEntry` system properly**, not the minimal
dedicated-field approach. This is the bigger, more invasive change: `HelpNeedEvaluator.evaluate()`'s
own read (`.get("level", ...)`) must change to a `BeliefEntry` lookup + `claim`/`certainty`
interpretation, and all 5 existing tests' construction pattern must be updated in the same ticket,
per the ticket's own Scope. The real `death_risk` signal from `CombatEngagementPhase.apply()` →
`EngagementRiskEvaluator.evaluate()` (already confirmed live-every-tick) is still the right source
signal to write from — this decision only changes *how* it's written (through the generic
`BeliefEntry`/`beliefs_add_or_update` path, not a new bespoke `StrategicUpdate` field), not *what*
computes it. Threshold tuning (mapping `death_risk` float to a `RiskLevel`/claim value) still needs
a real, evidenced starting point during implementation, not invented arbitrarily.

## Test Summary

## Files Changed

## Completion Summary
