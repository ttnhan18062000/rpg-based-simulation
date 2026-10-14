---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ACTIVATION-ROADMAP
artifact_type: investigation
date: 2026-10-08
tags: [architecture, planning]
---

# Investigation: citation re-check of gate_map_2026-10-08.md (at 4a2141df9)

Corrections made when writing the roadmap (the map's text is kept as the planner wrote it):
- M2 `BLOCKED` is at `m2_evidence_charter.md:96-97` (the map said 94-95: that is the heading); the rerun rule is `:100-106`; the owner-narrowing sentence is `:108`.
- The M1 count (55 MET / 7 GAP / 6 N/A) is at `m1_contract_register.md:28`, not `:66`; `W13.x` are rows `:231,232,234` (`W13.5` at `:233` is `MET`).
- The map's 'icons only at step 7 (06:65, 06:89)' cites the wrong lines: `06:65` is the gate-validity sentence; M6's single noncritical role is `06:41`, the non-goals (broad rollout, HUD redesign) `06:88`.
- 'C03/C04/C08 not run (04:48)': line 48 only states M4 targets them; the evidence is that no M4 record exists (`pilot_charter_am6.md:23`).
- FALSE CLAIM corrected: 'per-icon safety class NOT FOUND' and 'status frames and class hall have no fallback today'. `visual_keys.yaml` descriptions of all 36 icon keys state a class (35 identifying, 1 decorative) and a text fallback as PROSE; what is missing is a registry field (`W02.7`) and any check. The roadmap and `fallback_safety.md` say that instead.
- All other cited lines were confirmed as quoted (M0, M5, M6, M7, README, 04/05/07, icon_style_guide:164-165, ADR D14 at :43, proposal :754-763).
