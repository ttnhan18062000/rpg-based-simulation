---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260927-NATURAL-AGING-OLD-AGE-DISPATCH-RACE
phase: open
date: 2026-09-27
tags: [engine, lifecycle, bug]
---

# TCK-20260927-NATURAL-AGING-OLD-AGE-DISPATCH-RACE

## Title
An entity that dies of natural aging is deactivated with no recorded cause and no succession

## Status
OPEN — brief only, not started. First-wave milestone M1
(`docs/plans/systemic_world/first_wave_plan.md`). Starts only after the owner reviews the
first-wave scope. The implementation agent owns the technical resolution and regression design.

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
**Semantic contract.** A persistent fact has one canonical authority. A world effect must not commit
from a stale assumption without a declared resolution rule (roadmap §3.1). For death specifically:
when an entity dies of old age, the world records that it died, when, and why (OLD_AGE), and the
lineage consequences of that death follow. Those consequences are heir selection, inheritance,
feud inheritance, and dying wish (Mechanics Bible `05_world_evolution.md`; roadmap §3.2 lineage).

**Observed problem.** An entity that reaches its maximum age through ordinary per-tick aging ends
up inactive, with no death reason, no death tick, and no succession. It then stays in that state
permanently. Two code paths both decide old-age deactivation, and the path that does not record a
cause acts one tick before the path that does. The second path then skips the already-inactive
entity. Relevant locations, cited as evidence and not as a prescribed change:
- `src/engine/apply.py:106-109`;
- `src/systems/lifecycle_systems/lifecycle.py:147` and `:193-194`.

The existing aging and succession tests do not catch this. They stage an age already past the
maximum in the starting snapshot, so the recording path runs first.

**Evidence level: scenario runtime, verified 2026-09-27.** Seed 42, `PROD_SMALL`, two entities:
- subject: `age_ticks=0`, `max_age_ticks=3`, designated heir, carrying `iron_sword`;
- heir: alive, empty inventory.

Six real kernel ticks, no mid-run staging:

```
tick=1 age=1 active=True  death_reason=None heir=[]
tick=2 age=2 active=True  death_reason=None heir=[]
tick=3 age=3 active=False death_reason=None heir=[]
tick=4 age=4 active=False death_reason=None heir=[]   (never recovers)
```

**Frequency.** The default maximum age is 70 fantasy years, about 20M ticks
(`src/core/state.py:165`), far beyond current corpus runs. The defect is rare in today's runs but
real for any long run. It blocks the first wave's composed lineage run (M4a).

## Scope
- Restore the semantic contract for old-age death reached through ordinary aging: one declared
  authority for the deactivation, and a recorded cause and succession whenever it happens.
- Regression evidence that exercises ordinary per-tick aging with no mid-run staging.
- Registry and parity follow-through for the touched mechanisms (`aging_death`, `succession`),
  through the normal process.

## Out of Scope
- Other death causes, except to confirm they are not regressed. That includes the starvation /
  sleep-debt gap below, which gets its own ticket if confirmed.
- General redesign of the passive-decay or apply path, and any universal revalidation API.
- M4a (the composed two-hop run), M2 (the observer evidence path), and M3a/b/c (authority checks).

## Acceptance Criteria
1. **Outcome.** An entity that ages from 0 to its maximum age through ordinary ticks ends with an
   OLD_AGE death record (cause and tick), and its designated heir receives the inheritance effects.
2. **No silent death.** In that run, no tick leaves the entity inactive without a recorded cause.
3. **Timing is explicit.** The tick on which old-age death is recorded is pinned by a test and
   documented, including any shift from today's timing.
4. **No regressions.** Existing aging, succession, lineage-dispatch, lifecycle unit, and passive-decay
   tests pass unmodified, and combat death and HP-based passive deactivation behave as before.
5. **Scope of evidence stated.** The report names which death paths were verified and which were
   left unverified.
6. **Registry and parity.** The `aging_death` and `succession` registry entries and the relevant
   parity-ledger entry cite the new evidence.

## Related Tickets
- TCK-20260904-LINEAGE-DEATH-DISPATCH (the succession dispatch this unblocks)
- TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION (`aging_death` registry note)
- TCK-20260927-LINEAGE-TWO-HOP-NATURAL-COMPOSITION (M4a, gated on this ticket)

## Related Docs
- `docs/plans/systemic_world/roadmap.md` §3.1, §7.1
- `docs/plans/systemic_world/first_wave_plan.md` M1
- `docs/mechanics/05_world_evolution.md`

## Related Stored Artifacts
None.

## Related Code Areas
`src/engine/apply.py`; `src/systems/lifecycle_systems/lifecycle.py`;
`src/entities/archetype_factory.py`. Evidence locations only, not a change list.

## Assumptions / Open Questions
- **Inactive spawns (risk).** Today, a spawn created with `initial_active=False`
  (`src/entities/archetype_factory.py:130-131`) appears to be switched on by the first lifecycle tick,
  through the same code that deactivates for age. Any resolution touching that code may change it.
  The production spawner creates entities active; the only caller of the inactive form is a unit
  test. Establish whether that implicit activation is intended. This finding comes from code
  inspection and was not run.
- **Starvation / sleep-debt death (possible sibling gap).** Passive HP loss to 0 also appears to
  deactivate an entity without a recorded cause, and the recording path recognizes only old age and
  combat. If confirmed, file separately. This finding comes from code inspection and was not run.
- **Prototype evidence, not a fix.** Local branch `natural-aging-old-age-dispatch-fix-unreviewed` (not
  pushed) holds an unreviewed prototype change and a natural-aging scenario. The scenario failed 3/3
  against current code. The prototype was started under a superseded instruction and was never run
  against the suite. It does not address the inactive-spawn risk. The implementer may consult or
  discard it.

## Implementation Notes
_Not started — owned by the implementation agent._

## Test Summary
_Not started._

## Files Changed
_Not started._

## Completion Summary
_Not started._
