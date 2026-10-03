---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260608-RUNTIME-MODE-EXPLICIT
artifact_type: plan
tags: [runtime, mode, explicit]
---

# Plan — TCK-20260608-RUNTIME-MODE-EXPLICIT

1. Replace `RuntimeContentMode` enum in `src/core/modes.py` — remove MIGRATION/V2, add four new values.
2. Update all adapter constructors and branching in `src/core/registries.py`.
3. Update `seed_phase1_content` default and bottom call.
4. Update `test_registry_projection_parity.py` fixture.
5. Create `tests/unit/content/test_runtime_content_mode.py` with 7 tests covering all four modes.
