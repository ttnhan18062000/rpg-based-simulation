---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION
phase: open
date: 2026-09-16
tags: [architecture, schema, simulation-quality]
---

# TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION

## Title
Detect status-vocabulary in atlas/capabilities/wiring-map prose — status belongs to the registry,
never to hand-written descriptions

## Status
OPEN

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
- New: `tools/mechanism_status_language_check.py` (proposed)

## Assumptions / Open Questions
The exact status-vocabulary word list needs deriving from a real corpus scan during
implementation, not guessed in advance — this ticket's own Scope item 1 lists known examples, not
an exhaustive list.

## Implementation Notes
To be completed during implementation.

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Not yet started.
