---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY
artifact_type: plan
---

# Plan — TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY

## Decision

Keep continuation policy as an optional, provider-neutral field of
`workflows/implement-ticket.yaml`, but make it a validated contract object—not free-form renderer
input. Reuse the existing terminal-status schema loader as the single authority by extracting it
to the neutral orchestration package and having the Claude adapter import/re-export it. The neutral
`ContractBundle` will contain both the validated terminal vocabulary and continuation policy; the
Codex renderer will consume only that validated value. The policy applies only within an already
selected ticket invocation. It is guidance, not a runtime state machine: it cannot alter terminal
returns, select future work, or grant authority.

## Ordered implementation steps

1. Make the existing terminal-status validator provider-neutral without duplicating its schema.

   - Extract or move the strict parsing/validation currently in
     `tools/agent_orchestration_claude_adapter/terminal_status_loader.py` to
     `tools/agent_orchestration/`; preserve the Claude adapter through an import/re-export or
     equivalent one-authority arrangement. The neutral loader must never import a provider adapter.
   - Have `tools/agent_orchestration/loader.py` reuse that one validator and add the validated
     terminal-status vocabulary to `ContractBundle`; update `tools/agent_orchestration/generator.py`
     to retain it when materializing the contract.
   - Add `terminal-statuses.yaml` to `agent-orchestration/contract.yaml` with
     `terminal_status_schema_version`, update README layout/versioning text, and bump
     `workflow_version` because continuation policy adds governed workflow semantics. Record why
     the policy remains optional for backward-compatible loading and test absence as no render.

2. Add a strict continuation-policy model.

   - Define a small immutable `ContinuationPolicy` model (or equivalently constrained value) with
     exactly: `mode`, `instruction`, `non_gates`.
   - Require `mode == "continue_until_terminal_or_hard_gate"`; require a non-empty string
     instruction; require `non_gates` to be a non-empty list of non-empty strings.
   - Normalize candidates case-insensitively with hyphen/space/underscore equivalence and reject
     any entry that overlaps **every** terminal status other than `DONE`. This includes the nine
     Claude-required regression values and `SCOPE_AGENT_FAILED`, `DATA_RUNS_CLEAN_FAILED`,
     `PARITY_INCOMPLETE`, `FINALIZE_INCOMPLETE`, and `EPIC_SCOPED`.
   - Keep `continuation_policy` optional only for backward-compatible contract loading; when it is
     present, malformed content fails closed with `ContractValidationError` naming the workflow
     file and field. The current real contract must be valid.

3. Render only the validated policy and clarify authority bounds.

   - Change `tools/agent_orchestration_codex_adapter/generator.py::build_agents_md()` to consume
     the validated bundle continuation-policy field, rather than `workflow.get()` free-form data.
   - Render the approved text plus exact terminal semantics: all 15 declared terminal statuses end
     the current invocation; `DONE` and `EPIC_SCOPED` are terminal completion outcomes, while every
     other status is a stop/gate outcome. No scope expansion, gate-evidence editing, ticket
     selection, or live/destructive/provider activation authority follows from continuation.
   - Regenerate `AGENTS.md` only through the adapter after validation. Keep `.agents` skill files,
     `.claude`, `.codex/config.toml`, hooks, and live execution untouched.

4. Add focused tests before accepting the existing diff.

   - Extend `tests/agent_orchestration/test_validator_errors.py` with copied-contract mutations for
     missing/invalid policy fields and parameterized reserved-status overlap failures.
   - Extend `tests/agent_orchestration/test_contract_structure.py` with real-contract policy,
     terminal-vocabulary, required-nine-subset, and all-non-DONE-reserved assertions.
   - Extend `tests/agent_orchestration_codex_adapter/test_generator_traceability.py` with exact
     temporary `AGENTS.md` policy rendering and explicit-boundary assertions. Tests must not invoke
     Codex or depend on a real `AGENTS.md` write.
   - Extend existing Claude terminal-schema/conformance tests to prove the extraction preserves
     current behavior. Add a narrow contract/rendering assertion that all 15 statuses end an
     invocation; do not claim runtime enforcement or build a second workflow executor.

5. Document operations and record the review evidence.

   - Update `agent-orchestration/README.md` and, if needed, the relevant `docs/ai/` guidance to
     distinguish ordinary safe progress, terminal completion, and terminal gate outcomes; document
     how the policy can be removed by omitting it and regenerating `AGENTS.md` (rollback).
   - Add a narrow INFRA parity entry only if the Parity phase judges the orchestration behavior
     contract to be a new durable agent-tooling behavior. No simulation parity entry is applicable.
   - Record provider-omitted workflow monitoring through the existing scripts only. Do not imply a
     Codex execution occurred.

6. Enforce the human approval boundary before closure.

   - After technical architecture review, implementation, tests, parity, and Claude’s actual-diff
     review, present the exact final rendered `AGENTS.md` continuation section to the user.
   - Do not mark Verify READY_TO_CLOSE, move the ticket, or treat the quarantine as accepted until
     the user explicitly approves that text. A rejection or requested wording change is a genuine
     hard gate, not an invitation to silently revise or continue.

## Scope guards

- Do not change `.claude/workflows/implement-ticket.js`; its established terminal returns remain
  the operational authority being protected.
- Keep the Claude JS byte-identical and run existing Claude terminal-schema/conformance tests;
  document that shared continuation metadata is consumed only by the Codex renderer today.
- Do not enable hooks, alter `.codex/config.toml`, invoke Codex, set live/consent variables, or
  write real `provider=codex` monitoring records.
- Do not select a next ticket or use continuation to bypass a failed gate, unresolved question,
  security review, test failure, documentation gate, or human authorization decision.
- Keep the existing three-file diff quarantined until this plan is architecture-approved.

## Acceptance-criteria map

| Acceptance criterion | Steps | Evidence |
| --- | --- | --- |
| Origin and non-authorizations are documented | 5–6 | Ticket, review records, rendered guidance |
| All terminal outcomes end the invocation; only non-completion outcomes are gates | 1–2, 4 | Parametrized loader and vocabulary tests |
| Complete validation and faithful renderer | 2–4 | Negative validator cases + temp render test |
| No live/destructive/provider authority | 3–4 | Boundary assertions and unchanged-surface checks |
| Monitoring, rollback, Claude review, user sign-off | 5–6 | Docs, review response, explicit user approval |
