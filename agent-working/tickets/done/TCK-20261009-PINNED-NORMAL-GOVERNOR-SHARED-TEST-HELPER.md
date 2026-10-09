---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER
phase: done
date: 2026-10-09
tags: [testing, determinism]
---

# TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER

## Title
One shared test helper pins the governor to NORMAL, replaces the local copies (four named at filing, a fifth found by the guard), and a guard test stops a sixth

## Status
DONE

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
5. Found by the guard test on 2026-10-09, not named at filing: `tests/mechanic_scenarios/test_decision32_notice_and_decide.py` `_Pin` (also added by PR #457; identical body). Switched to the shared helper (testing-planner: in the spirit of the scope; rpg-planner ACKED 2026-10-09: same pin, same Kernel args, no rebase risk since neither rpg batch 2 nor the hunting branch touches that file).

## Scope
1. A new module `tests/helpers/kernel_pinning.py` (or a name that fits `tests/helpers/` better) exporting:
   - `PinnedNormalGovernor(ResourceGovernor)`: `_get_indicated_mode` returns `RuntimeMode.NORMAL`; `force_mode` is a no-op. Its docstring says why (host-speed independence; the wall-clock throttle) and names this ticket.
   - Optionally, a small factory for the common kernel shape (pinned governor, `LocalSequentialExecutor`, an effectively unlimited `max_tick_budget_ms`). Add it only if at least two of the four call sites can use it without changing what they run. Each call site keeps its own profile, flags, rng and seed.
2. Replace the local copies (the four above plus copy 5) with imports of the shared helper. Each test keeps its exact assertions, world, seed, tick count, flags and executor. The only change is where the class comes from. Copy 2 keeps its `monkeypatch` installation and only swaps in the shared class.
3. **Two unpinned CONFLICT-04 kernels (added 2026-10-09, rpg-planner ack):** `tests/mechanic_scenarios/test_conflict04_movement_layer.py` `_kernel()` (line ~47) and `tests/mechanic_scenarios/test_conflict04_fighter_holds_between_blows.py` (the `Kernel(...)` at line ~94) pin the executor and lift the tick budget, but leave the governor at its default. Pass `governor=PinnedNormalGovernor()` from the shared helper; change nothing else. Observed: the movement-layer invariant tests (`test_invariant_no_step_with_an_engaged_adjacent_hostile_on_a_tick_without_a_decision`, `test_invariant_no_entity_stays_blocked_by_the_rule_for_more_than_one_brain_cadence_plus_one`) go red in a parallel (xdist) run and green alone, on main edda25490 (rpg-implementer-2). Hypothesis: under CPU contention the default governor changes mode or throttles, which changes brain cadence. Also check the second suspect: `test_the_invariant_predicate_...` calls the process-global `configure_behavior_consumers()`/`reset_behavior_consumers()`. If another test in the same xdist worker leaves that global in a state that changes these runs, isolate it with a fixture (in this file, or a conftest under `tests/mechanic_scenarios/`) and record the finding.
4. A guard test in `tests/architecture/` (testing-owned): an AST scan of `tests/**/*.py` outside `tests/helpers/` that fails if a class subclasses `ResourceGovernor` (by name or as `governor_module.ResourceGovernor`) **and** has an `_get_indicated_mode` whose body is a single `return RuntimeMode.NORMAL` **and** a `force_mode` whose body is a bare `return None`, `return` or `pass`. The failure message names the file and points to the shared helper. Overrides with a different purpose must not match:
   - `tests/integration/world/test_camp_raid_targeting.py` pins `DEGRADED`;
   - `tests/integration/kernel/test_tick_budget_report_only.py` records `force_mode` calls and calls `super()`.
   The guard's own unit tests include one positive fixture (a copy that must be flagged) and those two negatives.

## Out of Scope
- Changing what any of these tests assert, or their worlds, seeds, tick counts or lanes.
- Pinning tests that are not pinned today, except the two CONFLICT-04 kernels in Scope 3. A sweep for other unpinned corpus `Kernel` runs is a separate question; list any you notice under Assumptions / Open Questions, do not fix them here.
- `src/engine/governor.py` or any `src/**` change (no production test hook).
- The two non-matching overrides above.

## Acceptance Criteria
1. `tests/helpers/` exports the shared `PinnedNormalGovernor`; no file outside `tests/helpers/` defines an equivalent class (checked by AC3's guard).
2a. The two CONFLICT-04 kernels pass the shared governor. Run `pytest -n auto tests/mechanic_scenarios/test_conflict04_movement_layer.py tests/mechanic_scenarios/test_conflict04_fighter_holds_between_blows.py` (with enough other tests in the session to create the contention, for example all of `tests/mechanic_scenarios`) 3 times before and 3 times after. Record red-before and green-after. If it is not red before, or still red after, the hypothesis is wrong: record what you found instead and report to testing-planner before closing. Record the behaviour-consumers check result too.
2. All five former copy sites import it, and each of their test files passes three times in a row at the new head, with the same pass/fail and the same asserted values as before the change (record the before/after commands and results in the test summary).
3. The guard test in `tests/architecture/` passes on the new head, and fails on a fixture that reintroduces a local copy. The positive and both negative fixtures are covered.
4. No diff under `src/`. No assertion, seed, tick count or world id changed in the seven files (a reviewer can check this from the diff).
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
- **Order-dependent strict xfail (found 2026-10-09, not fixed here, identical before and after):** `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py::test_real_campaign_episode_makes_deliberate_attacks` is a strict xfail. Alone (`pytest <file>::test_real_campaign_episode_makes_deliberate_attacks`) it XFAILs; with its whole file (`pytest tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`) it XPASS(strict) and counts as FAILED, 3 of 3 runs on main before any change and 3 of 3 after. To route to rpg-planner.
- pytest-xdist is not in the shared venv; not added here.
- **CONFLICT-04 overlap (rpg-planner, 2026-10-09):** rpg batch 2 (rpg-implementer-2, local d0ff978eb, unpushed) also edits both CONFLICT-04 files: the import line and the `_stage(compile_world(...))` calls, wrapped in `empty_inventories`. It does not touch the `Kernel(...)`/`_kernel()` hunks, so the merge should be textual only. Whichever lands second rebases. Do not ask batch 2 to add the pin.
- **Start after PR #457 merges** (MET: edda25490): copy 4 exists only on that branch. Starting earlier means a conflict in `test_entity_death_authority_boundary.py`.
- Path ownership: `tests/**` outside `tests/architecture/` and `tests/mutation/` is rpg-owned by path. testing-planner asked rpg-planner on 2026-10-09 to agree to this test-infrastructure change. **ACK received 2026-10-09 from rpg-planner**: testing-implementer does all of it (helper, the 4 import switches, the guard), after #457 merges. Only #457 touches one of the four files, and Lane B's earning batch touches none. Conditions: the helper behaves identically to the local copies (same mode pin, same executor and budget arguments the tests pass), so no digest or count moves; each of the four files is run 3 times at the new head with identical results; and rpg-planner reviews the rpg-path side of the PR.
- Whether the guard should also catch a pinned governor written inline (for example a lambda or `types.MethodType` patch) is left to the implementer. Match only the class form unless another form actually exists in the tree.

## Implementation Notes
- New `tests/helpers/kernel_pinning.py::PinnedNormalGovernor` (identical body to the local copies; docstring names this ticket). The optional factory was NOT added: the call sites differ in profile, flags, rng and executor, so no two could share one without changing what they run.
- Five local copies now import it: regrowth, species-relations (its `monkeypatch.setattr(governor_module, "ResourceGovernor", PinnedNormalGovernor)` is kept), catalog-spawn, entity-death-authority (its `_pinned_kernel` kept), and decision32 `_Pin` (copy 5). The two CONFLICT-04 kernels now pass `governor=PinnedNormalGovernor()`; nothing else changed in them.
- Guard: `tests/architecture/test_no_local_pinned_governor_copies.py` (AST, class form only; no inline form exists in the tree). It found copy 5 on its first run, which is evidence that it works. Its unit fixtures: 2 positives (Name base; module-attribute base with a `pass` body), 3 negatives (DEGRADED pin, recording `force_mode` with `super()`, a non-governor class), plus a check that the two real negative files stay unflagged and the shared helper is the only match.
- Unused `RuntimeMode`/`ResourceGovernor` imports removed from the files whose local class went away (the species file keeps `ResourceGovernor` as a monkeypatch string and `governor_module`).

## Test Summary
Commands: `../behavioral-5k-impl2/.venv/bin/python -m pytest <files> -q -p no:cacheprovider`; xdist from a scratchpad install (`pip install --target`, `PYTHONPATH`), not added to the shared venv.
- Before (main + #457), 3 runs: regrowth + species-relations + entity-death-authority: 8 passed each (267-381 s). catalog-spawn file: 10 passed, 1 failed each (strict XPASS, see Open Questions). `-n auto tests/mechanic_scenarios` (6 cores): 114 passed each (83-88 s).
- After (this head), 3 runs: the same three files: 8 passed each (264-309 s). catalog-spawn file: 10 passed, 1 failed each, the same test, same reason. `-n auto tests/mechanic_scenarios`: 114 passed each (55-62 s). Guard file: 7 passed. decision32 file: passes.
- AC2a (corrected 2026-10-09 per rpg-planner's code read): NOT red before on a 6-core host (`-n auto`, 3 runs, 114 passed each). The tests are governor-mode-sensitive: with scratch copies of the two unpinned CONFLICT-04 files and a governor subclass pinned per RuntimeMode with a no-op `force_mode` (scratch files deleted), NORMAL 9 passed; CONSTRAINED 1 failed (`test_cp_s19_control_pair_two_tiles_apart_gets_the_stalemate_break`); DEGRADED 4 failed (`test_control_the_same_walker_without_an_adjacent_hostile_walks_its_stored_target`, `test_invariant_no_entity_stays_blocked_by_the_rule_for_more_than_one_brain_cadence_plus_one`, `test_cp_s18_control_cautious_fighter_leaves_and_pays_the_opportunity_attack`, `test_cp_s19_control_pair_two_tiles_apart_gets_the_stalemate_break`); SURVIVAL 5 failed (those four plus `test_cp_s18_main_non_cautious_fighter_holds_between_blows`). The pin makes that sensitivity explicit and harmless, but both kernels pass `audit_mode=True`, under which the Kernel uses `ZeroedSignalSource` (`src/engine/signal_source.py:101-118`), so the governor already stays NORMAL and the pin is redundant there. The cause of the reported xdist red is OPEN; this ticket does not claim the pin fixes it.
- `configure_behavior_consumers` / `reset_behavior_consumers` check (process-global state in `src/engine/behavior_consumers.py`: `_catalog`, `_perception_gate`, `_pressure_resolver`): in `test_conflict04_movement_layer.py` the predicate test configures and resets inside `try/finally`, so this file does not leak its catalog. `reset` sets the globals to None rather than restoring a previous value, and the next consumer rebuilds them via `_auto_init()` from the same `data/content` catalog, so the visible state after reset equals the default. The other 9 test files that call `configure_behavior_consumers` each pair it with one `reset_behavior_consumers()` (8 via a fixture, 1 via `try/finally`). No leak found by reading; the process-global state remains a suspect for the xdist red but is NOT confirmed (no repro to test against). No isolation fixture added.

## Files Changed
- new: `tests/helpers/kernel_pinning.py`, `tests/architecture/test_no_local_pinned_governor_copies.py`
- imports switched: `tests/unit/world/test_resource_regrowth_wiring.py`, `tests/integration/lab/test_species_relations_metamorphic_validation.py`, `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`, `tests/mechanic_scenarios/test_entity_death_authority_boundary.py`, `tests/mechanic_scenarios/test_decision32_notice_and_decide.py`
- governor passed: `tests/mechanic_scenarios/test_conflict04_movement_layer.py`, `tests/mechanic_scenarios/test_conflict04_fighter_holds_between_blows.py`
- no diff under `src/`

## Completion Summary
Merged as PR #462 (2026-10-09). One shared `PinnedNormalGovernor` in `tests/helpers/kernel_pinning.py` replaces five local copies (four named at filing plus `test_decision32_notice_and_decide.py::_Pin`, found by the new guard), the two CONFLICT-04 kernels pass it, and `tests/architecture/test_no_local_pinned_governor_copies.py` flags any further copy. Behaviour identical before and after (3 runs each). AC2a: the xdist red was not reproduced before; the CONFLICT-04 tests are governor-mode-sensitive but both kernels run with `audit_mode=True`, so the pin is redundant there and the cause of the reported red is open (the order-dependent strict xfail and the behaviour-consumers globals are recorded under Open Questions for rpg-planner). Gap stated: the pin is not claimed to fix any flake.
