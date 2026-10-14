---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-THEME-FIT
artifact_type: investigation
tags: [architecture, testing, hud]
---

# Theme-fit audit of all 36 icons (D21: medieval fantasy plus magic, nothing modern), 2026-10-08

Three inputs, as the owner asked ("also check other icons, the description or something"): the **pixels** (the era question, one fresh agent, sonnet, on the 36 adopted drawings; plus a second agent on the four proposed revisions), the **spec text** (every `icon_specs.yaml` description checked against the modern-object list by the loader), and the **registry key descriptions and fallback text**.
Caveat: the era question is a weak instrument on its own: the agent answered "cannot tell" for 20 of 36 and "medieval or fantasy" for 16 and never "modern"; it only flags when the object it NAMES is a modern one (a wrench, a toolbox, a warning triangle), which is why the scoring also checks the named object.

## Offenders and borderline cases

| Icon | Verdict | Reason |
|---|---|---|
| `icon.item.tool` | OFFENDER | the adopted wrench is a modern mechanic's tool (era answer flagged by the object named); replaced by hammer and tongs (item 5 of this ticket) |
| `icon.building.hero_house` | OFFENDER | white walls, blue square glass windows, a red roof and a chimney read as a modern suburban house (the era answer could not say: "a small red house"); the spec says only "cottage" and does not ask for timber, thatch or small windows; redraw as a timber-framed cottage (needs the planner's and the owner's say-so) |
| `icon.status.frame_debuff` | OFFENDER | an inverted red triangle with a down arrow reads as a modern road-sign symbol (era answer: "a red warning triangle"; free text in four earlier rounds: "red warning triangle"); an adopted key-set slot; options: a different frame shape (the registry description even says "spiked frame"), or keep as a neutral UI glyph by the owner's choice |
| `icon.class.ranger` | registry text only | the longbow art is medieval; the registry fallback names today's UI icon `Lucide Crosshair` (a gun-sight): a modern object, but it is the UI's fallback, not the art; change belongs to the UI, not the art |
| `icon.building.inn` | borderline, keep | brown opaque body with a ring handle and foam: reads a tankard; the era answer said "medieval or fantasy: a beer mug"; the planner's first pass (glass mug) is overturned on the pixels; a wooden stave pattern would make it unmistakable (optional) |
| `icon.building.class_hall` | borderline, keep | an open book with ruled text lines and a bookmark; era answer medieval ("an open spellbook"); reads a hand-written tome; fine |
| `icon.building.store` | fine, note | `Lucide Store` fallback (a shop front with an awning) is a modern pictogram; the coin purse art is medieval |

**The planner's first pass, confirmed or overturned:** wrench confirmed (offender, replaced anyway); hero house confirmed (white walls and blue glass windows); inn mug **overturned** (the drawn mug is an opaque brown tankard, the era answer is medieval; borderline, keep). **Found by the audit and not on the first pass:** the adopted debuff frame (a red warning-triangle road sign) and the registry fallback `Lucide Crosshair` for the ranger (UI only).

## Spec text

All 36 specs pass the loader's guard (no modern word in the describing fields). The hero house spec is the one whose TEXT lets the offender through: it asks for "roof, walls, door, two windows, chimney" and never names timber framing, thatch, tiles or small windows. A theme-fit spec for it would say: a timber-framed cottage, thatched or tiled roof, small shuttered or leaded windows.

## Registry descriptions and fallbacks (not the art)

The fallback sentences name today's UI pictograms: the Lucide set (Hammer, Shield, Home, Bed, Store, Wand2, Crosshair, Sword) and emoji. They are UI chrome that the icons are meant to replace, not in-world art, so they are listed for information. The only modern OBJECT among them is `Lucide Crosshair` (ranger). No registry description names a modern object for the art itself.

## All 36

| Icon | Spec status | Era question answer (pixels) | Spec theme | Registry fallback | Audit |
|---|---|---|---|---|---|
| `icon.building.blacksmith` | adopted | medieval or fantasy: a blacksmith anvil and hammer | medieval: a blacksmith's anvil with a raised hammer | today's Lucide Hammer icon (#f59e0b) plus the building name  | ok |
| `icon.building.class_hall` | v2 | medieval or fantasy: an open spellbook | medieval: a hand-written tome or spellbook | the building name as text (the building panel has no icon fo | borderline, keep |
| `icon.building.guild` | v2 | medieval or fantasy: a red banner flag | medieval: a heraldic banner on a pole | today's Lucide Shield icon (#818cf8) plus the building name  | ok |
| `icon.building.hero_house` | v2 | cannot tell: a small red house | medieval: a timber-framed cottage with a thatched or tiled roof and sm | today's Lucide Home icon (#34d399) plus the building name as | OFFENDER |
| `icon.building.inn` | v2 | medieval or fantasy: a beer mug | medieval: a tavern tankard (wood, horn or pewter) of ale | today's Lucide Bed icon (#fb923c) plus the building name as  | borderline, keep |
| `icon.building.store` | v2 | medieval or fantasy: a gold coin pouch | medieval: a leather purse of coins at a market stall | today's Lucide Store icon (#38bdf8) plus the building name a | fine, note |
| `icon.class.mage` | v2 | medieval or fantasy: a wizard hat | medieval fantasy: a pointed wizard hat | today's Lucide Wand2 icon plus the class name as text | ok |
| `icon.class.ranger` | v2 | medieval or fantasy: a bow and arrow | medieval: a hunter's longbow and arrow | today's Lucide Crosshair icon plus the class name as text | registry text only |
| `icon.class.rogue` | revision | medieval or fantasy: a curved sword hilt | medieval fantasy: a hooded cowl of a thief or assassin | today's Lucide Sword icon plus the class name as text | ok |
| `icon.class.warrior` | adopted | medieval or fantasy: a sword shield | medieval: a heater shield with a sword emblem | today's Lucide Shield icon plus the class name as text | ok |
| `icon.item.armor` | v2 | medieval or fantasy: a steel breastplate | medieval: a plate breastplate with pauldrons | the item type as text, as the loot and inspect panels show i | ok |
| `icon.item.consumable` | v2 | medieval or fantasy: a red potion flask | medieval fantasy: a corked alchemical potion flask | the item type as text, as the loot and inspect panels show i | ok |
| `icon.item.material` | v2 | cannot tell: a grey ore rock | medieval: a chunk of raw ore with gold flecks | the item type as text, as the loot and inspect panels show i | ok |
| `icon.item.tool` | revision | cannot tell: a steel wrench | medieval: a smith's hammer crossed with tongs | the item type as text, as the loot and inspect panels show i | OFFENDER |
| `icon.item.trinket` | v2 | medieval or fantasy: a gold amulet pendant | medieval fantasy: an amulet on a chain | the item type as text, as the loot and inspect panels show i | ok |
| `icon.item.weapon` | v2 | medieval or fantasy: a short sword | medieval: an arming sword | the item type as text, as the loot and inspect panels show i | ok |
| `icon.marker.boss_arena` | v2 | cannot tell: a white skull | medieval fantasy: a skull marking a deadly place | today's skull emoji label (#f59e0b) plus the location name a | ok |
| `icon.marker.dungeon_entrance` | v2 | medieval or fantasy: a stone archway | medieval dungeon: a stone archway into a keep or cave | today's door emoji label (#e06080) plus the location name as | ok |
| `icon.marker.enemy_camp` | adopted | medieval or fantasy: crossed swords | medieval fantasy: crossed swords marking a hostile camp | today's emoji label (swords, | ok |
| `icon.marker.resource_grove` | v2 | cannot tell: a green tree | medieval fantasy: a wild broadleaf tree of the countryside | today's herb emoji label (#4ade80) plus the location name as | ok |
| `icon.marker.ruins` | v2 | cannot tell: a map or grid | medieval ruin: a broken masonry wall of a fort or castle | today's classical building emoji label (#a0906a) plus the lo | ok |
| `icon.marker.shrine` | v2 | medieval or fantasy: a stone obelisk | ancient or medieval: a standing stone, obelisk or waymarker | today's four-pointed star symbol label (#60a5fa) plus the lo | ok |
| `icon.plate.location` | adopted | cannot tell: a blue square button | abstract UI glyph: a plaque the glyph sits on, no setting | the bare glyph with no plate | ok |
| `icon.rarity.common` | revision | cannot tell: a grey round button | abstract UI glyph: a plain bead, no setting | today's rarity colour (#9ca3af) on the rarity name as text,  | ok |
| `icon.rarity.rare` | v2 | cannot tell: a purple diamond gem | abstract UI glyph: a sparkle gem, no setting | today's rarity colour (#a78bfa) on the rarity name as text,  | ok |
| `icon.rarity.uncommon` | v2 | cannot tell: a green diamond gem | abstract UI glyph: a cut gem, no setting | today's rarity colour (#34d399) on the rarity name as text,  | ok |
| `icon.status.frame_buff` | revision | cannot tell: a green glass orb | abstract UI glyph: an up arrow in a round frame, no setting | the effect's name as text in the Effects tab, which has no i | ok |
| `icon.status.frame_debuff` | adopted | cannot tell: a red warning triangle | abstract UI glyph: a down arrow in an inverted-triangle frame, no sett | the effect's name as text in the Effects tab, which has no i | OFFENDER |
| `icon.tier.a` | adopted | cannot tell: a grey round disc | abstract UI glyph: a rank badge in a seal-like octagon, no setting | today's colour chip (#fb923c) plus the letter A as text, whi | ok |
| `icon.tier.b` | adopted | cannot tell: a green round disc | abstract UI glyph: a rank badge in a seal-like octagon, no setting | today's colour chip (#60a5fa) plus the letter B as text, whi | ok |
| `icon.tier.c` | adopted | cannot tell: a dark round ring | abstract UI glyph: a rank badge in a seal-like octagon, no setting | today's colour chip (#34d399) plus the letter C as text, whi | ok |
| `icon.tier.d` | adopted | cannot tell: a dark green disc | abstract UI glyph: a rank badge in a seal-like octagon, no setting | today's colour chip (#94a3b8) plus the letter D as text, whi | ok |
| `icon.tier.e` | adopted | cannot tell: a dark green disc | abstract UI glyph: a rank badge in a seal-like octagon, no setting | today's colour chip (#6b7280) plus the letter E as text, whi | ok |
| `icon.tier.s` | adopted | cannot tell: a grey diamond | abstract UI glyph: a rank gem (diamond), no setting | today's colour chip (#f87171) plus the letter S as text, whi | ok |
| `icon.tier.ss` | adopted | cannot tell: a gold diamond ring | abstract UI glyph: a rank gem (diamond), no setting | today's colour chip (#f59e0b) plus the letter SS as text, wh | ok |
| `icon.tier.sss` | adopted | cannot tell: a white diamond shape | abstract UI glyph: a rank gem (diamond), no setting | today's colour chip (#ffd700) plus the letter SSS as text, w | ok |
