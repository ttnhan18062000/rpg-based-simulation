---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-RELEASE-BYTE-REPRODUCIBILITY
artifact_type: test_plan
tags: [architecture, testing]
---

# Test plan
test_release_byte_reproducibility.py: 2 local (`needs_aseprite`: rebuild and self-check of the verdicts), 8 CI. Run strict locally: `VISUAL_ASSETS_REQUIRE_ASEPRITE=1 pytest tests/visual_assets/test_release_byte_reproducibility.py`. No product code, so no mutants beyond the self-checks.
