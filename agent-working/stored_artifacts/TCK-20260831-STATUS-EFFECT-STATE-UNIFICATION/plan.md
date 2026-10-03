---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION
artifact_type: plan
tags: [architecture]
---

# Implementation Plan — TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION

## Summary

This plan implements two independent typed-state migrations that the ticket's own Scope text
bundles together but investigation.md shows are architecturally separate:

1. **`status_frozen`/`status_stunned`** move off `identity.properties` (untyped dict) onto a new
   `StatusEffectState` frozen dataclass, stored as `List[StatusEffectState]` on `CombatComponent`,
   following the `WoundState`/`ScarState` precedent exactly (typed dataclass → `List[...]` field on
   `CombatComponent` → dedicated `StatusEffectUpdate` on `EntityUpdate` → dedicated `StatusEffectPatch`
   registered in `extract_patches()`).
2. **`interaction_kind`** moves off `identity.properties`/`property_updates` onto a new `kind: Optional[str]`
   field on the already-existing `InteractionComponent`/`InteractionUpdate` — **not** into
   `StatusEffectState`. This is a correction to the ticket's literal Scope text ("interaction_kind...
   into a typed StatusEffectState"); investigation.md (`Current Behavior → InteractionComponent /
   InteractionUpdate`, lines 68-95) found `interaction_kind` and `target_node_id` are always set
   together at both producer call sites and always read together at all 7 consumer call sites — it
   belongs on the record that already tracks the multi-tick interaction, not folded into a
   combat-status record. AC #3's literal wording ("interaction_kind migrated off property_updates in
   all 7 real consumer files") does not name a target record, so this is satisfied by
   `InteractionComponent.kind` — see Acceptance Criteria Map.

Both migrations are storage-shape changes only: investigation.md confirms `status_frozen`/
`status_stunned` have **zero production writers** today (only 13 test-fixture sites across 8 files),
so the "provably unchanged" bar for that half is proven by porting those fixtures and by the one live
non-boolean consumer (`combat.py:84`'s SHATTER multiplier). `interaction_kind` has 2 live production
producers (harvest, loot) and 5 consumers with real production traffic through 3 of the 7 values;
the other 4 values (`chest`/`guild`/`inn`/`tavern`) remain test-fixture-only, unchanged by this
migration.

## Steps

### Step 1 — Add `StatusEffectState` dataclass to `src/core/state.py`
**Files:** `src/core/state.py`
**Change:** Add immediately after `ScarState` (currently `state.py:104-113`, verified read directly):
```python
@dataclass(frozen=True, slots=True)
class StatusEffectState:
    """A persistent status effect (e.g. frozen, stunned) applied to an entity."""
    kind: str  # "frozen", "stunned"
    source: str = ""
    magnitude: float = 0.0
    expires_tick: int = -1
```
Field name `kind` for the type discriminator matches the existing convention on `WoundState.kind`
(`state.py:93`, values `SLASH`/`CRUSH`/`PIERCE`/`BURN`, a plain `str` with a comment, no runtime
validator/enum) — `StatusEffectState` follows the identical convention: no `Literal`/enum, just a
`str` field with a comment listing the two current values. A discriminator field is required (not
optional) because, unlike the old two-separate-booleans shape, `status_effects` is now a *list* that
could in principle hold multiple simultaneous effects — `kind` is what lets a reader distinguish
"frozen" from "stunned" entries in that list.
`source`/`magnitude`/`expires_tick` are the three fields the ticket's own Scope text names. Per
investigation.md Risk #4 (lines 341-351): these three fields currently have **zero readers** anywhere
in the 5 consumer call sites (every current read is a boolean presence/truthiness check). This is a
conscious YAGNI trade-off, matching `WoundState`'s own precedent of being built out ahead of some of
its consumers — state this explicitly, do not treat it as validated by AC #2 (AC #2 is satisfied by
these fields simply being present-but-unread, not by them being justified).
**Do NOT touch:** `WoundState`, `ScarState` themselves — do not add a `status_type`/`kind` field to
either, do not merge this record with them.
**Verify:** New test `tests/unit/core/test_state_status_effect.py::test_status_effect_state_schema`
(Step 11).

### Step 2 — Add `status_effects` list field to `CombatComponent` + canonical-dict entry
**Files:** `src/core/state.py`
**Change:** In `CombatComponent` (verified `state.py:296-339`), add a new field alongside `wounds`/
`scars` (currently `state.py:312-313`):
```python
    status_effects: List[StatusEffectState] = field(default_factory=list)
```
Then in `CombatComponent.to_canonical_dict()` (`state.py:317-339`, verified read directly — currently
includes `"wounds": [asdict(w) for w in self.wounds]` and `"scars": [...]` at lines 334-335), add:
```python
            "status_effects": [asdict(s) for s in self.status_effects],
```
**Other writers of `CombatComponent`/its canonical dict this step must coexist with:** `CombatPatch`
(readiness/hp/etc.), `WoundPatch` (`patches.py:622-646`, writes `wounds`/`scars` onto the same
component via `changes["combat"] = new_com`), and `_apply_entity_update_to_dict`'s stats-dirty
recompute (`apply.py:465-502`, reads `new_com.wounds`/`new_com.scars` to feed
`SkillScalingService.get_effective_stats`). None of these write or read `status_effects` — this step
only adds the field and its canonical-dict entry; Step 4 (`StatusEffectPatch`) is the only writer.
This closes investigation.md Risk #1 (determinism-hash coverage) for the status-effect half: since
`CombatComponent.to_canonical_dict()` already feeds `EntityState.to_canonical_dict()` via
`"combat": self.combat.to_canonical_dict()` (verified `state.py:783`), no change to
`EntityState.to_canonical_dict()` itself is needed — `identity.properties` (state.py:796) simply
contains two fewer keys once Step 5 removes the old writes/reads.
**Do NOT touch:** `EntityState.to_canonical_dict()` (state.py:739-801) — no edit needed there per
above; do not add a redundant top-level `"status_effects"` key.
**Verify:** New canonical-hash guard test (Step 11, "Determinism/canonical-hash coverage guard").

### Step 3 — Add `StatusEffectUpdate` to `src/core/updates.py`, wire into `EntityUpdate`
**Files:** `src/core/updates.py`
**Change:** Add immediately after `WoundUpdate` (verified `updates.py:609-626`):
```python
@dataclass(frozen=True, slots=True)
class StatusEffectUpdate:
    """New status effects and effect removal."""
    effects_add: List[StatusEffectState] = field(default_factory=list)
    effects_remove: List[str] = field(default_factory=list)  # status `kind` values to remove

    def is_noop(self) -> bool:
        return not self.effects_add and not self.effects_remove

    def merge(self, other: StatusEffectUpdate) -> StatusEffectUpdate:
        if not other or other.is_noop():
            return self
        changes = {}
        if other.effects_add: changes["effects_add"] = self.effects_add + other.effects_add
        if other.effects_remove: changes["effects_remove"] = self.effects_remove + other.effects_remove
        return replace(self, **changes)
```
`effects_remove` takes `kind` strings (not per-instance IDs, unlike `WoundUpdate.wounds_heal` which
takes wound IDs) — `StatusEffectState` has no `id` field (Step 1 deliberately omits one; the old
boolean-flag shape had no per-instance identity either, so removal-by-`kind` preserves equivalent
semantics without inventing an unused ID field).
Then add to `EntityUpdate` (verified `updates.py:628-663`), immediately after `wound_update` (line
657):
```python
    status_effect_update: Optional[StatusEffectUpdate] = None
```
and add `(self.status_effect_update is None or self.status_effect_update.is_noop())` to
`EntityUpdate.is_noop()` (verified body starts `updates.py:664`, follow the existing pattern for
`wound_update`).
**Other writers of `EntityUpdate.is_noop()`/merge semantics this step must coexist with:** every
other `EntityUpdate` field already listed in `is_noop()` — this step only adds one more clause to an
existing `and`-chain; no reordering of existing clauses.
**Do NOT touch:** `WoundUpdate`, `CombatUpdate`, or any other existing `Optional[...]` field on
`EntityUpdate` — this is purely additive.
**Verify:** Exercised indirectly by Step 11's fixture-migration tests once producers/consumers use it
via Step 4's patch (no production writer exists yet — see Step 1's `Backward Compatibility` framing
in Scope Guards).

### Step 4 — Add `StatusEffectPatch` to `src/engine/patches.py`, register in `extract_patches()`
**Files:** `src/engine/patches.py`
**Change:** Add immediately after `WoundPatch` (verified `patches.py:622-646`):
```python
@dataclass(frozen=True, slots=True)
class StatusEffectPatch(ComponentPatch):
    status_effect_update: Optional[Any] = None  # StatusEffectUpdate

    def is_noop(self) -> bool:
        return self.status_effect_update is None or self.status_effect_update.is_noop()

    def merge(self, other: StatusEffectPatch) -> StatusEffectPatch:
        if not other or other.is_noop():
            return self
        merged = (self.status_effect_update.merge(other.status_effect_update)
                  if self.status_effect_update and other.status_effect_update
                  else (other.status_effect_update or self.status_effect_update))
        return StatusEffectPatch(entity_id=self.entity_id, status_effect_update=merged)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace
        if self.status_effect_update:
            new_com = changes.get("combat", entity.combat)
            new_effects = list(new_com.status_effects)
            if self.status_effect_update.effects_remove:
                new_effects = [e for e in new_effects if e.kind not in self.status_effect_update.effects_remove]
            new_effects.extend(self.status_effect_update.effects_add)
            new_com = replace(new_com, status_effects=tuple(new_effects))
            changes["combat"] = new_com
```
Register in `extract_patches()` (verified `patches.py:689-751`), add immediately after the
`update.wound_update` block (verified `patches.py:742-744`):
```python
    if update.status_effect_update is not None:
        p = StatusEffectPatch(entity_id, status_effect_update=update.status_effect_update)
        if not p.is_noop(): patches.append(p)
```
**Other writers to `changes["combat"]` this patch must coexist with — enumerated:** `CombatPatch`
(hp/readiness/tactical-role fields), `WoundPatch` (`patches.py:622-646`, writes `wounds`/`scars` onto
the same `changes["combat"]` key). `extract_patches()` runs patches in the fixed order shown above
(`CombatPatch` at line ~712-714, `WoundPatch` at line ~742-744, `StatusEffectPatch` newly inserted
right after `WoundPatch`) — each patch's `apply()` reads `changes.get("combat", entity.combat)` (the
prior patch's output if one already ran this tick) and writes back a new `CombatComponent`, so
ordering is safe: `StatusEffectPatch` running after `WoundPatch` sees `WoundPatch`'s already-applied
`wounds`/`scars` changes in `new_com` and preserves them via `replace(new_com, status_effects=...)`
(all other `CombatComponent` fields pass through unchanged). No two patches write conflicting fields
of `CombatComponent`, so there is no field-level race — only a well-defined last-writer-wins per field,
which this migration does not disturb.
**Explicitly NOT wired to `stats_dirty`:** `_apply_entity_update_to_dict`'s stats-dirty trigger
(verified `apply.py:475-489`) currently fires on `update.wound_update is not None` because
`SkillScalingService.get_effective_stats` (verified signature `src/engine/rpg_depth.py:342-355`:
`attributes, equipment=None, wounds=None, scars=None, learned_skills=None, traits=None, ...`) takes
`wounds`/`scars` as parameters and has **no `status_effects` parameter**. Do not add
`update.status_effect_update is not None` to the `stats_dirty` condition — there is no derived-stat
consumer to feed, and doing so would recompute stats for a state change no consumer reads (confirmed
by investigation.md Risk #4 — magnitude/expires_tick/source have zero readers).
**Do NOT touch:** `WoundPatch`, `CombatPatch`, `_apply_entity_update_to_dict`'s `stats_dirty` boolean
expression itself (only the enumeration above; no new clause added).
**Verify:** New `tests/unit/domains/optimization/test_component_patches.py` case for
`StatusEffectPatch` (Step 13).

### Step 5 — Migrate the 5 status-flag consumer files off `identity.properties`
**Files:** `src/engine/legality.py`, `src/engine/combat.py`, `src/engine/pipeline_phases/actor_validity.py`,
`src/systems/strategic_systems/work_queue.py`, `src/systems/strategic_systems/intelligence.py`
**Change:** Replace every read of `<entity>.identity.properties.get("status_frozen")` /
`.get("status_stunned")` with a check against the new typed list. Per investigation.md's exact call
site list (`Current Behavior → The 5 status-flag consumer files`, lines 97-131), the sites are:
- `legality.py:132, 166, 218, 319` — `actor.identity.properties.get("status_frozen") or
  actor.identity.properties.get("status_stunned")` → `any(s.kind in ("frozen", "stunned") for s in
  actor.combat.status_effects)` (variable name per call site: `actor`/`entity`/`attacker` — keep the
  existing local variable name at each site, only change the expression).
- `combat.py:84` — `defender.identity.properties.get("status_frozen")` → `any(s.kind == "frozen" for
  s in defender.combat.status_effects)`. **Preserve exact SHATTER semantics**: frozen (not stunned)
  on the **defender** (not attacker) multiplies **attacker** `atk_mult *= 1.5` and sets
  `trace["SHATTER"] = 1.5` — do not read `status_stunned` here, do not swap attacker/defender.
- `actor_validity.py:59-65` — `is_stunned`/`is_frozen` lines migrate to `any(s.kind == "stunned" for
  s in entity.combat.status_effects)` / `any(s.kind == "frozen" for s in
  entity.combat.status_effects)`. The third line, `is_sleeping = entity.identity.properties.get
  ("status_sleeping", False)`, is **left untouched** (out of scope) — this produces a deliberate
  hybrid read (2 typed + 1 untyped) at this one file; see Scope Guards.
- `work_queue.py:32` — same pattern, `any(...)` over `entity.combat.status_effects`.
- `intelligence.py:848, 918, 1221` — same pattern at all 3 call sites.
No helper method/property is added to `CombatComponent` for this check — each of the ~11 call sites
inlines `any(s.kind == "<value>" for s in <entity>.combat.status_effects)` directly, matching how
`WoundState`/`ScarState` consumers already inline reads of `entity.combat.wounds`/`.scars` rather than
going through a component-level helper method.
**Do NOT touch:** `status_sleeping` reads (anywhere) — explicitly out of scope per ticket text and
investigation.md Anti-Drift Hazards.
**Verify:** Existing tests in Regression Surface (test_plan.md) covering each file, ported per Step 12;
new no-active-status baseline cases (Step 13).

### Step 5a — Update `docs/mechanics/damage_formula_contract.md` to match the new SHATTER read
**Files:** `docs/mechanics/damage_formula_contract.md`
**Change:** Per CLAUDE.md's Authoritative Mechanics Rule ("Documentation and source code must
remain in 100% semantic parity... update the corresponding doc... in the same session"), Step 5
above changes `combat.py:84`'s SHATTER check from `defender.identity.properties.get("status_frozen")`
to `any(s.kind == "frozen" for s in defender.combat.status_effects)`. This doc names the exact old
expression in two places (verified read directly, current text quoted below):
- **Line 72**, multiplicative-modifiers table, `Frozen/Shatter` row, Condition cell — currently
  `` `defender.identity.properties.get("status_frozen")` truthy ``. Change to
  `` `any(s.kind == "frozen" for s in defender.combat.status_effects)` truthy `` — the identical
  expression Step 5 specifies for the migrated `combat.py:84` read (no paraphrase).
- **Line 224**, "High-ground flanking attack with Shatter" worked example, Defender line — currently
  `Defender: def_stat=10, max_hp=80, hp=80, status_frozen=True`. Change to
  `Defender: def_stat=10, max_hp=80, hp=80, status_effects=[StatusEffectState(kind="frozen")]` —
  describing the same fact (defender is frozen, which is what makes the "Multiplicative: shatter →
  atk_mult *= 1.50" line on the next lines of that example true) via the new typed storage shape
  (`CombatComponent.status_effects: List[StatusEffectState]`, Step 2) rather than the old
  `identity.properties["status_frozen"]` dict key.
No other line in this doc changes — Step 2's fractional-armor formula (lines 76-88), Step 3's
durability decay, the additive-modifiers table (lines 58-66), the other two multiplicative-modifier
rows (Sleep Exhaustion, Stamina Exhaustion — neither references `identity.properties` or
`status_frozen`), and the "no tactical modifiers" baseline worked example (lines 205-218) are all
untouched.
**Do NOT touch:** any other row of the additive/multiplicative modifier tables; the baseline
("no tactical modifiers") worked example; the wound-check math in either worked example (lines
217, 235-237) — only the two `status_frozen` mentions identified above change.
**Verify:** No dedicated automated test — this is a documentation-parity fix required by CLAUDE.md's
Authoritative Mechanics Rule, confirmed by manual doc/code cross-check during the Verify phase (same
class of check as a parity_ledger update). Indirectly corroborated by the new `test_shatter_logic`
asymmetry case (Step 13), which exercises the exact expression this doc now describes.

### Step 6 — Add `kind` field to `InteractionComponent` + canonical-dict entry
**Files:** `src/core/state.py`
**Change:** In `InteractionComponent` (verified `state.py:390-407`), add a field:
```python
    kind: Optional[str] = None  # "harvest", "ground_item", "corpse", "chest", "guild", "inn", "tavern"
```
placed after `start_tick` (matching `target_node_id`'s existing `int | None = None` style at line 393
— use `Optional[str] = None` for consistency with the file's typing-import style already in use for
this same class). Then in `InteractionComponent.to_canonical_dict()` (verified `state.py:398-407`),
add `"kind": self.kind,` alongside the existing `target_node_id`/`progress`/`start_tick` entries.
This closes investigation.md Risk #1 for the interaction-kind half: `InteractionComponent.to_canonical_dict()`
already feeds `EntityState.to_canonical_dict()` via `"interaction": self.interaction.to_canonical_dict()`
(verified `state.py:749`), so no further change to `EntityState.to_canonical_dict()` is needed.
No runtime validator is added for the 7-value closed set — matches `WoundState.kind`'s own precedent
(plain `str`/`Optional[str]`, comment-documented, no enum/`Literal` enforcement).
**Do NOT touch:** `target_node_id`, `progress`, `start_tick` field definitions themselves.
**Verify:** New canonical-hash guard test (Step 13).

### Step 7 — Add `kind` to `InteractionUpdate` (`is_noop`/`merge`)
**Files:** `src/core/updates.py`
**Change:** In `InteractionUpdate` (verified `updates.py:66-83`), add a field:
```python
    kind: Optional[str] = None
```
Update `is_noop()` (verified `updates.py:73-74`, currently `return self.target_node_id is None and
self.progress_delta == 0.0 and not self.reset`) to also require `self.kind is None`. Update `merge()`
(verified `updates.py:76-83`) to add: `if other.kind is not None: changes["kind"] = other.kind`,
following the exact pattern already used for `target_node_id`.
**Other writers to `InteractionUpdate` this step must coexist with:** the two producers
(`harvest.py`, `loot.py`, migrated in Step 9) are the only writers; `InteractionSystem.enforce`
(`src/engine/interaction.py`, confirmed by investigation.md as a live consumer of
`InteractionUpdate`/`ResourceNodeUpdate`/`IdentityUpdate` that does **not** reference
`identity.properties`/`interaction_kind` at all — zero grep hits) is unaffected by this field
addition since it never reads or writes `kind`.
**Do NOT touch:** `target_node_id`, `progress_delta`, `reset` field definitions.
**Verify:** New `InteractionPatch` test case (Step 13).

### Step 8 — Update `InteractionPatch.apply()` to carry `kind`
**Files:** `src/engine/patches.py`
**Change:** In `InteractionPatch.apply()` (verified `patches.py:132-144`), the `reset=True` branch
already replaces the whole component with `InteractionComponent()` (line 138) — this **naturally
clears `kind` for free** since the fresh component uses the field's default (`None`). No code change
needed for that branch. In the non-reset branch (lines 140-144), add `kind` to the `replace(...)`
call:
```python
                changes["interaction"] = replace(new_int,
                    target_node_id=u_int.target_node_id if u_int.target_node_id is not None else new_int.target_node_id,
                    progress=new_int.progress + u_int.progress_delta,
                    kind=u_int.kind if u_int.kind is not None else new_int.kind
                )
```
**Explicit behavior change from the old dict-based storage (must be pinned by a test, not left
implicit):** the old `interaction_kind` in `identity.properties` was merge-only (never cleared,
per investigation.md's "Reset/staleness note", lines 185-195) — it stayed set indefinitely after a
`reset=True`. The new `kind` field on `InteractionComponent` **is** cleared on reset, because
`reset=True` replaces the whole component. Investigation confirms this is provably inert (every
consumer gates on `entity.interaction.target_node_id is not None` before reading `kind`, so the
stale-vs-cleared difference is never observable) — but pin it with an explicit test (Step 13) rather
than let the difference pass silently.
**Do NOT touch:** the `reset=True` branch's `InteractionComponent()` construction itself.
**Verify:** New `InteractionPatch` reset-clears-kind test (Step 13).

### Step 9 — Migrate the 2 producers (`harvest.py`, `loot.py`) to set `kind` via `InteractionUpdate`
**Files:** `src/actions/harvest.py`, `src/actions/loot.py`
**Change:**
- `harvest.py:31-42` (verified location by investigation.md) — currently constructs
  `property_updates={"interaction_kind": "harvest", "harvest_duration": float(node.required_ticks)}`
  alongside `interaction=InteractionUpdate(target_node_id=..., progress_delta=0.0, reset=False)` in
  the same `EntityUpdate`/action-result construction. Change to
  `interaction=InteractionUpdate(target_node_id=..., progress_delta=0.0, reset=False, kind="harvest")`
  and **remove** `"interaction_kind"` from `property_updates`, leaving `"harvest_duration"` in
  `property_updates` untouched (adjacent-but-out-of-scope key, per Anti-Drift Hazards).
- `loot.py:38-46` — currently `property_updates={"interaction_kind": target_kind}` (where
  `target_kind` is `"ground_item"` or `"corpse"`) alongside the same `InteractionUpdate` pattern.
  Change to `interaction=InteractionUpdate(target_node_id=..., progress_delta=0.0, reset=False,
  kind=target_kind)` and remove `"interaction_kind"` from `property_updates` (no other keys are set
  there per investigation, so `property_updates` may end up empty/removed entirely at this call site
  if `interaction_kind` was its only key — verify against the real current call site before deleting
  the kwarg outright).
**Other writers to `property_updates`/`IdentityPatch` this step must coexist with:** `IdentityPatch`
(`patches.py:147-234`, specifically `props.update(self.property_updates)` at line 221) is the sole
applier of `property_updates` — it is a dict merge with no delete semantics. This step does not
change `IdentityPatch` itself; it only stops these two producers from adding the `"interaction_kind"`
key to the dict they pass in. Any other producer that independently writes `property_updates` at
these same two call sites (none found by investigation — `harvest_duration` is the only other key,
and it is untouched) is unaffected.
**Do NOT touch:** `harvest_duration` in `property_updates` at `harvest.py:39-40`; any other
`property_updates` keys unrelated to `interaction_kind`.
**Verify:** `tests/unit/resource/test_harvest_channeling.py`, `tests/unit/resource/test_loot_channeling.py`
(both located by grep for this plan, confirmed real files — see Anti-Drift Notes), plus
`tests/integration/kernel/test_resource_conservation.py` / `test_resource_conservation_v2.py`.

### Step 10 — Migrate the 5 `interaction_kind` consumer files off `identity.properties`
**Files:** `src/systems/world_systems/harvesting.py`, `src/systems/economy_systems/chests.py`,
`src/systems/economy_systems/loot.py`, `src/systems/economy_systems/town_service.py`,
`src/systems/social_systems/guilds.py`
**Change:** Replace every `entity.identity.properties.get("interaction_kind")` read (guarded by
`entity.interaction.target_node_id is not None`, per investigation.md's exact call sites, lines
160-170) with `entity.interaction.kind`:
- `harvesting.py:19` — gate `== "harvest"` → read `entity.interaction.kind == "harvest"`. Leave the
  adjacent `harvest_duration` read (`harvesting.py:43`, `entity.identity.properties.get
  ("harvest_duration", 10.0)`) untouched — out of scope.
- `chests.py:19` — gate `== "chest"` → `entity.interaction.kind == "chest"`.
- `loot.py:20-63` (economy_systems) — gate `in ["ground_item", "corpse"]` and the 3 further branches
  on the value (lines 20, 21, 28, 63) → all switch to `entity.interaction.kind`.
- `town_service.py:17-46` — gate `in ["inn", "tavern", "guild"]` and the "inn" vs other branch (line
  46) → switch to `entity.interaction.kind`.
- `guilds.py:19` — gate `== "guild"` → `entity.interaction.kind == "guild"`.
**Do NOT touch:** the `entity.interaction.target_node_id is not None` guard itself (unchanged — still
the primary gate); `harvest_duration` read in `harvesting.py`.
**Verify:** `tests/unit/world/test_town_services.py`, `tests/unit/world/test_guild_intel.py`,
`tests/unit/world/test_chest_lifecycle.py` (ported per Step 12), plus the resource-conservation
integration tests.

### Step 11 — Add `StatusEffectState` schema test
**Files:** new `tests/unit/core/test_state_status_effect.py`
**Change:** Assert `StatusEffectState` is `frozen=True` (attempting attribute mutation raises
`FrozenInstanceError`), assert default field values (`source=""`, `magnitude=0.0`,
`expires_tick=-1`), assert `asdict(StatusEffectState(kind="frozen"))` round-trips as a plain dict
(matching the `WoundState`/`ScarState` serialization pattern already exercised implicitly via
`to_canonical_dict()`). No existing sibling schema-only test file was found for `WoundState`/
`ScarState` by grep (`tests/unit/combat/test_tactical_wound_scar_wiring.py` constructs `WoundState`/
`ScarState` instances but as fixtures for wiring behavior, not schema assertions) — this is a new,
standalone file, not an extension of an existing one.
**Do NOT touch:** any existing test file for this step.
**Verify:** the test itself (new).

### Step 12 — Migrate the 13 status-flag test fixtures + 2 interaction_kind test fixtures (clean cutover)
**Files:** `tests/unit/combat/test_phase5_combat_legality.py` (line 62),
`tests/unit/combat/test_combat_legality_regression.py` (line 51),
`tests/unit/combat/test_rpg_core_recovery.py` (line 188),
`tests/unit/combat/test_phase5_negative_cases.py` (lines 184, 194, 255),
`tests/unit/combat/test_tactical_hardening.py` (line 30),
`tests/unit/strategic/test_status_hardening.py` (lines 22, 45),
`tests/unit/core/test_hardening_e5.py` (line 65),
`tests/unit/world/test_chest_lifecycle.py` (line 14),
`tests/unit/world/test_guild_intel.py` (line 12)
**Change: clean cutover, no compatibility shim.** Investigation confirms zero production writers for
`status_frozen`/`status_stunned` today, so there is no live caller whose behavior a transition-window
shim would need to bridge — a shim would add real complexity (dual-read logic in 5 consumer files)
to protect a code path that does not exist in production. Decision: migrate all fixtures to the new
typed construction and **remove** the old `identity.properties.get("status_frozen"/"status_stunned")`
reads entirely in the same step as Step 5 (no fallback/OR-read of the old dict key remains anywhere).
Concretely, replace this pattern (verified exact form at
`test_phase5_combat_legality.py:62`):
```python
attacker = replace(attacker, identity=replace(attacker.identity, properties={"status_frozen": True}))
```
with:
```python
attacker = replace(attacker, combat=replace(attacker.combat,
    status_effects=[StatusEffectState(kind="frozen", source="test_fixture", magnitude=1.0, expires_tick=-1)]))
```
(adjust `kind="stunned"` where the fixture currently sets `status_stunned`; both keys together where
a fixture sets both). For the 2 `interaction_kind` fixtures (`test_chest_lifecycle.py:14`,
`test_guild_intel.py:12`), replace `identity.properties={"interaction_kind": "chest"/"guild"}` with
`interaction=replace(entity.interaction, kind="chest"/"guild")` (or direct
`InteractionComponent(kind=...)` construction if the fixture builds the component fresh rather than
via `replace` — check each site's exact construction pattern before editing).
Every assertion in these test files stays unchanged — only the fixture-construction lines change.
This directly satisfies AC #2's "behavior provably unchanged" bar (a test that still asserts the same
blocked/gated outcome after switching construction APIs proves storage-shape equivalence).
**Do NOT touch:** any assertion logic in these files; the `status_sleeping` fixture construction in
`test_hardening_e5.py` if present (out of scope — verify it is not swept in accidentally).
**Verify:** all listed files pass unmodified in assertions; Scoped Pytest Commands (test_plan.md) run
green.

### Step 13 — Add remaining new/extended tests
**Files:**
- `tests/unit/combat/test_combat_legality_regression.py` — **extend** `test_shatter_logic` (verified
  real location, `test_combat_legality_regression.py:46-58` — this is the real SHATTER test;
  test_plan.md's guess of `test_direct_combat_outcomes.py` was unconfirmed and is corrected here) with
  an asymmetry case: `status_stunned` alone (no `frozen`) does **not** set `trace["SHATTER"]`.
- Each of the 5 consumer files' existing regression tests (Regression Surface, test_plan.md) — add a
  no-active-status baseline case (empty `status_effects` list) proving unblocked/no-multiplier/
  not-skipped behavior, per AC #2's "no active status" wording.
- `tests/unit/domains/optimization/test_component_patches.py` (verified current imports at line 8 do
  **not** include `InteractionPatch` — only `CombatPatch, NavigationPatch, AttributePatch,
  IdentityPatch, WoundPatch, KindPatch` — so `InteractionPatch`'s `kind` extension has **no existing
  coverage in this file today**, this is genuinely new, not just an extension) — add: (a) a
  `StatusEffectPatch` add/remove case mirroring the existing `WoundPatch` case, (b) an
  `InteractionPatch` case proving `kind` is set on a non-reset update and cleared on `reset=True`.
- `tests/unit/world/test_town_services.py`, `test_guild_intel.py`, `test_chest_lifecycle.py` —
  extend to confirm all 7 `interaction_kind` values route correctly post-migration (the 4
  never-produced values included, per Anti-Drift Test Guards).
- Canonical-hash coverage guard — new `tests/unit/core/test_canonical_hash_status_effect.py`:
  construct two otherwise-identical `EntityState`s, one with an active `StatusEffectState` entry (or
  a set `interaction.kind`) and one without; assert `to_canonical_dict()` output differs. No existing
  sibling file for `WoundState`/`ScarState` canonical-hash-specific coverage was found by grep (the
  general `to_canonical_dict`-referencing test files found are for unrelated components — cognition,
  self-model, faction, etc.) — this is a new file.
- `tests/unit/resource/test_harvest_channeling.py`, `tests/unit/resource/test_loot_channeling.py` —
  confirmed real files (found by grep, not previously verified in test_plan.md) covering
  `HarvestAction`/`LootAction`; extend if they assert on `property_updates["interaction_kind"]`
  directly (check before editing — if they only assert on `entity.interaction.target_node_id`/
  `progress`, no change needed beyond Step 9's producer change already being covered).
**Do NOT touch:** `status_sleeping`, `harvest_duration` test coverage in any of these files.
**Verify:** full Scoped Pytest Commands block from test_plan.md, run green.

### Step 14 — Parity ledger review (discretionary, not a required correctness fix)
**Files:** `docs/parity_ledger/combat_movement.yaml`, `docs/parity_ledger/town_resource.yaml`,
`docs/parity_ledger/strategic_cognition.yaml`, `docs/parity_ledger/social_narrative.yaml`
**Change:** Investigation confirms (Parity Ledger Overlap section) that no existing entry in
`combat_movement.yaml` names `status_frozen`/`status_stunned`/`ATTACKER_STATUS_BLOCKED` by field
(zero grep hits), and no entry's `status`/`v2_evidence` becomes false through this migration in
either `combat_movement.yaml` or `town_resource.yaml` (`TOWN-009`/`TOWN-010`'s pre-existing broken
`test_path` is out of scope — see Scope Guards). A grep run for this plan (`grep -n
"intelligence.py\|work_queue.py\|guilds.py" docs/parity_ledger/strategic_cognition.yaml
docs/parity_ledger/social_narrative.yaml`) found existing entries citing `intelligence.py` by file
path (none specifically naming `status_frozen`/`status_stunned`/the 3 guard call sites at lines
848/918/1221) and zero entries citing `work_queue.py` or `guilds.py` at all. Since this migration
changes only internal read expressions (not file paths, not function signatures those entries cite),
no existing entry's `v2_evidence` becomes inaccurate. **Decision: no ledger entry is required by this
migration** (matches investigation's own "discretionary strengthening opportunity, not a correctness
requirement" framing for `combat_movement.yaml`, extended here to the other 3 files on the same
reasoning). The parity-updater phase should still scan all 4 files during Verify to confirm this
holds after the real diff lands, and may optionally add a strengthening entry citing the new
`test_shatter_logic` asymmetry case or the new `StatusEffectPatch`/`InteractionPatch` tests if it
judges the evidence trail is meaningfully improved — but this plan does not mandate a specific new
entry ID, since no exact next-free ID was verified during investigation or this planning pass.
**Do NOT touch:** `TOWN-009`/`TOWN-010`'s broken `test_path` (pre-existing gap, explicitly out of
scope — see Scope Guards); do not fabricate a ledger entry ID without checking the real next-free ID
in the target file at implementation time.
**Verify:** N/A (documentation review step, not test-verified).

## Scope Guards

- Do not migrate `status_sleeping` (`actor_validity.py:59-61`) — same guard clause as
  `status_frozen`/`status_stunned` but not named in ticket scope. `actor_validity.py` ends this
  migration with a deliberate hybrid read (2 typed field checks + 1 remaining untyped dict read) —
  this is an accepted interim state, not an oversight.
- Do not touch `harvest_duration` (`harvest.py:39-40`, `harvesting.py:43`) — adjacent untyped
  property key set at the same call site as `interaction_kind`, explicitly out of scope.
- Do not touch `EmotionUpdateService`, `EmotionalModel`, or `src/engine/pipeline_phases/hardening.py:97`
  — confirmed zero code overlap with this ticket's 12 consumer files. AC #4 is resolved as "condition
  not met, not touched" (see Acceptance Criteria Map) — do not add an `EmotionalModel` row to
  `docs/architecture/cognition_domain_ownership.md` as part of this ticket.
- Do not add new production writers for the 4 never-produced `interaction_kind` values (`"chest"`,
  `"guild"`, `"inn"`, `"tavern"`) — wiring `ChestSystem`/`GuildIntelSystem`/`TownServiceSystem` to a
  real action producer is legitimate future work but a different ticket. This migration preserves
  their existing (test-fixture-only) behavior only.
- Do not fix the pre-existing broken `test_path` on `TOWN-009`/`TOWN-010` in
  `docs/parity_ledger/town_resource.yaml` (`tests_v2/parity/test_resource_interaction_parity.py` does
  not exist) — pre-existing gap, not caused by and not in scope for this ticket.
- Do not add `status_effect_update is not None` to the `stats_dirty` trigger in
  `_apply_entity_update_to_dict` (`apply.py:475-489`) — no derived-stat consumer reads
  `status_effects`' enrichment fields; see Step 4.
- Do not add a runtime validator/enum for either `StatusEffectState.kind` or
  `InteractionComponent.kind` — matches the `WoundState.kind` precedent (plain `str`, comment-only).
- `InteractionSystem.enforce` (`src/engine/interaction.py`) is confirmed not a consumer of
  `interaction_kind` (zero references) — do not modify this file as part of this migration.

## Dependency Map

Steps 1-4 (StatusEffectState → CombatComponent field → StatusEffectUpdate → StatusEffectPatch) must
land in that order before Step 5 (consumer migration) can compile against the new type. Steps 6-8
(InteractionComponent.kind → InteractionUpdate.kind → InteractionPatch.apply) must land in that order
before Steps 9-10 (producer/consumer migration). Steps 5 and 9-10 are independent of each other (touch
disjoint file sets) and can be implemented in either order once their respective prerequisite chains
are done. Step 11 depends only on Step 1. Step 12 depends on Steps 1-5 (status-flag fixtures) and
Steps 6-10 (interaction_kind fixtures) both being complete, since it ports fixtures for both halves.
Step 13 depends on all of Steps 1-12. Step 14 is independent and can run any time after Step 13's
tests are green (it is a documentation review, not a code change).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: A new `StatusEffectState` typed record exists following the `WoundState`/`ScarState` precedent | Step 1, Step 2 | `tests/unit/core/test_state_status_effect.py` (Step 11) |
| AC #2: `status_frozen`/`status_stunned` migrated off `identity.properties.get()` in all 5 consumer files, behavior provably unchanged for entities with no active status | Steps 3-5, Step 12, Step 13 | Regression Surface files (test_plan.md) + new no-active-status baseline cases (Step 13) |
| AC #3: `interaction_kind` migrated off `property_updates` in all 7 real consumer files | Steps 6-10 — satisfied via `InteractionComponent.kind`, **not** `StatusEffectState` (see Summary's explicit correction) | `test_town_services.py`, `test_guild_intel.py`, `test_chest_lifecycle.py`, resource-conservation integration tests |
| AC #4: `docs/architecture/cognition_domain_ownership.md` gains an `EmotionalModel` row ONLY IF scope touches `EmotionUpdateService` migration | Not implemented — condition not met (this ticket's scope never touches `EmotionUpdateService`, confirmed by investigation.md) | N/A — resolved as "condition not met, no doc change" |

## Anti-Drift Notes

- **AC #3 does not require folding `interaction_kind` into `StatusEffectState`.** The ticket's Title
  and Request Summary use the phrase "unify... into a typed StatusEffectState" loosely; investigation
  traced the real call-site evidence (both producers set `interaction_kind` and `target_node_id`
  together, both consumers read them together) and found `InteractionComponent`/`InteractionUpdate`
  is the architecturally correct home. Architecture-review should not flag this as scope deviation —
  it is a corrected implementation of AC #3's literal text, not a missed requirement.
- **SHATTER asymmetry** (`combat.py:84`): only `status_frozen`/`kind == "frozen"` on the *defender*
  triggers the 1.5x multiplier; `status_stunned` never does, and it is never checked on the attacker.
  Getting attacker/defender or frozen/stunned swapped here would silently change combat balance. The
  real test is `test_combat_legality_regression.py:46-58` (`test_shatter_logic`) — test_plan.md's
  original guess of `test_direct_combat_outcomes.py` for this coverage was unconfirmed and is
  corrected by this plan's grep verification.
- **Reset-clears-kind is a real, intentional, provably-inert behavior change.** The old
  `identity.properties["interaction_kind"]` never cleared on reset (merge-only dict). The new
  `InteractionComponent.kind` clears automatically because `reset=True` replaces the whole component.
  This is safe because every consumer gates on `target_node_id is not None` before reading `kind` —
  but pin it with the explicit reset test in Step 13 rather than leaving it as an unstated side
  effect.
- **Zero production writers for `status_frozen`/`status_stunned` today.** All 5 consumer branches for
  these two flags are currently dead code in live simulation runs — only test fixtures exercise them.
  This is why Step 12 chooses a clean cutover (no compatibility shim): there is no live caller to
  bridge, and adding dual-read logic across 5 files would protect a non-existent production path.
- **`InteractionUpdate`/`InteractionComponent` extension is low-risk relative to the pipeline.**
  Investigation confirmed `InteractionSystem.enforce` (the live production phase operating on
  `InteractionUpdate`) never references `identity.properties`/`interaction_kind` — this migration adds
  a field that phase simply never reads, no interaction with its existing logic.
- **`test_component_patches.py` currently has zero `InteractionPatch` coverage** (verified: its
  import list at line 8 includes `WoundPatch`/`IdentityPatch`/etc. but not `InteractionPatch`) — the
  `kind`-on-reset test in Step 13 is genuinely new coverage, not an extension of a pre-existing case
  that just needs a new assertion.

## Open Questions

None. All design decisions the ticket and investigation left open are resolved above:
`StatusEffectState`'s field shape (Step 1), its storage location (`CombatComponent`, Step 2), the
`interaction_kind`→`InteractionComponent.kind` correction and its full write path (Steps 6-9), the
clean-cutover backward-compatibility decision for the 13 test fixtures (Step 12), the determinism-hash
coverage steps for both halves (Steps 2 and 6), support for the 4 never-produced `interaction_kind`
values (retained, Step 10/Scope Guards), AC #4's resolution (not in scope, Acceptance Criteria Map),
and the parity ledger scope (Step 14 — discretionary, no mandated new entry). Implementer should
proceed without further clarification.
