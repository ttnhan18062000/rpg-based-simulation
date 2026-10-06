---
status: active
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE
artifact_type: plan
tags: [engine, combat]
---

# Plan

Planner ruling, option C (2026-10-06):
1. Leave `resolve_live_tracking_target` unchanged.
2. Record BRACKETING as de-facto pursuit in the tactical contract, divergence 2.70 and parity COMB-331, citing `movement.py:242-243` and the diagonal-flank distance.
3. Keep `bracket_pos` in `tactical.py`: it gates issuance (investigation section 4). The planner's instruction was to keep it if anything reads it.
4. File the latent `SEEK_COVER` case as a trigger ticket with the arrival-end rule as the candidate fix needing an owner decision.
5. Close this ticket as resolved by recording.
