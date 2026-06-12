---
status: active
layer: engine
authority: P1
audience: developer
---

# V2 Observability & Operational Artifact Contract

This document defines the supported operational surface (logs, metrics, reports, replays) for the V2 engine.

## 1. Logging Parity
- **Format**: Supports both plain text (`LEVEL:NAME:MESSAGE`) and JSON.
- **JSON Format**: Enabled via `--json-logs`. Produces a single JSON object per line.
- **Context Injection**: Every log record contains `timestamp`, `level`, `component`, and optionally `tick` if emitted during a simulation cycle.
- **Precedence**: CLI `--log-level` and `--json-logs` override environment and YAML defaults.

## 2. Metrics & Telemetry
- **Telemetry Toggle**: `TELEMETRY_DISABLED=1` environment variable disables the observability budget and internal stats collection.
- **Metrics Budget**: V2 enforces a `max_observability_budget_percent` in the `RuntimeProfile` to prevent diagnostic capture from stalling the kernel.

## 3. Replay Artifacts
- **Format**: Directory-based with JSON-L chunks (`chunk_XXXX.json`) and a metadata manifest (`manifest.json`).
- **Divergence**: This differs from the legacy single-file `replay.json`. V2 structure is optimized for streaming persistence and bounded memory usage.
- **Stable Names**: Chunk naming is deterministic and zero-padded.

## 4. Certification & Proof Reports
- **Release Proofs**: Located in `reports/release_proof/`.
- **Manifest**: `release_report.md` provides a human-readable summary of conformance tests.
- **Evidence**: `proofs_bundle.json` contains the machine-readable ground truth for all certification scenarios.

## 5. Known Divergences
- **Prometheus/Grafana**: V2 does not natively export to Prometheus in the Phase 10 baseline. Metrics are available via internal stats accessors and certification reports.
- **Log Context**: Some deep-level debug logs from third-party libraries may not contain the `tick` context.
