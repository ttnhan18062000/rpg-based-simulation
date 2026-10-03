---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260424-PH12-M4-CUTOVER-VALIDATION
artifact_type: plan
tags: [ph12, m4, cutover, validation]
---

# Phase 12 Milestone 4 Execution Plan: Cutover Validation

## 1. Real-Condition Simulation (V2 Default)
- Command: `python3 -m src cli --ticks 1000 --seed 42 --entities 50`
- Metric: Ensure completion in under 30s with stable RAM (<512MB).
- Verification: Check for `Tick 1000 complete` and `Replay written to replay.json`.

## 2. Rollback Integrity Test
- Command: `USE_LEGACY_SRC=1 python3 -m src cli --ticks 100 --seed 42 --entities 50`
- Verification: Confirm legacy logging (`registry_loader`) and `replay.json` generation.

## 3. Artifact Parity Audit
- Compare `replay.json` from a V2 run and a Legacy run for structural (schema) consistency.
- Ensure all "Allowed" fields (Position, State, Readiness) are present in both.

## 4. Final Verdict
- Compile findings into `investigation.md`.
- Authorization for Milestone 5 (Default-Authority Transition).
