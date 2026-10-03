---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS
artifact_type: investigation
tags: [architecture, schema, testing, documentation]
---

# Investigation — TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS

- `search_docs` and `graphify query` returned only unrelated world-assembly material; `visual_assets/` is not covered
  by the graph's relevant communities. Follow-up reads: `test_boundaries.py`, `docs/assets/store_contract.md`, the
  ADR, the plan README, proposal 9.6, the INIT ticket's staging artifacts.
- Existing boundary checker is a pure function over (path, source) with a `DRAWING_ALLOWED` table; the store only has
  a generic "must not import drawing" rule. Extension point: add `STORE_ALLOWED` and the AST forbidden-import rule.
- pydantic 2.12.5, PyYAML 6.0.2, Python 3.13 are present; neither Pillow nor numpy is used.
- `strict=True` + Python-dict validation rejects lists for tuple fields, so every record is parsed from JSON bytes
  (YAML registry is converted to JSON bytes first).
- Proposal 9.6 also lists quarantine/revocation state and animation metadata in the package; the ticket's minimum
  fields omit them (`declared_limitations` covers unsupported features). Not added; reported.
