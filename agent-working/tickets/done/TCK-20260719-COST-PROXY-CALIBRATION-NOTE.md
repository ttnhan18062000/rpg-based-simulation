---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-COST-PROXY-CALIBRATION-NOTE
phase: done
date: 2026-07-19
tags: []
---

# TCK-20260719-COST-PROXY-CALIBRATION-NOTE

## Title
Record cost_proxy calibration finding as a dated provenance note

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
The author wants the experiment's finding written down permanently — extending tools/agent-monitoring/cost_proxy.py's module docstring and/or docs/agent-monitoring/README.md's "What It Does NOT Capture" section with a short, dated note: the platform-blocked telemetry gap was reconfirmed 2026-07-19 against real local transcripts, edit_count is a weak/unconfirmed prior for being under-weighted, and recalibration remains blocked on better ground-truth data rather than missing investigation. experiments/cost_proxy_calibration/RESULTS.md should be linked as the evidence trail.

## Scope
- Add a dated (2026-07-19) note to tools/agent-monitoring/cost_proxy.py's module docstring (lines 1-16) and/or docs/agent-monitoring/README.md's "What It Does NOT Capture" section (lines 24-29)
- Note states the platform-blocked telemetry gap was reconfirmed against real local transcripts (33 files, 26,911 turns, isSidechain=false on all sidechain-flagged records)
- Note states edit_count is a weak, unconfirmed prior for W_EDIT under-weighting (Fit C r=0.91), explicitly not adopted as a shipped weight change
- Note states recalibration remains blocked on better ground-truth data, not missing investigation
- Note links experiments/cost_proxy_calibration/RESULTS.md by path

## Out of Scope
- Any change to W_BASH/W_AGENT/W_EDIT constants or compute_cost_proxy_score's logic
- Parity ledger entry — pure observability tooling doc change, not a Mechanics Bible/Engine Contract change
- C4's tool-promotion work — separate concern; coordinate sequencing with C4 if both land close together to avoid conflicting README edits

## Acceptance Criteria
- [ ] Dated 2026-07-19 note added stating the platform-blocked gap was reconfirmed against real local transcripts (33 files, 26,911 turns, isSidechain=false on all sidechain-flagged records)
- [ ] Same note states edit_count is a weak, unconfirmed prior for W_EDIT under-weighting (Fit C r=0.91), explicitly not adopted as a shipped weight change
- [ ] Note states recalibration is blocked on better ground-truth data, not missing investigation
- [ ] Note links experiments/cost_proxy_calibration/RESULTS.md by path
- [ ] No change to W_BASH/W_AGENT/W_EDIT constants or compute_cost_proxy_score's logic; all 3 existing tests in tests/tools/test_cost_proxy.py pass unmodified

## Related Tickets
- TCK-20260708-AGENT-COST-OBSERVABILITY

## Related Docs
- docs/agent-monitoring/README.md
- experiments/cost_proxy_calibration/RESULTS.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/cost_proxy.py
- docs/agent-monitoring/README.md
- experiments/cost_proxy_calibration/RESULTS.md
- experiments/cost_proxy_calibration/PROPOSAL.md

## Assumptions / Open Questions
- Placement decision needed: docstring vs README vs both — single-location placement with a cross-reference from the other is recommended to avoid disconnected duplicate records; Plan-phase decision
- C4 also touches README.md's same area — check C4's ticket status before implementing C5 if both are in flight, to avoid conflicting near-simultaneous edits

## Implementation Notes
Placement decision (per the ticket's own Assumptions section): single-location placement in
`docs/agent-monitoring/README.md`'s existing "What It Does NOT Capture" section (the most natural
home — that section already covers the platform-blocked token gap this note reconfirms), with a
one-paragraph cross-reference added to `tools/agent-monitoring/cost_proxy.py`'s module docstring
pointing back to it, rather than two disconnected duplicate records. No change to `W_BASH`/
`W_AGENT`/`W_EDIT` or `compute_cost_proxy_score()`'s logic. C4 (`TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE`)
was checked before this edit — still in `tickets/todos/`, not yet started, so no in-flight
conflict on README.md's same area.

## Test Summary
`python3 -m pytest tests/tools/test_cost_proxy.py -q` — 3/3 passing, unmodified.

## Files Changed
- docs/agent-monitoring/README.md (new dated note in "What It Does NOT Capture")
- tools/agent-monitoring/cost_proxy.py (docstring cross-reference to the note)

## Completion Summary
Added a dated (2026-07-19) provenance note to `docs/agent-monitoring/README.md`'s "What It Does
NOT Capture" section recording the cost_proxy_score calibration experiment's finding: the
platform-blocked telemetry gap was reconfirmed against 33 real local session transcripts (26,911
turns, zero subagent-turn transcripts found); `edit_count` is a weak, unconfirmed prior for
`W_EDIT` under-weighting (Fit C r=0.91), not adopted; recalibration remains blocked on
better-grained ground-truth data, not missing investigation. Linked
`experiments/cost_proxy_calibration/RESULTS.md` as the evidence trail. Cross-referenced from
`cost_proxy.py`'s own module docstring. No weight/logic change; all 3 existing tests pass
unmodified.
