---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE
artifact_type: investigation
tags: [architecture, mcp, testing, documentation]
---

# Investigation — TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE

- `search_docs` / `graphify query` return nothing relevant for `visual_assets/`; findings are from direct reads and experiments on the landed code and the pinned Aseprite 1.3.18.6.
- Reusable: `drawing.backend.sandbox` (bwrap, no network, one job dir, timeout) is the one allowed import from `drawing`; the drawing tools' preview already uses `--frame-range 0,0 --scale N --save-as`.
- `is_build_eligible` must be the only eligibility test; it is now `records.is_eligible`, shared with the key-holder check.
- A visual key maps to its source asset through the adoption record of the asset's latest eligible revision (the registry has no mapping); two assets claiming a key is ambiguous.
- PNG byte output is not guaranteed stable across Aseprite versions, hence D4: identity is the decoded-pixel hash.
- Pure-Python unfiltering is fast enough: a 256x256 Paeth image decodes in well under a second, a 1024x1024 filter-0 image in about 0.05 s.
- A stored review-time check lives in a gitignored directory any local process can write, so `adopt` re-renders and compares again; the check is evidence for the human, not the gate.
