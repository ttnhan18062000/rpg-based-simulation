---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE
phase: done
date: 2026-10-23
tags: []
---

# TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE

## Title
Regenerate the calibration on v1 (`make evaluate-full` plus its run_determinism sidecar) for testing's SimQ re-anchor, and point the D76 cumulative table at the v1 base

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
TCK-20261019-RECORD-BASELINE-V1 closed without its scope item 4. That item regenerates the calibration with `make evaluate-full` and its run_determinism sidecar on v1 (e8df8b96d) so testing can re-anchor SimQ. The record also left the D76 cumulative table pointing at the old base. The record PR says both are "not in this PR". This ticket carries them.

## Scope
1. `make evaluate-full` on v1 (e8df8b96d), with the run_determinism sidecar, on a quiet host (one heavy process).
2. Hand the calibration to testing-planner for the SimQ re-anchor (testing owns the anchors).
3. Re-point the D76 cumulative table at the v1 base (e8df8b96d). Later steps measure against v1.

## Out of Scope
SimQ anchor values (testing). Any simulation change.

## Acceptance Criteria
- Calibration regenerated on 341f700d0 (src = e8df8b96d) with a run_determinism sidecar in all 63 dirs (paths handed to testing-planner). `data/calibration/` is gitignored (.gitignore:251), so the dirs cannot be committed; the paths are handed over instead.
- The D76 table names v1 as its base: docs/plans/systemic_world/roadmap.md 12.3 now names the v1 record 341f700d0 (simulation e8df8b96d) with 903239fbe kept as history, consistent with 12.5's Base (memo row 89). rpg-planner updates its own draft table.

## Related Tickets
TCK-20261019-RECORD-BASELINE-V1.

## Related Docs
docs/plans/systemic_world/v1_disclosure.md; docs/plans/rpg_design_roadmap/ (12.3).

## Related Stored Artifacts

## Related Code Areas
Makefile (evaluate-full); src/observability/reporting/run_determinism.py.

## Assumptions / Open Questions
- The location of the D76 table is to be confirmed (owner memo D76 row / roadmap).
- DUE 2026-10-30 (lead, #725 review): testing's SimQ re-anchor on the v1 sha needs this calibration before 2026-10-31.

## Implementation Notes
`make evaluate-full` is tools/evaluate_simq.py; in live mode it imports tools.calibrate_simq, which writes the run_determinism sidecar (write_sidecar, calibrate_simq.py:605). Run from the v1rec worktree on rpg-v1-calibration-d76 (git diff 341f700d0 HEAD -- src content config tools was empty, so no detached pin was needed). PYTHONPATH=. gate venv, one heavy process, host free per rpg-planner.

## Test Summary
tools/evaluate_simq.py, 2026-10-24 01:03:39 -> 01:15:17 +07:00, PID 2021153: 63 scenarios regenerated; all 63 quality_report.run_determinism.json carry run_id (each containing PID 2021153, so none stale), audit_mode true, signals_zeroed true. Verdict against the old anchors: 630 pillars checked, 285 REGRESS, 0 missing; 272 of the REGRESS rows read no-data (FACTION 59, COGNITION 46, AGENCY 38, COMBAT 34, ...), 25 runs too_few_pillars_scored (keys in /mnt/data/scratch-rpg-implementer-2/too_few_pillars_keys.txt, sent to testing-planner). Expected before the re-anchor (min-events rule plus the v1 world), per rpg-planner and testing-planner; not diagnosed here. Log: /mnt/data/scratch-rpg-implementer-2/evaluate_full.log.

## Files Changed
docs/plans/systemic_world/roadmap.md (12.3 base line), this ticket, docs/REGISTRY.yaml, monitoring shards. No code or data change.

## Completion Summary
The calibration is regenerated on v1 with the sidecar in all 63 dirs and handed to testing-planner for the SimQ re-anchor (anchors are testing's). The D76 base in roadmap 12.3 now points at the v1 record. testing-planner asked that data/calibration/ under the v1rec worktree stay in place until testing-implementer's cross-check (evaluate_simq on the 63 dirs against the new anchors) is done.
