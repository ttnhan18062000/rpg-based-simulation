---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION
artifact_type: plan
tags: [architecture, mcp, testing, documentation]
---

# Plan — TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION

1. Contract additions (additive, schema_version stays 1): `AdoptionRecord.intake_hash`, `SourceRecord.adoption_hash`; `GateError`; regenerate fixtures.
2. New store layers with `STORE_ALLOWED` rows: `records` (safe read of catalog records), `catalogwrite` (all-or-nothing multi-file publish with rollback), `adoption`, `revoke`, `audit`.
3. `adopt` (all refusals before any write, then `confirm`, then publish), `revoke`, `is_build_eligible`, `audit_chain`.
4. CLI `adopt` / `revoke` (terminal on stdin, typed id) and extended `list` / `show`.
5. Boundary rule: no drawing module imports `store.adoption` or `store.revoke` (planted test).
6. Tests (CI, temp catalog roots, synthetic fixtures), docs, ticket close.

## Where the ticket and reality differ (reported to asset-planner before building)
- "edited approver" cannot be detected: nothing binds the adoption record's content. Fix: `intake_hash` in the adoption record and `adoption_hash` in the source record (limit stated: a consistent edit of both is not caught by the catalog alone).
- No default `source_asset_id`: `src-` + 16 hex of sha256(candidate_id). `adopt` takes an explicit `registry` so fixtures are testable and production refuses `fixture.*`.
- `revoke` needs an approver role (the contract requires it).
- Planner item carried from ticket 2: `adopt` refuses an Evidence marker as `licence_evidence_ref`.
