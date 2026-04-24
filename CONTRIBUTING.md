# Contributing to the Resource-Safe Engine

Thank you for contributing! This project follows a strict **Resource-Safe Engineering** model. All contributions must adhere to the laws defined in the [Engineering Playbook](docs/engine/engineering_playbook_m10.md).

## Critical Contributor Guardrails

To protect the engine from resource-safety drift, the following behaviors are **strictly forbidden**:

1.  **Unbounded Collections**: Never use a list, dictionary, or queue that can grow without limit. Every collection must have an explicit retention policy or maximum size.
2.  **Universal Performance Claims**: Do not claim "unlimited speed" or "real-time performance" in isolation. All throughput claims must be bound to a specific Profile and Hardware Class.
3.  **Alternate Authority Paths**: All simulation state changes must flow through the authoritative `apply` path. No static variables or hidden global state.
4.  **Implicit Dependencies**: No raw ad-hoc threading. Use the `Scheduler` and `WorkerPool` for all concurrent work.
5.  **Telemetry Leakage**: Do not store diagnostic fields, UI strings, or telemetry inside the `AuthoritativeState`. Keep the simulation core lean.

## Engine Authority (Phase 12+)
As of Phase 12, the **src_v2** engine is the project's operational default. All development should target the V2 substrate.

## Verification
Before submitting a pull request, you must ensure all tests pass:
```bash
make test
```
This command executes the **tests_v2** suite, which includes contract, parity, and stress scenarios. For coverage analysis, use:
```bash
make test-cov
```

## The TDD Loop

All new features must implement:
1.  **Contract Tests**: Verify the resource and semantic boundaries.
2.  **Implementation**: Minimal logic.
3.  **Scenario Tests**: Stress-test the feature under resource pressure.

For details on how to extend the simulation, see the [Engineering Playbook](docs/engine/engineering_playbook_m10.md).
