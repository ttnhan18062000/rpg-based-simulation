---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261019-RECORD-BASELINE-V1
artifact_type: investigation
tags: []
---

# Investigation — TCK-20261019-RECORD-BASELINE-V1

- Main moved from 5c9b84505 to 864f7b281 (#647, #659: tests/CI only; nothing under src/config/data). Lane C proved the simulation byte-identical from 6d7bd1509 through df3cb7256 and d6959714d.
- behavioral_5k fails on df3cb7256 (alive_avg 24.64 vs 13.30, gold_avg 0.0 vs 584.16, quest_active_count 6.12 vs 0). The test builds its Kernel without audit_mode, so a baseline from it can depend on host speed.
- Dry-run timings: paired 6 runs 35 min (jobs 2, shared host); behavioral_5k 5 min 21 s per run.
