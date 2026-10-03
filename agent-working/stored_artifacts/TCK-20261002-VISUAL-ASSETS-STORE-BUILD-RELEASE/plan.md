---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE
artifact_type: plan
tags: [architecture, mcp, testing, documentation]
---

# Plan — TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE

1. Contract additions (additive, schema_version 1): `ArtifactRecord.source_record_hash`, ordered `ReleaseId` (`rc-NNNN`), `VisualKeyDefinition.optional`, `ReviewRenderCheck` (typed, local), `AdoptionRecord.review_hash`.
2. Pure `store/pixels.py`: bounded PNG decoder and the `pixels-v1` hash; `intake` fully decodes the preview with it (finer finding codes).
3. `store/rendering.py` (injected `RenderTool`, one comparison) and `store/review.py` (records the check); `adopt` re-renders itself, copies the check into provenance, binds its hash; `visual_key_taken`.
4. `store/build/` (export config, fingerprint, sandboxed exporter + `build`), `store/release.py`, `store/verify.py`, `store/gc.py`, CLI commands.
5. Tests (CI with injected renderers; real Aseprite integration), docs, close.

## Where the ticket and reality differed (reported to asset-planner, who decided)
- Ordered `ReleaseId`, `optional` on registry keys, `source_record_hash` (chain anchoring) were missing from the contracts.
- The planner's preview-to-source binding (items 10 a-c) and `visual_key_taken` were added to this ticket; `adopt` re-renders at adoption time and never trusts a stored check.
- The PNG reader lives in a new pure layer `pixels` (intake and build both import it), `release` is `store/release.py`, `review` is its own layer so `intake` never imports `drawing`.
- Record naming: the PNG is `<pixel hash hex>.png`, the record is `<hex>.<source revision>.artifact.json`, so two revisions that render identically each have a record and share the PNG.
- Plain export runs no Lua: the fingerprint's "Lua pin hash" is the pin of the template mounted in the sandbox.
