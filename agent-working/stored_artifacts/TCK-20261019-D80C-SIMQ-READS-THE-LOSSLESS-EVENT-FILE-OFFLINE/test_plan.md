---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE
artifact_type: test_plan
tags: [observability]
---

# Test plan — TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE

Unit: refusal without the file; byte-identical report and scores on two replays; per-type counts; unreadable lines counted; offline equals live hub on the same events; scoring-off refusal; host-independence refusal. Scoped existing: test_calibrate_simq, test_report, test_evaluate_harness, test_calibrate_world_loading. Real run: a frozen prefix of a measurement run scored twice through `tools.simq_score_run`.
