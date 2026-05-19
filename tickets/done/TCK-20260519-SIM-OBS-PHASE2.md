# TCK-20260519-SIM-OBS-PHASE2

## Title

Implement Phase 2 Semantic Events and Post-Run Observatory

## Status

DONE

## Request Summary

Implement the Simulation Observatory semantic event layer and post-run diagnostics pipeline to allow the engine to cleanly extract low-volume domain events, buffer and write them to disk safely, store per-entity histories externally, analyze runs post-hoc for behavioral anomalies, and generate beautiful simulation health reports.

## Scope

- **Event Envelope Refactoring**: Extend Pydantic `SimulationEvent` to support standard envelopes, enums, categories, and severity boundaries.
- **Decoupled Event Extraction**: Move ad-hoc event extraction logic from `kernel.py` to `EventExtractor` inside `src/observability/event_extractor.py`.
- **Bounded Event Recorder**: Implement memory-bounded `EventRecorder` in `src/observability/event_recorder.py` with priority overflow evictions, stats tracking, and a buffered JSONL output writer (`simulation_events.jsonl`).
- **External Entity Timeline Store**: Implement external `EntityTimelineStore` in `src/observability/entity_timeline.py` to hold timelines thread-safely external to `EntityState`, eliminating serialization footprint risks.
- **Kernel Integration**: Cleanly integrate these decoupled components into `Kernel._phase_observability()`.
- **Post-Run Anomaly Analyzer**: Implement rule-based behavioral anomaly detection (stuck navigation, quest stalls, infinite combat loops, node crowding) in `src/observability/anomaly/`.
- **Simulation Run Report Generator**: Implement `RunReportGenerator` in `src/observability/reporting/` to compute a deterministic weighted Health Score (0-100), generate human-friendly Markdown and machine-readable JSON health reports, and list triage guides.
- **Exhaustive Automated Tests**: Cover unit, integration, and determinism/parity suites.

## Out of Scope

- Out-of-process live anomaly detection daemons (Redis/Kafka integrations).
- Complex balance profile YAML files or full scenario sweepers.
- ML/AI-based anomaly classification.
- Full real-time WebSocket dashboard UI.

## Acceptance Criteria

- **100% Deterministic State Parity**: Runs with observability enabled produce identical canonical state hashes as runs with observability disabled. No RNG calls or authoritative mutations occur inside the observability pipeline.
- **Robust Memory Bounds**: Event recording buffers and entity timelines respect strict max caps (5000 events globally, mode-based per-entity caps), preventing memory leaks.
- **Decoupled Architecture**: All event extraction, timeline management, anomaly analysis, and reporting code reside in dedicated helper files outside of `kernel.py` and `state.py`.
- **Empirical Post-Run Analytics**: The post-run analyzer reads `simulation_events.jsonl` and successfully flags stuck entities, stalled quests, or infinite combat loops in `anomalies.json`.
- **Comprehensive Run Reports**: A sample run produces a beautiful Markdown health report and a JSON summary with a computed deterministic Health Score.
- **100% Test Success**: Complete coverage for all unit, integration, and parity assertions passes with zero errors.

## Related Tickets

- `TCK-20260519-SIM-OBS-EVENTS` (Phase 1 WebSocket Event Stream)
- `TCK-20260519-SIM-OBS-HARD-LAW` (Phase 1 Hard Law Invariant Monitor)

## Related Docs

- `docs/observability/phase_1.md`
- `obs_sim_phase2.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/events.py`
- `src/observability/event_recorder.py` (new)
- `src/observability/event_extractor.py` (new)
- `src/observability/entity_timeline.py` (new)
- `src/observability/anomaly/` (new)
- `src/observability/reporting/` (new)
- `src/engine/kernel.py`

## Assumptions / Open Questions

- **Fallback timeline compatibility**: We will maintain fallback compatibility for existing WebSocket endpoints accessing `entity.timeline`, but deprecate it internally by referencing the external `EntityTimelineStore`.

## Implementation Notes

- Fully implemented the decoupled event architecture: `events.py` (Standard Event Envelopes), `event_extractor.py` (Decoupled extraction), `event_recorder.py` (Bounded JSONL recorder with severity eviction overflow policy), `entity_timeline.py` (External EntityTimelineStore keeping `EntityState` hashes strictly pure and clean).
- Designed and coded robust anomaly detection rules (`rules.py`) and a full post-run analysis runner (`post_run_analyzer.py`) that exports telemetry logs to structured JSON (`anomalies.json`) and beautiful readable summary boards (`anomaly_summary.md`).
- Formulated the weighted simulation Health Score system (100 base, with deductions per Critical/Error/Warning event) and the Markdown and JSON reports dashboard generators (`run_report.py`).
- Cleanly integrated the new sub-systems into `Kernel` without creating any state side-effects.

## Test Summary

- Added 3 comprehensive units test files covering standard event validation, bounded timeline rollover, and anomaly rule activation.
- Added 3 detailed integration test files verifying manual and automatic kernel recording pipelines, JSONL event file parsing, post-run bug reporting, and Health Score/timelines outputs.
- Added 1 strict certification suite confirming 100% final state hash reproducibility and exact SHA-256 equivalence across all 4 modes (OFF, LIGHT, DEBUG, CERTIFICATION).

## Files Changed

- `src/engine/kernel.py`
- `src/observability/events.py`
- `src/observability/event_extractor.py` [NEW]
- `src/observability/event_recorder.py` [NEW]
- `src/observability/entity_timeline.py` [NEW]
- `src/observability/anomaly/rules.py` [NEW]
- `src/observability/anomaly/post_run_analyzer.py` [NEW]
- `src/observability/reporting/run_report.py` [NEW]
- `tests/unit/observability/test_event_recorder.py` [NEW]
- `tests/unit/observability/test_entity_timeline.py` [NEW]
- `tests/unit/observability/test_anomaly_rules.py` [NEW]
- `tests/integration/observability/test_kernel_event_recording.py` [NEW]
- `tests/integration/observability/test_post_run_analyzer.py` [NEW]
- `tests/integration/observability/test_run_report_generator.py` [NEW]
- `tests/certification/test_event_observability_parity.py` [NEW]

## Completion Summary

- Delivered a complete, decoupled, memory-bounded, thread-safe, and 100% hash-stable Observability Phase 2 suite. All requirements in `obs_sim_phase2.md` have been satisfied, validated, and proven correct via strict automated tests.
