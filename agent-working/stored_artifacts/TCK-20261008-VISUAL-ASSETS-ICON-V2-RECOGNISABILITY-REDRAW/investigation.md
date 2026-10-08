---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW
artifact_type: investigation
tags: [architecture, testing, hud]
---

# Investigation — TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW

- The catalog's `tool` category holds two items (`repair_kit`, `spirit_lantern`; `data/content/world/items.yaml`): no mining tool, so the pickaxe was the wrong glyph and the wrench is the closest fit (the lantern has no match; flagged for the owner).
- The compliance table found a bug in my own measurement on its planted case (a wide grip made the measure take the pommel for the grip); fixed, and a test pins it. Two other definitions (pendant rows, hole drawn in the outline colour) were corrected after looking at the numbers on the new art; thresholds never changed.
- The blind check is noisy: unchanged icons flip between rounds (the dagger, the uncommon gem, tiers B, D, E). One synonym ("archway") was added after seeing a correct answer scored as a miss; "round" was removed from the bead's synonyms before scoring.
- The ruins stay flagged in free text after four ideas (boot, mountain peaks, wagon cart, "building blocks"); the choice pass names them correctly each time. Slabs and matched bricks under a wall read as a cart or a boot sole; a U-shaped broken top avoids a one-way slope.
- New look-alike pair: common bead vs tiers D and E at 25 XOR px (reported, not changed).
