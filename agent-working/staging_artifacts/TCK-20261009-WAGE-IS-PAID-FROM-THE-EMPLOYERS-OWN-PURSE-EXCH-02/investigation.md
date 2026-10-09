---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02
artifact_type: investigation
tags: [economy, resource]
---

# investigation — TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02

## Findings
A WORK shift (200 ticks) pays 6 gold from the inn's own purse to the worker, one transaction per shift (a held action executes twice per tick, so the shift id is carried in the held payload). Divergence 2.102.

## Code areas
`src/engine/work_shift.py`, `src/core/conservation.py`, `src/engine/blacksmith.py`

## Evidence
Paired pinned measurements (5 seeds x 3 worlds, 5000 ticks, kind groups) are in the PR; the earlier 4-arm table is in the removal-evidence probes directory.
