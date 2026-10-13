---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261014-A-CONQUEST-NO-LONGER-SPAWNS-A-STRONGHOLD-BODY-D71
artifact_type: plan
tags: []
---

# plan — TCK-20261014-A-CONQUEST-NO-LONGER-SPAWNS-A-STRONGHOLD-BODY-D71

1. Remove `FactionInfluenceService.process_conquest_lifecycle` and `EntityGenerator.spawn_stronghold`.
2. Drop the lifecycle call site's generator and the merge of conquest adds and removals; keep the world-update merge and the vacancy signal.
3. Leave `process_influence_shift` and both thresholds (-50 conquest, +50 liberation) untouched; add no number.
4. Replace `test_stronghold.py` with forced-conquest tests; point the id-fix tests at a monster spawn.
5. Docs: divergence 2.123, PROG-136, Bible 05 Section 3 note.
