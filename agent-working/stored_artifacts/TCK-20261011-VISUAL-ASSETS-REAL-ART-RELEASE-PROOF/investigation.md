---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-REAL-ART-RELEASE-PROOF
artifact_type: investigation
tags: [architecture, testing, documentation]
---

# Investigation: Build, rc-0009, export-runtime atlas and slices proof

Question: does the release and runtime-export half carry real art? `build` exports frame 1 only (`build/exportconfig.py:53`), so animated sources release as their first frame. rc-0009 = rc-0008's 70 + 3 on the owner's answer; the 12 tests that export the committed candidate are re-pointed from rc-0008 to rc-0009 without weakening; two icon candidate tests accept the exact set {rc-0008, rc-0009}. Export twice is byte-identical; slice coordinates match the sources at scale x1.
