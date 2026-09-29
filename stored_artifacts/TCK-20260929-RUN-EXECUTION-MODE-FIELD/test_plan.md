# Test Plan — TCK-20260929-RUN-EXECUTION-MODE-FIELD

Derived directly from the ticket's Acceptance Criteria; all implemented and passing.

1. `record_run.py --data '{..., "execution_mode": "pipeline"}'` writes it through; a record
   without it still passes validation (`test_execution_mode_pipeline_passes_through_unchanged`,
   `test_record_without_execution_mode_still_accepted`).
2. `record_hand_orchestrated_closure.py::build_records` output contains `execution_mode: "hand"`
   and `workflow: "implement-ticket"` (default)
   (`test_build_records_sets_execution_mode_hand_and_keeps_workflow_default`).
3. All 8 real `record_run.py --data` call sites across the 4 workflow `.js` files include
   `"execution_mode":"pipeline"` (parametrized text-level test,
   `test_run_execution_mode_field_wiring.py`); no `.js` file ever writes
   `execution_mode: "hand"` (negative check).
4. Fixture runs with pipeline/hand/absent `execution_mode` produce three separate groups with
   correct counts in `compute_retro_metrics`'s output and in the rendered `## Run Summary` table
   (4 tests, including a legacy `workflow: "hand-orchestrated"` row landing in `unlabelled`).
5. Pipeline avg duration is computed only from pipeline runs' own durations, unaffected by huge
   hand/unlabelled durations in the same fixture
   (`test_pipeline_avg_duration_excludes_hand_and_unlabelled_runs`).
6. `generate_retro.py` over the real corpus (20 W36 `workflow: "hand-orchestrated"` rows
   included) runs without error and produces byte-identical output across two calls
   (`test_generate_over_real_corpus_including_legacy_hand_orchestrated_rows_is_deterministic`).
7. `docs/agent-monitoring/schema.md` documents the field; `make knowledge-index-update` run
   (7 files re-embedded).
8. `pytest tests/tools -k "monitoring or retro or record"` → 573 passed, 4 skipped.
   `tests/tools/test_agent_ops_dashboard_ingest.py` → 49 passed. `node --check` on all 4 edited
   `.js` files: clean. `workflow_vocabulary_check.py`: all PASS.
