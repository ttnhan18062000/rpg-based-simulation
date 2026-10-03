---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME
artifact_type: plan
tags: [ai, agent-monitoring, determinism]
---

# Implementation Plan — TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME

## Summary

This ticket's own Request Summary states it is explicitly NOT actionable until its blocking
condition — a real `Workflow`/`tool_runner` execution surface in this harness — is confirmed
available, and that this confirmation must be re-checked at the start of any future Investigate
phase rather than assumed from the ticket's prior text. The Investigate phase that precedes this
Plan phase (see `investigation.md`, this same directory) re-ran that confirmation on 2026-07-11 and
found the blocking condition **still true**: every workflow-backed `SKILL.md` (`implement-ticket`,
`implement-epic`, `create-tickets`, `simq-audit` — 5 references across 4 files) still states "the
Workflow tool is not available," and this exact investigation session empirically probed its own
tool surface (via `ToolSearch`, which searches the full deferred-tool catalog, not just what's
listed at conversation start) and found no `Workflow` tool and no Agent-SDK `tool_runner`-style
construct anywhere in this harness.

Because the prerequisite platform capability this ticket depends on does not exist, **this plan
contains no ordered implementation steps, no files-to-change list, and no dependency map.** Writing
any of those against a confirmed-absent capability would be exactly the "speculative
implementation against a hypothetical execution surface before one is confirmed to exist" that the
ticket's own Out of Scope section forbids, and would fabricate content this planner has no basis
for. The correct output of this Plan phase is a documented non-plan: the blocking condition,
re-verified as still true, is raised as an unresolved question that the ticket's own workflow-level
Assumptions/Open Questions section already designates as the pause-for-human-review mechanism.

## Steps

None. There is nothing to plan against. No code, test, or documentation change is proposed by this
plan. Do not infer an implicit step list from the ticket's Scope section ("port
`.claude/workflows/*.js`...") — that section describes what *would* be done *if* the blocking
condition ever flips true; it is not a work order for this cycle.

## Scope Guards

Carried forward from the ticket's Out of Scope section and the investigation's Anti-Drift Hazards,
restated here so the implementer (if this file is ever read by one in error) does not proceed:

- Do not touch `.claude/workflows/*.js` (any of the 11 files, including the 7 with no matching
  `SKILL.md`: `compact-simulation-result.js`, `generate-simulation-setup.js`,
  `investigate-simulation-result.js`, `prepare-simulation-execution.js`,
  `propose-simulation-enhancements.js`, `register-simulation-result.js`,
  `update-knowledge-store.js`).
- Do not touch any `.claude/skills/*/SKILL.md` file's "Do not call the Workflow tool" wording —
  that wording is factually correct and must remain until the blocking condition changes.
- Do not modify `tools/gate_checks/workflow_meta_conformance.py` — that is
  `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK`'s shipped, DONE deliverable, explicitly Out of
  Scope here.
- Do not modify anything under the sub-agent bookkeeping-determinism epic's territory
  (`TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC` and its now-DONE children) — that is a
  different architectural layer (sub-agent mechanical-step reliability, not
  orchestrator-as-narrator).
- Do not write speculative tests against a hypothetical `Workflow`/`tool_runner` API shape. The
  test_plan.md for this cycle correctly produced none, for the same reason.
- Do not change this ticket's Status from BLOCKED, and do not move it to `tickets/done/` — AC1 is
  not satisfied (the surface has not become available; it was only re-confirmed absent), and AC2 is
  not actionable.

## Dependency Map

Not applicable — there are no steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: Confirm whether a real Workflow-tool/tool_runner execution surface has become available | Satisfied by the Investigate phase's re-verification (see `investigation.md`), not by any step in this plan — AC1 is a confirmation check, not a code change | No test; confirmation evidence is the two-pronged check documented in `investigation.md` (textual + empirical) |
| AC2: `.claude/workflows/implement-ticket.js` ported to real executable code | Not actionable — provisional and contingent on AC1 flipping true, which it has not | None — no test_plan entry exists for this AC this cycle, correctly |

## Anti-Drift Notes

- **Do not treat this Plan phase's existence as license to proceed to Implement.** A `plan.md` file
  existing in this directory is a workflow-tier artifact-completeness formality for a BLOCKED
  ticket, not evidence that implementation work should follow. The main session must not advance
  this ticket past Plan.
- **Re-verification, not re-assumption, is required every cycle.** Per the ticket's own Request
  Summary and the investigation's Anti-Drift Hazards, any future session must re-run the same
  two-pronged check (grep current `SKILL.md` wording + empirically probe that session's own tool
  surface via `ToolSearch`) rather than trusting this plan's or the investigation's 2026-07-11
  finding as still current. A stale doc claiming a surface exists, or a tool that exists but isn't
  wired to this harness's skill-invocation path, would both be false positives.
- **Scope ambiguity flagged by Investigate, not resolved here**: if the blocking condition ever
  flips true, a future Plan phase will need to explicitly decide whether porting scope is "all 11
  `.claude/workflows/*.js` files" or "only the 4 skill-backed ones" (`implement-ticket`,
  `implement-epic`, `create-tickets`, `simq-audit`) — the ticket's Scope section only names
  `implement-ticket.js` as an example. This planner does not decide that now; it is listed under
  Unresolved Questions below for the same reason.

## Unresolved Questions

- **Blocking condition (real Workflow-tool/tool_runner execution surface) confirmed absent as of
  2026-07-11.** This ticket cannot be planned or implemented until platform capability changes.
  Recommend: leave the ticket BLOCKED in `tickets/todos/` (or wherever the main session's routing
  keeps blocked-tier tickets), and re-run Investigate again only after a genuine capability change
  is confirmed — not on a fixed schedule.
- Carried forward from the ticket and investigation, still unresolved and not decided by this
  planner:
  - Whether a real `Workflow`/`tool_runner` execution surface is on any roadmap for this harness at
    all, or whether narration is the permanent shape of the system.
  - Whether, if/when unblocked, this work should be split into its own epic (the parent
    `TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC` already tracks it as an open child).
  - Whether porting scope (if ever unblocked) is "all `.claude/workflows/*.js`" or "the
    skill-backed subset" — newly surfaced by this Investigate pass, not previously flagged.

These require a human/main-session decision (or a genuine platform change) before any Plan or
Implement work can meaningfully proceed. No step in this document should be executed by an
implementer.
