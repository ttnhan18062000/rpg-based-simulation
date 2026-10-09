---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-FOUNDATION-DOCS-DRIFT
artifact_type: test_plan
date: 2026-10-09
tags: [architecture, documentation]
---

# Test plan

`tests/visual_assets/test_stored_evidence_tracked.py` (6 tests): the real tree has no ignored evidence without a tracked twin; each twin is byte-identical to its original; and the guard on a scratch git repository (a planted ignored `.json` fails it; a tracked twin satisfies it and an untracked one does not; other tickets and non-ignored files are out of scope; nested folders). Mutant: a real ignored `planted_mutant.json` planted in a visual-asset ticket folder made two tests fail, then it was removed. Docs tests and the knowledge index after the edits.
