# Phase 10 Entry Support Boundary

This document defines the honest support status of the system-compatibility surface as of the start of Phase 10.

## 1. CLI & Entrypoint
- **Supported**: Basic unified entry gate (`python -m src_v2`).
- **Provisional**: `--seed`, `--ticks`, `--config`.
- **Unsupported**: `--headless`, `--watchdog`, `--profile`, and full flag-parity with legacy `main.py`.

## 2. Infrastructure & Environment
- **Supported**: `BROKER_DISABLED=1` mode (In-memory fallback).
- **Provisional**: Standard YAML config loading.
- **Unsupported**: Environment-variable overrides for all sub-parameters, hardware-specific isolation modes.

## 3. Observability & Artifacts
- **Supported**: Replay JSON-L emission (Bit-identical content).
- **Provisional**: Replay chunking and finalization (Known flush-timing drift).
- **Unsupported**: Structured logging Trace-ID parity, Metrics/Telemetry disaggregation.

## 4. API & Protocol
- **Supported**: Health-check and basic state REST endpoints.
- **Provisional**: JSON serialization of state.
- **Unsupported**: WebSocket lifecycle signals, Gzip/Zstd compression, MessagePack transport.

## 5. Headless Execution
- **Unsupported**: Native headless execution mode parity. Currently relies on test harness for headless verification.
