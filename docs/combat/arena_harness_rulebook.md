---
status: historical
layer: combat
authority: P2
audience: developer
---

# Arena Harness Rulebook (Milestone 6)

## Purpose
The Arena Harness provides an authoritative, deterministic, and repeatable validation surface for the combat and movement overhaul. It enables "pattern-based" regression testing, shifting away from brittle move-by-move equality assertions to higher-level behavioral envelopes (e.g., "Win rate for Ranged in open space should be >70%").

## Arena-Harness Boundaries
- **Authoritative Runtime**: The harness executes the real `WorldLoop`, `SystemManager`, and `ActionSystem`.
- **Infrastructure Isolation**: All external telemetry, network protocols (Kafka/RabbitMQ), and persistence layers are disabled or replaced with in-memory buffers.
- **Strict Determinism**: Multi-threading is disabled (`num_workers=1`) and all seeds are derived from a single scenario-root seed.

## Scenario Contract
Every scenario must define:
- `id`: Unique identifier (e.g., `SCN-100-KITING-OPEN`).
- `participants`: List of archetypes (`ParticipantProfile`) including role, gear, and level.
- `initial_placements`: Exact grid coordinates for all participants.
- `map_config`: Grid dimensions and material layout (e.g., `open_field`, `chokepoint_v1`).
- `stop_conditions`: A list of termination predicates (`Elimination`, `Timeout`, `Stalemate`).
- `iterations`: Number of runs to perform for statistical significance.

## Outcome-Pattern Semantics
The harness does **not** assert exact HP or tick counts. It asserts **Outcome Envelopes**:
- **Win Rate Pattern**: $P(win) \in [min, max]$.
- **Efficiency Pattern**: $Mean(TTK) < baseline$.
- **Stability Pattern**: $StallRate < threshold$.

## Metric Semantics
- `win_rate`: Percentage of iterations where the primary faction achieved victory.
- `avg_ttk`: Mean ticks until scenario resolution.
- `stall_rate`: Percentage of runs that triggered the `Stalemate` stop condition.
- `clumping_factor`: A measure of spatial dispersion (detected via `SpatialHash`).

## Non-Goals
- No second combat engine for testing.
- No scenario-specific hidden combat rules.
- No UI-level balancing dashboards (Metrics are emitted as JSON).

## Determinism Rules
- Randomness is governed by `DeterministicRNG` using the iteration index as a sub-seed.
- All iterations for a scenario must produce identical results when run with the same root seed.
