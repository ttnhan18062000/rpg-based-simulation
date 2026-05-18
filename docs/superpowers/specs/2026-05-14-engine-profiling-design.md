# Design Spec: Engine Profiling Suite
**Date**: 2026-05-14
**Goal**: Implement a robust profiling harness to establish performance baselines and debug subsystem hotspots.

## 1. Problem Statement
The V2 RPG Engine is moving toward production-grade simulation. To ensure scalability (1,000 to 5,000+ entities), we must identify non-linear performance bottlenecks before they impact simulation integrity. 

## 2. Proposed Architecture
The `scripts/profile_engine.py` suite will act as a non-intrusive wrapper around the `Kernel.tick_once()` loop.

### 2.1 Core Components
- **Scenario Runner**: Orchestrates specific simulation states (Idle, Combat, Resource, Strategic).
- **Profiling Engine**: Uses `cProfile` and `pstats` to capture and format execution time.
- **Reporting Layer**: Outputs binary `.prof` and human-readable `.txt` reports to `reports/profile/`.

### 2.2 Scenarios
1. **IDLE_1000**: Baseline overhead of the kernel and state updates.
2. **MOVEMENT_1000**: Stresses spatial querying and navigation.
3. **RESOURCE_1000**: Stresses inventory and transaction resolution.
4. **STRATEGIC_1000**: Stresses the strategic cognition pipeline.

## 3. Data Flow
1. Load `RuntimeProfile` (Class A).
2. Generate `AuthoritativeState` with $N$ entities using `V2EntityBuilder`.
3. Enable `cProfile`.
4. Run $T$ ticks of `kernel.tick_once()`.
5. Disable `cProfile` and dump stats.
6. Generate sorted report by `cumtime`.

## 4. Verification Plan
- **Manual**: Run `python scripts/profile_engine.py --scenario idle` and verify `reports/profile/idle_1000.txt` exists and contains valid data.
- **Performance**: Ensure the harness does not significantly distort the relative cost of different phases.
