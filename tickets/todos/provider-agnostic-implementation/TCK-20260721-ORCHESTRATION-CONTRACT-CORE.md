---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-ORCHESTRATION-CONTRACT-CORE
phase: open
date: 2026-07-21
tags: []
---

# TCK-20260721-ORCHESTRATION-CONTRACT-CORE

## Title
Canonical contract core and validator for implement-ticket

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Stand up the versioned agent-orchestration/ semantic contract (contract.yaml, workflows/implement-ticket.yaml, roles/*.yaml, monitoring-schema.yaml, hook-events.yaml) as the one authoritative description of phases, terminal statuses, roles, artifacts, and gates for the first vertical slice, plus a deterministic, network-free validator/generator that fails clearly on malformed definitions and never touches provider files except through an explicit generation command. This matters because the ADR already decided YAML+generated-Python validation with the repo-root agent-orchestration/ as the source spec, and the Provider-Adapter Boundary bars adapters from redefining phases/statuses/gates/artifacts.

**Corrected per Codex review (2026-07-22):** the original AC treated `tools/agent-monitoring/vocabulary.py` as a permanent upstream authority the contract must stay generated-from-or-equal-to forever. That reverses the ADR's own Source Ownership decision (the contract, not `vocabulary.py`, is the eventual canonical source). The corrected approach is a one-time bootstrap, not a permanent binding — see the revised Scope/AC below.

## Scope
- Create agent-orchestration/ directory with contract.yaml, workflows/implement-ticket.yaml, roles/*.yaml, monitoring-schema.yaml, hook-events.yaml covering standard and hotfix tiers
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
- [ ] agent-orchestration/ exists with contract.yaml, workflows/implement-ticket.yaml, roles/*.yaml, monitoring-schema.yaml, hook-events.yaml, covering both standard and hotfix tiers
- [ ] workflows/implement-ticket.yaml's phase/agent vocabulary is bootstrap-initialized from tools/agent-monitoring/vocabulary.py's WORKFLOW_PHASES/WORKFLOW_AGENTS, with a test asserting equality while the Claude workflow remains live and vocabulary.py remains the legacy source of truth (this is a one-time bootstrap check, not a claim that vocabulary.py stays canonical forever)
- [ ] This ticket's own documentation (plan.md or the contract's own README.md) explicitly states the one-way future direction: the validated contract will drive generated/validated monitoring vocabulary and provider adapters going forward; it does not maintain two independently hand-authored vocabularies, and does not permanently generate the contract from vocabulary.py or any other provider/monitoring implementation module
- [ ] Validator raises a named, deterministic error type on an incomplete/malformed contract (mirroring the FixtureValidationError pattern)
- [ ] Validator/generator makes zero network calls (verified by an automated test)
- [ ] Validator/generator writes zero files outside agent-orchestration/ unless the explicit generation flag is passed (AST- or mock-verified test)
- [ ] contract.yaml contains a required `version` field, with the versioning scheme documented and tested in this ticket's plan/investigation artifacts before any provider adapter (Claude conformance, Codex guidance) consumes it

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

## Test Summary

## Files Changed

## Completion Summary
