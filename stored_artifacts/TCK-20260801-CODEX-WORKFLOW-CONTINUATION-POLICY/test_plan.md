---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY
artifact_type: test_plan
---

# Test Plan — TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY

## New coverage

1. **Real contract acceptance.** `load_contract()` returns a validated continuation-policy field
   and asserts the recognized mode, non-empty instruction, and exact approved non-gate list.
2. **Malformed-policy rejection.** Starting from a copied contract, mutate each of: absent policy,
   non-mapping policy, missing/invalid mode, absent/blank/non-string instruction, absent/non-list/
   empty/non-string/blank `non_gates`. Each must raise `ContractValidationError` naming the
   workflow path and affected field.
3. **Reserved-status rejection.** Parameterize every terminal-status value other than `DONE` as a
   normalized/case-varied `non_gates` entry and prove loader rejection. Include the nine statuses
   explicitly required by Claude as named regression cases: `NEEDS_HUMAN_INPUT`, `NEEDS_CHANGES`,
   `BLOCKED`, `DOD_BLOCKED`, `CONFLICTS_DETECTED`, `TAGS_NOT_REGISTERED`, `SECURITY_BLOCKED`,
   `TESTS_FAILED`, and `DOC_STALENESS_BLOCKED`.
4. **Terminal semantics and vocabulary completeness.** Assert all 15 values in
   `terminal-statuses.yaml` end the current invocation; assert `DONE` and `EPIC_SCOPED` are
   completion outcomes and every other declared value is a stop/gate outcome. Assert every
   non-DONE value is reserved by validation and the required nine are a subset. This prevents a
   future terminal outcome from silently becoming a permitted non-gate.
5. **Renderer fidelity.** Render to a temporary target and assert `AGENTS.md` includes the exact
   validated instruction and list in order, contains a clear policy heading, and does not render an
   optional/free-form invalid mapping.
6. **Guidance-only non-authorization.** Assert generated guidance names that continuation applies
   only to the current invocation and does not override terminal outcomes, required human decisions,
   scope control, or separate live/destructive authority. This is a textual contract test, not a
   runtime-enforcement claim.
7. **Single-authority/provider regression.** Run existing Claude terminal-status loader/extractor
   schema and conformance tests, plus orchestration loader, contract-structure, Codex-adapter
   traceability, workflow-meta-conformance, and current-run-sidecar tests. Assert the Claude JS
   stays byte-identical and only Codex guidance consumes the new declarative field.

## Commands

```bash
PYTHONPATH=.:tools .venv/bin/python -m pytest -q \
  tests/agent_orchestration/test_contract_structure.py \
  tests/agent_orchestration/test_validator_errors.py \
  tests/agent_orchestration_codex_adapter/test_generator_traceability.py \
  tests/tools/test_workflow_meta_conformance.py \
  tests/tools/test_current_run_sidecar_orchestrator.py
```

Run the generated-guidance test after all negative loader cases. No test may invoke Codex, modify
`.codex/config.toml`, register hooks, set consent/live-append environment variables, or append a
real provider-bearing Codex monitoring record.

## Acceptance-criteria mapping

| Ticket criterion | Tests |
| --- | --- |
| Reviewed origin and non-authorizations | Investigation/plan references + generated non-authorization text test |
| All terminal outcomes end; named gates remain stops | 3–4 |
| Loader validation and faithful renderer | 1–2, 5 |
| No live/destructive/provider activation authority | 6 + containment check |
| Monitoring/rollback and final human sign-off | Documentation review; manual closure gate |
