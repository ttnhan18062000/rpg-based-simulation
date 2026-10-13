---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261011-EVERY-LIVING-KIND-HEALS-NATURALLY-FASTER-AT-REST-ROW-65
artifact_type: investigation
phase: done
date: 2026-10-12
tags: []
---

# investigation: TCK-20261011-EVERY-LIVING-KIND-HEALS-NATURALLY-FASTER-AT-REST-ROW-65

The only HP writers outside combat were the town tile (1/tick), the paid inn rest, level-up and one core action (divergence 2.114 disclosure). The life-due branch of apply.py already holds the starvation HP term, so healing sits beside it and reuses the stage functions (starvation.recovery_scale, sleep_debt.recovery_scale) and sleep_debt.is_asleep. Two existing tests asserted health never changes while fed or sleep-indebted; they now assert none is lost. Measured result: see divergence 2.116 and probes/heal_measurement.txt.
