---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-RECALIBRATION
artifact_type: plan
tags: [content, determinism]
---

# Plan — TCK-20260902-PLACE-MIGRATION-RECALIBRATION

1. Confirm `canonical_state_hash` (not `state_hash`) is the correct signal for the state-hash-first
   check, per Stage A's own finding.
2. Confirm all 21 worlds' isolation property (already established in Stage A/B) applies as the triage
   conclusion for the state-hash-first check — no new work needed here.
3. Run the full 81-run_key `grade_anchors.json` sweep, comparing fresh recalibration against committed
   anchors using their own stated tolerance rules.
4. For any drift found, do NOT assume it's caused by idea 66 — test causally by reverting content and
   re-running a sample drifted run_key.
5. Based on the causal test's result, classify all drift as either a real regression (own hotfix ticket)
   or pre-existing staleness (documented in the existing follow-up ticket, broadened if needed).
6. Record the final triage conclusion and close the epic.
