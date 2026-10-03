---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION
artifact_type: investigation
tags: [architecture, mcp, testing, documentation]
---

# Investigation — TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION

- `search_docs` and `graphify query` return nothing relevant for `visual_assets/`; this follows from direct reads of the landed intake, contracts and boundary test.
- Reusable: `intake.quarantine` (O_NOFOLLOW directory fd, bounded reads, exclusive create, `.tmp-*` temp naming), `intake.service.show` (result load), `catalog.registry` (key check),
  `contracts` (AdoptionRecord, SourceRecord, RevocationRecord already carry the fields the ticket lists), `identities.next_revision`.
- `RevocationRecord` requires `approver_role`, which the ticket's `revoke` signature lacks.
- The current boundary rule lets `drawing.server` import any store module; the ticket asks that it never import the two gate modules.
- The catalog root is a tracked tree: nothing may be written there except by `adopt` and `revoke`; tests use temporary catalog roots (`config.CATALOG_ROOT` is read at call time).
- The human gate limits: a terminal check and a typed id stop accidental and scripted adoption; they do not authenticate the person.
