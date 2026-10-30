---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261028-EVENT-EXTRACTOR-SPLIT-BY-DOMAIN
phase: done
date: 2026-10-28
tags: [observability]
---

# TCK-20261028-EVENT-EXTRACTOR-SPLIT-BY-DOMAIN

## Title
Split EventExtractor.extract into one function per event domain in src/observability/extraction/, with the emitted event stream byte-identical

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
This is the M7 refactor lane, batch 2, ticket 2 of 2 (see SEQUENCE.md). `EventExtractor.extract` is 1,581 lines in one static method. The package registry lists `src/observability/event_extractor.py` under `do_not_imitate` for exactly that, and the file carries 15 code-health exceptions, including function-length, cognitive-complexity, C901, PLR0912/0915, class-length, module-length and duplicate-block.

This ticket splits the method by event domain. It is a pure move: nothing that is emitted changes, and nothing about when or in what order it is emitted changes.

## Scope
1. **The new subpackage `src/observability/extraction/`**, with one module per event domain found in `extract()`. Name the modules from the investigation, for example lifecycle, combat, economy, movement and routing, strategy and leads, social, contracts, progression and capability, resources, faction, and world events.
   - Each module exposes plain functions that take an explicit, read-only context and return a `list[SimulationEvent]`.
   - The context is a small frozen dataclass: `prior_state`, `current_state`, `update`, `mode`, `tick`, `now`, and the four resolved flag booleans.
   - The functions do not mutate state other than the per-run emit-once collections they already use.
2. **The facade.** `src/observability/event_extractor.py` keeps:
   - `EventExtractor`, with the same `extract()` signature and docstring meaning;
   - `reset_run_state()`;
   - the class-level per-run collections and constants, which tests and the domain functions reference as `EventExtractor._…`.

   `extract()` becomes:
   - resolve the flags once;
   - for each dirty entity, call the per-entity domain functions in the **same order** the blocks run today;
   - then call the world-level functions in their current order;
   - concatenate the results.

   `_real_combat_update` moves or is re-exported so that its current importers keep working.
3. **The emitted literals do not change.** That covers `source_system="event_extractor"`, every `event_type` and `event_category`, every payload key, and `timestamp=now`, taken once per `extract()` call as today. Every flag-gated rollback branch keeps its flag and its default.
4. **Local imports move to module top** where import cycles allow. Check each with `lint-imports` and `make code-health`, because new local imports fail ruff PLC0415.
5. **Baselines ratchet down only.**
   - Remove the code-health exceptions this resolves, using the tighten or sync commands in `codebase/`, and do not hand-edit them.
   - Drop the mypy and pyrefly entries that disappear. No new entry is allowed for the new modules: they type-check clean or the ticket is not done.
   - Update the `observability` package-registry `do_not_imitate` reason, or remove it if no function in the subpackage exceeds the standard's function-length limit.

## Out of Scope
- **Any change to an event's shape, content, order or flag behavior.** If something looks wrong, record it and tell codebase-planner, who routes it to rpg-planner.
- **Removing the `ENABLE_PUSH_EVENT_SHAPERS*` rollback branches.** That is a behavior decision for rpg-planner, outside this batch.
- **The private import `_MAX_CONSECUTIVE_REJECTIONS`** from `src/systems/strategic_systems/intelligence.py` (the `n3-private-name-import` exception). It stays: `intelligence.py` is rpg's file, and rpg-planner noted that it names `event_extractor`'s contract.
- `event_shapers.py`, `event_recorder.py` and `kernel.py`.

## Acceptance Criteria
1. Ticket 1's fixtures are byte-identical at this ticket's head: all 5 flag configurations and all modes, with `git diff` empty under `tests/fixtures/` for those files. The ticket 1 tests and the targeted unit tests pass unchanged.
2. **Pure-run digest (rpg's condition).** Run one short seeded run before (origin/main after #779) and after (the head). The event logs (`event_type`, `event_category`, entity, payload, ignoring `timestamp`) are identical, and so is the run digest. Record the command and both digests in test_plan.md.
3. No function in `src/observability/extraction/` or in `event_extractor.py` exceeds the standard's function-length and complexity limits, with no new exception added.
4. Code health reports 0 new and 0 worse, with the event_extractor exceptions reduced; list old→new. The mypy and pyrefly baselines don't grow. `lint-imports` and `tests/codebase` pass.
5. These pass, using the same command CI runs for each job they belong to:
   - `pytest tests/unit/observability`;
   - every existing test that imports `EventExtractor`;
   - `tests/architecture`;
   - the determinism and replay suites named in roadmap section 9.
6. `graphify update .` has been run, from the main checkout after merge (worktrees don't write the graph). The Files Changed section lists the new modules.

## Related Tickets
- Prev: `TCK-20261028-EVENT-EXTRACTOR-CHARACTERIZATION-TESTS`
- Pattern: `TCK-20261024-API-SERVER-INLINE-ROUTES-TO-ROUTERS` (M7 batch 1)

## Related Docs
- `docs/plans/codebase_health/python_code_craft_roadmap.md` (the M7 row, section 9)
- `docs/guidelines/python_code_standard.md`
- `docs/guides/observability.md`, if it names `event_extractor` internals

## Related Stored Artifacts
- none

## Related Code Areas
- `src/observability/event_extractor.py`, and the new `src/observability/extraction/`
- `codebase/baselines/code_health_exceptions.jsonl`, `mypy_baseline.txt`, `pyrefly_baseline.json`
- `codebase/structure/package_registry.jsonl` (the observability entry)

## Assumptions / Open Questions
- Resolved: a subpackage under `src/observability/` needs no registry entry; `tests/codebase` (519 passed) and `lint-imports` (17 kept, 0 broken) agree. The package registry's `do_not_imitate` entry for `event_extractor.py` was removed, since no function is over the limit now.
- The phase18 allowlist (pinned by `tests/architecture`) lets only `event_extractor.py` import `src.domains`, and it was not widened. The world-event loop and `commitment_abandoned` therefore stay in `event_extractor.py`; `quests.py` reaches the latter through `ctx.abandonment_events`.
- A subpackage under `src/observability/` needs no new package-registry entry, because the registry is per top-level package. Confirm this with `tests/codebase/test_package_registry.py` and the import-linter layers contract.
- If keeping block order needs a per-entity sequence that interleaves domains, keep that interleaving. Order is behavior.

## Implementation Notes
See staging artifacts `plan.md`, `investigation.md`, `test_plan.md`. Function bodies are the original text of each block, moved by line range with three mechanical renames. 14 modules plus `context.py` and `entity.py` in `src/observability/extraction/`; the longest function is 58 lines. The `threat_evolved` silent `except ... pass` now logs at debug level so that the new module adds no e3-silent-except row. Three tests that read the extractor's source text, and about 36 parity-ledger `v2_evidence` paths (via `parity_ledger_writer.py`), were re-pointed to the new modules.

## Test Summary
- Ticket 1's goldens unchanged (`git diff origin/main -- tests/fixtures` shows only ticket 1's own new files, none modified after commit); characterization tests: 12 passed. Event lines before/after on the corpus (1,360,042 bytes) are byte-identical; so are both kernel-scenario digests.
- AC5: `tests/unit/observability` + 15 other files that import EventExtractor + `tests/architecture`: 1543 passed, 83 skipped. Determinism and replay suites: 46 passed. `tests/codebase`: 519 passed.
- `tests/unit/worldassembly/test_corpus_diversity.py` (score-anchor drift under 3 ids) fails identically on a clean `git archive` of origin/main de5a223ca, so it is not caused by this change.
- Guard-test probes (6): all behave as required (see test_plan.md).
- Code health OK (13 event_extractor rows removed), mypy 0 new (16 rows removed), pyrefly nothing new (10 rows removed), parity schema 0 rose / 0 new.

## Files Changed
New: `src/observability/extraction/{__init__,context,entity,lifecycle,vitals,combat,progression,economy,strategy,leads,social,contracts,quests,capability,resources,world,faction}.py`, `tests/helpers/event_extractor_source.py`.
Edited: `src/observability/event_extractor.py` (now the facade), the three source-text guard tests, `docs/guides/observability.md`, nine `docs/parity_ledger/*.yaml` shards (v2_evidence only), `codebase/baselines/{code_health_exceptions.jsonl,mypy_baseline.txt,pyrefly_baseline.json}`, `codebase/structure/package_registry.jsonl`.

## Completion Summary
`EventExtractor.extract` is split into per-domain functions under `src/observability/extraction/`; every emitted event is unchanged.
