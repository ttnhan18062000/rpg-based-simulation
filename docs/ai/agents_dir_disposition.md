---
status: active
layer: ai
authority: P1
audience: developer
tags: [ai, workflows, process-improvement, lab-agent, documentation]
---

# .agents/ Directory Disposition — TCK-20260721-AGENTS-DIR-DISPOSITION

A dedicated audit of the legacy `.agents/` directory, performed as a precondition for any new Codex-adapter work (see `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md`). Every path under `.agents/` is classified below into exactly one of **retain-and-migrate**, **replace**, or **archive-retire**, and this doc settles today's approved active delivery surfaces for each provider separately — Claude and Codex do not share one location (see "Approved active location" below).

This is a decision record, not a migration. No file under `.agents/` is deleted, moved, or edited as part of landing this doc — classification only. Execution of any `retain-and-migrate` item is deferred to a future ticket.

## Per-path classification

| Path | Classification | Rationale |
|---|---|---|
| `.agents/task.md` | **archive-retire** | 0 bytes. No content to lose. |
| `.agents/rules/AGENTS.md` | **archive-retire** | Near-verbatim earlier draft of what is now `CLAUDE.md`'s top-level rule set. `CLAUDE.md` materially extends it (tag/layer registries, `docs/REGISTRY.yaml`, `agent-monitoring/`, tier routing — none present here). |
| `.agents/rules/workflow.md` | **archive-retire** | Earlier draft of `CLAUDE.md`'s "Workflow Rule" section; same Before/During/After skeleton, missing everything `CLAUDE.md` added since. |
| `.agents/rules/ticket.md` | **archive-retire** | Earlier draft of `CLAUDE.md`'s "Ticket Format" section. Its required-section list omits `## Tier` and `## Priority` entirely, and it has no frontmatter block at all — a confirmed older ticket shape. |
| `.agents/rules/testing.md` | **archive-retire** | Earlier draft of `CLAUDE.md`'s "Testing Rule" section, fully superseded. |
| `.agents/rules/architecture.md` | **archive-retire** | Earlier draft of `CLAUDE.md`'s "Architecture Rule" section, fully superseded. |
| `.agents/rules/authoritative_mechanics.md` | **archive-retire** | Earlier draft of `CLAUDE.md`'s "Authoritative Mechanics Rule" section. Line 18 cites a "17-phase apply sequence"; the current `docs/engine/authoritative_pipeline.md` and `CLAUDE.md` describe a 32-phase refinement sequence. This is a concrete factual drift, not just staleness — the file is actively wrong and must not be cited as a reference. |
| `.agents/rules/done.md` | **archive-retire** | Earlier draft of `CLAUDE.md`'s "Definition of Done" section, fully superseded. |
| `.agents/rules/graphify.md` | **archive-retire** | Earlier draft of `CLAUDE.md`'s "Graphify Integration" section, fully superseded. |
| `.agents/rules/engine_contracts.md` | **retain-and-migrate** | Not a strict subset of `CLAUDE.md`. Holds prescriptive per-subsystem "when X changes, update doc Y and parity ledger Z" operational detail that `CLAUDE.md`'s current Engine Contracts section (a summary table only) does not have. This content needs a home — candidate: fold into `docs/engine/` or expand `CLAUDE.md`'s Engine Contracts section — in a **future ticket**. This ticket does not perform that migration. |
| `.agents/skills/api-design-principles/`, `architecture/`, `backend-testing/`, `brainstorming/`, `debugging-strategies/`, `doc-coauthoring/`, `frontend-design/`, `prompt-builder/`, `python-performance-optimization/`, `python-testing-patterns/`, `test-driven-development/` (11 dirs) | **archive-retire** | Superseded by the same-named entries in `.claude/skills/`. One pair (`api-design-principles`) was byte-diffed identical during investigation. The remaining 10 pairs were **not** individually byte-diffed — record a follow-up hygiene spot-check as a future, non-blocking task rather than claiming full byte-verification that wasn't performed. |
| `.agents/skills/graphify/` | **archive-retire** | Superseded, but by the **user-level global** skill (`~/.claude/skills/graphify/SKILL.md`), not a `.claude/skills/` project-scope entry. This is a different tier, not a migration target — do not write this up as "needs migration into `.claude/skills/`". |
| `.agents/skills/clean-code/`, `codebase-search/`, `code-review/`, `create-skill/`, `receiving-code-review/`, `requesting-code-review/` (6 dirs) | **retain-and-migrate** | No `.claude/skills/` equivalent exists for any of these, and no test asserts their content. Nothing currently supersedes them. Record as candidates for a future promotion-review ticket rather than archiving unique, unreviewed content by default. |
| `.agents/workflows/*.md` (8 files: `generate-simulation-setup.md`, `prepare-simulation-execution.md`, `register-simulation-result.md`, `compact-simulation-result.md`, `investigate-simulation-result.md`, `propose-simulation-enhancements.md`, `update-knowledge-store.md`, `graphify.md`) | **archive-retire** | Confirmed declarative-only contracts (`allowed_actions`/`forbidden_actions`/etc.) never enforced at runtime — grep found zero references to `allowed_actions`, `forbidden_actions`, `.agents`, or `WorkflowRegistry` in the real `.claude/workflows/*.js` orchestration. Their only current consumer, `WorkflowRegistry` (see below), is decoupled from them by this same ticket (see "Test-pairing note" below), removing the last reason to keep them live. |

## Approved active location

**Two provider-native delivery surfaces exist today, not one shared location:**

- **Claude**: `.claude/` — rules → `CLAUDE.md`, orchestration → `.claude/workflows/*.js`, skills → `.claude/skills/`, agent role definitions → `.claude/agents/*.md`. Already active and correctly documented as-is; unchanged by this fix.
- **Codex**: root `AGENTS.md` (durable instructions) + `.agents/skills/` (repository skills), per the official Codex manual, verified in `docs/ai/codex_capability_matrix.md` (§5).

**Root `AGENTS.md` and a reviewed/generated Codex skill catalog are absent** — confirmed (`ls AGENTS.md`, `ls .codex/` both fail). But the legacy `.agents/skills/` tree is **currently auto-discoverable by Codex today**: it physically contains 18 `SKILL.md` files, and per the official Codex manual behavior verified in `docs/ai/codex_capability_matrix.md` (§5), Codex scans `.agents/skills` from cwd up to the repo root — a live Codex session pointed at this repo would find and could load this stale, unapproved content right now. It stays classified exactly per the per-path table above (unchanged by this fix, `archive-retire` or `retain-and-migrate` as listed) and must not be treated as the provider-agnostic workflow source. **No Codex project workflow or pilot is authorized while that legacy tree remains discoverable without an explicit containment decision.** The first Codex-delivery implementation ticket must quarantine/archive the legacy tree, or atomically replace it with the contract-generated catalog, before enabling root `AGENTS.md` or any project Codex configuration. This correction must not be read as "un-archiving" or re-enabling that content as an approved Codex delivery surface — it isn't reviewed or generated from the canonical contract, so it doesn't qualify as one; the correction is a documentation and sequencing fix, not an instruction to delete the legacy tree during discovery.

The `.agents/skills/` entries classified `archive-retire` above remain superseded specifically as **Claude** skill sources (by their `.claude/skills/` equivalents); that comparison was never about Codex. `.agents/rules/engine_contracts.md`'s unique operational content and the 6 unreviewed `.agents/skills/` `retain-and-migrate` dirs are still future-ticket work for the **Claude** surface (`CLAUDE.md` / `.claude/skills/`), not executed as part of landing this doc.

The eventual single semantic authority for both provider surfaces is the shared `agent-orchestration/` contract (repo-root, proposed but not yet built) — see `docs/architecture/agent_orchestration_contract.md`'s "Source Ownership" decision (Status: Decided). This section describes today's delivery surfaces only; it is not a claim that the shared contract already exists. A future, real Codex delivery subtree (root `AGENTS.md` + reviewed `.agents/skills/`) must eventually be generated/reviewed from that shared contract — not produced by simply reclassifying or re-enabling today's stale `.agents/skills/` copies. That generation work is separate, later implementation-epic scope, not part of this fix.

## WorkflowRegistry determination

`WorkflowRegistry` (`src/lab/registry.py:31-111`) is **dead/unwired code today**, not intended future production wiring. Evidence:

1. **Zero production call sites.** `grep -rn "WorkflowRegistry" src/` returns only the class definition and its two `src/lab/__init__.py` export lines. A graphify BFS from `WorkflowRegistry` shows every `imports`/`calls` edge terminating at `tests/unit/lab_agent/test_workflow_registry.py` — none terminate in any other `src/` module.
2. **Neither real consumer references it.** `src/lab/cli.py` (the `rpg-lab` console-script entry point) never references `registry` or `WorkflowRegistry`. `src/lab/workflows.py` (the 8 real workflow classes — `GenerateSimulationSetupWorkflow`, `PrepareSimulationExecutionWorkflow`, `RegisterSimulationResultWorkflow`, `CompactSimulationDataWorkflow`, `InvestigateSimulationResultWorkflow`, `ProposeSimulationEnhancementsWorkflow`, `UpdateSimulationKnowledgeWorkflow`, `RevertSimulationKnowledgeWorkflow`) never references `allowed_actions`, `forbidden_actions`, or `WorkflowRegistry`.
3. **Planned wiring was scoped, then abandoned — not merely never attempted.** `stored_artifacts/TCK-20260524-LAB-GUARDRAILS/plan.md:30` explicitly proposed integrating `WorkflowRegistry`'s dynamic frontmatter loading into the workflow classes. That ticket's delivered `Files Changed` (`src/lab/context.py`, `src/lab/workflows.py`, two new test files) never touches `registry.py`; its guardrail limits are sourced from a plain `limits: dict` parameter instead. This is direct evidence the intended call site was scoped and then dropped in favor of a simpler mechanism.

**This determination is explicitly separated from a second, different question this doc does not decide:** whether `WorkflowRegistry`'s YAML-frontmatter-to-Pydantic parsing pattern is structurally reusable for the parent epic's still-open contract-format decision (`docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md:428-430` — "reviewable YAML, validated Python models, or both"). `WorkflowRegistry`'s parsing pattern is structurally close to that undecided target shape, but reuse is a call for the parent epic's own future scope, not this one.

`WorkflowRegistry` and `WorkflowSkill` are left in place in `src/lab/registry.py`, unmodified, as inert-but-tested utility code. This ticket does not delete them; any future deletion or reuse decision belongs to the parent epic.

## Test-pairing note

`tests/unit/lab_agent/test_workflow_registry.py::test_real_registry_contracts` previously instantiated `WorkflowRegistry` directly against the live `.agents/workflows/` and `.agents/skills/` directories. As part of this ticket, it is repointed at committed fixture snapshots (`tests/unit/lab_agent/fixtures/agents_workflows/generate-simulation-setup.md`, `prepare-simulation-execution.md`, and an empty `tests/unit/lab_agent/fixtures/agents_skills/`) that are byte-identical copies of the two real files the test asserts field-level content against. This means the `archive-retire` classification of `.agents/workflows/*.md` above does not orphan or silently pass the test — the test remains coupled to a frozen snapshot of real Phase 14 contract content rather than to `.agents/`'s eventual fate.

## What this doc does not do

- It does not delete, move, or archive any `.agents/` file. Execution of the `archive-retire` and `retain-and-migrate` classifications above is future-ticket work.
- It does not migrate `.agents/rules/engine_contracts.md`'s unique content into `docs/engine/` or `CLAUDE.md`.
- It does not perform a promotion review of the 6 `retain-and-migrate` `.agents/skills/` dirs.
- It does not implement the Codex adapter, the shared `agent-orchestration/` contract format, or any provider-runtime code — blocked by the parent epic's exit gate (`TCK-20260721-PROVIDER-AGNOSTIC-EPIC`).
- It does not delete or modify `src/lab/registry.py` or `src/lab/__init__.py`.

## Related

- `docs/ai/agent_infrastructure_audit.md` — broader July audit of the `.claude/` orchestration layer, one of the two provider-native delivery surfaces this doc names (see "Approved active location").
- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md` — source proposal that pre-labels `.agents/` as stale and defines the retain-and-migrate/replace/archive-retire classification scheme used above.
- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_finding_01_claude.md` — predecessor finding that first discovered `WorkflowRegistry`'s live dependency on `.agents/` and warned against archiving without updating `test_real_registry_contracts` in the same change.
- `tickets/done/TCK-20260524-WORKFLOW-REGISTRY.md` — built `WorkflowRegistry`/`WorkflowSkill` and populated `.agents/workflows/*.md`.
- `tickets/done/TCK-20260524-LAB-GUARDRAILS.md` — the ticket whose delivered scope is the strongest evidence `WorkflowRegistry`'s intended wiring was dropped.
- `tickets/done/TCK-20260705-SIX-SKILLS-INVESTIGATION.md` — methodological precedent: classification-only investigation, verdict per item, no execution.
