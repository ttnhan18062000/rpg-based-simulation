---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02
artifact_type: report
tags: [economy, resource]
---

# arm7 ablation and starvation trace (scripts: trace2.py, an2.py; paired scripts: chain_ms.py, agg.py)

arm1 = main (edda25490), arm6 = batch 2, arm7 = batch 2 with declared inventory profiles NOT applied at spawn. Pinned NORMAL, 5000 ticks, seeds 42-46.

## Paired flags (>2 SE) in arm6 vs arm1, and what arm7 shows (means over 5 seeds)
| Flag | arm1 | arm6 | arm7 | Reading |
|---|---|---|---|---|
| living raiders alive @1000 | 4.2 | 1.8 | 3.0 | partly profile; closes by 2500 |
| living heroes_other starved | 5.2 | 7.0 | 6.6 | NOT profile (persists); trace: no batch-2 path |
| urban guards starved | 1.6 | 3.2 | 1.6 | profile content; mechanism open |
| living wildlife alive @1000 | 1.4 | 3.4 | 1.6 | profile content; @5000 not flagged |
| crowded heroes_other ever-ate | 1.6 | 0.0 | 1.2 | profile content |
| urban heroes_other starved | 1.8 | 0.8 | 1.8 | profile content (improvement) |
| urban alive total @1000 | 21.6 | 22.8 | 21.8 | profile content |
| tax paid by the poor, living / urban / crowded | 72 / 44 / 50 | 124 / 79 / 86 | 54 / 49 / 71 | profile coin is taxed |
Comparison count: 91 paired comparisons per table; flags >2 SE: 13 (arm6 v arm1), 7 (arm7 v arm1), 14 (arm7 v arm6); lines are not independent.

## Deaths by cause, 5 seeds pooled
| Group | arm | total | STARVATION | COMBAT | DEFEAT | other |
|---|---|---|---|---|---|---|
| living heroes_other | arm1 | 40 | 26 | 4 | 10 | |
| living heroes_other | arm6 | 40 | 35 | 1 | 4 | |
| living heroes_other | arm7 | 39 | 33 | 3 | 3 | |
| urban guards | arm1 | 37 | 8 | 16 | 1 | HAZARD 8, SLEEP_DEPRIVATION 4 |
| urban guards | arm6 | 39 | 16 | 10 | 3 | HAZARD 8, SLEEP_DEPRIVATION 2 |
| urban guards | arm7 | 38 | 8 | 16 | 4 | HAZARD 8, SLEEP_DEPRIVATION 2 |

## Victim pattern (non-combat victims)
- Heroes: no EAT / TOWN_SERVICE / CARRIED_FOOD / FORAGE event of any kind (accepted or rejected) in any arm; 12-60 tiles from the nearest inn; leash and intercept moves.
- Guards: no rejected meal in any arm; 9 of 16 arm6 starvation victims (3 of 8 arm1, 4 of 8 arm7) died hundreds of tiles outside the map while pursuing / intercepting.
- No SELL, WORK, SHOP or BUY payload in any victim's last decisions; gold at death never negative.
