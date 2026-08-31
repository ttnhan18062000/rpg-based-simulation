---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION
artifact_type: plan
tags: [progression]
---

# Implementation Plan — TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION

## Summary

`BreakthroughService.apply_bonuses` (`src/progression/breakthroughs.py:33-40`) is a literal `pass`
stub. This plan finishes it as a pure function `apply_bonuses(breakthrough_ids: Set[str],
current_attributes: AttributeComponent) -> AttributeComponent` that sums each known breakthrough's
`attribute_bonuses` from `REGISTRY` (lines 10-27) via `dataclasses.replace()`, ignoring unknown
ids and `fleet_foot`'s non-attribute `evasion_flat` key. It then wires this into the existing
effective-stats recompute chain — `SkillScalingService.get_effective_stats`
(`src/engine/rpg_depth.py:380-425`) gains an `active_breakthroughs=None` parameter and calls
`apply_bonuses` before delegating to `LevelingService.recalculate_combat_stats`
(`src/progression/leveling.py:76-184`, unchanged) — and threads that parameter through the one
call site in `ApplyPath._apply_entity_update_to_dict`
(`src/engine/apply.py:448-507`), which also gets its `stats_dirty` OR-condition
(lines 460-471) extended to fire on `update.identity.breakthroughs_add` alone. No new durable
state field is needed: `IdentityComponent.active_breakthroughs: Set[str]`
(`src/core/state.py:485`) already exists and is already threaded through `IdentityPatch`/
`_fast_replace_identity`. The plan closes with the required test coverage from `test_plan.md`,
correcting the false `test_path: null` on parity ledger entry PROG-024
(`docs/parity_ledger/progression.yaml:245-253`), and adding a `### Breakthroughs (Passive
Perks)` subsection to `docs/mechanics/01_entity_anatomy.md` Section 5 (currently lines 87-104,
ending with `### Level Up Rewards` at line 96 before the `---` separator at line 104).

## Steps

### Step 1 — Implement `BreakthroughService.apply_bonuses`
**Files:** `src/progression/breakthroughs.py`
**Change:** Replace the `pass` stub (lines 33-40) with:
```python
@staticmethod
def apply_bonuses(breakthrough_ids: Set[str], current_attributes: AttributeComponent) -> AttributeComponent:
    if not breakthrough_ids:
        return current_attributes
    deltas: Dict[str, int] = {}
    for b_id in breakthrough_ids:
        entry = BreakthroughService.REGISTRY.get(b_id)
        if not entry:
            continue
        for attr_name, amount in entry.get("attribute_bonuses", {}).items():
            deltas[attr_name] = deltas.get(attr_name, 0) + amount
    if not deltas:
        return current_attributes
    updated = {
        attr_name: getattr(current_attributes, attr_name) + amount
        for attr_name, amount in deltas.items()
    }
    return dataclasses.replace(current_attributes, **updated)
```
Add `import dataclasses` and `from src.core.state import AttributeComponent` at the top of the
file (currently only `from __future__ import annotations` and
`from typing import Dict, Any, Set` per the full file read at
`src/progression/breakthroughs.py:1-2`). Update the `current_attributes: Any -> Any` type hints
on the signature to `AttributeComponent -> AttributeComponent` to match. Confirmed field names
`spirit`, `wisdom`, `agility`, `strength` all exist on `AttributeComponent`
(`src/core/state.py:439-449`, read directly this session), so `getattr`/`replace` on those names
is safe. Confirmed `REGISTRY`'s three entries (`src/progression/breakthroughs.py:10-27`) each key
`attribute_bonuses` as a plain `{attr_name: int}` dict — `fleet_foot`'s `evasion_flat: 0.05` key
sits as a sibling key at the same dict level, not inside `attribute_bonuses`, so the loop above
naturally never touches it (see Scope Guards).
**Do NOT touch:** `get_breakthrough` (lines 29-31, already correct). Do not add any handling for
`evasion_flat`. Do not import `AuthoritativeState`/`EntityState` or anything beyond
`AttributeComponent` — this must stay a pure function with no world-state dependency (investigation
Anti-Drift Hazards, mirrors `enforce_attribute_caps` at `rpg_depth.py:32-45`).
**Verify:** `test_apply_bonuses_iron_will_returns_spirit_wisdom_plus_two`,
`test_apply_bonuses_sums_multiple_breakthrough_ids`,
`test_apply_bonuses_empty_ids_returns_unchanged`,
`test_apply_bonuses_unknown_id_returns_unchanged_no_raise`,
`test_apply_bonuses_mixed_known_and_unknown_ids` (all new, `tests/unit/progression/test_breakthroughs.py`).

### Step 2 — Add `active_breakthroughs` parameter to `SkillScalingService.get_effective_stats`
**Files:** `src/engine/rpg_depth.py`
**Change:** In `get_effective_stats` (signature at lines 380-393, confirmed by direct read this
session), add a new keyword parameter `active_breakthroughs: Optional[Set[str]] = None` after
`traits`. Immediately before the existing call to
`LevelingService.recalculate_combat_stats(attributes, equipment, learned_skills, traits, ...)`
(lines 401-407), insert:
```python
from src.progression.breakthroughs import BreakthroughService
effective_attributes = BreakthroughService.apply_bonuses(active_breakthroughs or set(), attributes)
```
and change the `recalculate_combat_stats` call's first positional argument from `attributes` to
`effective_attributes`. Everything downstream of that call (wound/scar penalty application at
lines 409-423, evasion clamp at line 423) is unchanged — those operate on the returned `Dict`, not
on `AttributeComponent`, so they need no modification. `recalculate_combat_stats`
(`src/progression/leveling.py:76-184`, read this session) needs no code change: its formulas at
lines 100-103 read `attributes.vitality`, `attributes.strength`, `attributes.endurance`,
`attributes.agility` off whatever `AttributeComponent` it is handed, so bonus-adjusted attributes
flow through automatically.
**Do NOT touch:** `recalculate_combat_stats`'s formulas (lines 99-103), the trait-bonus block
(lines 142-150), equipment-bonus block (lines 106-129), or tactical-role derivation (lines
157-174) — none of these need or should change. Do not add `spirit`/`wisdom` to any formula here.
**Verify:** `test_get_effective_stats_applies_breakthrough_attribute_bonus`,
`test_get_effective_stats_no_breakthroughs_unchanged` (both new,
`tests/unit/core/test_rpg_depth.py::TestEffectiveStats`).

### Step 3 — Wire `active_breakthroughs` through `apply.py`'s call site and fix `stats_dirty`
**Files:** `src/engine/apply.py`
**Change:** Two edits inside `ApplyPath._apply_entity_update_to_dict`
(`src/engine/apply.py:448-507`, confirmed by direct read this session):

1. Extend the `stats_dirty` OR-condition (currently lines 460-471) to add a new disjunct:
   `(update.identity is not None and update.identity.breakthroughs_add)` — a cheap truthiness
   check on the list, consistent with the existing `update.identity.learned_skills`/
   `traits_add`/`traits_remove` checks on the same lines, per the investigation's performance note
   (this function is on the hot per-tick apply path per its own docstring, "Merged v5 logic").
   Confirmed `IdentityUpdate.breakthroughs_add: list[str]` exists at `src/core/updates.py:229`.
2. In the `get_effective_stats` call (currently lines 479-485), add
   `active_breakthroughs=new_id.active_breakthroughs` as a new keyword argument. `new_id` is
   already bound to `curr_id` (= `changes.get("identity", entity.identity)`, line 459) at this
   point in the function, and `IdentityComponent.active_breakthroughs`
   (`src/core/state.py:485`) is already populated correctly by `IdentityPatch.apply()`
   (`src/engine/patches.py:187,206,224`, which unions `breakthroughs_add` into
   `active_breakthroughs` and runs as one of the `patches` applied at line 456, before this block
   executes) — so `new_id.active_breakthroughs` already reflects any `breakthroughs_add` from the
   *current* update by the time this call runs, in the same apply pass.

Other writers to `stats_dirty`'s inputs / to `changes["combat"]` in this same function: this is
the only place `stats_dirty` is computed and the only place `changes["combat"]`'s `atk`/`def_stat`/
`max_hp`/`evasion`/`move_cost`/`range`/`tactical_role` fields are set from `derived` in this
function (lines 487-495); `changes["combat"]` is separately touched at lines 497-503 for `hp`/
`stamina` reset on level-up, which is an independent branch after the block this step edits and is
untouched by this change. `extract_patches`/`patch.apply()` (line 453-456,
`src/engine/patches.py`) is the only other writer to `changes["identity"]` (via `IdentityPatch`)
in this function, and it runs strictly before the `stats_dirty` block reads `curr_id`, so there is
no ordering race — `new_id.active_breakthroughs` in this step is always post-patch, current-tick
state.
**Do NOT touch:** the level-up `hp`/`stamina` reset branch (lines 497-503), `_fast_replace_entity`
/`_fast_replace_identity`, or any other patch class in `src/engine/patches.py`.
**Verify:** `test_apply_path_recomputes_combat_stats_from_active_breakthroughs`,
`test_apply_path_stats_dirty_triggers_on_breakthroughs_add_alone` (both new,
`tests/unit/core/test_rpg_depth.py::TestBreakthroughApplyIntegration`).

### Step 4 — Write the new unit and integration tests
**Files:** `tests/unit/progression/test_breakthroughs.py`, `tests/unit/core/test_rpg_depth.py`
**Change:** Add all 9 tests specified in `test_plan.md`'s "New Tests Required" section, exactly as
named and scoped there:
1. `test_apply_bonuses_iron_will_returns_spirit_wisdom_plus_two`
2. `test_apply_bonuses_sums_multiple_breakthrough_ids`
3. `test_apply_bonuses_empty_ids_returns_unchanged`
4. `test_apply_bonuses_unknown_id_returns_unchanged_no_raise`
5. `test_apply_bonuses_mixed_known_and_unknown_ids`
(all five above in `tests/unit/progression/test_breakthroughs.py`, alongside the existing
`test_breakthrough_addition`/`test_duplicate_breakthrough_suppression` — do not modify those two)
6. `test_get_effective_stats_applies_breakthrough_attribute_bonus` — uses `titan_grip`
   (strength+4 -> visible `atk` delta), **not** `iron_will`, because `recalculate_combat_stats`
   (`src/progression/leveling.py:99-103`, confirmed this session) never reads `spirit`/`wisdom`.
7. `test_get_effective_stats_no_breakthroughs_unchanged` — asserts `get_effective_stats(attrs)`,
   `get_effective_stats(attrs, active_breakthroughs=None)`, and
   `get_effective_stats(attrs, active_breakthroughs=set())` all produce identical output.
(6 and 7 in `tests/unit/core/test_rpg_depth.py::TestEffectiveStats`)
8. `test_apply_path_recomputes_combat_stats_from_active_breakthroughs` — construct the test entity
   with `identity.active_breakthroughs` already populated directly (e.g.
   `replace(entity.identity, active_breakthroughs={"titan_grip"})`, matching the existing pattern
   in `test_duplicate_breakthrough_suppression`), run through `ApplyPath.apply_generation`/
   `_apply_entity_update` with an update that makes `stats_dirty` True independent of
   breakthroughs (e.g. `learned_skills`), assert `combat.atk` reflects the +4 strength bonus vs.
   an equivalent entity with no active breakthroughs.
9. `test_apply_path_stats_dirty_triggers_on_breakthroughs_add_alone` — `EntityUpdate` with
   `IdentityUpdate(breakthroughs_add=["titan_grip"])` and nothing else, assert `combat.atk`
   reflects the bonus after apply.
(8 and 9 in `tests/unit/core/test_rpg_depth.py`, new class `TestBreakthroughApplyIntegration`)
**Do NOT touch:** `test_breakthrough_addition`, `test_duplicate_breakthrough_suppression`
(existing, must keep passing unmodified — they guard the out-of-scope `breakthroughs_add`
granting mechanic), any test in `tests/unit/progression/test_leveling.py` (must stay
bit-identical — guards against `recalculate_combat_stats` formula drift). Do not construct
`breakthroughs_add` via any real gameplay-granting code path in these tests — `active_breakthroughs`
must be set directly on the constructed test entity/state, per investigation Anti-Drift Hazards.
**Verify:** Run `pytest tests/unit/progression/test_breakthroughs.py
tests/unit/progression/test_leveling.py -v`, `pytest tests/unit/core/test_rpg_depth.py -v`, and
`pytest tests/unit/progression/ -v` — all must pass, including the pre-existing regression surface
listed in `test_plan.md`.

### Step 5 — Correct `docs/parity_ledger/progression.yaml` PROG-024
**Files:** `docs/parity_ledger/progression.yaml`
**Change:** PROG-024 (confirmed at lines 245-253 this session: `text:
'`test_breakthrough_applies_bonus`: Breakthrough applies bonus.'`, `status: verified`, `priority:
P0`, `v2_evidence: Implementation proven via exhaustive checklist audit Phase 1-11`, `test_path:
null`) currently asserts a passing test that does not exist. After Step 4 lands, update:
- `test_path`: set to the real test path,
  `tests/unit/progression/test_breakthroughs.py::test_apply_bonuses_iron_will_returns_spirit_wisdom_plus_two`
  (this is the test that most directly matches PROG-024's text — "Breakthrough applies bonus" —
  since it exercises `apply_bonuses` in isolation against the registry, per AC #1).
- `v2_evidence`: replace the generic "Implementation proven via exhaustive checklist audit Phase
  1-11" line with a concrete evidence string, e.g. `BreakthroughService.apply_bonuses
  (src/progression/breakthroughs.py) implemented; verified by
  tests/unit/progression/test_breakthroughs.py`.
- `status`: leave as `verified` only because the cited test now exists and passes (P0 entries
  require a passing `test_path` per project CLAUDE.md).
Other writers to `progression.yaml`: this is a static YAML file with no runtime/concurrent writer
— the only other agent that touches it is a human/agent editing the ledger directly, and no other
step in this plan or concurrent pipeline phase writes to it. No ordering concern.
**Do NOT touch:** PROG-023 (lines 235-243, shares the same false-`test_path` pattern but is
explicitly named as not-in-scope by the ticket's Related Docs/Scope — investigation flags it as a
"recommend Plan phase consider" item, not required; leave it for a future ticket) or PROG-003
(umbrella entry, no action needed per investigation).
**Verify:** No dedicated test for parity-ledger content in this ticket's test surface; verified by
inspection that the corrected `test_path` matches an actual passing test after Step 4, and that
the file remains valid YAML (parity ledger schema in `docs/parity_ledger/schema.json`).

### Step 6 — Add breakthroughs subsection to `docs/mechanics/01_entity_anatomy.md`
**Files:** `docs/mechanics/01_entity_anatomy.md`
**Change:** Confirmed this session: Section 5 "Progression & Growth" currently spans lines 87-104,
containing `### Experience (XP) Curve` (line 90) and `### Level Up Rewards` (line 96-102, ending
with the `Level 10: fireball` bullet at line 102), followed by a `---` separator at line 104 and
`## 6. Trauma: Wounds & Scars` at line 106. Insert a new `### Breakthroughs (Passive Perks)`
subsection immediately after `### Level Up Rewards`'s content (i.e. after line 102) and before the
`---` separator (line 104). Content: list each of the three `REGISTRY` entries
(`src/progression/breakthroughs.py:10-27`) by id/name/attribute_bonuses (`iron_will`: spirit+2,
wisdom+2; `fleet_foot`: agility+3, plus its non-attribute `evasion_flat: 0.05` bonus noted as a
distinct, separately-applied bonus type not yet wired into the effective-stats path; `titan_grip`:
strength+4), and state the application rule in prose: breakthrough attribute bonuses are summed
and applied to the entity's base `AttributeComponent` before combat-stat derivation (Section 2's
formulas), via `BreakthroughService.apply_bonuses`.
**Do NOT touch:** `### Experience (XP) Curve`, `### Level Up Rewards`'s existing content, Section
2 "Derived Combat Stats" (lines 32-57, formulas stay as documented — bonuses are applied upstream
of these formulas by adjusting attributes, not by changing the formulas), Section 6 "Trauma:
Wounds & Scars" (lines 106+), or the `WOUND_THRESHOLD_RATIO` divergence noted at
`docs/mechanics/01_entity_anatomy.md:106-113` vs. `src/engine/rpg_depth.py:112` — this is a
pre-existing, unrelated doc/code mismatch and must not be "fixed" while editing this file (per
investigation Anti-Drift Hazards).
**Verify:** No automated test for doc prose content; verified by inspection that the new
subsection accurately lists the `REGISTRY` contents and describes the Step 1/2 behavior
correctly, and that `fleet_foot`'s `evasion_flat` is explicitly marked as not-yet-wired (matches
Step 1's Scope Guard, avoids the doc overclaiming coverage this ticket does not implement).

## Scope Guards

- Do not implement `fleet_foot`'s `evasion_flat` bonus in any form — it targets a derived stat
  directly, not `AttributeComponent`, and is out of scope for this pass (investigation Risk #2).
  Only `fleet_foot`'s `attribute_bonuses.agility` portion flows through the normal `apply_bonuses`
  path.
- Do not construct `breakthroughs_add` anywhere in production/gameplay code. `IdentityUpdate`
  (`src/core/updates.py:229`) and `IdentityPatch` (`src/engine/patches.py:187,206,224`) are fully
  wired but the mechanism that actually grants a breakthrough during gameplay is explicitly out of
  scope per the ticket and per TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION's prior finding.
  Tests must set `active_breakthroughs` directly on constructed test state, never via a real
  granting code path.
- Do not change `LevelingService.recalculate_combat_stats`'s formulas (`src/progression/leveling.py:99-103`)
  to make `spirit`/`wisdom` feed `max_hp`/`atk`/`def_stat`/`evasion`/`move_cost`/`tactical_role`.
  This would be an undocumented mechanics change requiring its own Mechanics Bible update and
  parity-ledger changes to `stat_recalculation_parity` (currently `VERIFIED v2`) — far beyond
  "finish the stub."
- Do not touch `WOUND_THRESHOLD_RATIO` (documented as `0.25`/strict `>` in
  `docs/mechanics/01_entity_anatomy.md:106-113`, implemented as `0.40`/`>=` at
  `src/engine/rpg_depth.py:112`). This is a pre-existing, unrelated divergence noticed in passing;
  fixing it is out of scope and must not be bundled into this ticket's doc edit (Step 6) even
  though it is in the same file.
- Do not touch PROG-023 or PROG-003 in `docs/parity_ledger/progression.yaml` — only PROG-024 is in
  scope.
- Do not modify `IdentityPatch`, `extract_patches`, or any other patch class in
  `src/engine/patches.py` — the `active_breakthroughs` field and its patch-application logic are
  already correct and untouched by this ticket.
- Do not add a new durable-state field anywhere — `active_breakthroughs` already exists on
  `IdentityComponent` (`src/core/state.py:485`).

## Dependency Map

- Step 1 (implement `apply_bonuses`) has no dependency — can be implemented and unit-tested first.
- Step 2 (`get_effective_stats` parameter) depends on Step 1 (calls `BreakthroughService.apply_bonuses`).
- Step 3 (`apply.py` wiring) depends on Step 2 (calls `get_effective_stats` with the new parameter).
- Step 4 (tests) depends on Steps 1-3 being implemented; the five `test_breakthroughs.py` tests can
  be written/run as soon as Step 1 lands, the `test_rpg_depth.py::TestEffectiveStats` tests as soon
  as Step 2 lands, and `TestBreakthroughApplyIntegration` only after Step 3 lands. All are listed
  together in one step per test_plan.md's grouping but may be implemented incrementally alongside
  Steps 1-3 rather than strictly after.
- Step 5 (parity ledger) depends on Step 4 (needs a real passing test to cite as `test_path`).
- Step 6 (mechanics doc) depends only on Step 1 (documents the `REGISTRY` and the application
  rule); independent of Steps 2-5 and can be done any time after Step 1.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `apply_bonuses({'iron_will'}, base_attributes)` returns spirit+2/wisdom+2 matching REGISTRY | Step 1 | `test_apply_bonuses_iron_will_returns_spirit_wisdom_plus_two` |
| `apply_bonuses` correctly sums bonuses when multiple breakthrough_ids are passed | Step 1 | `test_apply_bonuses_sums_multiple_breakthrough_ids` |
| Empty/unknown id returns attributes unchanged with no raise | Step 1 | `test_apply_bonuses_empty_ids_returns_unchanged`, `test_apply_bonuses_unknown_id_returns_unchanged_no_raise`, `test_apply_bonuses_mixed_known_and_unknown_ids` |
| After wiring active_breakthroughs into the effective-stats recompute path, an entity with populated active_breakthroughs shows the bonus in recomputed combat stats | Steps 2, 3 | `test_get_effective_stats_applies_breakthrough_attribute_bonus`, `test_apply_path_recomputes_combat_stats_from_active_breakthroughs`, `test_apply_path_stats_dirty_triggers_on_breakthroughs_add_alone` |
| (Ticket Scope) Correct PROG-024 and add mechanics doc section | Steps 5, 6 | Manual inspection (no automated test for doc/ledger prose) |

## Anti-Drift Notes

- AC #4's integration test must use `titan_grip` (or `fleet_foot`'s `attribute_bonuses.agility`
  portion), never `iron_will` — `recalculate_combat_stats` never reads `spirit`/`wisdom`, so an
  `iron_will`-only integration assertion would be vacuous (investigation Risk #1). AC #1's exact
  spirit/wisdom-delta assertion stays a direct unit-level `apply_bonuses` call, not routed through
  `get_effective_stats`.
- The `stats_dirty` gap (Step 3, item 1) is not a separate bug fix outside scope — the ticket's own
  Scope bullet 3 ("Wire active_breakthroughs into the effective-stats recompute path... not just
  isolated calls") already covers it, and AC #4 cannot be satisfied end-to-end without it.
- Keep the `stats_dirty` extension a cheap truthiness check (`update.identity.breakthroughs_add`),
  not a set-difference or registry lookup — `_apply_entity_update_to_dict` is on the hot per-tick
  apply path per its own docstring ("Merged v5 logic... sub-100ms targets" per file header).
- `apply_bonuses` must stay a pure function: no `AuthoritativeState`/`EntityState` dependency, only
  `Set[str]` + `AttributeComponent` in, `AttributeComponent` out.
