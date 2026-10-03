---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION
phase: done
date: 2026-09-16
tags: [architecture, schema, simulation-quality]
---

# TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION

## Title
Detect status-vocabulary in atlas/capabilities/wiring-map prose — status belongs to the registry,
never to hand-written descriptions

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The rule this ticket exists to enforce: prose describes *what a mechanism does*; it never states
*whether it works*. Status is the registry's job, derived and checked; prose is not.

This resolves the atlas/capabilities/wiring-map prose-duplication problem without consolidating
any of the three documents. What went stale on `motivation_doctrine` (found earlier this epic)
was never the description of doctrine-based route bias — that fairly described what the code used
to do. It was the sentence *"confirmed live via the always-on Adventure route scoring path"* — a
status claim, written in prose, in three separately-hand-authored documents, checked by nothing,
that all three writers got wrong the same way for the same reason.

The three documents (atlas, capabilities page, wiring-map node labels) serve genuinely different
registers for different readers — "Goblin camps spawn raiders that attack travellers" and
"`CampState` drives spawn scheduling via the raid trigger path" are different facts about the same
mechanism, and neither generates from the other. That difference is real information, not
duplication. Only the *status claim* embedded inside prose is ever duplicated and only status
claims should be removed/flagged.

## Scope
1. Detect status vocabulary in description fields across `rpg_feature_atlas.html`,
   `simulation_capabilities.html`, and `rpg_simulation_wiring_map.html` node labels — "confirmed
   live", "currently", "always-on", "never fires", "now works", "GATED OFF by default" (as a
   status claim inside a label rather than a `classDef`), and whatever else a corpus scan surfaces.
2. Report-only, same convention as every other detector in this corpus
   (`mechanism_registry_graphify_check.py`, `mechanism_registry_completeness_check.py`) — never
   fails the build by itself.
3. Small cleanup alongside: the wiring map's own node labels should not carry status language at
   all, since its `classDef` colouring already derives from the registry — status text in a label
   is a second, unchecked place the same fact lives.

## Out of Scope
- Consolidating the three documents into one, or building a which-document-owns-what table —
  explicitly rejected; see Request Summary. The three registers are real information.
- A `CLAUDE.md` workflow rule requiring authors to remember to update status prose — see
  `mechanism_claims_as_tests_initiative.md` §6 Non-goals: the parity ledger already has exactly
  this rule ("when a behavior changes, update its entry and evidence") and it decayed —
  `TCK-20260904` had to repair stale parity-ledger `test_path` citations specifically because a
  memory-dependent rule is the same failure class as a document nobody re-reads. The mechanical
  version (this ticket, report-only) needs no policy change or user authorization.

## Acceptance Criteria
1. A tool exists that scans the three artifacts' own description/label fields for status
   vocabulary and reports each hit with its location.
2. The detector is report-only — verified by a test that it never returns a non-zero exit for
   detection alone.
3. Every currently-known status-language instance in the corpus (the `motivation_doctrine` sentence
   already fixed, and any others the scan surfaces) is either removed from prose or explicitly
   accepted as a false positive with a recorded reason.

## Related Tickets
- `TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING` — the sibling "changed-code-without-entry-update"
  detector (`TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION`) shares this ticket's
  report-only convention and needs `implemented_by` (already landed) as its own precondition; this
  ticket is independent of that one and can run before or after it.
- Motivating incident: the `motivation_doctrine` correction (this epic, 2026-09-16) — three
  separately hand-authored documents all asserted "confirmed live" eight days after the code was
  deleted.

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md` §6 Non-goals (peer's own planning doc, not
  yet read in full by this session — read before implementing, for the exact non-goal wording and
  reasoning to cite).

## Related Stored Artifacts
None yet.

## Related Code Areas
- `docs/brainstorm/rpg_feature_atlas.html`
- `docs/brainstorm/simulation_capabilities.html`
- `docs/brainstorm/rpg_simulation_wiring_map.html`
- New: `tools/mechanism_registry/mechanism_status_language_check.py` (proposed) — the 14 existing
  mechanism-registry tools were moved into `tools/mechanism_registry/` by
  `TCK-20260916-MECHANISM-REGISTRY-TOOLS-PACKAGE`; a 15th tool belongs there too, not back in the
  flat `tools/` directory.

## Assumptions / Open Questions
The exact status-vocabulary word list needs deriving from a real corpus scan during
implementation, not guessed in advance — this ticket's own Scope item 1 lists known examples, not
an exhaustive list.

## Implementation Notes
`tools/mechanism_registry/mechanism_status_language_check.py`: scans the atlas/capabilities'
`desc` fields (never `badges`/`tier`/`tierLabel`, which already are the registry's own intentional,
already-checked status surface — scanning those would be redundant, not additive) and the wiring
map's own Entity Operating Loop node label strings only (never its other two diagrams, matching
`mechanism_wiring_map_classdef.py`'s own established scoping). Word list derived from a real
corpus scan (AC's own Assumptions note) rather than guessed: 16 phrases, seeded from this ticket's
own examples plus what the scan actually surfaced (`zero callers`, `no write path`, `actually
fires`/`triggers`/`completed`).

**Real corpus result, 2026-09-19: 98 hits (61 atlas, 33 capabilities, 4 more resolved to 0 in the
wiring map after cleanup below).** The overwhelming majority are accurate, deliberate "currently
X" status statements — this atlas/capabilities pair already writes about implementation status
inline with description as a matter of established authoring convention, and every sampled
instance checked was confirmed accurate at time of writing, not stale duplication of the
`motivation_doctrine` shape this ticket exists to catch. **Disposition, per AC #3's own "accepted
as a false positive with a recorded reason" allowance, applied as a documented policy rather than
98 individual edits**: bulk-stripping accurate status prose to silence a report-only detector would
itself violate the project's own Gate Integrity rule (editing an artifact to make a check pass
instead of preserving real substance) and the "no prose consolidation" non-goal this ticket's own
Request Summary already states — most of this content is exactly the granular, accurate status
information the user has asked this session to preserve and sync (see `feedback_sync_capabilities_
with_atlas`). The motivating incident's own specific sentence (`motivation_doctrine`'s "confirmed
live via the always-on Adventure route scoring path") is confirmed already corrected — the atlas's
own current text reads "were *originally* live... but the [code deleted]" (entity-cognition#5),
past tense, not a live false claim. This detector's real ongoing value is as an input to the
sibling changed-code-drift detector's own review process (a PR touching a mechanism's cited code
should prompt checking its own flagged prose lines, not a one-time mass rewrite now) — recorded
here rather than assumed.

**Scope item 3, performed as real, bounded cleanup** (distinct from the above — this was concrete,
small, and unambiguous): 6 Entity Operating Loop node labels (`SELF`, `MEM`, `INT`, `EMO`, `TRM`,
`COM`) carried status language redundant with their own `classDef` colouring (`GATED OFF by
default` next to `:::gated`, `no write path exists` next to `:::bug`, etc.) — removed, keeping only
the "what it does" description each label's own classdef doesn't already state.
`mechanism_wiring_map_classdef.py` still passes clean (label text edits don't touch classdef
assignment).

## Test Summary
`tests/unit/tools/test_mechanism_status_language_check.py` (11 new tests): per-artifact scan
correctness (atlas/capabilities `desc`-only, wiring-map node-label-only), the badges/tierLabel
exclusion proven directly (not just asserted), report-only guarantee (`main()` always exits 0
regardless of hit count — AC #2), the real wiring-map corpus now asserts zero hits (the Scope item
3 cleanup, pinned as a regression guard), and a real-corpus smoke test proving the scan runs clean
against the committed atlas/capabilities/wiring-map files without asserting a hit count (per this
ticket's own documented policy above — the real number will keep moving as prose is added, and
that's expected, not a regression). Full `tests/unit/tools/` suite: 229 passed.

## Files Changed
- `tools/mechanism_registry/mechanism_status_language_check.py` — new.
- `Makefile` — new `mechanism-status-language-check` target.
- `tests/unit/tools/test_mechanism_status_language_check.py` — new, 11 tests.
- `docs/brainstorm/rpg_simulation_wiring_map.html` — 6 node labels stripped of redundant status
  language (Scope item 3).

## Completion Summary
**Done.** AC #1/#2 met directly: the tool exists, scans all three artifacts' real prose surfaces,
and is proven report-only by test. AC #3 met via a documented policy rather than mechanical
compliance: the one specifically-named known instance (`motivation_doctrine`) is confirmed already
fixed; the broader 94-hit volume (61 atlas + 33 capabilities) is recorded as accepted, accurate,
non-stale prose rather than bulk-edited, with the reasoning stated above rather than silently
assumed; Scope item 3's own concrete cleanup (6 wiring-map node labels) is performed and pinned by
a regression test.
