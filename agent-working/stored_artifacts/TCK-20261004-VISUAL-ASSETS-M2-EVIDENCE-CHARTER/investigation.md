---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M2-EVIDENCE-CHARTER
artifact_type: investigation
tags: [architecture, documentation, testing]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-M2-EVIDENCE-CHARTER

Read: `02_synthetic_contract_harness_plan.md`, proposal section 17 (`AM-C02` and the gate definitions), the Python and frontend test files named in the charter, the committed fixtures, `.github/workflows/test.yml` for the CI lanes.

Findings that shaped the allowed conclusions:
- A run today is `BLOCKED` as a whole: `AM-M1` is not `PASS`, the charter is `DRAFT`, and there is no implementation authorization.
- Nothing resolves `variant_axes`, so variant precedence (`AM2-W01`/`W03`) has no fixture.
- The store's unknown-key `RegistryError` message echoes the caller's key, and no test shows diagnostics stay bounded for hostile input.
- The client manifest reader bounds entries, details and dimensions but not input text length; Python's `parse_record` bounds bytes first. So "reject before allocation" is shown for Python only.
- No cache exists, so cache keys and disposal (`AM2-W05`) are untested; no test shows a prior working snapshot survives an incompatible manifest (`AM2-W06`).
- Origins, redirects and MIME (`AM2-W07`) have no tests because under Profile A the client fetches only its build's files; the client does not recompute the pixel hash.
- The rehearsal fixtures are committed, and no test shows synthetic state can be removed without residue (`AM2-W10`).
- The pilot fixture is real-key material and is excluded from `AM-M2`; tests needing Aseprite are local-only and excluded.
