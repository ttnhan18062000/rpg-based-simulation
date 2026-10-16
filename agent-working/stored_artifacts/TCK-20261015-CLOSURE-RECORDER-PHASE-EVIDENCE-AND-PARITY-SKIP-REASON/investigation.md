---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON
artifact_type: investigation
tags: [agent-monitoring, data-quality, workflows]
---

# investigation — TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON

Source: RETRO-2026-W41 final note findings 2 and 5. 330 of 337 W41+W42 runs were hand-closed and 246 of 278 W41 runs carry the fixed six-event template, so the Paths section reported Investigate/Plan/Review/Architecture-Verify omitted on 125 standard closures although 189 of 194 had artifacts. Parity was skipped on 22 W41 and 4 W42 runs whose Files Changed list `src/` with free-text reasons. The W42 Run Summary said `Gate failures 0` while the Gates section showed 22 blocking verdicts, because the line counts run final_status only. The order assumption of the ticket (artifacts moved before the recorder runs) holds either way: both folders are checked.
