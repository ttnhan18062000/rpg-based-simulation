---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M37
artifact_type: investigation
tags: [sim, obs, m37]
---

# Investigation - TCK-20260520-SIM-OBS-M37

## Codebase Audit Findings

### 1. Existing Off-Loop Anomaly Rules
The existing rules in `src/observability/anomaly/rules.py` analyze pre-collected full event histories. They sort all events by tick, build timeline mappings, and run complex post-hoc checks.
For a live stream, doing full-timeline scans is prohibitively expensive and violates the bounded-memory principle.
We must construct streaming-friendly versions of these rules (`LiveAnomalyRule`) that maintain minimal sliding states and process events single-pass or look back over a highly bounded list of recent events.

### 2. Stream Consumer Adapter
We created `RedisStreamConsumer` in `src/observability/stream/consumer.py` during Milestone 36.
It exposes a synchronous block-based `read_and_process(handler, block_ms)` loop.
This makes a poll-based worker loop very straightforward:
```python
while not self.stop_event.is_set():
    processed = self.consumer.read_and_process(self.process_event, block_ms=1000)
    if processed > 0:
        self.flush_status()
```
If the backend is `in_process`, we can subscribe to the `LiveEventPublisher` singleton via callbacks, which avoids blocking threads.

### 3. Governor Events Hook
Currently, `GovernorModeChanged` is not standardly produced during standard ticks.
We audited `src/engine/kernel.py` and found that we can seamlessly emit a `GovernorModeChanged` event in `_phase_observability` by checking `self._status.last_transition_tick == tick`.
This ensures standard stream consumers get real-time visibility into engine degradation and recovery cycles.

### 4. Bounded Window Design
To enforce bounded memory, `LiveAnomalyWorker` needs to evict old events.
We will model this with a `deque` or a dictionary indexed by tick:
- When a new event arrives at `tick = T`, we update `self.current_live_tick = max(self.current_live_tick, T)`.
- We remove any stored events with `tick <= self.current_live_tick - window_ticks`.
- We similarly prune target entity position coordinates that are older than the window threshold.
- Memory usage is checked dynamically via `psutil` or `sys.getsizeof` to guarantee the worker adheres to configured limits.
