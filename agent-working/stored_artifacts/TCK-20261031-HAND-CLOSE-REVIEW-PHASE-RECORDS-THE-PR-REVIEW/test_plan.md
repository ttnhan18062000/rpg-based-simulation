---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-HAND-CLOSE-REVIEW-PHASE-RECORDS-THE-PR-REVIEW
artifact_type: test_plan
tags: [agent-monitoring, governance]
---

# Test plan

- Unit: `review_ref_event` shape; ref validation (`12#345` ok; `12`, `#345`, `12#`, `a#1`, empty refused).
- Recorder: standard closure with a ref gets Review `ok` with the ref in its summary, in plan order, Architecture-Verify still `skipped`/`no_hand_tool`; without a ref the added events equal today's (compare against `folded_phase_events`); hotfix with a ref exits 1 and writes nothing; a narrated Review plus a ref exits 1.
- path_report: a run whose Review is `ok` is not counted skipped, and a group of such runs is not a routing candidate for Review while Architecture-Verify still is.
- Command: `pytest tests/tools -k "hand_orchestrated or retro or closure" -p no:randomly`, serial; the full `tests/tools/test_closure_recorder*.py` and `test_path_report*.py` files.
- PR body: a W44-shaped Phase Status sample before and after (synthetic, built from the 37 standard rows).
