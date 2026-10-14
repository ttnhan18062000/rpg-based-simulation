---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC
artifact_type: investigation
tags: [architecture, hud, testing]
---

# Investigation — TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC

- 22 keys = 5 locations + 5 buildings + 3 classes + 3 rarity badges + 6 item families. Fallbacks read from the UI: LOCATION_TYPE_ICONS emoji labels, BuildingPanel and ClassHallPanel Lucide icons (the class hall has none), RARITY_COLORS, item_type text.
- `store verify` stays ok after registering keys; only the fresh-export guards and the pinned registry facts break (as for rc-0006).
- The icondraft freshness guard ignores registry_hash and needed no change.
