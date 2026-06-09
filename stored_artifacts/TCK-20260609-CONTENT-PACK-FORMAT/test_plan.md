---
ticket: TCK-20260609-CONTENT-PACK-FORMAT
phase: test_plan
---

# Test Plan

17/17 unit tests pass in tests/unit/content/test_content_pack_manifest.py.
Covers: valid manifests, no-consumer error, unknown fields, frozen, disabled,
pack_id format guards, dependency validation (pass/fail/multiple/raise/default).
