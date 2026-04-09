# Spec: High-Performance Binary WebSocket Protocol (BWS)

## Overview
Introduce an opt-in, high-performance binary synchronization protocol for real-time world state updates. This protocol aims to solve the overhead of polling-based JSON APIs by using WebSockets and MessagePack-encoded positional arrays.

## Requirements
1.  **Zero Breaking Changes**: Existing REST `/api/v1/state` must remain fully operational and untouched.
2.  **Dramatically Small Payloads**: Target >80% reduction in per-tick transfer size for 200+ entities.
3.  **Understandable Data**: Support for a JSON mode within the same WebSocket for developer debugging.
4.  **Static Definitions**: Rely on a pre-shared "Key Map" (fetched once) to avoid sending object keys in every tick.

## Architecture

### 1. Static Handshake
The UI will fetch game metadata from `/api/v1/static`. This response will be extended to include the `KeyMap`:
- **EntityKeyMap**: `["id", "x", "y", "hp", "state_id", "combat_target_id", "loot_progress"]`
- **StateEnumMap**: `{"IDLE": 0, "MOVE": 1, "COMBAT": 2, "LOOT": 3, ...}`

### 2. WebSocket Connection (`/api/v1/state/stream`)
The server supports multiple transport formats decided during the initial handshake over the socket.

#### Handshake Message (Client -> Server)
```json
{
  "type": "handshake",
  "format": "msgpack",
  "compression": "none"
}
```

#### Update Frame (Server -> Client)
The server broadcasts a binary blob (if `msgpack`) or a JSON string.
Structure (Positional Array):
`[tick_id, [entity_deltas], [new_events], [resource_node_deltas], ...]`

Each `entity_delta` is an array following the `EntityKeyMap` order.

### 3. Backend Implementation
- **New Dependency**: `msgpack`
- **WS Manager**: Handle active connections and broadcasting.
- **Encoder Layer**: Flexible serialization that can output either `Dict` (Rich) or `List` (Compact) and then encode to either `JSON` or `MsgPack`.

## Verification Plan
1.  **Payload Benchmarking**: Compare size of JSON REST vs BWS for 100 entities.
2.  **Latency Measurement**: Measure time-to-client for Websocket Push vs HTTP Poll.
3.  **Protocol Switching**: Verify that a JSON client can connect to the same WebSocket as a MsgPack client.
