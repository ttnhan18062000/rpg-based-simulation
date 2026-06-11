---
status: archive
authority: P2
audience: historical
layer: simulation
original_date: 2026-03-21
---

# High-Speed Chaos & Fraud Detection Design

## 1. Goal
To provide a rapid, conflict-free way to simulate thousands of ticks to detect logical fraud (zombie heroes, negative health, duplicated items), while safely separated from production state. Additionally, to provide a dedicated test for component reliability under extreme load.

## 2. Approach: Dual-Testing Strategy
Since true simulation speed implies disregarding network I/O, we must separate these goals into two specialized tools:

### A. The Headless Logic Runner (`scripts/turbo_run.py`)
**Focus**: Pure Game Logic & Mathematical Fraud Detection
- **Mechanism**: Bypasses RabbitMQ, Redis, and Kafka entirely.
- **Mocks**: Replaces the networked `WorkerPool` with an in-memory `FastWorkerPool` that loops the engine and AI synchronously. State is held in a Python dictionary instead of Redis.
- **Performance**: Simulation speed leaps from 1 tick/second to 1,000+ ticks/second.
- **Output**: Dumps structured event histories directly to a local file (`logs/stress_test.jsonl`).
- **Validation**: Acts as the feed for `scripts/audit_logs.py` to assert continuity (e.g., verifying a hero didn't attack while dead).

### B. The Component Reliability Stress Test (`tests/e2e/test_message_reliability.py`)
**Focus**: Infrastructure Dropped Packets & Queue Overload
- **Mechanism**: Connects to the living Docker cluster (RabbitMQ, Kafka, Redis).
- **Execution**: Asynchronously floods the API with 10,000+ synthetic requests or mocked ticks in a burst.
- **Isolation**: Employs dedicated isolated routing keys (e.g., `sim_tasks_turbo_test`) so live heroes do not mistake dummy packets for reality.
- **Validation**: Asserts that RabbitMQ perfectly queues, workers successfully drain the queue, and Kafka fully commits every single message without timeouts or exception loops.

## 3. Data Flow
1. **Turbo Logic**: `World Loop` → `FastWorkerPool (RAM)` → `fraud_audit.jsonl`
2. **Reliability Load**: `Async Flooder` → `RabbitMQ Queue` → `AI Workers` → `Kafka Topic` → `Prometheus Metrics Validation`

## 4. Error Handling & Constraints
- The Fraud Auditor will brutally fail if it mathematically proves a hero performed an illegal action (acting while dead, invalid gold values).
- The Component Reliability script will timeout and fail the pipeline if the consumed Kafka messages count is less than the flooded count, preventing silent drops from going unnoticed.
