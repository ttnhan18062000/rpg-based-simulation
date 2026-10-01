---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine]
---

# TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE

## Title
A `DEFEAT` / `REBIRTH` outcome, classified non-lethal, is silently converted into a permanent death by
`apply.py`'s passive HP gate one tick later

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Accepted world rule `docs/world_rules/life-body/lifecycle.md` **LIFE-02** (Disposition: ACCEPT) says that
losing active-participant status "does not, by itself, entail permanent lifecycle termination", and names
`DEFEAT` (non-lethal; `combat.py:136` forces `is_lethal=False` for `EntityRole.HERO`) and `REBIRTH`
(`generation_delta=1`, identity continues) as non-lethal outcomes; only `PERMADEATH` is final.

An entity driven to 0 HP by a non-lethal outcome gets `alive_set=False` and keeps `lifecycle.active=True`.
Nothing in `src/` ever sets `combat.alive=True` again (every `alive=True` is construction or a harness).
One tick later `ApplyPath._compute_entity_changes` (`src/engine/apply.py:106-109`) computes
`active=(new_hp > 0 and ...)` for the 0-HP entity and deactivates it, with no `death_reason`. So a
non-lethal outcome becomes a silent permanent death, and `REBIRTH` increments `generation` on an entity
that is then deactivated rather than reborn. This is the opposite error from the hazard route (a death
not recorded as one) fixed by `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`.

**Note on the deactivation trigger (verified 2026-10-01).** The `active=` write is guarded by
`total_passive_dmg > 0 or new_age != life.age_ticks`, and age increments on *every* life-due tick. So for
a 0-HP leftover carrying no passive damage, the `changes["combat"]` replace is skipped
(`new_hp == comb.hp == 0`) while `active=(new_hp > 0 and ...)` still evaluates `False`. The deactivation
therefore arrives via the **age** path, not the passive-damage path — a fix that only guards the
passive-damage branch will not close this.

**Premise correction (verified 2026-10-01 at `71c4aa321`): a HERO never reaches a terminal `DEFEAT`.**
This ticket's original summary and AC1 asserted a `DEFEAT` outcome on a HERO; that state is unreachable.
`combat.py:171` sets `outcome = "KILL" if is_lethal else "DEFEAT"`, but `:182-187` then overrides it
whenever `classification.rebirth_eligible` — and **both** classification paths return
`rebirth_eligible=True` for a HERO (`combat_rewards.py:106` on the relation-projection path;
`_CLASSIFICATIONS[EntityRole.HERO]` on the legacy-role fallback). A HERO at 0 HP is therefore always
`REBIRTH` (`generation < 4`) or `PERMADEATH` (`generation >= 4`). Terminal `DEFEAT` survives only where
`is_lethal=False` was passed by the caller **and** the target is not rebirth-eligible — i.e. a **non-HERO
hit by an opportunity attack**. This matches the corpus (4 `DEFEAT` vs 1 `REBIRTH` in 120 ticks) and
resolves `docs/world_rules/life-body/lifecycle.md`'s own open question 1 (`DEFEAT` is a live, reachable
outcome, not vestigial) — that doc text is owned by `world-rule-catalog-design` and handed to it, not
edited here.

**Design decisions (user, 2026-10-01).** Both were open because no accepted rule settled them:
1. **`REBIRTH` restores `combat.hp = max_hp` and `alive = True`**, alongside the existing `generation`
   increment. This is the plain reading of `docs/mechanics/02_combat_laws.md:65` ("they are reborn") and
   needs no recovery mechanism that does not exist; rebirth stays costly through the `generation` counter
   advancing toward the gen-4 permadeath cap.
2. **A terminal `DEFEAT` resolves to a recorded death with its own distinct `death_reason`**, rather than
   a new durable downed/recoverable state. Consistent with LIFE-02, which requires that a real
   classification process decide the outcome — not that every defeat be survivable — and it ends the
   silent unrecorded deactivation without inventing a revival writer.

Production evidence (`frontier_marches`, seed 42, 120 ticks, `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK`):
`DEFEAT` at ticks 20/68/113/115, `REBIRTH` at tick 88; the leftover entities remain combat-dead and
unrecorded (`tests/mechanic_scenarios/test_entity_death_authority_boundary.py`, corpus test).

## Scope
- Make `REBIRTH` actually rebirth: restore `combat.hp = max_hp` and `alive = True` on the authoritative
  apply path, alongside the existing `generation` increment, per decision 1 above. The restore must be a
  typed update applied through the authoritative path, never an in-place mutation in the resolver.
- Record a terminal `DEFEAT` as a death with its own distinct `death_reason`, per decision 2 above, so it
  stops being a silent deactivation. `resolve_lifecycle` (`lifecycle.py:202`) currently branches only on
  `("KILL", "PERMADEATH")`; the `DEFEAT` discriminant is added there, reading the persisted
  `outcome_kind` — never inferring from HP, role or bio thresholds.
- Make `apply.py`'s `active=` gate agree with both: a reborn entity must not be deactivated by the age
  path on the following tick, and a terminal `DEFEAT` must be deactivated *with* its reason recorded.
- Rewrite the corpus test's "DEFEAT/REBIRTH leftovers remain unrecorded" assertion to the new contract.
- Record the `REBIRTH` HP-restore value in `docs/mechanics/02_combat_laws.md` (the law states rebirth but
  no HP value) and update the `progression.yaml` / `combat_movement.yaml` parity entries this touches.

## Out of Scope
- The hazard route and the passive bio-death cause (`TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER`,
  this batch's sibling — it owns every passive-cause death, HERO included, via a role-blind discriminant).
- The hazard-overwrites-KILL defect (`TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND`).
- Any new durable downed/recoverable state or revival writer — explicitly rejected by decision 2.

## Acceptance Criteria
1. A terminal `DEFEAT` (non-HERO, opportunity attack) ends in a death recorded with a distinct
   `death_reason`, not a silent unrecorded deactivation. A test asserts the reason is non-None and
   distinguishable from `COMBAT` and from the sibling ticket's passive-cause reasons.
2. A `REBIRTH` outcome yields an entity that is alive at `max_hp` with `generation` incremented, and that
   is still active on the following life-due tick (regression-guards the age-path deactivation above).
3. A HERO at `generation >= 4` still resolves to `PERMADEATH` — unchanged; a test pins that this batch
   did not widen the rebirth path.
4. `docs/mechanics/02_combat_laws.md` records the rebirth HP-restore value; any departure from it is
   recorded in `docs/guidelines/intentional_divergences.md` with a rationale class and verification path;
   the parity-ledger entries touched are updated in the same session.
5. LIFE-02's evidence note and its open question 1 are updated **by `world-rule-catalog-design`**, not by
   this ticket — the finding is handed over, and the handover is recorded in Implementation Notes.

## Related Tickets
- `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`
- `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK`

## Related Docs
- `docs/world_rules/life-body/lifecycle.md` (LIFE-02, scenario LB-S02)
- `docs/mechanics/02_combat_laws.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK/investigation.md`

## Related Code Areas
- `src/engine/apply.py:94-110`, `src/engine/combat.py:136,182-187`, `src/engine/combat_rewards.py:106`,
  `src/systems/lifecycle_systems/lifecycle.py`

## Assumptions / Open Questions
- **Closed (user, 2026-10-01):** rebirth restores full HP + `alive`; a terminal `DEFEAT` becomes a
  recorded death with a distinct reason. See the two decisions in Request Summary.
- **Closed (verified, 2026-10-01):** a HERO cannot reach a terminal `DEFEAT`; the "defeated HERO" framing
  this ticket opened with was false. See the premise correction in Request Summary.
- Open, for Plan and the shared architecture review: the exact `death_reason` string for a terminal
  `DEFEAT`, and whether the `REBIRTH` HP restore belongs in `CombatUpdate` or in a lifecycle-side typed
  update. Both are placement questions, not semantic ones.
- Open: whether a reborn entity should also have accumulated `WoundState`/`ScarState` cleared. Not
  assumed either way here; BODY-03 holds that HP loss and injury are related but not identical facts, so
  restoring HP does not self-evidently clear wounds. Flagged for the architecture review.

## Implementation Notes

### Architecture review — 2026-10-01, verdict `NEEDS_CHANGES` (shared with the batch primary)

Full record in `TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER`'s notes. The two changes
specific to this ticket:

**R4 — this ticket's stated "blocking defect" was not real, and the fix removes work.** v1 claimed
`movement.py:248-252`'s guard means "no lifecycle update reaches the apply path at all" for a terminal
`DEFEAT`. Verified false: `resolve_lifecycle` **synthesizes its own** update —
`ent_upd = ent_upd or EntityUpdate(entity_id=e_id)` then `life_upd = ent_upd.lifecycle or LifecycleUpdate()`
(`lifecycle.py:205-216`) — so a `death_reason` reaches the apply path regardless. The real gap is solely
the missing `DEFEAT` discriminant at `lifecycle.py:202`. Widening the guard as planned would emit an
`is_noop()`-true update carrying nothing; the only widening that *would* carry something puts lifecycle
classification inside an opportunity-attack call site, the inversion this ticket rejects elsewhere.
**v1's S3 and test T11 are dropped**; T11′ instead pins the synthesis invariant.

**R3 — `CombatUpdate` cannot express "restore to `max_hp`".** It carries only relative `hp_delta`
(`updates.py:104`), and `CombatPatch.apply` computes `max(0, new_combat.hp + hp_delta)` with **no upper
clamp**, against a `changes["combat"]` that Section A may already have drained by up to 3 HP on a
life-due tick. A delta-based restore therefore lands at `max_hp - passive_drain`, making
`combat.hp == max_hp` cadence-dependent. Plan adds `hp_set: Optional[int]` following the existing
`alive_set`/`*_set` precedent. Also confirmed: the `alive` restore must be an **explicit positive write**,
because `combat.py:171` already set `alive_set=False` and `patches.py:322` honours it regardless of HP.

### Rule-owner review — 2026-10-01 (`world-rule-catalog-design`), requested by the user

All four decisions touching this ticket ruled rule-compliant, with conditions:

1. **`is_permadeath_set=True` on a `DEFEAT` death does NOT collapse LIFE-01 — no divergence needed.**
   The planner raised this as a possible violation and offered dropping the flag as an option; **that
   option would have been the actual violation** (a non-final death with no return path breaks
   `is_permadeath` as the single final marker LIFE-01/ID-05/LB-S02 rely on, creating permanent limbo).
   LIFE-01 requires the two facts to be *separately tracked*, not that both cannot be true; conflation
   means **deriving** one from the other, and this design derives `is_permadeath` from a real
   classification exactly as `KILL`→`COMBAT` and `OLD_AGE` already do through the same block. The owner
   is correcting LIFE-01's misleading evidence sentence itself (verbatim EDIT R2).
2. **Rebirth's HP restore must be *declared* in the rebirth law**, not left a code side effect — BODY-05
   forbids undeclared recovery, not a restore a declared law produces. Also: **do not build a general
   `heal` helper**; this is a rebirth-only consequence and general recovery stays MISSING.
3. **Terminal `DEFEAT` as a recorded death: confirmed**, with a stronger supporting argument than the
   planner's — since no recovery process exists anywhere (BODY-05), a "downed, recoverable" state would
   be permanent limbo, a fact claiming recoverability the world can never deliver. LIFE-02's
   continued-existence route is realised by `REBIRTH`.
4. **Wounds/scars persist across rebirth: rule-compliant as the default**, and a reset would be a
   *gameplay/balance* decision for the user, not a rule requirement. Ship no-reset, record it in the
   rebirth law, and **file a KEEP balance follow-up** to measure cross-generation penalty accumulation
   once SimQ is trustworthy. Do not decide balance by rule.

**Four verbatim catalog edits (R1–R4) are recorded in `plan.md` S6 and must land in the same commit as
the code that makes them true — never ahead of it.** They satisfy AC5 as the catalog-side update.

## Test Summary
Terminal `DEFEAT` is a recorded death (`death_reason="DEFEAT"`, `is_permadeath`, succession dispatch) classified by
`resolve_lifecycle` from the persisted `outcome_kind` (T8, T10, T11', T14 in
`tests/mechanic_scenarios/test_passive_death_cause_and_rebirth_defeat_lifecycle.py`; end-to-end proof in
`tests/unit/movement/test_tactical_movement.py::test_opportunity_attack_lethal_hero_defender_is_a_terminal_defeat_without_rebirth`).
The planned REBIRTH HP/alive restore (S2/R3, `hp_set`) and T9/T9b were WITHDRAWN and reverted after the rule owner found
STR-02 (resurrection needs a declared process); hero rebirth was then retired entirely by
TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION. Catalog edits R1/R3/R4 withdrawn, R2 applied.
Corpus boundary test rewritten (not deleted): every terminal DEFEAT recorded and inactive (was 4 unrecorded in 120 ticks).

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._
