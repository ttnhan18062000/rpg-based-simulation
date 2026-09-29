# Plan — TCK-20260929-RUN-EXECUTION-MODE-FIELD

1. Complete the consumer audit of the `workflow` field (acceptance blocker) before writing code.
2. `record_hand_orchestrated_closure.py::build_records`: add `"execution_mode": "hand"` to the
   run record.
3. Each of the 4 workflow `.js` files: add `"execution_mode":"pipeline"` to every
   `record_run.py --data` call site (not just the main success path — early-exit paths too).
4. `generate_retro.py`: split `compute_retro_metrics`'s run-summary computation into
   pipeline/hand/unlabelled groups; render a new sub-table in `generate()`'s `## Run Summary`.
5. Update the pre-existing frozen-output regression-lock test's pinned string (expected fallout
   of step 4, not a bug).
6. Document `execution_mode` in `docs/agent-monitoring/schema.md`; run
   `make knowledge-index-update`.
7. Tests: `record_run.py`, `record_hand_orchestrated_closure.py`, the 4 `.js` files (new pinning
   file), `generate_retro.py` (fixture-based split + real-corpus determinism).
8. Run the full specified test scope plus `node --check` on the 4 edited `.js` files plus
   `workflow_vocabulary_check.py` (unaffected, confirm PASS).

## Scope guards
- Do not change any writer's `workflow` value (option A rejected).
- Do not backfill or infer `execution_mode` for historical rows.
- Do not add any gate/ratchet on hand closures.
- Do not touch the dashboard UI beyond confirming it still works.
- Do not normalize the 20 W36 `workflow: "hand-orchestrated"` rows.

## Acceptance-criteria map
Every AC maps 1:1 to a specific test added or a direct invocation recorded in the ticket's Test
Summary.
