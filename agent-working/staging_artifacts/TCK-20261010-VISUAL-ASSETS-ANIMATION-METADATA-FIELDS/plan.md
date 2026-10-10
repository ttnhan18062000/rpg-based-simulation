---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS
artifact_type: plan
tags: [architecture, testing]
---

# Plan (DESIGN ONLY, no code yet): where animation metadata lives

Status: awaiting asset-planner approval of the placement.

## Facts
- Intake reads only COUNTS from the `.aseprite` (`intake/aseprite.py`: frames, layers, cels, tags, palette); frame durations and tag ranges/directions are in the file (frame header word `duration`; tags chunk 0x2018: from, to, direction, repeat, name) and are not read today. The handoff package declares `frame_count` and `tag_count` and intake checks them against the file (`FRAME_COUNT_MISMATCH`).
- Build exports ONE PNG per scale class (frame 1). Nothing exports frames yet; this ticket carries metadata, not frames.
- Registry (per key) is at 90 % of `MAX_REGISTRY_BYTES`; adopted records are hash-chained and committed.

## Proposed placement: derived from the source bytes, stored per SOURCE REVISION, never per key
1. **Derive, do not declare.** `intake/aseprite.read_facts` additionally returns `animation`: per-frame durations (ms) and tags (name, from, to, direction, repeat) walked from the same header/chunk fields it already visits. No producer-declared field, so no handoff-package schema change and nothing to cross-check except the file itself.
2. **Carry.** A new optional `animation` field on `SourceRecord` (copied at adoption from the intake's re-read of the source; omitted when the source has one frame, via `drop_absent`, so every committed record stays byte-identical and no hash in the chain moves). `ArtifactRecord` and the registry get NO field. Bounds: `MAX_ANIMATION_FRAMES` 16 (the drawing tools' own `MAX_FRAMES`) and `MAX_ANIMATION_TAGS` 16: two NEW bounds for the owner (budgets rows PROPOSED).
3. **Intake refuses (QUARANTINED, new finding codes):** a duration of 0 or over 65535 ms; a tag whose from/to is outside the frame range or from > to; more frames/tags than the bounds; a duplicate or empty tag name; an unknown direction/repeat value. Existing findings unchanged.
4. **Export.** Per the planner's decision the runtime manifest does not change and the client never sees it. `export-runtime --animation` (opt-in, like `--atlas`) writes `animation.json` (record `runtime_animation`: catalog_id, release_id, entries[{visual_key, detail?, frame_durations_ms, tags[]}] for the keys whose source has more than one frame), taken from the SourceRecord of each entry's artifact. No flag, no file.
5. **Loop mode:** Aseprite has no per-sprite loop mode; the loop behaviour is per tag (`repeat`) and per tag direction (forward, reverse, ping-pong). So the contract carries `direction` and `repeat` per tag and does NOT invent a sprite-level loop mode; the ticket's "loop modes" is satisfied by those two per-tag fields. (If the owner wants a sprite-level default it is a new declared field, which I would put in the handoff package, not the registry.)

## Files touched
`visual_assets/store/intake/aseprite.py`, `intake/validator.py` + `contracts/intake.py` (finding codes), `contracts/source.py`, `adoption.py` / `setadoption.py` (copy the field), `contracts/animation.py` (new), `runtime_export.py`, `cli.py`, `config.py`, tests, store_contract.md, budgets.md, a 4-frame fixture built with the existing test builders. No registry, no manifest, no `src/`, no client.

## Alternatives (not chosen)
- Producer-declared per-package field: adds a schema change and a cross-check for facts the file already holds.
- Per-key registry field: grows the registry at 90 % of its budget and puts per-art data in a per-key file.

## Proof Plan
A 4-frame source with distinct durations and two tags round-trips: intake -> adoption record -> artifact -> `animation.json`, equal to the values written into the file; each planted bad case (zero duration, tag out of range, from > to, over-bound frames, duplicate tag) is QUARANTINED with its code; every committed SourceRecord is byte-identical after the change (equality over the corpus).
