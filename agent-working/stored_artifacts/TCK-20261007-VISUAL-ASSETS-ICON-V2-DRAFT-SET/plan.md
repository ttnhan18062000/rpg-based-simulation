---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET
artifact_type: plan
tags: [architecture, testing, hud]
---

# Plan — TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET

1. Prototype all 22 icons on a local pixel canvas with the same lint and the fixed rule; look at rendered contact sheets; fix design problems (kite read as an arrow, bead like a dark tier badge, column vs obelisk) before drawing.
2. Draw through `visual_assets.drawing.api` in-process (planner-approved transport), export handoffs, intake with the worktree CLI, `draft keep --set icons-v2`, `draft verify`.
3. `tests/visual_assets/icon_v2_draft_set.py` reads the drafts back and runs the rule as measured; generalise `icon_draft_fixture` with `--set icons-v2`; commit `icondraft_v2/`.
4. Generalise the preview page: sizes from the manifests, optional second source, v2 sheets by family, location glyphs on the plate, rarity next to tiers in five visions, the recorded v2 result; isolation guard untouched except the fixture count pin.
5. Review doc, tests with mutants, close.
