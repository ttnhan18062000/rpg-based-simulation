# Phase 9 Investigation & Subsystem Reuse Mapping

## 1. Overview of Phase 9 Core Pillars

The central mission of **Phase 9 (Simulation Mining and AI-Assisted Investigation)** is to transition the observability platform from single-run heuristics and multi-run drift baselines into an **automated large-scale diagnostic pipeline**. 

It answers the ultimate developer question: *“We ran 500 simulations. What are the top 5 logical or balance regressions we must debug first, and what is the exact evidence?”*

The engine's fundamental safety policy requires:
1.  **Strict Performance Isolation**: All mining, dataset building, outlier detection, and AI orchestrations run completely asynchronous to and decoupled from the engine's core tick resolution pipeline.
2.  **No Hallucinations / Evidence-First constraint**: The AI Agent acts purely on top of deterministic extracted evidence (Parquet datasets, DuckDB SQL results, and metadata manifests). It never directly consumes raw stream events nor writes speculative recommendations.

---

## 2. Milestone Subsystem Mappings

We map the Phase 9 milestones to new modules inside `src/observability/mining/`:

| Milestone | Subsystem / Component | Namespace Target |
|-----------|------------------------|------------------|
| **M49** | Mining Experiment Controller | `src.observability.mining.controller` |
| **M50** | Mining Dataset Builder | `src.observability.mining.dataset` |
| **M51** | Data Quality & Determinism Auditor | `src.observability.mining.auditor` |
| **M52** | Cross-Run Pattern Mining Engine | `src.observability.mining.patterns` |
| **M53** | Priority Scoring & Backlog Generator | `src.observability.mining.priority` |
| **M54** | Evidence Pack Builder | `src.observability.mining.evidence` |
| **M55** | AI Agent Investigation Orchestrator | `src.observability.mining.orchestrator` |
| **M56** | Next Instrumentation & Exp Recommender | `src.observability.mining.recommender` |
| **M57** | Phase 9 Review Gate | `src.observability.mining.workflow` |

---

## 3. Core Reuse Opportunities & Codebase Analysis

To build Phase 9 without redundant code, we must bind directly to our hardened V2 core:

### A. Run Matrix Execution & Scenario Setup
*   **Reuse Candidate**: `src.observability.sweeper.ScenarioSweeper`
*   **Analysis**: `ScenarioSweeper` is fully equipped with concurrent multi-seeded runner logic. We can reuse its underlying headless thread pool execution engine inside `MiningExperimentController` but wrapping it with support for `same_seed_repeat` (nondeterminism audits) and `observability_comparison` (verifying telemetry has zero performance or state side-effects).

### B. Single-Run Directory Contracts
*   **Reuse Candidate**: `src.observability.reporting.RunArtifactRepository`
*   **Analysis**: The `RunArtifactRepository` already enforces the exact directory layout under `data/runs/<run_id>/` that houses Pydantic manifests, `simulation_events.jsonl`, and `metric_windows.jsonl`. Our new `MiningDatasetBuilder` will scan these standard directories using the Pydantic parser schema to safely ingest and normalize all outputs.

### C. Relational Data Externalization
*   **Reuse Candidate**: `src.observability.analytics` (Parquet and DuckDB integrations)
*   **Analysis**: In Phase 6, we implemented DuckDB and Arrow Parquet transactional pipelines. Phase 9 requires aggregating hundreds of runs into a single relational dataset (`runs.parquet`, `run_features.parquet`, etc.). We will extend the existing exporter classes to build partitioned Parquet archives and dynamic DuckDB connection files dynamically isolated under `data/mining_experiments/<experiment_id>/dataset/`.

### D. Hypothesis & Anomaly Ingestion
*   **Reuse Candidate**: `src.observability.understanding.hypothesis` and `src.observability.understanding.story`
*   **Analysis**: Phase 8's specialized analyzers produce highly detailed structured reports. The `PatternMiningEngine` (M52) can directly extract these pre-computed story events and root-cause candidates from the single-run JSON arrays and compile them into comparative tables, completely avoiding re-evaluating raw tick timelines.

---

## 4. Mining Dataset Layout (DuckDB & Parquet)

We design the local structured dataset file boundary under `data/mining_experiments/<experiment_id>/dataset/` to store:

1.  `runs.parquet`: Complete run catalog (started, ended, completed ticks, execution latency).
2.  `run_features.parquet`: Highly curated feature vector per run (P95 compute, max RSS, health score, total anomalies, earliest hard-law violation tick).
3.  `anomalies.parquet`: Aggregated rule activations across all runs to count occurrences.
4.  `hard_law_violations.parquet`: Table of physical simulation invariant failures (highly prioritized as P0 correctness issues).

---

## 5. Constraint & Safety Invariants

*   **AI Agent Context Bounding**: The AI orchestrator will NEVER be fed raw, un-mined event logs. It will read compact, Pydantic-validated **Evidence Packs** (`evidence_pack.json`) containing outlier summaries and specific metric window excerpts.
*   **Auditability**: Every AI finding must reference exact `run_id`, `seed`, and `tick_range` keys, mapping them to verifiable SQL records in the local DuckDB instance. Any finding without concrete evidence keys is marked invalid.
