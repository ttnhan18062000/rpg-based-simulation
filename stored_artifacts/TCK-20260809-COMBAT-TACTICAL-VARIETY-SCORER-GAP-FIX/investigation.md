---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX

## Context search (mandatory step)
`search_docs` for the tactical-modifier trace surfaced `docs/mechanics/02_combat_laws.md` §2
(the summary modifier table) directly, plus `TCK-20260608-REWARD-TRACE-COVERAGE` (prior, related
work on `REWARD_SOURCE` trace coverage across `resolve_attack`/`resolve_multi_attack`/
`resolve_skill_usage`, confirming `trace` is an established, real concept with prior
investigation, not a novel idea this ticket introduces).

## Re-confirmed: `tactical_modifier` has zero real producers
`CombatScorer.score()`'s `combat_damage` handler (`src/simulation_quality/scorers/combat.py:
77-82`):
```python
if et == "combat_damage":
    modifier = payload.get("tactical_modifier")
    if modifier and modifier not in self._seen_modifiers:
        self._seen_modifiers.add(modifier)
        return _rec(self.weights["tactical_variety"], f"new tactical modifier: {modifier}", ("tactical_variety",))
    return None
```
A real, ready, already-designed "first occurrence of each unique modifier" discovery signal
(+1, `tactical_variety`). Direct grep of `"tactical_modifier"` across all of `src/` confirms
**zero real construction of this payload key anywhere** — `event_type_coverage.md`'s own
`combat_damage` row (§1.1) makes no mention of it either. The exact same class of gap as
`combat_resolved` (`TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX`, same session): a real, ready
scorer handler, permanently dead for lack of a producer.

## Re-confirmed: the real trace data already exists, computed every attack, discarded
`CombatResolutionSystem.calculate_tactical_multipliers()` (`src/engine/combat.py:52-107`)
computes a real `trace: Dict[str, float]` on every single attack resolution:
`HIGH_GROUND` (+0.20 atk), `FLANKING` (+0.15 atk), `SURROUNDED` (+0.25 atk), `COVER_REDUCTION`
(+0.30 def), `SHATTER` (×1.5 atk), `EXHAUSTION` (×0.8 atk), `STAMINA_EXHAUSTION` (a real,
separately-computed multiplicative penalty — see below), `BOND_SYNERGY` (+0.10 atk). This dict is
stored on `CombatUpdate.trace` (returned from `resolve_attack`) but never read anywhere in
`src/observability/` (confirmed via grep) — the exact "computed but discarded" data this whole
investigation thread traces back to.

Two additional real trace keys, also computed but not "tactical modifiers" in the mechanics-bible
sense: `FINAL_ATK_MULT`/`FINAL_DEF_MULT` (aggregate final multipliers, not a discrete condition),
`REWARD_SOURCE`/`REWARD_CATEGORY` (reward classification, already the subject of the prior,
separate `TCK-20260608-REWARD-TRACE-COVERAGE` investigation), `WOUND_INFLICTED` (wound tracking).
All 5 excluded from `tactical_modifier` selection — confirmed not real tactical conditions per
the mechanics bible's own definition.

## `STAMINA_EXHAUSTION` missing from `02_combat_laws.md`'s own table — confirmed NOT a real gap
`docs/mechanics/02_combat_laws.md` §2's own table lists 7 modifiers but omits
`STAMINA_EXHAUSTION`. Checked `docs/mechanics/damage_formula_contract.md` (the more detailed,
authoritative damage-formula doc) — it **does** document Stamina Exhaustion in full (line 74,
line 193's compounding example, line 248's source citation). `02_combat_laws.md` §2 is a
summary table, not the sole source of truth; this is not a real, unfixed documentation gap —
confirmed, not pursued further.

## Real selection rule for `tactical_modifier` (multiple simultaneously-active modifiers)
A single attack can have more than one real modifier active (e.g. `HIGH_GROUND` + `FLANKING`
simultaneously). `CombatScorer`'s own contract expects a single string per `combat_damage` event.
Chosen rule: **select the first real tactical-modifier key present in `combat_upd.trace`, checked
in the mechanics bible's own documented table order** (`HIGH_GROUND`, `FLANKING`, `SURROUNDED`,
`COVER_REDUCTION`, `SHATTER`, `EXHAUSTION`, `STAMINA_EXHAUSTION`, `BOND_SYNERGY`) — deterministic,
traceable directly to the mechanics bible's own real ordering, not an arbitrary dict-iteration-
order dependency (Python dict insertion order in `calculate_tactical_multipliers()` happens to
match this same order today, but pinning to the mechanics-bible table explicitly is more robust
against future reordering of the trace-computation code itself).

## Docs Requiring Update
- `docs/simulation_quality/event_type_coverage.md` §1.1 — `combat_damage`'s own row gets a note
  on the new `tactical_modifier` field and its `tactical_variety` scoring consequence.
- `docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT — add a real producer citation
  next to the `tactical_variety` row, matching the `combat_resolved` sibling ticket's own pattern.
