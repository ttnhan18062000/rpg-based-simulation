---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT
artifact_type: test_plan
tags: [simulation-quality, calibration, corpus]
---

# Test Plan — TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT

No code changed by this ticket, so no new automated test is added. Verification is the
investigation evidence itself:

1. `grep -rn "campaign" tests/simulation_quality/fixtures/grade_anchors.json
   tests/simulation_quality/fixtures/expected_world_flag_state.json` — zero hits (Finding 1).
2. `pytest tests/integration/campaigns/ tests/unit/domains/campaigns/ -m "not slow and not
   extra_slow"` — 154 passed, 0 failed (Finding 2).
3. Real `campaign_life_arc` runs (both `tools/calibrate_simq.py` and a direct instrumented
   `CampaignOrchestrator.run_episode()` call) — real observed state inspected directly, not
   inferred (Finding 3).

Re-ran step 2 once more at closure time to confirm no regression was introduced between
investigation and closure.
