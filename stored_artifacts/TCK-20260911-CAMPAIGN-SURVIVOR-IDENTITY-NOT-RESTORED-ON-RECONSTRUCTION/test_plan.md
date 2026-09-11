# Test Plan — TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION

## Unit tests (new)
1. `EntityCarryForward`'s new fields (`kind`, `role`, `faction`, `properties`, `traits`,
   `personality`) round-trip through `to_dict()`/`from_dict()`.
2. `_extract_entity_carry_forwards()` captures all six unconditionally (not gated by
   `carry_forward_rules`).
3. Reconstruction: a survivor built from a carry-forward snapshot with real, non-default values for
   all six fields produces an `EntityState` whose `kind`/`identity.role`/`.faction`/`.properties`/
   `.traits`/`.personality` match those carried values exactly.
4. **The actual equivalence claim, not a spot-check**: spawn a real entity via
   `ArchetypeEntityFactory.build_entity()` (or the real catalog path), extract its own carry-forward
   snapshot, reconstruct it, and assert the reconstructed entity's six identity fields equal the
   original spawned entity's — the literal governing invariant this ticket states.
5. `get_faction_id_str()` on a reconstructed survivor returns the survivor's real original faction
   string, not a uniform default — the confirmed downstream consumer this ticket's own audit found.

## Stall investigation (separate from the fix's own correctness)
- Real event-stream instrumentation (`_CollectingRecorder` pattern) on episode 1 (known: completes)
  and episode 2 (known: stalls at tick 52) BEFORE the identity fix, to characterize what's actually
  different between them beyond identity (event type mix, entity counts, any other signal).
- Same instrumentation AFTER the identity fix, recording which of the three outcomes occurred:
  fixed, still stalls, or changes shape — reported as a real, specific finding, not assumed.

## Regression
- `pytest tests/unit/domains/campaigns/` — must pass unchanged.
- `pytest tests/integration/campaigns/` — must pass unchanged.

## Acceptance-bar test (transferred from the predecessor ticket)
`tests/integration/campaigns/test_survivor_reconstruction_position.py`'s existing real 3-episode
run gets extended (or a sibling test added) to assert full episode completion now that identity is
fixed — reporting the real outcome (completes / still stalls / different signature) rather than
assuming which one occurs before running it.
