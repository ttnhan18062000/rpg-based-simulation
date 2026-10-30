---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261028-EVENT-EXTRACTOR-CHARACTERIZATION-TESTS
artifact_type: plan
tags: [observability, testing]
---

# Plan
Test-only; `src/` untouched. A pytest plugin (`tests/unit/observability/extractor_characterization/recorder_plugin.py`) wraps `EventExtractor.extract` and evaluates each call under 8 configs (as built, default flags, each of the 4 `ENABLE_PUSH_EVENT_SHAPERS*` flags OFF alone, all four OFF under LIGHT and under NORMAL), restoring the run-scoped caches between evaluations, so the test's own call is unchanged.
Two sources of calls: (1) the existing `test_event_extractor_*.py` unit tests (371 calls after (A)); (2) two seeded real-Kernel runs under `audit_mode`, 200 ticks each (`lifecycle_full_coverage_world`, `dungeon_crawl`).
Pinned per call and config: event count + SHA-256 prefix over the ordered canonical lines (no `timestamp`, `created_at`, `event_id`; addresses scrubbed). Fixtures: `tests/fixtures/event_extractor_characterization/{unit_corpus,kernel_runs}.jsonl`. Both recorders run in a subprocess with `PYTHONHASHSEED=0`; a test records again at another seed and asserts identical rows.
Pinned rows must match; new unit tests add rows without a failure. Regenerate with `python -m tests.unit.observability.extractor_characterization.corpus`.
Two direct tests cover the two emitting blocks no recorded call reaches. Digests rather than event lines are committed: the full lines are 1.3 MB for the corpus alone; `EXTRACTOR_RECORD_FULL=<path>` writes them for a diff between two commits.
