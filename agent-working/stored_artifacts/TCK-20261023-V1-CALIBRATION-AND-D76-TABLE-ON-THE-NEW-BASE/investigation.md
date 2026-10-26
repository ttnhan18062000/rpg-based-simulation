---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE
artifact_type: investigation
tags: []
---

# Investigation — TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE

- make evaluate-full is tools/evaluate_simq.py. It reads and requires the host-independence sidecar; in live mode it imports tools.calibrate_simq, which writes it (write_sidecar, calibrate_simq.py:605-606).
- data/calibration/ is gitignored (.gitignore:251): the calibration cannot be committed, so it is handed over by path.
- The D76 rule is roadmap 12.3 (decision 76); the live table is rpg-planner's draft outside the repo, which rpg-planner updates itself.
- Expected: old anchors predate v1, so REGRESS rows (285; 272 no-data) are the min-events rule plus the v1 world; testing's re-anchor covers them.
