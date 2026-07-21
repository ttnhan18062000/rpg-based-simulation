---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-AGENTS-DIR-DISPOSITION
artifact_type: plan
tags: [ai, workflows, process-improvement]
---

# Implementation Plan — TCK-20260721-AGENTS-DIR-DISPOSITION

## Summary

This ticket is a decision-record/disposition ticket, not a migration ticket. The deliverable is a new durable doc, `docs/ai/agents_dir_disposition.md`, that classifies every top-level `.agents/` path into `retain-and-migrate` / `replace` / `archive-retire` (AC1), names `.claude/` (CLAUDE.md + `.claude/workflows/*.js` + `.claude/skills/` + `.claude/agents/*.md`) as the one approved active Codex/Claude instruction-and-skill location with `.agents/` fully superseded except two named carve-outs (AC2), and makes the reasoned determination that `WorkflowRegistry` (`src/lab/registry.py`) is dead/unwired code today — not intended future production wiring — while explicitly not deciding whether its parsing pattern gets reused by the parent epic's still-open contract-format question (AC3). Paired with the doc, `tests/unit/lab_agent/test_workflow_registry.py::test_real_registry_contracts` is decoupled from the live (soon-to-be-archived) `.agents/workflows/` directory by repointing it at two new committed test fixture files that snapshot the exact current content — this keeps the test green with its field-level assertions intact and non-dependent on `.agents/`'s eventual fate (AC4). No `.agents/` file is deleted, moved, or edited; no `.claude/workflows/*.js`, `.claude/agents/*.md`, `.claude/skills/*`, or `CLAUDE.md` is touched; `src/lab/registry.py` itself is not modified — only its test's fixture inputs change.

## Steps

### Step 1 — Confirm baseline before making any change
**Files:** none (verification only)
**Change:** Run `.venv/bin/python3 -m pytest tests/unit/lab_agent/ -v` and `.venv/bin/python3 -m pytest tests/integration/lab_agent/ -v` to confirm the investigation's baseline (`test_workflow_registry.py` 4/4 passing, all other `lab_agent` tests green) still holds with zero drift since the investigation ran. If anything differs from investigation.md's reported baseline, stop and re-flag before proceeding — do not build the disposition doc or test change on a stale assumption.
**Do NOT touch:** Any file. This step is read-only verification.
**Verify:** `tests/unit/lab_agent/` → 4/4 in `test_workflow_registry.py`, all pass in sibling files; `tests/integration/lab_agent/` → all pass.

### Step 2 — Write the disposition report
**Files:** `docs/ai/agents_dir_disposition.md` (new file)
**Change:** Create a new doc, following the frontmatter/heading style of `docs/ai/agent_infrastructure_audit.md` (frontmatter: `status: active`, `layer: ai`, `authority: P1`, `audience: developer`, `tags:` — check `python3 tools/tag_registry.py list` first and reuse already-registered tags such as `audit`, `agent-infrastructure`; do not invent new tags without registering them per CLAUDE.md's tag-registry rule). Content must include, at minimum:

1. **Per-path classification table (AC1)**, one row per top-level `.agents/` path, at subdirectory granularity where content diverges:
   - `.agents/task.md` → **archive-retire** (0 bytes, no content to lose).
   - `.agents/rules/AGENTS.md`, `workflow.md`, `ticket.md`, `testing.md`, `architecture.md`, `authoritative_mechanics.md`, `done.md`, `graphify.md` (8 files) → **archive-retire**. Each is a near-verbatim earlier draft of a `CLAUDE.md` section, now materially extended there (tag/layer registries, `docs/REGISTRY.yaml`, `agent-monitoring/`, tier routing — none present in the `.agents/rules/*` versions). `authoritative_mechanics.md:18`'s "17-phase apply sequence" is a concrete factual drift against the current 32-phase `docs/engine/authoritative_pipeline.md` — this file is actively wrong, not just old, and must not be cited as a reference.
   - `.agents/rules/engine_contracts.md` (224 lines) → **retain-and-migrate**. Not a strict subset of `CLAUDE.md` — it holds prescriptive per-subsystem "when X changes, update doc Y and parity ledger Z" operational detail that `CLAUDE.md`'s current Engine Contracts section (summary table only) lacks. Record explicitly: this content needs a home (candidate: fold into `docs/engine/` or expand `CLAUDE.md`'s Engine Contracts section) in a **future ticket** — this ticket does not perform that migration.
   - `.agents/skills/{api-design-principles, architecture, backend-testing, brainstorming, debugging-strategies, doc-coauthoring, frontend-design, prompt-builder, python-performance-optimization, python-testing-patterns, test-driven-development}` (11 dirs) → **archive-retire**. Superseded by the same-named entries in `.claude/skills/`. One pair (`api-design-principles`) was byte-diffed identical; record that the remaining 10 pairs were not individually diffed and note a follow-up hygiene spot-check as a future (non-blocking) task — do not claim full byte-verification you don't have.
   - `.agents/skills/graphify` → **archive-retire**, with the specific note that its replacement is the **user-level global** skill (`~/.claude/skills/graphify/SKILL.md`), not a `.claude/skills/` project-scope entry — a different tier, not a migration target.
   - `.agents/skills/{clean-code, codebase-search, code-review, create-skill, receiving-code-review, requesting-code-review}` (6 dirs) → **retain-and-migrate**. No `.claude/skills/` equivalent exists and no test asserts their content, so nothing supersedes them yet; record them as candidates for a future promotion-review ticket rather than archiving unique, unreviewed content by default.
   - `.agents/workflows/*.md` (8 files) → **archive-retire**. Confirmed declarative-only contracts never enforced by `.claude/workflows/*.js` at runtime (grep found zero references to `allowed_actions`/`forbidden_actions`/`.agents`/`WorkflowRegistry` in the real orchestration JS). Their only current consumer, `WorkflowRegistry`, is being decoupled from them in Step 4 below, removing the last reason to keep them live.

2. **Approved active location (AC2):** state explicitly that `.claude/` is the one approved active Codex/Claude instruction-and-skill location — rules in `CLAUDE.md`, orchestration in `.claude/workflows/*.js`, skills in `.claude/skills/`, agent role definitions in `.claude/agents/*.md`. `.agents/` is **fully superseded**, not retained as that location, except the two explicitly named retain-and-migrate carve-outs above (`engine_contracts.md`'s unique content, the 6 unreviewed skill dirs) — both flagged for future tickets, not executed here.

3. **WorkflowRegistry determination (AC3):** state the determination plainly: `WorkflowRegistry` (`src/lab/registry.py:31-111`) is **dead/unwired code today**, not intended future production wiring, based on (a) zero production call sites confirmed by grep and graphify BFS, (b) `src/lab/cli.py` and `src/lab/workflows.py` never referencing it, and (c) `TCK-20260524-LAB-GUARDRAILS`'s own plan explicitly proposing to wire it in, then shipping a plain-dict `limits` parameter instead — direct evidence the intended call site was scoped and dropped, not merely never attempted. Explicitly separate this from a second, *not*-decided-here question: whether `WorkflowRegistry`'s YAML-frontmatter-to-Pydantic parsing pattern is structurally reusable for the parent epic's still-open contract-format decision (`idea_provider_agnostic_agent_orchestration.md:428-430`). Record that the class is left in place in `src/lab/registry.py`, unmodified, as inert-but-tested utility code — this ticket does not delete it, and any future deletion or reuse decision belongs to the parent epic's own scope, not this one.

4. **Test-pairing note (AC4 cross-reference):** state that `test_real_registry_contracts` is repointed at committed fixtures rather than the live `.agents/workflows/` directory (see Steps 3–4), so the `archive-retire` classification of `.agents/workflows/*.md` above does not orphan or silently pass the test.

**Do NOT touch:** Any `.agents/` file, any `.claude/workflows/*.js`, `.claude/agents/*.md`, `.claude/skills/*`, or `CLAUDE.md`. This step only writes the new decision-record doc.
**Verify:** Manual review — the doc contains one unambiguous verdict per top-level `.agents/` path (all four required buckets covered: `.agents/task.md`, `.agents/rules/*`, `.agents/skills/*`, `.agents/workflows/*`), names exactly one approved active location, and states the `WorkflowRegistry` determination without hedging. This step has no executable test; it satisfies AC1–AC3 as a documentation artifact per the `TCK-20260705-SIX-SKILLS-INVESTIGATION` precedent (classification-only ticket, verdict in prose, no code).

### Step 3 — Add committed fixture snapshots for the two asserted workflow contracts
**Files:** `tests/unit/lab_agent/fixtures/agents_workflows/generate-simulation-setup.md` (new), `tests/unit/lab_agent/fixtures/agents_workflows/prepare-simulation-execution.md` (new), `tests/unit/lab_agent/fixtures/agents_skills/` (new, empty directory — needs to exist so `WorkflowRegistry(workflows_dir, skills_dir)` can construct against a valid `skills_dir`; no skill file content is asserted by `test_real_registry_contracts`, so an empty dir is sufficient)
**Change:** Copy the exact current byte content of `.agents/workflows/generate-simulation-setup.md` and `.agents/workflows/prepare-simulation-execution.md` verbatim into the two new fixture files. This is a snapshot, not a rewrite — the frontmatter fields the test asserts (`allowed_actions`, `forbidden_actions` for both workflows) must be byte-identical to what Step 1's baseline run already exercised. Use `cp` or `Read`+`Write` to guarantee an exact copy — do not retype content by hand.
**Do NOT touch:** `.agents/workflows/generate-simulation-setup.md` or `.agents/workflows/prepare-simulation-execution.md` themselves — copy from them, never edit them. Do not create fixtures for any other `.agents/workflows/*.md` file; only the two files `test_real_registry_contracts` actually asserts against are needed.
**Verify:** `diff .agents/workflows/generate-simulation-setup.md tests/unit/lab_agent/fixtures/agents_workflows/generate-simulation-setup.md` and the equivalent for `prepare-simulation-execution.md` both produce no output (exact copies).

### Step 4 — Repoint `test_real_registry_contracts` at the new fixtures
**Files:** `tests/unit/lab_agent/test_workflow_registry.py` (lines 92–117)
**Change:** In `test_real_registry_contracts`, change `workflows_dir`/`skills_dir` construction (currently `project_root / ".agents" / "workflows"` and `project_root / ".agents" / "skills"`, lines 94–96) to point at `Path(__file__).resolve().parent / "fixtures" / "agents_workflows"` and `Path(__file__).resolve().parent / "fixtures" / "agents_skills"` respectively. Keep every field-level assertion (lines 103–104, 108–109, 113–117) byte-for-byte unchanged — they must still pass against the fixture content copied in Step 3. Add a one-line comment or update the docstring immediately above the function citing this ticket ID and explaining the rationale (e.g. `"""Verify workflow contract parsing against a frozen snapshot of the real Phase 14 contracts — decoupled from live .agents/ per TCK-20260721-AGENTS-DIR-DISPOSITION, which classifies .agents/workflows/ as archive-retire."""`). Do not rename the test function — it remains part of the same 4-test suite structure.
**Do NOT touch:** `test_scan_and_register_success`, `test_workflow_fields_validation`, `test_unknown_workflow_rejected` (they already use `tmp_path` fixtures and have no dependency on `.agents/`) or any other file in `tests/unit/lab_agent/` or `tests/integration/lab_agent/`. Do not touch `src/lab/registry.py` or `src/lab/__init__.py` — `WorkflowRegistry`/`WorkflowSkill` stay exported unchanged; only the test's input paths move.
**Verify:** `.venv/bin/python3 -m pytest tests/unit/lab_agent/test_workflow_registry.py -v` → 4 passed, with `test_real_registry_contracts` now reading from the fixture paths (confirm via `-v` output or a temporary `print`/assert on the resolved path during a dry run, then remove any debug print before finalizing).

### Step 5 — Full scoped regression pass
**Files:** none (verification only)
**Change:** Run the full scoped command set from `test_plan.md`:
```
.venv/bin/python3 -m pytest tests/unit/lab_agent/ -v
.venv/bin/python3 -m pytest tests/integration/lab_agent/ -v
.venv/bin/python3 -c "import src.lab"
.venv/bin/python3 -c "import src.lab.cli"
```
All four must succeed. The import checks are cheap defensive guards confirming that `src/lab/__init__.py`'s export surface (`WorkflowRegistry`, `WorkflowSkill`) is untouched and `src/lab/cli.py` still imports cleanly, even though this ticket does not modify either file.
**Do NOT touch:** Nothing new here — pure verification. If any test outside `test_workflow_registry.py` changes behavior, that is scope creep — stop and investigate rather than editing further files to "fix" it.
**Verify:** All four commands exit 0. `git status` afterward shows changes confined to: `docs/ai/agents_dir_disposition.md` (new), `tests/unit/lab_agent/fixtures/agents_workflows/*.md` (new, 2 files), `tests/unit/lab_agent/fixtures/agents_skills/` (new, empty dir — note git does not track empty dirs; add a `.gitkeep` placeholder if the empty dir must be committed), `tests/unit/lab_agent/test_workflow_registry.py` (modified), plus this ticket's own artifacts (`tickets/inprogress/TCK-20260721-AGENTS-DIR-DISPOSITION.md`, `staging_artifacts/TCK-20260721-AGENTS-DIR-DISPOSITION/*`). Nothing under `.agents/`, `.claude/`, `CLAUDE.md`, `tools/agent-monitoring/`, or `agent-monitoring/*.jsonl` should appear.

### Step 6 — Update the ticket body with the decision and results
**Files:** `tickets/inprogress/TCK-20260721-AGENTS-DIR-DISPOSITION.md`
**Change:** Fill in `## Implementation Notes` (summarize the classification outcome and the fixture-decoupling approach), `## Test Summary` (paste the Step 5 pass counts), `## Files Changed` (the exact file list from Step 5's `git status` check), and `## Completion Summary`. Check all four `## Acceptance Criteria` boxes, since Steps 2–5 satisfy them. Do not alter `## Scope`, `## Out of Scope`, or `## Related Tickets` — those are fixed at ticket-creation time.
**Do NOT touch:** Frontmatter fields other than what closure conventions require (this step is body-content only).
**Verify:** All four AC checkboxes ticked with content that matches what Steps 2–5 actually produced (no aspirational claims).

## Scope Guards

- Do not delete, move, or edit any file physically under `.agents/` (all 42 files, all 4 top-level paths). This ticket documents the disposition; it does not execute the migration.
- Do not modify `.claude/workflows/*.js`, `.claude/agents/*.md`, `.claude/skills/*`, or `CLAUDE.md`.
- Do not modify `src/lab/registry.py` or `src/lab/__init__.py` — `WorkflowRegistry`/`WorkflowSkill` remain exported and unmodified; only `test_real_registry_contracts`'s input paths change.
- Do not modify any `tests/unit/lab_agent/` file other than `test_workflow_registry.py`, and only the one function (`test_real_registry_contracts`) within it.
- Do not modify any `tests/integration/lab_agent/*.py` file.
- Do not touch `tools/agent-monitoring/*` or `agent-monitoring/*.jsonl` beyond whatever the standard ticket-workflow run/event entries require (governed by the workflow harness, not this plan).
- Do not implement the Codex adapter, the shared `agent-orchestration/` contract format, or any provider-runtime code — blocked by the parent epic's exit gate (`TCK-20260721-PROVIDER-AGNOSTIC-EPIC`).
- Do not perform the actual migration of `.agents/rules/engine_contracts.md` content into `docs/engine/`, nor the promotion-review of the 6 untested `.agents/skills/` dirs — both are named `retain-and-migrate` in the disposition doc as future-ticket work, not executed here.
- Do not touch sibling in-flight tickets' domains (`TCK-20260721-CODEX-CAPABILITY-MATRIX`, `TCK-20260721-MONITORING-WRITER-DECISION`).

## Dependency Map

- Step 1 has no dependencies; run first to establish a clean baseline.
- Step 2 (disposition doc) has no code dependency on Steps 3–5 — it can be written in parallel with them, but logically precedes them since Steps 3–4 implement the consequence of Step 2's `.agents/workflows/` = archive-retire classification. Write Step 2 first for narrative consistency.
- Step 3 (fixture files) must complete before Step 4 (test repoint), since Step 4's assertions depend on the fixture content existing and being byte-identical to the source.
- Step 4 must complete before Step 5 (regression pass needs the updated test in place).
- Step 5 must complete before Step 6 (ticket closure documents actual verified results, not planned ones).
- Steps 1–6 are otherwise fully sequential and independently verifiable; no step needs to be revisited once its own Verify condition passes.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — classify every top-level `.agents/` path into retain-and-migrate/replace/archive-retire, at subdirectory granularity | Step 2 | Manual doc review (no executable test; documentation deliverable) |
| AC2 — name exactly one approved active Codex instruction/skill location; state `.agents/`'s status relative to it | Step 2 | Manual doc review |
| AC3 — determine and document whether `WorkflowRegistry` is intended future production wiring or dead/unwired code | Step 2 | Manual doc review |
| AC4 — `tests/unit/lab_agent/test_workflow_registry.py` passes (real-path intact / updated paths / explicit retirement), never left red or silently orphaned | Steps 3, 4, 5 | `.venv/bin/python3 -m pytest tests/unit/lab_agent/test_workflow_registry.py -v` → 4 passed; `tests/unit/lab_agent/` and `tests/integration/lab_agent/` full scoped runs green |

## Anti-Drift Notes

- **Do not conflate the two archive-retire classifications with a green light to delete `.agents/` in this ticket.** The disposition doc records the decision; execution (actual deletion/archival of `.agents/` files) is out of scope and belongs to a future migration ticket that this doc's classification unblocks.
- **`test_real_registry_contracts`'s fixture content must be an exact copy, not a re-authored approximation.** The test's assertions are keyed to specific `allowed_actions`/`forbidden_actions` string values (`resolve_specs`, `execute_simulation_command`, `run_simulation_directly`, `create_draft_specs`, `run_simulation`, `promote_trusted_specs`, `update_rulebooks_directly`) — copy-paste or `cp`, never retype.
- **Do not let "WorkflowRegistry has zero callers" collapse into "delete the class."** AC3 only requires documenting the wiring-status determination; deleting `src/lab/registry.py` or its `__init__.py` export is a larger, separate call this ticket does not make (and test_plan.md's regression surface explicitly treats `src/lab/__init__.py`'s export list as something that must still resolve cleanly).
- **`.agents/rules/engine_contracts.md` and the 6 untested `.agents/skills/` dirs are `retain-and-migrate`, not `archive-retire`.** Do not let the "'.agents/ is stale scaffolding" framing from the ticket's Request Summary sweep these two carve-outs into blanket archival in the disposition doc — the investigation found concrete unique content/no-superseding-equivalent for both.
- **`.agents/skills/graphify` is superseded by a user-global skill, not a `.claude/skills/` entry.** Do not write it up as "needs migration into `.claude/skills/`" in the disposition doc.
- **Empty git-tracked directories:** `tests/unit/lab_agent/fixtures/agents_skills/` will not be tracked by git if left empty — add a `.gitkeep` (or equivalent placeholder) if Step 5's `git status` check requires the directory to actually persist in the commit.

## Deviations

- **Step 2 tags:** the plan's Step 2 suggested reusing tags "such as `audit`, `agent-infrastructure`" from `docs/ai/agent_infrastructure_audit.md`'s frontmatter. Checked `python3 tools/tag_registry.py list` before writing the doc and found neither tag is actually registered — `docs/ai/agent_infrastructure_audit.md` is dated 2026-07-03, before the 2026-07-04 tag-registry validation cutoff, so its tags were never checked against the registry. Used `[ai, workflows, process-improvement, lab-agent, documentation]` instead — all five confirmed present in `python3 tools/tag_registry.py list` output, matching the ticket's own already-registered tags plus two additional exact matches for this doc's subject matter. No other deviation from the plan; all six steps executed as specified.
