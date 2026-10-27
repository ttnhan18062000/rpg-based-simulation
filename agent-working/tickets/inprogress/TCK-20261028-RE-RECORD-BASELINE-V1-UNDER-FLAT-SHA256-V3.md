---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261028-RE-RECORD-BASELINE-V1-UNDER-FLAT-SHA256-V3
phase: inprogress
date: 2026-10-28
tags: [benchmarking]
---

# TCK-20261028-RE-RECORD-BASELINE-V1-UNDER-FLAT-SHA256-V3

## Title
Re-record baseline v1 under the proof digest scheme `flat-sha256-v3` (after #758), with outcomes proven equal to v1

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
#758 (perf F1, TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS) merged as 957caf8f6
(#715 6449765506). It moves every proof digest from `flat-sha256-v2` to `flat-sha256-v3` (v2 plus seven
carried-state fields); outcomes do not move. Roadmap §12.5 "Hash scheme": the v1 base must be re-recorded under
the new scheme before any M1 paired or gate comparison. F1's AC: "The v1 base is re-recorded under v3 (rpg)
before any M1 paired or gate comparison, with outcomes equal to v1"; perf then checks that only digests moved.
rpg owns the record and its harness (TCK-20261019-RECORD-BASELINE-V1, #725).

## Scope
1. Record base = origin/main at or after 957caf8f6 whose diff from v1 (`e8df8b96d`) under the measured paths
   (src, content, config, data, registries, tools/rpg_measure, gate paths) is stated in full, with each change
   classed as digest-only (F1) or carried by its own already-measured step. If any non-digest behaviour change sits
   in that diff, STOP and report to rpg-planner before recording.
2. The three parts of v1, each re-done under v3:
   a. Gate baseline JSON (M0): from a gate run on main. Triggering the workflow (workflow_dispatch) is an external
      write: it needs the owner's go, asked in the implementer's own terminal.
   b. behavioral_5k rebaseline.
   c. 1b paired base arms: the cached base arms for the 3 gate worlds x s42-46 x 5000t under v3
      (`tools/rpg_measure/paired.py`, `--self-check full`), so later M1 paired runs compare v3 to v3.
3. Outcome equality against v1: per-entity fates, start, counters and adds identical to the v1 record for every
   world and seed; only `final_hash` / `start_hash` (and digest-bearing fields) differ. A table per world in the
   ticket. Any outcome difference = STOP.
4. Record the new base id and scheme where v1 is cited for M1 (roadmap §12.5 line and the known-entries file if it
   names the scheme), with rpg-planner's review.
5. Hand perf the comparison (fates/counters equal, digests moved) for its check.

## Out of Scope
- Any behaviour change; HUNGER step A and other M1 steps.
- Calibration and SimQ re-anchor (TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE), unless the digest move
  breaks them; then report.

## Acceptance Criteria
1. The diff from e8df8b96d to the record base is listed and classed; no unclassed behaviour change.
2. Gate baseline JSON, behavioral_5k and the 1b base arms exist under `flat-sha256-v3`.
3. **Amended 2026-10-28 by rpg-planner's ruling (Option A):** F1 moves only digests. P (v2, 04b85fb2e) and R (v3, 957caf8f6) are equal in every paired result field except start_hash and final_hash. Differences from v1 are attributed to measured steps. The original wording, "outcomes equal v1 on every world and seed", is superseded by finding 1: #753 step B (2.138) lies between v1 and R and moved fates.
4. Self-check (base repeat) spread 0 under v3.
5. perf's check requested; owner sign-off by merge of the record PR.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (#725, the v1 record)
- TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS (#758, F1)
- TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE

## Related Docs
- docs/plans/rpg_design_roadmap/ (§12.5 Hash scheme)
- docs/engine/deterministic_execution.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261019-RECORD-BASELINE-V1/
- agent-working/stored_artifacts/TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS/evidence.md

## Related Code Areas
- tools/rpg_measure/paired.py, src/engine/checkpoint.py (read only)

## Assumptions / Open Questions
- u24 heavy slot: this ticket holds it first; the U3 batch neutral proof follows.
- If F4 (#765) merges before the record, F4 is in the diff: it is hash-neutral on all gate worlds (probe A0,
  --neutral IDENTICAL), so it is classed as covered by its own measurement.

## Implementation Notes
Taken by rpg-implementer-2 on 2026-10-28. Branch rpg-v1-rerecord-v3, worktree .claude/worktrees/rerecord, off origin/main 957caf8f6.
**Findings sent with the plan, ruled by rpg-planner (Option A):**
- **Finding 1:** e8df8b96d..main holds #753 step B, a measured behaviour change (2.138). So "outcomes equal v1" cannot hold on main, and AC3 is amended (above).
- **Finding 2:** only the 1b paired results carry a proof digest. The gate JSON and behavioral_5k are NOT re-recorded. `rpg_gate_v1.json` holds only `harness_hash`, and none of its harness inputs changed since v1 (fresh until 2026-11-21). `baseline_5k.json` holds metrics only. Re-recording either on main would be a behaviour rebaseline that absorbs step B, which is a separate question and out of scope.

**Settings, fixed by the ruling:**
- R = 957caf8f6 exactly; P = 04b85fb2e (its parent). R does not move to a later main.
- 1b covers seeds 42-51, matching v1's 1b shape; --jobs 2.
- Diff classing is in `investigation.md`. #757 is dead-path deletions; #762 is a docstring plus an error path no completed run takes, with its own neutral; #760 is neutral. No STOP.

**1b base arms:** they are kept at `/mnt/data/scratch-rpg-implementer-2/v3/cache/results/957caf8f6cff-<child hash>-5000/` (30 files). A later M1 paired run reuses them by `--cache /mnt/data/scratch-rpg-implementer-2/v3/cache`, or after the compare they are copied into the shared paired cache under the same `results/<sha12>-<child>-5000/` name (rpg-planner's choice). Nothing moves while the run is live.

## Test Summary

## Files Changed

## Completion Summary
