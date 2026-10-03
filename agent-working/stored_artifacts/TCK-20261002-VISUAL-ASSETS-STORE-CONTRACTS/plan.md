---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS
artifact_type: plan
tags: [architecture, schema, testing, documentation]
---

# Plan — TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS

Pure, read-only Python; tests first per module where practical. Order follows the import layering.

1. `errors.py`, `config.py` (true leaves), `identities.py` (imports `errors` only; see deviation D-1).
2. `contracts/base.py` (strict frozen base, `canonical_json`, `parse_record`, enums, `Evidence`, text types), then one module per record.
3. `catalog/registry.py` (duplicate-key + anchor-rejecting YAML loader, validation, `Registry.resolve`); data file with zero keys.
4. Fixtures generated once by a scratch script from dicts through `parse_record`/`canonical_json`, committed as bytes.
5. Boundary test: store layering table, forbidden-import AST rule for `contracts`/`identities`, planted violations.
6. Unit tests under `tests/visual_assets/store/unit/`.
7. Docs and bookkeeping (scope item 9), index update, graph update.

## Deviations from the ticket (reported to the planner)
- D-1: `identities` imports `errors` (its helpers raise `IdentityError`); ticket calls it a stdlib+pydantic leaf.
- D-2: `UtcTimestamp` real-date check is hand-written (no `datetime` import allowed in `identities`).
- D-3: the eight ID types are distinct for static typing (`NewType`) but share one runtime syntax, so cross-assignment
  of same-shaped IDs cannot be rejected at runtime; criteria only require rejection where shapes differ.
- D-4: `scale_class` has no value list in the docs; modelled as a registry-axis value (bounded identifier string).
