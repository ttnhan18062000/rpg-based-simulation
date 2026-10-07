---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-06
tags: [architecture, documentation, hud]
---

# Icon key set `icons-key-v1`: what was drawn, how it measures, how to review it

Written by `TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET`. **Adopted by the owner on 2026-10-06T15:21:47Z** (set adoption `sa-b4bb738d6b5526f0`, approver nhan, owner), after this review; recorded by `TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION`. The sources are in the catalog; **no release candidate covers them** (rc-0006 has 34 slots), nothing is built for them and the game does not read them. Before the adoption the set was a draft; the text below describes the set as reviewed.
Style: `docs/assets/icon_style_guide.md` (D20). Palette and sheet rule: `docs/assets/icon_criteria.md` (the user's thresholds, 2026-10-06).

## What is in the set (14 keys, own pixels, palette `icons-v1` only)

| Key | Size | Drawing |
|---|---|---|
| `icon.plate.location` | 16x16 | location plate: 1 px rim `#9ea4b6`, slate fill, light top-left edge, shadow bottom-right, cut corners |
| `icon.marker.enemy_camp` | 16x16, live area 12x12, 2 px margin | crossed swords, dark outline; drawn over the plate by the client |
| `icon.building.blacksmith` | 24x24 | anvil, raised hammer, sparks |
| `icon.class.warrior` | 24x24 | shield with a sword emblem |
| `icon.tier.e` to `icon.tier.sss` | 8x8 each | E and D: plain octagon; C and B: octagon with one and two pip cut-outs; A: octagon with a frame cut-out; S, SS, SSS: diamond with none, one and two pip cut-outs, in silver, gold and platinum fills |
| `icon.status.frame_buff` | 16x16 | rounded frame, green rim, up chevron |
| `icon.status.frame_debuff` | 16x16 | inverted-triangle frame, ember rim, solid down arrow (redrawn before the gate, see finding 3) |

Provenance: every drawing is our own pixels with the Aseprite MCP tools (`licence_state UNREVIEWED`, as for terrain); no outside art was copied or traced and no AI generator was used. Nothing outside was
looked at while drawing beyond the committed research.

## The sheet rule on this set, as measured

`python -m tests.visual_assets.icon_draft_set` (recorded in the preview fixture as `rule_result.json`; draft set hash `sha256:29854e8b32bcd9701f5e717a2e01dce5934cc04af63d4c6e3bc156c78ce5cbbd`):

| Rule | Measured | Needed |
|---|---|---|
| I1 shape, tiers (26 pairs across classes) | smallest difference 4 px (C vs E, S vs SS) | 3 px at 8x8 |
| I1 shape, buff vs debuff | 92 px | 6 px at 16x16 |
| I2 value, tiers (28 pairs) | smallest L* gap 8.74 (protan), 9.14 (normal), 8.79 (deutan), 9.30 (tritan) | 6 |
| I2 value, buff vs debuff | 7.7 (deutan) to 15.2 (protan) | 6 |
| I3 plate rim vs the 23 terrain tiles | 18.0 (deutan), closest tile snow | 12 |
| Result | **PASS** | |

Also measured, not ruled: no pixel outside the palette; `lint_sprite` has no warning on any of the 14 (info notes only: diagonal strokes count as orphan pixels, and plates, frames and badges touch the
canvas edge on purpose); the glyph's bounding box is 2, 2, 13, 13 (margin 2 px all round); colour counts are within the lint budgets (8 at 16 px or less, 12 at 24 px).

**How this was reached (stated plainly).** The rule was fixed first. The shapes and fills were then prototyped against it before any pixel was drawn, as design feedback; the thresholds never moved. The
first prototype failed I2 on two pairs: the ring badge A had no interior pixels left (so its mean was the outline's), and the buff and debuff frames had identical interiors. A became a smaller cut-out and
the two frames got different interiors; the drawn set was not tuned after that.

## Things the owner should judge with their own eyes (honest findings)

1. **Dark tier badges on a dark panel.** E and D (dark green fills, near-black outline) are hard to see at 1x on the dark panel and fine on the light one (preview page, contact sheet). The value ladder has to
   start dark for eight steps to fit the palette (the best palette ladder is 8.74 L* apart, `icon_criteria.md`); the letter stays as text beside every badge.
2. **Stars.** S, SS and SSS are a diamond with 0, 1 and 2 pip cut-outs (silver, gold, platinum), not stars. A true 1/2/3-star badge does not fit 8x8 under the dark outline policy: one outlined four-point
   sparkle is 5x5 and three need more than 8 px even overlapped. Unoutlined 3x3 plus-stars would pass I1 (5 px each) but break the outline policy and read poorly on a light panel. The threshold did not change.
3. **The debuff frame: fixed by planner request, before the gate.** The first drawing (a down chevron with two light dots in the triangle) read as a smiling face at the preview scale, which a debuff must not. Only that key was redrawn (intake `in-64c1eef69abd939b`, replacing `in-5eb3750c52019dca` in the draft set): the dots are gone and a solid bone-coloured down arrow (2 px shaft, a 4-then-2 px head) sits centred in the triangle; the inverted-triangle frame and ember rim are unchanged. Before and after on the sheet rule: I1 buff vs debuff 92 px, unchanged; I2 buff vs debuff smallest gap 14.2 (deutan) before and 7.7 (deutan) after (the lighter arrow raises the frame's interior brightness, still over 6); I3 and the tiers unchanged. A larger 6-wide arrow head was tried first in a prototype and failed I2 against the buff (2.8), so the head is smaller; the arrow's lint is clean (the chevron's orphan-pixel note is gone).
4. **The plate rim is mid-light `#9ea4b6`, not a dark outline** (the terrain is dark: a dark rim reaches only L* 6.0 against the floor tile). This departs from the research's "dark outline" advice for plates only.
5. **Tier fills are mixed hues** (dark green to platinum) because the value ladder, not the hue, carries the order; hue is reinforcement only.
6. **Fallbacks.** Every key shows today's fallback beside it on the page; the status frames have none today (the effect's name as text).

## Review it

The preview page shows every view: the contact sheet at 1x and 2x on a dark and a light panel beside the fallbacks; the plate and glyph over the darkest (floor) and brightest (snow) terrain-v1 tile; a small map
scene at a whole-number scale; the tier ladder and the status frames in colour, greyscale and three simulated visions (a visual approximation only: the verdict is the recorded result above); and the recorded
rule result.

```
cd /home/vboxuser/Work/rpg-aseprite-mcp/frontend && npx vite
# open http://localhost:5173/rehearsal-icons.html  (the port Vite prints; dev only, never in the production build)
```

If you adopt the set, you run `adopt-set` yourself with your own name, role, licence decision and evidence (nothing is taken from the drafts, and the licence value is not pre-answered here; `adopt-set --help` says only `CLEARED` is adoptable):

```
/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python -m visual_assets.store adopt-set icons-key-v1 \
  --approver "<your name>" --approver-role "<your role>" --licence "<your licence decision>" \
  --licence-evidence "<your own evidence reference>" --review-evidence "preview page rehearsal-icons.html of icons-key-v1, draft set hash sha256:29854e8b32bcd9701f5e717a2e01dce5934cc04af63d4c6e3bc156c78ce5cbbd"
```

Run it from `/home/vboxuser/Work/rpg-aseprite-mcp` (the worktree that holds the drafts). If the set is not adopted, the batch stops with children 1 to 5.

## Where the intakes are

The 14 drafts were submitted twice: through the MCP `submit_candidate` tool, which runs from the main checkout, and again with the CLI from the worktree (identical, content-derived ids). The worktree's
copies are the ones the draft set uses. The main checkout's gitignored quarantine (`/home/vboxuser/Work/rpg-based-simulation/visual_assets/catalog/.quarantine/`) also holds the 14 stray intakes below, plus two
throwaway size tests (`in-912123fa34e41d8a` 8x8, `in-b7494c152ff23e1e` 24x24); nothing there is tracked and nothing was deleted (30-day local retention applies).

`in-b38a2188769869c1` plate, `in-641f3c59f5f4939d` marker, `in-37bd500fef9a7034` blacksmith, `in-8737f1d1f0c8ba06` warrior, `in-ba348f41d73dfade` E, `in-4b525122b446cb8b` D, `in-7f5f75a61b4342a0` C,
`in-2c7256eaabef8a0e` B, `in-134be4b2159fdd2e` A, `in-31644cad57a45f11` S, `in-5c261a962f9915bd` SS, `in-065bc4aa0dea7235` SSS, `in-ec0f01dd297e3dc9` buff frame, `in-5eb3750c52019dca` first debuff frame (replaced by the arrow redraw `in-64c1eef69abd939b`, which was submitted from the worktree only).
