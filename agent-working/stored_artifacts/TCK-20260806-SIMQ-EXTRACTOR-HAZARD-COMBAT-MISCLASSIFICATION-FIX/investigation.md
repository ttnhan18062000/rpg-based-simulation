---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX
artifact_type: investigation
tags: [observability, combat, simulation-quality]
---

# investigation.md — TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX

## Summary

**A second, more consequential bug was found during this Investigate pass, distinct from and
compounding the originally-scoped `outcome_kind` filter gap.** Both are confirmed with direct
source evidence, not inferred.

## Bug 1 (already scoped): missing `outcome_kind` filter

`event_extractor.py` lines 136-151 (combat-damage detection) fire on any `hp_diff < 0` with no
check on `CombatUpdate.outcome_kind`. Hazard drain (`world_dynamics.py:39`, tagged
`outcome_kind="HAZARD"`) gets misclassified as `combat_damage`/`combat_initiated`/
`near_death_survival`.

## Bug 2 (newly found, this session, this Investigate pass): wrong attribute name — `combat_upd` does not exist on `EntityUpdate`

Grepped every use of `combat_upd` vs. `combat` across `event_extractor.py` and `src/core/updates.py`:

```
event_extractor.py:103   getattr(e_upd, "combat_upd", None)   — has_attacker check (despawn branch)
event_extractor.py:144   getattr(e_upd, "combat_upd", None)   — CombatDamageEvent.attacker_id
event_extractor.py:145   e_upd.combat_upd.attacker_id
event_extractor.py:157   getattr(e_upd, "combat_upd", None)   — CombatKillEvent.killer_id
event_extractor.py:158   e_upd.combat_upd.attacker_id
event_extractor.py:184   getattr(e_upd, "combat_upd", None)   — combat_initiated payload attacker_id
event_extractor.py:185   e_upd.combat_upd.attacker_id
event_extractor.py:395   getattr(e_upd_ext, "combat", None)   — CORRECT, this one reads "combat"
```

`e_upd` at every one of the first 4 call sites is `update.entity_updates.get(eid)`, typed
`Dict[int, EntityUpdate]` (`src/core/updates.py:873`). `EntityUpdate`'s real field is `combat:
Optional[CombatUpdate] = None` (`src/core/updates.py`, confirmed directly) — there is no
`combat_upd` attribute anywhere on this class, and grep across `src/core/updates.py` in full found
no alias/property either. (`combat_upd` *is* a real field name — but on a completely different
type, `CombatIntent`/similar in `src/core/conservation.py`, unrelated to `EntityUpdate`.)

Because all 4 sites use `getattr(e_upd, "combat_upd", None)` **with a default**, this doesn't raise
`AttributeError` — it silently returns `None` every single time. Concrete, confirmed consequences:

1. `CombatDamageEvent.attacker_id` — **always `None`**, at every real combat hit, not just hazard
   hits. This exactly matches this session's earlier raw-event observation ("every observed hit had
   `attacker_id: None`") — previously attributed to "the mutating system not populating the field,"
   which was the wrong explanation. The field *is* populated correctly by `combat.py`
   (`CombatUpdate.attacker_id`); the extractor just never successfully reads it.
2. `CombatKillEvent.killer_id` — always `None`, same root cause.
3. `combat_initiated`'s payload `attacker_id` — always `None`, same root cause.
4. **`has_attacker` (line 103) is always `False`.** This gates whether a despawn emits
   `demographic_mortality` (lifecycle category) — per the surrounding code, `demographic_mortality`
   is meant to fire only when an entity despawns *without* a combat attacker (natural death/removal).
   With `has_attacker` always `False`, **every despawn — including real combat kills — also emits
   `demographic_mortality`**, alongside the correct `CombatKillEvent`. This is a real WORLD/lifecycle
   pillar signal-quality bug, not just a combat-payload cosmetic issue, and was not part of this
   ticket's original scope — flagging it here rather than silently expanding into it without
   disclosure.

## Interaction between the two bugs

Fixing Bug 1 alone (adding an `outcome_kind` check) without fixing Bug 2 would still leave every
combat event's `attacker_id`/`killer_id` permanently `None` — the causal-attribution problem this
session's broader investigation was originally trying to solve would remain unsolved even after the
misclassification fix. Both must be fixed together for this ticket to actually deliver a
trustworthy combat event stream.

## Bug 3 candidate — caught before it shipped: `outcome_kind` alone is not a safe discriminant

Before writing the fix, grepped every source in `src/` that sets `hp_delta` on an `EntityUpdate`/
`CombatUpdate` (not just the two already-discussed sources), to check whether an
`outcome_kind`-based allow-list (e.g. `{"SURVIVE","DEFEAT","KILL","SUCCESS"}`) would actually be
safe:

```
src/engine/combat.py          — 5 real combat sites, ALL set attacker_id, outcome_kind ∈ {SURVIVE,DEFEAT,KILL,SUCCESS,REJECTED}
src/engine/world_dynamics.py  — hazard drain, outcome_kind="HAZARD", never sets attacker_id
src/systems/lifecycle_systems/biological.py:40 — CombatUpdate(hp_delta=hp_delta) for starvation/
  exhaustion damage, NO outcome_kind passed → defaults to CombatUpdate's dataclass default,
  "SURVIVE" — NEVER sets attacker_id
src/engine/town_resolution.py, src/systems/economy_systems/town_service.py — positive hp_delta
  only (healing), irrelevant to the hp_diff<0 branch
src/engine/evolution.py:137  — adds a heal bonus on top of an existing hp_delta via replace(),
  inherits whatever attacker_id was already set, not a new discriminant source
src/engine/sabotage.py:67    — build_upd.hp_delta, BuildingState HP, unrelated to entity combat.hp
```

**A plain `outcome_kind` allow-list including `"SURVIVE"` would have misclassified biological
starvation/exhaustion damage as combat too** — `CombatUpdate`'s dataclass default happens to be
`"SURVIVE"`, and `biological.py` relies on that default rather than setting an explicit tag,
exactly the same class of problem hazard drain has, just via a different mechanism (an unset field
colliding with a real combat value, rather than an unchecked field being ignored).

**Correct discriminant: `attacker_id is not None`, not `outcome_kind` alone.** Every one of
combat.py's 5 real damage-dealing call sites sets `attacker_id=attacker.id` (confirmed directly).
Neither `world_dynamics.py`'s hazard drain nor `biological.py`'s starvation/exhaustion damage ever
sets it (both default to `None`). This is a more semantically direct check too — "was this entity
attacked by another entity" is precisely what "is this combat" means, and it doesn't depend on the
2 known non-combat sources being the only ones that will ever exist; a 3rd future non-combat
HP-reducing system that also fails to set `attacker_id` (the honest default) would still be
correctly excluded, whereas an outcome_kind allow-list has no such protection against new sources
relying on the same default.

**Final fix design**: combat classification requires `combat_upd is not None and
combat_upd.attacker_id is not None and combat_upd.outcome_kind not in ("HAZARD", "REJECTED")` —
`attacker_id` as the primary, semantically-correct discriminant; the `outcome_kind` exclusions as
defense-in-depth (a future combat-adjacent system could theoretically set `attacker_id` while still
representing a non-combat-resolution outcome; belt-and-suspenders, not load-bearing given the
`attacker_id` check already covers the two known real cases).

## Revised Scope (supersedes the ticket's original single-bug framing)

1. Fix all 4 `combat_upd` → `combat` attribute references (lines 103, 144-145, 157-158, 184-185).
2. Add a combat-classification guard to the combat-damage/combat-initiated/near-death-survival
   branches (lines 136-203): `combat_upd is not None and combat_upd.attacker_id is not None and
   combat_upd.outcome_kind not in ("HAZARD", "REJECTED")` — `attacker_id` as the primary,
   semantically-correct discriminant (per the Bug 3 analysis above), `outcome_kind` exclusions as
   defense-in-depth.
3. Fix the `demographic_mortality` double-fire: since Bug 2's fix makes `has_attacker` behave
   correctly, this should self-resolve as a side effect — verify via test that a real combat kill no
   longer also emits `demographic_mortality`.
4. Add regression tests specifically asserting `attacker_id`/`killer_id` are correctly populated
   (not just present), not only that the right event *type* fires. Add a dedicated test for the
   biological-damage-not-misclassified-as-combat case (Bug 3), not just the hazard case.
5. **Fix the existing test-fixture bug**: 3 tests in `tests/unit/observability/
   test_event_extractor_simq.py` mock `MagicMock(combat_upd=...)` — matching the *buggy* attribute
   name, not the real `EntityUpdate.combat` field. This is why these tests never caught Bug 2. Fix
   the mocks to use the real field name so they actually exercise the fixed code path, not a
   fictional one.
