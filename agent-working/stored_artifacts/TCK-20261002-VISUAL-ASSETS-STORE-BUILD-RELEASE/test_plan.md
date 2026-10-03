---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE
artifact_type: test_plan
tags: [architecture, mcp, testing, documentation]
---

# Test plan — TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE

## Proof Plan

| Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|
| unit | `pixels-v1` equals a hand-computed value; 12 encodings of one image hash identically; one pixel/width/swap changes it; RGB under alpha 0 ignored | the documented definition | identical hashes for identical pixels | `pytest tests/visual_assets/store/unit/test_pixels.py` |
| unit | reader refuses bad signature/CRC, 16-bit, interlace, over-limit, truncated, decompression bomb, trailing data, APNG, colour-key tRNS | ticket acceptance list | `PngDecodeError` with a stable code, bounded work | same |
| unit | review check, forged/stale/mismatching checks, adopt re-render, `visual_key_taken` | planner decisions 4 and 8 | adopt refuses with its own code, tree unchanged | `pytest tests/visual_assets/store/unit/test_review_render.py` |
| unit | build (idempotent, history, unchanged pixels, non-reproducible render refused, revoked refused), release (every refusal, ordered ids, no active pointer), verify (one finding per planted fault), gc (dry run, delete limits) | ticket acceptance list | coded errors, nothing written on refusal | `pytest tests/visual_assets/store/unit/test_build.py test_release.py test_verify.py test_gc.py` |
| unit | committed catalog verifies clean in CI | ticket acceptance list | no blocking finding | `pytest tests/visual_assets/test_catalog_integrity.py` |
| integration (needs Aseprite) | real sandboxed export is reproducible and its pixels match what the drawing tools preview | real Aseprite 1.3.18.6 | same PixelHash twice, one artifact file | `pytest tests/visual_assets/store/integration/test_build_real.py` |
| architecture | store layering rows, strict `build/exporter.py` sandbox-import assertion, gate layers unreachable from drawing | `STORE_ALLOWED` | boundary test green | `pytest tests/visual_assets/test_boundaries.py` |
| mutation | hand-applied mutants of the new guards | n/a | each fails the intended test | scratch script (not committed) |
