---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER
phase: open
date: 2026-10-09
tags: [testing, determinism]
---

# TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER

## Title
One shared test helper pins the governor to NORMAL, replaces the four local copies, and a guard test stops a fifth

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Tests that run a real `Kernel` over a compiled world are timing-dependent unless they pin the `ResourceGovernor` to `RuntimeMode.NORMAL` (with a no-op `force_mode`, so the mid-tick wall-clock throttle cannot flip it) and use `LocalSequentialExecutor`. Without the pin, identical code gives different outcomes depending on host speed (latest case: `test_defeat_deaths_are_recorded_in_unscripted_corpus_play` read 0, 1 or 2 DEFEAT deaths across runs on main 28e29ed2e). Each fix so far copied the same private `_PinnedNormalGovernor` class into its own file. After PR #457 there are four copies. Filed by testing-planner; the owner approved the work on 2026-10-09.

Copies, all identical in intent (`_get_indicated_mode` returns `RuntimeMode.NORMAL`, `force_mode` returns `None`):
1. `tests/unit/world/test_resource_regrowth_wiring.py:21`
2. `tests/integration/lab/test_species_relations_metamorphic_validation.py:117` (installed via `monkeypatch.setattr(governor_module, "ResourceGovernor", ...)`)
3. `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py:132`
4. `tests/mechanic_scenarios/test_entity_death_authority_boundary.py` (added by PR #457, with a local `_pinned_kernel` factory that also lifts `max_tick_budget_ms`)

## Scope
1. A new module `tests/helpers/kernel_pinning.py` (or a name that fits `tests/helpers/` better) exporting:
   - `PinnedNormalGovernor(ResourceGovernor)`: `_get_indicated_mode` returns `RuntimeMode.NORMAL`; `force_mode` is a no-op. Its docstring says why (host-speed independence; the wall-clock throttle) and names this ticket.
   - Optionally, a small factory for the common kernel shape (pinned governor, `LocalSequentialExecutor`, an effectively unlimited `max_tick_budget_ms`). Add it only if at least two of the four call sites can use it without changing what they run. Each call site keeps its own profile, flags, rng and seed.
2. Replace the four local copies with imports of the shared helper. Each test keeps its exact assertions, world, seed, tick count, flags and executor. The only change is where the class comes from. Copy 2 keeps its `monkeypatch` installation and only swaps in the shared class.
3. A guard test in `tests/architecture/` (testing-owned): an AST scan of `tests/**/*.py` outside `tests/helpers/` that fails if a class subclasses `ResourceGovernor` (by name or as `governor_module.ResourceGovernor`) **and** has an `_get_indicated_mode` whose body is a single `return RuntimeMode.NORMAL` **and** a `force_mode` whose body is a bare `return None`, `return` or `pass`. The failure message names the file and points to the shared helper. Overrides with a different purpose must not match:
   - `tests/integration/world/test_camp_raid_targeting.py` pins `DEGRADED`;
   - `tests/integration/kernel/test_tick_budget_report_only.py` records `force_mode` calls and calls `super()`.
   The guard's own unit tests include one positive fixture (a copy that must be flagged) and those two negatives.

## Out of Scope
- Changing what any of these tests assert, or their worlds, seeds, tick counts or lanes.
- Pinning tests that are not pinned today. A sweep for other unpinned corpus `Kernel` runs is a separate question; list any you notice under Assumptions / Open Questions, do not fix them here.
- `src/engine/governor.py` or any `src/**` change (no production test hook).
- The two non-matching overrides above.

## Acceptance Criteria
1. `tests/helpers/` exports the shared `PinnedNormalGovernor`; no file outside `tests/helpers/` defines an equivalent class (checked by AC3's guard).
2. All four former copy sites import it, and each of their test files passes three times in a row at the new head, with the same pass/fail and the same asserted values as before the change (record the before/after commands and results in the test summary).
3. The guard test in `tests/architecture/` passes on the new head, and fails on a fixture that reintroduces a local copy. The positive and both negative fixtures are covered.
4. No diff under `src/`. No assertion, seed, tick count or world id changed in the four files (a reviewer can check this from the diff).
5. Standard close: ticket, staging artifacts, working-log row, monitoring records.

## Related Tickets
- TCK-20261006-TWO-WORLD-INTEGRATION-TESTS-FAIL-ON-MAIN-PH9-ASSERTS-A-BOSS-AND-TRAUMA-LONG-RUN-HITS-THE-60S-LIMIT (closed by PR #457; same batch added copy 4)
- TCK-20261008-SERVICE-LOOKUP-CRASHES-UNDER-THE-CONCURRENT-EXECUTOR-WORKERPACKET-HAS-NO-BUILDING-TILES (PR #457; the unpinned executor path is where that crash hides)

## Related Docs
- `docs/plans/test_architecture/` (roadmap, testing-planner)
- `docs/testing/test_taxonomy.md`
- `docs/engine/kernel.md` (governor and executor roles in the tick loop)

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/helpers/` (new module)
- The four files listed in Request Summary
- `tests/architecture/` (new guard test)
- `src/engine/governor.py` (read only: `ResourceGovernor._get_indicated_mode`, `force_mode`)
- `src/engine/executor.py` (read only: `LocalSequentialExecutor`)

## Assumptions / Open Questions
- **Start after PR #457 merges**: copy 4 exists only on that branch. Starting earlier means a conflict in `test_entity_death_authority_boundary.py`.
- Path ownership: `tests/**` outside `tests/architecture/` and `tests/mutation/` is rpg-owned by path. testing-planner asked rpg-planner on 2026-10-09 to agree to this test-infrastructure change. **ACK received 2026-10-09 from rpg-planner**: testing-implementer does all of it (helper, the 4 import switches, the guard), after #457 merges. Only #457 touches one of the four files, and Lane B's earning batch touches none. Conditions: the helper behaves identically to the local copies (same mode pin, same executor and budget arguments the tests pass), so no digest or count moves; each of the four files is run 3 times at the new head with identical results; and rpg-planner reviews the rpg-path side of the PR.
- Whether the guard should also catch a pinned governor written inline (for example a lambda or `types.MethodType` patch) is left to the implementer. Match only the class form unless another form actually exists in the tree.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
