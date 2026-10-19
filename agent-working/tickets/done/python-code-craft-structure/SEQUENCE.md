# Implementation Sequence — python-code-craft-structure

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order. Filed 2026-10-04 by codebase-implementer from
`docs/plans/codebase_health/python_code_craft_m5_structure_ticket_brief.md` (codebase-planner).

`TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC` is scope-only and is not in the order.

## Order

1. TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT  (no deps; its layer column feeds 2 and 4)
2. TCK-20261004-PACKAGE-REGISTRY-VALIDATOR  (depends on: 1)
3. TCK-20261004-AST-GREP-RULE-PACK-ADVISORY  (independent; may run alongside 1 and 2; the flip ticket already carries the `ast_grep` exclusion; this ticket verifies it matches the implemented tool key)
4. TCK-20261004-IMPORT-LINTER-EVALUATION  (depends on: 2; report only)

Every ticket: no `src/` diff, nothing blocking, M4 soak rows untouched.

Follow-up filed by ticket 2: TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING (BLOCKED until its soak ends; dates written at the validator's merge).

Follow-up filed 2026-10-05 by the import-linter adoption batch: `TCK-20261004-IMPORT-LINTER-ADOPTION` is DONE (2026-10-05, PR #351; moved to `done/`); it filed `TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT` (BLOCKED until a two-week soak from its merge; dates written at merge).
