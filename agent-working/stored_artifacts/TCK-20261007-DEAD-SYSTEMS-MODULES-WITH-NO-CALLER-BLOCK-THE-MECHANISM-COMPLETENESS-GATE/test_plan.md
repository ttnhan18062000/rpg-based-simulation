---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE
artifact_type: test_plan
tags: [world, engine]
---

# Test Plan — TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE

- Reachability: the four-kind table in investigation.md, re-run at the branch tip before the final SHA.
- `python3 -m tools.mechanism_registry.mechanism_registry_completeness_check` — unbound list recorded in the ticket.
- Pins: `tests/unit/tools/test_mechanism_registry_completeness_check.py` (targets 65 to 63, unbound 7 to 5, and the shim example moved from chests to market), `tests/unit/tools/test_mechanism_state_caller_check.py` (shim fixture moved to market).
- `tests/architecture/test_legacy_enum_usage_boundaries.py` (allowlist line removed), `tests/unit/social/test_appraisal_logic.py`, `tests/refactor/test_import_compatibility.py`, `tests/refactor/test_public_facades.py`.
- `make mechanism-registry-validate`, `make mechanism-state-caller-check`, html `--check`.
- Hash neutrality: the batch `paired --neutral` run (the deleted code has no caller, so no tick can reach it).
