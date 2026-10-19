---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261010-CAMPAIGN-EPISODE-COOPERATION-SHARE-CROSSES-HALF-ON-MAIN-AFTER-BATCH-2
date: 2026-10-16
tags: []
---

# Investigation: TCK-20261010-CAMPAIGN-EPISODE-COOPERATION-SHARE-CROSSES-HALF-ON-MAIN-AFTER-BATCH-2

Method: the test's own `_run_episode` (seeds 42 and 1337, 70 ticks, audit_mode) run on slim `git archive` trees; bisect over the rpg-next first-parent range 20af2959a..5829b1986, then inside the pre-squash branch rpg-single-pr (scripts in probes/).

Causes of the share 0.51 -> 0.70 (pooled):
- A (plant-eater commit 8464582f5, TCK-20261009-GENERIC-PLANT-EATER-ARCHETYPES-GRAZE-AND-FLEE-DECISIONS-45-50): 0.5167 -> 0.598. A herd adds alive entities (+13% evaluations); the herd is hunted, so combat_support_needed (206/218 -> 373/330 events) and healer_needed (5/22 -> 47/67) rise; cooperation events 885 -> 1359.
- B (merge 8a40fb79b of rpg-fold-next, the treasury batch): 0.5815 -> 0.7005. Cooperation barely moves (1348 -> 1450); gold_sink_fired (the per-head TAX, 162 + 168 events, 14% of the stream) disappears, so total events fall 2318 -> 2070. Inferred from the commit lists and the event change; not bisected inside the merge.
- With B's events put back the tip would still be about 0.60 because of A.

Why a ratio over all events is the wrong measure: step B shows it moves when an unrelated event type is retired.

The original bug the test guards (TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING, fixed by real per-entity spawn positions): every spawned entity on one tile inflated cooperation to ~79% of the stream. Re-introduced in a scratch copy of the tip (all entities placed on the first entity's tile): pooled share 0.761, cooperation per entity-tick 0.451 (combat_support_needed 1276 vs about 380 events; hostiles adjacent from tick 1 give HIGH combat risk). Check (a) still PASSES there (co-located entities still produce typed help needs), check (b) FAILS (0.4513 > 0.30). So (b) is the check that catches the bug; (a) guards the structure only.

Basis of the tip's 1450 cooperation events: help need 848 (58%), group member with no need 541 (37%), incoming offer 61 (4%). An "every event carries a help need" assertion would therefore be false on a healthy tree.

Measured cooperation per entity-tick (pooled): c35ebf475 0.13-0.15 (pre-determinism-fix commit, varies run to run), 8464582f5 0.19, tip 5829b1986 0.2107 (deterministic). Ceiling 0.30 (tip + 42%; co-location 0.451).
