---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-RECALIBRATION
artifact_type: test_plan
tags: [content, determinism]
---

# Test Plan — TCK-20260902-PLACE-MIGRATION-RECALIBRATION

**Normal flow:** a world with an unchanged `state_hash` is recorded lossless with no grade run.

**Edge cases:** a world whose hash changes but whose grade shift stays within `grade_anchors.json`'s
tolerance band — still requires a recorded triage note explaining why, not silently passed as "within
tolerance therefore fine" (tolerance passing is not the same claim as "confirmed compile-shape noise").

**Failure modes:** a real gameplay regression hiding behind a hash change that gets mis-triaged as
compile-shape noise — cross-check any "noise" triage against the actual semantic diff, not just the
grade delta.

**Regression-prone paths:** all 84 committed `run_keys`, not just the 21 top-level world hashes.

**Scope command:** `pytest tests/simulation_quality/ -k "grade_anchors" -m "not slow"` for the grade-shift
re-run mechanics; `state_hash` diffing is a script-level comparison, not a pytest suite.
