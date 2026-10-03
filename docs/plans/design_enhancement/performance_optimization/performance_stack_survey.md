---
status: active
layer: performance
authority: P2
audience: developer
tags: [performance, architecture]
---

# Performance Stack Survey

Date: 2026-10-02

## Purpose and status

The owner directed on 2026-10-02 that the performance program prefer a modern, widely adopted
stack, framework, or design, even when it is more complex
(`performance_optimization_roadmap.md`, "Technology direction"). This survey names, per layer, what
the repository uses today, the established options, and a recommended direction.

It is a planning input, not a decision and not a ticket list. Nothing here is authorized by this
document. The recommendations come from the planner's knowledge of these tools and from reading
this repository; **no candidate was installed or measured here**, and tool versions, licensing,
and hosted-service terms must be checked before any ticket adopts one.

## What the repository uses today

Measured on `origin/main` at `7dfd1349`:

- CPython, `requires-python >=3.11`, CI on 3.13. The engine is pure Python: no NumPy, no compiled
  extension of its own.
- Records: dataclasses and Pydantic v2 (89 importing modules).
- Workers: `ThreadPoolExecutor` / `ProcessPoolExecutor` in `src/engine/worker_manager.py`.
- Benchmarks: a bespoke harness (`src/perf/`, about 1,400 lines) plus scripts in `tools/perf/`
  (about 2,400 lines), JSON baselines in `tests/perf/baselines/`, thresholds in
  `tests/tools/perf_assertions.py`.
- Profiling: `cProfile`/`pstats`, `tracemalloc`, `psutil`.
- Metrics: `prometheus-client` on the API `/metrics` route, plus the kernel's own
  `_phase_costs`/`TickAudit` counters. No tracing.
- Data and serialization already in `requirements.txt`: `pyarrow`, `duckdb`, `msgpack`, `xxhash`,
  `redis`.

## Survey by layer

Each row gives the direction the planner recommends. "When" refers to the roadmap's milestones and
its RPG-core stability entry gate.

### A. Measurement and assurance tooling (foundation; no engine change)

| Layer | Today | Established options | Recommended direction | When |
|---|---|---|---|---|
| Benchmark harness | Bespoke `BenchHarness`, average-only comparison | `pytest-benchmark` (most used pytest plugin for this), `pyperf` (rigorous statistics, used by the CPython benchmark suite), `asv` (history tracking, used by NumPy and pandas) | Keep the scenario builders; move execution and statistics to `pytest-benchmark` for the PR lane and `pyperf` for controlled confirmation runs. Both give percentiles and variance the bespoke gate lacks | M2, after the entry gate; survey and design may start now |
| CI regression tracking on noisy runners | JSON file compare with `max(5 ms, baseline × 1.25)` | Instruction-count measurement (CodSpeed and similar), hosted or self-hosted trend tracking (Bencher, `github-action-benchmark`) | Instruction-count based measurement for the PR tripwire, because it is repeatable on shared runners where wall-clock is not; wall-clock capacity claims stay on controlled runs. A hosted service is an owner decision (data leaves the repository, possible cost) | M2/M4 |
| CPU profiling | `cProfile` (deterministic tracing, high overhead, distorts hot loops) | `py-spy` (sampling, attaches to a running process, flame graphs), `pyinstrument`, Scalene (line-level CPU and memory), the interpreter's `perf` support | `py-spy` as the standard profiler for tick profiling; Scalene for exploratory line-level work. Sampling is the industry default because its overhead does not distort the result | Now, as tooling under `tools/perf/` |
| Memory profiling | `tracemalloc`, `psutil` RSS | `memray` (allocation tracing with native frames, flame graphs), Scalene | `memray` for allocation attribution; keep `psutil` RSS for the gate's high-water check | Now, as tooling |
| Metrics and tracing | `prometheus-client` plus bespoke phase counters | OpenTelemetry (the vendor-neutral standard for traces, metrics, logs), exported to Prometheus and a trace store such as Tempo or Jaeger | OpenTelemetry as the one instrumentation API for M3: a span per tick, a child span per phase, with work-cardinality attributes; Prometheus stays as an exporter. Emission must be bounded and must not touch authoritative state | M3, after the entry gate |
| Telemetry storage | JSON/JSONL files, DuckDB warehouse | Parquet via Arrow, queried by DuckDB | Write benchmark and phase telemetry as Parquet and query with DuckDB — both already dependencies | M3/M4 |

### B. Engine hot path (exact optimization; Gate A selects, nothing preselected)

| Layer | Today | Established options | Recommended direction | Determinism note |
|---|---|---|---|---|
| Record types on hot paths | Dataclasses, Pydantic models | `msgspec` structs (fast, frozen, built-in MessagePack/JSON), `attrs` slots | `msgspec` structs for hot-path immutable records and worker payloads; Pydantic stays at API and content boundaries | Representation only; field order and encoding must be pinned |
| Columnar / data-oriented views | Per-entity Python objects | NumPy structured arrays, Apache Arrow (already present), Polars | Arrow-backed disposable column views for homogeneous Collection loops (the plan's "narrow SoA view") | Vectorized float reductions sum in a different order than a Python loop, so results can differ in the last bits; needs PERF-D2 and a parity oracle |
| Compiled kernels | None | Rust via PyO3 and maturin (the route taken by Pydantic core, Polars, Ruff, uv), Cython, mypyc, Numba | Rust/PyO3 for the kernels Gate A proves material (candidates by structure: spatial index, pathfinding, hashing). Highest headroom and the current mainstream choice; costs a second toolchain and wheel builds in CI | Integer and explicit-order float code keeps determinism; no fast-math |
| State hashing | Flat SHA-256 of canonical state, computed directly on the FULL persistence path | BLAKE3 (fast, a tree hash by construction, so incremental and parallel), `xxhash` for non-proof fingerprints | BLAKE3 as the candidate for PERF-D5 if hash cost proves material; flat SHA-256 stays the certification reference until then | A scheme change is a versioned identity change; never compare across schemes |
| Snapshot and worker IPC | Pickle through `ProcessPoolExecutor` | Arrow buffers in shared memory (zero-copy), `msgspec` encoding | Arrow shared-memory snapshots for the process backend | Read-only by construction, which matches the Collection contract |
| Parallel execution | Thread pool under the GIL, or process pool with copying | Free-threaded CPython (PEP 703), subinterpreters (PEP 734), Ray or Dask for multi-node | Evaluate free-threaded CPython for Collection first: workers already receive read-only state, so threads without the GIL remove the copy cost. Ray only if a multi-node requirement appears | Completion order must stay out of semantics; already a plan invariant |

### C. Architecture (changes structure or semantics; Gate B and a separate proposal)

| Topic | Today | Established design | Planner's reading |
|---|---|---|---|
| Entity model | Object-per-entity state with component dataclasses | Archetype ECS with data-oriented storage (Bevy ECS, flecs, Unity DOTS) | This is the modern large-scale answer and where the "very big" future points. For this engine it means a new core, not an optimization, so it belongs in a dedicated architecture proposal with a migration plan |
| Phase scheduling | Serial RESOLUTION, 44 handwritten phase calls | Systems that declare read/write access, scheduled in parallel when access does not conflict (the Bevy schedule model) | Matches the existing P1 sub-phase domain-contract epic almost exactly; that epic is the on-ramp. Parallel RESOLUTION still needs the conflict, staging, and commit design the plan already demands |
| Distant-region simulation | Every entity simulated individually, with cadence and LOD gates | Level-of-detail and aggregate simulation, interest management | An intentional fidelity change; needs product acceptance bounds, as the plan says. Interest management stays owned by the live-map epic |
| Determinism model | Seeded, canonical ordering, hash proofs | Deterministic lockstep with fixed-order reductions | Keep. It is the property every option above must preserve |

## What this changes in the plan

- Section A can be designed now and built as tooling without touching the engine; it replaces
  parts of M2 and M3 that would otherwise extend bespoke code.
- Section B does not relax Gate A. The direction decides *which* implementation is chosen once a
  contributor is proven material; it does not decide *that* one is built.
- Section C reverses nothing by itself. It gives the M6-T05 proposal a stated preferred direction
  (data-oriented ECS core with access-declared scheduling) to evaluate first.

## Owner decisions

Decided 2026-10-02 (the owner accepted the planner's recommendations):

- **A second language toolchain (Rust, via PyO3 and maturin) is acceptable** in this repository's
  build and CI. This permits Rust as the implementation choice for a compiled kernel; it does not
  select any kernel. Gate A still decides what, if anything, is compiled.
- **The ECS/data-oriented core is scoped now, as an architecture proposal only**, in parallel with
  the foundation instead of waiting for Gate B. The proposal is a document: it changes no code,
  and nothing in it is implemented before the RPG-core entry gate lifts and the owner approves it.

Still open, to be decided when the tooling tickets are written:

1. Is a hosted benchmark-tracking service acceptable, or must tracking stay inside the repository
   and CI artifacts?
2. Is moving the supported interpreter to a free-threaded CPython build acceptable as a target,
   given it constrains every compiled dependency?

## Sources

- `performance_optimization_roadmap.md`, "Plan review, 2026-10-02"
- `performance_m5_exact_optimization_delivery_epic.md`, `performance_m6_gate_b_future_architecture_epic.md`
- `../subphase_domain_contracts_epic.md`
- `requirements.txt`, `pyproject.toml`, `src/perf/`, `tools/perf/`, `src/engine/worker_manager.py`
