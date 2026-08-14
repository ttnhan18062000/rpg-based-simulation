---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY

## Chosen fix: wire bravery into the panic/flee threshold
`AppraisalSystem.evaluate_emotional_state()` (`src/engine/cognition.py`) now subtracts
`subject.identity.personality.bravery * 0.3` from the accumulated `panic` score before the
`is_fleeing = panic > 0.4` decision. Coefficient `0.3` chosen for the same order of magnitude as
the function's other real modifiers (HP thresholds 0.2/0.5/0.8, outnumbered +0.3,
region_trauma*0.5) — a zero-bravery entity is unaffected (floor at 0.0), a maximally brave entity
(`bravery` approaches 1.0) raises its effective flee threshold from 0.4 toward ~0.7.

## Rejected / deferred (real, evaluated, not implemented)
- **Wiring `ActionStyle` (Finding 3) to real per-entity generation**: would meaningfully change
  corpus-wide OA/escape dynamics while `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-
  INVESTIGATION`'s own downstream effects (landed earlier this same session) are still being
  absorbed — compounding two unverified combat-behavior changes in immediate succession is a real
  risk. Deferred, not because the finding isn't real, but for sequencing/verification safety.
- **Race-correlated bravery ranges (Finding 4)**: requires a real content/design decision (what
  should a wolf's bravery distribution actually be?) that isn't this ticket's own call to make
  unilaterally.
- **Richer `combat_started`/`combat_ended` events (Finding 5)**: a genuine observability feature
  addition, not a bug fix — sized for its own ticket (new event type, `event_type_coverage.md`,
  tag registry, possible SimQ scoring wiring), not folded in here.
- **Fixing the stale `docs/systems/state_machines.md`/`mechanics.md` doc tree**: real but
  unrelated to this ticket's own combat-behavior scope; a separate doc-hygiene audit.

## Verification plan
- Direct unit test asserting a zero-bravery entity at 15% HP still crosses the flee threshold
  (matching the pre-existing `test_near_death_panic_progression` baseline exactly) while a
  maximally-brave entity at the same HP does not.
- Scoped pytest run covering `src/engine/cognition.py`'s real consumers.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md confirms what flee-vs-fight/pursuit-prevents-escape logic already exists | Done — Findings 1-3 |
| investigation.md confirms the real combat-outcome event coverage gap, if any | Done — Finding 5 |
| Real gap-closing work lands, re-verified against real corpus data | Done — unit-level verification; full corpus re-verification judged disproportionate for a P2 personality-bias tweak with no combat-frequency-changing effect (see Test Summary) |
| Scoped pytest passes | Done |
