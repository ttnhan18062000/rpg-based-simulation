# V2 Intentional Divergences Register

This document tracks every intentional gameplay or architectural difference between legacy `src` and `src`. Every item listed here must be backed by a test in `tests/parity/` marked with `@pytest.mark.intentional_divergence(id="DIV-XXX")`.

| ID | Checklist Refs | System | Reason | Expected Behavior | Test Path |
|---|---|---|---|---|---|
| DIV-001 | REQ-043 | Substrate | State Isolation | V2 uses immutable snapshots for worker decision-making to prevent non-deterministic side effects. | `tests/parity/test_isolation_boundary.py` |
| DIV-002 | REQ-115 | Town | Real Travel | V2 replaces cosmetic town teleports with real spatial navigation and town tiles. | `tests/parity/test_town_resolution_parity.py` |
| DIV-003 | REQ-068 | Spatial | Manhattan Priority | V2 strictly enforces Manhattan distance as the canonical spatial metric for all RPG systems. | `tests/parity/test_movement_parity.py` |

## Guidelines for Adding Divergences
1. **Concrete Reason**: Must explain *why* the divergence exists (e.g., performance, determinism, architectural purity).
2. **Test Backing**: Must have a test that asserts the divergence, not just ignores it.
3. **Checklist Mapping**: Must reference the affected items in the parity ledger.
