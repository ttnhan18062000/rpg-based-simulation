# Implementation Sequence — python-code-craft-agent-integration

Filed 2026-10-04 by codebase-implementer from `docs/plans/codebase_health/python_code_craft_m6_agent_integration_ticket_brief.md` (codebase-planner).
`TCK-20261004-PYTHON-CODE-CRAFT-AGENT-INTEGRATION-EPIC` is scope-only and is not in the order.

## Order

1. TCK-20261004-EXEMPLAR-MODULES  (no deps)
2. TCK-20261004-REVIEW-RUBRIC  (no deps; docs-only, no plan.md round trip)
3. TCK-20261004-EDIT-RATCHET-HOOK  (no deps; owner confirms the settings.json diff before commit)
4. TCK-20261004-CODE-CRAFT-SKILL  (depends on 1, 2, 3; owner confirms the implementer.md diff before commit)
5. TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT  (independent)

Every ticket: no `src/` diff, nothing blocking. Re-check PR #314 does not touch the `.claude` files before the push.
