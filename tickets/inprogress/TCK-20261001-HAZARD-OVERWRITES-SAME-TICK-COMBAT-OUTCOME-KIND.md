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
INPROGRESS

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
- **The HP/alive-keyed death branch in `resolve_lifecycle`** — that is
  `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP` and its successor
  `TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER`. The two fixes are complementary.
  **NARROWED 2026-10-01:** this exclusion was aimed at the *HP/alive-keyed* branch and still holds for
  it. It does **not** exclude an `outcome_kind == "HAZARD"`-keyed branch, which this ticket now does
  need (AC2 as amended) — that is the same shape as the existing `KILL`/`PERMADEATH` branch, and the
  ticket's own Q2 answer already placed the `HAZARD` classification "with or after" this fix. R1 turned
  "with or after" into "with", because "after" now means shipping permanent zombies.
- `DEFEAT`/`REBIRTH` routes to `alive_set=False` (same sibling ticket).
- Re-deriving the two ownership writers in
  `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` — it already carries that comparison.
- Changing hazard damage magnitude, `calculate_hazard_drain`, or faction hazard immunities.

## Acceptance Criteria
1. A same-tick combat kill on an entity also taking nonzero hazard drain records a combat death:
   `death_reason='COMBAT'`, `death_tick` set, `is_permadeath` set, succession dispatched — matching
   the hazard-free control arm.
2. **AMENDED 2026-10-01 — the original wording is no longer achievable, see Implementation Notes.**
   A hazard-only drain death is **recorded and classified**: `death_reason='HAZARD'`, `death_tick` set,
   `is_permadeath=True`, deactivated by `resolve_lifecycle` as the sole declared authority. Their
   *previous* observable behaviour — deactivated one tick late and silently by `apply.py`'s HP gate — was
   removed by R1 in `TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER`, so "keep their
   current observable behaviour" would now mean keeping a permanent zombie. `HAZARD` is a legitimate
   declared cause of death per BODY-07 / ENV-02 (rule owner, 2026-10-01), **only** where the drain
   itself took HP from `> 0` to `<= 0`, never inferred from being in a hazardous region (LIMIT-04); an
   immune subject cannot die of it.
2b. The `"HAZARD"`
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
- **Q2 answered 2026-10-01: recording a hazard death must NOT land before this ticket.** An attempt
  (`TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`'s `HAZARD` branch in `resolve_lifecycle`, keyed on
  `outcome_kind == "HAZARD"` and `alive_set is False`) was reverted after peer review. `world_dynamics.py:39`
  overwrites the incoming `outcome_kind` (`KILL`, `DEFEAT` or `REBIRTH`) with `"HAZARD"` before
  `resolve_lifecycle` reads it, so the branch cannot tell a hazard death from a hazard-overwritten
  non-lethal outcome. Demonstrated by `rpg-feature-planning` on `mechanic_scenario_combat_judgement_withdrawal`:
  a HERO defender at `generation=1` takes the `REBIRTH` branch; with an immune `hazard_kind` the result is
  `gen` 1 to 2, no death record, `is_permadeath=False` (LIFE-02 honoured); with a non-immune kind it is
  `death_reason='HAZARD'`, `is_permadeath=True`, and the succession dispatch fires. The discriminant exists
  only before the overwrite, so this ticket (decline to clobber a non-lethal outcome, or carry hazard
  lethality in a separate field) is the prerequisite; the `HAZARD` classification lands with or after it.
  The branch is on record in `stored_artifacts/TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP/`.
- **Reachability is low but nonzero, and this is not a reason to deprioritise below P1.** C1 saw 0
  `KILL`/`PERMADEATH` in 120 unscripted corpus ticks and hazard drain on 0.3% of entity-ticks, so
  the conjunction is rare. The severity is that it silently destroys a durable record when it does
  fire, and the `@slow`/unreported-anchor situation
  (`TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`) means nothing would report it.

## Implementation Notes

### AC4 joint planning + AC6 escalation — DISCHARGED 2026-10-01 (planner)

Full record in `staging_artifacts/TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND/`.

**Joint premise with `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`** (both tickets concern
the same `world_dynamics` `pipeline.py:348` → `lifecycle` `:414` ordering): **this fix is
order-independent and does not move `world_dynamics`.** Reordering was ruled out because **AC3** demands
a byte-identical state hash for non-collision runs, and moving `world_dynamics` relative to `lifecycle`
changes hazard timing for *every* hazard-affected entity (hazard drain touches ~0.3% of entity-ticks)
rather than only colliding ones (0 in 120 corpus ticks). The hazard write (`world_dynamics.py:30-40`)
and the ownership sweep (`:44+`) are separate blocks in one function, so the sovereignty ticket retains
all three of its recorded outcomes and is **not** pre-empted. Confirmed sound by the rule owner against
roadmap §3.1.

**Two findings that invalidate the obvious fixes:**
1. A plain non-clobbering conditional is **insufficient**. `event_extractor.py:778` emits
   `hazard_drain_applied` **only** when `outcome_kind == "HAZARD"`, so merely declining to overwrite a
   `KILL` preserves the combat death but **silently drops the hazard observability event** for exactly
   the colliding entities — violating AC2. Hazard application must be signalled **independently** of
   `outcome_kind`.
2. `alive_set=(new_hp > 0)` at `:39` is written unconditionally and `CombatPatch.apply`
   (`patches.py:322`) honours `alive_set` over the HP-derived value, so hazard could **resurrect** a
   defeated entity. Latent, not observed — implement as a guard.

**Q1 answered by the rule owner, 2026-10-01 — and the planner's reasoning was wrong while its answer
was right.** The planner argued combat wins because it carries more durable information; the ruling is
**sufficiency plus declared phase order**: a `KILL` means combat damage *alone* was sufficient to take
the subject from `hp > 0` to `hp <= 0` (`combat.py:163-171`, start-of-tick HP, combat damage only),
resolved first at `:297`/`:320`. Recording `HAZARD` would assert a causal link that did not exist —
CAUSE-03 (adjacency ≠ causation), CAUSE-06 (no invented causal relations), LIMIT-04 (pushing HP further
below zero is not a cause). So the rule is **not** "combat always wins" but "the first sufficient cause
in phase order wins", which decides the edge cases information-content cannot — notably **a non-lethal
combat hit plus decisive hazard drain records `HAZARD`**. **No new world-rule Rule ID** is needed (an
application of CAUSE-03/CAUSE-06/LIMIT-04/BODY-07 — a reference, not a new Rule); the engine-level law
goes in the Bible, verbatim text in `catalog_edits.md`.

### BLOCKED — no HERO `death_reason` may land yet

The rule owner flagged, and the user escalated back to it, whether **hero rebirth is consistent with the
world-rule model at all**, given that reproduction/lineage (LIFE-04 / ID-04) already provide continuity
through a *new* identity while `REBIRTH` provides it through the *same* identity, and that
`rebirth_eligible` is `True` only for `EntityRole.HERO` (`combat_rewards.py:44-51`, `:106`) with no Rule
ID granting a role-specific lifecycle exemption. Until that resolves: **do not land a HERO
`death_reason`** on this path or the death batch's passive path, and do not land `catalog_edits.md`'s
Bible block (its `REBIRTH` bullet is contingent). Test H11 is directly affected. Note
`V2EntityBuilder` defaults to role **HERO, gen 1**, so any fixture not explicitly setting
`.identity(role=...)` is a hero.
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._
