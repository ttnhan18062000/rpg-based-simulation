---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX

## Real fix: populate `combat_damage`'s `tactical_modifier` from `CombatUpdate.trace`

In `src/observability/event_shapers.py`'s `CombatShaper.shape()`, at the existing `combat_damage`
construction site (inside the `if hp_delta < 0 and real_combat is not None:` block), add a real
helper call that selects the first real tactical-modifier key present in `real_combat.trace`
(checked in mechanics-bible table order — see investigation.md), and include it in the payload as
`tactical_modifier` only when one is present (omit the key entirely otherwise — `CombatScorer`'s
own `if modifier and modifier not in self._seen_modifiers:` already handles `None`/absent
correctly, no need to send an empty placeholder).

```python
_TACTICAL_MODIFIER_ORDER = (
    "HIGH_GROUND", "FLANKING", "SURROUNDED", "COVER_REDUCTION",
    "SHATTER", "EXHAUSTION", "STAMINA_EXHAUSTION", "BOND_SYNERGY",
)

def _select_tactical_modifier(trace: dict) -> Optional[str]:
    for key in _TACTICAL_MODIFIER_ORDER:
        if key in trace:
            return key
    return None
```
Called once per `combat_damage` construction, real `trace = getattr(real_combat, "trace", None) or {}`.

## What is deliberately NOT touched
- `CombatResolutionSystem.calculate_tactical_multipliers()`'s own real modifier-computation logic
  — untouched, this fix reads its already-computed output only.
- `CombatScorer.score()`'s own scoring logic — already correct and ready.
- `REWARD_SOURCE`/`REWARD_CATEGORY`/`WOUND_INFLICTED`/`FINAL_ATK_MULT`/`FINAL_DEF_MULT` — real
  trace keys, deliberately excluded from `tactical_modifier` selection (not tactical conditions).
- `docs/mechanics/02_combat_laws.md`'s own missing `STAMINA_EXHAUSTION` row — confirmed not a
  real gap (already documented in `damage_formula_contract.md`), not touched.

## Rejected alternative
- **Building a brand-new, standalone "per-attack tactical trace" event type**: rejected in favor
  of reusing the already-designed, already-scored `combat_damage`/`tactical_modifier`/
  `tactical_variety` contract — the exact same reuse-over-invention precedent the sibling
  `TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX` established for `combat_resolved`. A new event
  type would duplicate real, existing scoring infrastructure for no added benefit.
- **Emitting all active modifiers, not just one**: rejected — `CombatScorer`'s own contract is a
  single string per event; changing the payload shape would require also changing the scorer
  (out of this ticket's own scope, and the scorer's own "first occurrence of each unique
  modifier" design intent doesn't obviously benefit from multi-modifier attribution per hit).

## Verification plan
1. Unit tests in `tests/unit/observability/test_event_shapers.py`: `tactical_modifier` populated
   correctly for a single active modifier; correct precedence when multiple are simultaneously
   active (mechanics-bible table order); absent (key omitted) when no real modifier is active.
2. Full scoped pytest: `tests/unit/observability/`, `tests/simulation_quality/test_combat_scorer.py`.
3. Real corpus re-verification (2000-tick, corpus-default flags, both worlds, all session combat
   fixes active): confirm `tactical_variety` fires at real, non-zero volume if the corpus's own
   real combat activity includes a tactically-modified attack; disclose honestly if not reachable
   at this scale (a real possibility given how rare real combat itself still is), matching this
   session's own established precedent for low-frequency events.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md re-confirms gap + trace field list | Done |
| Deterministic selection rule designed and justified | Done |
| combat_damage carries tactical_modifier | Implement phase |
| Docs corrected | Document-Update phase |
| Real corpus re-verification | Test phase |
| Scoped pytest passes | Test phase |
