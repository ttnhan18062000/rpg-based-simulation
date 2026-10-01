---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS
artifact_type: investigation
tags: [simulation-quality, progression]
---

# Investigation

Every code fact here was read at HEAD on 2026-10-01. Where an earlier note on this ticket said
something different, the correction is called out explicitly rather than silently replaced.

## 1. The defect, confirmed

`src/engine/apply.py:616-623` calls `SkillScalingService.get_effective_stats(...)` with **no**
`base_hp`/`base_atk`/`base_def`/`base_evasion`. `src/engine/rpg_depth.py:349-352` defaults them to
`base_hp=100, base_atk=10, base_def=5, base_evasion=0.05`. So any `stats_dirty` recalculation
rebuilds combat stats from a generic baseline. A `goblin_scout` spawned at `max_hp=35` recalculates
to `112` (`100 + 5*2 + int(5*0.5)`, i.e. `vitality=endurance=5`).

## 2. THE DECISIVE FINDING — the two writers disagree on *semantics*, not just on the base value

This is the finding that determines the whole implementation shape, and it was **not** in the
ticket before this investigation.

**`stat_profiles.yaml`'s `max_hp` is a FINAL spawned stat, not a base term.** Spawn assigns it
directly: `src/entities/contract_builder.py` sets `max_hp=stats.max_hp` from the resolved profile,
with no attribute contribution added. `goblin_scout_base` declares `hp: 35, max_hp: 35` and the
entity spawns at exactly `35`.

But `recalculate_combat_stats` (`src/progression/leveling.py:99`) treats its `base_hp` as a **term
to which attributes are then added**: `max_hp = base_hp + vitality*2 + int(endurance*0.5)`.

**Therefore "pass the profile value through as `base_hp`" — the ticket's original Scope step 2, and
the obvious reading of the fix — is WRONG and would not restore the spawn value.** For
`goblin_scout` it yields `35 + 10 + 2 = 47`, not `35`. It replaces a 35→112 inflation with a 35→47
inflation. Smaller, still wrong, and much harder to notice.

The two paths embody incompatible models of what a profile number means. **That is the real defect**,
and the base-value substitution is its symptom.

## 3. Consequence: the stored base must be the residual, and it must be per-entity

To make the single derivation reproduce the spawned value exactly, the stored base term must be

    base_hp := profile_max_hp - (vitality*2 + int(endurance*0.5))   # at spawn attributes

For `goblin_scout`: `35 - 12 = 23`, and `23 + 12 = 35` ✓.

**It must be per-entity, not per-profile**, because spawn attributes are not uniform across entities
sharing a profile — `stat_profiles.yaml` carries an `attribute_bias` block (`goblin_scout_base` has
none; `wolf_predator_base` has `agility: high, instinct: very_high, perception: high`), so two
entities off the same profile can spawn with different attributes and therefore different residuals.
This is precisely why it is **durable per-entity state** under the Durable State Rule, and not a
content lookup — which independently re-confirms that Option A (resolve the profile at recalc time)
could never have been correct even if a catalog had been reachable.

**Clamp at `>= 0`.** A profile with a low `max_hp` and a high-vitality bias can produce a negative
residual. Must be clamped and asserted in tests.

## 4. Why Option A was impossible anyway

1. **No entity→profile link.** `EntityState` (`src/core/state.py:879`) carries `kind: str` and no
   `archetype_id`/`species_id`/`stat_profile_id`; nor does `IdentityComponent`.
   `grep archetype_id src/core/` returns one unrelated hit (`registries.py:517`). The resolved
   contract computes `archetype_id` and `species_id` (`contract_builder.py:28-29`) and `EntityState`
   **discards both**. The base identity is resolved at spawn and thrown away.
   `entity.kind` is not a substitute: on the archetype-native path it is `arch.species_id`
   (`contract_builder.py:31`, whose own comment adds "may be overridden by spawn context") and a
   species id is not a stat-profile id; on the legacy builder path it defaults to the literal
   `"hero"` (`src/core/builder.py:95`) and is freely settable (`:117`). **The ticket's
   explicitly-unconfirmed caveat is hereby closed: `kind` does not resolve to a profile id.**
2. **No catalog in the apply path.** `ApplyPath.apply_generation` (`apply.py:189-198`) is a static
   method taking `prior_state`/`update`/`next_tick`/`next_world_time`/`cadence`/`audit_mode`/
   `audit_dirty_set`/`passive` — no catalog or repository parameter, and the file contains no
   `catalog`/`repo` reference at all.

## 5. Why Option C (retire the recalc) was impossible

`world-rule-catalog-design` supplied the governing rules and the deciding test:

- **OWN-01** (`docs/world_rules/foundations/state-ownership.md:23`, ACCEPT) — a durable concept has
  one canonical owner that must not independently establish conflicting truth. Two writers producing
  35 vs 112 for the same `max_hp` violate it directly. **OWN-03** adds that stored
  `max_hp`/`atk`/`def` is a materialised derivation, so two derivations cannot both be
  authoritative. **The dual authority, not the wrong default, is the rule-level defect.**
- OWN-01 requires *one* owner without saying which; the deciding question is **coverage**. The
  additive writers emit nothing for equipment, trait, learned-skill, breakthrough or class changes —
  all `stats_dirty` triggers (`apply.py:595-608`) with real terms in the derivation
  (`leveling.py:110-150`). Retiring the recalc would leave derived stats stale after exactly those
  changes: an OWN-03 violation in the other direction.

So the full derivation is the writer that must survive.

## 6. The permanent-grant writer, and why grants must not fold into the base

`recalculate_combat_stats` computes `max_hp` **absolutely** and has **no term for an accumulated
permanent grant**. But a declared-permanent grant exists:
`src/engine/pipeline_phases/hardening.py:84` writes `max_hp_delta=5`, described in that phase's own
LAW block as "a small **permanent** max-HP increase" for surviving a near-death hit, merged
absolutely at `patches.py:321` (`max_hp = new_combat.max_hp + u_com.max_hp_delta`).

**So a correct base alone still erases every accumulated hardening grant on the first recalc.**

**Grants must go in their own typed accumulator, NOT folded into the base** — the rule owner's
correction, accepted. An earlier draft of this resolution folded them in, on the theory that the base
had to be the single owner. That misreads OWN-01: it governs who writes the **derived** stats, and
one derivation writer satisfies it however many typed inputs it reads — a typed grant input is an
*owned input*, not a second owner of `max_hp`. Folding destroys provenance: after a few grants the
base could no longer say how much was species-declared and how much was earned, which **CAUSE-05**
(causal history traceable within its declared reach) and **HP-02** (provenance needs a real causal
ancestor) both cut against, and which would defeat the de-hero inventory's "re-ground capability on
real state".

## 7. The activation hazard, and why this fix is value-neutral

If hardening stops writing `CombatUpdate.max_hp_delta` and writes the accumulator instead, and the
accumulator is read only by the derivation, then **hardening stops having any effect** — because
`stats_dirty` never fires today (measured: zero firings across three worlds, 600/400/400 ticks,
seed 42, 40 deaths, with a passing positive control).

So `stats_dirty` **must gain the accumulator as a trigger**. That makes the recalculation fire in
corpus play for the first time.

**This is safe precisely because of the residual.** With `base = profile_max_hp − attribute
contribution at spawn`, the derivation reproduces today's values exactly:

| state | today (additive) | after fix (derivation) |
|---|---|---|
| `goblin_scout` at spawn | 35 | `23 + 12 = 35` ✓ |
| after one hardening grant | 40 | `23 + 12 + 5 = 40` ✓ |
| after vitality 5→7 | 40 (attributes ignored) | `23 + 16 + 5 = 44` (attributes now matter) |

**Activation is value-neutral at spawn and under hardening, and only changes behaviour where today's
behaviour is the bug** (attribute changes failing to propagate). That equivalence is the fix's
central safety property and must be asserted directly, not assumed.

## 8. Out of scope, with the reason: the `execute_allocate_ap` double-count

`CoreActions.execute_allocate_ap` (`core_actions.py:311-317`) sets the attribute delta **and** a
hand-written combat delta for the same allocated point: `vitality_delta=amount` with
`max_hp_delta=amount*10` against §2's `vitality*2`, and `strength_delta=amount` with
`atk_delta=amount*2` against §2's `strength*0.5` — a double-count at 5× and 4× divergent weights.

**It is dormant by a recorded decision and is deliberately NOT in this ticket's scope.** An earlier
note on this ticket claimed it was "wired" and that the re-raise condition was met; **that claim is
withdrawn** — it name-matched two distinct `ALLOCATE_AP` paths:

- `ConversionKind.ALLOCATE_AP` resolves at `src/domains/progression/resolver.py:82-91` to
  `IdentityUpdate(unspent_ap_delta=-1)`, a decrement-only **zero-attribute-gain** no-op returned
  directly as an `EntityUpdate` (`phase.py:73`), never through `ActionRouter`. It cannot set
  `update.attributes` and so cannot trigger `stats_dirty`.
- No `src/` code constructs the `{"action": "ALLOCATE_AP", …}` router payload; the only constructors
  are two cases in `tests/unit/quest/test_progression_regression.py`.

**`DEV-004`** (`docs/guidelines/intentional_divergences.md:2094`) decided "keep `execute_allocate_ap`
wired but dormant", ratifying `SUB-376` (`substrate.yaml`) and `ENTITY-008`
(`docs/event_ledger/entity.yaml`). Its 2026-08-30 update records a 4-leg corpus trial finding it
unreachable for two independent reasons, both re-verified at HEAD: `ENABLE_PROGRESSION_EVOLUTION` is
`FeatureMode.OFF` (`feature_flags.py:48`, gating `pipeline.py:387`), and `RewardLedgerService` has
zero callers so the only trigger path has no producer. Dormancy is test-guaranteed — 4 passing at
HEAD, incl. `tests/integration/progression/test_allocate_ap_dormancy.py::
test_allocate_ap_unreachable_via_real_kernel_tick`.

**DEV-004 already owns the fix**: it recommends porting `AllocateAttributeAction`'s correct
PROG-015/PROG-069 aptitude-multiplier logic into this same function and correcting the resulting
PROG-068/069/015 parity gap. Fixing the weights is the same edit to the same function; doing it from
two tickets is how they diverged in the first place. **Leave `execute_allocate_ap` untouched here.**
(DEV-004's line citations have drifted — `core_actions.py:146-176` / `action_router.py:49-50` are now
`:295-317` / `:55-56`. The decision is unchanged.)

## 9. Rule and authority basis to cite

- **OWN-01** / **OWN-03** — single-writer obligation over derived state.
- **CAUSE-05** / **HP-02** — why grants keep their own provenance.
- The **user-accepted 2026-09-30 ruling on this ticket**: species profile values are the entity's
  spawn stats and a recalc must not discard them.
- CLAUDE.md's **Durable State Rule** for the typed home.
- **There is NO catalog Rule declaring species-derived base stats** — the rule owner checked
  `docs/world_rules/` and confirmed none exists. ID-02/STR-01 permit classification-driven
  properties without requiring them; Bible 01 §3 declares *class* bases (NOVICE 100/10/5), not
  species. **Do not cite a species-base Rule; it does not exist.**
- Bible **01 §2** is the formula of record (`base + VIT*2 + END*0.5 + gear`).
- No `progression.yaml` entry covers base-stat preservation — a **new** id is required, not an
  update. PR #276 removed the rebirth/generation entries, so re-read the ledger rather than reusing a
  remembered neighbour.

## 10. Severity note

**P2 stands.** The erosion still does not fire at corpus run lengths. The rule owner corrected one
framing point: the generic profiles do not fully coincide with the recalc defaults — `hero_base`,
`commoner_base` and `monster_base` are `100/10/`**`0`** while `rpg_depth.py` defaults
`base_def=`**`5`**, so erosion is observable on `commoner_base` too (`def 0 → 5`), and
`commoner_base` is live (`entity_archetypes.yaml:98`). It is **not** confined to the `LEGACY-EXPORT`
goblin/wolf/spider profiles.
