---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING
phase: open
date: 2026-09-29
tags: [testing]
---

# TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING

## Title
Epic C — Test workflow and failure handling: test-plan fields, an advisory test-quality checklist, and one failure-triage procedure

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary

In `implement-ticket`:
- only the test *level* is decided in `test_plan.md`;
- the implementer writes both code and tests;
- no phase reviews test quality;
- the installed test skills are never invoked.

Failure handling is also split across three sources:
- `docs/testing/regression_policy.md` §4–7;
- the CI Failure Triage section of `docs/guides/delivery_process.md`;
- CLAUDE.md's gate-integrity rule.

`regression_policy.md` §6 allows unbounded `xfail(strict=False)` for flaky tests.

Roadmap: `docs/plans/test_architecture/roadmap.md` §2–3.

## Scope

1. **Test-plan fields** (existing `investigator`):
   - mandatory: proof kind, oracle source (Bible/contract section + parity-ledger id), expected
     effect, selected commands;
   - optional: negative cases, fixtures, non-functional risk.
2. **Advisory test-quality checklist** in the existing `architecture-reviewer` at
   Architecture-Verify, diff-scoped. A clean review is a valid outcome.
3. **Epic coordination note** for `implement-epic` children: shared fixtures and patterns recorded
   at the epic level.
4. **Unified failure-triage procedure** in `docs/testing/regression_policy.md`, with the other
   sources linking to it:
   - an evidence record (reproduction command, seed/world/config, SHA, run ids, expected vs
     observed, rerun result);
   - failure classes, each with a role, an immediate action and a closure condition;
   - the prohibitions of roadmap §2.5;
   - defects found by tests handed to the feature team.
5. **Oracle-review step — gated by D-M2 (only this part):** when an acceptance criterion adds or
   changes an expectation, the Bible/contract and parity ledger change first. Silence, missing
   ownership, disputes and intra-Bible conflicts escalate to the user. Advisory during the pilot.
6. **Bounded-quarantine policy text — gated by D-MF (only this part):** replaces §6's unbounded rule.
   **Enforcement tooling is deferred until a real case needs quarantine.** Existing failures stay
   visible.

## Out of Scope

- A new workflow phase or a dedicated test-writing agent. That is a later option, triggered only by
  shortcomings the pilot observes.
- Review-record storage or validator (deferred to its trigger); no new proof-status record.
- Quarantine tooling (deferred).
- Changing Bible/contract content (feature teams and the user).

## Acceptance Criteria

1. On at least 2 tickets (real, or clearly labelled synthetic), the mandatory `test_plan.md` fields
   are present and `done-checker` checks their presence.
2. The checklist runs on changed tests. Each substantive finding is acted on, or declined with a
   reason.
3. The triage procedure is one document, and the other sources link to it. A drill classifies at
   least one real case (the Epic A leak) and one synthetic case, and routes each to the right role.
4. **(After D-M2)** A ticket that changes an expectation shows the document and ledger change before
   the test change, or an escalation record.
5. **(After D-MF)** §6 states the bounded policy. No existing failure is quarantined.

## Related Tickets
- Depends on Epic B (taxonomy doc) for the field vocabulary.
- Feeds Epic D.

## Related Docs
- `docs/plans/test_architecture/roadmap.md`
- `docs/plans/test_architecture/reference/architecture_design_notes.md` §5, §6.3, §7 (non-binding;
  includes the observed pytest 9.0.2 xfail semantics)
- `docs/testing/regression_policy.md`, `docs/guides/delivery_process.md`

## Related Stored Artifacts
None.

## Related Code Areas
`.claude/agents/investigator.md`, `.claude/agents/architecture-reviewer.md`,
`.claude/agents/done-checker.md`, `.claude/workflows/implement-epic.js` (notes only),
`docs/testing/regression_policy.md`.

## Assumptions / Open Questions
- **D-M2, D-MF pending:** parts 1–4 proceed without them.
- The installed `obra/superpowers` `testing-anti-patterns.md` is the checklist basis.

## Implementation Notes
- The cost of the added fields is observed via `tool_call_count` per phase: a coarse proxy, not time
  or tokens.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
(Open.)
