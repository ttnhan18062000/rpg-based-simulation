---
status: active
layer: engine
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine, determinism]
---

# Test Plan — TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND

Tests are numbered H1–H8 to avoid collision with the death batch's T-series.

**Homes:** `tests/mechanic_scenarios/test_entity_death_authority_boundary.py` (collision + zombie
contract — it already owns this boundary and carries the defect-asserting pins), a world-dynamics unit
home for the write-level tests, `tests/unit/observability/` for the extractor assertions.

**Scoped command:**
`pytest tests/mechanic_scenarios/test_entity_death_authority_boundary.py tests/unit/observability -m "not slow"`
plus the world-dynamics unit file once chosen.

**Use a scripted scenario, not the live corpus world, for every pinned assertion.** `rpg-implementer`'s
repro caveat: frontier_marches logs "Tick N exceeded budget" and its population varies run to run under
load, as the corpus test itself showed. Its counts are cited as **order-of-magnitude evidence**, not as
pinned expectations. The existing boundary test already uses a scripted scenario — follow it.

## The collision (AC1)

**H1 — a same-tick combat kill plus nonzero hazard drain records the combat death.** The differential
C1 measured, turned into a pinned test: scripted scenario, `hazard_kind` the **only** field differing
between arms (immune vs non-immune), real `Kernel.tick_once()`.

| arm | expected |
|---|---|
| immune `hazard_kind` (control) | `death_reason='COMBAT'`, `death_tick` set, `is_permadeath=True`, succession dispatched |
| non-immune `hazard_kind` | **identical** to the control arm |

On `71c4aa321` the non-immune arm gives `death_reason=None` and `is_permadeath=False`, so this fails
before the fix for the right reason. The equality against the control arm *is* the assertion — pinning
absolute values alone would not catch a fix that changed both arms together.

**H2 — the killer and lineage survive the collision.** Assert `killer_id` attribution and that the
heirloom/nemesis/dying-wish dispatch fires in the non-immune arm. AC1 says "succession dispatched"; this
asserts the *content* survived, not merely that a death was recorded. This is the durable information
the defect destroys, so it deserves its own assertion.

## The sufficiency rule's edge cases (rule owner, 2026-10-01) — all four must be pinned

The declared rule is **not** "combat wins"; it is "the first cause in declared phase order whose own
effect was sufficient to reach 0 HP wins" (`catalog_edits.md`). An implementation of "combat always
wins" passes H1 and H2 and still gets H9 wrong, so these are not optional.

**H9 — combat non-lethal + decisive hazard records `HAZARD`.** Combat resolves `SURVIVE` (damage alone
does not reach 0), then hazard drain takes the subject to 0. Assert `death_reason = HAZARD`. **This is
the case my own original rationale would have gotten wrong** — hazard was the decisive producer, and the
earlier combat damage stays traceable through its own events (TRANS-04), not as the death cause.

**H10 — terminal `DEFEAT` + same-tick hazard keeps the `DEFEAT` classification.** Combat was sufficient,
so the sibling batch's `DEFEAT` reason stands and hazard does not override it.

**H11 — `REBIRTH` + same-tick lethal hazard still rebirths.** The most important of the four. Assert the
gen 1–3 hero ends **reborn**: `alive`, `hp == max_hp`, `generation + 1`, `is_permadeath False`. Today the
overwrite erases `REBIRTH`, so the hero dies permanently by `HAZARD` — a LIFE-02 violation *with*
permadeath. Note the rebirth restore lands in lifecycle (after `:348`), so this must be an explicit
end-state test, not inferred from the outcome label. **Blocked while the hero-rebirth question is open**
(see below).

**H12 — an immune subject cannot die of `HAZARD`.** Automatic, since `calculate_hazard_drain()` returns 0
after immunities, but pin it — and pin that a hazardous *region* alone never produces a hazard death
without a nonzero drain (LIMIT-04: never infer the cause from being in the region).

**H13 — hazard deaths are final.** `is_permadeath = True` for a genuine hazard death, by the same
sufficiency reasoning.

## BLOCKED — do not pin a HERO `death_reason` yet

`world-rule-catalog-design` raised, and the user escalated back to it, whether hero rebirth is
consistent with the world-rule model at all, given that reproduction/lineage (LIFE-04 / ID-04) already
supply continuity through a *new* identity while `REBIRTH` supplies it through the *same* identity.
Until it resolves, **no HERO `death_reason` may be pinned on the hazard path** (nor on the death batch's
passive path). H11 is affected directly. Note from `rpg-implementer`: `V2EntityBuilder` defaults to role
**HERO, gen 1**, so any fixture not explicitly setting `.identity(role=...)` is a hero — check every
fixture rather than assuming.

## Hazard-only behaviour and the discriminant (AC2) — the real regression surface

**H3 — `hazard_drain_applied` still fires for a hazard-only drain.** Must pass **unchanged** before and
after. Guards S1's repointing of `event_extractor.py:778` onto the new field.

**H4 — `hazard_drain_applied` ALSO fires for a collider.** The new requirement, and the one a plain
"don't clobber" fix silently breaks (investigation Finding 1). Assert the colliding entity emits **both**
the combat death and `hazard_drain_applied`. Without this test the observability loss ships invisibly.

**H5 — the `"HAZARD"` discriminant still excludes hazard-only drains from real combat.** Assert a
hazard-only drain is still filtered by `_NON_COMBAT_OUTCOME_KINDS` (`event_extractor.py:29`,
`phase.py:95`) and `_real_combat_update`, i.e. **not** counted as a combat kill. AC2 names the opposite
outcome as "a regression, not a fix", citing
`TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION`. Conversely assert the **collider** now
*is* counted as a real combat kill — which is correct, since it is one.

**H5b — `alive_set` is never flipped `False` → `True` by hazard (S3).** Construct a `CombatUpdate`
carrying `alive_set=False` with HP that hazard arithmetic would leave positive, apply hazard, assert
`alive_set` stays `False`. Tests the guard directly rather than hoping the arithmetic never reaches it —
the investigation records this as latent, and a latent guard with no test is not a guard.

## Determinism (AC3)

**H6 — byte-identical state hash for a run with no collision.** Named seed/world, canonical state hash
compared before and after the change. This is the acceptance criterion that **ruled out reordering the
pipeline**, so it must actually be run and its result stated, not assumed. Note S1 adds a field to
`CombatUpdate` (an update type, not a durable component), so confirm whether it enters any canonical
hash; if it does, the "before" side must be captured prior to the change.

## The zombie route (R1 consequence)

**H7 — rewrite the defect-asserting pins, do not delete them (AC6).**
`test_entity_death_authority_boundary.py::test_hazard_drain_destroys_a_same_tick_combat_kill_record` is
the pin whose failure *is* the signal this fix worked. `rpg-implementer` has already updated its second
half to an interim pin (victim stays `active=True`) that names this ticket; **this ticket must tighten
that to the fixed contract** — recorded, classified, deactivated. Likewise the slow corpus test's
"hazard residue pinned non-empty" assertion, deliberately left loose by the death batch so this fix has
to tighten it: it must now assert the residue is **empty**.

**H8 — no permanent zombies remain.** A scripted scenario producing hazard-only HP-0 entities: assert
**zero** entities end `active=True` with `hp == 0` and `death_reason is None`. Cite
`rpg-implementer`'s 8-entity measurement (frontier_marches, seed 42, 400 ticks; first-seen ticks 2, 4, 5,
151, 167, 302, 303) as the **evidence this population is real and reachable**, explicitly as
order-of-magnitude, while the assertion itself runs on the scripted scenario. This is the test that
justifies stacking the ticket before merge, so it should fail loudly on the death-batch-only tree.

## Architecture tests

**HA1 — read-only logic did not mutate live state.** `WorldDynamicsSystem.resolve_dynamics` expresses
its effect only through the returned `StateUpdate`; the input `AuthoritativeState` is unmodified.

**HA2 — one declared authority for deactivation.** Assert no path outside `resolve_lifecycle` sets
`lifecycle.active=False` for an HP death. This is the contract `PROG-030` established and R1 completed,
and S4 is the last branch needed to make it true for every HP-0 population. A safety net outside
`resolve_lifecycle` was explicitly rejected, so this test is what prevents one creeping back.

**HA3 — the cause is read, never re-derived.** Assert the `HAZARD` branch reads the persisted
`outcome_kind` and never infers from `hp`, `alive`, bio thresholds or role — the same discipline the
sibling batch applies.

## Failure modes / regression-prone paths

- `event_extractor.py:471-477`'s "HAZARD-preceded" logic (killer_id `None`, prior `outcome_kind`
  `"HAZARD"`) — H5 covers the intent; read that block during implementation, since a collider now
  reaches it with `outcome_kind="KILL"` for the first time.
- The terminal-outcome constant drifting from `_DEFEATED_OUTCOME_KINDS` — plan S2 requires deriving one
  from the other or documenting why not; assert identical membership if they are meant to match.
- Q1's reason value is **blocked** on the rule ruling; H1 asserts equality with the control arm, so it
  holds whichever value is declared — but the literal must not be hardcoded in the test before the
  ruling lands.

## Out of scope

No new `@slow` tests. **SimQ is not a valid signal** — 13 of 15 grade anchors are red on untouched
`main` and ~10 are non-deterministic by construction
(`TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`); the nightly corpus-diversity CI step has
been failing since at least 2026-09-07. Do not read a red nightly as caused by this ticket.
