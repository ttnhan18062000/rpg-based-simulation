---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE
artifact_type: plan
tags: []
---

# Plan — TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE

1. Run tools/evaluate_simq.py (make evaluate-full) from the v1rec worktree: src is identical to the v1 record 341f700d0 (e8df8b96d), checked with git diff, so no detached pin.
2. Confirm quality_report.run_determinism.json (run_id, audit_mode, signals_zeroed) in every calibration dir; a missing one is a STOP, fixed by hand never.
3. Hand the paths to testing-planner (anchors are testing's).
4. Re-point the D76 base in roadmap 12.3 to 341f700d0 with 903239fbe as history, consistent with 12.5.
Out of scope: anchor values, any simulation change.
