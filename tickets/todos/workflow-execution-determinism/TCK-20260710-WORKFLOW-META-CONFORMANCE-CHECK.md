---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK
phase: open
date: 2026-07-10
tags: [ai, agent-monitoring, determinism]
---

# TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK

## Title
Workflow meta.phases conformance check — detect silently-skipped phases (DRAFT — needs investigation)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
**DRAFT — this ticket has only been lightly scoped directly from the idea doc. A full Investigate
phase (real file:line evidence, existing-test discovery, confirmed related-ticket check) has NOT
been run and MUST happen before Plan/Implement — do not skip straight to Plan from this ticket
as-is.**

Source idea doc: `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md`,
section "Near-horizon: a workflow-conformance self-check (actionable now)".

The idea: every `.claude/workflows/*.js` file exports a declarative `meta.phases` array (a list of
`{ title, detail }` pairs describing every phase the workflow is supposed to execute), and every
phase already pushes an event to `agent-monitoring/events.jsonl` with a `phase` field — but these
two things are never cross-checked against each other today. Add a static verifier,
`tools/gate_checks/workflow_meta_conformance.py`, that given a completed run's `run_id`, parses the
workflow's `meta.phases` list (small regex/AST-lite extraction from the `.js` source, not a full JS
parser) and cross-references it against that run's actual `events.jsonl` entries, flagging any
phase declared in `meta.phases` with zero matching events — a phase the narrating LLM silently
skipped entirely, not just under-instrumented. This mirrors the existing
`tools/gate_checks/parity_updater_static.py`'s `cross_reference_touched` pattern (which already
catches "a `src/` file mapped to a ledger subsystem had no corresponding ledger touch"), applied
one layer up: phases vs. events instead of files vs. ledger entries.

This does not make the orchestrator deterministic — it makes a specific, cheap, high-value class
of failure (an entire phase silently vanishing from a run) detectable after the fact, the same way
`done_checker_static.py`'s `run_finalize_selfcheck` already makes "did Finalize actually move the
ticket" detectable rather than trusted.

## Scope
- Add `tools/gate_checks/workflow_meta_conformance.py`, a static verifier that:
  - Given a `run_id`, locates the corresponding workflow source file under `.claude/workflows/`.
  - Extracts the `meta.phases` array via lightweight regex/AST-lite parsing (NOT a full JS parser —
    the idea doc is explicit about this constraint).
  - Reads `agent-monitoring/events.jsonl`, filters to entries with that `run_id`, and collects the
    set of `phase` values present.
  - Flags any phase name present in `meta.phases` with zero matching events for that run.
- Mirror the shape/precedent of `tools/gate_checks/parity_updater_static.py`'s
  `cross_reference_touched` function as closely as reasonable.
- Mechanism for surfacing findings (advisory nudge vs. hard gate/block) is explicitly TBD — an open
  question carried from the idea doc, not decided in this ticket.

## Out of Scope
- The long-horizon "execute, don't narrate" idea from the same source doc (porting
  `.claude/workflows/*.js` to run as real code under a genuine workflow-execution surface) — that is
  explicitly flagged in the idea doc as not actionable today and is tracked separately as
  TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME (sibling draft, being created in parallel).
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC's scope (sub-agent-layer mechanical-step
  reliability, e.g. Step 0b sidecar registration) — that is a different architectural layer
  (sub-agent-as-worker) per the idea doc's own framing, not this ticket's concern
  (orchestrator-as-narrator).
- Building a full JavaScript parser/AST toolchain — lightweight regex/AST-lite extraction only, per
  the idea doc's explicit constraint.
- Deciding advisory-vs-blocking severity for findings — flagged as an open question, to be resolved
  during Plan, not assumed here.

## Acceptance Criteria
- [ ] (provisional) `workflow_meta_conformance.py` correctly parses `meta.phases` from at least
      `implement-ticket.js`.
- [ ] (provisional) cross-reference correctly flags a synthetic run missing an event for a declared
      phase.
- [ ] (provisional) advisory-vs-blocking decision from the idea doc's Open Questions is resolved
      during Plan, not assumed here.

## Related Tickets
- TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC (parent — being created in parallel; exact ID
  may need reconciling once created)
- TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME (sibling draft, long-horizon "execute, don't narrate"
  idea, being created in parallel)
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC (related but distinct architectural layer, per
  idea doc framing — not a duplicate)

## Related Docs
- `docs/plans/agent_infrastructure/idea_workflow_execution_determinism.md` (primary source — see
  "Near-horizon: a workflow-conformance self-check (actionable now)" section)
- `docs/agent-monitoring/schema.md` (defines `events.jsonl` schema, including the `phase` field and
  the current `phase` value vocabulary for the implement-ticket workflow)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/gate_checks/` (new file location, expected: `tools/gate_checks/workflow_meta_conformance.py`)
- `.claude/workflows/*.js` (source of the `meta.phases` declarative array)
- `agent-monitoring/events.jsonl` (source of actual per-phase event records)
- `tools/gate_checks/parity_updater_static.py` (`cross_reference_touched` — direct structural
  precedent for this ticket's cross-reference logic)

## Assumptions / Open Questions
- Carried forward verbatim from the idea doc: should a missing-phase-event finding from the
  proposed conformance check be advisory (a nudge, like `retro_nudge_hook.py`) or a hard block at
  Finalize? CLAUDE.md's Hard Rule that "monitoring write failure must never fail the workflow"
  governs *monitoring writes*; a silently-skipped phase is arguably a workflow-integrity failure,
  not a monitoring-write failure — this distinction should be decided deliberately, not defaulted
  either way.
- Carried forward from the idea doc: is a real `Workflow`/tool-runner execution surface plausible on
  any roadmap for this harness, or is "an LLM narrates a `.js` spec into tool calls" the permanent
  shape of this system? Unknown from inside this repo; relevant context for how much investment this
  ticket's mitigation deserves relative to the long-horizon sibling idea.
- Carried forward from the idea doc: should this be scoped as its own epic when scheduled, or
  treated as a fourth child of `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`? This ticket
  currently assumes it is a child of the separate `TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC`
  per the idea doc's leaning — if that's wrong, Related Tickets above needs correcting.
- This ticket is a draft — its own Investigate phase must independently re-verify the `meta.phases`
  parsing approach, confirm no existing test/tool already does this, and resolve the
  advisory-vs-blocking question before Plan proceeds.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

