---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION
artifact_type: investigation
tags: [architecture, schema, simulation-quality]
---

# Investigation — TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION

## Corpus scan, real data (2026-09-19)

A first-pass word list (`confirmed live`, `always-on`, `never fires`, `now works`, `gated off`)
against the atlas's own `desc` fields returned 7-30 hits per phrase — high enough that "currently"
alone needed direct inspection before trusting it as signal (30 hits, every one sampled was a real,
accurate status statement — "currently switched off", "currently scoped to", "currently-orphaned" —
not noise). Full scan across all three artifacts: 98 hits (61 atlas, 33 capabilities, 6 wiring-map
node labels).

## The wiring-map node labels, checked directly

Grep for the known phrase list against the Entity Operating Loop diagram's own `NODE["label"]`
syntax found 6 real hits, all redundant with an already-applied `classDef`:

- `SELF`, `MEM`: `"... — built correctly, GATED OFF by default"` next to `:::gated`.
- `INT`: `"... — no write path exists"` next to `:::bug`.
- `TRM`: `"... — near-death trauma-tagging exists but has zero callers"` next to `:::bug` (this
  session's own addition, from `TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-
  RESOLUTION`'s own `trauma` correction — already redundant the moment it was added, since the
  `:::bug` override carries the same fact).
- `EMO`, `COM`: `"... — live via ..."` clauses, redundant with the diagram's own `live` classDef.

All 6 removed, keeping only the "what it does" half of each label. `mechanism_wiring_map_
classdef.py` confirmed clean afterward (label text edits don't touch classdef assignment).

## The atlas/capabilities' 92 remaining hits, sampled

Read a representative sample (not all 92) across both artifacts, cross-checking each against real
code where the claim was checkable within this investigation's own scope:

- `entity-cognition#5` (Motivation & Doctrine, the motivating incident's own card): now reads
  "evaluation were *originally* live via the always-on Adventure route scoring path, but the
  [doctrine chain was deleted]" — past tense, already corrected, not a live stale claim.
- Several "zero callers" hits (Emotion, Time/Temporal Pressure, Cross-Episode Social Consequences,
  Building Sabotage) match already-closed orphan-state investigations elsewhere in this epic —
  consistent with the registry's own current `state` for each, not stale.
- The bulk of "currently X" hits describe genuinely accurate present-tense implementation facts
  (flag-gated states, unused code paths, scoped-but-not-general features) that match this session's
  own independently-derived findings where cross-checked (e.g. `status_effects`, `trauma`'s own
  orphan corrections this session are NOT yet reflected in atlas prose — worth flagging as a real,
  small follow-up: `status_effects`'s atlas card and `trauma`'s own card should be checked for
  "currently"-style claims that may now be stale given this session's own state corrections; not
  chased further here since this ticket's own scope is building the detector, not clearing its
  full backlog).

## Conclusion driving the disposition

No systematic staleness was found in the sampled 92 (beyond the two individual cases above, worth
a small separate follow-up, not filed as a blocking gap here). The volume is explained by an
authoring convention (this atlas/capabilities pair writes status inline with description as a
matter of style), not by neglect. Bulk-editing accurate prose to zero out a report-only detector's
hit count would itself be the Gate Integrity violation this project's own rules exist to prevent.
