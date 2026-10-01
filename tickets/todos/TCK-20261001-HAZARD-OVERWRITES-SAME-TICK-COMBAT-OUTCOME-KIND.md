---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND
phase: open
date: 2026-10-01
tags: [engine, lifecycle, combat, determinism]
---

# TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND

## Title
`WorldDynamicsSystem.resolve_dynamics` unconditionally overwrites a victim's same-tick
`outcome_kind="KILL"` with `"HAZARD"`, erasing the combat death record before
`resolve_lifecycle` ever reads it

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Filed 2026-10-01 out of `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK` (Card C1), which
confirmed this defect but is a check and does not fix. **No existing open ticket covers it** — the
sibling routing target (`TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`) owns the *missing
HP/alive death branch*, which is a different defect with a different fix.

`src/engine/world_dynamics.py:39` does:

```python
c_upd = replace(c_upd, hp_delta=c_upd.hp_delta - hazard_dmg, outcome_kind="HAZARD", alive_set=(new_hp > 0))
```

`c_upd` is the victim's **already-accumulated** `CombatUpdate` for this tick, which may already
carry `outcome_kind="KILL"` from combat resolution. The overwrite is unconditional. It is
positioned exactly between the phase that writes `KILL` and the phase that reads it:
`action_routing` (`pipeline.py:297`) → `combat_engagement` (`:320`) → **`world_dynamics` (`:348`)**
→ `lifecycle` (`:414`), all inside one accumulating `StateUpdate`. The eligibility guard
(`world_dynamics.py:31`) reads **committed** state, where a victim killed earlier in this same tick
is still `alive`/`active` — so the victim is always eligible. The `KILL` sits on the **victim's**
own `EntityUpdate` (`combat.py:495`, `:553`), which is precisely the key
`resolve_lifecycle:202` reads.

Result: `resolve_lifecycle` sees `"HAZARD"`, does not match `("KILL","PERMADEATH")`, and the combat
death is never recorded — no `death_reason`, no `death_tick`, no `is_permadeath`, and therefore no
succession, heirloom or lineage dispatch. Regional trauma is still booked. Deactivation lands a
tick late via `apply.py:109`'s passive HP gate, with no cause.

**C1's measured differential** (`mechanic_scenario_combat_judgement_withdrawal`, real
`Kernel.tick_once()`, `hazard_kind` the only field changed between arms, engine `e9db40f0a`):

| arm | drain | after tick 1 | after tick 2 |
|---|---|---|---|
| immune `hazard_kind` | 0 | `death_reason='COMBAT'`, `death_tick=0`, `permadeath=True` | unchanged |
| non-immune `hazard_kind` | 10 | `active=True`, `death_reason=None`, `permadeath=False` | `active=False`, `death_reason` **still** `None` |

## Scope
- Make the hazard write stop destroying a same-tick combat outcome. The shape of the fix is the
  open design question (see Assumptions) — an accumulating/priority-aware `outcome_kind`, a
  separate hazard field, or ordering — and is **not** pre-decided here.
- Preserve the hazard mechanic's own effects: `hp_delta` accumulation, `alive_set`, the
  `hazard_drain_applied` observability path (`event_extractor.py:774-778`), and the
  `_NON_COMBAT_OUTCOME_KINDS` combat-classification discriminant that depends on `"HAZARD"` being
  distinguishable from a real combat resolution.
- Determinism must hold: identical seed/world must produce identical results before and after.
- Regression coverage for the collision, replacing C1's defect-asserting pins.

## Out of Scope
- **The missing HP/alive death branch in `resolve_lifecycle`** — that is
  `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`. The two fixes are complementary, and this
  ticket must not grow a `death_reason` classification branch of its own.
- `DEFEAT`/`REBIRTH` routes to `alive_set=False` (same sibling ticket).
- Re-deriving the two ownership writers in
  `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` — it already carries that comparison.
- Changing hazard damage magnitude, `calculate_hazard_drain`, or faction hazard immunities.

## Acceptance Criteria
1. A same-tick combat kill on an entity also taking nonzero hazard drain records a combat death:
   `death_reason='COMBAT'`, `death_tick` set, `is_permadeath` set, succession dispatched — matching
   the hazard-free control arm.
2. Hazard-only drain deaths keep their current observable behaviour, and the `"HAZARD"`
   discriminant that `_NON_COMBAT_OUTCOME_KINDS` and `_real_combat_update` rely on still
   distinguishes hazard drain from a real combat resolution. A fix that makes hazard deaths look
   like combat kills to the event extractor is a regression, not a fix — that exact
   miscounting was `TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION`'s subject.
3. Determinism preserved: a named seed/world produces a byte-identical state hash before and after
   for a run containing no collision.
4. **AC6 inherited from C1 — escalation before implementation.** This fix touches the ordering /
   write-precedence between world dynamics and lifecycle, so it must be escalated to the planner
   before it is written, and **sequenced against
   `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`**, which is determinism-sensitive (a
   naive consolidation delays death-driven ownership changes by one tick).
5. **AC7 inherited from C1** — this changes who effectively decides alive/dead, so
   `make semantic-control-plane-drift-check` is run afterwards and its output **shown**, not
   assumed. SCP rows `LIFE-01`/`LIFE-02` cite `combat_resolution`; the check is report-only
   (exit 0 always), so a clean run must be demonstrated.
6. `tests/mechanic_scenarios/test_entity_death_authority_boundary.py`'s defect-asserting tests are
   **rewritten to the fixed contract, not deleted** — their failure is the signal this fix worked.
7. Parity ledger updated: the relevant `combat_movement.yaml` / `world_dynamics.yaml` entries get
   `status` + `v2_evidence` refreshed, per the Authoritative Mechanics Rule.

## Related Tickets
- `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK` — the check that confirmed this; carries the
  full evidence and the AC6/AC7 inheritance.
- `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP` — complementary, not duplicate. Fixing
  either alone leaves a gap; see Assumptions Q2.
- `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` — **held**; hard sequencing constraint,
  see AC4.
- `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` — merged `5d4e4a237` (PR #254); made
  `resolve_lifecycle` sole authority for old-age deactivation. Same field, different cause.
- `TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION` — why the `"HAZARD"` discriminant
  must survive this fix (AC2).

## Related Docs
- `docs/plans/systemic_world/roadmap.md` §3.1 — boundary 2, 2026-10-01 addendum.
- `docs/engine/authoritative_mutation_pipeline_contract.md` — mutation rules and apply-path law.
- `docs/engine/kernel.md` — the 7-phase deterministic loop.
- `docs/simulation/lifecycle_systems_contract.md` — declared death authority.
- `docs/mechanics/05_world_evolution.md` — regional hazard law.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK/investigation.md` — the
  differential, the production evidence, and the instrument caveats.

## Related Code Areas
- `src/engine/world_dynamics.py:30-41` — the hazard loop and the unconditional overwrite.
- `src/engine/pipeline.py:348` vs `:297`/`:320`/`:414` — the phase ordering that makes it reachable.
- `src/systems/lifecycle_systems/lifecycle.py:202-218` — the reader and the `if is_dead:` block.
- `src/engine/combat.py:495`, `:553` — where `KILL` is written onto the victim's update.
- `src/observability/event_extractor.py:27-47`, `:774-778` — the `"HAZARD"` discriminant (AC2).
- `tests/mechanic_scenarios/test_entity_death_authority_boundary.py` — the pins to rewrite.

## Assumptions / Open Questions
- **Q1. What should the collision actually record?** A combat kill that coincides with lethal
  hazard damage is arguably either. C1 takes no position. The Mechanics Bible
  (`docs/mechanics/02_combat_laws.md`, `05_world_evolution.md`) should be checked for an existing
  law before inventing one; if neither declares precedence, this needs a declared rule and an
  `intentional_divergences.md` entry rather than an implementation guess.
- **Q2. Ordering against the sibling ticket.** If
  `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP` lands first and keys its new branch on
  "`combat.alive=False` with no `death_reason`", the collision would then be *recorded* — but as a
  passive/hazard death, still losing the combat attribution and the killer. That is an improvement,
  not a fix for this ticket. Confirm which lands first and re-check this ticket's AC1 against it.
- **Q3.** Whether `hp_delta` double-counting is also in play when combat and hazard both apply in
  one tick was **not** separately verified by C1 — the observed `hp` floors at 0 either way, so the
  arithmetic is not provably correct, only not provably wrong. Worth checking during
  implementation.
- **Reachability is low but nonzero, and this is not a reason to deprioritise below P1.** C1 saw 0
  `KILL`/`PERMADEATH` in 120 unscripted corpus ticks and hazard drain on 0.3% of entity-ticks, so
  the conjunction is rare. The severity is that it silently destroys a durable record when it does
  fire, and the `@slow`/unreported-anchor situation
  (`TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`) means nothing would report it.

## Implementation Notes
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._
