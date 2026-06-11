---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260322-BWS_PROTO
phase: done
date: 2026-03-22
tags: [bws_proto]
---

# TCK-20260322-BWS_PROTO: High-Performance Binary WebSocket Protocol (BWS)

## Description
Implement an opt-in binary WebSocket protocol using MessagePack and positional arrays to reduce API payload size and improve real-time synchronization.

## Scope
- `pyproject.toml`: Add `msgpack` dependency.
- `src/api/schemas.py`: Add `KeyMap` metadata.
- `src/api/encoder.py`: New shared serialization layer (Rich vs Compact).
- `src/api/routes/stream.py`: New WebSocket endpoint.
- `src/api/app.py`: Gzip middleware and route integration.

## Acceptance Criteria
- [ ] `/api/v1/state/stream` supports `msgpack` format.
- [ ] `/api/v1/state/stream` supports `json` format (interoperability).
- [ ] >80% reduction in payload size for 200 entities using `msgpack` vs REST JSON.
- [ ] No regression in existing REST `/api/v1/state`.

## Related Tickets
- `infra-04-realtime-state-streaming` (Legacy streaming)
- `TCK-20260322-PERF_OPT` (Previous engine optimizations)

## Status: INPROGRESS
Plan approved. Starting implementation.

**Tier:** standard
**Type:** chore
**Priority:** P1
