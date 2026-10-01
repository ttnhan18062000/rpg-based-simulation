---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION
phase: open
date: 2026-10-01
tags: [lifecycle, combat, progression, architecture]
---

# TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION

## Title
Retire hero `REBIRTH` — it is an undeclared resurrection mechanism that fails STR-02/ID-02/CAUSE-04/ID-06
and duplicates the reproduction/succession continuity model

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
**User decision, 2026-10-01: retire hero rebirth.** Raised by the user while reviewing the death batch
("hero rebirth seem not follow with our world rule ... because we already thought about reproduction"),
analysed by `world-rule-catalog-design`, which **reversed its own earlier approval** of implementing the
rebirth HP/`alive` restore. The planner verified the governing citation directly.

**`REBIRTH` is resurrection, and it is undeclared.** `docs/world_rules/magic-supernatural/supernatural-transformation.md:84`
**STR-02** (Disposition: **ACCEPT**) requires, for any same-identity return after death: (a) the death
remains a real historical fact that resurrection never erases, (b) a **declared supernatural process**,
and (c) that process explicitly declaring whether the same identity returns. `REBIRTH` has none: no
death is recorded, there is no declared process, and same-identity is simply assumed via an unchanged
`entity_id`. STR-02's own evidence line asserts "no resurrection mechanism exists anywhere" — which is
how the catalog never recognised `REBIRTH` as one. Calling it "non-lethal defeat" was a reframing that
let it bypass STR-02.

Additional accepted rules it fails:
- **ID-02** — identity and its fate are not determined by role. `rebirth_eligible` is `True` **only**
  for `EntityRole.HERO` (`combat_rewards.py:44-51`, `:106`).
- **CAUSE-04** — capability gates must be real state, not narrative. A role-exclusive exemption from
  death has no in-world capability behind it.
- **ID-06** — identity behaviour across the reset was never declared, so it is silently assumed.

**It collides with the user's own continuity model.** LIFE-04/ID-04 and lineage-descent make continuity
happen through *new* identities — reproduction, heirs, heirlooms, feuds, dying wishes. Hero rebirth
answers the same world question the opposite way, and reuses the same word: `lifecycle.generation` counts
**rebirths of one entity** while lineage "generations" are new identities. It also defers succession for
heroes across four lives, working against the succession goals.

**Retiring it removes nothing anyone has experienced.** `REBIRTH` has never worked at runtime — every one
ends in permanent silent deactivation (C1's evidence; the `apply.py` gate). Implementing the restore
would have been the *first* time the mechanic existed. This is the cheap moment.

**This ticket also unblocks a merge.** With the restore dropped and R1 kept, a `REBIRTH` defender ends
`hp=0`, `alive=False`, `generation + 1`, `lifecycle.active=True` and **nothing deactivates it** — the
`DEFEAT` branch ignores `REBIRTH` and the HERO branch is held. That makes `REBIRTH` a second zombie class
alongside the hazard population (`rpg-implementer`, measured). The death batch cannot merge until this
lands.

## Scope
- Remove rebirth eligibility: `combat_rewards.py:44-51` (`_CLASSIFICATIONS[HERO].rebirth_eligible`) and
  `:106` (the relation-projection path). Retire the `REBIRTH` and `PERMADEATH` outcome kinds, or fold
  them into `KILL` — decide and justify, do not do both.
- `combat.py:136`'s `is_lethal = is_lethal and (role != EntityRole.HERO)` goes **with this ticket**:
  after retirement, leaving it would make a lethal hit on a former hero resolve as terminal `DEFEAT`
  rather than `KILL`. A lethal hit must become an ordinary recorded `COMBAT` death with
  succession/heirs/heirlooms firing as for any subject.
- `lifecycle.generation`: decide whether it is removed or kept as a **true lineage generation** (birth
  order). Either way it must stop meaning "rebirth count". Check consumers at
  `event_extractor.py:66`, `:1283` and `apply_plan.py:347`.
- Rewrite `docs/mechanics/02_combat_laws.md` §"The Hero's Journey (Generations)" to remove the
  generations-of-rebirth law.
- `docs/guidelines/intentional_divergences.md` entry — rationale class **Intentional Gameplay Change**,
  citing STR-02/ID-02/CAUSE-04 and the reproduction continuity model, with a verification path.
- Update parity entries: `combat_movement.yaml::COMB-297` and the outcome-lattice entry,
  `progression.yaml` rebirth/generation entries.
- Catalog text is drafted by `world-rule-catalog-design` and lands **with** this code: LIFE-02's evidence
  becomes "permitted, not currently realised"; STR-02's evidence becomes "no resurrection mechanism
  exists; the former hero `REBIRTH` (retired 2026-10-01) was an undeclared one"; LB-S02 updated.

## Out of Scope
- **The broader "stop relying on the term hero" direction** — `EntityRole.HERO`-gated rewards, the
  hero-guild routing content, `hero_adventurers`, `HERO_*` event names. That is epic-sized, needs an
  inventory before ticket planning, and is tracked separately. Only the rebirth-specific HERO coupling
  (`combat_rewards` eligibility and `combat.py:136`) is in scope here.
- Designing resurrection as a real feature. The user chose retirement, not redesign. If resurrection is
  ever wanted it needs its own epic designed to STR-02 (declared process gated on real state, each death
  recorded as history first, declared identity semantics, counter renamed).
- The hazard zombie route — `TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND`.
- The death batch's own cause-at-writer, `DEFEAT`-recording and R1 work.

## Acceptance Criteria
1. No code path grants `rebirth_eligible` on the basis of `EntityRole.HERO`; no `REBIRTH` outcome is
   produced. A test asserts a lethal hit on a former hero records an ordinary `COMBAT` death with
   `death_tick`, `is_permadeath=True` and succession/heirloom dispatch.
2. No entity ends `hp == 0` with `lifecycle.active=True` via the former rebirth path — the second zombie
   class is closed, demonstrated on the same scenario that exposed it.
3. `lifecycle.generation` no longer means "rebirth count"; its decided meaning is documented and every
   consumer (`event_extractor.py:66`, `:1283`, `apply_plan.py:347`) agrees with it.
4. Bible 02's rebirth law is rewritten; an `intentional_divergences.md` entry exists with rationale class
   and verification path; parity entries updated.
5. The death batch's HERO `death_reason` hold is released, because former heroes die like any subject —
   sequenced so the batch never ships hero-specific death handling this ticket then removes.
6. Catalog text from `world-rule-catalog-design` lands in the same commit as the code that makes it true.

## Related Tickets
- `TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER` / `...-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE`
  — the death batch; blocked from merging until this lands, and whose HERO hold this releases.
- `TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND` — the other merge blocker.
- `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK` — C1, the evidence that `REBIRTH` never worked.
- `TCK-20261001-CROSS-GENERATION-WOUND-SCAR-ACCUMULATION-BALANCE` — **close or re-scope**: its premise
  (wound/scar penalties accumulating across four generations) disappears if rebirth is retired.

## Related Docs
- `docs/world_rules/magic-supernatural/supernatural-transformation.md` — STR-02, the governing rule.
- `docs/world_rules/life-body/lifecycle.md` — LIFE-01, LIFE-02, LIFE-04.
- `docs/mechanics/02_combat_laws.md` — "The Hero's Journey (Generations)".
- `docs/world_rules/foundations/causality.md` — CAUSE-04.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK/`
- `staging_artifacts/TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE/` — the reverted
  restore and the withdrawn catalog edits R1/R3/R4.

## Related Code Areas
- `src/engine/combat_rewards.py:44-51`, `:106`
- `src/engine/combat.py:136`, `:170-187`
- `src/systems/lifecycle_systems/lifecycle.py` — the death classification branches
- `src/observability/event_extractor.py:66`, `:1283`; `src/engine/apply_plan.py:347`

## Assumptions / Open Questions

**Both open questions are now CLOSED (2026-10-01). Full reasoning in `staging_artifacts/`.**

- **Q1 CLOSED — fold `REBIRTH` and `PERMADEATH` into `KILL`; retire both outcome kinds; keep
  `is_permadeath`.** Decided by `world-rule-catalog-design`. LIFE-01's single final marker was never the
  `PERMADEATH` *outcome kind* — its evidence names the lifecycle field `LifecycleUpdate.is_permadeath_set`
  (and ID-05's `active=False, is_permadeath_set=True`). `PERMADEATH` is a combat classification *label*;
  `is_permadeath` is the lifecycle *fact*. Both labels simply drop out of `_DEFEATED_OUTCOME_KINDS`
  (`learning_outcome.py:33`), where `KILL` already sits, so the combat-learning layer sees an unchanged
  "defender lost" signal. **`is_permadeath` stays a separately tracked fact** even though it becomes
  `True` for every recorded death: it is the hook STR-02 requires, since a future *declared* resurrection
  process is the only thing permitted to produce a recorded death with `is_permadeath False`. Flagged so
  it is not "simplified away" later as redundant with `death_reason`.
- **Q2 CLOSED — remove `lifecycle.generation`.** The user delegated this decision explicitly
  ("ask `world-rule-catalog-design`"); the owner decided **removal**, not re-grounding and not deferral.
  Lineage depth is derivable from the birth record's parent links and a derived value cannot drift from
  it; with two parents "generation" is ill-defined until lineage design exists; and decisively,
  `event_extractor.py:1283-1297` emits `life_arc_incoherent` with `payload={"generation": ...}`, so
  recorded events already encode the rebirth meaning and re-grounding would **retroactively change the
  meaning of data already on disk**. The divergence entry must record that *lineage depth, if needed, is
  derived from the birth record's parent links when lineage design declares it (ID-06)*, so the deferred
  question has a written owner rather than a missing field.

### Findings that widen the blast radius beyond this ticket's first draft

- **There are TWO rebirth sites, and the live one is the second.** `combat.py:401-413`
  (`resolve_multi_attack`) as well as `:181-187` (`resolve_attack`). Its own comment records that
  `resolve_attack` is "the one real combat function this corpus's own AI never actually calls (0 real
  calls in 2000-tick runs)" — ported by `TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION`.
  **Retiring only `:183` would leave rebirth fully live on the only path that runs.** This is also a
  second confirmation of the premise: an earlier ticket found rebirth structurally unreachable and
  hardened its reachability without anyone asking whether the mechanic should exist.
- **`generation` is durable on a second object:** `CorpseState.generation`, written at
  `apply_plan.py:347`. It must be removed with the same legacy-key tolerance.
- **An observability detector depends on the rebirth meaning.** `life_arc_incoherent`
  (`event_extractor.py:1283-1297`) infers "late generation + level ≤ 1 + no skills = incoherent", which
  is only valid if `generation` counts lives that should have accumulated capability. Under any lineage
  reading it would false-positive on an ordinary young descendant. **Retire the detector**, don't
  re-point it, and sweep its registered/consumed literals so nothing is orphaned.
- **`generation_delta` must not be left as dead plumbing** — four lift sites plus `patches.py:82` whose
  guards reduce to `is_permadeath_set is not None` once it can never be non-zero.

### Still open
- **Architecture review has not been run on this plan.** It removes durable fields from the
  authoritative path, so run `architecture-reviewer` before implementation, as the death batch did.
- Whether `rebirth_eligible` disappears from `RewardClassification` entirely or remains always-`False` —
  plan prefers removal; an always-`False` field is the dead structure this ticket exists to delete.

## Implementation Notes
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._
