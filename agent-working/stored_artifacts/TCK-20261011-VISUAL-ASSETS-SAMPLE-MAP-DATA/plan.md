---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA
artifact_type: plan
tags: [architecture, testing, documentation]
---

# Plan: Read-only sample-map data

1. `tools/visual_assets_sample_map.py data <world>`: compile in memory, present, map names to keys by an exact rule (near keys listed, not applied), write one deterministic JSON per world under the gitignored report directory. 2. Tests: the rule, RLE, output location, determinism, `data/worlds` untouched, cell-by-cell equality with the compiled state, the aliases only for names without an exact key.
