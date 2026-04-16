# TCK-20260414-INFRA-REMEDIATION

## Title
Infrastructure Isolation & Replay-Assertion Repair

## Status
DONE

## Request Summary
Address the remediation track from `strategy_implementation_updated_v2.md`: prove optional infrastructure disabled-modes, repair stale replay-vs-graph assertions, and define explicit truth-surface ownership.

## Scope
- Prove RabbitMQ/Kafka disabled-mode collection and execution.
- Fix `assert_strategic_consistency` and `assert_cognition_consistency` stale read paths.
- Document and enforce truth-surface (Replay/API/Graph) ownership and overlap.
- Implement end-to-end documentation-integrity tests against populated artifacts.

## Out of Scope
- Expanding strategic logic (Leads, Social, Events).
- Changing CognitionCapacityBuilder formulas.

## Acceptance Criteria
- [x] Smoke tests prove test collection succeeds without `pika` (RabbitMQ) or `confluent-kafka` installed/enabled.
- [x] Artifact-consistency assertions read `ticks[-1]["entities"]` path.
- [x] Parity tests ensure Replay summaries align with API schemas for populated state.
- [x] Documentation integrity tests gate on real artifact content, not just symbol existence.

## Related Tickets
- TCK-20260413-INTEL-CAPACITY-IMPLEMENTATION (Precursor)

## Related Docs
- strategy_implementation_updated_v2.md
- intel_capacity_implementation_updated.md

## Related Code Areas
- `src/api/rabbitmq_client.py`
- `src/api/engine_manager.py`
- `src/testing/assertions.py`
- `tests/ai/test_cognition_integrity.py`
- `src/api/presenters/entity_presenter.py`

## Implementation Notes
- Hardened `EngineManager` with `HAS_KAFKA` guards to prevent crashes in brokerless environments.
- Unified `EntityPresenter` and `AIPresenter` strategic serialization to ensure bit-identical truth across surfaces.
- Updated `EntityCognitionExporter` and `assertions.py` to include expanded overload metrics (`primary_overload_source`, `last_overload_tick`).

## Test Summary
- `tests/remediation/test_brokerless_isolation.py`: Verified simulation loop runs without `pika`/`confluent-kafka`.
- `tests/ai/test_cognition_integrity.py`: 
    - `test_truth_surface_parity`: Proven parity across Replay, API, and Graph.
    - `test_documentation_alignment`: Proven Milestone 8 integrity.
- All 7 integrity tests passed.

## Files Changed
- `src/api/engine_manager.py` (Guard imports, fix uuid NameError)
- `src/api/presenters/entity_presenter.py` (Delegate to AIPresenter)
- `src/api/presenters/ai_presenter.py` (Expose serialize_strategy)
- `src/core/logic/cognition_graph_exporter.py` (Add missing fields)
- `src/testing/assertions.py` (Repair stale paths and logic)
- `tests/remediation/test_brokerless_isolation.py` [NEW] (Isolation proof)
- `tests/ai/test_cognition_integrity.py` (Add parity and doc tests)
- `intel_capacity_implementation_updated.md` (Update progress checkboxes)

## Completion Summary
Infrastructure isolation is now programmatically proven. All truth surfaces (Replay, API, Graph) are synchronized for intellectual capacity and strategic state, supported by robust regression assertions that align with the latest schema.
