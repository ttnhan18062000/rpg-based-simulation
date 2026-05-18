# Phase 10 Compatibility Backlog

This document defines the frozen set of legacy system-compatibility rows owned by Phase 10.

## Phase 10 Row Set

| ID | Area | Atomic Item | Closure Condition | Status |
| :--- | :--- | :--- | :--- | :--- |
| **LEG-SYS-001** | SYS-COMPAT | CLI Mode / Args | Full parity with legacy `main.py` entrypoint. | BACKLOG |
| **LEG-SYS-002** | SYS-COMPAT | Config Precedence | Verified YAML -> Env -> CLI precedence. | BACKLOG |
| **LEG-SYS-006** | SYS-COMPAT | Disabled-mode Isolation | No infrastructure imports in disabled mode. | BACKLOG |
| **LEG-SYS-009** | SYS-COMPAT | Replay JSON-L | Bit-identical JSON-L stream parity. | BACKLOG |
| **LEG-SYS-010** | SYS-COMPAT | Det. Replay Path | Replay-based state reconstruction parity. | BACKLOG |
| **LEG-SYS-011** | SYS-COMPAT | Structured Logging | Trace-ID and level propagation parity. | BACKLOG |
| **LEG-SYS-012** | SYS-COMPAT | Telemetry Parity | Disaggregated metric emission parity. | BACKLOG |
| **LEG-SYS-013** | SYS-COMPAT | WebSocket behavior | Runtime lifecycle events via WS. | BACKLOG |
| **LEG-SYS-014** | SYS-COMPAT | Gzip/Zstd | Compressed artifact support parity. | BACKLOG |
| **LEG-SYS-015** | SYS-COMPAT | Headless consistency | Headless mode execution parity. | BACKLOG |
| **LEG-SYS-016** | SYS-COMPAT | Dep degradation | Graceful fallback when deps missing. | BACKLOG |
| **LEG-SYS-018** | SYS-COMPAT | CLI --seed | External seed injection parity. | BACKLOG |
| **LEG-SYS-019** | SYS-COMPAT | CLI --watchdog | Hardware/hang watchdog parity. | BACKLOG |
| **LEG-SYS-020** | SYS-COMPAT | Status endpoints | RESTful health and state endpoints. | BACKLOG |

## Closure Requirements
1. **Contract Tests**: Each row must have a `tests/compat/` contract test.
2. **Differential Proof**: Critical rows (CLI, Replay, API) must have a differential proof against `src`.
3. **Boundary Update**: The Phase 10 exit support boundary must reflect the results.
