---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-THEME-FIT
artifact_type: investigation
date: 2026-10-08
tags: [architecture, hud, testing]
---

# Investigation

- D20 fixed style, sizes, palette and sources but no setting, so a modern wrench and a toolbox passed every check.
- Audit (`audit_36_icons.md`): offenders are the adopted wrench, the hero house (white walls, blue glass) and the debuff frame (red warning triangle); the glass-mug first pass was overturned (opaque tankard, borderline keep, staves added as a light improvement). The ranger's registry fallback `Lucide Crosshair` is today's UI chrome, left as is.
- Era question alone is weak (most answers are 'cannot tell'); a named modern object in the free text or era answer is what flags. Round 5 still flagged the tool (wrench) and the debuff frame (gear); reported, not tuned.
- Store: adopted sources take new revisions only via `adopt --parent`; `adopt-set` cannot; `draft keep` refuses an existing source id, hence `_fix` ids; no command drops a draft slot.
