---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [bws_proto]
---

# High-Performance Binary WebSocket Protocol (BWS)

Optimize the real-time world state synchronization by introducing a binary WebSocket protocol using MessagePack and positional arrays.

## Proposed Changes

### [Infrastructure & Dependencies]
Add `msgpack` to the project to support binary serialization.

#### [MODIFY] [pyproject.toml](file:///d:/Projects/rpg-based-simulation/pyproject.toml)
- Add `msgpack>=1.0.0` to the dependencies.

### [API Schema & Serialization]
Implement a lean serialization layer for positional arrays.

#### [MODIFY] [schemas.py](file:///d:/Projects/rpg-based-simulation/src/api/schemas.py)
- Update `StaticDataResponse` to include `entity_key_map` and `state_enum_map`.
- Define a `KeyMap` constant/registry for consistent indexing.

#### [NEW] [encoder.py](file:///d:/Projects/rpg-based-simulation/src/api/encoder.py)
- Implement `WorldStateEncoder`: Converts snapshot data to either "Rich" (Dict) or "Compact" (List) structures.
- Supports both JSON and MessagePack output.

### [WebSocket Implementation]
Create the streaming endpoint with protocol negotiation.

#### [NEW] [stream.py](file:///d:/Projects/rpg-based-simulation/src/api/routes/stream.py)
- Implement `GET /api/v1/state/stream` WebSocket endpoint.
- Handle initial handshake for `format` (json vs msgpack).
- Broadcast tick updates as they arrive from the Engine.

#### [MODIFY] [app.py](file:///d:/Projects/rpg-based-simulation/src/api/app.py)
- Add `GZipMiddleware` for the standard REST endpoints.
- Manage WebSocket connection lifecycle.

## Verification Plan

### Automated Tests
- **Payload Benchmarking**: Compare size of JSON REST vs Binary WebSocket for 200 entities.
- **Protocol Test**: Verify that both `json` and `msgpack` formats work correctly over the same WebSocket endpoint.
- **Regression Test**: Ensure existing REST `/state` results are unchanged.

## Phase 3: Production Stability & Logging (TCK-20260322-STABILITY)

Resolve the system "freeze" caused by corrupted proxy configuration and restore centralized visibility.

### [Nginx Proxy Optimization]
Implement dynamic connection upgrades for BWS and standard HTTP.

#### [MODIFY] [nginx.conf](file:///d:/Projects/rpg-based-simulation/nginx.conf)
- Use `map` block for `$connection_upgrade` (WebSocket vs HTTP).
- Fix corrupted `/api/` location block.

### Logging Stack Upgrade
Update Loki/Promtail to `v3.0.0` and ensure correct label mapping.

#### [MODIFY] [docker-compose.yml](file:///d:/Projects/rpg-based-simulation/docker-compose.yml)
- Remove obsolete `version: '3.8'`.
- Upgrade `loki` and `promtail` to `v3.0.0`.
- Mount `promtail-config.yml` to `/etc/promtail/config.yml`.

#### [MODIFY] [promtail-config.yml](file:///d:/Projects/rpg-based-simulation/promtail-config.yml)
- Sync `job` label with dashboard's `varlogs` expectation.
- Ensure `container` label matches `backend|ai_worker` regex.

## Verification Plan
...
