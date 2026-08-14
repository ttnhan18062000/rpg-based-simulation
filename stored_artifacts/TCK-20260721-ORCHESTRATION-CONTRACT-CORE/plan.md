---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-ORCHESTRATION-CONTRACT-CORE
artifact_type: plan
tags: [ai, workflows, process-improvement]
---

# Implementation Plan — TCK-20260721-ORCHESTRATION-CONTRACT-CORE

## Summary

Stand up the repo-root `agent-orchestration/` directory as the first version of the provider-neutral
semantic contract (`contract.yaml`, `workflows/implement-ticket.yaml`, `roles/*.yaml` — 10 files,
`skills.yaml`, `monitoring-schema.yaml`, `hook-events.yaml`), bootstrap its phase/agent vocabulary
once from `tools/agent-monitoring/vocabulary.py` (read-only), and build a deterministic,
network-free validator/generator under `tools/agent_orchestration/` that raises a named error type
on malformed contract data and refuses to write outside `agent-orchestration/` unless an explicit
generation flag is passed. The versioning scheme is decided here (see Step 1) as a simple
integer generation number, not semver. Each of the six contract files, the validator, and the test
suite under `tests/agent_orchestration/` land as independent, individually verifiable steps, closely
mirroring test_plan.md's 8 new-test list plus its 6 anti-drift guards. The work is strictly additive
and read-only with respect to `vocabulary.py`, `implement-ticket.js`, and `validate.py` — no
provider file changes, no conformance/adapter code, no generation-direction flip.

## Steps

### Step 1 — `contract.yaml` with the decided versioning scheme
**Files:** `agent-orchestration/contract.yaml`

**Change:** Create the top-level contract manifest. Decide and apply the versioning scheme now,
per AC #8 and the ADR's "thinnest-evidenced" framing (`docs/architecture/agent_orchestration_contract.md:80-90`):

> **Versioning scheme: simple integer generation number.** `version: 1` (bare integer, not a
> string, not semver). Increment by exactly 1 on any breaking schema change to any file under
> `agent-orchestration/` (a field rename, a required-field addition, a structural reshape).
> Non-breaking additions (a new optional field, a new role/skill entry) do not bump `version`.
> Rationale: this is a single-repo internal contract with zero external consumers today (no
> provider adapter yet reads it) — semver's major/minor/patch triad models compatibility
> guarantees for external consumers that do not yet exist. An integer generation number is the
> simplest scheme that still gives a monotonic, comparable "which contract shape is this"
> signal, consistent with the ADR's instruction not to invent more structure than the evidence
> supports.

Fields to include: `version: 1` (int), `name: implement-ticket-agent-orchestration-contract`,
`description` (one line), and pointers/notes describing the six sibling files this manifest
governs (`workflows/`, `roles/`, `skills.yaml`, `monitoring-schema.yaml`, `hook-events.yaml`) —
no duplication of their content, just a manifest. Apply the ADR's naming-consistency rule: this
file's field is named `version`; the sibling files use `workflow_version` (Step 2),
`hook_schema_version` (Step 6) — each an independent `version: 1` counter scoped to its own file,
not one shared counter across all six files (a breaking change to `roles/*.yaml` alone should not
force-bump `hook-events.yaml`'s counter).

**Do NOT touch:** `tools/agent-monitoring/vocabulary.py`, `.claude/workflows/implement-ticket.js`,
`tools/agent-monitoring/validate.py`. Do not invent a semver scheme — the decision above is final
for this ticket.

**Verify:** `test_contract_yaml_has_versioning_field_and_documented_scheme`
(`tests/agent_orchestration/test_contract_structure.py`).

---

### Step 2 — `workflows/implement-ticket.yaml`: bootstrap vocabulary + tier-applicability matrix
**Files:** `agent-orchestration/workflows/implement-ticket.yaml`

**Change:** Create the workflow definition. Two distinct pieces of data, both required:

1. **Phase/agent name lists**, bootstrapped verbatim (value-equal, not identity) from
   `vocabulary.py`'s `WORKFLOW_PHASES["implement-ticket"]` (11 phases) and
   `WORKFLOW_AGENTS["implement-ticket"]` (11 agents, **minus** `implement-ticket-orchestrator` —
   that name is a pseudo-agent label for one Test-phase cleanup-failure event, not a role; exclude
   it from this file's agent list entirely).
2. **Per-phase tier-applicability matrix** — new modeling work, not present in `vocabulary.py`,
   derived directly from `implement-ticket.js`'s real branch structure documented in
   investigation.md's Current Behavior section. Use a `tier_behavior` value per phase, per tier,
   from the set `{full, skipped_event, conditional_absent}`:
   - `Scope`, `Implement`, `Test`, `Verify`, `Finalize`: `full` for both `standard` and `hotfix`.
   - `Investigate`, `Plan`, `Review`, `Architecture-Verify`: `full` for `standard`;
     `skipped_event` for `hotfix` (the phase still emits an event with `status: skipped` —
     it is not literally absent from `events.jsonl`, per `implement-ticket.js:595-597` and
     `:772`).
   - `Parity`: `full` for both tiers when there is a `src/` change and `behavior_changed` is
     true; `skipped_event` for both tiers otherwise (`implement-ticket.js:917`) — this axis is
     content-driven, not tier-driven, so encode it as `conditional: src_change_and_behavior_changed`
     applying identically to both tiers, not as a tier-keyed value.
   - `Security-Review`: `full` when the ticket is tagged `security` or lists `/security-review`
     in `suggested_skills`; **`conditional_absent`** otherwise — meaning no event at all is
     written (`implement-ticket.js:1020-1068` has no `else` branch), which is a materially
     different behavior from `skipped_event` and must use a distinct enum value so a future
     reader (or the Codex conformance ticket) does not conflate "wrote a skipped event" with
     "wrote nothing."

   Concrete YAML shape (implementer may adjust key names slightly but must preserve this
   information):
   ```yaml
   workflow_version: 1
   workflow_id: implement-ticket
   phases:
     - name: Scope
       tiers: {standard: full, hotfix: full}
     - name: Investigate
       tiers: {standard: full, hotfix: skipped_event}
     - name: Plan
       tiers: {standard: full, hotfix: skipped_event}
     - name: Review
       tiers: {standard: full, hotfix: skipped_event}
     - name: Implement
       tiers: {standard: full, hotfix: full}
     - name: Architecture-Verify
       tiers: {standard: full, hotfix: skipped_event}
     - name: Test
       tiers: {standard: full, hotfix: full}
     - name: Parity
       tiers: {standard: conditional, hotfix: conditional}
       condition: src_change_and_behavior_changed
       if_false: skipped_event
     - name: Security-Review
       tiers: {standard: conditional, hotfix: conditional}
       condition: security_tag_or_suggested_skill
       if_false: conditional_absent
     - name: Verify
       tiers: {standard: full, hotfix: full}
     - name: Finalize
       tiers: {standard: full, hotfix: full}
   agents:
     - ticket-scoper
     - investigator
     - planner
     - architecture-reviewer
     - implementer
     - test-scoper
     - parity-updater
     - security-reviewer
     - done-checker
     - finalizer
   ```

**Do NOT touch:** `vocabulary.py` itself (read-only reference). Do not include
`implement-ticket-orchestrator` in the `agents` list. Do not model `Security-Review`'s
`conditional_absent` the same way as `Investigate`/`Plan`/`Review`/`Architecture-Verify`'s
`skipped_event` — they are genuinely different behaviors per investigation.md.

**Verify:** `test_workflow_covers_both_tiers` and
`test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py`
(`tests/agent_orchestration/test_contract_structure.py`,
`tests/agent_orchestration/test_bootstrap_vocabulary_equality.py`).

---

### Step 3 — `roles/*.yaml` (10 files, `implement-ticket-orchestrator` excluded)
**Files:** `agent-orchestration/roles/ticket-scoper.yaml`, `investigator.yaml`, `planner.yaml`,
`architecture-reviewer.yaml`, `implementer.yaml`, `test-scoper.yaml`, `parity-updater.yaml`,
`security-reviewer.yaml`, `done-checker.yaml`, `finalizer.yaml` (10 files total).

**Change:** One YAML file per real role. Each file carries: `role_id` (matches filename stem),
`description` (one line, what the role does in the workflow), `phases` (which
`workflows/implement-ticket.yaml` phase(s) it participates in — e.g. `architecture-reviewer`
lists both `Review` and `Architecture-Verify`, matching investigation.md's finding that one
subagent backs both phases), `has_agent_file` (bool — true for the 9 with a
`.claude/agents/{role}.md` file, false only for `finalizer`), and for `finalizer` specifically an
explicit `inline_prompt_exception` field/note stating it is prompted inline inside
`implement-ticket.js` (around `:1151-1255`) rather than defined as a separate `.claude/agents/*.md`
subagent file — this is the documented exception AC requires, not a silent gap.

Example (`finalizer.yaml`):
```yaml
role_version: 1
role_id: finalizer
description: Closes out the ticket — DoD checks, artifact migration, working_log, monitoring writes.
phases: [Finalize]
has_agent_file: false
inline_prompt_exception: >
  finalizer has no .claude/agents/finalizer.md file; it is prompted inline inside
  implement-ticket.js (~lines 1151-1255), not defined as a separate subagent file.
  This is a documented, intentional exception, not a missing role definition.
```

**Do NOT touch:** Do not create an 11th file for `implement-ticket-orchestrator` — it is the
orchestrator's own pseudo-agent label for the Test-phase cleanup-failure event, not a delegated
role with obligations/gates of its own. Do not invent obligations/gates content beyond what
`implement-ticket.js`'s real call sites and `.claude/agents/*.md` files support — no speculative
role capabilities.

**Verify:** `test_agent_orchestration_dir_has_required_files` (10 role files present, parse as
YAML), `test_roles_never_include_orchestrator_pseudo_agent`,
`test_finalizer_role_entry_documents_inline_prompt_exception`
(all `tests/agent_orchestration/test_contract_structure.py`).

---

### Step 4 — `skills.yaml`: minimal skill catalog with stable ids
**Files:** `agent-orchestration/skills.yaml`

**Change:** One entry per `.claude/skills/*/SKILL.md` directory (16 directories per investigation.md:
`agent-monitoring-retro`, `api-design-principles`, `architecture`, `backend-testing`,
`brainstorming`, `create-tickets`, `debugging-strategies`, `doc-coauthoring`, `frontend-design`,
`implement-epic`, `implement-ticket`, `prompt-builder`, `python-performance-optimization`,
`python-testing-patterns`, `simq-audit`, `test-driven-development`). Minimal shape decided here
(no upstream doc specifies more):

```yaml
skills_version: 1
skills:
  - id: implement-ticket
    description: "Full ticket implementation workflow orchestrator."
    workflows: [implement-ticket]
    roles: []
  - id: create-tickets
    description: "Ticket creation/scoping workflow."
    workflows: []
    roles: []
  # ... one entry per .claude/skills/*/SKILL.md directory
```

Rules for this shape:
- `id` is the directory name verbatim (already a stable, Python-identifier-safe, unique string —
  no need to invent a separate slug).
- `description` is a single short line, either pulled from the SKILL.md's own frontmatter/opening
  description if present, or written fresh if not — do not leave it empty.
- `workflows` is a list of `workflows/*.yaml` workflow ids this skill associates with (may be
  empty for skills that are standalone, e.g. `python-performance-optimization`).
- `roles` is a list of `roles/*.yaml` role ids this skill associates with (may be empty — most
  skills are not tied to a specific subagent role).
- **No `obligations`, `gates`, `phases`, or any other field from the `roles/*.yaml` schema** —
  keep the two schemas structurally distinct (this is the guard in Step 9).

This satisfies `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`'s AC #3 traceability requirement:
that ticket's generated Codex `.agents/skills/` catalog must trace to `id` values in this file.

**Do NOT touch:** `.claude/skills/*/SKILL.md` files themselves (read-only source for descriptions).
Do not add role-shaped fields to any skill entry.

**Verify:** `test_skills_yaml_validates_and_has_stable_ids`, `test_skills_yaml_does_not_duplicate_role_fields`
(`tests/agent_orchestration/test_skills_catalog.py`).

---

### Step 5 — `monitoring-schema.yaml`: carry execution identity fields verbatim
**Files:** `agent-orchestration/monitoring-schema.yaml`

**Change:** Carry the three already-decided fields from
`docs/ai/monitoring_writer_decision.md` §2 / the ADR's "Execution Identity (Consumed Input)"
subsection verbatim — this ticket does not re-derive or alter their shape:

```yaml
schema_version: 1
fields:
  execution_id:
    description: >
      Immutable per-execution key: f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}".
      Generated fresh once per workflow execution. Never reused. Never a join key.
    format: "{provider}-{ticket_id}-{unix_ts_ms}-{token_hex_8}"
    source: docs/ai/monitoring_writer_decision.md#execution-identity-model
  run_id:
    description: >
      Human-readable run reference, unchanged shape (TCK-YYYYMMDD-SHORT-SCOPE or EPIC-*/FOLDER-*).
      Display/reference field, not the execution's primary key.
    source: docs/ai/monitoring_writer_decision.md#execution-identity-model
  ticket_id:
    description: >
      Stable cross-run join key. All records for all executions of the same ticket, by any
      provider, share the same ticket_id value.
    source: docs/ai/monitoring_writer_decision.md#execution-identity-model
```

This is documentation of an already-decided field model, not a new schema design — do not add
fields beyond these three, do not change their format strings, and do not imply any real
`agent-monitoring/*.jsonl` file has been changed (it has not, per this ticket's Out of Scope).

**Do NOT touch:** `tools/agent-monitoring/` implementation files. `monitoring-schema.yaml`
describes a future schema — it is not itself a writer and does not touch
`agent-monitoring/*.jsonl`.

**Verify:** `test_agent_orchestration_dir_has_required_files` (file exists, parses as YAML)
(`tests/agent_orchestration/test_contract_structure.py`).

---

### Step 6 — `hook-events.yaml`: the two real hook types
**Files:** `agent-orchestration/hook-events.yaml`

**Change:** Normalize exactly the two hook types actually wired in `.claude/settings.json`
(`PreToolUse`, `PostToolUse`, per investigation.md) — no speculative `SessionStart`/`Stop`/other
hook types:

```yaml
hook_schema_version: 1
hook_types:
  - id: PreToolUse
    description: Fired before a tool call executes.
  - id: PostToolUse
    description: Fired after a tool call completes; feeds tools.jsonl writes.
```

**Do NOT touch:** `.claude/settings.json` itself. Do not add hook types not currently wired —
this file documents the real, current vocabulary only.

**Verify:** `test_agent_orchestration_dir_has_required_files` (file exists, parses as YAML)
(`tests/agent_orchestration/test_contract_structure.py`).

---

### Step 7 — Validator/loader with named error type
**Files:** `tools/agent_orchestration/__init__.py` (new), `tools/agent_orchestration/errors.py` (new),
`tools/agent_orchestration/loader.py` (new)

**Change:** Build the validation entry point, mirroring `tools/agent_replay/fixture_envelope.py`'s
shape exactly:
- `errors.py`: single flat exception class, no subclass hierarchy —
  `class ContractValidationError(Exception): """Raised by load_contract when a required
  agent-orchestration/ field is missing, malformed, or the YAML root is not a mapping."""`
  Messages must name the exact file path and exact missing/malformed field, e.g.
  `f"{path}: missing required field 'version'"`, `f"{path}: roles[{idx}] missing required
  field 'role_id'"`, `f"{path}: YAML root is not a mapping"`.
- `loader.py`: `load_contract(root: Path) -> ContractBundle` (a frozen dataclass, mirroring
  `FixtureEnvelope`) — a single entry point that reads and validates all six files under
  `agent-orchestration/` (`contract.yaml`, `workflows/implement-ticket.yaml`, all `roles/*.yaml`,
  `skills.yaml`, `monitoring-schema.yaml`, `hook-events.yaml`), raising `ContractValidationError`
  on any of: missing required field (`version`/`workflow_version`/`hook_schema_version`/
  `schema_version`/`skills_version`/`role_version`, `role_id`, `phases`, etc.), non-mapping YAML
  root, or a `roles/*.yaml` file missing a required obligation-shaped field. Returns the parsed,
  validated bundle on success.
- Use only `yaml.safe_load` (already a repo dependency, per `fixture_envelope.py`'s own usage
  pattern) and the stdlib — no new third-party dependency.

**Do NOT touch:** `tools/agent_replay/fixture_envelope.py` itself — read it as a template, do not
import from it or modify it. Do not reach for `requests`/`urllib`/`socket`/`http.client` anywhere
in this module (guarded structurally in Step 8, but do not write code that would need them —
everything here is local filesystem + YAML parsing).

**Verify:** `test_validator_raises_named_error_on_malformed_contract`
(`tests/agent_orchestration/test_validator_errors.py`).

---

### Step 8 — Generator with structural write-guard + zero-network-calls guard
**Files:** `tools/agent_orchestration/generator.py` (new)

**Change:** Build the generation command as a separate module from `loader.py` (keeps the
"read/validate" and "write" concerns physically separated, making the AST write-guard scan
simpler). Public entry point, e.g. `generate(target_dir: Path, *, allow_outside_contract: bool =
False) -> None` (or an equivalent explicit-flag CLI subcommand `--generate --output-dir <path>
--i-know-this-writes-outside-agent-orchestration`). Structural rule, not just a docstring:

- The function must refuse (raise, e.g. `ContractValidationError` or a dedicated
  `GeneratorWriteGuardError`) any write whose resolved target path is not inside
  `agent-orchestration/` **unless** the explicit flag/argument is `True`/present. Implement this
  as an actual path-containment check (`target_path.resolve().is_relative_to(repo_root /
  "agent-orchestration")`) guarding every write call — not a generic `--output-dir` flag with no
  default restriction (the anti-drift hazard investigation.md flags explicitly).
- No `.py` file under `tools/agent_orchestration/` may import or dotted-call into `socket`,
  `urllib`, `http.client`, or `requests` — this is enforced by the AST-scan test in Step 10, but
  write the code to naturally satisfy it (pure filesystem I/O only).

**Do NOT touch:** Anything outside `agent-orchestration/` in the default/no-flag path. Do not
default the guard flag to `True`.

**Verify:** `test_validator_generator_zero_network_calls`,
`test_generator_write_guard_refuses_writes_outside_agent_orchestration_without_flag`
(`tests/agent_orchestration/test_validator_no_network_calls.py`, and/or
`tests/agent_orchestration/test_generator_write_guard.py` if split).

---

### Step 9 — Bootstrap-equality test with one-time framing
**Files:** `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py` (new)

**Change:** Write `test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py`: import
`tools/agent-monitoring/vocabulary.py` (read-only import, `sys.path` insertion pattern matching
`tests/tools/test_validate_agent_monitoring.py:9-14`'s `_MONITORING_TOOLS_DIR` precedent), load
the contract via `load_contract()` from Step 7, and assert **value-equality** (not identity):
`set(contract_phase_names) == vocabulary.WORKFLOW_PHASES["implement-ticket"]` and
`set(contract_agent_ids) == vocabulary.WORKFLOW_AGENTS["implement-ticket"] -
{"implement-ticket-orchestrator"}`.

The test's docstring (and ideally a short comment on `load_contract`/the workflow YAML's own
top-level description, but the pytest docstring is the load-bearing one for the meta-test in
this step) must state explicitly, in prose: this is a **one-time bootstrap-correctness check**,
run while `.claude/workflows/implement-ticket.js` remains live and `vocabulary.py` remains the
legacy, operative source of truth — **not** an ongoing single-source-of-truth guarantee the way
`test_canonical_vocabulary_single_sourced`'s identity check is. Do not phrase it as "these two
must always stay equal forever" — that re-introduces the reversed-ownership bug the ticket's
Codex-review correction #1 already fixed once.

Also add `test_bootstrap_equality_test_docstring_states_one_time_not_permanent` in the same file:
a meta-test that reads this test function's (or the module's) docstring/comments via
`inspect.getdoc()` and asserts it contains bootstrap/one-time framing language (e.g. contains one
of `"bootstrap"`, `"one-time"`, `"legacy source of truth"`) — a soft/lint-style guard whose real
purpose is forcing the correct framing to exist in the first place.

**Do NOT touch:** `vocabulary.py` itself. Do not assert object identity. Do not word the
docstring as a permanent sync guarantee.

**Verify:** Both tests pass; `pytest tests/agent_orchestration/test_bootstrap_vocabulary_equality.py -v`.

---

### Step 10 — Remaining tests from test_plan.md
**Files:** `tests/agent_orchestration/test_contract_structure.py`,
`tests/agent_orchestration/test_skills_catalog.py`,
`tests/agent_orchestration/test_validator_errors.py`,
`tests/agent_orchestration/test_validator_no_network_calls.py` (all new)

**Change:** Implement every remaining test named in test_plan.md's "New Tests Required" and
"Anti-Drift Test Guards" sections not already covered by Steps 1-9:

- `test_agent_orchestration_dir_has_required_files` — all 6 top-level paths exist and parse
  (`contract.yaml`, `workflows/implement-ticket.yaml`, the 10 `roles/*.yaml`, `skills.yaml`,
  `monitoring-schema.yaml`, `hook-events.yaml`); asserts exactly 10 role files, not 11.
- `test_workflow_covers_both_tiers` — asserts the `tier_behavior`/tiers structure from Step 2
  matches the exact expected-value fixture for all 11 phases (hardcode the expected matrix from
  Step 2's table as the fixture — this is new modeling work with no generated source to compare
  against, per investigation.md).
- `test_contract_yaml_has_versioning_field_and_documented_scheme` — `contract.yaml`'s `version`
  field is present, is an `int`, equals `1`, and this plan.md documents the scheme (satisfied by
  this document existing).
- `test_roles_never_include_orchestrator_pseudo_agent` — no `roles/*.yaml` filename or `role_id`
  field matches `implement-ticket-orchestrator` (case-insensitive).
- `test_finalizer_role_entry_documents_inline_prompt_exception` — `roles/finalizer.yaml` has
  `has_agent_file: false` and a non-empty `inline_prompt_exception` field.
- `test_skills_yaml_validates_and_has_stable_ids` — `skills.yaml` validates via
  `load_contract()`; every `id` is unique and Python-identifier-safe; id set non-empty.
- `test_skills_yaml_does_not_duplicate_role_fields` — no skill entry has any of the keys used by
  the `roles/*.yaml` schema (`phases`, `has_agent_file`, `inline_prompt_exception`, or any
  `obligations`/`gates`-shaped field).
- `test_validator_raises_named_error_on_malformed_contract` — table-driven over at least: (a)
  `contract.yaml` missing `version`, (b) a `roles/*.yaml` file missing a required field, (c) a
  non-mapping YAML root; each asserts `ContractValidationError` and a message substring
  containing the file path and field name.
- `test_validator_generator_zero_network_calls` — AST-scan (modeled directly on
  `tests/agent_replay/test_runner_no_forbidden_calls.py`'s `_FORBIDDEN_MODULE_NAMES` /
  `_dotted_call_name` pattern) over every `.py` file under `tools/agent_orchestration/`, forbidden
  set = `{socket, urllib, http.client, requests}` and their dotted-call forms.
- `test_generator_write_guard_refuses_writes_outside_agent_orchestration_without_flag` — static
  half (no unconditional out-of-tree `open`/`write_text` reachable without the flag branch) +
  behavioral half (call `generate()` without the flag against a `tmp_path` outside
  `agent-orchestration/`, assert it raises and no file appears; call it WITH the flag, assert it
  succeeds — positive control).
- `test_no_conformance_or_provider_adapter_code_in_this_tickets_tree` — scope-creep guard:
  no file under `tools/agent_orchestration/` or `agent-orchestration/` references `.claude/`
  conformance-diff paths or `.codex/` adapter paths.

**Do NOT touch:** `tests/agent_replay/`, `tests/tools/test_validate_agent_monitoring.py`, or any
other existing test file — read them as templates only.

**Verify:** `pytest tests/agent_orchestration/ -v` all green; then run the three regression
commands from test_plan.md's "Scoped Pytest Commands" section
(`tests/tools/test_validate_agent_monitoring.py`, `test_agent_monitoring_legacy_reader.py`,
`test_codex_capability_diagnostics.py`; and `tests/agent_replay/`) to confirm zero regression.

---

### Step 11 — `agent-orchestration/README.md`
**Files:** `agent-orchestration/README.md` (new)

**Change:** Document, in prose, for a future reader landing in this directory cold:
1. What this directory is (the provider-neutral semantic contract for `implement-ticket`, per
   `docs/architecture/agent_orchestration_contract.md`'s Source Ownership decision).
2. The versioning scheme decided in Step 1 (simple integer generation number, one independent
   counter per file: `version` in `contract.yaml`, `workflow_version`,
   `hook_schema_version`, `schema_version`, `skills_version`, `role_version`) and the rule for
   when to bump it (breaking schema change only).
3. **The one-way future direction, stated explicitly** (this is also required by the ticket's
   own AC #3): today, `workflows/implement-ticket.yaml`'s phase/agent vocabulary was
   bootstrap-initialized once from `tools/agent-monitoring/vocabulary.py` (a one-time
   correctness check, verified by `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py` —
   not an ongoing sync). Going forward, once provider adapters exist, this contract becomes the
   upstream semantic authority: `vocabulary.py` (and any provider adapter's own vocabulary) is
   expected to become generated/validated FROM this contract, not the reverse. This ticket does
   not implement that flip — it is explicitly out of scope, follow-on work for a later ticket
   once adapters exist (per the ticket's own Scope/Out-of-Scope text).
4. How to run the validator (`load_contract()`) and the generator's explicit-flag invocation.
5. Pointer to `docs/architecture/agent_orchestration_contract.md` (the ADR) and
   `docs/ai/monitoring_writer_decision.md` as upstream authorities this directory implements.

**Do NOT touch:** the ADR document itself (`docs/architecture/agent_orchestration_contract.md`) —
this ticket does not flip its `## Status` field or edit its Decision sections; it only implements
what the ADR already decided.

**Verify:** No dedicated pytest test (README content is prose) — covered by done-checker's
documentation-completeness check and by AC #3's own wording ("This ticket's own documentation
(plan.md or the contract's own README.md) explicitly states the one-way future direction") —
already partially satisfied by this plan.md Step 1/11 text, and finalized by this README.

## Scope Guards

- **Never modify** `tools/agent-monitoring/vocabulary.py`, `.claude/workflows/implement-ticket.js`,
  or `tools/agent-monitoring/validate.py` — read-only bootstrap/reference sources for the entire
  plan. Confirm via `git diff --stat` before claiming completion (test_plan.md's Static/manual
  confirmation section).
- **Never flip the generation direction.** `vocabulary.py` → `agent-orchestration/` is one-time
  and one-way in this ticket. Do not build any code path that regenerates `vocabulary.py` from
  the contract — that is explicitly follow-on work for a future ticket.
- **Never include `implement-ticket-orchestrator`** as a `roles/*.yaml` entry — it is a
  pseudo-agent label for one event, not a role.
- **Never build the Claude conformance/diff tooling** or any `.claude`/`.codex` adapter/hook code
  — both are owned by separate, already-scoped tickets (`TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`
  and siblings named in Related Tickets).
- **Never let `skills.yaml` and `roles/*.yaml` share schema fields** — they model distinct
  vocabulary axes (reusable skills vs. delegated subagent roles) and must stay structurally
  separable for the downstream Codex traceability ticket.
- **Never default the generator's write-guard to permissive** — no writes outside
  `agent-orchestration/` without the explicit flag, enforced structurally, not just documented.
- **Never touch `docs/architecture/agent_orchestration_contract.md`'s own Status or Decision
  text** — this ticket implements the ADR, it does not amend it.
- **No new third-party dependency** — `yaml` (already used by `fixture_envelope.py`) and stdlib
  only, consistent with the zero-network-calls requirement.

## Dependency Map

- Steps 1-6 (the six contract YAML files) are independent of each other and can be done in any
  order, but Step 2 (workflow tier matrix + bootstrap vocabulary) should land before Step 9
  (bootstrap-equality test) since the test needs real data to assert against.
- Step 7 (validator/loader) depends on Steps 1-6 existing (needs real files to validate against
  for its own tests), but its code can be written in parallel and tested last.
- Step 8 (generator) depends on Step 7 (`errors.py`/`ContractValidationError` reused for the
  write-guard's error path) but is otherwise independent.
- Step 9 (bootstrap-equality test) depends on Step 2 (workflow YAML must exist with real data)
  and Step 7 (`load_contract()` must exist to load it).
- Step 10 (remaining tests) depends on Steps 1-8 all being complete — it is the consolidation
  step that exercises every file and every guard.
- Step 11 (README) depends on Step 1 (versioning scheme) and can be written any time after Step 1,
  but should be finalized last so it accurately reflects the finished directory layout.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `agent-orchestration/` exists with all 6 required files/dirs, covering both tiers | Steps 1-6 | `test_agent_orchestration_dir_has_required_files`, `test_workflow_covers_both_tiers` |
| `skills.yaml` created, validated, traceable stable ids | Step 4, Step 7 | `test_skills_yaml_validates_and_has_stable_ids` |
| `workflows/implement-ticket.yaml` bootstrap-initialized from `vocabulary.py`, one-time equality test | Step 2, Step 9 | `test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py`, `test_bootstrap_equality_test_docstring_states_one_time_not_permanent` |
| Plan/README documents the one-way future direction | Step 11 (and this plan.md's Summary/Step 1/Step 9) | Manual doc review (done-checker DoD gate) |
| Validator raises named, deterministic error type mirroring `FixtureValidationError` | Step 7 | `test_validator_raises_named_error_on_malformed_contract` |
| Validator/generator makes zero network calls | Step 8 | `test_validator_generator_zero_network_calls` |
| Validator/generator writes zero files outside `agent-orchestration/` unless explicit flag passed | Step 8 | `test_generator_write_guard_refuses_writes_outside_agent_orchestration_without_flag` |
| `contract.yaml` has required `version` field, versioning scheme documented and tested | Step 1 | `test_contract_yaml_has_versioning_field_and_documented_scheme` |

## Anti-Drift Notes

- The bootstrap-equality test (Step 9) must read as a **one-time correctness check**, never as a
  permanent two-way sync guarantee — this is the exact bug Codex's review already caught and
  corrected once in this ticket's own history (see the ticket's "Corrected per Codex review"
  note). The meta-test in Step 9 exists specifically to keep this framing from silently drifting
  back.
- `Security-Review`'s `conditional_absent` behavior (Step 2) is materially different from
  `Investigate`/`Plan`/`Review`/`Architecture-Verify`'s `skipped_event` behavior — a
  `skipped_event` phase still writes an event to `events.jsonl`; a `conditional_absent` phase
  writes nothing at all. Do not collapse these into one enum value.
- `finalizer` is the one role with no `.claude/agents/*.md` file — its `roles/finalizer.yaml`
  entry must carry the documented exception, not silently look identical to the other 9 role
  files.
- The write-guard (Step 8) must be a structural path-containment check, not a docstring
  convention or an undocumented default — the natural shortcut (a generic `--output-dir` flag
  with no restriction) fails the AC.
- `skills.yaml` and `roles/*.yaml` are different vocabulary axes; keep their schemas
  non-overlapping (Step 4, guarded by Step 10's `test_skills_yaml_does_not_duplicate_role_fields`).
- Every file this ticket writes lives under `agent-orchestration/`, `tools/agent_orchestration/`,
  or `tests/agent_orchestration/` — nothing under `tools/agent-monitoring/`, `.claude/`, or
  `tools/agent_replay/` is ever modified.

## Deviations

Implementation followed all 11 steps as written. Two additive, non-scope-changing deltas from
the plan's literal illustrative text, recorded here per the "never silently deviate" rule:

1. **Step 4 (`skills.yaml`)** — the plan's example shape shows `roles: []` for every
   illustrated entry except implicitly leaving room for real associations. The implemented
   `create-tickets` skill entry sets `roles: [ticket-scoper]` (not `[]`) — `vocabulary.py`'s
   `WORKFLOW_AGENTS["create-tickets"]` confirms `create-tickets.js` really does invoke a
   `ticket-scoper`-labeled agent, and `roles/ticket-scoper.yaml` already exists in this
   contract, so the association is real, not speculative. All other 15 skill entries keep
   `roles: []` as illustrated. `workflows` stays `[]` everywhere except `implement-ticket`
   (only `workflows/implement-ticket.yaml` exists in this ticket's scope — referencing
   `create-tickets`/`implement-epic`/`simq-audit` as workflow ids would dangle since those
   `workflows/*.yaml` files are out of scope here).
2. **Step 10 (tests)** — added three tests beyond test_plan.md's minimum list, all strictly
   additive sanity/coverage, none altering or replacing a required test:
   `test_load_contract_succeeds_against_the_real_contract` (positive-path sanity check that the
   real, committed contract validates end-to-end), and in the write-guard file,
   `test_generator_allows_writes_inside_agent_orchestration_without_flag` and
   `test_generated_output_round_trips_through_load_contract` (proves writes inside
   `agent-orchestration/` are unrestricted, and that generated output is itself valid,
   re-loadable contract data — closes the loop on the generator actually working, not just
   refusing).
