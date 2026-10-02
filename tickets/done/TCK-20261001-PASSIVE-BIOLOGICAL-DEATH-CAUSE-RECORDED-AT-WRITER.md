---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER
phase: done
date: 2026-10-01
tags: [bug, lifecycle, engine, determinism]
---

# TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER

## Title
Record the cause of a passive hunger/sleep-debt death at the writer, then classify it in `resolve_lifecycle`

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Passive starvation/sleep-debt HP-loss deaths are still silent: `apply.py:98-110` writes
`combat.alive=False` and `lifecycle.active=False` with no persisted cause, so `resolve_lifecycle` never
records a `death_reason` or dispatches lineage consequences. `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`
shipped no classification. Its first design inferred the cause from `hunger >= 95` /
`sleep_debt >= 98`; that was rejected (see that ticket's Implementation Notes): being at a threshold is not
the cause (`docs/world_rules/foundations/capacity.md` LIMIT-04, ACCEPT), the cause would be fabricated
(CAUSE-01, HP-02, CAUSE-05), and a `DEFEAT` leftover (non-lethal, LIFE-02) would be mislabelled with
succession fired. `DEFEAT` also hits non-HERO entities via opportunity attacks, so a role gate fails.

## Scope
- Record the cause where it is known: in `apply.py`'s passive branch, when it takes HP from positive to
  zero (`comb.hp > 0 and new_hp == 0`). A `DEFEAT`/`REBIRTH` entity is already at `hp == 0`, so this
  excludes every combat-caused zero with no role or outcome inference.
- Add it as a typed durable field with a defined lifecycle, inspection/debug visibility and
  serialization tests (Durable State Rule). Do not change the `total_passive_dmg` computation or the
  `new_hp > 0` gate.
- `resolve_lifecycle` reads the typed field (it never infers) and records distinct `STARVATION` /
  `SLEEP_DEPRIVATION` reasons with `is_permadeath_set=True` and the existing succession dispatch.
- **Run `architecture-reviewer` on the plan before writing code** (user-approved), because this adds a
  typed field on the authoritative apply path.

## Out of Scope
- DEFEAT/REBIRTH handling (`TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE`).
- The hazard route (done) and hazard-overwrites-KILL.

## Acceptance Criteria
1. A passive hunger or sleep-debt death records a distinct non-None `death_reason` and dispatches full lineage.
2. A `DEFEAT`/`REBIRTH` leftover, HERO or not, is never classified by this path.
3. The cause is a typed, serialized, inspectable field; `event_extractor.py` stays exact-match on COMBAT.
4. Architecture-reviewer verdict recorded before implementation; contract and parity docs updated.

## Related Tickets
- `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`
- `TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE`

## Related Docs
- `docs/simulation/lifecycle_systems_contract.md`
- `docs/world_rules/foundations/capacity.md` (LIMIT-04); `docs/world_rules/life-body/lifecycle.md` (LIFE-02)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK/investigation.md`

## Related Code Areas
- `src/engine/apply.py:94-110`, `src/systems/lifecycle_systems/lifecycle.py`

## Assumptions / Open Questions
- Field name and home (on `LifecycleComponent` vs elsewhere) are for Plan and the architecture review.
- **Batched (2026-10-01, direction from `world-rule-catalog-design`, user-confirmed):** this ticket ships
  as one batch with `TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE` under a
  **single** architecture review. Both change the same site — the `apply.py` passive HP gate — and
  editing that site twice from two premises is the failure C1's sequencing constraint warns about.
- **Verified 2026-10-01:** this ticket's discriminant is **role-blind**, so a starving HERO is covered
  here. `resolve_lifecycle` (`lifecycle.py:191-204`) has only `OLD_AGE` and `KILL`/`PERMADEATH`→`COMBAT`
  branches — there is no passive bio-death branch and **no** `EntityRole.HERO` exclusion anywhere on this
  path. The sibling ticket's original AC3 ("a starving HERO is recorded") is therefore satisfied by this
  ticket, and has been removed from that one to keep a single owner per behaviour.
- **Verified 2026-10-01:** the discriminant `comb.hp > 0 and new_hp == 0` is sound against the sibling's
  population precisely because a `DEFEAT`/`REBIRTH` leftover is **already** at `hp == 0`, so `comb.hp > 0`
  is false for it — no role or outcome inference is needed to exclude it.
- **Verified 2026-10-01 — affects where the guard goes:** the `active=` write in `apply.py` is guarded by
  `total_passive_dmg > 0 or new_age != life.age_ticks`, and age increments every life-due tick. A guard
  placed only on the passive-damage branch will not cover the age path. Noted here because both tickets
  touch this same condition.

## Implementation Notes

### Architecture review — 2026-10-01, verdict `NEEDS_CHANGES` (AC4)

Ran `architecture-reviewer` over v1 of both batch plans before any code, per Scope. Verdict
**`NEEDS_CHANGES`** with six required changes R1–R6. The planner independently re-verified every
load-bearing claim at `71c4aa321` before accepting (phase order, the `:147` eligibility guard, the
`:205-216` synthesis, `CombatUpdate`'s field set, `CombatPatch.apply`'s missing HP clamp, `PROG-030`'s
text). The review was correct on all of them, and **it corrected two factual errors in v1**:

1. **Blocking (R1).** v1 claimed the cause is read "on a later phase of the same tick". False:
   `kernel.py:776-781` runs `refine()` (containing the lifecycle phase, `pipeline.py:414`) **before**
   `ApplyPath.apply_generation()`, so the cause is first readable at tick N+1 — and by then
   `apply.py:109` has set `active=False`, so `lifecycle.py:147`'s
   `if not entity.lifecycle.active: continue` skips the entity before any branch runs. **The planned
   classification branch was unreachable**, and v1's own scope guard ("do not change the `new_hp > 0`
   gates") forbade the only fix. Plans v2 adopt R1: drop the HP term from `apply.py:109`'s `active=`
   expression, making `resolve_lifecycle` the sole declared authority for HP-death deactivation —
   mirroring `PROG-030`, which did exactly this for the **age** half of the same dual-writer race and
   deliberately left the HP half for this ticket.
2. **Sibling's "blocking defect" was not one (R4).** See that ticket's notes; the fix removes work.

**R1 is a scope expansion, accepted by explicit user decision 2026-10-01.** Consequences now planned:
an `intentional_divergences.md` entry for the one-tick shift; `PROG-030` (P0) joins the parity set with
its `test_path` required to pass; passive deaths begin entering `EconomicVacancyService`'s
`recent_deaths`; and `test_starvation_sleep_debt_driven_hp_loss_is_still_silent_post_fix`
(`test_natural_aging_old_age_dispatch.py:155`) becomes a **named** expected failure, updated per its own
docstring rather than deleted.

Other rulings folded into the plan: field home is `LifecycleComponent` as a **typed enum** (a transient
is impossible — the fact crosses a tick boundary); canonical inclusion confirmed, but the re-baseline
surface must be **measured** rather than asserted; the stale-cause-on-a-corpse hazard (R2) needs an
explicit clear/ignore rule and a test; the both-thresholds precedence must be a **declared** rule, not
derived from the `+= 2`/`+= 1` constants (R5); and the combat-outranks-passive guard is **cross-tick
idempotency, not branch ordering** (R6), implemented once and shared with the sibling's `DEFEAT` branch.

### Rule-owner review — 2026-10-01 (`world-rule-catalog-design`)

Requested at the user's instruction. All five batch decisions ruled rule-compliant with conditions. The
one affecting this ticket: **CAUSE-05 / TIME-02 traceability.** Once R1 moves `death_tick` to N+1 while
HP reached zero at N, the record must not lose N. The plan takes the preferred option — **the cause field
carries the zeroing tick** — so traceability lives in the data rather than in prose and survives any
future cadence change that would break a fixed `+1` relationship.

## Test Summary
Implemented in commit 384f8cc44 (one batch with the three sibling tickets).

New: `tests/mechanic_scenarios/test_passive_death_cause_and_rebirth_defeat_lifecycle.py` (T1-T7, A1-A3: hunger/sleep-debt
death recorded at tick N and classified one kernel step later, declared hunger-over-sleep precedence, non-fatal drain records
nothing, zero-HP leftovers invent no cause, combat death on the same tick wins and clears the stale cause, canonical dict,
determinism, input state not mutated). Updated, not deleted, the four named expected failures:
`test_natural_aging_old_age_dispatch.py::test_starvation_sleep_debt_driven_hp_loss_is_recorded_post_fix` (was `..._still_silent_post_fix`),
`tests/unit/engine/test_apply.py` (passive branch records the cause but never deactivates; never reactivates an inactive young
entity), `test_entity_death_authority_boundary.py` (two pins rewritten to the fixed contract), and
`test_dirty_set_passive_decay_consumers.py` (no longer asserts an `active` flip). `PROG-030`'s P0 `test_path` passes.
R1 formula correction (measured): the planned `active=(life.active or new_age < max_age)` re-activated every dead young
entity (24 DEFEAT corpses ended active=True in 400 ticks); the passive branch now never deactivates and its only `active`
write is the `initial_active=False` spawn reactivation gated on `new_hp > 0` and no death record.
Broad non-slow sweep: failures are only pre-existing on base (`test_behavioral_5k_regression`, `test_long_run_stability`,
`test_bravery_quartile_combat_rate_2x`, `test_cert_long_run_stability` x3, one collection error) or load-sensitive and
passing in isolation; certification identical to base. SimQ deliberately not cited (anchors red on main).

## Files Changed
Landed in PR #276 (`786f9ee9b`, implementation commit `384f8cc44`).
- `src/engine/apply.py` (passive branch records the cause at the HP>0 -> 0 transition; never deactivates), `src/core/updates.py`, `src/core/state.py`, `src/core/enums.py`, `src/systems/lifecycle_systems/lifecycle.py` (`resolve_lifecycle` reads the typed field, records `STARVATION` / `SLEEP_DEPRIVATION`).
- Tests: `tests/mechanic_scenarios/test_passive_death_cause_and_rebirth_defeat_lifecycle.py` (new), `test_natural_aging_old_age_dispatch.py`, `test_entity_death_authority_boundary.py`, `tests/unit/engine/test_apply.py`, `test_dirty_set_passive_decay_consumers.py`.
- Docs: `docs/simulation/lifecycle_systems_contract.md`, parity ledger, `docs/guidelines/intentional_divergences.md`.

## Completion Summary
Passive hunger / sleep-debt deaths now persist a typed cause at the apply-path writer and `resolve_lifecycle` classifies them (`STARVATION` / `SLEEP_DEPRIVATION`, permadeath, succession dispatched) without inferring from thresholds, role or outcome. Zero-HP leftovers never get a cause. The R1 formula correction (passive branch never deactivates) is recorded in Implementation Notes. Architecture-reviewer verdict was recorded pre-implementation. All ACs met; SimQ deliberately not cited (anchors red on main).
