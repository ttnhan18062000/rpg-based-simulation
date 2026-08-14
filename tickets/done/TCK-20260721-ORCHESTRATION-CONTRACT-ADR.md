---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-ORCHESTRATION-CONTRACT-ADR
phase: done
date: 2026-07-21
tags: [ai, workflows, process-improvement]
---

# TCK-20260721-ORCHESTRATION-CONTRACT-ADR

## Title
Produce the shared orchestration-contract ADR

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
An architecture decision record that decides the provider-neutral contract representation, source ownership, versioning, the provider-adapter boundary, and the conformance mechanism — as a decision artifact, not a runtime migration. Execution identity is consumed as an already-decided input from TCK-20260721-MONITORING-WRITER-DECISION, not decided independently here (corrected per Codex's 2026-07-21 ticket-batch review — the original draft contradictorily claimed to both decide and not decide execution identity). Explicitly depends on the outputs of the .agents audit, Codex capability matrix, and monitoring/writer decision child tickets, and must not lock in final location/writer choices ahead of that evidence.

## Scope
- This ticket may create only isolated contract, replay, fixture, diagnostic, or decision-record work. It must not modify production Claude/Codex workflows, hooks, monitoring writers, live ticket artifacts, or the shared monitoring JSONL corpus.
- Decide the provider-neutral contract representation/format, source ownership, versioning, provider-adapter boundary, and conformance mechanism as a decision artifact, not a runtime migration.
- Treat execution identity (immutable execution key, human-readable run reference, ticket linkage) as an already-decided input from TCK-20260721-MONITORING-WRITER-DECISION — this ADR may specify how the shared contract carries/represents that identity, but must not choose its format or ownership independently.
- Consume TCK-20260721-AGENTS-DIR-DISPOSITION, TCK-20260721-CODEX-CAPABILITY-MATRIX, and TCK-20260721-MONITORING-WRITER-DECISION as required evidence inputs before finalizing any decision.
- Pick and document one explicit ADR filename/numbering convention for this and future ADRs in docs/architecture/.

## Out of Scope
- Creating any provider-runtime implementation ticket — blocked until all 5 discovery outputs are complete, evidence-backed, and explicitly approved (see parent epic TCK-20260721-PROVIDER-AGNOSTIC-EPIC).
- Deciding the execution-identity format or ownership (Open Decision #3) or the concurrent-write strategy (Open Decision #5) — both are TCK-20260721-MONITORING-WRITER-DECISION's decisions to make; this ADR only consumes their output as a required evidence input.
- No runtime migration or production code change implementing the decided contract.

## Acceptance Criteria
- [x] New ADR doc lands at docs/architecture/<name>.md with valid frontmatter (status/layer/authority/audience) passing tools/validate_frontmatter.py, using an already-registered layer (e.g. ai).
- [x] ADR body contains explicit, separately labeled decisions for: contract representation/format, source ownership, versioning, provider-adapter boundary, and conformance mechanism — not folded into general prose.
- [x] ADR treats execution identity as a required, already-decided input consumed from TCK-20260721-MONITORING-WRITER-DECISION — it may specify how the shared contract represents/carries that identity, but does not choose its format or ownership independently; the ADR's Scope, Out of Scope, and Acceptance Criteria all state this same boundary with no contradictory wording between sections.
- [x] ADR explicitly states it makes no final location or writer-implementation choice and cites TCK-20260721-AGENTS-DIR-DISPOSITION, TCK-20260721-CODEX-CAPABILITY-MATRIX, and TCK-20260721-MONITORING-WRITER-DECISION as the evidence inputs it consumed.
- [x] This ticket's own process picks and documents ONE explicit ADR filename/numbering convention (recommend following the two real precedent docs' frontmatter + unnumbered-title + Status/Context/Decision/Rationale/Trade-offs/Consequences shape over the unused numbered ADR-XXX template), stating which was chosen and why — not silently defaulted.
- [x] ADR is registered via docs/REGISTRY.yaml regeneration (make knowledge-index-update) and linked from the 'Related Material' section of the main plan doc.

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260721-AGENTS-DIR-DISPOSITION
- TCK-20260721-CODEX-CAPABILITY-MATRIX
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-CODEX-REPLAY-PROOF

## Related Docs
- docs/architecture/simulation_watchdog.md
- docs/architecture/performance_optimization.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_ticket_handoff_codex.md
- docs/guidelines/frontmatter_schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/skills/architecture/trade-off-analysis.md
- .agents/skills/architecture/trade-off-analysis.md

## Assumptions / Open Questions
- No formal 'how to write an ADR' doc exists in docs/guidelines/ — the only ADR template (.claude/skills/architecture/trade-off-analysis.md, mirrored in .agents/) prescribes a numbered 'ADR-[XXX]' title and docs/architecture/adr-NNN-*.md filename, but neither existing ADR-shaped doc (simulation_watchdog.md, performance_optimization.md) follows that convention — this ticket must explicitly pick a convention rather than silently defaulting to the unused skill template.
- Zero adr-*.md files exist in the repo today — a just-closed hotfix (TCK-20260720-CLAUDE-MD-CONSISTENCY-FIXES) had to strip stale CLAUDE.md references to nonexistent 'adr-004/adr-005' files — do not resurrect that numbering without a deliberate decision.
- Two of the idea doc's five 'Open Decisions' (#3 execution-ID format, #5 concurrent-write strategy) are owned by sibling concern TCK-20260721-MONITORING-WRITER-DECISION, not this ADR — scope-creep risk if this ticket tries to resolve them itself instead of consuming that ticket's output as evidence.
- Depends on TCK-20260721-AGENTS-DIR-DISPOSITION, TCK-20260721-CODEX-CAPABILITY-MATRIX, and TCK-20260721-MONITORING-WRITER-DECISION landing first — must be encoded as an explicit blocking/depends-on link, not marked ready-to-implement until those three land.

## Implementation Notes
Authored `docs/architecture/agent_orchestration_contract.md` following the plan exactly:
frontmatter (`status: active`, `layer: ai`, `authority: P1`, `audience: developer`,
`tags: [ai, workflows, process-improvement]`, all registry-backed values confirmed via
`tools/layer_registry.py list` / `tools/tag_registry.py list`), unnumbered title, and the
`Status → Context → Decision → Rationale → Trade-offs → Consequences → Revisit Trigger`
shape matching `simulation_watchdog.md` / `performance_optimization.md`. A leading italic
note under the title states the filename/convention rationale (descriptive-slug +
frontmatter vs. the unused numbered `ADR-[XXX]` template).

`## Decision` has exactly 5 labeled `###` subsections (Contract Representation and Format,
Source Ownership, Versioning, Provider-Adapter Boundary, Conformance Mechanism), each
closed with a bolded `**Status:** ...` tag per the plan's evidence-weight assignment
(Decided / Decided / Proposed-pending-implementation-evidence / Decided /
Proposed-pending-implementation-evidence). A sixth, separately labeled
`### Execution Identity (Consumed Input)` subsection quotes
`docs/ai/monitoring_writer_decision.md:91-142` §2 verbatim (immutable `execution_id`
format string, `run_id` display field, `ticket_id` join-key promotion) and is tagged
`**Status:** Consumed-as-input`, with an explicit sentence that this ADR does not choose
that format/ownership independently.

`## Context` cites all 3 evidence-input tickets/docs and cites the source plan's own
"Approval model and exit gate" 5-output list (`idea_..._orchestration.md:124-145`), not
the ticket-handoff doc's differently-ordered sequencing table, per the plan's explicit
instruction. States the no-final-location/writer-choice sentence verbatim as specified.

Steps 2-5 executed as planned:
- Step 2: `python3 tools/validate_frontmatter.py docs/architecture/agent_orchestration_contract.md` → exit 0.
- Step 3: `python3 tools/generate_registry.py` (the actual regeneration target; `make
  knowledge-index-update` only rebuilds the semantic search index, it does not touch
  `docs/REGISTRY.yaml` — see Deviations note in `plan.md`) plus `make knowledge-index-update`
  itself for the search index. New ADR entry confirmed present in `docs/REGISTRY.yaml` with
  `layer: ai` and the 3 tags.
- Step 4: added one link line, `` - `docs/architecture/agent_orchestration_contract.md` ``,
  to the source plan's `## Related Material` section, matching the existing 11 entries'
  bare-backtick-path style exactly (no descriptions in that section's actual style, contrary
  to the plan's paraphrase "relative path + short description" — matched the real style, not
  the paraphrase).
- Step 5: both scoped pytest commands pass (136 passed; 8 passed). `git status`
  confirms this ticket's diff contribution is confined to the expected file set; all other
  modified/untracked files present in the working tree (agent-monitoring/*, other docs/ai/*.md,
  stored_artifacts/ for sibling tickets, tickets/working_log.csv entries, etc.) predate this
  implementation session and belong to the 3 already-done sibling discovery tickets in the same
  batch.

No architectural conflicts encountered. No `agent-orchestration/` directory, contract file,
or runtime code created. `docs/ai/agents_dir_disposition.md`, `docs/ai/codex_capability_matrix.md`,
and `docs/ai/monitoring_writer_decision.md` were read/cited only, never edited.

## Test Summary
- `python3 tools/validate_frontmatter.py docs/architecture/agent_orchestration_contract.md` — exit 0.
- `.venv/bin/python -m pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py -v` — 136 passed.
- `.venv/bin/python -m pytest tests/integration/content/test_registry_projection_parity.py -v` — 8 passed.
- Full test suite not run (scoped per project testing rule).

## Files Changed
- `docs/architecture/agent_orchestration_contract.md` (new)
- `docs/REGISTRY.yaml` (regenerated)
- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md` (one added link line in `## Related Material`)

## Completion Summary
Produced the shared orchestration-contract ADR (`docs/architecture/agent_orchestration_contract.md`)
as a pure documentation deliverable: 5 explicitly labeled decisions (contract
representation/format, source ownership, versioning, provider-adapter boundary,
conformance mechanism) plus a separate, verbatim-quoted "consumed input" subsection for
execution identity from `TCK-20260721-MONITORING-WRITER-DECISION`. Frontmatter validated,
`docs/REGISTRY.yaml` regenerated with the new entry, and the ADR linked back from the source
plan's Related Material section. No `agent-orchestration/` directory, contract file, runtime
code, or production Claude/Codex workflow file was created or touched. All acceptance
criteria met; all scoped tests pass; containment confirmed via `git status`.
