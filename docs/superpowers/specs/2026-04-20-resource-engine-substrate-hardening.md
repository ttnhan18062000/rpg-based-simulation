# Design Specification: Resource Engine Substrate Hardening (A/B/C Closure)

## 1. Problem Statement
The V2 Resource Engine has advanced layers (D/E: Concurrency and Certification) that are running ahead of the core substrate truth (A/B/C). 
- **Milestone A**: The baseline execution path is entangled with concurrency plumbing.
- **Milestone B**: Operational status signals lack clear, bounded, source-tracing "truth."
- **Milestone C**: Certification proof for lifecycles is partly simulated rather than derived from runtime outcomes.

## 2. Proposed Architecture: The Executor Split

To resolve the Milestone A entanglement, we will decouple the "Simulation Logic" from the "Execution Strategy."

### 2.1 The `IWorkExecutor` Abstraction
We will introduce a protocol/interface for executing a batch of simulation work items.

```python
class IWorkExecutor(Protocol):
    def execute(
        self, 
        work_items: List[WorkItem], 
        state: AuthoritativeState, 
        rng: DeterministicRNG
    ) -> List[WorkerResult]:
        ...
```

### 2.2 `LocalSequentialExecutor` (MA Truth)
- **Direct Execution**: Iterates through `WorkItem`s and calls domain logic synchronously.
- **No Packets**: Bypasses `WorkerPacket`, serialization, and `WorkerManager`.
- **Pure Semantic Truth**: This becomes the absolute reference for all A-level stability tests.

### 2.3 `ConcurrentExecutionAdapter` (MD/ME Path)
- **Adapter Logic**: Builds `WorkerPacket`s as it does today.
- **WorkerManager Dispatch**: Sends packets to the concurrent thread pool.
- **Fallback Logic**: Handles queue pressure by falling back to `LocalSequentialExecutor`.

## 3. Component Details

### 3.1 Kernel Refactoring
- `Kernel.__init__` now accepts an `executor: IWorkExecutor`.
- `_phase_collection` is simplified to a single delegation call to the executor.
- Orchestration becomes phase-pure: **Scheduling -> Execution -> Resolution**.

### 3.2 Signal Source Audit (MB Hardening)
- **WorkerManager peak tracking**: Fix the `reset_tick_stats` ordering so peaks are captured BEFORE they are wiped for the next tick.
- **RuntimeStatus History**: Tighten the 5-tick rolling window calculation to use strictly bounded source facts.

### 3.3 Lifecycle Truth (MC Hardening)
- **`ShutdownResult`**: A new structured model for shutdown outcomes.
- **Kernel.shutdown()**: Updates `RuntimeStatus` with the final authoritative hash and result metadata.
- **CertificationHarness**: Reads `status.lifecycle_outcome` instead of hardcoding scenarios.

## 4. Implementation Sprints

### Sprint 1: Milestone A Isolation (MA)
- Focus: `IWorkExecutor` and `LocalSequentialExecutor`.
- Goal: Pass `test_milestone_a_closure.py` using a pure local path.

### Sprint 2: Signal Truth (MB)
- Focus: `WorkerManager` audit and `RuntimeStatus` refinement.
- Goal: Pass `test_signal_truth.py`.

### Sprint 3: Lifecycle Proof (MC)
- Focus: `ShutdownResult` and Harness de-simulation.
- Goal: Pass `test_lifecycle_reproducibility.py`.

## 5. Testing & Verification
- **Equivalence Tests**: Use the same initial state and seed to prove that `LocalSequentialExecutor` and `ConcurrentExecutionAdapter` produce bit-identical `AuthoritativeState` outcomes.
- **Phase Order Tests**: Verify that refactoring the Kernel doesn't break the 6-phase authoritative contract.
