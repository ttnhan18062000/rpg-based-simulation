---
status: active
layer: engine
authority: P1
audience: developer
---

# `src` Known Limitations

This document records the current technical limitations, unsupported features, and runtime constraints of the `src` engine.

> **Machine-readable state:** For a queryable capability matrix, see `docs/engine/capability_registry.yaml` and `src/engine/capability.py`. This document keeps only human-readable context and notes.

## 1. Gameplay / Mechanics Limitations

### 1.1 Spatial / Navigation
- **Linear Stepping Only**: Pathfinding through dynamic obstacles (e.g., other entities or newly spawned objects) is best-effort. V2 currently relies on direct linear stepping toward coordinates for supported proofs.
- **Congestion Weakness**: While congestion is handled by yielding, high-density entity overlaps are not yet hardened against all edge cases.

### 1.2 Resource loops
- **No Complex Regeneration**: Resource nodes do not currently support complex regeneration logic (e.g., seasonal growth, depletion cooldowns). Nodes are static or reset on scenario reload.
- **Town Buildings**: `TownResolutionSystem` currently supports Blacksmith (crafting), Inn (REST), and Tavern (EAT) building types. Guilds, Class Halls, and other building types are not yet functionally integrated.

### 1.3 Strategic AI
- **Material-Only Blockers**: The `StrategicIntelligenceSystem` only recognizes and resolves crafting blockers for "Material" resources. Social, capability, or plot-based blockers are unsupported.
- **Location-Only Leads**: Strategic leads are restricted to coordinate-based locations. Concept or person-based leads are not yet modeled in the supported slice.

### 1.4 Commerce Limitations

- **Reputation-based shop discounts** — Previously unsupported. **Now implemented** as of TCK-20260619-E33D-REP-DISCOUNTS. Formula and mechanics: see `docs/mechanics/03_economic_laws.md §4.1`. Faction-scoped discounts remain out of scope (no per-faction reputation dict on `SocialComponent` — DEV-001).

### 1.5 Feature Flag Defaults (Phase 10 Rollout Gates)

All 10 Phase 10 feature flags in `src/domains/optimization/feature_flags.py` default to
`FeatureMode.OFF`. The flags are:

- `ENABLE_WORLD_CAPABILITY_LAYER`
- `ENABLE_SELF_MODEL_COGNITION`
- `ENABLE_ADVENTURE_ROUTING`
- `ENABLE_COMBAT_ENGAGEMENT`
- `ENABLE_BELIEF_ASSIMILATION`
- `ENABLE_PROGRESSION_EVOLUTION`
- `ENABLE_SOCIAL_COOPERATION`
- `ENABLE_WORLD_EMERGENCE`
- `ENABLE_LIFE_ARC_CAMPAIGNS`
- `ENABLE_ENHANCED_TRACE_EVENTS`

**Implication for balance and behavioural measurement:** Any scenario or test that needs to
measure behaviour gated behind one of these flags must explicitly enable the flag via the
`overrides` constructor argument or `FeatureFlagManager.set_flag_mode()`. The existing
`_build_kernel(enable_routing=True)` pattern in
`tests/integration/scenarios/test_balance_regression.py` is the canonical example.

**Do not change the default to `ON` without first re-running `tools/balance_measure.py`** on
the affected scenario (e.g. `urban_political`, seed 42, 100 ticks) to establish new baseline
constants, and updating the corresponding constants in `test_balance_regression.py`.

The sentinel test `test_adventure_routing_defaults_off()` in
`tests/integration/scenarios/test_balance_regression.py` guards the `ENABLE_ADVENTURE_ROUTING`
default. If you intentionally change the default to `ON`, that test will fail with an explicit
error message and instructions for updating the baseline.

Decision recorded in `docs/guidelines/intentional_divergences.md` § DEV-002
(TCK-20260627-P0A-ADVENTURE-FLAG).

## 2. Runtime / Performance Constraints

### 2.1 Execution Modes
- **Worker Parity**: While concurrency (Thread/Worker) is implemented, bit-identical parity vs original `src` is only officially ratified for the **Sequential** execution mode.

### 2.2 System Contention
- **Deterministic Resolution**: Contention for limited resources (e.g., two entities looting the same corpse) is resolved by deterministic registration order. Complex social negotiation or "roll-off" logic is not yet implemented.

### 2.3 Phase Isolation Detection

**Isolation breaches in non-audit phases are only fully caught in `audit_mode=True`.**

The Kernel's `_guard_stability()` method fingerprints the full `AuthoritativeState` (SHA-256 over all fields) before read-only phases (Scheduling, Collection) and raises `ProtocolViolationError` on any mutation. This full check is **only active when `Kernel` is initialized with `audit_mode=True`** (used in certification scenarios — see `src/certification/harness.py`).

A **lightweight gross isolation guard** (`_guard_gross_isolation()`) runs unconditionally in standard (non-audit) mode. It checks only `len(state.entities)` and `state.tick` — two O(1) integer reads with negligible overhead on all hardware classes. This detects:
- Entity creation or deletion mid-phase (gross lifecycle violation)
- Tick number advancing outside the authoritative pipeline

It does **not** detect field-level mutations within existing entities (e.g., an HP change during Collection). Those require `audit_mode=True`.

**Summary of detection coverage by run mode:**

| Violation type | Standard mode | `audit_mode=True` |
|---|---|---|
| Entity count change mid-phase | Detected (lightweight guard) | Detected (full hash) |
| Tick advancement mid-phase | Detected (lightweight guard) | Detected (full hash) |
| Field-level mutation within entity | **Not detected** | Detected (full hash) |

Source: D09 Finding 5 (Risk 11/15). Ticket: TCK-20260627-P1G-STABILITY-GUARD.

### 2.4 Canonical State Hash Availability by Runtime Mode

`_phase_persistence()` in `src/engine/kernel.py` records a `tick_hash` value in the
`TICK_END` replay event. Whether that value is a real SHA-256 or the sentinel string
`"SKIPPED"` depends on the active `GovernorPolicy`:

| RuntimeMode | `replay_richness` | `replay_allowed` | TICK_END `hash` value |
|---|---|---|---|
| NORMAL | "FULL" | True | SHA-256 canonical hash |
| CONSTRAINED | "FULL" | True | SHA-256 canonical hash |
| DEGRADED | "MINIMAL" | True | `"SKIPPED"` |
| SURVIVAL | "OFF" | False | no TICK_END event emitted |

In **NORMAL** and **CONSTRAINED** modes — the two most common runtime configurations —
`replay_richness == "FULL"`, so `CanonicalStateHasher.get_hash()` runs on every tick
and the canonical SHA-256 is present in every `TICK_END` event.

In **DEGRADED** mode, `replay_richness` drops to `"MINIMAL"` to shed hashing overhead.
The `TICK_END` event is still emitted, but `hash` is the literal string `"SKIPPED"`.
Consumers inspecting TICK_END sequences in DEGRADED-mode runs must handle this sentinel.

In **SURVIVAL** mode, `replay_allowed = False`: no TICK_END event is emitted at all.

The **final canonical hash** (`CanonicalStateHasher.get_hash()` called in `Kernel.shutdown()`)
is always computed regardless of mode — it is not gated on `replay_richness`.

#### Lightweight fingerprint (`StateFingerprinter`)

In all modes where `replay_allowed = True` (NORMAL, CONSTRAINED, DEGRADED), the
`REFINED_UPDATE` event includes a `"fingerprint"` key populated by
`AuthoritativeState.fingerprint()` → `StateFingerprinter.get_fingerprint()`.

This fingerprint covers the following domains:

- Entity identity, position, HP, gold, readiness, lifecycle, skills, inventory, bonds, reputation
- Full per-entity strategic state (projects, blockers, leads, directives, concerns, contracts, boredom)
- Global resources, resource nodes, regions, local scars, groups, macro world state

The fingerprint uses **MD5** (not SHA-256). It is a broad-coverage dirty signal, not a
cryptographic determinism proof. It is the primary per-tick observability signal in
DEGRADED mode, where the canonical hash is skipped.

**Fields present in `CanonicalStateHasher` but absent from `StateFingerprinter`:**
buildings, corpses, ground\_items, chests, home\_storage, camps, blocked\_tiles, town\_tiles,
building\_tiles, periodic\_due\_ticks, work\_debt, rng\_checkpoint.

Divergences in those domains are not captured by the fingerprint. The canonical SHA-256
remains the authoritative determinism proof for complete state verification.

Source: D09 Finding 6 (Risk 8/15). Ticket: TCK-20260627-P2F-CANON-HASH-DOC.

## 3. Tooling / Observability
- **Metric Granularity**: Some runtime signals (e.g., per-entity strategic bandwidth) are visible in the engine but not yet exported to the external Prometheus/Grafana baseline.

---
*Last updated: 2026-06-27.*
