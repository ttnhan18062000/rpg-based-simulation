# Investigation — TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS

## Key findings

- `tactical.py` hostile loop: lines ~138–160; dist computed per-neighbor; insertion point before `semantics_service.is_hostile_compat()`
- `target_score()` closure at line ~298; captures all enclosing scope variables
- `entity_pressures` resolved before hostile loop; available to closure without extra resolution
- `disciplined_protector` drive: duty=high, safety=medium (0.6) — does NOT trigger safety_pressure retreat (threshold 0.75)
- `cautious_commoner` drive: safety=high (0.9) — confirms safety_pressure retreat trigger
- All existing tactical tests use entities at distance ≤ 10 with default signals (visibility=medium) — perception gate passes for all at neighbor radius
