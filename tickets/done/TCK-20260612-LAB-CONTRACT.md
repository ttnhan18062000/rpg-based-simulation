---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260612-LAB-CONTRACT
phase: done
date: 2026-06-12
tags: [documentation, contract, lab, agentic, compliance]
---

# TCK-20260612-LAB-CONTRACT

## Title
Write engine contract for src/lab/ agentic simulation lab (SCENARIO-* compliance namespace)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P0

## Request Summary
`src/lab/` is an 18-file module (orchestrator.py, session.py, mutation_orchestrator.py, guardrails.py, metamorphic.py, audit.py, comparison.py, context.py, mutation.py, registry.py, repository.py, request.py, schema.py, store.py, validator.py, workflows.py, cli.py) implementing the full agentic simulation lab. orchestrator.py carries Compliance IDs SCENARIO-012, SCENARIO-013, SCENARIO-014, SCENARIO-015. The only existing doc is the historical `docs/observability/phase_14_agentic_lab.md` — a phase report, not a contract. Agents extending the lab (mutation pipeline, approval workflow, guardrails) have no contract to enforce against, and the SCENARIO-* namespace is unverifiable.

## Scope
- Create `docs/lab/` folder with `lab_contract.md`
- Contract must cover: lab session lifecycle (creation, execution, completion, expiry), mutation pipeline (how mutations are generated, validated, and applied), safety guardrails contract (what guardrails.py enforces and what triggers rejection), metamorphic testing rules, audit trail requirements, human-gated approval flow
- Map all SCENARIO-* Compliance IDs found in src/lab/ to their source file:line
- Declare authoritative status of lab state, resource budget (session limits, storage ceiling), retention/overflow policy
- Pass frontmatter validation and add to parity ledger
- Run `make docs-registry`

## Out of Scope
- Changing source code in `src/lab/`
- Writing new lab tests
- Documenting the agentic workflow orchestration (that is in docs/ai/)

## Acceptance Criteria
- [ ] `docs/lab/lab_contract.md` exists with valid frontmatter (`status: authoritative`, `layer: simulation`, `authority: P1`, `last_verified: 2026-06-12`)
- [ ] Session lifecycle section covers: creation → execution → completion/expiry with state transitions
- [ ] Guardrails section enumerates each guardrail enforced by guardrails.py (one rule per known rejection condition)
- [ ] All SCENARIO-* Compliance IDs found in `src/lab/` are listed with `source_file:line` as v2_evidence
- [ ] Resource budget declared: max sessions, max storage per session, retention policy when store overflows
- [ ] `python3 tools/validate_frontmatter.py docs/lab/` exits 0
- [ ] At least one parity ledger entry added pointing to the new contract
- [ ] `docs/REGISTRY.yaml` updated after `make docs-registry`

## Related Tickets
- None in this batch.

## Related Docs
- docs/observability/phase_14_agentic_lab.md (historical — reference only)
- docs/engine/engineering_playbook_m10.md
- docs/parity_ledger/infrastructure.yaml
- docs/parity_ledger/schema.json

## Related Stored Artifacts
- None.

## Related Code Areas
- src/lab/orchestrator.py
- src/lab/session.py
- src/lab/mutation_orchestrator.py
- src/lab/guardrails.py
- src/lab/metamorphic.py
- src/lab/audit.py
- src/lab/workflows.py
- src/lab/schema.py

## Assumptions / Open Questions
- Whether lab session state participates in the authoritative simulation hash or is isolated shadow state must be confirmed from orchestrator.py before writing
- Full list of SCENARIO-* IDs beyond 012-015 unknown — scan all 18 files before writing

## Implementation Notes
Compliance namespaces broader than ticket assumed: also covers METAMORPHIC-RULE-*, MUTATION-ENGINE-*, MUTATION-ORCHESTRATOR-*, BALANCE-COMPARE-*. Lab state confirmed as shadow state in data/lab_sessions/ — not in AuthoritativeState hash. Human approval gates documented for GENERATION, EXECUTION_SUPPORT, ENHANCEMENT stages. Parity ledger INFRA-186 added.

## Test Summary
python3 tools/validate_frontmatter.py docs/lab/ — OK: 1 file, no violations. make docs-registry — simulation layer now has 1 doc, no errors.

## Files Changed
- docs/lab/lab_contract.md (created)
- docs/parity_ledger/infrastructure.yaml (INFRA-186 appended)

## Completion Summary
Wrote full agentic lab contract covering all compliance namespaces (SCENARIO-*, METAMORPHIC-RULE-*, MUTATION-ENGINE-*, MUTATION-ORCHESTRATOR-*, BALANCE-COMPARE-*), session lifecycle state machine, guardrails hard/soft stops, mutation pipeline, metamorphic testing rules, and storage budget.
