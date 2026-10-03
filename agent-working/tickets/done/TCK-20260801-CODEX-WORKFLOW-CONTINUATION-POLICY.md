---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY
phase: done
date: 2026-08-01
tags: [ai, workflows, process-improvement, agent-monitoring, testing]
---

# TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY

## Title
Formalize and safety-review Codex ticket-workflow continuation policy

## Status
DONE

## Tier
standard

## Type
process-improvement

## Priority
P1

## Request Summary
Account for and review the proposed provider-agnostic continuation policy that directs Codex to
continue an already-started ticket workflow through applicable phases until DONE or a genuine hard
gate. Establish its precise boundaries, validation, monitoring, and rollback behavior before it is
accepted into the shared orchestration contract.

## Scope
- Investigate the existing `implement-ticket` gate/return semantics and the Codex adapter's
  generated instruction surface.
- Define an explicit, conservative meaning of a hard gate. It must name and preserve each existing
  terminal condition: `NEEDS_HUMAN_INPUT`, `NEEDS_CHANGES`, `BLOCKED`, `DOD_BLOCKED`,
  `CONFLICTS_DETECTED`, `TAGS_NOT_REGISTERED`, `SECURITY_BLOCKED`, `TESTS_FAILED`, and
  `DOC_STALENESS_BLOCKED`, plus required human decisions, missing authority for live/destructive
  work, and external blockers.
- Ensure the policy cannot authorize scope expansion, a gate-bypass artifact edit, a live provider
  activation, a hook/config change, or a decision that needs user direction.
- Add loader-level structural validation, using the hook-surface-policy loader as the direct
  precedent: typed policy fields, a dedicated bundle field, recognized mode, non-empty instruction,
  and rejection of any `non_gates` entry that overlaps the reserved gate-condition vocabulary.
- Add contract/generator tests that validate the complete policy shape, faithful `AGENTS.md`
  generation, and one non-continuation assertion for every named gate condition.
- Document review, rollback, and monitoring expectations for a continued versus stopped ticket
  workflow.

## Out of Scope
- Implementing or modifying any ticket's feature work, bypassing a workflow gate, or selecting a
  future ticket automatically.
- Enabling a Codex hook, changing `.codex/config.toml`, running a live Codex invocation, or
  writing a real `provider=codex` monitoring record.
- Changing Claude's workflow execution behavior without separate review.

## Acceptance Criteria
- [x] The policy's origin, objective, and non-authorizations are documented in a reviewed ticket
      rather than attributed to an unrelated implementation.
- [x] Hard gates and explicit non-gates are unambiguous and preserve every existing requirement for
      human authority, scope control, and gate integrity; tests cover each named existing terminal
      condition and pin the session's `NEEDS_HUMAN_INPUT` unresolved-questions stop as a precedent.
- [x] Loader-level contract validation rejects a missing/invalid mode, missing/empty instruction,
      malformed non-gates, and every reserved gate-condition value in `non_gates`; the Codex
      renderer faithfully produces only the validated policy text.
- [x] Validation and rendered guidance prove continuation cannot be interpreted as permission to
      cross a failed gate or begin a live/destructive/provider-activation action without explicit
      authority; no runtime enforcement is claimed.
- [x] The resulting operational guidance describes monitoring and rollback/disable behavior, and
      Claude review and explicit user sign-off on the final rendered policy text both approve it
      separately from the pilot-executor ticket.

## Related Tickets
- TCK-20260731-CODEX-PILOT-EXECUTOR (approved separately; does not own this change)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC
- TCK-20260730-PROVIDER-HOOK-POLICY
- TCK-20260731-GATE-BYPASS-HARDENING

## Related Docs
- docs/plans/agent_infrastructure/codex_pilot_executor_review_response_claude.md
- docs/plans/agent_infrastructure/codex_pilot_executor_review_response_codex.md
- docs/plans/agent_infrastructure/codex_workflow_continuation_policy_review_claude.md
- docs/plans/agent_infrastructure/codex_workflow_continuation_policy_actual_diff_correction_claude.md
- agent-orchestration/workflows/implement-ticket.yaml
- agent-orchestration/contract.yaml
- AGENTS.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260731-CODEX-PILOT-EXECUTOR/

## Related Code Areas
- agent-orchestration/workflows/implement-ticket.yaml
- tools/agent_orchestration/loader.py
- tools/agent_orchestration_codex_adapter/generator.py
- tests/agent_orchestration/test_contract_structure.py
- tests/agent_orchestration/test_validator_errors.py
- tests/agent_orchestration_codex_adapter/test_generator_traceability.py

## Assumptions / Open Questions
- The policy must apply only after a ticket workflow has begun; it does not choose a next ticket.
- A workflow's declared gate semantics remain authoritative over this general continuation policy.
- Whether continuation policy belongs in the workflow schema or an adapter-specific policy document
  must be resolved during investigation and architecture review.
- The pre-existing 39 passing orchestration tests are additive-compatibility evidence only; they do
  not exercise or validate `continuation_policy` and must not be cited as policy coverage.

## Implementation Notes
Implemented the reviewed contract/guidance boundary: the terminal-status validator is now neutral
and re-exported by the Claude adapter, `ContractBundle` validates terminal statuses and optional
continuation policy, the generator materializes terminal statuses, and Codex guidance renders only
validated policy. Claude independently approved the corrected actual diff, and the user explicitly
approved the final rendered text; the policy remains guidance-only and authorizes no live action.

## Test Summary
Scoped regression: **122 passed, 2 failed**. Both failures are the known, pre-existing brittle
hardcoded line-number assertions in `tests/agent_orchestration_claude_adapter/test_terminal_status_
conformance.py` and `test_terminal_status_extractor.py` (`[1234, 1246]` expected vs current
`[1344, 1356]`); they are outside this ticket by explicit review instruction. The new generated
contract round-trip regression passes independently.

## Files Changed
- `agent-orchestration/{contract.yaml,README.md,terminal-statuses.yaml,workflows/implement-ticket.yaml}`
- `tools/agent_orchestration/{loader.py,generator.py,terminal_statuses.py}`
- `tools/agent_orchestration_claude_adapter/terminal_status_loader.py`
- `tools/agent_orchestration_codex_adapter/generator.py`
- `AGENTS.md`
- `tests/agent_orchestration/{test_contract_structure.py,test_validator_errors.py}`
- `tests/agent_orchestration_codex_adapter/test_generator_traceability.py`
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-309`)
- `staging_artifacts/TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY/`

## Completion Summary
Validated and rendered the provider-neutral Codex continuation guidance with a neutral
terminal-status schema authority, full non-DONE terminal reservation, generated-contract
round-trip support, and explicit no-authority wording. Claude approved the actual diff and the
user approved the exact rendered policy text; no hook, config, live Codex, or provider-bearing
monitoring action was enabled.
