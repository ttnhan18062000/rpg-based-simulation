---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION
artifact_type: investigation
tags: [progression]
---

# Investigation — TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION

## Context Search Note

`mcp__knowledge-search__search_docs` returned `{"error":"index not found"}` for query
"BreakthroughService apply_bonuses active_breakthroughs effective stats". Fallback
`python3 tools/knowledge_search.py query "..." --top-k 5` returned `knowledge index not found —
run make knowledge-index`. Both semantic-search paths are unavailable in this repo state.
Proceeded to `graphify query` (both queries ran successfully — results folded into Current
Behavior below) and then to direct file reads, per the ticket's fallback instruction.

## Current Behavior

**`src/progression/breakthroughs.py` (whole file, 41 lines).**
- `BreakthroughService.REGISTRY` (lines 10–27) — the exact current contents:
  - `iron_will`: `{"name": "Iron Will", "attribute_bonuses": {"spirit": 2, "wisdom": 2}, "description": "..."}`
  - `fleet_foot`: `{"name": "Fleet Foot", "attribute_bonuses": {"agility": 3}, "evasion_flat": 0.05, "description": "..."}` — the only registry entry with a bonus key (`evasion_flat`) that is not inside `attribute_bonuses`.
  - `titan_grip`: `{"name": "Titan Grip", "attribute_bonuses": {"strength": 4}, "description": "..."}`
- `get_breakthrough(b_id)` (line 29–31) — simple registry lookup, already correct, no changes needed.
- `apply_bonuses(breakthrough_ids: Set[str], current_attributes: Any) -> Any` (line 33–40) is a **literal `pass` stub** — returns `None` unconditionally. This is the exact gap the ticket targets. Docstring even says "Placeholder for complex synergy logic."

**`src/progression/leveling.py:142–150` — the trait pattern the ticket references.**
```python
# 3.1. Add Trait Bonuses (Task 6.3)
if traits:
    # Simple mapping for now
    if "Tough" in traits:
        max_hp += 20
    if "Quick" in traits:
        evasion += 0.02
    if "Strong" in traits:
        atk += 3
```
This is **not** a bonus-delta dict and **not** a new `AttributeComponent` — it is inline `if`/`elif` logic that mutates local derived-stat accumulator variables (`max_hp`, `evasion`, `atk`) directly inside `recalculate_combat_stats`, operating on **derived combat stats**, not base attributes. Traits here never touch `AttributeComponent` fields at all.

This matters because the breakthrough registry's `attribute_bonuses` (spirit/wisdom/agility/strength) is a different tier: it modifies **base attributes**, which then flow into `recalculate_combat_stats`'s formulas (`src/progression/leveling.py:99–103`). Only `strength`, `vitality`, `endurance`, `agility` are consumed by those formulas — `spirit` and `wisdom` are **not referenced anywhere** in `recalculate_combat_stats`. See Risks below — this directly affects whether `iron_will` alone can satisfy AC #4.

Given the codebase's dominant pattern for producing a modified frozen dataclass (`dataclasses.replace(...)`, used throughout `src/engine/patches.py` and `src/engine/apply.py` for `IdentityComponent`/`CombatComponent`), and that `attribute_bonuses` keys map 1:1 onto `AttributeComponent` field names, the natural typed signature is:

```python
def apply_bonuses(breakthrough_ids: Set[str], current_attributes: AttributeComponent) -> AttributeComponent
```
returning a **new `AttributeComponent`** via `replace()` with summed bonuses applied — not a bare delta dict, and not mimicking leveling.py:142–150's local-derived-stat-mutation style (that style only works because it's private to one function's local scope; `apply_bonuses` is a public service method called from multiple sites in the recompute chain, so it needs a real typed return value other callers can consume). This is a recommendation backed by the evidence above, not an assumption — Plan should confirm it but there is no conflicting pattern in the codebase for public component-bonus application.

**Effective-stats recompute path — exact hop-by-hop trace:**

1. `src/engine/apply.py:448–507` `ApplyPath._apply_entity_update_to_dict()`. `stats_dirty` (lines 460–471) currently triggers only on `update.attributes`, `update.equipment`, `update.identity.learned_skills`/`traits_add`/`traits_remove`/`evolution_level_set` increase, or `update.wound_update`. **It does NOT check `update.identity.breakthroughs_add`.** This is a real gap: an `EntityUpdate` that sets only `IdentityUpdate(breakthroughs_add=[...])` (no attribute/equipment/skill/trait/level change) will leave `stats_dirty` False, so `get_effective_stats` never re-runs and the bonus never reaches `combat` that tick.
2. When `stats_dirty` is True, line 479–485 calls:
   ```python
   derived = SkillScalingService.get_effective_stats(
       new_att, new_eq,
       wounds=new_com.wounds, scars=new_com.scars,
       learned_skills=new_id.learned_skills,
       traits=new_id.traits,
       current_role=new_com.tactical_role
   )
   ```
   `new_id` (= `curr_id`, line 459) already carries `new_id.active_breakthroughs` — it is available at this call site but **not passed**. This is the second wiring point: add `active_breakthroughs=new_id.active_breakthroughs` to this call, and add `update.identity.breakthroughs_add` to the `stats_dirty` OR-condition above it.
3. `src/engine/rpg_depth.py:347–425` `SkillScalingService.get_effective_stats(attributes, equipment=None, wounds=None, scars=None, learned_skills=None, traits=None, current_role=..., base_hp=..., base_atk=..., base_def=..., base_evasion=...)` has **no `active_breakthroughs` parameter today**. At line 401–407 it calls `LevelingService.recalculate_combat_stats(attributes, equipment, learned_skills, traits, ...)`, passing `attributes` straight through, unmodified. To wire breakthroughs in: add an `active_breakthroughs=None` parameter here, and before calling `recalculate_combat_stats`, call `BreakthroughService.apply_bonuses(active_breakthroughs, attributes)` to get bonus-adjusted attributes, then pass those adjusted attributes (not the raw ones) into `recalculate_combat_stats`.
4. `src/progression/leveling.py:76–184` `LevelingService.recalculate_combat_stats()` needs **no changes** if step 3 pre-adjusts attributes before calling it — the existing formulas (lines 99–103) will pick up bonus-adjusted `strength`/`agility`/`vitality`/`endurance` automatically. `spirit`/`wisdom` still won't surface in any derived stat this function returns (see Risks).

**`src/core/state.py` — `active_breakthroughs` already exists.**
- `IdentityComponent.active_breakthroughs: Set[str] = field(default_factory=set)` — line 485. **No new state field is needed**; this was already added (presumably for TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION's `breakthroughs_add` mechanic). Already included in `IdentityComponent.to_canonical_dict()` (line 507) and copied through `_fast_replace_identity` (`src/engine/apply.py:524`) and the canonical/frozen conversion at `src/core/state.py:828`.
- `AttributeComponent` (line 439–448) has `spirit` and `wisdom` fields already — confirmed the right place for `iron_will`'s bonus target.

**`src/core/updates.py` / `src/engine/patches.py` — the "add a breakthrough" mechanic (separate from "apply its bonus").**
- `IdentityUpdate.breakthroughs_add: list[str]` — `src/core/updates.py:229`; merged in `merge()` at line 256.
- `src/engine/patches.py:187,206,224` — `IdentityPatch.apply()` unions `u_id.breakthroughs_add` into `active_breakthroughs` and writes it back via `replace(..., active_breakthroughs=frozenset(brk), ...)`. This mechanic is fully wired and already tested (`tests/unit/progression/test_breakthroughs.py::test_breakthrough_addition`, `::test_duplicate_breakthrough_suppression`). It is **out of scope** per the ticket — confirmed nothing constructs `breakthroughs_add` in production/gameplay code (matches TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION's finding, restated in this ticket's Out of Scope). This investigation did not find any new evidence contradicting that.

## Mechanics / Engine Constraints

- `docs/mechanics/01_entity_anatomy.md` Section 5 "Progression & Growth" (lines 87–104) currently documents only the XP curve and level-up rewards (AP/level cap/skill unlocks) — it has **no breakthroughs subsection at all**, despite `docs/parity_ledger/progression.yaml` PROG-003 already asserting "Skill scaling and breakthroughs are explicit progression systems" as `verified`. This is a pre-existing doc gap the ticket must close.
- Section 2 "Derived Combat Stats" (lines 32–57) documents the HP/ATK/DEF/Evasion formulas that `recalculate_combat_stats` implements — this is the section that would need a one-line cross-reference note if breakthrough attribute bonuses are described as flowing into these formulas via bonus-adjusted attributes (optional, not mandatory, since the bonus is applied upstream of these formulas, not by changing the formulas themselves).
- No `docs/engine/` contract constrains this work directly — the kernel/pipeline phase structure and the `authoritative_mutation_pipeline_contract.md` apply-path rules are unaffected; this ticket only fills a stub inside an already-existing call chain (`apply.py` → `rpg_depth.py` → `leveling.py`), it does not add a new pipeline phase or a new durable-state field (the field already exists).
- Architecture Rule (project CLAUDE.md, "Durable State Rule"): `active_breakthroughs` is already a typed field with a stable location (`IdentityComponent`) and existing lifecycle (added via `breakthroughs_add` → `IdentityPatch`) — implementing `apply_bonuses` as a pure, stateless bonus-computation function (no new mutation site) stays inside that boundary. The only mutation-adjacent risk is the `stats_dirty` gap in `apply.py` (see Current Behavior #1) — that is a read/recompute correctness fix, not a new durable-state write path.

## Docs Requiring Update

- `docs/parity_ledger/progression.yaml`: PROG-024 currently claims `status: verified`, `priority: P0`, `test_path: null`, `v2_evidence: Implementation proven via exhaustive checklist audit Phase 1-11` for text `'test_breakthrough_applies_bonus: Breakthrough applies bonus.'` — but `apply_bonuses` is a literal `pass` stub and no test named `test_breakthrough_applies_bonus` exists anywhere in `tests/`. This entry must be corrected once the real implementation and test land: `test_path` populated with the real test's path, `v2_evidence` updated to cite the actual implementation, and `status` re-confirmed as `verified` only after the test passes (P0 entries require a passing `test_path` per project rules).
- `docs/mechanics/01_entity_anatomy.md`: add a breakthroughs documentation subsection. Best-fit location, verified against the actual chapter table of contents (`## 1. Core Attributes`, `## 2. Derived Combat Stats`, `## 3. Class Registry`, `## 4. Biological Laws`, `## 5. Progression & Growth`, `## 6. Trauma: Wounds & Scars`): **Section 5 "Progression & Growth"** is the best fit — it already documents milestone-triggered rewards (level-up AP, skill unlocks at specific levels), and breakthroughs are the same kind of milestone-triggered passive perk, just keyed by breakthrough ID instead of level. A new `### Breakthroughs (Passive Perks)` subsection there, listing the registry contents (id, attribute_bonuses, any non-attribute bonus fields) and the bonus-application rule, is the natural continuation of that section's existing content. (Section 2 "Derived Combat Stats" was considered as an alternative since bonuses ultimately feed the same formulas, but rejected as primary location — Section 2 documents the *formulas*, not the *sources* of attribute values, and traits/gear bonuses that already feed those formulas are not documented there either, so adding breakthroughs there would be inconsistent with the chapter's existing structure.)

The `docs/engine/authoritative_mutation_pipeline_contract.md` doc (under `docs/engine/`) is not required to change for this ticket: `apply_bonuses` is a pure computation added to an already-existing call chain inside the apply path, it does not add a new mutation type, new `Update` field, or new pipeline phase — the one field it touches (`active_breakthroughs`) already exists and is already threaded through `IdentityPatch`/`_fast_replace_identity`.

The `docs/guidelines/intentional_divergences.md` doc (under `docs/guidelines/`) is not required to change for this ticket: implementing `apply_bonuses` to match the registry's already-`verified` PROG-003/PROG-024 entries is completing existing intended behavior, not an intentional divergence from the Mechanics Bible or legacy behavior — there is no rationale class (Hardened/Enforced/Unified/Stabilized/Bounded/Bug Fix/Intentional Gameplay Change) that applies here beyond "finishing a stub to match already-documented intent."

## Parity Ledger Overlap

- **PROG-024** (`docs/parity_ledger/progression.yaml`, ~line 245): `text: 'test_breakthrough_applies_bonus: Breakthrough applies bonus.'`, `status: verified`, `priority: P0`, `test_path: null`. **Must be corrected** — this is explicit ticket scope. P0 requires a passing `test_path` after this ticket; currently none exists.
- **PROG-023** (~line 235): `text: 'test_breakthrough_is_added: Breakthrough is added.'`, also `status: verified`, `test_path: null`. Not explicitly in this ticket's scope (only PROG-024 is named), but flagged here because it shares the same false-`test_path` pattern — the real tests that satisfy it are `tests/unit/progression/test_breakthroughs.py::test_breakthrough_addition` and `::test_duplicate_breakthrough_suppression` (names differ from the ledger's asserted test name `test_breakthrough_is_added`). Recommend Plan phase consider fixing PROG-023's `test_path` in the same pass since the touched file is identical and the fix is nearly free, but this is a scope-expansion call for Plan/human judgment, not asserted as required here.
- **PROG-003** (~line 22): `text: 'Skill scaling and breakthroughs are explicit progression systems.'`, `status: verified`, `test_path: null`. General/umbrella entry, not specifically about bonus application — no action required by this ticket, noted for awareness only.
- No P0 entries in `combat_movement.yaml`, `town_resource.yaml`, or other subsystem ledgers overlap this ticket's scope (attribute-bonus application stays entirely inside `src/progression/` + `src/engine/apply.py` + `src/engine/rpg_depth.py`).

## Prior Work

- **TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION** (`stored_artifacts/TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION/`) — established that `breakthroughs_add` (the mechanic that populates `active_breakthroughs`) is fully wired end-to-end (`IdentityUpdate` → `IdentityPatch` → state) but is never constructed anywhere in production gameplay code — only in tests. This ticket's Out of Scope section correctly inherits that finding and does not attempt to fix the "grant a breakthrough during gameplay" gap.
- `tests/unit/progression/test_breakthroughs.py` (both existing tests) exercise only the "add a breakthrough to `active_breakthroughs`" mechanic via `ApplyPath.apply_generation` — neither test touches `apply_bonuses` or `get_effective_stats` at all. No prior test coverage exists for the bonus-application behavior this ticket implements.
- `tests/unit/core/test_rpg_depth.py::TestSkillScaling`, `::TestEffectiveStats`, `::TestStaminaApplyIntegration`, `::TestWoundApplyIntegration` establish the existing test patterns for `SkillScalingService` (direct unit calls) and apply-path integration (`ApplyPath._apply_entity_update` / `ApplyPath.apply_generation` round-trips) that this ticket's new tests should follow for consistency.

## Risks and Open Questions

1. **`iron_will` alone may not produce an observable change in "combat stats" (AC #4 wording risk).** `recalculate_combat_stats` (`leveling.py:99–103`) only consumes `strength`, `vitality`, `endurance`, `agility` — never `spirit` or `wisdom`. `iron_will`'s `attribute_bonuses: {spirit: 2, wisdom: 2}` would correctly land on the entity's `AttributeComponent` via `apply_bonuses`, but would produce **zero change** in `max_hp`/`atk`/`def_stat`/`evasion`/`move_cost`/`tactical_role`, since none of those formulas read spirit/wisdom. If AC #4's integration test uses `iron_will` as its example (the same breakthrough named in AC #1), the assertion "shows the bonus in recomputed combat stats" will have nothing to assert against. Recommend the AC #4 integration test use `titan_grip` (strength+4 → visible `atk` change) or `fleet_foot` (agility+3 → visible `evasion` change, ignoring `evasion_flat` per the fleet_foot scope decision below) instead of `iron_will`, while AC #1's exact spirit/wisdom-delta assertion stays a direct unit-level `apply_bonuses` call (not routed through `get_effective_stats`). **This does not block implementation** — it only changes which breakthrough ID the AC #4 integration test should exercise. Flagging so Plan doesn't accidentally pick `iron_will` for both and produce a vacuous integration test.
2. **`fleet_foot`'s `evasion_flat` is a genuinely different bonus shape** — it sits outside `attribute_bonuses` and targets a *derived* stat (evasion) directly, not a base attribute. Recommend treating it as **out of scope** for this pass: `apply_bonuses`'s signature (`Set[str], AttributeComponent -> AttributeComponent`) has no natural way to carry a derived-stat bonus, and wiring it would require either a second return channel from `apply_bonuses` or a second call site inside `get_effective_stats` after `recalculate_combat_stats` returns — a materially larger change than "finish the stub." AC #2 ("correctly sums bonuses when multiple breakthrough_ids are passed") can be fully satisfied using `iron_will` + `titan_grip` (both pure `attribute_bonuses`, non-overlapping attribute keys) without touching `fleet_foot` at all — so leaving `fleet_foot`'s `evasion_flat` unimplemented does not block any AC. `fleet_foot`'s `attribute_bonuses: {agility: 3}` portion should still work through the same `apply_bonuses` path as the other two; only its `evasion_flat` key is excluded.
3. **`stats_dirty` gap (Current Behavior #1)** is a correctness bug beyond the literal "implement `apply_bonuses`" scope, but AC #4 explicitly requires "an entity with populated active_breakthroughs shows the bonus in recomputed combat stats" through the full `apply.py` → `rpg_depth.py` → `leveling.py` path — which cannot be satisfied without also fixing this gate. Treat it as in-scope (the ticket's own Scope bullet 3, "Wire active_breakthroughs into the effective-stats recompute path," already covers it), not a separate ticket.
4. **No open question blocks implementation.** All four "Assumptions / Open Questions" the ticket lists have concrete answers from this investigation: (a) signature → `AttributeComponent -> AttributeComponent` via `replace()`; (b) `fleet_foot` `evasion_flat` → recommend out of scope, doesn't block any AC; (c) `active_breakthroughs` state field → already exists, no schema change needed; (d) `layer: core` → already correctly justified in the ticket's own frontmatter note.

## Anti-Drift Hazards

- **Do not let `apply_bonuses` reach into `get_effective_stats`'s wound/scar/gear penalty logic.** Its job is strictly: given a set of breakthrough IDs and a base `AttributeComponent`, return a bonus-adjusted `AttributeComponent`. Keep it a pure function with no `AuthoritativeState`/`EntityState` dependency — mirrors `enforce_attribute_caps` (`rpg_depth.py:32-45`) and `SkillScalingService.calculate_skill_damage`'s existing pure-function style.
- **Do not silently expand scope into constructing `breakthroughs_add` in gameplay code.** That is explicitly out of scope (ticket + TCK-20260808 finding) — the temptation exists because "an entity with populated active_breakthroughs" (AC #4) might read as "give the test entity a breakthrough via the real granting mechanism," but the correct interpretation is "construct a test entity/state with `active_breakthroughs` already populated" (as `test_duplicate_breakthrough_suppression` already does via `replace(entity.identity, active_breakthroughs={"iron_will"})`), not "build the missing granting system."
- **Do not change `recalculate_combat_stats`'s existing formulas** (lines 99–103) to make `spirit`/`wisdom` feed into `max_hp`/`atk`/`def`/`evasion` "so iron_will has a visible effect." That would be an undocumented mechanics change requiring its own Mechanics Bible update and parity-ledger entries for `stat_recalculation_parity` (currently `VERIFIED v2`), well beyond "finish the `apply_bonuses` stub." Use the AC #4 test-breakthrough-choice fix (Risk #1) instead.
- **Do not touch `WOUND_THRESHOLD_RATIO`.** Noticed in passing: `docs/mechanics/01_entity_anatomy.md:106-113` documents `WOUND_THRESHOLD_RATIO = 0.25` with strict `>`, but `src/engine/rpg_depth.py:112` has `WOUND_THRESHOLD_RATIO = 0.40` with `>=`. This is a pre-existing, unrelated doc/code divergence — out of scope for this ticket; do not "fix" it while editing the same chapter file for the breakthroughs subsection.
- **Preserve the `stats_dirty` short-circuit's performance intent.** `apply.py`'s `_apply_entity_update_to_dict` is on the hot per-tick apply path (see file header's "Optimized v5... sub-100ms targets"); when adding `breakthroughs_add` to the dirty-check OR-condition, keep it a cheap truthiness check on the list (`update.identity.breakthroughs_add`), consistent with the existing checks, not a set-difference or registry lookup.
