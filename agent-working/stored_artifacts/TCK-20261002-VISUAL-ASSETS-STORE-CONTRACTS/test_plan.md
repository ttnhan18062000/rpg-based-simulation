---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS
artifact_type: test_plan
tags: [architecture, schema, testing, documentation]
---

# Test plan — TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS

Location `tests/visual_assets/store/unit/`; no Aseprite; runs in the existing CI `tests/visual_assets` step.

| Area | Tests |
|---|---|
| identities | accept canonical, reject case/whitespace/empty/over-length/separators/`..`/trailing newline; sibling shapes; hash types not interchangeable; revision helpers incl. `r0000`, `r9999`; real-date timestamps (leap years) |
| records | per record type: round trip both directions on committed fixtures; rejects unknown/missing field, duplicate key (top + nested), wrong record_type, schema_version 2, oversize, invalid UTF-8, NaN/Infinity |
| handoff | assertion literal required; file-name allowlist; separators/`..` rejected |
| structure | field walk: no `metadata`/`extra`/`notes`, no unconstrained dict/Any; release manifest has no `active`/`current` field |
| cross-field | parent None iff `r0001`; unique release keys; WITHDRAWN licence not adoptable; PASSED/QUARANTINED vs findings |
| registry | duplicate YAML key, anchors, missing alias target, alias==key, chain, fixture namespace, over-bounds, zero-key committed file, `resolve` unknown registers nothing |
| boundaries | store layering table, forbidden-import AST rule, unknown layer, config-as-module rule, each with a planted violation |
