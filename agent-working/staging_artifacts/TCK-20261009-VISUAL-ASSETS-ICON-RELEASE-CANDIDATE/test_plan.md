---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE
artifact_type: test_plan
date: 2026-10-09
tags: [architecture, testing]
---

# Test plan

## New
- rc-0008 equality test: entries = rc-0007's 34 (byte-equal entry records) + exactly one entry per adopted `icon.*` key at
  its current revision; no other entry.
- Icon artifact facts: decoded size equals the key's declared size; artifact bound to the current `SourceRecord`.

## Updated (by equality, never loosened)
- `adopted_facts.RELEASE_CANDIDATES`, stdio release count, `test_icon_v2_keys.py` and icon set tests that assert no
  artifact/release slot for icons.

## Mutation proofs (scratch copy; assert the mutant applied to exactly one site)
- Remove one icon entry from rc-0008 -> new test fails.
- Change one terrain entry's artifact id -> new test fails.

## Runs (heavy ones foreground under `systemd-run --user --scope -p MemoryMax=4G`, one at a time)
- `pytest tests/visual_assets`, `tests/unit/tools`, `tests/tools`, docs/static/architecture lanes.
- `python -m visual_assets.store verify` and `audit`.
- Frontend `iconScene.test.ts` only if a fixture moved.
