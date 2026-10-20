---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-RPG-GATE-EVERY-VALIDITY-ROW-HAS-A-KERNEL-POSITIVE
artifact_type: investigation
date: 2026-10-20
tags: [testing, regression, simulation-quality]
---

# Investigation — TCK-20261019-RPG-GATE-EVERY-VALIDITY-ROW-HAS-A-KERNEL-POSITIVE

## Findings
- #682 is on main: all eight kernel positives exist (V1 and V4 in their own files, V2/V3/V5-V8 in test_gate_validity_checks_fire_through_the_real_kernel.py) and collect (12 tests including the two controls).
- The tests reach `build_kernel` through helpers: `run_gate_metrics` in the shared file (also imported by the V1 file, a one-hop import) and `_v4_row` in the V4 file. V7 reaches `pool` through a run helper.
- config.yaml `required_validity` is `{run: [V1..V6, V8], pooled: [V7]}`.

## Decisions
- Static (ast) check, no import of the tests. It follows same-module functions and imports from repo modules (depth 4), and requires both a `build_kernel` call and a `compute`/`pool` call (rpg-planner's lesson: V4 once asserted a private counter). What a test asserts stays with review; the format doc says so.

## Risks
- A helper reached through a dynamic call is not followed; a test like that fails the lint rather than passing silently.
