# Milestone 7: Structured Reason Migration & Documentation Integrity

This milestone finalizes the Combat and Movement Overhaul by hardening the observability contract. It ensures that every action decision — whether accepted or rejected — is traceable via a structured `ActionReason` schema, and that these outcomes are aggregated into the Arena reports for deep stability auditing.

## User Review Required

> [!IMPORTANT]
> **Authoritative Schema**: `ActionReason` is now the **authoritative** model. Legacy `str` is strictly for compatibility/output only. All new engine, legality, and tactical code MUST emit structured reasons.
> **Explicit Rejection Auditing**: Only authoritative rejections (actions dropped by legality, conflict resolution, or interaction services) will be tracked. "AI considerations" that weren't proposed are NOT rejections.

## Proposed Changes

### [Component] Core Models & Observability

#### [MODIFY] [arena.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/arena.py)
- Extend `ArenaResult` to include `rejection_counts: Dict[str, int]`.
- Extend `ScenarioReport` to include `avg_rejection_counts`.

#### [MODIFY] [metrics.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/arena/metrics.py)
- Update `MetricService` to helper with rejection aggregation.

---

### [Component] Legality & Action Validation

#### [MODIFY] [legality_service.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/logic/legality_service.py)
- Update validation methods to optionally return or support building `ActionReason` (e.g., distinguishing between Out-of-Range vs No-LOS).

#### [MODIFY] [move.py](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/move.py)
- Populate `ActionReason(code=ReasonCode.OCCUPANCY_VIOLATION)` or `PATH_NOT_FOUND` on validation failure.

#### [MODIFY] [combat.py](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/combat.py)
- Populate `ActionReason(code=ReasonCode.OUT_OF_RANGE)` or `TARGET_INVALID` on validation failure.

---

### [Component] Tactical AI & Engine

#### [MODIFY] [tactical_evaluator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/tactical/tactical_evaluator.py)
- Replace `ReasonCode.LEGACY_FALLBACK` with specific codes: `ADVANCING`, `KITING`, `ALLY_SPACING`, etc.

#### [MODIFY] [runner.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/arena/runner.py)
- Aggregate explicit rejections where `proposal.reason` is an `ActionReason` with `is_rejection=True`.
- **Constraint**: No set-diff inference; only count explicitly emitted rejections.

---

### [Component] Documentation

#### [NEW] [overhaul_spec.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/overhaul_spec.md)
- Consolidate all milestone rules (Legality, LOS, Tactical Modes, Stat Diminishing Returns) into a single authoritative reference.

## Verification Plan

### Automated Tests
- **Rejection Audit Test**: Execute a scenario with heavy congestion and verify that `ScenarioReport` contains non-zero `rejection_counts` for `occupancy_violation`.
- **Reason Traceability Test**: Verify that a Movement action in the log contains a structured `ActionReason` with the correct `ReasonCode`.

### Manual Verification
- Review the generated `ScenarioReport` to ensure the new metrics are human-readable and accurate.
