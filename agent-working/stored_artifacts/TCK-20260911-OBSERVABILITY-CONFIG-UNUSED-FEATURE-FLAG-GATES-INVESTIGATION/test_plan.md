# Test Plan — TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION

## Real evidence (see investigation.md for full detail)
- Re-verified the ticket's own "3 confirmed live siblings" premise before trusting it — caught a
  near-over-correction (broad grep including `tests/` nearly produced a false "ticket is wrong"
  conclusion) and corrected back to a narrow, `src/`-only re-check before finalizing.
- Full sweep of all 17 `is_X_enabled()` methods (not just the 10+3 named), confirming only 2 are
  called by name anywhere in real code.
- Direct read of `kernel.py:270-277` and `cognition/recorder.py:31-58` confirming the real,
  coarse-mode-based gating pattern used by real consumers, including an existing ticket
  (`TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP`) that already documents the same mismatch for
  its own consumer.
- Confirmed `BehaviorWorker(`/`EpisodeDetector(`/etc. have zero real construction sites in `src/`,
  each with its own dedicated test file confirming they're real and tested, not dead code —
  corrected an initial wrong-class-name grep (real names `RunBehaviorComparison`/
  `BehaviorMetricsAggregator`, not the flag-name-derived guesses) before concluding.
- Confirmed `src/api/routes/behavior.py`'s real endpoint count (7, via `@router.get` grep, not the
  5-6 first estimated) and that all read from `LocalWarehouseAdapter`.

## Regression check
`src/observability/config.py` modified — deleted 3 unused convenience methods. Ran:
- `tests/unit/config/` + `tests/unit/observability/` — 1078 passed, 1 skipped, no regression.
- Grep confirms zero remaining references to `is_event_recorder_enabled`/
  `is_entity_timeline_enabled`/`is_warehouse_ingest_enabled` anywhere in `src/`/`tests/`.
`tests/integrity/test_no_duplicate_content_blocks.py` and `validate_frontmatter.py --content-type
ticket` passed on this ticket and both newly-touched/filed ticket files.

## Acceptance criteria mapping
- Each of the 10 unused flags mapped to its real intended subsystem, confirmed directly → done,
  investigation.md's Per-flag determination section.
- Each flag's real bucket determined with evidence → done — 3 confirmed vestigial (subsystem live,
  gated differently); 8 confirmed as one shared symptom of a bigger finding (pipeline never
  started), not 8 independent buckets.
- A disposition recorded per flag, with rationale → 3 deleted; 8 routed to their own ticket rather
  than resolved here, since the real disposition (wire vs. defer the pipeline) isn't a per-flag
  question.
- Any flag determined a real missing-gate bug routed through peer review before implementation →
  the 8-flag finding's own real disposition is routed via
  `TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT`, not implemented here.
