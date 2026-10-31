---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-HAND-CLOSE-REVIEW-PHASE-RECORDS-THE-PR-REVIEW
artifact_type: investigation
tags: [agent-monitoring, governance]
---

# Investigation

- `record_hand_orchestrated_closure.py::folded_phase_events` writes Review and Architecture-Verify as `skipped`/`no_hand_tool` for every standard/epic closure whose tier plan marks them `full` and whose closer narrated none. It skips a phase the closer already narrated (`given`), so a narrated Review event is kept as is.
- `path_report.analyze` counts a phase as `ran` when any event for it has `status != skipped`, so a Review recorded `ok` leaves the skipped count and the routing candidate (`routing()`, share of runs skipped or omitted) drops by itself. Only the explanatory text needs to say so.
- Owner decision (a), #715 6545962757: `--review-ref <PR#>#<comment id>` records Review `ok` with the ref; no ref keeps today's event, so a really missing review still shows. Architecture-Verify is unchanged. (b) is out of scope.
- The tier plan decides where Review exists: hotfix lists it `skipped_event`, so `full_phases("hotfix")` has no Review and the ref has nothing to attach to.
- Existing tests: `tests/tools/test_closure_recorder_folded_phases.py` covers the folded events; `tests/tools/test_path_report*.py` the routing text.
