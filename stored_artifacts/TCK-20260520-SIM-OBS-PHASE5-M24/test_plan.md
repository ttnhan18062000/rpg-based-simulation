# Test Plan: WebSocket Live Observatory API

We will implement automated unit and API integration tests to verify the correctness, performance, safety limits, and filtering behavior of the new WebSocket endpoint.

## Automated Verification Tests

### Test Target: `tests/api/test_observability_websocket.py`

#### 1. Connection and Handshake Verification
- **Scenario**: Connect to `ws://127.0.0.1:{port}/api/v1/ws/observability/events` with no filters.
- **Verification**: Verify that connection is accepted and receives a `subscription_ack` message with an empty filter structure.

#### 2. Subscription Filters Verification
- **Scenario**: Connect with `?severity_min=WARNING&entity_id=1`.
- **Verification**: Verify that the subscription filter is successfully parsed. Publish `INFO` events for entity 1 (should not receive), and `WARNING` events for entity 1 (should receive).

#### 3. Filtering Out Non-Matching Events
- **Scenario**: Connect with `?category=combat`.
- **Verification**: Verify that `CombatDamageEvent` (combat category) is delivered, but `MovementEvent` (movement category) is ignored.

#### 4. Parameter Validation & Error Handling
- **Scenario**: Connect with an invalid query parameter `?unknown_param=hello`, or an invalid severity `?severity_min=DUMMY`, or an invalid entity_id format `?entity_id=abc`.
- **Verification**: Verify that connection fails, or returns a clear `error` message and closes with code 1003.

#### 5. Safety Capacity Limit
- **Scenario**: Open 11 concurrent WebSocket connections.
- **Verification**: The 11th connection must be rejected or closed with code 1008.

#### 6. Client Disconnection & Resource Cleanup
- **Scenario**: Client connects, receives events, and disconnects.
- **Verification**: Verify that the `LiveEventPublisher` active subscriber list decreases by 1 and all memory queues are garbage collected.
