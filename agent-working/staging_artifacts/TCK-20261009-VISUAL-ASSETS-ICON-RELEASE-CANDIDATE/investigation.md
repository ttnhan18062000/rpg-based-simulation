---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE
artifact_type: investigation
date: 2026-10-09
tags: [architecture, planning]
---

# Investigation (planner, 2026-10-09, read-only, HEAD `0c3a5654b`)

Re-verify each claim before relying on it.

## Facts
- `visual_assets/catalog/sources/` holds 36 `icon_*` sources; `visual_assets/catalog/generated/` holds 34 artifact dirs
  (terrain tiles + `border_*` masks). No icon has ever been built.
- `manifests/candidates/pilot/` ends at `rc-0007.json` (34 entries, equal to rc-0006's;
  `TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC` line 45 put icon builds out of scope).
- Human-gated CLI commands are only `adopt`, `adopt-set`, `revoke` (TTY check, `visual_assets/store/cli.py:138`).
  `build` and `release` are store commands an agent may run (`docs/assets/store_contract.md` line 39). The rc-0005 and
  rc-0007 precedent still asked the user before assembling a candidate; keep that.
- `build` renders frame 1 at an integer scale through `/usr/bin/aseprite` in a bwrap sandbox
  (`visual_assets/store/build/exporter.py:55-70`); the pinned export config has one scale class `x1`
  (`catalog/build-config/export.toml`). Nothing in the exporter is size-specific, so 8x8 / 16x16 / 24x24 sources need no
  config change. Aseprite and bwrap are present on this machine.
- `assemble_release` refuses `key_without_artifact` (non-optional key) and, since #471, `fallback_missing`
  (`docs/assets/fallback_safety.md` ~line 100). All 36 icon keys are `optional` and carry a structured `fallback`.
- Fixture guards derive from the stored candidate since #471 (`tests/visual_assets/derived_runtime.py`), so a new rc
  should not force fixture churn by itself.
- Stale doc: `docs/assets/store_contract.md` line 15 says the 22 v2 keys are "registered, not drawn, not adopted, in no
  release candidate"; they were adopted in PR #418.
- Bookkeeping: hardening `SEQUENCE.md` status says the PR awaits authorization (merged as `0c3a5654b`); epics HARDENING and
  ICON-SET-V2 say `EPIC_SCOPED` while 103 of 111 done epics say `DONE`; both values are legal
  (`tools/ticket_field_values.py:48-50`).

## Unknowns for the implementer
- Does `build` with no source id rebuild existing artifacts? Read `exporter.build()` (`:91`) before running it.
- Which tests assert "no artifact / no release slot for an icon" today (`test_icon_v2_keys.py` says so per the v2 ticket)?
- `MAX_MANIFEST_BYTES` headroom with 70 entries (expected ample; record the size).
