---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA
artifact_type: investigation
tags: [architecture, testing, documentation]
---

# Investigation: Read-only sample-map data

Question: what does a typical compiled world place, and how much of it has a visual key? Method: the API's own build path (`engine_manager.py:133-136`, seed 42, in memory, no `output_report_path`) plus `present_map` / `present_static`; `present_map`'s integer codes are per world (`terrain_code_map`, `state_presenter.py:183`), so cells are stored by terrain NAME. Findings: 73,808 cells over `frontier_living_world`, `highland_traverse`, `dungeon_crawl`; 87.9 % have no exact key (`PLAIN` 54,661, `plain` 5,578, `ruin` 3,362, `river` 1,271); `PLAIN` and `plain` are two names in one world; building, resource-node, place and entity kinds mostly have no key; no sample world has a chest. asset-planner added a labelled `proposed_aliases` table (unconfirmed, for rpg-planner, #519).
