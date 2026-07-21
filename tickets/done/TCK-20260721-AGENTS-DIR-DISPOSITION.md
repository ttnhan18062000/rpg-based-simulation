---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-AGENTS-DIR-DISPOSITION
phase: done
date: 2026-07-21
tags: [ai, workflows, process-improvement]
---

# TCK-20260721-AGENTS-DIR-DISPOSITION

## Title
Audit and disposition the legacy .agents/ directory

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
A dedicated audit of the existing .agents/ directory before any new Codex adapter work begins. Every path in .agents/ must be classified as retain-and-migrate, replace, or archive/retire, and the audit must settle on exactly one approved future active Codex instruction/skill location. .agents/ is historical/stale scaffolding and must not be assumed safe to enable as-is, to avoid becoming a third, ambiguous source of agent instructions.

## Scope
- This ticket may create only isolated contract, replay, fixture, diagnostic, or decision-record work. It must not modify production Claude/Codex workflows, hooks, monitoring writers, live ticket artifacts, or the shared monitoring JSONL corpus.
- Classify every top-level path under .agents/ (rules/, skills/, workflows/, task.md) into retain-and-migrate, replace, or archive/retire, at subdirectory granularity where content diverges.
- Settle on exactly one approved future active Codex instruction/skill location and state whether .agents/ is retained as that location, partially retained, or fully superseded.
- Determine and document whether WorkflowRegistry (src/lab/registry.py) is intended future production wiring or itself dead/unwired code.
- Resolve tests/unit/lab_agent/test_workflow_registry.py::test_real_registry_contracts's hardcoded dependency on .agents/workflows and .agents/skills paths, consistent with whatever disposition is chosen.

## Out of Scope
- Creating any provider-runtime implementation ticket — blocked until all 5 discovery outputs are complete, evidence-backed, and explicitly approved (see parent epic TCK-20260721-PROVIDER-AGNOSTIC-EPIC).
- No Codex adapter implementation work — this ticket is audit/disposition only.
- No modification of any production Claude workflow, hook, or monitoring writer as part of this audit.

## Acceptance Criteria
- [x] Audit classifies every top-level path under .agents/ (rules/, skills/, workflows/, task.md) into exactly one of retain-and-migrate/replace/archive-retire, at subdirectory granularity where content diverges.
- [x] Audit names exactly one approved future active Codex instruction/skill location and states explicitly whether .agents/ itself is retained as that location, partially retained, or fully superseded.
- [x] The audit itself makes and documents the determination of whether WorkflowRegistry (src/lab/registry.py) is intended future production wiring or itself dead/unwired code — this AC does not assume either answer in advance.
- [x] After the ticket lands, pytest on tests/unit/lab_agent/test_workflow_registry.py passes with either real-path assertions intact (if retained as-is), updated paths/assertions (if migrated), or explicit documented test retirement (if the Lab WorkflowRegistry feature is itself retired) — never left red or silently orphaned.

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260524-WORKFLOW-REGISTRY

## Related Docs
- docs/ai/agent_infrastructure_audit.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/lab/registry.py
- tests/unit/lab_agent/test_workflow_registry.py
- .agents/task.md
- .agents/rules/AGENTS.md
- .agents/rules/workflow.md
- .agents/rules/ticket.md
- .agents/rules/testing.md
- .agents/rules/architecture.md
- .agents/rules/authoritative_mechanics.md
- .agents/rules/graphify.md
- .agents/rules/engine_contracts.md
- .agents/rules/done.md
- .agents/workflows/generate-simulation-setup.md
- .agents/workflows/prepare-simulation-execution.md
- .agents/workflows/register-simulation-result.md
- .agents/workflows/compact-simulation-result.md
- .agents/workflows/investigate-simulation-result.md
- .agents/workflows/propose-simulation-enhancements.md
- .agents/workflows/update-knowledge-store.md
- .agents/workflows/graphify.md

## Assumptions / Open Questions
- WorkflowRegistry is never instantiated anywhere in src/ — only 3 call sites total, all inside tests/unit/lab_agent/test_workflow_registry.py; audit must determine whether this is planned future wiring or itself vestigial, not assume either answer.
- The 'copied skills' framing is only partially accurate — .agents/skills/ (18 dirs) and .claude/skills/ (16 dirs) diverge in membership; treat as its own divergent catalog, not a 1:1 duplicate.
- Real .agents/skills/*/SKILL.md content is never asserted by any currently-passing test (only get_workflow() against real content is tested) — retiring/migrating skills/ carries no test-breakage risk today but also no test-verified correctness.
- .agents/rules/AGENTS.md confirmed an older, simpler rule set (no docs/REGISTRY.yaml, tag/layer registries, or parity ledger mentions), supporting the historical/stale framing for rules/ specifically; .agents/task.md confirmed 0 bytes.
- This disposition is a stated precondition for the broader Codex-adapter proposal — implementing Codex adapter work before this lands risks creating a third, ambiguous source of agent instructions.
- Depends on TCK-20260721-PROVIDER-AGNOSTIC-EPIC as parent; no dependency on sibling children TCK-20260721-CODEX-CAPABILITY-MATRIX or TCK-20260721-MONITORING-WRITER-DECISION — can run in parallel with them.

## Implementation Notes

Created `docs/ai/agents_dir_disposition.md`, the disposition doc classifying every top-level `.agents/` path:
- `.agents/task.md` and all 8 `.agents/rules/*.md` files → **archive-retire** (near-verbatim earlier drafts of now-extended `CLAUDE.md` sections; `authoritative_mechanics.md` additionally cites a factually stale "17-phase apply sequence" vs. the current 32-phase pipeline).
- `.agents/rules/engine_contracts.md` → **retain-and-migrate** (prescriptive per-subsystem update-rule detail not present anywhere in current `CLAUDE.md`; migration target left as future-ticket work).
- 11 `.agents/skills/*` dirs with `.claude/skills/` name-matches → **archive-retire** (one pair byte-diffed identical; remaining 10 not individually diffed, follow-up spot-check flagged as non-blocking future work).
- `.agents/skills/graphify/` → **archive-retire**, superseded by the user-global `~/.claude/skills/graphify/SKILL.md`, not a project-scope migration target.
- 6 `.agents/skills/*` dirs with no `.claude/skills/` equivalent (`clean-code`, `codebase-search`, `code-review`, `create-skill`, `receiving-code-review`, `requesting-code-review`) → **retain-and-migrate** (unique content, no test coverage, candidates for a future promotion-review ticket).
- All 8 `.agents/workflows/*.md` files → **archive-retire** (declarative-only contracts never enforced by `.claude/workflows/*.js` at runtime; their only consumer, `WorkflowRegistry`, is decoupled from them in this same ticket).

Named `.claude/` (CLAUDE.md + `.claude/workflows/*.js` + `.claude/skills/` + `.claude/agents/*.md`) as the single approved active Codex/Claude instruction-and-skill location. `.agents/` is fully superseded except the two named `retain-and-migrate` carve-outs, both deferred to future tickets.

Determined `WorkflowRegistry` (`src/lab/registry.py:31-111`) is **dead/unwired code today**: zero production call sites (grep + graphify BFS), `src/lab/cli.py` and `src/lab/workflows.py` never reference it, and `TCK-20260524-LAB-GUARDRAILS` concretely scoped wiring it in then shipped a plain-dict `limits` parameter instead — direct evidence of abandoned, not merely deferred, wiring. Separated this from the un-decided question of whether its YAML-frontmatter-to-Pydantic parsing pattern is reusable for the parent epic's still-open contract-format decision — not resolved here, left to the parent epic. `src/lab/registry.py` and `src/lab/__init__.py` were not modified.

Decoupled `test_real_registry_contracts` (`tests/unit/lab_agent/test_workflow_registry.py`) from the live `.agents/workflows/`/`.agents/skills/` directories by adding two committed fixture files (`tests/unit/lab_agent/fixtures/agents_workflows/generate-simulation-setup.md`, `prepare-simulation-execution.md` — verified byte-identical to the `.agents/workflows/` source via `diff`) and an empty `tests/unit/lab_agent/fixtures/agents_skills/` dir (tracked via `.gitkeep`). Repointed the test's `workflows_dir`/`skills_dir` construction at the fixtures and updated its docstring to cite this ticket; every field-level assertion is unchanged. No other test in `tests/unit/lab_agent/` or `tests/integration/lab_agent/` was touched. `.agents/` files were only read/copied from, never edited.

**Deviation from plan.md:** the plan suggested reusing tags `audit`/`agent-infrastructure` (matching `docs/ai/agent_infrastructure_audit.md`'s frontmatter) on the new doc. Checked `python3 tools/tag_registry.py list` and found neither tag is actually registered (that older doc predates the 2026-07-04 tag-registry validation cutoff, so it was never checked). Used the ticket's own already-registered tags instead (`ai`, `workflows`, `process-improvement`) plus two more exact registry matches (`lab-agent`, `documentation`). Recorded in `staging_artifacts/TCK-20260721-AGENTS-DIR-DISPOSITION/plan.md`'s Deviations section.

## Test Summary

Baseline (Step 1, before any change) and final (Step 5, after all changes) both green, identical counts — confirms zero regression:
- `tests/unit/lab_agent/` → 33 passed (includes `test_workflow_registry.py` 4/4, `test_real_registry_contracts` now reading from fixtures)
- `tests/integration/lab_agent/` → 62 passed
- `python3 -c "import src.lab"` → OK
- `python3 -c "import src.lab.cli"` → OK

## Files Changed

- `docs/ai/agents_dir_disposition.md` (new) — disposition doc
- `tests/unit/lab_agent/fixtures/agents_workflows/generate-simulation-setup.md` (new) — byte-identical fixture snapshot
- `tests/unit/lab_agent/fixtures/agents_workflows/prepare-simulation-execution.md` (new) — byte-identical fixture snapshot
- `tests/unit/lab_agent/fixtures/agents_skills/.gitkeep` (new) — empty dir placeholder
- `tests/unit/lab_agent/test_workflow_registry.py` (modified) — `test_real_registry_contracts` repointed at fixtures, docstring updated; no assertion changed
- `tickets/inprogress/TCK-20260721-AGENTS-DIR-DISPOSITION.md` (this file) — closure updates
- `staging_artifacts/TCK-20260721-AGENTS-DIR-DISPOSITION/plan.md` — Deviations section added

No file under `.agents/`, `.claude/`, `CLAUDE.md`, or `src/lab/registry.py`/`src/lab/__init__.py` was modified.

## Completion Summary

Audited and classified every top-level `.agents/` path (task.md, 9 rules files, 18 skill dirs, 8 workflow files) into retain-and-migrate/archive-retire at subdirectory granularity, recorded in `docs/ai/agents_dir_disposition.md`. Named `.claude/` as the single approved active Codex/Claude instruction-and-skill location, with `.agents/` fully superseded except two named carve-outs deferred to future tickets. Determined `WorkflowRegistry` is dead/unwired code today, evidence-backed, without foreclosing on reuse of its parsing pattern for the parent epic's open contract-format question. Decoupled `test_real_registry_contracts` from live `.agents/` content via committed fixture snapshots, keeping it green and no longer coupled to the now-archived-classified `.agents/workflows/`. All 4 acceptance criteria met; full scoped regression (33 + 62 tests, 2 import checks) passes with zero drift from the pre-change baseline. No `.agents/`, `.claude/`, `CLAUDE.md`, or `src/lab/registry.py` file was touched.
