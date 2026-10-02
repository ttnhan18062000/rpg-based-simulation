---
status: active
layer: engine
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine]
---

# Investigation — TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE

Observed engine commit: `71c4aa321` (`origin/main` @ #273, 2026-10-01).

**Shared ground is in the batch sibling's investigation**
(`staging_artifacts/TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER/investigation.md`):
the exact `apply.py:93-110` site, the three facts about its guards, and the state of
`resolve_lifecycle`. Not restated here. This file covers only what is specific to the non-lethal
outcomes.

## The outcome lattice, read exactly

`src/engine/combat.py:170-187`:

```python
if new_hp <= 0:
    outcome = "KILL" if is_lethal else "DEFEAT"
    alive = False
    classification = CombatRewardClassificationService.classify_defeated_target(attacker, defender, state)
    ...
    if classification.rebirth_eligible:
        if defender.lifecycle.generation < 4:
            gen_delta = 1
            outcome = "REBIRTH"
        else:
            perma_set = True
            outcome = "PERMADEATH"
```

with `combat.py:136`: `is_lethal = is_lethal and (defender.identity.role != EntityRole.HERO)`.

### A HERO cannot reach a terminal `DEFEAT` — the ticket's opening premise was false

`rebirth_eligible` is `True` for a HERO on **both** classification paths, verified in
`src/engine/combat_rewards.py`:

- Relation-projection path (`:106`): `rebirth_eligible=(defender_role == EntityRole.HERO)`.
- Legacy-role fallback (`:116-117` → `classify()` → `_CLASSIFICATIONS`): the `EntityRole.HERO` entry
  carries `rebirth_eligible=True` (`:44-51`).

So for a HERO the `if classification.rebirth_eligible:` branch is always taken, and `outcome` is always
overwritten from `"DEFEAT"` to either `"REBIRTH"` or `"PERMADEATH"`. The `"DEFEAT"` assignment at `:171`
is transient for that role.

**Therefore the populations are:**

| Outcome | Reached by | `alive` | Final? |
|---|---|---|---|
| `KILL` | non-HERO, `is_lethal=True` | `False` | yes, recorded `COMBAT` |
| `DEFEAT` (terminal) | **non-HERO, caller-passed `is_lethal=False`** (opportunity attacks) | `False` | **unrecorded — defect** |
| `REBIRTH` | HERO, `generation < 4` | `False` ← **defect** | no, but behaves as final |
| `PERMADEATH` | HERO, `generation >= 4` | `False` | yes, recorded `COMBAT` |

This matches the corpus evidence from `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK`
(`frontier_marches`, seed 42, 120 ticks): 4 `DEFEAT` (ticks 20/68/113/115) against 1 `REBIRTH` (tick 88)
— a ratio consistent with opportunity attacks on ordinary entities, not with hero defeats.

**Side effect for the rule owner:** this resolves open question 1 in
`docs/world_rules/life-body/lifecycle.md` — `DEFEAT` is a live, reachable outcome (non-HERO opportunity
attacks), not a vestigial label. That text is owned by `world-rule-catalog-design` and has been handed
to it; this ticket does not edit it (AC5).

### `REBIRTH` restores nothing

`gen_delta = 1` is the entire effect. Verified by exhaustive search: every `alive = True` /
`alive=True` in `src/` is either object construction (`worldbuilding/compiler.py:672`,
`worldassembly/entity_spawner.py:70,151`, `perf/scenarios.py` ×6), a local initializer before the
outcome branch (`engine/combat.py:165,271,381`), a provider default
(`world/providers/requirements.py:175`), or a test harness (`observability/readiness/harness.py:100`).
**No runtime writer ever restores `alive` on an existing entity.** Nor is `hp` restored anywhere on the
rebirth path.

So a reborn hero is a 0-HP, `alive=False` entity with `generation` incremented, which the age path then
deactivates on the next life-due tick. `docs/mechanics/02_combat_laws.md:65` says a Gen 1–3 hero "are
reborn (Generation increments)". The generation half is implemented; the rebirth half is not. This is a
**code-vs-law divergence**, not a doc gap — the law is clear that the hero continues.

## What the law and the rules do and do not settle

| Question | Settled? | By |
|---|---|---|
| Does a defeat necessarily mean death? | **No, it does not** | LIFE-02 (ACCEPT) |
| Is zero HP a sufficient cause of any single outcome? | **No** — it triggers classification | BODY-02, scenario LB-S03 |
| Is a Gen 1–3 hero at 0 HP reborn? | **Yes** | `02_combat_laws.md:65` |
| What HP does a reborn hero have? | **Unspecified** | — → user decision 1 |
| What does a terminal `DEFEAT` leave behind? | **Unspecified** | — → user decision 2 |
| Is `is_permadeath_set` the only final marker? | **Yes** | LIFE-01, scenario LB-S02 |

The two unspecified rows are the two decisions the user closed on 2026-10-01 (recorded in the ticket's
Request Summary): rebirth restores `hp = max_hp` and `alive = True`; a terminal `DEFEAT` becomes a
recorded death with a distinct `death_reason`.

Decision 2 is worth defending explicitly against a misreading of LIFE-02. LIFE-02 says a defeat "does
not, **by itself**, entail permanent lifecycle termination" and that "a real classification process
**may** route a defeat toward continued existence". It requires that a genuine classification decide the
outcome — not that every defeat be survivable. Routing terminal `DEFEAT` to a recorded death is a real
classification producing a recorded result, and it is consistent with the rule. What the rule forbids is
precisely what the code does today: an *unclassified, unrecorded* slide into permanent deactivation.

## Architectural constraints this fix must respect

- `resolve_lifecycle` reads `ent_upd.combat.outcome_kind`. The `DEFEAT` discriminant must be added
  **there**, reading the persisted discriminant — never re-deriving it from HP, role or bio state. This
  is the same discipline the sibling ticket applies to the passive cause.
- The `REBIRTH` restore is a durable mutation and must travel as a typed update applied on the
  authoritative path. It must not be an in-place edit inside `CombatResolutionSystem`, which is decision
  logic and may read state but not authoritatively mutate it.
- `"HAZARD"` is a live discriminant that `_NON_COMBAT_OUTCOME_KINDS` depends on
  (`TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND` AC2). Adding `DEFEAT` to the
  recorded-death set must not disturb that set's existing members.
- `event_extractor.py` stays exact-match on `COMBAT` (sibling's AC3) — a new reason must not be made to
  look like `COMBAT` to satisfy an extractor.

## Open questions carried to Plan

1. The exact `death_reason` string for a terminal `DEFEAT` (`"DEFEAT"` is the obvious candidate and keeps
   the reason aligned with the `outcome_kind` that produced it).
2. Whether the `REBIRTH` HP restore rides on `CombatUpdate` or a lifecycle-side typed update — a
   placement question for the architecture review.
3. Whether rebirth clears accumulated `WoundState` / `ScarState`. **Not assumed.** BODY-03 holds that HP
   loss and injury are related but not identical facts, so restoring HP does not self-evidently clear
   wounds; a hero reborn at `max_hp` while carrying the full penalty stack of its previous life is a
   plausible intent, and so is the opposite. Flagged for the review rather than decided here, per the
   Uncertainty Rule.
