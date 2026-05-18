# Test Plan: Milestone 9 Certification Harness

## 1. Harness Contract Tests
- **Scenario Extraction**: Verify the harness can discover and load named scenarios.
- **Profile Binding**: Verify that a scenario run correctly initializes the `Kernel` with the targeted profile.
- **Artifact Geometry**: Verify the output `CERTIFICATION_REPORT.md` has the required sections and valid measurements.

## 2. Envelope Conformance Tests
- **Memory Violation**: Run a scenario that deliberately exceeds `max_ram_mb` and verify the harness marks it as `FAILED: RAM_VIOLATION`.
- **Latency Violation**: Run a scenario where work exceeds `max_tick_budget_ms` and verify it is caught.
- **Throughput Bounds**: Verify that the reported throughput is normalized by hardware class.

## 3. Resilience and Degradation Tests
- **Shedding Proof**: Verify that under pressure, the `Governor` emits `SHED_ACTIONS` and the harness records this transition.
- **No-Crash Guarantee**: Verify that the engine stays stable until a controlled shutdown even when reaching 95% budget capacity.
- **Recovery Verification**: Verify that when pressure is removed, the engine returns to `NORMAL` mode within $N$ ticks.

## 4. Hardware and Platform Tests
- **Detection Reliability**: Verify `HardwareClass` detection on the current host.
- **Rate-Limiting**: Verify that `BENCHMARK_MODE` (if implemented) successfully stabilizes tick variance.

## Test Files
- `tests/certification/test_harness_contract.py`
- `tests/certification/test_envelope_violations.py`
- `tests/certification/test_resilience_recovery.py`
