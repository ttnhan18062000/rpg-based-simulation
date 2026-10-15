---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS
artifact_type: investigation
tags: [architecture, testing, mcp]
---

# Investigation: object markers, reference study (what makes each read at its size)

Method (style guide, 2026-10-08): spec, reference study, owner-approved silhouette sheet, draw, compliance table, blind check, owner gate. References are looked at only (Kenney Tiny Dungeon and 1-Bit Pack, CC0; nothing traced). The specs are in `visual_assets/icons/icon_specs.yaml` (18 new entries, `status: v2`, plus the new `node` family convention).

Decisions the code forced:
- The existing building icons are SIGNATURE OBJECTS, not houses (tankard for the inn, anvil for the blacksmith, coin purse for the store; `icon_specs.yaml` family `building`). The new buildings follow it: healer hut = mortar and pestle, town hall = a charter scroll (option B a bell), mine entrance = a pickaxe (option B a mine cart), watchtower = the tower itself (a tower is already an object).
- A resource node is not a location, so its glyph has NO plate (the new `node` family); a place glyph (nest) sits over the plate like the other `icon.marker.*` keys.
- Today's client draws, for a kind it has no entry for: a white-outlined square with a question mark (buildings, `useCanvas.ts:157-175`), an inset square in the default `#7dd3a0` (nodes, `useCanvas.ts:179-200`, only `herb_patch` has its own colour `#6ee7b7`; the V2 kinds are missing from `RESOURCE_COLORS`), a bullet `#aaa` (places, `GameCanvas.tsx:527`). These are the registry fallbacks.

What makes each read at 12 x 12 / 20 x 20 (and what it must not read as):
- healer_hut: the bowl rim and the diagonal pestle; the green sprig (colour) separates it from a cup or cauldron. Risk: a soup bowl.
- town_hall: A scroll: curled ends and a seal; risk: a letter or map. B bell: flared lip, top loop, clapper; risk: a shrine bell (the obelisk shrine "must not read as a bell").
- mine_entrance: A pickaxe: a curved double-point head on a diagonal haft (the blacksmith is a hammer on an anvil, so a diagonal pointed head differs); B cart: a box on two wheels heaped with ore.
- watchtower: crenellations and a pennant; risk: a chess rook (distractor in the check).
- wood vs berry vs herb vs flower vs cover: separated by silhouette class (stacked discs; round blob with nubs; three upright sprigs; one flower head on a stem; blades). Cover patches: only HEIGHT differs (11, 7, 4 px), by design.
- iron vs silver vein: the weakest pair (see the README of the silhouette folder). Iron is angular with ore nubs on the top edge; silver is smooth with two sparkle nubs.
- crystal_outcrop vs frost_shard_cluster: crystals stand on a rock base in a fan of three; shards radiate from one point with no base.
- spirit_wisp vs candle flame: a teardrop with a curled tail and no stem or holder.
- moon_resin_tree vs the existing resource_grove tree: the grove glyph sits on the plate; the node is slimmer with a pale trunk and an amber drop.
- nest vs boulder blobs: twig ends poking out left and right and egg bumps on top.
