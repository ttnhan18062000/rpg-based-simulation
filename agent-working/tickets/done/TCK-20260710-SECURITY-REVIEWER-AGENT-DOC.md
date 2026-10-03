---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260710-SECURITY-REVIEWER-AGENT-DOC
phase: done
date: 2026-07-10
tags: [documentation, ai]
---

# TCK-20260710-SECURITY-REVIEWER-AGENT-DOC

## Title
Document the `security-reviewer` agent in docs/ai/agents.md

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`.claude/agents/security-reviewer.md` exists and is wired into `implement-ticket.js`'s conditional
Security-Review phase (documented in `docs/ai/ticket-lifecycle.md`'s `### Security-Review` section
and referenced in `docs/agent-monitoring/schema.md`'s `SECURITY_BLOCKED` status and phase-name lists).
It was added by `TCK-20260705-WORKFLOW-SECURITY-GATE` (done, 2026-07-05). However, `docs/ai/agents.md`
— the single reference doc enumerating all agents (Role / What it does / Inputs / Outputs / When to
invoke directly, plus an Agent Summary Table row) — has no `security-reviewer` entry. All 12 other
agents currently defined under `.claude/agents/` have both a dedicated subsection and a summary-table
row; `security-reviewer` is the one gap. This is a pure documentation omission with self-evident intent
— no code, workflow, or schema behavior needs to change.

## Scope
- Add a new `### \`security-reviewer\`` subsection to `docs/ai/agents.md`, following the existing
  per-agent structure (Role, What it does, Inputs, Outputs, When to invoke directly) used by every
  other agent entry in the file.
- Content must accurately reflect the actual agent definition at `.claude/agents/security-reviewer.md`:
  its trigger condition (runs only on security-tagged tickets, per `docs/ai/ticket-lifecycle.md`'s
  `### Security-Review` section), its six review categories (injection, unsafe deserialization, path
  traversal, subprocess/command injection, secrets-in-code, raw-domain-model API exposure — the last
  cross-referencing `architecture-reviewer`'s API-boundary rule rather than restating it), its
  `docs/REGISTRY.yaml`-first lookup step, and its APPROVED/NEEDS_CHANGES/BLOCKED verdict output with a
  `summary` field.
- Place the new subsection in the section of `docs/ai/agents.md` that best matches where
  `security-reviewer` sits in the pipeline (it runs after Test/Parity and before Verify, per
  `ticket-lifecycle.md`) — most likely alongside `## Quality and Compliance Agents` (where
  `parity-updater` and `mechanics-auditor` already live) or as its own clearly-labeled gate, consistent
  with how `architecture-reviewer` is presented as a gate under Ticket Lifecycle Agents.
- Add a corresponding row to the `## Agent Summary Table` at the bottom of `docs/ai/agents.md`,
  matching the table's existing `| agent | phase-type | primary output |` column format.

## Out of Scope
- Any change to `.claude/agents/security-reviewer.md` itself (its prompt, tool access, or review
  categories are not being revisited here).
- Any change to `.claude/workflows/implement-ticket.js`'s Security-Review phase logic, gating
  condition, or `SECURITY_BLOCKED` status.
- Any change to `docs/ai/ticket-lifecycle.md` or `docs/agent-monitoring/schema.md` (both already
  document the phase correctly; only `agents.md` has the gap).
- Adding or modifying any parity ledger entry — this is a docs-only change with no simulation behavior
  implication.
- Re-auditing whether any other agent's `docs/ai/agents.md` entry is stale or inaccurate.

## Acceptance Criteria
- [ ] `docs/ai/agents.md` contains a `### \`security-reviewer\`` heading with Role / What it does /
      Inputs / Outputs / When to invoke directly subsections, consistent in structure with the other
      12 agent entries in the file.
- [ ] The new subsection correctly states the trigger condition (security-tagged tickets only, via
      `tags` including `security` or `suggested_skills` including `/security-review`), the six review
      categories, and the APPROVED/NEEDS_CHANGES/BLOCKED verdict output — verifiable by direct
      comparison against `.claude/agents/security-reviewer.md`'s actual content.
- [ ] `## Agent Summary Table` in `docs/ai/agents.md` has a new row for `security-reviewer` with a
      phase-type and primary-output description consistent with the table's existing columns.
- [ ] `docs/ai/agents.md` documents exactly 13 agents (one entry, one summary-table row, per agent
      under `.claude/agents/`) after this change — no other agent gains or loses an entry.
- [ ] `make knowledge-index-update` is run after the docs change (per CLAUDE.md's "After Work" rule for
      any modified `docs/` file) and `docs/REGISTRY.yaml` reflects the updated file at ticket close.

## Related Tickets
- TCK-20260705-WORKFLOW-SECURITY-GATE (done) — added `security-reviewer` and the Security-Review
  phase; this ticket closes the doc gap that ticket's scope did not cover.
- TCK-20260709-CONCERN-INVESTIGATOR-AGENT (done) — precedent for adding a new agent's `docs/ai/agents.md`
  subsection + summary-table row in the same structural pattern being followed here.
- TCK-20260705-AI-AGENT-OVERVIEW-DOC (done) — authored `docs/ai/system_overview.md`, which already
  references `security-reviewer`; not in scope to change, listed for cross-reference only.

## Related Docs
- `docs/ai/agents.md` (file being edited)
- `docs/ai/ticket-lifecycle.md` (`### Security-Review` section — authoritative description of the
  phase/trigger/gate behavior to mirror accurately, not to modify)
- `docs/agent-monitoring/schema.md` (`SECURITY_BLOCKED` status, `Security-Review` phase name list —
  cross-reference only)
- `docs/ai/system_overview.md` (already references the three-layer agent model)
- `docs/ai/workflows.md` (references `security-reviewer` in workflow context)

## Related Stored Artifacts
None found in `stored_artifacts/` specific to `security-reviewer` documentation. Related prior work:
`stored_artifacts/TCK-20260705-WORKFLOW-SECURITY-GATE/` (the gate's original implementation artifacts)
and `stored_artifacts/TCK-20260709-CONCERN-INVESTIGATOR-AGENT/` (structural precedent for this same
kind of agents.md addition).

## Related Code Areas
- `.claude/agents/security-reviewer.md` (source of truth for the new doc content; not modified)
- `docs/ai/agents.md` (edited)

## Assumptions / Open Questions
- Assumes `layer: ai` is correct per this repo's tag-taxonomy note that `layer: ai` denotes the Claude
  agent-orchestration domain (not gameplay AI/cognition, which is tracked under `strategy`) — consistent
  with every other agent-documentation ticket found (e.g. `TCK-20260709-CONCERN-INVESTIGATOR-AGENT`).
- Assumes placement under `## Quality and Compliance Agents` is the best fit; if a reviewer disagrees
  and prefers grouping it under `## Ticket Lifecycle Agents` next to `architecture-reviewer` (both are
  gates), that is a placement-only decision left open for planning/implementation to resolve — it does
  not change scope or acceptance criteria.
- Assumes no `security` tag is needed on this ticket itself: the ticket's own subject matter is a docs
  edit describing a security-review agent, not a change to security-sensitive code, so it does not meet
  the `security` tag's registered scope (matches `/security-review` skill 1:1). This ticket touches only
  `docs/ai/agents.md`, not credentials, secrets, or auth-sensitive code paths.

## Implementation Notes
Added a `### \`security-reviewer\`` subsection to `docs/ai/agents.md`, placed under
`## Quality and Compliance Agents` between `mechanics-auditor` and `world-debugger` (matches the
ticket's primary placement suggestion; the phase runs after Test/Parity and before Verify in the
pipeline, so it sits alongside the other post-implementation compliance agents rather than as its
own top-level gate section). Structure mirrors the existing entries exactly: Role, Trigger,
Registry lookup, What it checks (all six categories from `.claude/agents/security-reviewer.md`,
verbatim on substance), Inputs, Outputs, Gate behavior (cross-referencing `SECURITY_BLOCKED` from
`docs/agent-monitoring/schema.md` and `docs/ai/ticket-lifecycle.md`'s `### Security-Review`
section), and When to invoke directly. Added a matching row to `## Agent Summary Table` between
`mechanics-auditor` and `world-debugger`. No other agent entries were touched. Ran
`make knowledge-index-update` after the edit (1 file re-embedded, 15 chunks). No `src/` code,
workflow logic, or parity ledger changes were made — pure docs addition.

## Test Summary
Docs-only change; no automated tests apply. Verified manually: `docs/ai/agents.md` now documents
exactly 13 agents (one `.claude/agents/*.md` file per entry, one summary-table row each) — confirmed
by comparing agent entry headings against `ls .claude/agents/*.md` (13 files). New section content
cross-checked line-by-line against `.claude/agents/security-reviewer.md` and
`docs/ai/ticket-lifecycle.md`'s `### Security-Review` section / `docs/agent-monitoring/schema.md`'s
`SECURITY_BLOCKED` and phase-name references for consistency.


## Files Changed
- `docs/ai/agents.md` — added `### \`security-reviewer\`` subsection under `## Quality and Compliance Agents` (between `mechanics-auditor` and `world-debugger`) and a corresponding row in `## Agent Summary Table`.
- `tickets/inprogress/TCK-20260710-SECURITY-REVIEWER-AGENT-DOC.md` — this ticket (Implementation Notes, Test Summary, Files Changed, Completion Summary).

## Completion Summary
Closed the one gap in `docs/ai/agents.md`: `security-reviewer` existed on disk and was fully wired
into the `implement-ticket` pipeline's conditional Security-Review phase, but had no entry in the
canonical agent reference doc, unlike all 12 other agents. Added a subsection (Role, Trigger,
Registry lookup, the six review categories, Inputs, Outputs, Gate behavior, When to invoke
directly) under `## Quality and Compliance Agents`, plus a matching Agent Summary Table row.
`docs/ai/agents.md` now documents exactly 13 agents, one per file under `.claude/agents/`. Pure
docs change — no `src/` code, workflow logic, or parity ledger impact. `make knowledge-index-update`
was run after the edit. Verified via 6 passing tests (`test_add_frontmatter_live.py::test_ai_dir_active`,
`test_concern_investigator_agent_definition.py` x5) plus `validate_frontmatter.py` on both changed files.

