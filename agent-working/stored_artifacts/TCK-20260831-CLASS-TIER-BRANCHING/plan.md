---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260831-CLASS-TIER-BRANCHING
artifact_type: plan
tags: [progression]
---

# Implementation Plan — TCK-20260831-CLASS-TIER-BRANCHING

## Summary

Add a mutually-exclusive class-tier branching mechanism generalized from `EvolutionSystem.kind_set`'s
apply-path pattern, not copied from its hardcoded linear mapping. A new `CLASS_TIER_REGISTRY` in
`src/core/classes.py` defines >=2 tier options each for `WARRIOR` and `MAGE` (the two most
content-ready base classes per the existing, unimplemented `docs/core/attributes_and_classes.md`
§5 narrative). A new `class_id_set: Optional[str]` field on `IdentityUpdate` carries the branch
choice through the existing typed-update -> apply-path chain, wired into `IdentityPatch.apply()`
exactly where `role_set`/`life_stage_set` are already handled (`src/engine/patches.py:170-228`) —
`class_id` was the one `IdentityComponent` field that call omitted. Tier stat bonuses are applied
as attribute-level bonuses via a new `ClassTierService.apply_bonuses()`, mirroring
`BreakthroughService.apply_bonuses()`'s exact live-recompute mechanism (looked up by durable id,
not stored as a permanent delta) — chained into `SkillScalingService.get_effective_stats()`
immediately after the existing breakthrough-bonus chain (`src/engine/rpg_depth.py:364-365`), and
threaded through the single live call site of that function (`src/engine/apply.py:481-488`). This
sidesteps the confirmed pre-existing bug where `get_effective_stats()`'s un-sourced
`base_hp`/`base_atk`/`base_def` defaults silently wipe any `CombatUpdate`-shaped bonus on the next
`stats_dirty` recompute — that bug is *not* fixed by this ticket (out of scope, named explicitly
below). PROG-108's divergence is recorded as an ACTIVE (not deferred) intentional gameplay change,
since this ticket ships a real, live post-spawn `class_id` mutation, not just a schema addition.
`docs/core/attributes_and_classes.md` §5's linear Warrior->Champion->Warlord /
Mage->Archmage->Ghost Stalker narrative is explicitly superseded (not left standing) for the two
classes this ticket implements.

## Corrected Type Detail (Fact-Check Note)

The ticket resolution text describes `attribute_bonuses` as `Dict[str, float]`. This is corrected
to `Dict[str, int]` before implementation: `AttributeComponent`'s fields (`strength`, `agility`,
`vitality`, `endurance`, `intelligence`, `spirit`, `wisdom`, `perception`, `charisma`) are all typed
`int` (`src/core/state.py:441-449`), and `BreakthroughService.REGISTRY`'s existing
`attribute_bonuses` values are int literals (`src/progression/breakthroughs.py:13-28`, e.g.
`"spirit": 2`), not floats. Using `float` would silently produce non-integer attribute values via
`dataclasses.replace(current_attributes, **updated)` (`breakthroughs.py:54-58`), which the schema
does not support. `Dict[str, int]` is the only value consistent with the cited schema and the
mechanism being mirrored — implement it that way.

## Module Placement Decision

`CLASS_TIER_REGISTRY` and its `ClassTierOption` dataclass live in `src/core/classes.py` (same
module as `CLASS_REGISTRY`) per explicit ticket-resolution instruction — this is pure class data,
consistent with `CLASS_REGISTRY` already living there. The *service* that applies tier bonuses
(`ClassTierService.apply_bonuses`) lives in a new `src/progression/class_tiers.py`, matching this
codebase's existing `src/core/` (data/registry) vs `src/progression/` (service/logic) split —
`BreakthroughService`, `LevelingService`, `VeterancyService` are each a separate `src/progression/`
module (investigation Risk #1), and `class_id_set`'s reconstruction site (`IdentityPatch.apply()`)
lives in `src/engine/`, not `src/core/`, so there is no existing precedent for putting apply/service
logic inside `src/core/classes.py` itself. `ClassTierService` imports `CLASS_TIER_REGISTRY` from
`src.core.classes`.

## Steps

### Step 1 — Add `ClassTierOption` dataclass and `CLASS_TIER_REGISTRY` to `src/core/classes.py`

**Files:** `src/core/classes.py`

**Change:** Below the existing `CLASS_REGISTRY` dict (after line 51, confirmed as the current
end-of-file via read of `src/core/classes.py:1-51`), add:

```python
@dataclass(frozen=True)
class ClassTierOption:
    tier_id: str                    # new class_id value, e.g. "WARRIOR_CHAMPION"
    name: str
    attribute_bonuses: Dict[str, int] = field(default_factory=dict)

CLASS_TIER_REGISTRY: Dict[str, List[ClassTierOption]] = {
    "WARRIOR": [
        ClassTierOption(tier_id="WARRIOR_CHAMPION", name="Champion",
                         attribute_bonuses={"strength": 4, "vitality": 2}),
        ClassTierOption(tier_id="WARRIOR_GUARDIAN", name="Guardian",
                         attribute_bonuses={"vitality": 4, "endurance": 3}),
    ],
    "MAGE": [
        ClassTierOption(tier_id="MAGE_ARCHMAGE", name="Archmage",
                         attribute_bonuses={"intelligence": 4, "spirit": 2}),
        ClassTierOption(tier_id="MAGE_STORMWEAVER", name="Stormweaver",
                         attribute_bonuses={"spirit": 4, "wisdom": 3}),
    ],
}
```

Bonus magnitudes are authored fresh (investigation confirms "no numeric anchor exists anywhere
for branch-tier stat bonuses" — Risks #1/Assumptions) at the same 2-4-point-per-stat scale already
established by `BreakthroughService.REGISTRY` (`src/progression/breakthroughs.py:13-28`), doubled
across two stats per option for Tier-2 significance. All bonuses are strictly additive/positive —
no penalty fields — so AC #4's win-rate comparison has no downside path to account for. `WARRIOR`'s
two options intentionally diverge in focus (offense-lean `WARRIOR_CHAMPION` reuses the existing
§5 "Champion" name; defense-lean `WARRIOR_GUARDIAN` is new content) so the two are genuinely
mutually exclusive, not a relabeled single path. Same logic for `MAGE`.

**Do NOT touch:** `CLASS_REGISTRY`'s existing 4 entries or their exact `base_hp`/`base_atk`/
`base_def`/`starting_skills`/`starting_gear` values (test_plan.md's anti-drift guard re-runs
`test_class_registry.py`'s exact-value assertions). Do NOT add `NOVICE`/`ROGUE` entries to
`CLASS_TIER_REGISTRY` — out of AC scope, note as future-scope only in the doc step (Step 9).

**Verify:** `test_class_tier_registry_has_branching_options` (new, Step 5) — asserts
`len(CLASS_TIER_REGISTRY["WARRIOR"]) >= 2`, all `tier_id`s distinct, and that the registry is not
a single linear 1:1 mapping like `EvolutionSystem._get_evolved_kind`.

---

### Step 2 — Add `class_id_set` field to `IdentityUpdate`

**Files:** `src/core/updates.py`

**Change:** In the `IdentityUpdate` dataclass (`src/core/updates.py:220-267`, confirmed current
15-field shape via direct read), add one new field following the exact `life_stage_set` pattern
(a simple `Optional[...] = None`, last-write-wins, not an accumulating delta):

```python
class_id_set: Optional[str] = None
```

Add it to `is_noop()` (currently `src/core/updates.py:239-246`):
```python
... and self.class_id_set is None and ...
```

Add it to `merge()` (currently `src/core/updates.py:248-267`), following the exact `life_stage_set`
branch shape:
```python
if other.class_id_set is not None: changes["class_id_set"] = other.class_id_set
```

**Other writers to this field:** `IdentityUpdate` is a single dataclass constructed and merged by
exactly one call chain (`EntityUpdate.identity` -> `IdentityUpdate.merge()` -> consumed once by
`IdentityPatch` in `extract_patches()`, Step 3) — there is no other writer to `IdentityUpdate`
itself; this step only adds a field, it does not touch any other producer.

**Do NOT touch:** the other 15 existing fields, their `is_noop()`/`merge()` branches, or their
ordering. Do NOT give `class_id_set` delta/accumulating semantics — every other class-identity-set
field on this dataclass (`role_set`, `faction_set`, `evolution_level_set`, `life_stage_set`,
`unspent_ap_set`) is last-write-wins, and `class_id_set` must match that shape exactly.

**Verify:** `IdentityUpdate(class_id_set=None).is_noop() is True`; `merge()` last-write-wins
behavior asserted directly in Step 5's new test file, following the existing pattern for sibling
`_set` fields (test_plan.md test #2).

**Depends on:** none (independent of Step 1).

---

### Step 3 — Wire `class_id_set` into `IdentityPatch.apply()`

**Files:** `src/engine/patches.py`

**Change:** `IdentityPatch.apply()` (`src/engine/patches.py:170-228`, confirmed via direct read)
currently reads every other `IdentityUpdate` "_set" field into a local var (`rl`, `fac`, `lvl`,
`ls`, `ap`, etc., lines 176-189 read defaults from `new_id`, lines 191-209 apply the update) but
never reads or writes `class_id` — it is absent from both the local-var block and the final
`replace(...)` call (lines 223-228), so `class_id` today always survives unchanged (dataclass
`replace` preserves unlisted fields). Add:

1. In the local-var read block (near line 176-189, alongside `rl = new_id.role`):
   ```python
   cls_id = new_id.class_id
   ```
2. In the `if self.identity:` block (near line 193-209, alongside `if u_id.role_set is not None: rl = u_id.role_set`):
   ```python
   if u_id.class_id_set is not None: cls_id = u_id.class_id_set
   ```
3. Add `class_id=cls_id` as a new kwarg to the final `replace(new_id, role=rl, faction=fac, ...)`
   call (line 223-228).

This mirrors `kind_set`'s apply-path integration pattern (`KindPatch.apply()`,
`src/engine/patches.py:38-52`, `entity.kind` -> `changes["kind"]`) at the level of "a typed `_set`
field flows through a `ComponentPatch.apply()` into a `replace()` call" — but does NOT reuse
`EvolutionSystem._get_evolved_kind`'s hardcoded 1:1 mapping (`src/engine/evolution.py:156-169`);
the branch-choice logic lives entirely in the caller that constructs `IdentityUpdate(class_id_set=...)`
(a test in this ticket's scope; a real producer is explicitly out of scope, see Scope Guards).

**Other writers to `IdentityComponent.class_id` (enumerated):**
- `V2EntityBuilder.identity(class_id=...)` (`src/core/builder.py:176,198`) — spawn-only, runs once
  at world-compile time via `WorldCompiler`, never again post-spawn. No collision: this step only
  fires through the apply path, which never runs during spawn/compile.
- `src/core/state.py:500` (`IdentityComponent.to_canonical_dict()`) and `src/core/state.py:868`
  (frozen/canonical conversion) — both are read/serialize paths, not writers.
- No other apply-path file writes `class_id` (confirmed by investigation's full-repo grep,
  reconfirmed here: `IdentityPatch.apply()` is the only `ComponentPatch.apply()` that touches
  `IdentityComponent`, and no other `*Patch` class references `class_id`). After this step,
  `IdentityPatch.apply()` becomes the sole post-spawn writer of `class_id`. Within a single tick,
  `IdentityUpdate.merge()` (Step 2) already resolves multiple queued `class_id_set` values via
  last-write-wins before `IdentityPatch.apply()` ever runs once per entity per tick — same
  race-free guarantee every other `_set` field on this dataclass already has.
- `KindPatch` writes `entity.kind` (a distinct top-level `EntityState` field, not
  `entity.identity.class_id`) — no overlap.

**Do NOT touch:** `KindPatch`, `EvolutionSystem`, or `_get_evolved_kind`'s hardcoded mapping dict.
This ticket generalizes the apply-path pattern; it does not extend or repurpose the linear one.

**Verify:** `test_class_id_set_applies_via_identity_patch` (Step 5).

**Depends on:** Step 2 (needs `class_id_set` to exist on `IdentityUpdate`).

---

### Step 4 — Thread tier attribute bonuses through `get_effective_stats()` via a new `ClassTierService`

**Files:** `src/progression/class_tiers.py` (new), `src/engine/rpg_depth.py`, `src/engine/apply.py`

**Change, part A — new service module** `src/progression/class_tiers.py`:

```python
from __future__ import annotations
import dataclasses
from typing import Dict, Optional
from src.core.state import AttributeComponent
from src.core.classes import CLASS_TIER_REGISTRY

class ClassTierService:
    @staticmethod
    def _lookup(class_id: Optional[str]) -> Optional[Dict[str, int]]:
        if not class_id:
            return None
        for options in CLASS_TIER_REGISTRY.values():
            for opt in options:
                if opt.tier_id == class_id:
                    return opt.attribute_bonuses
        return None

    @staticmethod
    def apply_bonuses(class_id: Optional[str], current_attributes: AttributeComponent) -> AttributeComponent:
        bonuses = ClassTierService._lookup(class_id)
        if not bonuses:
            return current_attributes
        updated = {
            attr_name: getattr(current_attributes, attr_name) + amount
            for attr_name, amount in bonuses.items()
        }
        return dataclasses.replace(current_attributes, **updated)
```

This is a direct parallel of `BreakthroughService.apply_bonuses()`'s exact shape and semantics
(`src/progression/breakthroughs.py:31-58`): input is a durable identifier plus the current
`AttributeComponent`, output is a freshly-derived `AttributeComponent` — the bonus is **not**
stored as a permanent delta anywhere; it is recomputed live from `class_id` (already durable on
`IdentityComponent`) on every call, exactly like breakthroughs recompute live from
`active_breakthroughs` on every call. Unmatched/base `class_id`s (e.g. `"NOVICE"`, `"WARRIOR"`
itself before branching) return `current_attributes` unchanged, mirroring "unknown ids are
ignored."

**Change, part B —** `src/engine/rpg_depth.py:341-389` (`SkillScalingService.get_effective_stats`,
confirmed via direct read): add a new optional parameter `class_id: Optional[str] = None` to the
signature (after `active_breakthroughs`, matching that parameter's optional/keyword-only style).
Immediately after the existing breakthrough-bonus line:
```python
effective_attributes = BreakthroughService.apply_bonuses(active_breakthroughs or set(), attributes)
```
(`rpg_depth.py:365`), add:
```python
from src.progression.class_tiers import ClassTierService
effective_attributes = ClassTierService.apply_bonuses(class_id, effective_attributes)
```
chaining the two bonus sources exactly as breakthroughs already chain into the base attributes,
before `LevelingService.recalculate_combat_stats(...)` consumes `effective_attributes` (line 366).

**Change, part C —** `src/engine/apply.py`:
1. `stats_dirty` OR-clause (`src/engine/apply.py:461-473`, confirmed via direct read): add one more
   OR-branch inside the existing `update.identity is not None and (...)` group, alongside
   `update.identity.breakthroughs_add`:
   ```python
   update.identity.class_id_set is not None
   ```
   **Other writers to this exact condition/OR-clause:** the clause already has 6 branches
   (`update.attributes is not None`, `update.equipment is not None`, and 4 sub-conditions inside
   `update.identity is not None and (...)`: `learned_skills`, `traits_add`, `traits_remove`,
   `breakthroughs_add`, plus the `evolution_level_set`-increase check) plus `curr_id.evolution_level`
   increase and `update.wound_update is not None`. This ticket adds a 7th purely additive OR-branch;
   it does not reorder, remove, or change evaluation of any existing branch. The prior ticket
   `TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION` added `breakthroughs_add` to this exact clause
   using the identical pattern — this step repeats that precedent for `class_id_set`.
2. The single live call site of `get_effective_stats()` (`src/engine/apply.py:481-488`, confirmed
   via direct grep as the only call site in `src/` outside the definition): add `class_id=new_id.class_id`
   as a new kwarg (`new_id` is already bound to `curr_id` at line 460/478, which already reflects
   any `class_id_set` mutation applied by `IdentityPatch` earlier in the same `extract_patches()`
   pass, since patches run before the `stats_dirty` block in `_apply_entity_update_to_dict`,
   `src/engine/apply.py:454-457` then `459-473`).

**Other call sites of `get_effective_stats()`:** confirmed via `grep -rn "get_effective_stats(" src/`
that `src/engine/apply.py:481-487` is the only production call site. Test files that call it
directly (e.g. `tests/unit/core/test_rpg_depth.py`) are unaffected since `class_id` is a new
optional kwarg defaulting to `None`, which resolves to "no tier bonus" (identical to today's
behavior).

**Do NOT touch:** the confirmed pre-existing bug where `get_effective_stats()` never receives real
`base_hp`/`base_atk`/`base_def`/`base_evasion` (falls back to `NOVICE`-shaped defaults,
`rpg_depth.py:350-353`) — this is out of scope per the investigation's Anti-Drift Hazards (fixing
it is a materially larger, separately-scoped change affecting every class, not just new tiers).
Do NOT implement tier bonuses as `CombatUpdate`/`AttributeUpdate` deltas applied once at
`class_id_set` time — they would be silently discarded by the next unrelated `stats_dirty` event
per that same bug; the `ClassTierService.apply_bonuses()` live-recompute mechanism in this step is
what avoids it. Do NOT touch `BreakthroughService.REGISTRY`, its `evasion_flat` handling, or any
other breakthrough-specific key.

**Verify:** `test_tier_bonus_survives_subsequent_stats_dirty_event` (guard test, Step 5) and
`test_branch_selection_diverges_class_id` (AC #3 test, Step 5) — both require the bonus to be
observable in `entity.combat` stats after `class_id_set`, and to remain observable after an
unrelated later `stats_dirty` trigger.

**Depends on:** Step 1 (`CLASS_TIER_REGISTRY` must exist), Step 3 (`class_id` must already reflect
the mutation by the time `stats_dirty` reads `curr_id`/`new_id`).

---

### Step 5 — New unit test file: registry, apply-path, divergence, and stats-persistence tests

**Files:** `tests/unit/progression/test_class_tiers.py` (new)

**Change:** Add 4 tests, following `tests/unit/progression/test_evolution.py::test_goblin_evolution`
(`tests/unit/progression/test_evolution.py:56-103`, confirmed present) for the "identical starting
state, diverging update input, assert on `new_state.entities[...].identity`" apply-path pattern,
and `tests/unit/core/test_class_registry.py::make_class_entity` (`tests/unit/core/test_class_registry.py:30`,
confirmed present) for the "manually apply `CLASS_REGISTRY` stats via the builder" entity-construction
helper pattern:

1. `test_class_tier_registry_has_branching_options` — asserts `CLASS_TIER_REGISTRY["WARRIOR"]` and
   `CLASS_TIER_REGISTRY["MAGE"]` each have `>= 2` entries with distinct `tier_id`s, and that no base
   class maps to exactly one hardcoded destination (the anti-pattern check).
2. `test_class_id_set_applies_via_identity_patch` — construct an `EntityState` with
   `identity.class_id == "WARRIOR"`, build `EntityUpdate(identity=IdentityUpdate(class_id_set="WARRIOR_CHAMPION"))`,
   run through `ApplyPath` (matching `test_goblin_evolution`'s apply-path call pattern), assert
   `new_entity.identity.class_id == "WARRIOR_CHAMPION"`. Also assert `IdentityUpdate(class_id_set=None).is_noop()`
   is `True` and `merge()` last-write-wins for two non-`None` values.
3. `test_branch_selection_diverges_class_id` — build two entities from identical starting state
   (`class_id="WARRIOR"`, identical attributes), apply `class_id_set="WARRIOR_CHAMPION"` to one and
   `class_id_set="WARRIOR_GUARDIAN"` to the other through the real apply path, assert both entities'
   resulting `identity.class_id` differ from each other and from `"WARRIOR"`, AND assert their
   post-mutation `combat.atk`/`combat.max_hp` (derived via the `stats_dirty` path, Step 4) differ
   from each other in the direction implied by each tier's `attribute_bonuses` (offense-leaning
   `WARRIOR_CHAMPION` should show a higher `atk` than defense-leaning `WARRIOR_GUARDIAN`, and vice
   versa for `max_hp`) — this is the direct AC #3 fraud-catcher.
4. `test_tier_bonus_survives_subsequent_stats_dirty_event` — apply `class_id_set` +tier bonus, then
   trigger a second, unrelated `stats_dirty` event (e.g. an `AttributeUpdate` delta unrelated to the
   tier's own bonused stats, or `learned_skills` addition), and assert the tier-derived `atk`/`max_hp`
   bonus is still present after the second event (regression guard for investigation Risk #3 /
   Current Behavior #6 — confirms the *implementation shape* chosen in Step 4 correctly sidesteps
   the pre-existing base-stat-reset bug without fixing it).

**Do NOT touch:** `tests/unit/progression/test_evolution.py`, `tests/unit/progression/test_breakthroughs.py`,
`tests/unit/core/test_class_registry.py` — all must remain unchanged and green (test_plan.md
Regression Surface).

**Verify:** `pytest tests/unit/progression/test_class_tiers.py -v` all green.

**Depends on:** Steps 1-4 (exercises all of them).

---

### Step 6 — New integration test: tier bonus does not decrease combat win-rate

**Files:** `tests/integration/combat/test_class_tier_win_rate.py` (new)

**Change:** `tests/integration/combat/` already exists (confirmed:
`tests/integration/combat/test_relation_combat_integration.py`,
`tests/integration/combat/test_wound_healing_permanence.py`) as the right home for this test.
`CombatResolutionSystem.calculate_damage(attacker, defender, atk_mult, def_mult)`
(`src/engine/combat.py:30-46`, confirmed via direct read) is a **pure, fully deterministic**
function — `raw_damage = int(atk * (atk / (atk + dfn * 2.0 + 1.0)))`, no RNG, no dice roll. This
means the AC #4 win-rate check does **not** need statistical/seeded sampling for variance; it
needs a fixed roster of varied opponents so the comparison is meaningful across different matchups
(mirroring "N runs" from test_plan.md as "N deterministic opponent profiles," not "N random RNG
draws").

Design:
1. Build a fixed roster of ~20 opponent `EntityState`s with swept `atk`/`def_stat`/`hp` values
   (e.g. `atk` in `range(8, 28, 2)` paired with proportionate `def_stat`/`hp`), using the
   `V2EntityBuilder(...).kind().location().identity().combat(...).build()` pattern already
   established in `tests/unit/combat/test_combat_matrix.py:8-29` (confirmed via direct read).
2. Build one `WARRIOR` attacker at base (pre-tier) effective stats via
   `SkillScalingService.get_effective_stats(attributes, ..., class_id=None)`, and one identical
   attacker post-`class_id_set="WARRIOR_CHAMPION"` via the same call with `class_id="WARRIOR_CHAMPION"`.
3. For each opponent, run a deterministic alternating-turn damage exchange using
   `CombatResolutionSystem.calculate_damage()` directly (no legality/state machinery needed — this
   keeps the test lightweight per test_plan.md's explicit instruction not to reuse the full
   `src/lab/metamorphic.py` pipeline) until one side's simulated hp reaches <= 0 or a fixed round
   cap (e.g. 50) is hit; record win/loss/draw for both the pre-tier and post-tier attacker against
   the same opponent.
4. Assert `wins(post_tier) >= wins(pre_tier)` across the full roster — exact `>=`, no statistical
   tolerance needed since the underlying damage formula is deterministic (confirmed above).

**Do NOT touch:** `src/lab/metamorphic.py`, `CombatResolutionSystem.resolve_attack()`'s legality/
reward/wound side effects (irrelevant to a pure win-rate stat comparison) — call
`calculate_damage()` directly, not `resolve_attack()`, to avoid needing a full `AuthoritativeState`/
legality setup.

**Verify:** `pytest tests/integration/combat/test_class_tier_win_rate.py -v` — AC #4.

**Depends on:** Step 4 (needs `ClassTierService`-wired `get_effective_stats()`).

---

### Step 7 — Parity ledger: PROG-108 divergence note + new PROG-122 entry

**Files:** `docs/parity_ledger/progression.yaml`, `tests/unit/entity/test_entity_archetypes.py`
(comment-only)

**Change:**
1. `PROG-108` (`docs/parity_ledger/progression.yaml:1121-1139`, confirmed present, `status: verified`,
   `priority: P1`): add a `divergence_note` field cross-referencing the new
   `docs/guidelines/intentional_divergences.md` §2.49/DEV-006 entry (Step 8). Do **not** change
   `status` away from `verified` — PROG-108's claim ("class_id is assigned by role from
   spawn_tables.yaml at world compilation") remains true for spawn-time assignment; the new
   divergence is that class_id can *also* mutate post-spawn via `class_id_set`, which is a
   distinct, additional fact, not a falsification of the spawn-time claim. `test_path` stays
   `tests/unit/entity/test_entity_archetypes.py::test_hero_archetypes_cover_combat_mage_rogue`
   unchanged (that test only exercises `WorldCompiler.compile()`, no ticks/apply-path, so it cannot
   observe `class_id_set` regardless — confirmed by investigation Risk #5).
2. Add a new entry `PROG-122` (next available id, confirmed via `grep`: highest existing is
   `PROG-121` at `docs/parity_ledger/progression.yaml:1447`) for: "A class-tier registry
   (`CLASS_TIER_REGISTRY`, `src/core/classes.py`) defines >=2 mutually-exclusive next-tier options
   per base class (WARRIOR, MAGE), applied post-spawn via `IdentityUpdate.class_id_set` through the
   authoritative apply path." `status: verified`, `priority: P1`, `v2_evidence` citing
   `src/core/classes.py`, `src/core/updates.py`, `src/engine/patches.py::IdentityPatch.apply()`,
   `test_path: tests/unit/progression/test_class_tiers.py::test_class_id_set_applies_via_identity_patch`.
3. Optional, non-behavioral: add a one-line clarifying comment to
   `test_hero_archetypes_cover_combat_mage_rogue`'s docstring noting it asserts spawn-time class
   only (per investigation Risk #5) — assertions (`hero_classes <= {"WARRIOR", "MAGE", "ROGUE"}`)
   must remain byte-identical; this is a comment-only touch, not a test-logic change.

**Do NOT touch:** any other `progression.yaml` entry. Do NOT loosen
`test_hero_archetypes_cover_combat_mage_rogue`'s actual assertions.

**Verify:** `done-checker`'s `frontmatter_valid`/doc-coverage check; `PROG-122`'s cited test passes
(Step 5).

**Depends on:** Step 5 (needs the real test path to cite).

---

### Step 8 — Record the divergence in `docs/guidelines/intentional_divergences.md`

**Files:** `docs/guidelines/intentional_divergences.md`

**Change:** Add a new numbered entry `### 2.49 Post-Spawn class_id Mutation via class_id_set
Diverges from PROG-108's Spawn-Only Framing (TCK-20260831-CLASS-TIER-BRANCHING)`, following the
existing `### 2.48` entry's format (confirmed present at `docs/guidelines/intentional_divergences.md:1397`)
and the `DEV-00N` cross-reference convention (confirmed highest existing is `DEV-005` at line 1548;
this entry is `DEV-006`).

**Rationale class: Intentional Gameplay Change** (not Hardened/Enforced/Unified/Stabilized/Bounded/
Bug Fix — this is a deliberate new mechanic, not a correction or hardening of existing behavior).

**Status: ACTIVE, not DEFERRED.** Per the resolved decision: this ticket ships a real, live
`IdentityPatch.apply()` code path that mutates `class_id` post-spawn (Step 3) — unlike the
`### 2.48` Clan Succession entry's DEFERRED status (which recorded a decision without live behavior
change), this divergence is a real, currently-invoked-in-tests, apply-path-wired behavior change
from the moment this ticket lands, even though (per Prior Work/Scope Guards below) no live
AI/gameplay producer calls it in production yet — that "wired but not yet invoked by production
code" state does not make the divergence itself deferred; the mechanism is active and callable
today, matching the precedent set by `breakthroughs_add`/`traits_add` (fully wired, zero production
callers, still recorded as live per `TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION`).

**Verification:** `tests/unit/progression/test_class_tiers.py::test_branch_selection_diverges_class_id`
(Step 5).

**Do NOT touch:** `### 2.48` or any `DEV-001`-`DEV-005` entry.

**Verify:** `done-checker` doc-coverage check; entry present and cites the correct test path (must
match Step 5's actual test names — reconcile after Step 5 lands if names shifted).

**Depends on:** Step 5 (needs real test path), Step 7 (companion parity entry, should land together).

---

### Step 9 — Rewrite `docs/core/attributes_and_classes.md` §5 to supersede the linear model for WARRIOR/MAGE

**Files:** `docs/core/attributes_and_classes.md`

**Change:** §5 "Hero Classes" (`docs/core/attributes_and_classes.md:171-225`, confirmed via direct
read: "Base Classes (Tier 1)" table at line 186-193, "Breakthrough Classes (Tier 2)" table at
195-202, "Transcendence Classes (Tier 3)" table at 204-211, mermaid diagram at 213-225) currently
documents a strictly **linear** per-class tree (`Warrior -> Champion -> Warlord`, etc.) that is
**explicitly superseded** by this ticket's branching model, for `WARRIOR` and `MAGE` only:

1. In the "Breakthrough Classes (Tier 2)" table (line 195-202), replace the single `Warrior ->
   Champion` row with two rows reflecting the real `CLASS_TIER_REGISTRY["WARRIOR"]` content:
   `Champion` (STR/VIT-focused, from Warrior) and `Guardian` (VIT/END-focused, from Warrior) — both
   Tier 2, mutually exclusive. Replace the single `Mage -> Archmage` row similarly with `Archmage`
   (INT/SPI-focused) and `Stormweaver` (SPI/WIS-focused), both from Mage, mutually exclusive.
2. Update the mermaid diagram (line 213-225) to show `Warrior --> Champion` AND `Warrior -->
   Guardian` as two separate branch edges (not a single linear edge), and similarly `Mage -->
   Archmage` / `Mage --> Stormweaver`.
3. Leave `Ranger`/`Rogue` rows and their `Sharpshooter`/`Assassin` Tier-2 destinations, and the
   entire "Transcendence Classes (Tier 3)" table, **untouched** — this ticket does not implement
   Tier 3, `Ranger`, or `Rogue` branching; those rows remain as pre-existing aspirational/
   unimplemented content, explicitly out of this ticket's scope (matches the ticket's own framing:
   "ROGUE/NOVICE tiers can be a documented future-scope note, not required by AC").
4. Add a short note directly above the Tier 2 table stating: "As of TCK-20260831-CLASS-TIER-BRANCHING,
   Warrior and Mage Tier-2 progression is implemented as branching (>=2 mutually-exclusive options
   per base class) via `CLASS_TIER_REGISTRY` (`src/core/classes.py`), superseding the single-path
   tree previously documented here for these two classes. Ranger and Rogue Tier-2 rows below remain
   unimplemented/aspirational." This directly resolves the pre-existing mermaid-vs-table
   inconsistency for Mage/Ghost Stalker only insofar as Mage's Tier-2 destinations are now
   Archmage/Stormweaver, not Archmage alone — the pre-existing Ranger/Sharpshooter/Ghost Stalker
   mismatch (investigation Current Behavior #7) is untouched, out of scope.

**Do NOT touch:** §5.5 "Mob Archetypes", §5.7 "Attribute Breakthrough Traits", or any other section
of this doc. Do NOT invent Tier 3 content for Warrior/Mage (`Warlord`/`Storm Caller` stay
unimplemented, untouched).

**Verify:** No test verifies doc prose directly; `done-checker`'s doc-coverage check confirms the
file was touched as required by the investigation's "Docs Requiring Update" section. Manual
consistency check: the doc's Tier 2 Warrior/Mage rows must name the same `tier_id`s as
`CLASS_TIER_REGISTRY` (Step 1).

**Depends on:** Step 1 (must cite the real registry content).

---

### Step 10 — Document the new `stats_dirty` trigger condition in the attribute progression contract

**Files:** `docs/mechanics/attribute_progression_contract.md`

**Change:** The "Derived Stat Recalculation Order" / Lifecycle section (confirmed by investigation
at `docs/mechanics/attribute_progression_contract.md` lines 135-142 and 247-250) enumerates the
`IdentityUpdate` fields that trigger `stats_dirty`. Add `class_id_set` to that enumeration,
alongside the existing `evolution_level`, `attributes`, equipment, `learned_skills`,
`traits_add`/`traits_remove`, `breakthroughs_add` list — this is required regardless of any other
scope choice, since every other field already in the `stats_dirty` OR-clause (`src/engine/apply.py:461-473`)
is documented here and `class_id_set` becomes a peer of `breakthroughs_add` after Step 4.

**Do NOT touch:** any other section of this contract (XP formulas, level-up gain tables, etc. are
untouched by this ticket).

**Verify:** `done-checker` doc-coverage check; manual cross-check against the actual
`src/engine/apply.py:461-473` OR-clause after Step 4 lands.

**Depends on:** Step 4 (must describe the real trigger condition, not a planned one).

---

## Scope Guards

- Do NOT modify `EvolutionSystem`, `_get_evolved_kind`, or `KindPatch` (`src/engine/evolution.py`,
  `src/engine/patches.py:38-52`) — this ticket generalizes the apply-path pattern those establish,
  it does not extend, refactor, or repurpose them.
- Do NOT modify `BreakthroughService.REGISTRY`, `BreakthroughService.apply_bonuses()`, or make
  breakthroughs mutually exclusive — ticket Out of Scope, explicit.
- Do NOT fix the `get_effective_stats()` `base_hp`/`base_atk`/`base_def` un-sourced-defaults bug
  (`src/engine/rpg_depth.py:350-353`, `src/engine/apply.py:481-488`) — confirmed pre-existing,
  affects every class including the 3 already-live ones, materially larger and separately-scoped.
  This plan's Step 4 works *around* it (attribute-level bonuses, not combat-stat deltas); it does
  not repair it.
- Do NOT author `NOVICE` or `ROGUE` entries in `CLASS_TIER_REGISTRY` — not required by AC #1 (which
  only requires >=2 options for "at least one base class"); document as future scope in Step 9 only.
- Do NOT build a live AI/decision producer that calls `class_id_set` in production gameplay code —
  ticket Scope only requires registry + typed field + apply-path wiring + the required tests; a
  fully-wired-but-uninvoked-in-production end state is an accepted precedent
  (`TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION`), not a defect to complete here.
  Do NOT touch the `ALLOCATE_AP`/`progression_conversion` feature-flag-gated pipeline
  (`TCK-20260824-ALLOCATE-AP-BRANCH-DECISION`) — unrelated, out of scope.
  A producer is a separate, future ticket if ever needed.
- Do NOT loosen `test_hero_archetypes_cover_combat_mage_rogue`'s actual assertions
  (`hero_classes <= {"WARRIOR", "MAGE", "ROGUE"}` must stay byte-identical) — it tests spawn-time-
  only compiled state, unaffected by this ticket's apply-path mutation.
- Do NOT touch `docs/core/attributes_and_classes.md` §5.5, §5.7, the Ranger/Rogue Tier-2 rows, or
  any Tier-3 content — only the Warrior/Mage Tier-2 rows and the mermaid diagram's Warrior/Mage
  edges are superseded.
- Do NOT implement tier bonuses as `CombatUpdate`/`AttributeUpdate` one-time deltas — must be the
  live-recompute `ClassTierService.apply_bonuses()` mechanism from Step 4.

## Dependency Map

```
Step 1 (registry) ──────┬─→ Step 4 (bonus service + apply.py wiring) ─┬─→ Step 5 (unit tests)
Step 2 (IdentityUpdate)─┼─→ Step 3 (IdentityPatch.apply) ─────────────┤        │
                         │                                             │        ├─→ Step 7 (parity ledger)
                         │                                             ├─→ Step 6 (win-rate test)  │
                         │                                             │                            ├─→ Step 8 (divergence doc)
Step 1 ──────────────────────────────────────────────────────────────→ Step 9 (attrs&classes.md §5)
Step 4 ──────────────────────────────────────────────────────────────→ Step 10 (attr progression contract)
```

Steps 1 and 2 are fully independent and can be implemented/verified in either order. Step 3 depends
only on Step 2. Step 4 depends on Steps 1 and 3. Steps 5 and 6 depend on Step 4 (and transitively on
1-3). Steps 7-10 are documentation steps that depend on the real content/test names produced by
earlier steps — implement them last so citations are accurate rather than provisional.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — class-tier registry with >=2 mutually-exclusive next-tier options per base class | Step 1 | `test_class_tier_registry_has_branching_options` (Step 5) |
| AC #2 — `class_id_set` on `IdentityUpdate` authoritatively mutates `class_id` via apply path, with PROG-108 divergence recorded | Steps 2, 3, 7, 8 | `test_class_id_set_applies_via_identity_patch` (Step 5); divergence doc entry (Step 8) verified by `done-checker` doc-coverage |
| AC #3 — two entities with identical starting class/race but different branch-selection inputs diverge in class_id/tier state, test analogous to `test_goblin_evolution` | Steps 3, 4, 5 | `test_branch_selection_diverges_class_id` (Step 5) |
| AC #4 — a tier's stat bonuses do not decrease average combat win-rate | Step 4, Step 6 | `test_tier_bonus_does_not_decrease_win_rate` in `test_class_tier_win_rate.py` (Step 6) |

## Anti-Drift Notes

- The single most important hazard from the investigation: `get_effective_stats()`'s only live call
  site (`src/engine/apply.py:481-488`) never sources real `base_hp`/`base_atk`/`base_def`, so any
  `CombatUpdate`-shaped tier bonus would be silently wiped by the next unrelated `stats_dirty` event.
  Step 4's design (live-recompute via `ClassTierService.apply_bonuses()`, chained into the
  `effective_attributes` input of `recalculate_combat_stats`, not a stored combat-stat delta) is
  the only implementation shape that survives this bug without fixing it. Step 5's guard test
  (`test_tier_bonus_survives_subsequent_stats_dirty_event`) exists specifically to catch a
  regression back toward the unsafe shape.
- `EvolutionSystem._get_evolved_kind`'s hardcoded 1:1 linear dict (`src/engine/evolution.py:156-169`)
  is the anti-pattern this ticket's Request Summary explicitly says not to copy. `CLASS_TIER_REGISTRY`
  (Step 1) must keep >=2 options per branching class — never collapse to a single hardcoded
  destination per base class.
- `docs/core/attributes_and_classes.md` §5 is `authority: P0`, `status: authoritative`
  (investigation Mechanics/Engine Constraints) — Step 9 must not leave it silently contradicting
  the new code; the supersession must be stated explicitly in the doc itself, not just implied by
  the code change.
- PROG-108's `test_path` (`test_hero_archetypes_cover_combat_mage_rogue`) tests spawn-compiled state
  only and cannot observe `class_id_set` (no ticks run in that test) — Step 7 must not attempt to
  make this test "cover" the new apply-path mutation; a new, separate `test_path` (`PROG-122`) is
  required instead.
- Breakthroughs and class tiers must remain fully independent mechanisms sharing only the
  `attribute_bonuses: Dict[str, int]` *shape* (Step 4) — never the same registry, field, or
  mutual-exclusivity semantics. Ticket Out of Scope is explicit on this point.

## Deviations

Steps 1-6 were implemented exactly as specified (same field names, same registry shape, same
tier_ids/bonus values, same wiring points). Two interpretive notes on the doc-level steps, both
outcome-preserving:

1. **Step 7 (parity ledger)**: implemented via `tools/parity_ledger_writer.py::write_entry()` (the
   sanctioned, schema-validating write path that upserts by `id` and rebuilds the derived index)
   rather than a raw `Edit` on `docs/parity_ledger/progression.yaml`. The resulting YAML content —
   `PROG-108`'s `divergence_note`, the new `PROG-122` entry, `status`/`priority`/`test_path` values
   — matches this plan's Step 7 exactly; only the write mechanism differs, chosen because this
   project treats big full-file YAML rewrites via raw `Edit`/ad-hoc scripts as a real corruption
   risk on this ledger, while the sanctioned writer tool is precedented as safe.
2. **Step 8 (intentional_divergences.md)**: this plan's own phrasing — "next available slot is
   `DEV-006` / `### 2.49`" — reads `DEV-006` and `#2.49` as one identifier pairing rather than two
   separate doc-location instructions. Implemented as a single entry, `### 2.49 ... — cross-referenced
   as DEV-006`, placed in Section 2 ("Detailed Records", following `### 2.48`'s exact format,
   consistent with where this doc's most recent entries already live) rather than also duplicating
   it as a standalone `### DEV-006` header in Section 5 ("Economy Divergences", a section whose
   title is already stale relative to its actual DEV-004/DEV-005 Engine/Combat content). The
   `DEV-006` alias is what `docs/parity_ledger/progression.yaml`'s `PROG-108` `divergence_note`
   cross-references, satisfying the cross-reference convention either way. Step 7's item 3
   (optional docstring clarification on `test_hero_archetypes_cover_combat_mage_rogue`) was not
   done — the plan itself marks it optional and comment-only, no assertion/behavior change.
