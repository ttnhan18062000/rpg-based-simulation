---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261028-EVENT-EXTRACTOR-SPLIT-BY-DOMAIN
artifact_type: test_plan
tags: [observability]
---

# Test plan
All numbers are from this worktree at the commit that closes the ticket; origin/main is de5a223ca.

1. Ticket 1's goldens unchanged: `git diff origin/main -- tests/fixtures/` is empty for the two fixtures and `tests/unit/observability/test_event_extractor_characterization.py` passes (10 tests, includes the two-seed check).
2. Event-log diff before/after on the corpus and two seeded kernel runs, recorded at the `extract()` call with `EXTRACTOR_RECORD_FULL`:
   `PYTHONHASHSEED=0 python -m pytest -p tests.unit.observability.extractor_characterization.recorder_plugin ... tests/unit/observability/test_event_extractor_*.py` (with the corpus `--deselect`/`-k`) at the pre-split commit and at the head: the full-line file (1,360,042 bytes, every event of 371 calls under 8 configs) is byte-identical (`cmp`), and so are the per-tick digests of `lifecycle_full_coverage_world` seed 42 and `dungeon_crawl` seed 42, 200 ticks each (`python -m tests.unit.observability.extractor_characterization.kernel_scenario <world> 42 200`, 400 ticks x 8 configs).
3. Code health: `make code-health` OK, 0 worse. Event_extractor rows removed (13): module-length, class-length, function-length, cognitive-complexity (776), ruff C901/D100/F401/I001/N806/PLR0912/PLR0915, e3-silent-except, jscpd. Kept: PLC0415 (the Kernel import) and n3-private-name-import. The two report-only jscpd duplicates of event_shapers.py against `extraction/contracts.py` (15 lines) and `extraction/world.py` (11 lines) replace the old 28-line duplicate row.
4. `make typecheck-py`: 0 errors; 16 event_extractor.py rows removed from mypy_baseline.txt. `make typecheck-pyrefly`: nothing new from this change (the one new error, `watchdog.py:87`, is not in a file touched here); 10 event_extractor.py rows removed from pyrefly_baseline.json. `make lint-imports`: 17 kept, 0 broken. `tests/codebase`: 519 passed.
5. AC5 suites: see Test Summary in the ticket.

6. Guard probes (each revert verified with `cmp`): `test_detector_literals_are_gone` fails with `life_arc_incoherent` or `_LATE_GENERATION_THRESHOLD` planted in `event_extractor.py` (2 probes) and in `extraction/vitals.py` (2 probes); the presence guards `TestAntiDriftGuards::test_defer_property_name_constant_matches_phase_and_extractor` and `test_event_extractor_stays_exact_match_on_combat_for_passive_reasons` fail when the literal is removed from the module that holds it, and pass when it is present only in `event_extractor.py`.
7. AC5: 1543 passed, 83 skipped (observability, 15 importer files, architecture); determinism and replay 46 passed. `test_corpus_diversity.py` ids `..urban_political_seed123_500t_cognition..`, `..hero_guild_routing_seed42_1000t_cognition..`, `..urban_political_selfmodel_probe_seed42_200t_social_world..` fail on a clean archive of origin/main de5a223ca as well (score drift), so they are not ours; `..seed123_1000t_social_economy..` passed on the head.
8. Parity ledger: 36 entries re-pointed (v2_evidence only), `parity_ledger_schema check` 0 rose / 0 new, 2658 errors unchanged.
