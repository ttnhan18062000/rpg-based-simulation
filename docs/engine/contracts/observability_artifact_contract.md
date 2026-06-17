---
status: active
layer: engine
authority: P1
audience: developer
---

# Observability & Operational Artifact Contract

This document defines the supported operational surface (logs, metrics, reports, replays) for the engine.

## 1. Logging Parity
- **Format**: Supports both plain text (`LEVEL:NAME:MESSAGE`) and JSON.
- **JSON Format**: Enabled via `--json-logs`. Produces a single JSON object per line.
- **Context Injection**: Every log record contains `timestamp`, `level`, `component`, and optionally `tick` if emitted during a simulation cycle.
- **Precedence**: CLI `--log-level` and `--json-logs` override environment and YAML defaults.

## 2. Metrics & Telemetry
- **Telemetry Toggle**: `TELEMETRY_DISABLED=1` environment variable disables the observability budget and internal stats collection.
- **Metrics Budget**: The engine enforces a `max_observability_budget_percent` in the `RuntimeProfile` to prevent diagnostic capture from stalling the kernel.

## 3. Replay Artifacts
- **Format**: Directory-based with JSON-L chunks (`chunk_XXXX.json`) and a metadata manifest (`manifest.json`).
- **Divergence**: This differs from the legacy single-file `replay.json`. The current format is optimized for streaming persistence and bounded memory usage.
- **Stable Names**: Chunk naming is deterministic and zero-padded.

## 4. Certification & Proof Reports
- **Release Proofs**: Located in `reports/release_proof/`.
- **Manifest**: `release_report.md` provides a human-readable summary of conformance tests.
- **Evidence**: `proofs_bundle.json` contains the machine-readable ground truth for all certification scenarios. It is populated via `CertificationResult.to_artifact_dict()` — never via `dataclasses.asdict()` on live state.
- **Manifest snapshot**: `manifest_snapshot.json` is written to the proof output directory as a verbatim copy of the manifest used for the run (see `extended_certification_contract.md` §9).
- **Evidence levels**: `proofs_bundle.json` entries reflect the `EvidenceLevel` used for the run:
  - `SUMMARY` (default): scalar metrics + entity/resource/region counts.
  - `COMPACT`: adds `entity_sample` (top 5) and `resource_snapshot` (top 5 by quantity).
  - `FULL`: adds `final_state_artifact_path` and `final_state_hash`; canonical state written to `<output_dir>/state/<run_id>.final_state.canonical.json`.
- **`final_state` is never embedded**: Proof bundle entries always have `final_state: null`. Full state is written to a separate file only under `EvidenceLevel.FULL`.

## 5. Known Divergences
- **Prometheus/Grafana**: The engine does not natively export to Prometheus in the current baseline. Metrics are available via internal stats accessors and certification reports.
- **Log Context**: Some deep-level debug logs from third-party libraries may not contain the `tick` context.
