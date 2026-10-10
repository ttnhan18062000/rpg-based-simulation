---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS
phase: open
date: 2026-10-10
tags: [architecture, testing]
---

# TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS

## Title
Animation metadata in the handoff and artifact records, after a registry budget review

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Child 7 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. store_contract.md:226: per-frame durations, tag ranges and loop modes are not in the handoff package nor checked by intake. budgets.md standing rule: any new per-key registry field needs a `MAX_REGISTRY_BYTES` review first (realistic max 414942 B = 90%).

## Scope
- **Design first (planner approves where the fields live).** Default: per-artifact/handoff fields (frame durations ms, tags with from/to/direction, loop mode), validated at intake against Aseprite's own data; **no** per-key registry field. If the design needs a registry field, the budget review comes first and the owner approves any new bound.
- Intake checks (durations > 0, tag ranges inside frame_count, bounded counts), contract records, export carries them through to the runtime export.
- store_contract.md, budgets.md.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- Raising MAX_SOURCE_BYTES / MAX_FRAMES (reopened only when real animated art exceeds them, budgets.md:46). Slices, 9-slice, pivots. Client playback.

## Acceptance Criteria
- [ ] Placement approved by the planner; budget review recorded if any registry growth.
- [ ] Intake refuses each planted bad case; a 4-frame fixture round-trips to the runtime export.

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`
- `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` (gap research; this batch takes items it parked)

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (`internal_gap_audit.md`, `research_asset_pipeline.md`; moved to stored_artifacts by child 9)

## Related Code Areas


## Assumptions / Open Questions


## Implementation Notes
- **Planner approval (2026-10-10):** placement APPROVED as designed (derived from the file, carried per SOURCE REVISION, no registry field, no manifest change, so no registry-budget review; per-tag direction and repeat instead of an invented sprite loop mode). Additions: a SECURITY REVIEW (new parser path over untrusted bytes), the corpus byte-identity proof stays mandatory, and the two NEW bounds `MAX_ANIMATION_FRAMES` 16 and `MAX_ANIMATION_TAGS` 16 are PROPOSED until the owner decides (asset-planner asks; the implementer does not).
- **Parser (`intake/aseprite.py`):** `read_facts` also returns `frame_durations_ms` (the frame header word at offset 8, at most 16 kept) and `animation_tags` (`RawTag`: name, from, to, direction byte, repeat). The tags chunk is walked by `_read_tags`, which (1) refuses a declared total over the tag bound BEFORE reading any entry, (2) checks the whole declared run against the chunk's own bytes with the smallest legal tag size before looping, (3) re-checks each name length against the chunk, and (4) validates names with the SAME contract type the record uses (`TagName`), so parser and contract cannot disagree. Every failure is a quarantine finding (`SOURCE_TRUNCATED_CHUNK` or a new `ANIMATION_*` code), never an exception.
- **New intake finding codes:** `ANIMATION_OUT_OF_BOUNDS`, `ANIMATION_FRAME_DURATION_INVALID`, `ANIMATION_TAG_RANGE_INVALID`, `ANIMATION_TAG_INVALID`. A duration "over 65535" from the design cannot occur (the header field is a WORD); the contract still bounds it to 1..65535.
- **Choices beyond the plan (for the planner to confirm):** (a) duration 0 is refused only for a source with MORE THAN ONE frame, so previously accepted one-frame art cannot start failing; tag ranges are checked for every source. (b) Tag names are limited to 32 plain-text characters: a contract-level limit on the new record (not a config bound), needed because the file's name length is a WORD. (c) A source with more than 16 frames is now quarantined (before, accepted); the drawing tools cap at 16, so only hand-made files are affected. (d) `build_entry_records` takes the source bytes and derives the animation itself, so `adopt` and `adopt-set` share one path; an invalid animation refuses with `source_animation_invalid` rather than store a bad record. (e) The export picks the NEWEST source revision whose artifact has the entry's pixel hash (the one `build` takes).
- **Carry:** `SourceRecord.animation` (optional; omitted for a one-frame source via `drop_absent`, so every committed record is byte-identical: a test round-trips all of them). `ArtifactRecord`, the registry and the runtime manifest are untouched.
- **Export:** `export-runtime --animation` writes `animation.json` (`runtime_animation`); no flag, no file; the manifest and every PNG are byte-identical either way (tested).
- **Real-Aseprite oracle:** `test_the_parser_reads_animation_metadata_exactly_as_aseprite_reads_it_back` has real Aseprite write a 4-frame sprite (durations 50/100/150/200 ms, one tag per direction) and compares the parser to what Aseprite reads back.
- **Budgets and docs:** two PROPOSED rows in `budgets.md`; a section in `store_contract.md`. The record `docs/assets/aseprite_local_proof.json` goes stale with this change (guarded files changed) and is refreshed in its own commit after the last store change.
- **Security review (independent reviewer, 2026-10-10): NEEDS_CHANGES, one real defect, fixed in a follow-up commit.** Finding 1 (MEDIUM, availability): a tag name of unassigned code points (plain-text valid; `repr` expands each to a 10-character escape) made the quoted intake finding exceed `IntakeFinding.detail`'s 256-character bound, so `validator.validate` RAISED instead of quarantining (reproduced on the committed code with `aseprite(frames=2, tag_specs=[("\U000e0080"*32, 5, 9, 0, 0)])`). Fix: findings name a tag by its position (`tag 3`), never by its text, at both message sites; and `_finding` clamps any detail to 256 characters (defence in depth: every other finding text was already short, so this changes nothing for them). Finding 2 (LOW, informational): work is proportional to the bytes present, not to declared counts; about 3,000 tag chunks of invalid tags give about 4,200 problem tuples in 8 ms, and `validate` already keeps only 64 findings; no action. The reviewer could not break: per-read bounds checks in `_read_tags` and the duration read (60,000 mutated files), arithmetic on declared counts, the frame/tag caps, intake-PASSED-but-adoption-raises (39,041 mutated files with no finding, none raised), and name handling (a tag name reaches only JSON; no path, log or script context); `runtime_animation_bytes` cannot traverse paths (`artifact_id` and `pixel_hash` patterns exclude `/`, `..` and glob characters).

## Test Summary
- `tests/visual_assets/store/unit/test_animation_metadata.py`: 40 passed, no Aseprite: round trips the 4-frame fixture from the file to `animation.json` and equals the values written; 11 planted bad cases each quarantined with its code (zero duration, tag past the last frame, from after to, tag outside a one-frame source, 17 frames, 17 tags, duplicate/empty/over-long/control-character names, unknown direction, non-UTF-8 name); hostile cases (the tags chunk claimed at every shorter length, declared counts of 17/1000/65535 in under 0.5 s each, a name length running past the chunk, 1500 random mutations plus truncations never raise); the contract refuses 9 violations; every committed `SourceRecord` round-trips byte for byte with no `animation`; every committed source reads with no new finding.
- Real Aseprite oracle: 1 passed in strict mode.
- `tests/visual_assets/store`: 1241 passed (the 1196 existing + the new module, including the security regression cases).
- Security regression proof: 4 new cases (hostile names on a bad range, an unknown direction, sixteen 17-to-32-character hostile tags, and the finding clamp) all FAIL with the two source fixes stashed and pass with them; the first draft of the sixteen-tag case survived the mutation (names too short to trip the limit), so it was strengthened and re-proved.

## Files Changed
`visual_assets/store/{config,adoption,setadoption,runtime_export,cli,animation (new)}.py`, `visual_assets/store/contracts/{animation (new),source,intake}.py`, `visual_assets/store/intake/aseprite.py`, `tests/visual_assets/store/{builders,adoption_support}.py`, `tests/visual_assets/store/unit/test_animation_metadata.py` (new), `tests/visual_assets/store/integration/test_real_aseprite.py`, `docs/assets/{budgets,store_contract}.md`.

## Completion Summary
(open: the two bounds await the owner; the security review result is recorded below when it returns; the local proof record is refreshed after the last store change)
