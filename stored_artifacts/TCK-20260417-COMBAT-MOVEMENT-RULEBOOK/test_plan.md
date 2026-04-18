# Test Plan: Combat and Movement Milestone 1

## Rule-Contract Tests
- [ ] Manhattan Distance: Verify `Vector2.manhattan` for cardinal and diagonal positions.
- [ ] Adjacency: Verify orthodox adjacency (North, South, East, West) results in `dist == 1`.
- [ ] Occupancy: Verify `world.is_occupied` correctly reflects entity presence.
- [ ] AoE Legality:
    - [ ] Target center within range.
    - [ ] LOS to center.
    - [ ] Splash radius (Manhattan) covers correct tiles.

## Lifecycle and Time Model Tests
- [ ] Readiness Turns: Entities only act when `tick >= next_act_at`.
- [ ] World-Time Progression: Passive systems (e.g. status effect decay) advance even when no entity acts.
- [ ] Determinism: Repeated identical ticks produce exact same results.

## Regression Tests
- [ ] Existing units tests for combat and movement should remain passing or be explicitly updated to match the new rules.
