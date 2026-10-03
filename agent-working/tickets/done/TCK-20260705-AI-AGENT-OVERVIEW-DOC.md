---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260705-AI-AGENT-OVERVIEW-DOC
phase: done
date: 2026-07-05
tags: [documentation, ai, workflows]
---

# TCK-20260705-AI-AGENT-OVERVIEW-DOC

## Title
Write a single consolidated technical overview document for the AI agent system

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
User asked whether a single document exists explaining the AI agent system technically, including
simulation-testing workflows and project-implementation/development workflows. The information exists
today but is split across 6 files under `docs/ai/` (`README.md`, `agents.md`, `workflows.md`,
`skills.md`, `ticket-lifecycle.md`, `agent_infrastructure_audit.md`) plus `docs/simulation/lab_contract.md`
and `docs/simulation_quality/audit_workflow.md`. User confirmed: write a consolidated document.

## Scope
- Read all source documents in full (see Related Docs) to synthesize accurately — no re-deriving
  content from memory or assumption.
- Write one new document that gives a complete technical narrative of the AI agent system:
  - The three-layer model (agents / workflows / skills) and how they compose.
  - The full ticket lifecycle / project-implementation-and-development workflow
    (`create-tickets` → `implement-ticket` → `implement-epic`, the 9-phase pipeline, tiers, gates).
  - The simulation-testing/lab workflow (`generate-simulation-setup` → `prepare-simulation-execution`
    → `investigate-simulation-result` → `propose-simulation-enhancements` → `register-simulation-result`
    → `compact-simulation-result` → `update-knowledge-store`, human-gated design) and the SimQ audit
    workflow (`docs/simulation_quality/audit_workflow.md`) as the two distinct testing/quality lanes.
  - Observability (agent-monitoring: runs.jsonl/events.jsonl/tools.jsonl, retro process).
  - Where to go deeper (cross-references to the 6+ source docs, not a replacement for them).
- This is a synthesis/narrative document, not a replacement for the detailed reference docs — those
  stay the source of truth for exact schemas/field lists; this doc's job is the "complete technical
  explanation" narrative the user asked for, with links out for detail.
- Add the new document to `docs/ai/README.md`'s Document Index and `docs/README.md`'s AI Tooling
  section.

## Out of Scope
- Modifying any of the 8 source documents' actual content (agents.md, workflows.md, skills.md,
  ticket-lifecycle.md, agent_infrastructure_audit.md, lab_contract.md, audit_workflow.md, schema.md) —
  read-only inputs for synthesis.
- Re-auditing or re-scoring the agent infrastructure — `agent_infrastructure_audit.md` already exists
  for that; this new doc narrates the system, it doesn't re-evaluate it.
- Building any new tooling, workflow, or code — pure documentation.

## Acceptance Criteria
- [ ] New document exists, covering: three-layer model, full ticket-lifecycle/implementation workflow,
      simulation-testing/lab workflow, SimQ audit workflow, observability/monitoring, with accurate
      cross-references to all source docs.
- [ ] Every specific claim (phase names, file paths, tier rules, gate names) is verified against the
      actual current source docs/code, not paraphrased from memory.
- [ ] `docs/ai/README.md`'s Document Index has a new row for this document.
- [ ] `docs/README.md`'s AI Tooling section references it.
- [ ] Frontmatter passes `tools/validate_frontmatter.py`.

## Related Tickets
None — first ticket of its kind; no prior "consolidated overview" doc existed.

## Related Docs
- docs/ai/README.md (index target + source)
- docs/ai/agents.md (source — all 11 subagents)
- docs/ai/workflows.md (source — all 8 workflows, dev + simulation)
- docs/ai/skills.md (source — skill catalog)
- docs/ai/ticket-lifecycle.md (source — full dev flow)
- docs/ai/agent_infrastructure_audit.md (source — scored audit, cross-reference not re-derive)
- docs/simulation/lab_contract.md (source — simulation lab workflow contract)
- docs/simulation_quality/audit_workflow.md (source — SimQ audit workflow)
- docs/agent-monitoring/schema.md, docs/guides/agent_monitoring.md (source — observability)
- docs/README.md (index target)

## Related Stored Artifacts
staging_artifacts/TCK-20260705-AI-AGENT-OVERVIEW-DOC/ (standard tier)

## Related Code Areas
N/A — pure documentation ticket, no code.

## Assumptions / Open Questions
- Exact file name/path for the new document — left for Plan to decide (candidate:
  `docs/ai/system_overview.md` or similar, under `docs/ai/` since this is meta-documentation about the
  agent tooling itself, not a `docs/guides/` subsystem how-to).

## Implementation Notes
Implemented per the approved plan (`staging_artifacts/TCK-20260705-AI-AGENT-OVERVIEW-DOC/plan.md`),
zero deviations.

- Created `docs/ai/system_overview.md` (frontmatter `status: active`, `layer: ai`, `authority: P1`,
  `audience: developer`, matching every other `docs/ai/*.md` file) with 6 headed sections: (1) Overview
  and Purpose, (2) The Three-Layer Model, (3) Ticket Lifecycle and the Development Pipeline, (4)
  Simulation Testing: the Lab Workflow Chain and the Lab Session Contract, (5) Quality Lanes: Test, Lab,
  and SimQ Audit, (6) Observability and Where to Go Deeper. Per the plan's own note, the plan's internal
  "Sections 1-4" / "Sections 5-7" step labels were for review tracking only; the final document uses a
  natural 6-heading scheme covering the same content.
- Re-verified directly against source before writing (not copied from investigation.md verbatim):
  confirmed `.claude/agents/*.md` = 11 files; confirmed via `grep -n "phase("` that
  `create-tickets.js`, `generate-simulation-setup.js`, `investigate-simulation-result.js`, and
  `compact-simulation-result.js` have the exact phase names investigation reported (Comprehend/
  Investigate/Structure/Write/Link; Scan/Draft/Validate; Load/Analyze/Report; Scan/Compact/Archive) —
  all 4 attributed in the new doc's prose to the `.js` file, never to `workflows.md`; confirmed
  `docs/agent-monitoring/schema.md` L111-113 independently lists the same 5 `create-tickets` phases;
  confirmed `docs/simulation/lab_contract.md`'s 6 stages, session states, and human-approval-gate wording;
  confirmed `docs/simulation_quality/audit_workflow.md`'s 7 phases and Report-phase branching; confirmed
  `docs/ai/agent_infrastructure_audit.md` L15 headline "8.0 / 10 — Mature, gated, not yet deterministic"
  verbatim; confirmed 16 skill folders via `ls -d .claude/skills/*/ | wc -l`.
- Never wrote "8 workflows" as a factual total anywhere in the new doc; stated "11 workflow files ...
  10 ... documented ... the 11th, simq-audit.js ...". Kept the lab_contract/workflows relationship
  paragraph hedged ("drives", "corresponds to", "no source document states an exact mapping"). Kept
  Section 5 to three distinct quality lanes (dev-pipeline Test phase / simulation lab / SimQ audit), not
  two. Phrased Section 6's staleness paragraph as a dated observation ("as of 2026-07-05 ... does not yet
  ... these are candidates for a future documentation-maintenance ticket") — never as "fixed" or
  "corrected".
- Added exactly one new row (first row) to `docs/ai/README.md`'s Document Index table, and exactly one
  new bullet (first bullet) to `docs/README.md`'s AI Tooling section, using the plan's exact text. No
  other line in either file was touched — confirmed via `git diff`, which shows only the one added line
  per file (the stale "All 8 workflows" row in `docs/ai/README.md` was deliberately left untouched, per
  Scope Guards).
- Did not edit any of the 8 source documents' body content (`agents.md`, `workflows.md`, `skills.md`,
  `ticket-lifecycle.md`, `agent_infrastructure_audit.md`, `lab_contract.md`, `audit_workflow.md`,
  `docs/agent-monitoring/schema.md`). Did not create a new ticket for the workflows.md/skills.md
  staleness — recorded only in the new doc's Section 6 and in this ticket's Completion Summary below.
- No code, `src/`, or `tests/` files changed; no `data/runs/` or `reports/release_proof/` artifacts were
  produced (nothing to clean up).

## Test Summary
Documentation-only ticket — no `src/`/`tests/` behavior changed. Verification run:

```
python3 tools/validate_frontmatter.py docs/ai/system_overview.md
  → OK: 1 file(s) checked — no violations (exit 0)
python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260705-AI-AGENT-OVERVIEW-DOC/investigation.md
  → OK: 1 file(s) checked — no violations (exit 0)
python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260705-AI-AGENT-OVERVIEW-DOC/plan.md
  → OK: 1 file(s) checked — no violations (exit 0)
python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260705-AI-AGENT-OVERVIEW-DOC/test_plan.md
  → OK: 1 file(s) checked — no violations (exit 0)
python3 -m pytest tests/tools/test_validate_frontmatter.py -q
  → 64 passed (exit 0)
```

Manual fact-check checklist from `test_plan.md` was applied during drafting (see Implementation Notes
above) rather than left to a separate Verify pass, since this is a synthesis document and drafting-time
verification is the only meaningful check available.

## Files Changed
- `docs/ai/system_overview.md` (new file)
- `docs/ai/README.md` (Document Index — one new row added)
- `docs/README.md` (AI Tooling section — one new bullet added)

## Completion Summary
New consolidated overview document written and wired into both doc indexes; all 5 verification commands
pass; no source document content was modified. Observable behavior change: none (pure documentation).

**Recommended follow-up (not filed as a ticket, per this ticket's Out of Scope and the plan's explicit
"Follow-up ticket decision"):** `docs/ai/workflows.md` is stale in 4 places relative to
`.claude/workflows/*.js` (`create-tickets`, `generate-simulation-setup`,
`investigate-simulation-result`, `compact-simulation-result` phase names) and is missing `simq-audit`
from its catalog entirely; `docs/ai/skills.md` is missing a `/simq-audit` entry; `docs/ai/README.md`'s
Document Index row for `workflows.md` still reads "All 8 workflows" against an actual count of 11 files
/ 10 documented. A future documentation-maintenance ticket should reconcile these three files with
current code.
