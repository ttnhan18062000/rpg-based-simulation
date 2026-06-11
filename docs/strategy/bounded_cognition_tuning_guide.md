---
status: active
layer: strategy
authority: P1
audience: developer
---

# Tuning Guide: Bounded Strategic Cognition

## Numeric Ranges & Feel

### Intellectual Capacity (INT + WIS)
- **High (Hero/Sage)**: Budget 7-9. Can track multiple complex projects and dozens of leads. Rarely overloads.
- **Medium (Standard NPC)**: Budget 4-5. Can focus on a main goal and 1-2 side-concerns. Overloads if multiple threats emerge at once.
- **Low (Minion/Commoner)**: Budget 2-3. "Single-track" minds. Will drop leads to focus on immediate threats.

### Judgment Stability (WIS)
- **High**: 0.8 - 0.95. Extremely consistent. Will stick to long-term projects even during turmoil.
- **Low**: 0.2 - 0.4. Fickle. Abandons projects the moment a minor concern appears.

## Recommended Defaults (Common Archetypes)

| Archetype | INT | WIS | PER | CHA | Planning Budget | Stability | Slice Limit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Veteran Hero** | 12 | 10 | 11 | 10 | 8 | 0.85 | 8 |
| **Guard** | 8 | 8 | 10 | 8 | 5 | 0.65 | 5 |
| **Vagrant** | 6 | 4 | 8 | 5 | 3 | 0.35 | 3 |

## Troubleshooting & Failure Patterns

### "My NPCs are ignoring obvious world events."
- **Check**: `active_slice_limit` and `concern_intake_limit`.
- **Cause**: The NPC might be overloaded by high-priority internal motives, causing them to drop new world events.
- **Fix**: Increase INT/WIS or reduce the priority noise of their internal motives.

### "Entities are switching projects every 5 ticks."
- **Check**: `judgment_stability`.
- **Cause**: Low WIS coupled with high environmental volatility.
- **Fix**: Use `SimulationConfig.PROJECT_LOCK_TICKS` to force a cooldown, or increase WIS.

### "Replay summaries are missing cognitive data."
- **Check**: `AIBrain._strategic_appraisal_phase`.
- **Cause**: If the entity didn't perform a "strategic" tick (e.g. they were stunned or in a state that skips appraisal), no refresh was sent.
- **Fix**: This is expected behavior; cognitive state is only updated during active strategic thought.

## Rebalancing Safely
To change cognitive feel without breaking deterministic replay:
1.  **Attribute Caps**: High-level tuning should happen at the `Attribute` level.
2.  **Builder Constants**: Modify the exact formulas in `src/ai/cognition_capacity.py`.
3.  **REGRESSION PROOF**: Always run `pytest tests/ai/test_intel_capacity_regression.py` after a formula change to see how much the artifacts diverge.
