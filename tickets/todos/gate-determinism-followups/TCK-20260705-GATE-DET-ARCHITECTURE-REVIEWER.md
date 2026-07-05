---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER
phase: open
date: 2026-07-05
tags: [ai, workflows, determinism]
---

# TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER

## Title
Add deterministic static scans backing architecture-reviewer's durable-state/API-boundary judgments

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Fourth and hardest of 4 gate-determinism tickets (see
`tickets/todos/gate-determinism-followups/SEQUENCE.md` for shared design decisions and full context;
deliberately sequenced last). Per `docs/plans/agent_infrastructure/idea_agent_gate_determinism.md`'s
table: "AST scan for direct durable-state mutation outside `src/engine/authoritative_pipeline*`;
grep-scoped check for raw domain objects returned from `src/api/`; regex check for known 'meaning
smuggled into `reason`/`metadata` string' patterns." What stays LLM-judged: whether the *design* is
sound — strategic/tactical boundary, whether an abstraction is premature.

## Scope
- **Durable-state-mutation AST scan**: given the plan's proposed changed files (or, more practically,
  the *actual* diff once Implement has run — Investigate should determine whether this check is more
  useful pre-Implement against `plan.md`'s described files, or post-Implement against the real diff,
  since architecture-reviewer today runs pre-Implement against a plan, not code), parse each proposed/
  actual `src/` file with Python's `ast` module and flag any direct mutation of durable state (e.g.
  attribute assignment on a known `AuthoritativeState`/`EntityState` object) occurring outside
  `src/engine/authoritative_pipeline*`. This is the most technically ambitious check of the 4 tickets —
  Investigate must scope realistic precision/recall before committing to a specific AST pattern set;
  a first version that catches only the clearest violations (and is honest about its false-negative
  rate) is preferable to an over-ambitious one that's unreliable.
- **Raw-domain-object API-boundary grep**: a scoped grep/AST check over `src/api/` for functions
  returning a raw domain model type (not a shaped read model/presenter) — reuse whatever naming/typing
  convention already distinguishes the two (Investigate should confirm this convention exists and is
  consistent enough to check mechanically before assuming it).
- **Reason/metadata-smuggling regex check**: a pattern check for known anti-patterns (e.g. durable
  meaning encoded as a parsed/split string inside a `reason` or `metadata` field) — Investigate should
  gather a small corpus of confirmed historical violations (if any exist in `git log`/past architecture-
  review findings) to derive realistic patterns, rather than guessing patterns with no evidence base.
- Add a `verified_by` field to `REVIEW_SCHEMA` in `implement-ticket.js`.
- At least one coverage-honesty test per scan (a fixture file with a known violation must be caught; a
  clean fixture file must not false-positive).

## Out of Scope
- The other 3 gates' static verifiers — see SEQUENCE.md.
- Re-deciding strategic/tactical boundary soundness or abstraction-premature-ness — remains LLM-judged.
- Achieving perfect precision/recall on the AST scan — an honest, documented, imperfect-but-useful first
  version is the target, not a complete static-analysis framework.
- Token/cost telemetry.

## Acceptance Criteria
- [ ] `tools/gate_checks/architecture_reviewer_static.py` exists with 3 documented check functions
      (durable-state mutation, raw-domain-object API exposure, reason/metadata smuggling), each with an
      explicit, disclosed precision/recall caveat.
- [ ] The Review phase's prompt instructs architecture-reviewer to run these checks first and address
      any flagged item, or explain why a flagged item is a false positive.
- [ ] `REVIEW_SCHEMA` gains a `verified_by` field.
- [ ] At least one coverage-honesty test per check function, including a clean-fixture negative control.
- [ ] `docs/ai/agents.md`'s `architecture-reviewer` section and the other 3 shared docs updated.

## Related Tickets
- TCK-20260705-GATE-DET-DONE-CHECKER, TCK-20260705-GATE-DET-PARITY-UPDATER,
  TCK-20260705-GATE-DET-MECHANICS-AUDITOR (siblings — do this one last per SEQUENCE.md)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_gate_determinism.md
- tickets/todos/gate-determinism-followups/SEQUENCE.md
- docs/ai/agents.md, docs/ai/workflows.md, docs/ai/system_overview.md, docs/ai/ticket-lifecycle.md
- CLAUDE.md's Architecture Rule / Durable State Rule (the authoritative definitions these checks encode)

## Related Stored Artifacts
None yet.

## Related Code Areas
- .claude/agents/architecture-reviewer.md
- .claude/workflows/implement-ticket.js (Review phase)
- src/core/, src/engine/authoritative_pipeline*, src/api/ (read-only reference — the actual code shapes
  these checks must recognize)

## Assumptions / Open Questions
- Whether the AST scan should run against `plan.md`'s described files (pre-Implement, matching when
  architecture-reviewer currently runs) or the actual post-Implement diff (more accurate but a pipeline-
  ordering change) — left for Investigate/Plan, this is a genuine design decision that may need
  surfacing back to the user given it could change *when* in the pipeline this check fires.
- Whether a reliable, mechanically-checkable convention already distinguishes "raw domain model" from
  "shaped read model" types in `src/api/` — left for Investigate to confirm before assuming.

## Implementation Notes
(not yet implemented — ticket filed for review before proceeding)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
