---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT
artifact_type: plan
tags: [simulation-quality, calibration, corpus]
---

# Plan — TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT

No implementation plan — this ticket resolves to a null result per its own Acceptance Criteria's
explicit escape clause ("If the conclusion is that no baseline actually drifted, that null result
is recorded with the evidence that supports it — a clean answer is an acceptable outcome").

## Steps taken
1. Enumerate every regression-tracked fixture Campaign mode could have a baseline in
   (`grade_anchors.json`, `expected_world_flag_state.json`, `FAST_ANCHOR_KEYS`) — found none.
2. Run the existing Campaign-mode test suite in full to confirm no hidden numeric-assertion
   regression exists anywhere else.
3. Run `campaign_life_arc` for real (both via `calibrate_simq.py` and via a direct instrumented
   `CampaignOrchestrator.run_episode()` call) to observe whether the PR #148-reactivated
   subsystems (war/siege, calamity) produce any real effect, rather than reasoning from code alone.
4. Peer review (`rpg-feature-planning`) caught that the first draft's Finding 3 conclusion
   ("structurally can't fire") overstated what the evidence (52-tick truncated episodes against a
   200-tick configured limit) actually supported. Corrected to the narrower, honest claim, and
   filed the truncation itself as its own ticket
   (`TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`) rather than either overclaiming or
   silently dropping it.
5. No `docs/guidelines/intentional_divergences.md` entry needed for this ticket specifically — the
   subsystems' own reactivation is already disclosed by `CAMPAIGN-REGION-PLACE-CARRY`'s own
   post-closure amendment; this ticket found no additional divergence to record, only a null
   baseline-drift result and a genuinely separate truncation bug.
