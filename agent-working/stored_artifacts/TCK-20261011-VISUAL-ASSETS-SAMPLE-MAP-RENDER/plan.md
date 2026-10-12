---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-RENDER
artifact_type: plan
tags: [architecture, testing, documentation]
---

# Plan: Sample-map renderer

1. Export rc-0009 once with `export-runtime` into the report directory. 2. Port the border rule and prove parity three ways (the TS test vectors ported, a drift test against the TS text, a differential test against the real TS rule via the frontend's esbuild). 3. Draw terrain, fringes, buildings, places and resource nodes; mark and count every gap. 4. Write four PNGs, `render_stats.json` and a static page per run; two runs byte-identical.
