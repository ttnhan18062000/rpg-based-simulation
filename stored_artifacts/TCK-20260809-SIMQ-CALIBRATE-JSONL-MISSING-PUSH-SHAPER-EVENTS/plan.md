---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS
artifact_type: plan
tags: [simulation-quality, combat, observability]
---

# Plan — TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS

## No code fix lands in this ticket
`investigation.md` definitively rules out the originally-suspected calibration-tool/JSONL-
persistence bug via 3 controlled A/B tests — file and in-memory recorder always match exactly.
The real cause was a methodological inconsistency in the sibling
`TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK` ticket's own verification (using
`ENABLE_COMBAT_ENGAGEMENT=ON`, inconsistent with the rest of this session's own established
corpus-default methodology), not a defect in `tools/calibrate_simq.py`, `EventRecorder`, or
`event_shapers.py`. No production code needs to change.

## Real correction: the sibling ticket's own closed record
`TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK` is already closed (DONE) with a conclusion
now known to be based on flawed methodology. Per this session's own established precedent
(the correction addenda already added to `COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE` and
`COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE` earlier), the responsible action is a visible
correction addendum to that ticket's own record — not a silent rewrite — documenting the real,
correct-methodology finding (COMBAT pillar events under corpus-default flags do include all of
this session's new event types; grade stayed C in both worlds under the correct methodology too,
a small honest improvement in norm visible but not enough to cross a grade boundary).

## Real, disclosed follow-up: `ENABLE_COMBAT_ENGAGEMENT=ON`'s own real suppression effect
A new, real, unexpected finding (the flag appears to suppress the tactical.py/event_shapers.py
combat path, contradicting its own documented "gates posture assessment only" scope) is
disclosed in `investigation.md` but deliberately not investigated further here — out of this
ticket's own proportionate scope. Filed as its own dedicated follow-up ticket.

## Verification plan
Already complete — the real, controlled A/B tests documented in `investigation.md` (3 separate
real runs: with-flag ×2, without-flag ×1 via direct probe, plus 3 real `tools/calibrate_simq.py`
invocations without the flag) constitute the real verification for this ticket's own closure.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md identifies the exact real point events are lost | Done — nowhere; file/memory always match; the real cause was a flag-usage inconsistency, not a pipeline gap |
| Real scope of impact determined | Done — zero real scope; the calibration tool's own JSONL pipeline is confirmed correct for all push-shaper event types |
| Concrete recommendation produced | Done — correct the sibling ticket's own record; file a new, separate follow-up for the real ENABLE_COMBAT_ENGAGEMENT suppression finding |
| If a fix lands: real corpus re-verification | N/A — no fix landed |
