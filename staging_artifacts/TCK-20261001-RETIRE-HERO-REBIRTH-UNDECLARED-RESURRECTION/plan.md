---
status: active
layer: combat
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION
phase: open
date: 2026-10-01
tags: [lifecycle, combat, progression, architecture]
---

# Plan — TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION

Read `investigation.md` first — it maps a blast radius wider than the ticket's first draft, including a
**second rebirth site** the ticket did not name.

**Both open questions are now answered**, so this plan is fully unblocked:
- **Q1** (rule owner): fold `REBIRTH` and `PERMADEATH` into `KILL`, retire both outcome kinds, **keep
  `is_permadeath`**.
- **Q2** (rule owner, on the user's explicit delegation): **remove `lifecycle.generation`.** Do not
  re-ground it, do not defer it.

**Architecture review:** not yet run. This removes a durable field (`LifecycleComponent.generation`,
`CorpseState.generation`) and an update field (`generation_delta`) from the authoritative path, so run
`architecture-reviewer` on this plan before implementation, as the death batch did. The field *removal*
and legacy-key tolerance are the parts most worth a second opinion.

## Why `generation` is removed rather than re-grounded (record this, it will be re-litigated)

- Its only meaning is the rebirth count, which is being retired.
- Lineage depth is **derivable** from the birth record's `parent_a_entity_id`/`parent_b_entity_id` chain;
  a stored counter would be a second hand-maintained copy of a derivable fact, and a derived value
  cannot drift from the birth record while a stored one can.
- With two parents, "generation" is **ill-defined** (max? min? per-line?) until lineage design exists.
  Inventing an answer now would be a new undeclared durable meaning — the exact pattern that produced
  rebirth.
- **Decisive:** `event_extractor.py:1283-1297` emits `life_arc_incoherent` with
  `payload={"generation": ...}`. Recorded events already carry `generation` as a *rebirth count*, so
  re-grounding would retroactively change the meaning of data already on disk. Removal does not.
- Keeping it deferred would leave a field whose only meaning has been retired, inviting someone to give
  it a new meaning silently (ID-06).

## Steps

### S1 — Retire BOTH rebirth sites
`combat.py:181-187` (`resolve_attack`) **and** `combat.py:401-413` (`resolve_multi_attack`). The second
is the one that actually fires — `resolve_attack` has "0 real calls in 2000-tick runs" per its own
comment. Retiring only the first leaves rebirth fully live.

Remove `rebirth_eligible` from the classification: `combat_rewards.py:44-51`
(`_CLASSIFICATIONS[EntityRole.HERO]`) and `:106` (the relation-projection path). Decide whether the field
disappears from `RewardClassification` entirely or remains always-`False` — **prefer removal**; an
always-`False` field is dead structure of the kind this ticket exists to delete.

### S2 — Fold `REBIRTH` and `PERMADEATH` into `KILL` (Q1)
No `REBIRTH` or `PERMADEATH` `outcome_kind` is produced. A lethal hit records an ordinary `COMBAT` death
with `death_tick`, `is_permadeath=True`, and succession/heirs/heirlooms firing as for any subject.

- **CORRECTED 2026-10-01 by `rpg-implementer`, against its in-progress diff: shrink ONE constant, not
  two lists.** `TERMINAL_COMBAT_OUTCOME_KINDS` now lives in `src/core/combat_constants.py` and
  `_DEFEATED_OUTCOME_KINDS` is **derived** from it. It still contains `"REBIRTH"` and `"PERMADEATH"`.
  Remove them from that single constant and the derived list follows. Editing
  `learning_outcome.py:33` directly, as this plan originally said, would now be editing a derived value.
  `KILL` remains, so the combat-learning layer sees an unchanged "defender lost" signal.
- `resolve_lifecycle`'s `("KILL", "PERMADEATH")` tuple reduces to `("KILL",)`. **This edit lands on top
  of the death batch's diff**, which has already added `DEFEAT`, `HAZARD` and passive-cause branches
  through one shared idempotency guard while leaving that tuple intact. Do not collide with it.
- **`is_permadeath` stays a separately tracked fact**, even though it becomes `True` for every recorded
  death and looks redundant with "has a `death_reason`". It is the hook STR-02 needs: a future
  *declared* resurrection process is the only thing permitted to produce a recorded death with
  `is_permadeath False`. **Say this in the code comment** so it is not simplified away later.

### S3 — `combat.py:136` goes with this ticket
`is_lethal = is_lethal and (defender.identity.role != EntityRole.HERO)`. Leaving it would make a lethal
hit on a former hero resolve as terminal `DEFEAT` rather than `KILL`. Remove the role clause so
`is_lethal` means only what the caller passed.

**Scope boundary:** this is the *only* `EntityRole.HERO` coupling in scope. `HERO_KILL` rewards, the
hero-guild routing content, `hero_adventurers`, `HERO_*` event names are the separate de-hero epic and
need its inventory first.

### S4 — Remove `generation`, with legacy-key tolerance (Q2)
Per-consumer, verified by the rule owner on `origin/main` — **re-grep at implementation time**:

1. `state.py:169`/`:191` — `LifecycleComponent.generation` field and its `to_dict`; `builder.py:586`/
   `:606`. Remove. **`from_dict` must tolerate and ignore a legacy `"generation"` key** so old saves,
   replays and fixtures still load. Pin a test that loads a legacy dict containing the key.
2. `LifecycleUpdate.generation_delta` and `patches.py:82`. Remove. Note the four lift sites whose guards
   reference it (`movement.py:250-252`, `domain/combat_actions.py:111-113`,
   `domain/skill_actions.py:125-127`, `domain/aoe_actions.py:75-77`) reduce to
   `is_permadeath_set is not None`. **Do not leave `generation_delta` as dead plumbing.**
3. The rebirth branches — already gone via S1.
4. `CorpseState.generation` (`state.py:1224`/`:1236`), written at `apply_plan.py:347`. Remove, with the
   **same legacy-key tolerance** in `CorpseState` deserialization. A corpse's lineage, if ever needed,
   comes from `original_entity_id` plus the birth record.
5. `event_extractor.py:66` `_LATE_GENERATION_THRESHOLD` and the `life_arc_incoherent` detector
   (`:1283-1297`): **retire the whole detector**, do not re-point it. Its premise is "a completed Hero's
   Journey rebirth already occurred", which ceases to exist; under any lineage reading it would emit a
   false positive for an ordinary young descendant (a 4th-generation newborn is legitimately level 1
   with no skills). **Before removing, grep for registered/consumed `life_arc_incoherent` literals** —
   event-type registry, SimQ scorers, tests, docs, parity entries — and retire them in the same change
   so nothing is orphaned. Previously recorded events keep their original meaning (a rebirth count as of
   the run that emitted them); dated evidence is not rewritten.
6. `src/certification/scenarios.py` `.lifecycle(generation=...)` at `:119, :131, :170, :298, :322, :365,
   :377` — drop the argument. **`:170` ("One away from permadeath") tests rebirth itself**: retire or
   rewrite that scenario under this ticket, do not merely strip its argument.

**Explicitly out of scope — same word, unrelated:** `ApplyPath.apply_generation`, and the lab
`generation` directory/status in `audit.py`/`session.py`.

### S5 — Docs, law, parity
- Rewrite `docs/mechanics/02_combat_laws.md` §"The Hero's Journey (Generations)" — remove the
  generations-of-rebirth law.
- `docs/guidelines/intentional_divergences.md` entry, rationale class **Intentional Gameplay Change**,
  citing STR-02 / ID-02 / CAUSE-04 and the reproduction continuity model, with a verification path. It
  must include the owner's line verbatim in substance: *lineage depth, if needed, is derived from the
  birth record's parent links when lineage design declares it (ID-06)* — so the deferred question has a
  written owner rather than a missing field.
- Parity: `combat_movement.yaml::COMB-297` and the outcome-lattice entry; `progression.yaml`'s
  rebirth/generation entries. Re-check `progression.yaml::PROG-030` is unaffected (it is about the age
  path, but the death batch already touched it).
- Catalog text **C1–C5** in `catalog_edits.md` — lands in **this** ticket's commit, written against the
  state after both the death batch and this ticket.

## Starting state — this ticket lands ON TOP of the death batch + hazard diff

Reported by `rpg-implementer` 2026-10-01 from its in-progress worktree (branch
`entity-death-cause-at-writer`, nothing committed or pushed). Implement against this, not against
`71c4aa321`:

- **`combat.py` is untouched** by the death batch and the hazard work — the rebirth restore was reverted,
  so S1/S2/S3 start from pre-batch `combat.py`.
- **`lifecycle.py` has gained** `DEFEAT`, `HAZARD` and passive-cause branches through **one shared
  idempotency guard**. The `("KILL", "PERMADEATH")` tuple is still intact, so S2 edits it on top of that
  diff.
- **`TERMINAL_COMBAT_OUTCOME_KINDS` is now in `src/core/combat_constants.py`** with
  `_DEFEATED_OUTCOME_KINDS` derived from it (see S2 — shrink the one constant).
- **`patches.py` / `updates.py` are clean** — the `hp_set` additions were reverted with the restore, so
  S4.2's `generation_delta` removal starts from unmodified files.
- **Two test files reference `REBIRTH` and `generation`** and need coordinated R-series edits:
  `tests/mechanic_scenarios/test_passive_death_cause_and_rebirth_defeat_lifecycle.py` and the boundary
  test.
- The implementer's new tests currently default to role HERO; it will switch them to explicit roles once
  retirement lands, at which point the HERO hold is moot.

## Scope guards

- **Do not** touch the broader `EntityRole.HERO` privileges — separate epic, inventory first.
- **Do not** design resurrection. The user chose retirement; if it is ever wanted it needs its own epic
  built to STR-02.
- **Do not** remove `is_permadeath`.
- **Do not** rewrite the roadmap §3.1 addendum's "a HERO is always rebirth-eligible and resolves to
  `REBIRTH`" — a dated record of the C1 run at `e9db40f0a`, true then. Dated evidence is not rewritten.
- **Do not** re-point `life_arc_incoherent` at a new signal; retire it.
- Coordinate `resolve_lifecycle:202` with the death batch's `DEFEAT` addition.

## Acceptance-criteria map

| AC | Steps | Verified by |
|---|---|---|
| 1 — no `rebirth_eligible`, no `REBIRTH` outcome; lethal hit records `COMBAT` + lineage | S1, S2, S3 | R1, R2 |
| 2 — the `REBIRTH` zombie class is closed | S1, S2 | R3 |
| 3 — `generation` removed; every consumer agrees; legacy keys tolerated | S4 | R4, R5, R6 |
| 4 — Bible rewritten, divergence entry, parity updated | S5 | S5 diff |
| 5 — death batch's HERO hold released | S1, S2 | R7 |
| 6 — catalog text lands in this commit | S5 | `catalog_edits.md` |
