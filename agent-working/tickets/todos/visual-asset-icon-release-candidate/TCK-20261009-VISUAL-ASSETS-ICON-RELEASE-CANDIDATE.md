---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE
phase: open
date: 2026-10-09
tags: [architecture, testing]
---

# TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE

## Title
Build the 36 adopted icons and assemble the first release candidate that covers icon slots (`pilot/rc-0008`); close the bookkeeping drift left by the hardening and icon-v2 batches

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
The owner asked (2026-10-09, "start order as your recommendation") to proceed with the planner's order. The 36 adopted
icons (14 key set + 22 v2; 7 of them at r0002) have never been built: `visual_assets/catalog/generated/` holds 34
artifacts (the terrain era), and no release candidate covers an icon slot (`rc-0007` = rc-0006's 34 entries). The icon-v2
keys ticket left "building icons into artifacts" out of scope on purpose. This ticket builds them and assembles the next
candidate. It is store work only: a candidate is not an active release; activation stays parked (owner, 2026-10-08) and
nothing is wired into the app.

## Scope
1. **Bookkeeping drift (first commit, docs only):** the hardening batch is merged (PR #471, `0c3a5654b`), but
   `agent-working/tickets/done/visual-asset-foundation-hardening/SEQUENCE.md` still says "the PR awaits the user's
   authorization" and the epic `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` has `## Status EPIC_SCOPED` with its
   one AC unchecked. Set the status line to the merged outcome (PR #471, `0c3a5654b`), tick the AC, set `## Status` to
   `DONE`. Do the same `## Status` change for `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2` (its ACs are already ticked).
   Both values are legal (`tools/ticket_field_values.py`); `DONE` is the convention of the other asset epics. Touch no
   other domain's epics.
2. **Build:** `python -m visual_assets.store build` for the adopted icon sources, current revision only (the 7 slots at
   r0002 build r0002; r0001 of those is not built). No terrain artifact may change (34 artifact dirs byte-identical).
3. **Assemble `pilot/rc-0008`, only after the user's answer to a blocking question the implementer asks** (precedent:
   rc-0005, rc-0007). Expected: rc-0007's 34 entries unchanged + one entry per adopted icon key = 70; registry hash = the
   current registry (post-#471); `fallback_missing` and `key_without_artifact` both silent.
4. **Guards, re-pointed by equality, nothing loosened** (precedent: rc-0006/rc-0007): `adopted_facts.RELEASE_CANDIDATES`
   gains rc-0008; the stdio release count 7 -> 8; a new test "rc-0008 = rc-0007's 34 entries + exactly the 36 adopted
   icon keys at their current revision"; `test_icon_v2_keys` / icon set tests that assert "no artifact or release slot"
   for icons are updated to the new fact, not deleted. Fixture guards derive from the stored candidate since #471
   (`tests/visual_assets/derived_runtime.py`); re-export a fixture only if its guard says it moved.
5. **Evidence:** `verify` and `audit` clean; every icon artifact decodes to its key's declared size (24x24 / 16x16 /
   8x8) and its `pixel_hash` equals the adopted source's frame-1 pixels at x1 (or say plainly why not).
6. **Docs:** `docs/assets/store_contract.md` (the catalog paragraph is stale: it says the v2 keys are "not drawn, not
   adopted"; state the 36 adopted icons, the build and rc-0008), `docs/assets/pilot_terrain_key.md` (rc-0008 paragraph
   with the registry hash, as for rc-0007), the session handoff snapshots under `docs/assets/session_handoff/` (refreshed
   from `.claude/handover/asset-{planner,implementer}.md`), `make knowledge-index-update`.

## Out of Scope
- Activation, any runtime export into the frontend app, wiring icons into panels, the Live Map art path, any gate or
  milestone result (M0-M7 stay as recorded). The client-side family glyph fallback (`fallback_safety.md`, "not wired into
  the real Live Map") stays parked with activation.
- Any registry schema change (so no `MAX_REGISTRY_BYTES` budget review is triggered; `docs/assets/budgets.md` requires one
  before the next per-key field).
- New scale classes (export stays x1), new art, revisions of adopted icons.

## Acceptance Criteria
- [ ] Hardening and icon-v2 epics read `DONE`; hardening `SEQUENCE.md` status names PR #471 and `0c3a5654b`.
- [ ] 36 icon artifacts built at the current revision; the 34 terrain-era artifacts are byte-identical.
- [ ] `pilot/rc-0008` assembled only after the user's recorded answer (verbatim in Implementation Notes); 70 entries, the
  34 old ones equal to rc-0007's.
- [ ] `verify` and `audit` clean; icon artifact size and pixel-hash checks recorded.
- [ ] Guards re-pointed by equality with the new rc-0008 test; no assertion removed or weakened.
- [ ] Docs above updated; snapshots refreshed; knowledge index updated.
- [ ] Tests run: `tests/visual_assets`, `tests/unit/tools`, `tests/tools`, docs/static/architecture lanes, frontend
  `iconScene.test.ts` if a fixture moved.

## Related Tickets
- TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC (rc-0007; icon build left out of scope)
- TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING (PR #471; derived fixture guards, `fallback_missing`)
- TCK-20261008-VISUAL-ASSETS-ACTIVATION-ROADMAP (activation parked)

## Related Docs
- docs/assets/store_contract.md, docs/assets/pilot_terrain_key.md, docs/assets/fallback_safety.md, docs/assets/budgets.md
- docs/architecture/visual_asset_foundation_adr.md (D8 Profile A, D10 Aseprite local)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ACTIVATION-ROADMAP/gate_map_2026-10-08.md

## Related Code Areas
- visual_assets/store/build/exporter.py, visual_assets/store/release.py, visual_assets/catalog/{generated,manifests}/
- tests/visual_assets/ (adopted_facts.py, derived_runtime.py, test_icon_v2_keys.py, icon set tests, stdio guard)

## Assumptions / Open Questions
- Owner question (implementer asks, blocking): assemble `pilot/rc-0008` with 70 entries. Without a yes, stop after the
  build and report.
- Catalog id stays `pilot` (precedent rc-0005..rc-0007); a separate catalog for icons is not asked for.
- `build` with no source id: the implementer confirms it builds only revisions without an artifact and leaves existing
  artifacts untouched before running it; if it would rebuild terrain, build per icon source id instead.
- Resolved during implementation (planner ruling 2026-10-09, see Implementation Notes): the three closed draft-set fixture guards are anchored to the gate's own record, not to the moving catalog; the frontend page and fixtures are unchanged.

## Implementation Notes
- **Owner's answer, verbatim (blocking question the implementer asked, 2026-10-09):** "Yes, assemble rc-0008" (question: assemble `pilot/rc-0008` = rc-0007's 34 entries + the 36 adopted icons = 70, on the current registry; nothing activates). Assembled only after it.
- **Build:** `build()` with no id walks every adopted source (idempotent), so the 36 icons were built one source id at a time. The 34 terrain-era artifact files hash identically before and after (tree hash `2523829c...`). `verify` and `audit` pass. For all 36: the revision is the newest, the decoded size equals the key description, the source record and the artifact record, and `pixel_hash` equals an independent `aseprite` render of frame 1 at x1.
- **rc-0008:** 70 entries; the 34 non-icon entries equal rc-0007's; 36 distinct `icon.*` entries; 11,767 bytes against `MAX_MANIFEST_BYTES` 524,288; `registry_hash` differs from rc-0007's (#471 changed the registry); neither `key_without_artifact` nor `fallback_missing` fired.
- **Finding (unplanned): building the icons changes what a fresh draft export holds.** `draftexport._adopted_references` adds a labelled reference for every adopted slot that has a built artifact and skips "adopted but not built yet" slots. After the build a fresh export of `icons-key-v1`, `icons-v2` and `icons-owner-fixes-v1` has 70 entries each (committed: 48 / 56 / 43), so three fixture guards failed. Regenerating the fixtures with their own `--write` fixed those but broke 15 frontend vitest tests (`IconHarness.test.tsx`) and the `isolation.test.ts` build-output count (194 -> 257); the baseline was 270/270. The regeneration was reverted.
- **Planner ruling (2026-10-09), option (c): re-anchor the guard, keep the export and the page as they are.** The three sets are CLOSED owner gates; their fixtures and `IconHarness` are the evidence the owner decided on, so they are not regenerated (not option a), and the reference list is not made terrain-only (not option b: references exist so a future draft set sees all adopted art). The three guards were anchored to the moving catalog, the defect #471 child 1 fixed for the runtime fixtures. Now `adopted_facts.CLOSED_DRAFT_SETS` pins each closed set to its adoption record(s) and draft set hash, and `tests/visual_assets/closed_draft_fixture.py` checks a closed set's fixture as: (i) draft entries equal the fresh export's draft entries and draft PNGs are byte-equal; (ii) every adopted-reference entry is byte-equal to the catalog artifact it names (append-only, so strict); (iii) no stray entry, duplicate slot or unnamed file. It does NOT require the references a fresh export adds for art built after the gate. An open set (no pin) keeps the full fresh-export equality. This re-anchors the guard to the gate's own record; it is not a relaxation to make a test pass: drafts and references stay byte-checked, only "must include art built after the gate" is dropped, and only for gate-closed sets.
- **Mutation proofs** (`test_closed_draft_fixtures.py`, each asserted to apply at one site, run for all three sets): a flipped draft PNG byte, a flipped reference PNG byte, a reference naming an artifact that does not exist, a stray entry, and a set removed from the pin (the full-equality path then fails on today's store). `test_icon_release_candidate.py` adds rc-0008 = rc-0007 + exactly the 36 icon keys with mutants (a dropped icon entry, one altered terrain entry, an icon naming another icon's artifact, a stray icon entry).
- **Other guards, by equality, nothing loosened:** stdio releases 7 -> 8 and artifacts 34 -> 70 (the artifact request now asks `limit: 200`, as the source request already did, because the tool's default page is 50); `adopted_facts.RELEASE_CANDIDATES` gains `rc-0008.json`, `GENERATED` is now the 70 artifact directories; the "no artifact / no icon slot" assertions in `test_icon_set_adoption` and `test_icon_v2_keys` now state the new fact (built; only rc-0008 lists the icons).
- `draftexport.py` docstring fixed ("16 x 16 artifact" -> the x1 artifact); `icon_draft_fixture.py` warns not to run `--write` on a closed set.
- Frontend untouched; vitest `src/visualAssets` stays 270/270.

## Test Summary

## Files Changed

## Completion Summary
