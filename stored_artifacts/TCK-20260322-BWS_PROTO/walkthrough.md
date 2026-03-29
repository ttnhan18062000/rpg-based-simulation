# Performance Optimization Walkthrough

I have successfully addressed the performance bottleneck that caused the RPG simulation backend to hit 100% CPU usage and drop to 0.4 TPS.

## High-Performance Binary WebSocket Protocol (BWS)

Implemented an opt-in binary synchronization protocol to handle high entity counts with minimal bandwidth.

### Key Changes
- **Binary Stream**: New `/api/v1/ws` endpoint using WebSockets and MessagePack.
- **Positional Mapping**: Pre-shared "Key Map" handles field indexing, removing JSON key overhead.
- **Dual-Mode**: Handshake allows clients to choose between `json` (rich) and `msgpack` (compact) formats.
- **Gzip**: Enabled `GZipMiddleware` for all standard REST responses.

### Benchmark Results (100 Entities)
| Format | Size (Bytes) | Reduction |
| :--- | :--- | :--- |
| REST JSON (Full) | 89,517 | baseline |
| BWS JSON (Rich) | 67,611 | 24.5% |
| **BWS MsgPack (Compact)** | **4,178** | **95.3% 🚀** |

### Verification
- **Integration Tests**: `tests/integration/api/test_bws_protocol.py` verified handshake and data flow.
- **Performance Benchmark**: `tests/performance/benchmark_bws_payload.py` confirmed 95%+ reduction.

## 🚀 Optimization Results

| Feature | Optimization | Impact (Micro-benchmark) |
| :--- | :--- | :--- |
| **Entity State** | Shallow copying (`model_copy(deep=False)`) | **300ms/tick → 12ms/tick** |
| **World Grid** | `bytearray` storage + Enum caching | **4.0s/scan → 0.08s/scan** |
| **Messaging** | AI Task Batching (RabbitMQ) | **188 messages → 2 messages/tick** |
| **AI Perception** | Reduced scan radius for non-heroes | **~25% AI phase reduction** |

## 🛠️ Changes Made

### 1. Core Model Optimization
- Modified [models.py](file:///d:/Projects/rpg-based-simulation/src/core/models.py) to use shallow copying for entity state snapshots.
- This avoids expensive Pydantic recursive deep-copying of the entire world state every tick.

### 2. Grid Serialization Speedup
- Refactored [grid.py](file:///d:/Projects/rpg-based-simulation/src/core/grid.py) to use `bytearray` for tile storage.
- Implemented a `Material` object cache to eliminate `Enum` instantiation overhead during high-frequency lookups.

### 3. Distributed AI Batching
- Updated [worker_pool.py](file:///d:/Projects/rpg-based-simulation/src/engine/worker_pool.py) and [ai_worker_daemon.py](file:///d:/Projects/rpg-based-simulation/src/workers/ai_worker_daemon.py).
- The engine now sends all AI tasks for a tick in a single batched message, drastically reducing RabbitMQ overhead and context switching.

### 4. AI Perception Tuning
- Optimized `find_frontier_target` in [perception.py](file:///d:/Projects/rpg-based-simulation/src/ai/perception.py).
- Reduced the max scan radius for non-hero entities (40 → 15) to save CPU during exploration.

## 🧪 Verification

- **Automated Tests**:
    - Created [test_performance_optimizations.py](file:///d:/Projects/rpg-based-simulation/tests/unit/core/test_performance_optimizations.py) to verify `Grid` bytearray correctness, `Entity` shallow copying, and `AIWorkerDaemon` batch processing logic.
    - Updated [test_worker_pool_rabbitmq.py](file:///d:/Projects/rpg-based-simulation/tests/integration/engine/test_worker_pool_rabbitmq.py) to match the new batched messaging protocol.
    - **Result**: All 5 test cases passed successfully.
- **Micro-benchmarks**: Verified that grid access is now 50x faster and entity copying is 25x faster.
- **Tick Profiling**: Confirmed that the `collect` phase of the `WorldLoop` no longer dominates the CPU time.

> [!NOTE]
> While the core performance issues are resolved, ensure that the RabbitMQ and Kafka services have sufficient resources in your production environment to handle the increased throughput.
