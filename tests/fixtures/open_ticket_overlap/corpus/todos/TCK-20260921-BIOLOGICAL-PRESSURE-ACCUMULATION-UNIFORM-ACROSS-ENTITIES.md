---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES
phase: open
date: 2026-09-21
tags: [simulation-quality, progression]
---

# TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES

## Title
Design decision needed: hunger/sleep-debt accumulation is identical for every entity regardless
of attributes — is uniform biological pressure intended, or should vitality/endurance modulate it?

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Found while investigating `attributes_biology` as the priority candidate for the value-
differential instrument's horizon rule
(`TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT`, waves 4). The mechanism was
declined for that program (no per-entity varying input means there is nothing to differential-test
— the instrument does not apply to it as implemented, a correct and separate disposition, not
revisited here). But the underlying fact is worth its own design question, reframed here per peer
review before it could sit as a buried negative result.

`ApplyPath._compute_entity_changes` (`src/engine/apply.py:88-91`) accumulates biological pressure
identically for every entity in the simulation:
```
hunger=min(100.0, bio.hunger + 0.1 * cadence.biological)
sleep_debt=min(100.0, bio.sleep_debt + 0.05 * cadence.biological)
```
The only quantities read are `cadence.biological` (a world/profile-level config shared by every
entity) and the entity's own current `hunger`/`sleep_debt` value (for the `min(100, ...)` cap
only). No attribute, trait, species, or role reads anywhere in this code path. **A frail entity
and a hardy one get hungry and sleep-deprived at exactly the same rate.** Nothing an entity is or
becomes — its `vitality`, its `endurance`, its species, its life stage — changes how fast
biological pressure accumulates on it.

This is not a bug: the code correctly implements what it says. It is a design observation. For a
simulation whose entities carry explicit `vitality`/`endurance` attributes
(`docs/mechanics/01_entity_anatomy.md`), a reasonable expectation is that those attributes would
modulate biological pressure the way they modulate combat stats
(`readiness_speed_scaling`/`derived_stats`, both real, attribute-driven formulas) — and they
don't, here.

**Worth reading alongside `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS`** (the P0
world-integrity finding from the same program): that ticket found species/content-driven combat-
stat differentiation erodes toward generic defaults after spawn; this one finds biological-pressure
accumulation was never differentiated by entity identity in the first place. Different code paths,
same underlying question for the roadmap session: **how much does entity identity (attributes,
species, role) actually influence this simulation's moment-to-moment behavior**, versus how much
converges to a shared baseline regardless of what an entity is? Presented together rather than as
two unrelated tickets, per peer instruction, though each stands on its own evidence.

## Scope
For the roadmap/planning session to decide, not to implement here:
1. Is uniform biological-pressure accumulation intentional (a deliberate simplification — hunger
   and fatigue are treated as universal biological constants, not attribute-scaled) or a real gap
   (vitality/endurance should modulate hunger/sleep-debt rate, matching how they modulate combat
   stats elsewhere)?
2. If it's a gap: what's the right modulation shape — a linear scaling factor on the existing rate
   (e.g. `0.1 * cadence.biological * (some function of endurance)`), a flat per-entity multiplier
   set at spawn, or something else? Should it be symmetric for hunger and sleep_debt, or does each
   have its own natural attribute driver (e.g. endurance for hunger, vitality for sleep_debt, or
   vice versa)?
3. How this interacts with the other real code path already flagged on `attributes_biology`'s own
   registry entry (`_compute_entity_changes`'s second, not-yet-investigated age-related check) —
   not this ticket's concern to resolve, but worth the same reviewer noticing both live in the same
   method.

## Out of Scope
- Any code change — this ticket exists to get a decision, not to make one unilaterally, matching
  `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`'s and
  `TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES`'s own framing for
  comparable design-question tickets.
- Re-investigating the value-differential program's own disposition of `attributes_biology`
  (declined, instrument does not apply) — that finding stands; this ticket exists because of what
  that investigation surfaced, not to revisit it.
- `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS` itself — referenced for context
  only, not modified or re-scoped here.

## Acceptance Criteria
1. A real design decision from the roadmap session on whether uniform biological-pressure
   accumulation is intended or a gap.
2. Once decided: either a real implementation ticket scoped to the attribute-modulation fix (if a
   gap), or an explicit registry-note/doc update recording the design choice (if intended), never a
   silent code change made to match a guess at what the decision would have been.

## Related Tickets
- `TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT` — where this was found (wave
  4, `attributes_biology` investigated as the horizon-rule candidate)
- `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS` — the companion finding from the
  same program; read together per peer instruction, not merged
- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`,
  `TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES` — the comparable
  "design decision, not a bug report" framing this ticket follows

## Related Docs
- `docs/mechanics/01_entity_anatomy.md` (attribute definitions, including vitality/endurance)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/apply.py::ApplyPath::_compute_entity_changes` (lines 88-91, the accumulation itself)
- `src/core/state.py` (`BiologicalComponent`, `AttributeComponent`)

## Assumptions / Open Questions
Whether uniform accumulation was a deliberate simplification or an oversight is genuinely unknown
— not assumed either way. That's Scope item 1's own first task.

## Implementation Notes
(none yet — not started; awaiting the design decision this ticket exists to request)

## Test Summary
(none yet)

## Files Changed
(none yet)

## Completion Summary
(none yet)
