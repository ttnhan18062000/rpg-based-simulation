# infra-05: Multiprocessing AI Workers (GIL Workaround)

## Objective
Bypass Python's Global Interpreter Lock (GIL) by shifting heavy AI evaluations (A*, FOV calculations) into a `ProcessPoolExecutor` with lock-free shared memory access.

## Rationale
Threads (`ThreadPoolExecutor`) only provide true concurrency for I/O operations in Python. As scale expands to hundreds of entities with complex narrative AI decisions (Epic-12), the engine will hit CPU-bound limits under the GIL, throttling the `Collect` phase of the `WorldLoop`.

## Scope
- Swap `ThreadPoolExecutor` for a process-based solution (`multiprocessing.Process` or `concurrent.futures.ProcessPoolExecutor`).
- Implement `multiprocessing.shared_memory` to provide worker processes with zero-copy read-only access to the `Snapshot` and `WorldState` grid, avoiding massive IPC serialization overhead.
- Introduce bounded MPSC (Multi-Producer, Single-Consumer) work queues.
- Enforce strict backpressure (drop proposals gracefully if the pipeline is overwhelmed).

## Acceptance Criteria
- AI `Collect` phase execution time drops linearly across multiple logical CPU cores.
- `make profile` demonstrates >500 entities processed without stalling the main `WorldLoop` tick target.
- Determinism is perfectly maintained across process boundaries.
