---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260902-SCHEMA4-DIVERGENCE-NOTE
phase: done
date: 2026-09-02
tags: [documentation]
---

# TCK-20260902-SCHEMA4-DIVERGENCE-NOTE

## Title
Annotate rpg_expected_schemas.html schema-4 ("Unified Modification") as built differently than proposed

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`docs/brainstorm/rpg_expected_schemas.html`'s schema-4 section ("Unified Modification", idea 4)
proposes a single `ModificationRecord` type (`kind: WOUND | SCAR | STATUS_FROZEN | BUFF | DEBUFF`)
unifying Wound/Scar/Status-Effect state. `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION` (done)
implemented this area of the system and its approved plan explicitly rejected that unified shape:
plan.md line 69 states "Do NOT touch: `WoundState`, `ScarState` themselves — do not add a
`status_type`/`kind` field to either, do not merge this record with them." The real, landed
implementation added a third genuinely separate typed record, `StatusEffectState` (`state.py:114`,
fields `kind`/`source`/`magnitude`/`expires_tick`), stored as `CombatComponent.status_effects:
List[StatusEffectState]` alongside the pre-existing `wounds`/`scars` lists — confirmed directly in
`src/core/state.py` and in `docs/core/state.md:23` ("`hp`, `readiness`, `alive`, `wounds`, `scars`,
`status_effects`"). Separately, `interaction_kind` landed on `InteractionComponent.kind` /
`InteractionUpdate.kind` (`docs/core/state.md:25`), not inside any modification record at all. This
was flagged during that ticket's Document-Update phase as a stale brainstorm/tracking artifact worth
a follow-up decision, but was explicitly out of that ticket's scope (brainstorm docs aren't part of
the standard per-family doc-update rules; updating the status badge was called "a judgment call
beyond this task"). This ticket makes that judgment call: add a status note to schema-4 recording
that the unified-record proposal was evaluated and rejected during implementation, pointing readers
to the real landed shape and the ticket ID, without rewriting the original proposal (which remains a
historical record of what was proposed).

## Scope
- Add a status/outcome annotation to the schema-4 ("Unified Modification") section of
  `docs/brainstorm/rpg_expected_schemas.html` (currently lines 715-732), stating that this proposal
  was evaluated and NOT built as originally shaped: no `ModificationRecord` type or unifying `kind`
  enum (`WOUND | SCAR | STATUS_FROZEN | BUFF | DEBUFF`) was created; `StatusEffectState` was added as
  a fourth, genuinely separate typed record following the existing `WoundState`/`ScarState`
  precedent, and `interaction_kind` landed on `InteractionComponent.kind` instead.
- Cite `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION` (done) as the implementing ticket and briefly
  state the rejection rationale (the approved plan's explicit "do not merge this record with
  Wound/Scar" instruction), so the note reflects the real reasoning, not a guess.
- Match this file's own existing convention for divergence/outcome notes where one already exists
  in this document (see the Trauma — Scar row's "Decided, not merely orphaned" / "Idea 17
  superseded" prose pattern at lines 491 and 953: a bolded lead-in phrase plus a cross-reference to
  the deciding ticket, written as prose, not a new badge/column). Since schema-4 (unlike idea 17)
  has its own dedicated section with an existing `<p class="loop-note">`, add the annotation as an
  additional paragraph in that section (e.g. a second `loop-note`-styled paragraph) rather than
  altering the existing proposal table's rows.
- Do not alter the existing `<table>` of proposed `ModificationRecord` fields (id 723-729) — those
  rows are the historical record of what idea 4 originally proposed and must stay legible as such.

## Out of Scope
- Do not touch any other `schema-N` section in `docs/brainstorm/rpg_expected_schemas.html` (e.g.
  schema-13's Trade & Team-Up, schema-44's Settlement Capacity) — none were found to reference the
  `ModificationRecord`/unified-modification concept during investigation.
- `docs/brainstorm/rpg_feature_atlas.html` has three rows referencing idea 4 (roadmap Milestone 2
  row at line 837, Cross-Cutting Risk "Modification untyped dict keys" row at line 878, and Shared
  Implementation Opportunities "Wire an already-built orphan" row at line 904) — these discuss idea
  4's blast-radius correction (17 real consumers) but do not themselves assert the unified-record
  shape will be built, so they are not factually wrong as written. Whether they also warrant an
  outcome/landed-shape note is left as an open question for a separate follow-up (see Assumptions /
  Open Questions) — do not edit `rpg_feature_atlas.html` in this ticket.
- Do not touch `src/core/state.py`, `docs/core/state.md`, or any other implementation/doc file — the
  real implementation is already correct and complete; this ticket only corrects a stale tracking
  artifact.
- Do not re-open or re-litigate the architecture decision itself (unified vs. separate records) —
  that decision was already made and implemented by TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION.

## Acceptance Criteria
- [x] schema-4 section of `docs/brainstorm/rpg_expected_schemas.html` contains a clearly-worded
      note stating the unified `ModificationRecord`/`kind` enum was NOT built as proposed.
- [x] The note names the real landed shape: `StatusEffectState` as a fourth separate typed record
      (not merged with `WoundState`/`ScarState`), and `interaction_kind` landing on
      `InteractionComponent.kind` instead of any modification record.
- [x] The note cites `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION` by ticket ID.
- [x] The original proposal table (fields `modification_id`/`entity_id`/`kind`/`magnitude`/
      `applied_tick, expires_tick`/`source`) is unchanged — diff review confirms only an addition,
      no edits to existing rows/text.
- [x] `docs/brainstorm/rpg_expected_schemas.html` remains valid HTML (renders without structural
      breakage — verify by viewing the file or a basic HTML lint, since this is a static reference
      doc with no automated test suite).

## Related Tickets
- TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION (done — the implementing ticket whose approved plan
  rejected the unified-record shape)

## Related Docs
- docs/core/state.md (real, current shape of `StatusEffectState`/`WoundState`/`ScarState`/
  `InteractionComponent` — reference only, not edited by this ticket)

## Related Stored Artifacts
- stored_artifacts/TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION/plan.md (source of the explicit
  rejection rationale, line 69: "Do NOT touch: WoundState, ScarState themselves — do not add a
  status_type/kind field to either, do not merge this record with them.")

## Related Code Areas
- docs/brainstorm/rpg_expected_schemas.html (schema-4 section, lines 715-732)
- src/core/state.py (`WoundState`, `ScarState`, `StatusEffectState` — reference only, confirms the
  real three-separate-records shape; not edited)

## Assumptions / Open Questions
- `layer: guidelines` was chosen because this is a cross-cutting brainstorm/tracking-doc convention
  edit, not gameplay mechanics, engine, or a specific subsystem; no more specific registered layer
  fits a brainstorm-document annotation.
- Whether `docs/brainstorm/rpg_feature_atlas.html`'s three idea-4-referencing rows (lines 837, 878,
  904) also need a landed-outcome note is left open — they were not found to be factually incorrect
  as currently written (they discuss blast-radius scoping, not the final record shape), so adding a
  note there was judged separate, optional follow-up scope rather than a "genuine additional
  reference" requiring a consistent edit in this same ticket. If a future reviewer disagrees, file a
  separate small ticket for that file.
- No existing brainstorm-doc-wide convention document (e.g. a style guide) was found specifying
  exactly how outcome/divergence notes should be formatted; this ticket infers the convention from
  the one concrete precedent in the same file (idea 17's "Decided, not merely orphaned" / "superseded"
  prose pattern) rather than inventing a new badge or column type.

## Implementation Notes
Added a second `<p class="loop-note">` paragraph immediately after the existing schema-4 loop-note
(line 731 → now followed by a new line 732) in `docs/brainstorm/rpg_expected_schemas.html`, matching
the file's own established divergence-note convention (bolded lead-in phrase + prose cross-reference
to the deciding ticket, as used at lines 491 and 953 for idea 17's "Decided, not merely orphaned" /
"superseded" pattern). The new paragraph:
- Opens with the bolded lead-in "Evaluated and rejected, not built as proposed."
- Cites `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION` (done) and quotes the approved plan's
  explicit rejection rationale (`plan.md:69`: "Do NOT touch: WoundState, ScarState themselves...").
- States the real landed shape: `WoundState`/`ScarState` untouched, plus a fourth genuinely separate
  typed record `StatusEffectState` (`src/core/state.py:116`), stored as
  `CombatComponent.status_effects: List[StatusEffectState]`, cross-referenced against
  `docs/core/state.md:23`.
- Notes `interaction_kind` landed on `InteractionComponent.kind`/`InteractionUpdate.kind`
  (`docs/core/state.md:25`), not inside any modification record — this detail was verified against
  the ticket's own Request Summary text and included to satisfy AC #2 fully (an earlier draft of the
  paragraph omitted it and was corrected before finalizing).
- Does not touch the pre-existing `<table>` (proposal fields, lines 723-729) or the section-lede
  (line 717) — both remain exactly as originally written, preserving the historical record.
No other schema-N section, `rpg_feature_atlas.html`, `src/`, or `docs/core/` files were touched, per
Out of Scope. Verified the diff is a single-line addition (`git diff`) and that the file still
parses as valid HTML (`html.parser` feed with no errors reported).

## Test Summary
This is a prose/HTML annotation to a brainstorm/design-tracking doc (`docs/brainstorm/`), which is
not part of the standard per-family `docs/` update rules and has no automated test suite or parity
ledger coverage — no automated test applies. Verification performed instead:
- `git diff -- docs/brainstorm/rpg_expected_schemas.html` reviewed to confirm the change is a single
  added line, with zero edits to the original proposal table or section-lede text.
- Python's built-in `html.parser.HTMLParser` fed the full file with no parse errors reported,
  confirming the document remains structurally valid HTML after the edit.
- All three cited facts were checked directly against source rather than taken on faith: `plan.md:69`
  in `stored_artifacts/TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION/`, `src/core/state.py:116`
  (`class StatusEffectState`), and `docs/core/state.md:23` and `:25`.

## Files Changed
- docs/brainstorm/rpg_expected_schemas.html (schema-4 section: one new `<p class="loop-note">`
  paragraph added after the existing one; original proposal table and lede text unchanged)
- tickets/inprogress/TCK-20260902-SCHEMA4-DIVERGENCE-NOTE.md (this ticket: Status, Acceptance
  Criteria checkboxes, Implementation Notes, Test Summary, Files Changed, Completion Summary)

## Completion Summary
Added a divergence/outcome note to the schema-4 ("Unified Modification") section of
`docs/brainstorm/rpg_expected_schemas.html`, recording that the proposed unified `ModificationRecord`
(with a `WOUND | SCAR | STATUS_FROZEN | BUFF | DEBUFF` enum) was evaluated and explicitly rejected
during `TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION`, and that the real landed shape keeps
`WoundState`, `ScarState`, and a new, separate `StatusEffectState` as three distinct typed records
(with `interaction_kind` landing separately on `InteractionComponent.kind`). The note follows the
file's own existing divergence-note convention (bolded lead-in + ticket cross-reference, added as
prose, not a new badge/table) and was added purely as an additional paragraph — the original schema-4
proposal table and lede text are unchanged, preserving the historical record of what was proposed.
No code, other schema sections, or other docs were touched.
