---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS
artifact_type: plan
tags: [simulation-quality, progression]
---

# Plan

> **Amended 2026-10-01 at implementation (rpg-feature-planning ruling D + A):** Step 3.3 (accumulator as a `stats_dirty` trigger) is WITHDRAWN and Step 4 became a dual-write (hardening keeps `max_hp_delta` and also increments the accumulator), because Step 0 measurement showed the full derivation drifts `move_cost`/`atk_range` (and the Step 2 zero-clamp is dropped: residuals are unclamped). See the ticket's Implementation Notes. `investigation.md` §7's value-neutrality table holds only for max_hp/atk/def/evasion.

**Target shape: one base owner, one grant accumulator, one derivation.** Read
`investigation.md` §2 and §7 before starting — §2 says why the obvious fix ("pass the profile value
as `base_hp`") is wrong, and §7 says why the whole change is value-neutral. Those two sections are
the plan's load-bearing facts.

## Step 0 — reproduce the premise and the trap, before changing anything

Write a throwaway probe (not committed) confirming, on a real `goblin_scout` from
`data/worlds/mechanic_scenario_combat_judgement_withdrawal/`:

- it spawns at `combat.max_hp == 35`;
- `recalculate_combat_stats(attributes, base_hp=100)` → `112` (today's bug);
- `recalculate_combat_stats(attributes, base_hp=35)` → **`47`**, not `35`.

**That third assertion is the trap.** If it does not reproduce, stop and report — the residual
arithmetic in Step 2 rests on it, and my reading of the spawn path may be wrong.

## Step 1 — typed durable base + grant accumulator

Add to the combat/stat durable state a typed, inspectable home for:

- `base_hp: int`, `base_atk: int`, `base_def: int`, `base_evasion: float` — the entity's **base
  terms**, written once at spawn, **immutable thereafter**. Provenance: the resolved stat profile.
- `permanent_max_hp_bonus: int` (and the equivalents for atk/def/evasion **only if** a writer for
  them exists today — do not invent fields for writers that don't exist; `hardening.py` writes
  `max_hp` only).

Constraints, all non-negotiable:

- **Not** `identity.properties` or any free-form dict — CLAUDE.md forbids durable meaning in
  free-form metadata.
- Typed model, stable location in entity state, defined lifecycle, inspection/debug visibility,
  tests — the full Durable State Rule.
- Must round-trip through `to_canonical_dict()` and whatever serialization its component already
  participates in. **Determinism must hold**: a new field in the canonical dict changes state hashes,
  so check `CanonicalStateHasher` and the replay/fingerprint tests deliberately rather than
  discovering it in CI. (`DEV-004`'s own 2026-08-30 update records a hasher crash from a
  non-serializable value — same class of hazard.)
- Choose the component deliberately and say why in the ticket. `CombatComponent` is the obvious home
  since every consumer is a combat stat; `IdentityComponent` is wrong (base stats are not identity).

## Step 2 — write the base at spawn, as the RESIDUAL

At the spawn path that currently assigns `max_hp=stats.max_hp`
(`src/entities/contract_builder.py`, plus whichever other construction paths set combat stats from a
profile — **check all three paths the file's own docstring names**: archetype-native, worldspec
role/faction expansion, and `V2EntityBuilder`):

    base_hp      := max(0, profile_max_hp - (vitality*2 + int(endurance*0.5)))
    base_atk     := max(0, profile_atk     - int(strength*0.5))
    base_def     := max(0, profile_def     - int(vitality*0.3))
    base_evasion := max(0.0, profile_evasion - (agility*0.001))

computed from **that entity's own spawn attributes**, not the profile's. Per `investigation.md` §3,
`attribute_bias` means two entities off one profile can spawn with different attributes, so this is
per-entity by necessity.

**Mirror the formula, don't re-type it.** The subtrahends must stay in lockstep with
`recalculate_combat_stats`. Either factor the attribute-contribution terms into one shared helper
that both the spawn residual and the derivation call, or — if that is too invasive — add a test that
fails if the two drift. A silent drift here reintroduces this exact bug in a harder-to-see form.
**Prefer the shared helper.**

**Clamp at zero** (above) and **assert the clamp** — a low-`max_hp` profile with a high-vitality bias
can go negative. If any live profile actually clamps, say so in the ticket: it means that entity's
spawn stat cannot be reproduced by the formula, which is a real finding, not a rounding detail.

## Step 3 — feed the derivation, and make the accumulator a trigger

1. `src/engine/apply.py:616-623` — pass the stored `base_hp`/`base_atk`/`base_def`/`base_evasion`
   into `SkillScalingService.get_effective_stats(...)`, and thread them through
   `rpg_depth.py:342-356` into `recalculate_combat_stats`.
2. Add the permanent-grant accumulator as a term of the derivation, so
   `max_hp = base_hp + attributes + gear + traits + permanent_max_hp_bonus`.
3. **Add the accumulator to the `stats_dirty` condition** (`apply.py:595-608`). Without this,
   hardening silently stops working once Step 4 lands — see `investigation.md` §7.

## Step 4 — hardening writes the accumulator, not `CombatUpdate.max_hp_delta`

`src/engine/pipeline_phases/hardening.py:84` currently merges `max_hp_delta=5`. It must instead
increment the durable `permanent_max_hp_bonus`, keeping its existing `trace` keys
(`NEAR_DEATH_HARDENING`, `NEAR_DEATH_PROJECTED_HP`, `NEAR_DEATH_THRESHOLD`) so the grant stays
traceable — that traceability is the CAUSE-05/HP-02 reason the accumulator exists at all.

Observable behaviour must not change: a near-death survivor still ends at `+5` max_hp on that tick.
Verify the event shape too — `src/observability/event_shapers.py:1829` reconstructs `max_hp` as
`prior_max_hp + combat_upd.max_hp_delta`, so it will need to account for the new path or it will
report a stale number.

**Leave `CombatUpdate.max_hp_delta` itself in place.** `core_actions.py:317` still writes it and is
out of scope (Step 6). Do not delete the field or the `patches.py:321` merge.

## Step 5 — parity ledger and docs

- **Add a NEW `docs/parity_ledger/progression.yaml` entry** for base-stat preservation — no existing
  id covers it. Re-read the ledger first: **PR #276 removed the rebirth/generation entries**, so do
  not reuse a remembered neighbouring id. If you rate it `P0`, it needs a passing `test_path`.
- `PROG-030` is P0 and its `test_path` must still pass — it is the dual-writer fix this change
  completes the spirit of. Run it explicitly.
- Update the Bible **01 §2** neighbourhood to state that the base terms are per-entity durable state
  sourced from the stat profile, and that the derivation is the sole writer of the four derived
  stats. Keep the formula itself unchanged — it is the law here, not the thing being changed.
- `docs/core/state.md` if the component gains a field that affects the immutability/partitioning
  description.
- If anything under `docs/` changes, run `make knowledge-index-update`.

## Step 6 — explicitly OUT of scope

- **`CoreActions.execute_allocate_ap`'s double-count. Do not touch it.** It is dormant by `DEV-004`
  and that entry already owns the fix (porting PROG-015/069 aptitude logic into the same function).
  `investigation.md` §8 has the full reasoning and the withdrawal of the earlier "it's live" claim.
- Deleting `CombatUpdate.max_hp_delta` or the `patches.py:321` merge.
- Flipping `ENABLE_PROGRESSION_EVOLUTION`.
- Re-authoring `stat_profiles.yaml` so profiles declare base terms instead of final stats. That is
  the wider, arguably cleaner alternative (one formula in content, used by both spawn and recalc) but
  it is a **content-semantics change** belonging to the mechanics/rule owners, and it would move
  spawn values unless every base were re-derived by hand. Recorded as a future option; **not this
  ticket.**
- Any SimQ re-baseline. Not implied: the fix is value-neutral at spawn and under hardening (§7), and
  the eroding path does not execute today.

## Acceptance-criteria map

| Ticket AC | Satisfied by |
|---|---|
| AC1 — a real decision + fix for whether recalc preserves spawned bases | Steps 1-4; decision recorded in the ticket's Implementation Notes and `investigation.md` §§2-7 |
| AC2 — differential test that a `stats_dirty` trigger no longer erodes species bases | `test_plan.md` T3, T4 |
| AC3 — real corpus measurement recorded | Already recorded (2026-09-30: zero firings, 3 worlds, positive control). `test_plan.md` T7 re-measures **after** the fix, since Step 3 makes the path reachable for the first time — that is a new number and the one that matters now. |

## Scope guards

- Do not "simplify away" `is_permadeath` if you pass near it — it is the STR-02 hook (see the death
  batch's decisions).
- Do not edit a test or a validator to make a gate pass. A blocking result is information to report.
- If Step 0's third assertion fails, or if the residual cannot reproduce a live profile's spawn stat,
  **stop and report** rather than adjusting the arithmetic until it fits.
