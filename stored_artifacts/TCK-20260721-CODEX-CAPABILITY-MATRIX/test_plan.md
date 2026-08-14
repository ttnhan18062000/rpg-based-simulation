---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CODEX-CAPABILITY-MATRIX
artifact_type: test_plan
tags: [ai, workflows, process-improvement]
---

# Test Plan — TCK-20260721-CODEX-CAPABILITY-MATRIX

## Regression Surface

This ticket's deliverable is a documentation/decision-record artifact (a Codex capability matrix, likely `docs/ai/codex_capability_matrix.md` or similar — see investigation.md's open question on placement) plus, if AC3's fixture experiment is executed in Plan/Implement, isolated fixture files outside this repo's `.codex/` trust boundary. It must not touch `src/engine/capability.py`, `.claude/settings.json`, `.claude/workflows/*.js`, or `tools/agent-monitoring/*`. Given that, the regression surface is deliberately narrow — these are the tests that prove nothing this ticket touches (or could plausibly be touched by mistake, given the "Related Code Areas" name collision noted in investigation.md) regressed:

**Unit — engine capability registry (must stay green; confirms this ticket did not accidentally touch the coincidentally-named sim-engine registry):**
- `tests/unit/engine/test_capability_registry.py` — all 10 tests (`test_capability_registry_yaml_exists`, `test_capability_registry_is_valid_yaml`, `test_all_registry_entries_have_required_fields`, `test_all_registry_statuses_are_valid`, `test_registry_has_minimum_entries`, `test_capability_reader_is_supported`, `test_capability_reader_is_unsupported`, `test_capability_reader_get_status`, `test_capability_reader_unknown_id`)

**Architecture guard:**
- `tests/architecture/test_capability_references.py::test_capability_ids_are_unique`

**Unit/integration — Lab agent workflow-registry family (adjacent `.agents/`-related area; confirms this ticket does not silently re-touch what the just-completed sibling `TCK-20260721-AGENTS-DIR-DISPOSITION` already decided and closed):**
- `tests/unit/lab_agent/` (33 tests per that sibling ticket's closure baseline, includes `test_workflow_registry.py`, `test_agent_guardrails.py`, `test_approval_gate.py`, `test_workflow_request_model.py`, `test_context_pack_builder.py`, `test_audit_trail.py`)
- `tests/integration/lab_agent/` (62 tests per that sibling ticket's closure baseline)

**Tooling — Claude-side hook scripts (must stay untouched/green; confirms this ticket's Codex-hook *investigation* did not bleed into modifying the repo's actual, unrelated Claude PreToolUse/PostToolUse wiring):**
- `tests/tools/test_post_tool_hook.py`

## New Tests Required

Per AC1-AC4, this ticket's primary deliverable is a documentation artifact, not executable behavior — most acceptance criteria are satisfied by the matrix doc's content and citations, not by new pytest tests. One new test is warranted if the Plan/Implement phase executes a fixture experiment (per AC3 and investigation.md's "Live-environment fixture-experiment feasibility" finding that `codex` CLI is installed and `codex features list` already confirms `hooks: stable, true`):

- **Test name:** `test_codex_hooks_feature_reported_enabled` (or equivalent)
  - **Category:** diagnostic / fixture-experiment guard (not a simulation-domain unit/integration test — this is process-tooling verification, so it should live outside `tests/unit`/`tests/integration`'s simulation-domain tree, mirroring how `tests/tools/test_post_tool_hook.py` already sits outside those trees for a similar reason)
  - **What it verifies:** that running `codex features list` (or `codex features list --json` if available) on the environment's installed Codex CLI reports the `hooks` feature as present with a truthy/`stable` state — i.e., codifies the direct-experiment evidence this investigation gathered manually, so it can be re-run instead of re-discovered by hand in a future session. Should skip (not fail) if `codex` is not on `PATH`, since CLI presence is an environment fact, not a repo invariant this ticket can guarantee across all future environments.
  - **Where it should live:** `tests/tools/test_codex_capability_diagnostics.py` (new file, sibling to `test_post_tool_hook.py`), OR, if the matrix artifact ships a small reader module analogous to `src/engine/capability.py` for the Codex matrix (a Plan-phase decision, not resolved here), a corresponding `tests/unit/.../test_codex_capability_matrix.py`.
  - **Note:** this test necessarily depends on an external binary (`codex`) and its installed version/feature flags — it is inherently more fragile than a pure in-repo unit test and should be marked/skippable accordingly (e.g. `pytest.importorskip`-style `shutil.which("codex")` guard), consistent with the containment rule's "diagnostic" allowance and with not making CI depend on a third-party product being installed.

- **Optional second test, only if Plan/Implement executes the full stdin-payload fixture experiment recommended in investigation.md's Risks section:**
  - **Test name:** `test_codex_pretooluse_payload_matches_documented_schema`
  - **Category:** fixture / contract-conformance guard
  - **What it verifies:** that a captured real `PreToolUse` hook invocation's `stdin` JSON contains the documented common-input fields (`session_id`, `cwd`, `hook_event_name`, `model`, `permission_mode`, `turn_id`) — turning the one-off fixture experiment into a durable, re-runnable regression check against a **committed** fixture (the captured payload JSON, redacted of any session-specific secrets), not a live re-invocation of `codex` in CI.
  - **Where it should live:** `tests/tools/fixtures/codex_hooks/pretooluse_sample.json` (fixture) + `tests/tools/test_codex_hook_payload_contract.py` (test).
  - **Explicitly deferred:** this is scoped for Plan/Implement to decide whether to pursue; not required to close this Investigate phase.

## Scoped Pytest Commands

```bash
# Regression surface — coincidentally-named sim-engine capability registry
.venv/bin/python3 -m pytest tests/unit/engine/test_capability_registry.py tests/architecture/test_capability_references.py -v

# Regression surface — adjacent Lab agent / .agents workflow-registry family
.venv/bin/python3 -m pytest tests/unit/lab_agent/ tests/integration/lab_agent/ -v

# Regression surface — Claude-side PostToolUse hook script (must remain untouched/green)
.venv/bin/python3 -m pytest tests/tools/test_post_tool_hook.py -v

# New diagnostic test, once added (Plan/Implement)
.venv/bin/python3 -m pytest tests/tools/test_codex_capability_diagnostics.py -v
```

Never run `pytest tests/` for this ticket — the change surface is a documentation artifact plus, at most, one or two new diagnostic/fixture tests; the above scoped commands cover every file this ticket could plausibly touch or accidentally regress.

## Anti-Drift Test Guards

- `tests/unit/engine/test_capability_registry.py` and `tests/architecture/test_capability_references.py` passing unchanged is itself the guard against the "Related Code Areas name collision" hazard flagged in investigation.md — if this ticket's work ever causes these to need updating, that is a signal the work has drifted into the wrong (unrelated) `capability.py`/`capability_registry.yaml` system.
- `tests/unit/lab_agent/` + `tests/integration/lab_agent/` passing at the same 33+62 counts recorded in the just-closed sibling `TCK-20260721-AGENTS-DIR-DISPOSITION`'s Test Summary is the guard against this ticket silently re-opening or perturbing that sibling's already-closed `.agents/`/`WorkflowRegistry` disposition work — this ticket has no dependency on that sibling and must not touch its files.
- `tests/tools/test_post_tool_hook.py` passing unchanged is the guard against Codex-hook investigation/verification work bleeding into an edit of this repo's actual live Claude `PreToolUse`/`PostToolUse` hook scripts (`tools/agent-monitoring/post_tool_hook.py` et al.) — those are explicitly out of scope per the containment rule and owned by the separate `TCK-20260721-MONITORING-WRITER-DECISION` child.
- If a fixture experiment is added (optional test above), it must assert against a **committed, redacted** fixture file, not a live `codex exec` invocation inside the test — a test that shells out to a real, authenticated third-party CLI on every CI run would be nondeterministic, slow, and a monitoring/cost risk; this guards against that anti-pattern being introduced later.
- No test in this plan should assert on the *content* of the matrix doc itself beyond existence/parseability if a machine-readable format is chosen (Plan-phase decision) — the matrix's accuracy is a documentation-review concern (citations, dates, VERIFIED/UNVERIFIED marks), not something a pytest assertion can meaningfully validate.
