---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261019-RECORD-BASELINE-V1
phase: open
date: 2026-10-19
tags: []
---

# TCK-20261019-RECORD-BASELINE-V1

## Title
Record baseline v1: paired fingerprints, gate V1-V8 rows and the behavioral_5k rebaseline, all on one commit, with v1_disclosure.md as what v1 does not claim

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Milestone 0 ends with the baseline v1 record, and milestone 1 measures against it. The recipe below is the designer's (rpg-designer, 2026-10-19). The user's merge of the v1 PR is the owner's sign-off.

## Scope
0. Precondition checklist (it goes in the v1 PR body). Every "before v1" ruling must be folded on the v1 commit:
   - D70 camp spawns;
   - D71 stronghold;
   - D72 terrain cost;
   - D74 species;
   - D75 route;
   - the D78 gate path: earning, eating, cover, high ground, chokepoints;
   - the grief fix (TCK-20261016-GRIEF-AS-STATE-…);
   - the event-drop fix (TCK-20261016-EVENT-FILE-KEEPS-EVERY-EVENT-THAT-PASSED-THE-MODE-FILTER, to confirm) and its tests;
   - V8.
   Each one cites a fold sha and a test path. Anything not folded is either listed in v1_disclosure.md or blocks v1.
1. The commit is main after #654 (R2) and the designer's docs batch (v1_disclosure.md must be on main).
2. Paired fingerprints become the new D76 cumulative base, replacing 903239fbe:
   - 3 gate worlds × seeds 42-51 (10) × 5000t;
   - audit_mode, signals zeroed, full self-check.
   Behaviour steps after v1 are still measured on seeds 42-46.
3. Gate V1-V8 rows, recorded as rpg_gate_baseline_format.md "Recording v1" specifies:
   - the candidate comes from a scheduled or dispatched MAIN run, never --evidence-only, on the config's 5 seeds (42-46, D54), governor-pinned NORMAL;
   - then `rebaseline --milestone M0 --cite TCK-20261019-RECORD-BASELINE-V1`, with the JSON in the v1 PR;
   - if any kind group crosses R2 (O2.seeds_with_survivors min 1), the rebaseline needs `--owner-ruling-ref/date` from the OWNER;
   - R1 is not in v1 by construction, because it needs the two-arm free-meal run.
4. Calibration regenerated with make evaluate-full (host-independent sidecar), so testing can re-anchor SimQ (TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1). That is data for the after-v1 rebuild, never called a grade.
5. behavioral_5k is rebaselined on the same commit (T2, TCK-20261007-BEHAVIORAL-5K-REBASELINE-…).
6. The PR body has one line asking the owner to accept v1 with v1_disclosure.md, and names the two edge items:
   - crowded_frontier at the D76 stop edge;
   - the frontier M2 report-only reading, which would have stopped had it been live.

## Out of Scope
- D73 free-meal removal: it comes after v1 and is measured against it, followed by the gate.
- The roadmap §12.3 v1 sha line and the disclosure header (the designer adds them in the next batch).
- Never compare across the gate record (governor-pinned NORMAL) and the paired record (audit_mode).

## Acceptance Criteria
- Every precondition row has a sha and test path, or is named in v1_disclosure.md.
- The paired base is recorded on the v1 commit (10 seeds, self-check spread 0) and the D76 table points at it.
- The gate baseline JSON comes from a main run, is committed in the v1 PR, and is cited to this ticket.
- behavioral_5k is green on the v1 commit after the rebaseline.
- The calibration dirs carry the run_determinism sidecar. Testing-planner is told the v1 sha.

## Related Tickets
- TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 (testing; check date 10-31)
- TCK-20261007-BEHAVIORAL-5K-REBASELINE-… (expires 11-15)
- TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK

## Related Docs
- docs/plans/systemic_world/v1_disclosure.md
- docs/plans/systemic_world/roadmap.md §12.3
- docs/plans/systemic_world/owner_decision_memo.md (D44, D54, D70-D78)
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md ("Recording v1")

## Related Stored Artifacts
- .claude/handover/drafts/M0-CUMULATIVE-WATCH-TABLE.md

## Related Code Areas
- tools/rpg_measure/paired.py
- the rpg gate rebaseline tool
- tests/regression/test_behavioral_5k.py

## Assumptions / Open Questions
- Whether main after 6d7bd1509 (the #645 tip) has moved simulation behaviour (deps window, R1, R2, other domains). A hash-identity check answers this before the record.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
