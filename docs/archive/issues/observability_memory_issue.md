---
status: archive
authority: P2
audience: historical
layer: observability
original_date: unknown
---

### Investigation Report: Pytest instability, memory growth, and worker-thread accumulation

Prepared for: Engineering management / issue tracking

### Issue statement (for management board)

Problem

The Python test suite intermittently crashes during full-suite execution with MemoryError, Fatal Python error: Aborted, and large numbers of background worker threads remaining active between tests. Individual tests often pass when executed in isolation, suggesting cumulative resource leakage across the test process.

Impact

This affects CI reliability, increases test execution time, and risks masking real failures behind infrastructure/resource failures. The issue appears to be related to observability/event-recording infrastructure used by the simulation kernel.

### Symptoms observed

Memory exhaustion during full test runs

Pytest reported MemoryError while generating failure reports and writing its cache. The crash stack traces indicate that memory was already exhausted before pytest attempted its own reporting/cleanup logic.

Tests pass when run individually

The same tests that participate in the failure generally succeed when executed alone, which is consistent with cumulative state or resource leakage rather than a single test requiring excessive memory.

Large number of active background threads

The fatal traceback shows many threads blocked in the same method:

This suggests multiple QueueDrainWorker instances remained alive simultaneously.

### Relevant code reviewed

QueueDrainWorker (observability/queue.py)

Observations

- The worker has a valid shutdown path (stop()).

- The worker thread is marked as a daemon thread.

- The queue itself is a module-level singleton (\_global_queue).

### Working hypotheses (not yet proven)

Most likely: workers are started but not consistently stopped

Evidence supporting this hypothesis:

- Dozens of threads remain in \_run.

- Tests pass individually but fail cumulatively.

- The traceback shows worker creation originating from EventRecorder.**init** and Kernel.**init**.

What is not yet confirmed:

- Whether EventRecorder exposes a close/shutdown method.

- Whether test teardown invokes that shutdown path.

Possible singleton state accumulation

Because the queue is global, repeated kernel constructions may attach multiple workers to the same queue. This alone does not guarantee a leak, but it can amplify resource usage if workers are not cleaned up.

Possible secondary memory growth inside observability/event recording

The thread leak may not be the only contributor. Additional investigation is needed to determine whether queued events, subscribers, log buffers, or other structures grow over time.

### Evidence

Evidence that supports the primary hypothesis

1. Repeated worker stack traces

   This line corresponds to the worker loop:

2. Worker creation path appears in the main thread traceback

   This indicates that creating a kernel starts a queue worker.

3. Isolation behavior

   Tests that pass individually but fail in a suite are a classic indicator of process-wide resource accumulation.

### What remains unverified

- Whether every QueueDrainWorker instance receives a matching stop() call.

- Whether EventRecorder owns the worker and cleans it up during shutdown.

- Whether tests create kernels without disposing them.

- Whether additional memory leaks exist beyond thread accumulation.

- Whether the observed crash is due to exhaustion of memory, thread count, file descriptors, or another OS-level resource limit.

### Recommended investigation tasks

Verify worker lifecycle

Inspect EventRecorder and Kernel teardown paths. Confirm that every worker started is stopped.

Add diagnostics

Log thread count and RSS memory after each test. Count active QueueDrainWorker threads.

Isolate tests

Run the suite with pytest-forked or similar process isolation to verify that failures disappear when state cannot accumulate.

### Proposed remediation

Short-term

1. Add explicit cleanup in tests that create kernels/event recorders.

2. Introduce a fixture that calls shutdown/close after each test.

3. Consider running problematic integration tests in isolated processes until the root cause is fixed.

Long-term

1. Make worker lifecycle management explicit and deterministic.

2. Add safeguards against multiple workers attaching to the same global queue unintentionally.

3. Add automated leak-detection checks (thread count, memory growth) in CI.

### Suggested ticket title

Observability QueueDrainWorker threads accumulate across tests, causing memory/resource exhaustion

Type: Bug / Reliability

Priority: High (CI stability)

### Suggested acceptance criteria

1. Thread count remains stable across the full test suite.

2. Full-suite execution completes without MemoryError or Fatal Python error: Aborted.

3. Observability workers are started and stopped deterministically.

4. CI includes a regression check for thread/resource leakage.

Note: Several conclusions above are intentionally labeled as hypotheses because only queue.py was reviewed directly. The behavior of EventRecorder, Kernel, and test teardown code has not yet been confirmed.
