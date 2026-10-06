---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES
artifact_type: investigation
tags: [architecture, hud, testing]
---

# Investigation — TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES

- Ticket vs landed: the ticket said the registry hash change matters only for a new rc; in fact `test_pilot_fixture` and `test_terrainset_fixture` fresh-export rc-0004/rc-0005 and fail with `registry_mismatch` once any key is added. Reported to asset-planner; user chose "Assemble rc-0006" by my own blocking question.
- `release` assembles every adopted slot, so no forest-only candidate on the new registry can exist; the pilot guard needed a planner ruling.
- `fallback.ts` knows families item/terrain/ui only (generic "?" otherwise): no change here.
- Draft tooling 16x16 assumption: not examined here (child 5).
