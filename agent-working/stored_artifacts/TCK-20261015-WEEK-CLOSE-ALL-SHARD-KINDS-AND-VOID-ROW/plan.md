---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261015-WEEK-CLOSE-ALL-SHARD-KINDS-AND-VOID-ROW
artifact_type: plan
tags: [agent-monitoring, data-quality]
---

# plan — TCK-20261015-WEEK-CLOSE-ALL-SHARD-KINDS-AND-VOID-ROW

1. Add gate_verdicts to the week-close kinds. 2. Void: a typed row in the working_log shard family; the fold applies it and records it in a per-week voids file; the pending-shard parser applies it so every reader agrees. 3. Stage the void for the DEPENDABOT row. 4. Fold W41. Rejected: deleting the pending row (a silent delete) and editing the other shard (not ours to edit).
