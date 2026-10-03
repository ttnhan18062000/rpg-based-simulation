---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-ORCHESTRATION-CONTRACT-CORE
phase: done
date: 2026-07-21
tags: []
---

# TCK-20260721-ORCHESTRATION-CONTRACT-CORE

## Title
Canonical contract core and validator for implement-ticket

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Stand up the versioned agent-orchestration/ semantic contract (contract.yaml, workflows/implement-ticket.yaml, roles/*.yaml, skills.yaml, monitoring-schema.yaml, hook-events.yaml) as the one authoritative description of phases, terminal statuses, roles, skills, artifacts, and gates for the first vertical slice, plus a deterministic, network-free validator/generator that fails clearly on malformed definitions and never touches provider files except through an explicit generation command. This matters because the ADR already decided YAML+generated-Python validation with the repo-root agent-orchestration/ as the source spec, and the Provider-Adapter Boundary bars adapters from redefining phases/statuses/gates/artifacts.

**Corrected per Codex review (2026-07-22, two rounds):** (1) the original AC treated `tools/agent-monitoring/vocabulary.py` as a permanent upstream authority the contract must stay generated-from-or-equal-to forever, reversing the ADR's own Source Ownership decision — fixed to a one-time bootstrap, not a permanent binding. (2) `skills.yaml` was missing entirely from this ticket's deliverables despite `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE` already consuming it as its generation source, and despite the ADR's own approved contract layout (`docs/architecture/agent_orchestration_contract.md:73`) listing it explicitly — added as an interface-completeness fix, no scope/ownership change.

## Scope
- Create agent-orchestration/ directory with contract.yaml, workflows/implement-ticket.yaml, roles/*.yaml, **skills.yaml**, monitoring-schema.yaml, hook-events.yaml covering standard and hotfix tiers, per the ADR's approved contract layout (`docs/architecture/agent_orchestration_contract.md:69-76`)
- Decide and document a versioning scheme; contract.yaml carries a required `version` field
- Build a deterministic, network-free validator/generator tool that fails clearly on malformed contract definitions
- Ensure the generator only writes outside agent-orchestration/ when invoked via an explicit generation command/flag
- **Bootstrap the phase/status vocabulary from `tools/agent-monitoring/vocabulary.py`'s WORKFLOW_PHASES/WORKFLOW_AGENTS as a one-time initialization step**, with a test asserting equality while the Claude workflow remains live and `vocabulary.py` is still the operative legacy source of truth
- **Define the one-way future relationship explicitly in this ticket's own documentation**: once this contract is validated, it becomes the upstream semantic authority; `vocabulary.py` (and any provider adapter's own vocabulary) must become generated/validated FROM the contract, not the other way around — this ticket does not flip that direction itself (that's follow-on work once adapters exist), but it must not design the vocabulary relationship as a permanent two-way equality assertion, and must not permanently generate the contract from `vocabulary.py`

## Out of Scope
- Does not modify or reroute the live .claude/workflows/implement-ticket.js
- Does not build the Claude conformance/diff tooling (owned by the Claude conformance adapter ticket)
- Does not implement Codex-side adapters or hooks (owned by the Codex guidance/fixture-capture and Codex replay tickets)
- Does not flip `vocabulary.py` to be generated from the contract, and does not modify `vocabulary.py` itself — this ticket only bootstraps from it and documents the future one-way direction; actually reversing the generation direction is follow-on work for a later ticket once provider adapters consume the contract

## Acceptance Criteria
- [x] agent-orchestration/ exists with contract.yaml, workflows/implement-ticket.yaml, roles/*.yaml, skills.yaml, monitoring-schema.yaml, hook-events.yaml, covering both standard and hotfix tiers
- [x] skills.yaml is created, validated by the same deterministic validator/generator as the rest of the contract, and lists the semantic skill catalog for the first vertical slice — the generated Codex `.agents/skills/` catalog produced by `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE` must trace to entries in this file, not to independently curated content
- [x] workflows/implement-ticket.yaml's phase/agent vocabulary is bootstrap-initialized from tools/agent-monitoring/vocabulary.py's WORKFLOW_PHASES/WORKFLOW_AGENTS, with a test asserting equality while the Claude workflow remains live and vocabulary.py remains the legacy source of truth (this is a one-time bootstrap check, not a claim that vocabulary.py stays canonical forever)
- [x] This ticket's own documentation (plan.md or the contract's own README.md) explicitly states the one-way future direction: the validated contract will drive generated/validated monitoring vocabulary and provider adapters going forward; it does not maintain two independently hand-authored vocabularies, and does not permanently generate the contract from vocabulary.py or any other provider/monitoring implementation module
- [x] Validator raises a named, deterministic error type on an incomplete/malformed contract (mirroring the FixtureValidationError pattern)
- [x] Validator/generator makes zero network calls (verified by an automated test)
- [x] Validator/generator writes zero files outside agent-orchestration/ unless the explicit generation flag is passed (AST- or mock-verified test)
- [x] contract.yaml contains a required `version` field, with the versioning scheme documented and tested in this ticket's plan/investigation artifacts before any provider adapter (Claude conformance, Codex guidance) consumes it

## Related Tickets
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260721-CODEX-REPLAY-PROOF
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-AGENTS-DIR-DISPOSITION
- TCK-20260721-CODEX-CAPABILITY-MATRIX

## Related Docs
- docs/architecture/agent_orchestration_contract.md
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/ai/replay_fixture_spec.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/architecture/agent_orchestration_contract.md
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/ai/replay_fixture_spec.md
- tools/agent-monitoring/vocabulary.py
- docs/agent-monitoring/schema.md
- tools/agent_replay/fixture_envelope.py
- tools/agent_replay/runner.py
- .claude/workflows/implement-ticket.js
- tests/tools/test_validate_agent_monitoring.py

## Assumptions / Open Questions
- Versioning scheme is Proposed-pending per the ADR — this ticket's Plan phase must decide it (e.g. semver vs. date-based) since no existing scheme applies
- Terminal statuses currently live only in implement-ticket.js prose/schema.md with no structured source — roles/*.yaml and terminal-status structuring is new modeling work with no existing source to lift from

## Implementation Notes

Implemented all 11 plan steps as specified, following `staging_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md` exactly. No deviations from the plan required.

**Contract data (`agent-orchestration/`):**
- `contract.yaml` — `version: 1` (int), manifest naming and pointing to the five sibling files, with the versioning scheme decision (simple integer generation counter, one independent counter per file) recorded in a header comment.
- `workflows/implement-ticket.yaml` — 11 phases with `tiers` (`{standard, hotfix}` → `full`/`skipped_event`/`conditional`) bootstrap-copied from `vocabulary.py`'s phase names, plus the new per-phase tier-applicability matrix derived from `implement-ticket.js`'s real branch structure (Investigate/Plan/Review/Architecture-Verify → `skipped_event` for hotfix; Parity → `conditional`/`if_false: skipped_event`; Security-Review → `conditional`/`if_false: conditional_absent`, kept as a distinct enum value from `skipped_event` per the plan's explicit instruction). `agents` list has the 10 real roles, `implement-ticket-orchestrator` excluded.
- `roles/*.yaml` (10 files) — one per real role; `finalizer.yaml` carries `has_agent_file: false` and an `inline_prompt_exception` note (no `.claude/agents/finalizer.md` exists; it's prompted inline in `implement-ticket.js` ~1151-1255).
- `skills.yaml` — 16 entries, one per `.claude/skills/*/SKILL.md` directory, each with `id`/`description`/`workflows`/`roles`; only `implement-ticket` and `create-tickets` carry non-empty `workflows`/`roles` associations (referencing only ids that actually exist elsewhere in this contract today — no dangling references to not-yet-built `workflows/create-tickets.yaml`, etc.).
- `monitoring-schema.yaml` — the three execution-identity fields (`execution_id`/`run_id`/`ticket_id`) copied verbatim from `docs/ai/monitoring_writer_decision.md` §2, no re-derivation.
- `hook-events.yaml` — the two real hook types (`PreToolUse`, `PostToolUse`) confirmed against `.claude/settings.json`.
- `README.md` — documents the versioning scheme and the one-way future-authority direction (contract becomes upstream once adapters exist; `vocabulary.py` stays legacy source of truth for now; bootstrap is one-time, not permanent).

**Validator/generator (`tools/agent_orchestration/`):**
- `errors.py` — `ContractValidationError` (flat, mirrors `FixtureValidationError`) and `GeneratorWriteGuardError` (flat, separate class — not a subclass of the validation error, since they signal structurally different failure classes: malformed data vs. refused write).
- `loader.py` — `load_contract(root: Path) -> ContractBundle` (frozen dataclass), the single validation entry point; reads and validates all six files, raising `ContractValidationError` naming the exact path and field on any missing/malformed required field or non-mapping YAML root.
- `generator.py` — `generate(repo_root, target_dir, *, allow_outside_contract=False)`; validates via `load_contract()` then re-serializes the bundle back out as YAML under `target_dir`. Structural write-guard (`_assert_write_allowed`) does a real `Path.resolve().is_relative_to(...)` containment check before every write — checked before the first file write, so a disallowed target raises `GeneratorWriteGuardError` before any file appears. No network-capable imports/calls anywhere in the package (AST-verified).

**Tests (`tests/agent_orchestration/`, 20 tests, all passing):** `test_bootstrap_vocabulary_equality.py` (value-equality bootstrap check + docstring-framing meta-test), `test_contract_structure.py` (file existence/parseability, tier-matrix fixture comparison, orchestrator-exclusion guard, finalizer inline-prompt-exception guard, versioning field), `test_skills_catalog.py` (stable/unique/identifier-safe ids traceable to real skill directories, schema-distinctness guard), `test_validator_errors.py` (3 table-driven malformed-contract cases), `test_validator_no_network_calls.py` (AST zero-network-calls scan, write-guard refuse/allow-with-flag/allow-inside-without-flag with a positive control, round-trip check, scope-creep guard restricted to `.py`/`.yaml` so README prose mentioning `.codex/` as a concept doesn't false-positive).

Confirmed via `git diff --stat` that `tools/agent-monitoring/vocabulary.py`, `.claude/workflows/implement-ticket.js`, `tools/agent-monitoring/validate.py`, and `.claude/settings.json` are byte-for-byte unchanged.

## Test Summary

- `pytest tests/agent_orchestration/ -v` — 20 passed.
- `pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_agent_monitoring_legacy_reader.py tests/tools/test_codex_capability_diagnostics.py -v` — 45 passed (no regression).
- `pytest tests/agent_replay/ -q` — 25 passed (no regression).
- No behavior-changing `src/` edit was made; `behavior_changed: false`.

## Files Changed

- `agent-orchestration/contract.yaml` (new)
- `agent-orchestration/workflows/implement-ticket.yaml` (new)
- `agent-orchestration/roles/ticket-scoper.yaml` (new)
- `agent-orchestration/roles/investigator.yaml` (new)
- `agent-orchestration/roles/planner.yaml` (new)
- `agent-orchestration/roles/architecture-reviewer.yaml` (new)
- `agent-orchestration/roles/implementer.yaml` (new)
- `agent-orchestration/roles/test-scoper.yaml` (new)
- `agent-orchestration/roles/parity-updater.yaml` (new)
- `agent-orchestration/roles/security-reviewer.yaml` (new)
- `agent-orchestration/roles/done-checker.yaml` (new)
- `agent-orchestration/roles/finalizer.yaml` (new)
- `agent-orchestration/skills.yaml` (new)
- `agent-orchestration/monitoring-schema.yaml` (new)
- `agent-orchestration/hook-events.yaml` (new)
- `agent-orchestration/README.md` (new)
- `tools/agent_orchestration/__init__.py` (new)
- `tools/agent_orchestration/errors.py` (new)
- `tools/agent_orchestration/loader.py` (new)
- `tools/agent_orchestration/generator.py` (new)
- `tests/agent_orchestration/__init__.py` (new)
- `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py` (new)
- `tests/agent_orchestration/test_contract_structure.py` (new)
- `tests/agent_orchestration/test_skills_catalog.py` (new)
- `tests/agent_orchestration/test_validator_errors.py` (new)
- `tests/agent_orchestration/test_validator_no_network_calls.py` (new)

## Completion Summary

Stood up the repo-root `agent-orchestration/` provider-neutral semantic contract (6 required files/dirs, 10 role files) for the `implement-ticket` workflow, bootstrap-initialized its phase/agent vocabulary once (value-equality, one-time-framed) from `tools/agent-monitoring/vocabulary.py`, and built a deterministic, network-free, write-guarded validator/generator under `tools/agent_orchestration/` mirroring the `FixtureValidationError`/AST-scan precedents from `TCK-20260721-CODEX-REPLAY-PROOF`. All 8 acceptance criteria satisfied; 20 new tests plus 70 existing regression tests pass; no production file (`vocabulary.py`, `implement-ticket.js`, `validate.py`, `.claude/settings.json`) was touched; no observable simulation/production behavior changed.
