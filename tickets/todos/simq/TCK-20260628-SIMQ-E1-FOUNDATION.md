---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-SIMQ-E1-FOUNDATION
phase: open
date: 2026-06-28
tags: [simulation-quality, scoring, models, data-layer]
---

# TCK-20260628-SIMQ-E1-FOUNDATION

## Title
Simulation Quality Scoring — Core Models & Data Layer

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement the typed model layer and data persistence infrastructure for the Simulation
Quality Scoring Module. This ticket produces no user-visible behavior but is the
prerequisite for all subsequent scorer and hub implementation.

## Scope

### Config layer (data files — no logic)
- `config/simulation_quality/scoring_weights.yaml` — all per-pillar, per-rule delta
  magnitudes; no numeric literals may appear in scorer Python files
- `config/simulation_quality/grade_thresholds.yaml` — S/A/B/C/D/F normalized score
  boundaries (initial estimates; calibrated in E7-CALIBRATE)
- `config/simulation_quality/detection_params.yaml` — loop detection threshold (0.70),
  window size (200), time-gate tick values (e.g., stasis_gate_ticks: 5,
  zero_harvest_after_tick: 100), MAX_WORST_EVENTS (100)
- `config/simulation_quality/profiles/default.yaml` — all pillar weights = 1.0

### Python layer (logic only)
- `src/simulation_quality/__init__.py`
- `src/simulation_quality/pillars.py` — `PillarId` enum (10 values), `PILLAR_METADATA`
- `src/simulation_quality/weights.py` — `ScoringWeights` Pydantic model: loads and
  validates the config YAML; provides typed accessors `w["rule_key"] -> float` and
  `w.int("gate_key") -> int`; raises `ValidationError` on malformed config at startup
- `src/simulation_quality/score_record.py` — `ScoreRecord` frozen dataclass,
  `ScoringContext` frozen dataclass
- `src/simulation_quality/pillar_accumulator.py` — `PillarAccumulator` (thread-safe
  `raw_score`, `event_count`, `negative_count`, `worst_events` bounded list,
  `window_buffer` deque, `loop_flags` set, `add()`, `snapshot()`)
- `src/simulation_quality/quality_report.py` — `QualityReport` dataclass,
  `QualityReportBuilder.build()` from accumulator snapshots, grade assignment using
  thresholds from `ScoringWeights`, overall_score computation
- `src/simulation_quality/persistence.py` — `QualityPersistence`: writes
  `quality_scores.jsonl` (non-blocking append), writes `quality_report.json` at run end

## Out of Scope
- QualityHub subscriber wiring (E2)
- Any pillar scorer logic (E2–E4)
- REST API routes (E5)

## Acceptance Criteria
- [ ] `PillarId` has exactly 10 values matching contract §5
- [ ] `ScoreRecord` is frozen, all fields typed, `tags` is `tuple[str, ...]` not `list`
- [ ] `ScoringWeights` loads and validates `scoring_weights.yaml` via Pydantic;
  raises `ValidationError` at startup for malformed or missing keys
- [ ] `ScoringWeights` loads `grade_thresholds.yaml` and `detection_params.yaml`
- [ ] No numeric delta literals appear anywhere in scorer files — all values via `self.weights`
- [ ] `PillarAccumulator.worst_events` never exceeds `MAX_WORST_EVENTS` (read from config)
- [ ] `PillarAccumulator.window_buffer` is `deque(maxlen=W)` where W is from config
- [ ] `PillarAccumulator` is thread-safe: `add()` uses a lock
- [ ] `QualityReport.build()` reads grade thresholds from `ScoringWeights`, not from constants
- [ ] `QualityReport.build()` produces correct normalized scores and health grades
- [ ] `QualityPersistence` writes to `data/runs/{run_id}/quality_scores.jsonl`
- [ ] `QualityPersistence` writes to `data/runs/{run_id}/quality_report.json`
- [ ] All persistence writes are non-blocking (async or fire-and-forget)
- [ ] Unit tests for: `ScoringWeights` load + validation, `PillarAccumulator.add()`,
  `worst_events` ceiling, `window_buffer` overflow, `QualityReport.build()` grade assignment,
  `QualityPersistence` file output, config missing-key raises at startup not silently at score time

## Related Tickets
- Parent: TCK-20260628-SIMQ-EPIC
- Next: TCK-20260628-SIMQ-E2-HUB-CORE (requires this foundation)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §4 (Score Model)
- `docs/simulation_quality/quality_scoring_contract.md` §8 (Persistence schema)
- `docs/simulation_quality/quality_scoring_contract.md` §3.2 (Overhead Budget)

## Implementation Notes
Grade thresholds in `pillars.py` are initial estimates; they will be calibrated in
E7-CALIBRATE. Mark them with a comment noting they are pre-calibration estimates.

`PillarAccumulator.snapshot()` must return an immutable view — do not return the
mutable `worst_events` list directly. Return a frozen copy.

`ScoringContext.pillar_scores` must be a `Mapping` (read-only), never a mutable dict.
