---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260523-OBS-HARDENING
artifact_type: plan
tags: [obs, hardening]
---

# Implementation Plan - RPG Engine V2 Observability Hardening (Phases 1-9)

This plan details the technical steps to harden the V2 Simulation Observatory across Phases 1-9. We will address every P0, P1, and P2 issue identified during the detailed audit.

## Proposed Changes

We will systematically modify the observability package files and create missing test assets to cover all gaps.

### 1. Fix ObservabilityMode Mapping & Sweeper [P0]
- **File**: `src/observability/sweeper.py`, `src/observability/mining/experiment.py`, `src/observability/config.py`
- **Change**: Align string mapping of production, full, light, none, cert with actual enum values (`OFF`, `LIGHT`, `DEBUG`, `CERTIFICATION`, `LONG_RUN`).
- **Safety**: Verify mapping does not crash during Scenario Sweeper execution.

### 2. Clean Up Docker Compose Module Paths [P0]
- **File**: `docker-compose.yml`
- **Change**: Purge references to deprecated/non-existent `src.workers.ai_worker_daemon` and `src.utils.watchdog`. Keep only valid active services or set up distinct profiles.

### 3. Add Scenario-Specific Expectation Packs [P1]
- **Directory**: `src/observability/understanding/expectation_packs/`
- **New Files**:
  - `resource_economy.json`
  - `combat_heavy.json`
  - `peaceful_village.json`
  - `mixed_sandbox.json` (ensure this has full set of hard/warning/domain expectations)
- **Change**: ExpectationPackLoader should load scenario-specific packs and stop falling back silently without raising or indicating missing packs.

### 4. Standardize Artifact Schema & Hard-Law Persistence [P0]
- **Files**: `src/observability/warehouse/adapters.py`, `src/observability/event_recorder.py`, `src/observability/hard_law_monitor.py`
- **Change**: Standardize on `hard_law_violations.jsonl` everywhere. Make sure `HardLawMonitor` writes violations directly to `hard_law_violations.jsonl` via `RunArtifactRepository`.

### 5. Fix Determinism Auditor [P0]
- **File**: `src/observability/mining/auditors.py`
- **Change**: Ensure that when hashes are missing/empty, determinism audit returns `INSUFFICIENT_DATA` rather than `DETERMINISTIC`.

### 6. Exporter Metrics and Grafana Dashboard Alignment [P1]
- **File**: `src/observability/prometheus_collector.py`
- **Change**: Export all metrics referenced by Grafana dashboard (`sim_world_difficulty_mult`, `sim_faction_population`, `sim_entity_level_distribution`, `sim_items_crafted_total`, `sim_shop_transactions_total`, `sim_combat_events_total`, `sim_skill_events_total`, etc.).

### 7. ResourceProductionZero & Anomaly Rule Tuning [P1]
- **File**: `src/observability/anomaly/rules.py`
- **Change**: Update `ResourceProductionZero` to use actual production signals (e.g. resource harvested, node depletions, items crafted) rather than gold average.

### 8. Robust Parquet & PyArrow Optional Fallback [P1]
- **File**: `src/observability/warehouse/exporter.py`
- **Change**: Fall back to JSON or skip Parquet cleanly with an informative warning if `pyarrow` is not installed, preventing tests/CLI runs from failing unexpectedly.

### 9. Harmonize SimulationEvent Taxonomy [P1]
- **File**: `src/observability/events.py`, `src/observability/event_extractor.py`
- **Change**: Define canonical semantic names mapping low-level IDs to proper types (`combat_kill` -> `EntityKilled`, etc.).

### 10. AI Agent Heuristic Hardening [P1]
- **File**: `src/observability/mining/ai_agent.py`
- **Change**: Enhance the heuristic stub to validate and require spacetime evidence references before promoting findings.

### 11. Public Query SQL Protection [P2]
- **File**: `src/observability/warehouse/query.py`
- **Change**: Restrict public CLI/API queries to named queries only, disabling raw SQL input outside internal/dev modes.

## Verification Plan

We will add a robust suite of 21 tests covering all audited P0/P1/P2 behaviors.

### Automated Tests
- Run `pytest tests/unit/observability` and `pytest tests/integration/observability`.
- Add all new P0, P1, and P2 tests in a unified regression suite `tests/unit/observability/test_observability_hardening.py`.
