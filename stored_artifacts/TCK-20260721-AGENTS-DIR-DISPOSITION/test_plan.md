---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-AGENTS-DIR-DISPOSITION
artifact_type: test_plan
tags: [ai, workflows, process-improvement]
---

# Test Plan — TCK-20260721-AGENTS-DIR-DISPOSITION

## Regression Surface

This is an audit/disposition ticket producing a decision-record deliverable, plus whatever minimal fixture/test change AC4 requires on `test_workflow_registry.py`. The regression surface is deliberately narrow — no simulation engine, mechanics, or Claude/Codex production workflow code is touched.

**Unit — `src/lab` registry/workflow package (must keep passing exactly, or be explicitly and deliberately updated per the chosen disposition):**
- `tests/unit/lab_agent/test_workflow_registry.py` — 4 tests (`test_scan_and_register_success`, `test_workflow_fields_validation`, `test_unknown_workflow_rejected`, `test_real_registry_contracts`). Verified passing today via direct run (`.venv/bin/python3 -m pytest tests/unit/lab_agent/test_workflow_registry.py -v` → 4 passed). This file — specifically `test_real_registry_contracts` — is the AC4 target: it must end the ticket passing with real-path assertions intact, updated paths/assertions, or explicit documented retirement, never red or silently orphaned.
- `tests/unit/lab_agent/test_agent_guardrails.py`, `test_approval_gate.py`, `test_audit_trail.py`, `test_context_pack_builder.py`, `test_workflow_request_model.py` — sibling tests in the same package; confirmed none import `WorkflowRegistry` or depend on `.agents/` paths (only `test_workflow_registry.py` does), so they are pure regression guards that nothing in this ticket's likely change surface should affect.

**Integration — `src/lab` E2E (must keep passing, confirms no accidental `src/lab/__init__.py` or `registry.py` breakage cascades):**
- `tests/integration/lab_agent/*.py` (9 files, e.g. `test_human_gated_agentic_lab_e2e.py`, `test_generate_simulation_setup_workflow.py`, `test_prepare_simulation_execution_workflow.py`) — none reference `WorkflowRegistry` or `.agents/`, but they do exercise the same `src/lab/__init__.py` export surface; a low-cost confirmation that removing/changing the `WorkflowRegistry`/`WorkflowSkill` export (if that's the eventual disposition) doesn't break unrelated imports.

**No other domain** (combat, economy, strategy, world, engine kernel, dashboard, monitoring) is in the regression surface for this ticket — confirmed via the containment constraint and via grep showing zero cross-references from `.agents/`, `WorkflowRegistry`, or `src/lab/registry.py` into any other subsystem.

## New Tests Required

Per acceptance criteria, exactly one test-shaped deliverable is required (AC4); the other three ACs (audit classification, active-location determination, WorkflowRegistry disposition) are decision-record/documentation outputs, not new test code.

1. **Whatever change `test_real_registry_contracts` needs to reflect the chosen disposition** (exact shape depends on which of the three disposition outcomes the implementation lands on — not pre-decided by this investigation, per the ticket's own framing):
   - **If `.agents/workflows/`/`.agents/skills/` are retained as-is:** no test change needed; keep the test as a real-path regression guard exactly as it is today.
   - **If `.agents/workflows/`/`.agents/skills/` content is migrated to a new canonical location:** update `test_real_registry_contracts`'s `workflows_dir`/`skills_dir` construction (test_workflow_registry.py:94-96) to point at the new location, and keep its field-level assertions (lines 103-104, 108-109, 113-117) valid against the migrated content.
   - **If `WorkflowRegistry` itself is retired as dead code:** replace `test_real_registry_contracts` with an explicit retirement marker (e.g. `pytest.skip("WorkflowRegistry retired — see TCK-20260721-AGENTS-DIR-DISPOSITION")` or delete the test with a Files-Changed note), and keep `test_scan_and_register_success`/`test_workflow_fields_validation`/`test_unknown_workflow_rejected` (which use `tmp_path` fixtures, not real `.agents/` paths) passing as pure unit coverage of the still-present `WorkflowSkill`/`WorkflowRegistry` classes, or remove them too if the classes are deleted outright.
   - Category: unit. Verifies: AC4's "never left red or silently orphaned" requirement.
   - Location: `tests/unit/lab_agent/test_workflow_registry.py` (in place — no new file).

No other new test is required by this ticket's acceptance criteria — the classification and location-determination ACs are prose/decision-record outputs, not executable assertions, consistent with the `TCK-20260705-SIX-SKILLS-INVESTIGATION` precedent (classification-only ticket, zero new test files, verdict expressed in `investigation.md`/ticket body).

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/lab_agent/ -v
.venv/bin/python3 -m pytest tests/integration/lab_agent/ -v
```

Never `pytest tests/` — scoped to the `lab_agent` unit and integration domains only, the sole area this ticket's Related Code Areas and containment rule touch.

If the implementation also edits `src/lab/__init__.py` (e.g. removing the `WorkflowRegistry`/`WorkflowSkill` export), additionally run a broad-but-cheap import sanity check before the full lab suite:

```
.venv/bin/python3 -c "import src.lab"
```

## Anti-Drift Test Guards

- **`test_real_registry_contracts` must not silently start passing against a fixture that no longer represents real repo content.** If the disposition migrates `.agents/workflows/*.md` content elsewhere, the test's assertions (`resolve_specs`/`execute_simulation_command`/`run_simulation_directly` for `PrepareSimulationExecution`; `create_draft_specs`/`run_simulation`/`promote_trusted_specs`/`update_rulebooks_directly` for `GenerateSimulationSetup`) must be re-verified against the migrated file content, not just re-pointed at a new path with unchecked assertions.
- **A green `tests/unit/lab_agent/` run after this ticket must not be achieved by deleting or skipping tests without a documented reason.** Any `pytest.skip`/removal on `test_real_registry_contracts` must cite this ticket ID and the specific disposition decision, per AC4's "explicit documented test retirement" wording — a bare skip with no reason string fails the spirit of the AC even if pytest reports green.
- **No other `tests/unit/lab_agent/` or `tests/integration/lab_agent/` file should change.** If implementation touches any file in that surface beyond `test_workflow_registry.py`, that is scope creep beyond this ticket's Related Code Areas and the containment rule — flag it rather than silently including it.
- **`src/lab/cli.py` must still import and run cleanly** if `src/lab/__init__.py`'s export list changes — confirms no CLI entry-point regression from touching the `WorkflowRegistry` export, even though `cli.py` never used it (`.venv/bin/python3 -c "import src.lab.cli"` is a cheap guard).
- **No file outside `.agents/`, `src/lab/registry.py`, `src/lab/__init__.py`, `tests/unit/lab_agent/test_workflow_registry.py`, and this ticket's own artifacts should appear in `git status`** after implementation — a guard against accidentally touching `.claude/`, `CLAUDE.md`, `tools/agent-monitoring/`, or `agent-monitoring/*.jsonl`, all explicitly barred by the containment rule.
