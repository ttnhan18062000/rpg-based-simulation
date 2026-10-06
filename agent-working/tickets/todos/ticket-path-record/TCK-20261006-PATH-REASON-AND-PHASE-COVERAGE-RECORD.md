---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD
phase: open
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD

## Title
A run records why it took its path and which planned phases it left out; a skipped phase says why

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 1 of `TCK-20261006-EPIC-TICKET-PATH-RECORD`. Make three things explicit:
- why a ticket was closed by hand rather than by the pipeline;
- which phases its tier plans but its record does not contain;
- why a recorded phase was skipped.

Today a missing phase and a phase that never ran look the same. Of 222 W40–W41 standard closures, only 32 carry a
Plan event.

## Scope
- **The run's `path_reason`**, set through `record_hand_orchestrated_closure.py --path-reason <enum>
  [--path-note "..."]` and through the pipeline's own run write. Values, defined in `vocabulary.py`:
  - `pipeline_default`: the formal pipeline ran. The pipeline sets this itself.
  - `pipeline_unavailable`: no repo-root session, or agent types not loaded.
  - `native_port_blocked`
  - `small_change`
  - `owner_directed`
  - `batch_hand_close`
  - `investigation_only`
  - `other`: `--path-note` required.
  - `unstated`: the default when the flag is missing; the CLI prints one stderr hint.
- **The run's `phases_omitted`**: phases that the tier marks `full` in
  `agent-working/agent-orchestration/workflows/implement-ticket.yaml` but that have no event. The closure tool and
  the pipeline compute it at write time from that file, not from a hard-coded copy.
  - `conditional` phases are never counted as omitted.
  - Epic and `n/a` tiers record `[]`.
- **The event's `skip_reason`** on `status: skipped`. Values:
  - `tier_plan`: the tier marks it `skipped_event`.
  - `condition_false`: e.g. Parity's `src_change_and_behavior_changed`.
  - `not_applicable`
  - `no_hand_tool`
  - `deferred`
  - `other`
  - `unstated`: the default.

  The pipeline sets `tier_plan` and `condition_false` itself at its existing skip sites. A hand closure passes it
  per event inside `--events`.
- **Docs and validation.**
  - `schema.md` and `monitoring-schema.yaml` gain the three fields.
  - `validate.py` accepts them and rejects unknown enum values.
  - The CLAUDE.md "After Work" closure command example gains `--path-reason`, and a `skip_reason` on its Parity
    event.

## Out of Scope
- The reading and the retro section (child 2).
- Making either reason required.

## Acceptance Criteria
1. A hand closure of a standard ticket whose events are Scope, Implement, Test, Parity (skipped,
   `skip_reason: condition_false`), Verify and Finalize writes a run with:
   - `phases_omitted == [Investigate, Plan, Review, Document-Update, Architecture-Verify]`;
   - the given `path_reason`;
   - the Parity event's `skip_reason`.
2. The same closure for a hotfix ticket gives `phases_omitted == []`.
3. With no `--path-reason`, the run has `path_reason: unstated` and the CLI prints one stderr hint. The exit code
   is unchanged. An unknown value exits non-zero and writes nothing.
4. Editing `implement-ticket.yaml` to mark a phase `skipped_event` for standard changes `phases_omitted` with no
   code change. A test pins this.
5. A pipeline fixture run records `path_reason: pipeline_default` and `skip_reason: tier_plan` on its hotfix
   skipped events.
6. `validate.py` and the schema docs are updated. CLAUDE.md example updated. The scoped monitoring tests are green.

## Related Tickets
- `TCK-20261006-EPIC-TICKET-PATH-RECORD` (parent)

## Related Docs
- `docs/agent-monitoring/schema.md`
- `agent-working/agent-orchestration/monitoring-schema.yaml`
- `agent-working/agent-orchestration/workflows/implement-ticket.yaml`

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`, `record_run.py`, `record_events.py`,
  `vocabulary.py`, `validate.py`
- `.claude/workflows/implement-ticket.js` (its run write and skip sites)

## Assumptions / Open Questions
- Document-Update is `full` for hotfix too. If hand hotfix closures rarely log it, the reading will show that.
  That is a finding for child 2, not a reason to special-case it here.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06.

## Test Summary

## Files Changed

## Completion Summary
