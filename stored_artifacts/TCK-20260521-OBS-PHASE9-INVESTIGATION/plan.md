---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260521-OBS-PHASE9-INVESTIGATION
artifact_type: plan
tags: [obs, phase9, investigation]
---

# Phase 9 Implementation Plan — Simulation Mining and AI-Assisted Investigation

## 1. Goal Description

This plan implements the comprehensive data engineering and AI-assisted prioritized diagnostic system (Phase 9, Milestones 49–57) for the V2 RPG Engine. 

By building a deterministic pattern mining and evidence pack aggregation system, we bridge the gap between massive multi-run telemetry data and constrained, evidence-backed AI diagnostic prioritization, giving developers clear, prioritized engineering backlogs.

---

## 2. Proposed Changes

We will introduce a clean, decoupled mining namespace under `src/observability/mining/`:

### [NEW] Components

#### 1. [NEW] `src/observability/mining/controller.py`
*   Implements `MiningExperimentConfig`, `MiningExperimentController`, and `MiningRunMatrixBuilder`.
*   Generates run specifications dynamically for six experiment modes (`same_seed_repeat`, `multi_seed_sweep`, `observability_comparison`, etc.).
*   Tracks execution manifests under `data/mining_experiments/<experiment_id>/experiment_manifest.json`.

#### 2. [NEW] `src/observability/mining/dataset.py`
*   Implements `MiningDatasetBuilder` utilizing DuckDB and Parquet storage.
*   Extracts run-level feature vectors (`worst_tick_range_start`, `memory_rss_bytes_max`, `health_score`) and normalizes single-run JSONL files into tabular relational formats.

#### 3. [NEW] `src/observability/mining/auditor.py`
*   Implements `DataCompletenessAuditor` (identifying missing signals or mismatched schemas) and `DeterminismAuditor`.
*   Groups repeated seed runs and audits final state hashes and event sequences to detect nondeterminism (earliest divergence tick finder).

#### 4. [NEW] `src/observability/mining/patterns.py`
*   Implements `PatternMiningEngine`, `OutlierDetector`, and `RecurringAnomalyMiner`.
*   Scores and clusters anomalies by domain, temporal windows, and resource/quest hotspots.

#### 5. [NEW] `src/observability/mining/priority.py`
*   Implements `PriorityScorer` scoring issues into P0 (correctness/corruption) through P4 (interesting emergent behavior) based on severity, blast radius, and frequency.
*   Generates structured `engineering_backlog.json` and `engineering_backlog.md`.

#### 6. [NEW] `src/observability/mining/evidence.py`
*   Implements `EvidencePackBuilder` isolating compact timeline snippets, reproduction commands, and relevant anomaly slices for a specific prioritized issue.

#### 7. [NEW] `src/observability/mining/orchestrator.py`
*   Implements `AIAgentInvestigationRunner` and `AgentOutputValidator`.
*   Orchestrates a constrained, zero-context LLM diagnostic analyzer using only the curated evidence pack. Refuses speculative assertions without concrete SQL keys.

#### 8. [NEW] `src/observability/mining/recommender.py`
*   Implements `NextExperimentRecommender` and `InstrumentationGapDetector` suggesting what signals or logging spans are missing to resolve the root cause.

#### 9. [NEW] `src/observability/mining/workflow.py`
*   Implements `MiningReviewWorkflow` and `MiningQualityGate`.
*   Enables human verification labels and provides a CI gate that passes, warns, or fails on determinism divergency or hard law violations.

---

## 3. Verification Plan

### Automated Tests
We will implement dedicated test modules under `tests/unit/` and `tests/integration/`:

#### Unit Tests
- `tests/unit/test_mining_controller.py`: Verifies matrix generation and manifest formats.
- `tests/unit/test_mining_dataset.py`: Verifies DuckDB feature extraction.
- `tests/unit/test_mining_auditor.py`: Verifies data quality classifications and determinism divergence checks.
- `tests/unit/test_mining_patterns.py`: Verifies anomaly ranking, domain clustering, and hotspot detection.
- `tests/unit/test_mining_priority.py`: Verifies severity and actionability priority scoring.
- `tests/unit/test_mining_evidence.py`: Verifies compact snippet limits.

#### Integration Tests
- `tests/integration/test_mining_experiment_flow.py`: Runs a complete multi-seed sweep, builds the Parquet dataset, detects outliers, and builds evidence packs automatically.
- `tests/integration/test_same_seed_determinism_flow.py`: Simulates seed replication and checks the divergence auditor.
- `tests/integration/test_mining_quality_gate.py`: Verifies CI gating conditions.

### Manual Verification
- Execute new CLI actions under `rpg-observe mining run` and verify output directories under `data/mining_experiments/`.
- Review generated `engineering_backlog.md` and `determinism_audit.md` reports for absolute accuracy and parity.
