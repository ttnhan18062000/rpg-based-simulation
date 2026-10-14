---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS
artifact_type: investigation
tags: [architecture, hud, documentation]
---

# Investigation — TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS

- Loaded `CatalogRepository("data/content")`: 37 items, first categories material 19, weapon 10, trinket 2, armor 2, tool 2, consumable 2; rarity common 13, uncommon 12, rare 11, legendary 1; equipment_slot and use_kind unset on all.
- Frontend: RARITY_COLORS has common, uncommon, rare only; item_type is text in LootPanel, InspectPanel, BuildingPanel.
- Catalog building definitions (9) differ from the UI building types (6).
- `store verify` rejects any file in catalog/definitions other than its own.
