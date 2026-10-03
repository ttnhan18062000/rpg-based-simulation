---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261003-PERF-PHASE-COUNT-PINNED-TEXT
date: 2026-10-03
tags: [performance, documentation]
---

# Investigation: TCK-20261003-PERF-PHASE-COUNT-PINNED-TEXT

The pinned text was `AGENTS.md` ("39-phase") and `authoritative_pipeline.md` ("39 phases") in `test_agents_md_generation.py`, plus the generator note. Pre-change, `build_agents_md()` equalled `AGENTS.md`, so regeneration changes only the note line. Remaining "39-phase" mentions left to other tracks: `docs/plans/render-and-art/` (README and plans), `docs/plans/render_and_art_program_roadmap.md`, `docs/plans/live_map_rendering_and_surface_integration_milestone_plan.md`, `docs/plans/aseprite-mcp-pixel-art/README.md`, and `docs/brainstorm/` (several files).
