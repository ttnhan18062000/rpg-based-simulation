---
status: active
layer: engine
authority: P1
audience: developer
---

# Certification Contract

## Purpose
The Certification Contract defines the formal proof requirements for an engine run. Every certified run must evaluate a named scenario against a specific profile and record the results in a structured, machine-readable evidence set.

## 1. Certification Run Semantics
- **Atomic Evidence**: A certification run produces exactly one `certification_run.json` containing all measurements, hardware metadata, and conformance results.
- **Binding Law**: A run MUST explicitly bind:
    - `runtime_profile`: The authoritative budget contract used.
    - `scenario_id`: The formal stress/logic case being tested.
    - `detected_hardware_class`: The actual environment detected.
    - `effective_hardware_class`: The class used for throughput evaluation (may be overridden).
- **Seed Law**: All certification runs must be seeded for reproducibility.

## 2. Conformance Proof Taxonomy
A run is marked as `FAILED` if any of the following are observed:
- `FAILED_ENVELOPE`: Exceeded RAM/CPU/Queue ceilings defined in the profile.
- `FAILED_DEGRADATION_SEQUENCE`: The governor failed to shed load in the correct priority order. (An earlier version of this document called it `FAILED_DEGRADATION_ORDER`; the code's name is the reference.)
- `FAILED_RECOVERY_TIMEOUT`: The engine failed to return to NORMAL mode within the declared timeout after pressure was removed. (Earlier name `FAILED_RECOVERY`.)
- `FAILED_SEMANTIC_DRIFT`: The final authoritative hash (the proof digest, `docs/engine/deterministic_execution.md`) differs from the deterministic baseline run.
- `FAILED_REPORTING_INCOMPLETE`: Measurements were missing or corrupt.

## 3. Hardware Classification Rules (Proof-Stable)
**This section is the single definition of hardware class** (PERF-D4, approved 2026-10-03). Other documents refer here and do not restate the thresholds. `src/certification/hardware.py` (`HardwareClassifier.detect_class`) implements it.

Classification is binary and deterministic based on host resources at startup:
- **CLASS_A**: $\ge$ 16 Logical Cores AND $\ge$ 32GB Total RAM.
- **CLASS_B**: $\ge$ 4 Logical Cores AND $\ge$ 8GB Total RAM.
- **CLASS_C**: All other systems.
- **Override Rule**: Overriding hardware class is permitted for testing but MUST be recorded. The recorded field is `override_applied` in the evidence environment record (an earlier version of this document named it `hardware_class_override_applied`; the code's name is the reference).

## 4. Measurement & Sampling
- **Sampling Cadence**: Defined per scenario (e.g., sample every 10 ticks).
- **MeasurementPoint**: Contains tick, mode, memory (RSS), queue_utilization, and compute_time.
- **Baseline Equivalence**: Every certification run includes or references a `baseline_hash` established by a sequential (1-worker) reference run.

## 5. Reporting Law (Honest Language)
- **Law**: Performance claims are FORBIDDEN unless bound to `(Profile, Scenario, Hardware Class)`.
- **Labeling**: Reports must explicitly label "Forced" classes vs "Detected" classes.
- **Artifacts**: JSON is the source of truth. Markdown is a derivative summary.

## 6. Non-Goals
- No "Universal TPS" claims.
- No storageIO classification.
- No distributed cluster verification.
- No modification of kernel laws for benchmark vanity.
