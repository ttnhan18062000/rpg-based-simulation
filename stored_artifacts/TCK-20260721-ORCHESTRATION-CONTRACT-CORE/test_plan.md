---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-ORCHESTRATION-CONTRACT-CORE
artifact_type: test_plan
tags: [ai, workflows, process-improvement]
---

# Test Plan — TCK-20260721-ORCHESTRATION-CONTRACT-CORE

## Regression Surface

This ticket adds a new `agent-orchestration/` data directory and a new validator/generator tool
tree; it must not touch any live provider file. The regression surface is therefore about proving
non-interference, not about re-running unrelated suites wholesale.

**Unit**
- `tests/tools/test_validate_agent_monitoring.py` — full file must stay green, unmodified. In
  particular `test_canonical_vocabulary_single_sourced` (`:188-193`) asserts
  `record_events.WORKFLOW_PHASES is validate.WORKFLOW_PHASES` and
  `record_events.infer_workflow is validate.infer_workflow` — an identity check on the *existing*
  legacy single-source wiring. This ticket's new bootstrap-equality test (see below) is a sibling,
  not a replacement, and must not alter `tools/agent-monitoring/vocabulary.py`,
  `tools/agent-monitoring/record_events.py`, or `tools/agent-monitoring/validate.py` in any way that
  would change this test's outcome. Run this file before and after implementation and diff results.
- `tests/tools/test_agent_monitoring_legacy_reader.py` — flagged by the task brief as
  potentially import-pattern-adjacent (may import from `tools/agent-monitoring/`); confirm it
  still passes and that nothing in this ticket's new code shadows or monkeypatches
  `sys.path` entries it relies on (`_MONITORING_TOOLS_DIR` insertion pattern used by
  `test_validate_agent_monitoring.py:9-14`).
- `tests/tools/test_codex_capability_diagnostics.py` — recently added (untracked in working tree
  per repo status), reads `.claude`/`.codex` capability surfaces; confirm this ticket's new
  `agent-orchestration/` directory does not collide with any path it globs.

**Integration**
- `tests/agent_replay/` (full directory: `test_runner_no_forbidden_calls.py`,
  `test_no_mutation_snapshot.py`, and siblings) — this ticket's validator/generator explicitly
  reuses `tools/agent_replay/fixture_envelope.py`'s `FixtureValidationError` pattern and
  `test_runner_no_forbidden_calls.py`'s AST-scan pattern as templates; it must not import from or
  modify `tools/agent_replay/` itself. Confirm the existing suite is unaffected (no shared mutable
  state, no path collisions under `tests/fixtures/agent_replay/`).

**Static/manual confirmation (not a pytest run, but must be checked before claiming completion)**
- `git diff` (or `git status`) after implementation must show `tools/agent-monitoring/vocabulary.py`,
  `.claude/workflows/implement-ticket.js`, and `tools/agent-monitoring/validate.py` as **untouched**
  — this is a hard Out-of-Scope/Anti-Drift requirement from both the ticket and the investigation,
  not something a pytest assertion alone can guarantee, so it must be checked explicitly as part of
  verification.

## New Tests Required

Per the ticket's Acceptance Criteria (`tickets/inprogress/TCK-20260721-ORCHESTRATION-CONTRACT-CORE.md:49-56`):

1. **`test_agent_orchestration_dir_has_required_files`**
   - Category: integration (filesystem-structure check)
   - Verifies: `agent-orchestration/contract.yaml`, `agent-orchestration/workflows/implement-ticket.yaml`,
     `agent-orchestration/roles/*.yaml` (at least the 9 real subagents plus `finalizer`, per the
     investigation's role inventory — 10 files, not 11: `implement-ticket-orchestrator` must be
     absent), `agent-orchestration/skills.yaml`, `agent-orchestration/monitoring-schema.yaml`,
     `agent-orchestration/hook-events.yaml` all exist and parse as valid YAML (not just exist as
     files — `yaml.safe_load` must not raise).
   - Location: `tests/agent_orchestration/test_contract_structure.py`

2. **`test_workflow_covers_both_tiers`**
   - Category: unit
   - Verifies: `workflows/implement-ticket.yaml` encodes a per-phase tier-applicability field (e.g.
     `tiers: [...]`) for all 11 phases, and that the hotfix-tier subset matches
     `implement-ticket.js`'s real branch structure as documented in investigation.md's Current
     Behavior section — Investigate/Plan/Review/Architecture-Verify present-but-`skipped`-eligible
     for hotfix, Security-Review and Parity conditionally present, remaining phases (Scope, Implement,
     Test, Verify, Finalize) present for both tiers. This is new modeling work (no existing source),
     so the test encodes the tier matrix as an explicit expected-value fixture, not a generated
     comparison.
   - Location: `tests/agent_orchestration/test_contract_structure.py`

3. **`test_skills_yaml_validates_and_has_stable_ids`**
   - Category: unit
   - Verifies: `skills.yaml` validates against the validator, each entry has a stable, unique `id`
     field (not free-prose keys) traceable to a `.claude/skills/*/SKILL.md` directory, and every
     entry declares which workflow/role(s) it associates with. This is the concrete traceability
     surface `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`'s AC #3 depends on — the test should
     assert the id set is non-empty and every id is a valid Python-identifier-safe string (generator
     ergonomics for the downstream ticket).
   - Location: `tests/agent_orchestration/test_skills_catalog.py`

4. **`test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py`**
   - Category: unit (value-equality, not identity — per investigation.md's explicit distinction
     from `test_canonical_vocabulary_single_sourced`'s identity check)
   - Verifies: `set(contract phases for implement-ticket)` == `vocabulary.WORKFLOW_PHASES["implement-ticket"]`
     and `set(contract agents for implement-ticket)` == `vocabulary.WORKFLOW_AGENTS["implement-ticket"]`
     minus `implement-ticket-orchestrator` (pseudo-agent, excluded from `roles/*.yaml` per
     investigation.md's Anti-Drift Hazards). Docstring/test name must state explicitly this is a
     one-time bootstrap-correctness check, not an ongoing sync guarantee (see Anti-Drift Test Guards
     below for the companion guard enforcing that framing).
   - Location: `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py`

5. **`test_validator_raises_named_error_on_malformed_contract`**
   - Category: unit
   - Verifies: the new validator exposes a single, flat, named exception type (mirroring
     `FixtureValidationError` at `tools/agent_replay/fixture_envelope.py:22-23`) that is raised —
     naming the exact file and exact missing/malformed field in the message — for at least: (a) a
     `contract.yaml` missing the required `version` field, (b) a `roles/*.yaml` file missing a
     required obligation field, (c) a non-mapping YAML root. Table-driven / parametrized over these
     malformed-fixture cases, each asserting both the exception type and a message substring
     containing the file path and field name.
   - Location: `tests/agent_orchestration/test_validator_errors.py`

6. **`test_validator_generator_zero_network_calls`**
   - Category: architecture guard (AST-scan, static — per investigation.md's explicit note that no
     runtime-monkeypatch precedent exists and a monkeypatch approach would not be structural/
     deterministic)
   - Verifies: every `.py` file under the new validator/generator's tool directory contains no
     `import socket` / `import urllib` / `import http.client` / `import requests` (or `from X import`
     equivalents), and no dotted-call forms reaching those modules (e.g. `urllib.request.urlopen`,
     `requests.get`, `socket.socket`). Modeled directly on
     `tests/agent_replay/test_runner_no_forbidden_calls.py`'s `_FORBIDDEN_MODULE_NAMES` /
     `_dotted_call_name` pattern, with the forbidden set swapped to network-library names instead of
     the four monitoring-script names.
   - Location: `tests/agent_orchestration/test_validator_no_network_calls.py`

7. **`test_generator_write_guard_refuses_writes_outside_agent_orchestration_without_flag`**
   - Category: architecture guard (AST-scan and/or behavioral, mock-verified)
   - Verifies two layers per the AC's "AST- or mock-verified" wording: (a) statically, the generator
     module contains no unconditional call that writes to a path outside `agent-orchestration/`
     (i.e. no bare `open(path, "w")` / `Path(...).write_text` reachable without the explicit
     generation-flag branch guarding it); (b) behaviorally, invoking the generator's public entry
     point without the explicit flag against a path outside `agent-orchestration/` raises/refuses
     rather than writing (assert no file appears via `tmp_path` + monkeypatched cwd), and invoking it
     WITH the flag against an allowed target path succeeds — a positive control, mirroring
     `test_fake_stand_ins_exist_and_are_actually_called_inside_replay_slice`'s pattern of proving the
     guard is actually wired in, not merely present-but-unused.
   - Location: `tests/agent_orchestration/test_validator_no_network_calls.py` (write-guard tests
     colocated with the containment-guard file) or a dedicated
     `tests/agent_orchestration/test_generator_write_guard.py` if the file grows unwieldy —
     implementer's call, driven by how many assertions land in each.

8. **`test_contract_yaml_has_versioning_field_and_documented_scheme`**
   - Category: unit
   - Verifies: `contract.yaml`'s `version` field is present, matches the scheme this ticket's Plan
     phase documents (e.g. a regex/type check consistent with whatever semver-vs-integer decision
     Plan records), and that the versioning scheme is documented in `plan.md` or the contract's own
     README before this test is considered satisfied — the test itself only checks the mechanical
     field, not the doc; the doc requirement is enforced by done-checker's frontmatter/DoD gate, not
     by this pytest test. Named consistently with `workflow_version`/`hook_schema_version` per the
     ADR's Versioning section (`docs/architecture/agent_orchestration_contract.md:80-90`).
   - Location: `tests/agent_orchestration/test_contract_structure.py`

## Scoped Pytest Commands

```
pytest tests/agent_orchestration/ -v
pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_agent_monitoring_legacy_reader.py tests/tools/test_codex_capability_diagnostics.py -v
pytest tests/agent_replay/ -v
```

Never `pytest tests/`. If the implementation ends up placing new tests under `tests/tools/` instead
of a new `tests/agent_orchestration/` directory (implementer's call, but `tests/agent_orchestration/`
mirrors the existing `tools/agent_replay/` <-> `tests/agent_replay/` naming precedent and is
preferred), adjust the first command to the actual glob
(`pytest tests/tools/test_agent_orchestration*.py -v`).

## Anti-Drift Test Guards

Each guard below maps directly to an Anti-Drift Hazard in investigation.md.

- **`test_vocabulary_py_file_unmodified` (or equivalent git-diff-based check run manually, not as a
  pytest assertion)** — confirms `tools/agent-monitoring/vocabulary.py`,
  `.claude/workflows/implement-ticket.js`, and `tools/agent-monitoring/validate.py` byte-for-byte
  unchanged from the pre-ticket commit. A pytest test can hash-compare against a checked-in
  reference hash captured at Plan time if the implementer wants this automated; otherwise this is a
  Verify-phase manual `git diff --stat` check — either way it must happen before claiming DoD.

- **`test_roles_never_include_orchestrator_pseudo_agent`** — asserts no file under
  `agent-orchestration/roles/*.yaml` has a role name or filename matching
  `implement-ticket-orchestrator` (case-insensitive substring check on both filename and any `name`/
  `id` field inside each YAML). Directly guards investigation.md's Anti-Drift Hazard: "Do not let
  `roles/*.yaml` silently include `implement-ticket-orchestrator`."
  Location: `tests/agent_orchestration/test_contract_structure.py`.

- **`test_bootstrap_equality_test_docstring_states_one_time_not_permanent`** — a meta-test that
  inspects the docstring/comments of test #4 above (`test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py`)
  or the validator module it exercises, asserting it contains language indicating a one-time
  bootstrap check (e.g. asserting the string does NOT read as an unconditional "always" claim, and
  DOES contain phrasing consistent with "bootstrap"/"one-time"/"while vocabulary.py remains legacy
  source of truth"). This is intentionally a soft/lint-style guard (string-matching a docstring is
  weak signal) — its real purpose is to force a human/implementer to write the correct framing
  in the first place, catching the reversed-ownership bug the ticket's Codex-review correction #1
  already fixed once. Location: `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py`
  (colocated with the equality test it documents).

- **`test_skills_yaml_does_not_duplicate_role_fields`** — asserts no entry in `skills.yaml` shares
  the exact key shape used by `roles/*.yaml` entries (e.g. no `obligations`/`gates` field bleeding
  from the role schema into the skill schema) — guards investigation.md's "Do not let `skills.yaml`
  duplicate role obligations" hazard by checking the two schemas stay structurally distinct.
  Location: `tests/agent_orchestration/test_skills_catalog.py`.

- **`test_no_conformance_or_provider_adapter_code_in_this_tickets_tree`** — a scope-creep guard:
  asserts no file under the new validator/generator tool tree or `agent-orchestration/` imports
  from or references `.claude/` conformance-diff tooling paths or `.codex/` adapter paths — guards
  against accidentally starting the Claude conformance/diff tooling or Codex adapter work this
  ticket explicitly excludes (Out of Scope). Location: `tests/agent_orchestration/test_validator_no_network_calls.py`
  or a dedicated scope-guard file, implementer's call.

- **`test_finalizer_role_entry_documents_inline_prompt_exception`** — asserts the `finalizer.yaml`
  role entry (if present, per investigation.md noting `finalizer` has no `.claude/agents/finalizer.md`
  file) carries an explicit field/note stating it is inline-prompted rather than a separate subagent
  file — guards against silently treating all 9-vs-10 role files as uniform when one is structurally
  different. Location: `tests/agent_orchestration/test_contract_structure.py`.
