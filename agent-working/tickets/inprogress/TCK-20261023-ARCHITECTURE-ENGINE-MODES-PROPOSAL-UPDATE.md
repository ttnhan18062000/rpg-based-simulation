---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261023-ARCHITECTURE-ENGINE-MODES-PROPOSAL-UPDATE
phase: open
date: 2026-10-23
tags: [architecture, determinism]
---

# TCK-20261023-ARCHITECTURE-ENGINE-MODES-PROPOSAL-UPDATE

## Title
Update the engine execution modes proposal with the 2026-10-22 rulings and measurements, and make it agree with the port-leak audit and the conformance-suite design

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`docs/plans/architecture/engine_execution_modes_proposal.md` (#719) predates four facts from 2026-10-22, and in a few
places it now contradicts `port_leak_audit.md` and `conformance_suite_design.md` (TCK-20261022-ARCHITECTURE-PORT-LEAK-AUDIT
and TCK-20261022-ARCHITECTURE-CONFORMANCE-SUITE-DESIGN). The user approved this update and its scope on 2026-10-23 (#715
issuecomment-6347241081). Ownership is architecture-planner's: architecture-planner-u24 confirmed it is not in flight there
(#715 6346668935 and 6347176111).

## Scope
Edit `engine_execution_modes_proposal.md` only, plus the README Contents row if its one-line description changes. Each change
cites its source. Define each fact once: where the audit or the design already holds the detail, link to it instead of
restating it.

1. **Mode 2 (§4) and §8 Q2: perf ruled YES** on T3 / Mode 2 (#593 issuecomment-6343379030), under five conditions. Replace
   "Three facts to verify first (draft T3)" with the ruling and its conditions:
   - `arm_child` and the gate share `rpg_gate_run.build_kernel`, so `no_replay` is passed from the arm path only, or it
     silently changes the gate;
   - the flag is recorded, and mixed arms are refused;
   - the saving is a PROVISIONAL tooling number, not a perf claim;
   - replay stays on wherever a per-tick digest trail is needed;
   - the fifth condition, as stated in the ruling. Read #593 issuecomment-6343379030 and quote all five accurately.
   Mark §8 Q2 as answered by perf's ruling, and keep any adoption decision that is still the owner's as an owner question.
2. **§2 and §8 Q3: H3 and H4 re-measured, both CLOSE** (#593 issuecomment-6343696936, PR #723):
   - H3: `EventRecorder.record` is 0.69 % (was 42.5 %);
   - H4: the shapers are 1.18 %, and event-path pydantic is 0.65 %;
   - the 7.15 % total pydantic share belongs to the H1/H2 callers;
   - the `frontier_extended` shapers at 3.74 % are rpg's call.
   Mark §8 Q3 as answered. H2 still gets a ticket after v1. Update §3 and §6 wherever they list H3 and H4 as pending.
3. **T2 runner facts (§6, or wherever T2 is):**
   - there is no self-hosted runner, and the repo is public, so adding one means hardware, hardening and an owner decision;
   - GitHub-hosted runners have 4 vCPU and 16 GB, a 6 h job limit and free minutes;
   - runner identity is a description, not a fixed machine: fine for byte-identity checks, unfit for timing comparisons;
   - platform recommends running both arms of a pair in the same job, on one VM.
   Source: platform-planner, relayed by lead-planner on 2026-10-22.
4. **PERF-M6-T05:** note that it has no ticket. It is a line in `docs/plans/design_enhancement/performance_milestones_epic.md`
   (M6).
5. **Agreement with the audit (§5):**
   - Replace the "known leak" column with the audited verdicts, one short phrase per port, linking to `port_leak_audit.md`.
     The clock leak is the default `LIVE` contract, not the pacing. The hash omits six fields, including
     `information_providers`; terrain is not a gap.
   - Fix the event-sink row: "ordering feeds the digest" is unconfirmed, because no event digest exists and the final hash is
     state-only.
   - Under Mode 1 or §5, state that Mode 1 runs on fixed budgets (`audit_mode`, or pinned NORMAL) per PERF-D1 A2. Canonical is
     only for cost or governance runs. Runs are never compared across contracts.
   - Note that the v1 baseline cannot vouch for the six fields. The fix is perf's PERF-D5 scheme bump, after v1. rpg answered
     that `recent_world_events` is state (#593), so all six fields go in: cite rpg's #593 comment if it is posted by then;
     otherwise say "rpg-planner, relayed by lead-planner-u24".
6. **Agreement with the design (§5 "Conformance suite"):** keep the three summary bullets, and point to
   `conformance_suite_design.md` for the worlds, seeds, cases, blind-to lists, side digest, Mode 3 matrix and lanes. Lanes
   stay pending testing-planner.
7. **§6 ownership and step table:** mark the audit and the design as done, with their doc links, and leave the rest unchanged.
8. Add a dated "Revised 2026-10-23" line near the top, listing what changed and why.

## Out of Scope
- Any new proposal content beyond the items above. No new modes, no change to recommendations other than those the rulings force.
- `port_leak_audit.md` and `conformance_suite_design.md`, except for a broken cross-link, if any.
- Anything outside `docs/plans/architecture/**`. ADR text goes to lead-planner.

## Acceptance Criteria
- AC1: scope items 1 to 8 are each done, with a citation (issue comment, PR or doc path).
- AC2: no statement in the proposal contradicts `port_leak_audit.md` or `conformance_suite_design.md`. Grep both for each
  §5 port and check.
- AC3: no fact is restated in full where a link suffices.
- AC4: frontmatter validates, `docs/REGISTRY.yaml` is regenerated, and the README row is updated if needed.
- AC5: no file outside `docs/plans/architecture/**`, `docs/REGISTRY.yaml`, this ticket and `agent-working/agent-monitoring/`
  changes.

## Related Tickets
- TCK-20261022-ARCHITECTURE-PORT-LEAK-AUDIT, TCK-20261022-ARCHITECTURE-CONFORMANCE-SUITE-DESIGN

## Related Docs
- docs/plans/architecture/engine_execution_modes_proposal.md, port_leak_audit.md, conformance_suite_design.md,
  faster_feature_testing_draft_tickets.md
- docs/architecture/performance_optimization_decisions.md (PERF-D1 A2, PERF-D5)
- docs/plans/design_enhancement/performance_milestones_epic.md (M6)

## Related Stored Artifacts
- none

## Related Code Areas
- none (docs only)

## Assumptions / Open Questions
- If #593 issuecomment-6343379030 states the five conditions differently from this ticket, the comment wins.

## Implementation Notes
Branch: architecture-implementer-engine-modes, on top of e43247bcc. This folds into the open A+C PR: re-render the PR
title and body afterwards to cover three tickets. Close by hand with `--path-reason investigation_only`. Send the SHA to
architecture-planner before any push.

## Test Summary
## Files Changed
## Completion Summary
