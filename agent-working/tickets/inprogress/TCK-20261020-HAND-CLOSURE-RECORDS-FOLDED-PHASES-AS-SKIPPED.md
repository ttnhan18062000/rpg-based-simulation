---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-HAND-CLOSURE-RECORDS-FOLDED-PHASES-AS-SKIPPED
phase: open
date: 2026-10-20
tags: [agent-monitoring, data-quality, workflows]
---

# TCK-20261020-HAND-CLOSURE-RECORDS-FOLDED-PHASES-AS-SKIPPED

## Title
Hand closures record Review, Document-Update and Architecture-Verify as skipped with a skip_reason instead of omitting them

## Status
OPEN

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
This comes from RETRO-2026-W42's final note (81 runs), "What to change?" item 3. The owner said yes on 2026-10-20, relayed by lead-planner.

On the hand path, closers give no event for three phases:
- standard tickets: Review, Document-Update and Architecture-Verify, in 54 of 54 runs;
- hotfixes: Document-Update, in 23 of 23 runs.

The phases are folded into Implement/Verify, or the hand path has no separate step for them. The path report shows them as `omitted`, the same as a real gap, so the retro cannot tell "folded" from "missing".

From now on, `record_hand_orchestrated_closure.py` records them, so `phases_omitted` names only real gaps.

## Scope
1. **`tools/agent-monitoring/record_hand_orchestrated_closure.py`.** After `evidence_phase_events`, add a step that fills in hand-path phases the closer gave no event for. The phases come from the tier plan: `full` phases for that tier in `path_report`/`path_record`, only Review, Document-Update and Architecture-Verify, and never a phase the closer narrated.
   - **Review and Architecture-Verify** (standard/epic): record an event with `status: skipped`, `skip_reason: no_hand_tool`, and a summary saying the recorder added it because the hand path has no separate review or architecture-verify step.
   - **Document-Update** (every tier whose plan lists it as `full`):
     - If the ticket's own changed files (`_ticket_changed_files`) include a file under `docs/`, record `status: ok`. Exclude `docs/REGISTRY.yaml` (regenerated on every close) and `docs/parity_ledger/**` (that's Parity's evidence). The summary is "derived by the recorder" and names up to 3 of those files.
     - Otherwise record `status: skipped`, `skip_reason: no_hand_tool`.
     - When the changed files can't be read (`None`), record skipped with `no_hand_tool`, and the summary says the docs check couldn't run.
   - **Ordering:** keep the canonical order of the tier plan when inserting. Use the same approach as the existing derived events, or sort by the plan's phase order. Print one `NOTE:` line naming the phases added.
   - **Agent:** the added events carry the run's default agent, like the derived events do.
   - **Phases not covered:** don't add events for any other phase (Investigate, Plan and Test stay as they are now). Don't add events for phases the tier marks `skipped_event` or `conditional`.
2. **Docs:**
   - `docs/agent-monitoring/README.md` ("Recording coverage for a hand-orchestrated closure"): one short paragraph on what the recorder adds and why.
   - `docs/agent-monitoring/schema.md`, the `skip_reason` row: say that `no_hand_tool` is what the hand-closure recorder sets for these phases.
3. **Tests** in `tests/tools/test_closure_recorder_phase_evidence.py`, or a new sibling file:
   - Standard closure with none of the three phases narrated: Review and Architecture-Verify are skipped with `no_hand_tool`, and `phases_omitted` no longer lists them.
   - Document-Update is `ok` when the changed files include `docs/guides/x.md`.
   - Document-Update is skipped with `no_hand_tool` when the only docs changes are `docs/REGISTRY.yaml` and `docs/parity_ledger/y.yaml`.
   - Document-Update is skipped with `no_hand_tool` when the changed files are `None`.
   - A closer-narrated event for any of the three phases is kept as given; nothing is added for it.
   - Hotfix: only Document-Update is added. No Review or Architecture-Verify events appear (they're `skipped_event` in the plan).
   - Every added event passes `record_events` validation: the skip_reason is in `SKIP_REASONS`, and the shared run_id/seq fields are present.

## Out of Scope
- Backfilling past runs.
- Changing `path_report`'s routing rule. Skipped phases still count toward a routing candidate, and the table's `skip_reason` column will now show `no_hand_tool`.
- The `implement-ticket.js` pipeline.
- CLAUDE.md's example `--events` list. Closers may still narrate these phases; the recorder only fills the gaps.

## Acceptance Criteria
- A hand closure of a standard ticket that narrates none of the three phases records all three, with `phases_omitted` free of them. The skip_reasons and statuses follow Scope §1.
- A narrated event always wins over an added one.
- The tests above pass, along with the existing `tests/tools/test_record_hand_orchestrated_closure.py` and `test_closure_recorder_phase_evidence.py`.
- The README and schema are updated, and REGISTRY is regenerated after the last docs edit.

## Related Tickets
- TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON (the derived-evidence pattern this extends)
- TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD (`skip_reason` and `phases_omitted`)
- TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE

## Related Docs
- agent-working/agent-monitoring/retro/RETRO-2026-W42.md (final note, item 3)
- docs/agent-monitoring/README.md, docs/agent-monitoring/schema.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON/

## Related Code Areas
- tools/agent-monitoring/record_hand_orchestrated_closure.py (`evidence_phase_events`, `_ticket_changed_files`, `main`)
- tools/agent-monitoring/path_record.py, path_report.py (tier phase plan), vocabulary.py (`SKIP_REASONS`)

## Assumptions / Open Questions
- **`no_hand_tool`** is the existing enum value that fits: "the hand path has no step for this phase". No new vocabulary is needed.
- **Document-Update evidence** is a docs change in the ticket's own diff, outside REGISTRY and the parity ledger. A doc change that doesn't describe a behaviour change still counts. That's accepted as evidence that the phase ran, the same way `plan.md` is evidence for Plan.

## Implementation Notes
- 2026-10-20 (agent-working-planner): owner yes (via lead-planner). Batch 6, dispatched to agent-working-implementer.

## Test Summary

## Files Changed

## Completion Summary
