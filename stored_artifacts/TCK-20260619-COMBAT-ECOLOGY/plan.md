# Plan: TCK-20260619-COMBAT-ECOLOGY

## Steps

1. Add `combat_loss_counts: Dict[int, int]` to `SocialComponent` (frozen dataclass)
2. Add `combat_loss_delta: Dict[int, int]` to `SocialUpdate`; update `is_noop()` and `merge()`
3. In `combat.py::resolve_attack`, add `combat_loss_delta={attacker.id: 1}` to defender social_upd when `not alive`
4. In `relationships.py::process_update`, apply `combat_loss_delta` increments
5. In `builder.py::with_social_changes`, pass `combat_loss_counts`
6. In `state.py`, add `combat_loss_counts` to debug serialization
7. In `service.py::evaluate`, short-circuit with AVOID when `combat_loss_counts[target.id] >= 3`
8. Add parity ledger entries for combat_loss_counts + fear_avoidance

## Scope Guards
- Do NOT cross-episode persist (requires Epic 3.2)
- Do NOT change existing grudge accumulation logic
- Do NOT change posture for loss_count < 3
- `prune_low_salience` in relationships.py does NOT prune combat_loss_counts (it's not salience-gated)
