---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC
phase: done
date: 2026-08-06
tags: [simulation-quality, documentation, progression, faction]
---

# TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC

## Title
Document the COMBAT/PROGRESSION pillar boundary and the layer-lifecycle-trajectory gap (no new top-level pillar)

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
A 2026-08-06 session discussion (user-driven, following the SimQ epic closeout and full-corpus
calibration refresh) identified two related, real gaps in the current 10-pillar model, distinct
from the 4 candidates already checked and closed by `TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC`
(determinism, performance, checkpoint integrity, content/catalog health):

1. **COMBAT/PROGRESSION scope ambiguity.** COMBAT (`quality_scoring_contract.md` §5, lines 642-678)
   already correctly scores resolution mechanics (damage, tactical-modifier variety via
   `tactical_variety`, durability, wounds). PROGRESSION (lines 771-810) scores XP/level/skill/trait
   events, but only as isolated per-event deltas — there is no signal for whether an entity's
   overall **capability** (level + equipped-gear quality + wealth + skills, combined) is actually
   trending upward across its lifetime, which is the fuller "growing richer/stronger" sense of
   progression the user described. No event for equipping/upgrading gear currently exists
   (verified: no `equip`/`item_equipped` hit in `event_type_coverage.md` or
   `src/simulation_quality/pillars.py`).
2. **No per-layer lifecycle-trajectory signal for entity or faction layers.** WORLD already has a
   real trajectory-coherence rule — `trauma_hazard_broken` ("regional trauma monotonically
   increasing with no hazard_level effect", line 942) — that catches a degenerate *trend*, not just
   a single bad event. Neither PROGRESSION (entity layer) nor FACTION (faction layer, lines
   681-718: `faction_monopoly`, `all_factions_neutral`, `tension_oscillation` are threshold/event
   checks, not full-run trajectory checks) has an equivalent rule. Region and world layers are
   already covered by WORLD's existing rules (`trauma_hazard_broken`, `world_static`,
   `trauma_accumulation_broken`) — confirmed during this investigation, no gap there.

Applying the same §7.1-vs-§7.2 test `TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC` used: both gaps are
new scoring rules on existing usage questions ("are entities growing", "are factions interacting in
a balanced way"), not new usage questions requiring their own pillar. **Conclusion: no new
top-level pillar is justified.** PROGRESSION should own entity capability-trend + entity life-arc
coherence; FACTION should own a `trauma_hazard_broken`-style faction-trajectory rule.

## Scope
1. Add a new `### 7.6 Pillar Completeness Audit (2026-08) — Combat/Progression Boundary &
   Layer-Lifecycle Trajectory` subsection to `docs/simulation_quality/quality_scoring_contract.md`,
   directly after the existing `### 7.5` (same precedent pattern), recording:
   - The COMBAT (resolution-only) vs PROGRESSION (growth + capability trend, all layers of "the
     entity is getting richer/stronger") scope boundary, explicitly, so future scoring-rule
     additions know which pillar owns which question.
   - The layer-lifecycle-trajectory finding: entity and faction layers lack a
     `trauma_hazard_broken`-style rule; region/world layers already have one and need no change.
   - The "no new top-level pillar" conclusion and why (§7.1/§7.2 test applied).
   - Cross-references to `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE` and
     `TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY` as the implementing tickets.
2. Add a new `## 12. Layer-lifecycle trajectory & build-capability signals` axis to
   `docs/simulation_quality/extension_points.md` (after axis 11), documenting the same finding in
   that doc's axis format, cross-referencing quality_scoring_contract.md §7.6.
3. Add `### Finding 9 — COMBAT/PROGRESSION boundary and layer-lifecycle-trajectory gap identified,
   scoped (not yet implemented)` to `docs/audits/D20_simq_quality_status_review.md`'s Findings
   section, and a corresponding entry in that doc's `## Candidate Work Items` section noting tickets
   have now been filed (supersedes the "none filed yet" caveat in that section's own heading, for
   this specific item only — do not reword the heading itself, just note in the new entry's text
   that these two are filed).
4. Add `### 5. Add entity-layer and faction-layer lifecycle-trajectory signals — SCOPED (tickets
   filed)` to `docs/simulation_quality/current_state.md`'s `## Recommended next features` section.
5. Run `make knowledge-index-update` (all 4 edits are under `docs/`).

## Out of Scope
- Implementing either scoring rule, any new event emission, or any scorer code change — that is
  `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE` and
  `TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY`'s scope. This ticket is documentation-only.
- Re-litigating the 4 candidates already closed by `TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC` —
  this is a distinct, additional finding, not a re-audit.
- Prescribing exact delta values, tag names, or event schemas for the new rules — deferred to the
  two implementing tickets' own Investigate/Plan phases, per the Uncertainty Rule ("vague leads
  stay vague until evidence narrows them").

## Acceptance Criteria
- [ ] `quality_scoring_contract.md` has a new §7.6 subsection with the boundary rule, the gap
      finding, the conclusion, and both cross-references
- [ ] `extension_points.md` has a new axis 12 documenting the same finding in that doc's format
- [ ] `D20_simq_quality_status_review.md` has a new Finding 9 and a Candidate Work Items entry
      noting the two tickets are filed
- [ ] `current_state.md`'s Recommended next features has a new item 5
- [ ] `make knowledge-index-update` runs successfully
- [ ] `python3 tools/validate_frontmatter.py <each changed doc> --content-type doc` passes for all
      four files

## Related Tickets
- TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC (precedent — the 2026-07 audit this extends, different
  candidate set)
- TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE (implements the PROGRESSION side; cites this
  ticket's §7.6 as rationale; should land after this ticket)
- TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY (implements the FACTION side; cites this ticket's
  §7.6 as rationale; should land after this ticket)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT (642-678), §5 PROGRESSION
  (771-810), §5 FACTION (681-718), §5 WORLD DYNAMICS (898-958, `trauma_hazard_broken` at line 942),
  §7.1-§7.5 (Extensibility Protocol and its existing precedent)
- `docs/simulation_quality/extension_points.md` axes 9-11 (most recently added axes, same doc/style
  target)
- `docs/audits/D20_simq_quality_status_review.md` (Findings + Candidate Work Items sections)
- `docs/simulation_quality/current_state.md` (Recommended next features section)
- `docs/mechanics/01_entity_anatomy.md` §1-2 (attributes/derived stats), §5 (XP/level curve)
- `docs/mechanics/02_combat_laws.md` (Victory Outcomes, Hero's Journey generations)
- `docs/mechanics/05_world_evolution.md` (Regional Sovereignty, Trauma Score)

## Related Stored Artifacts
None yet — hotfix tier, self-evident intent per CLAUDE.md.

## Related Code Areas
None — documentation-only ticket. `src/simulation_quality/scorers/progression.py`,
`src/simulation_quality/scorers/faction.py`, and `src/simulation_quality/scorers/world_dynamics.py`
are cited as evidence but not modified here.

## Assumptions / Open Questions
- Assumes the region/world-layer coverage-is-already-sufficient finding (point 2 above) holds;
  re-verified directly against `quality_scoring_contract.md`'s live WORLD section during this
  session rather than assumed from memory.
- The exact scoring-rule design (delta values, tag names, whether entity capability-trend and
  entity life-arc coherence become one PROGRESSION rule or two) is intentionally left open here —
  that is the implementing tickets' Investigate/Plan work, not this ticket's.

## Implementation Notes
Added `### 7.6 Pillar Completeness Audit (2026-08)` to `quality_scoring_contract.md` directly after
the existing `### 7.5`, following the same precedent structure: boundary ruling (COMBAT stays
resolution-only, PROGRESSION owns capability-trend + life-arc coherence), a per-layer table
re-checking all 4 simulation layers against WORLD's `trauma_hazard_broken` bar, and the "no new
top-level pillar" conclusion with cross-references to the two implementing tickets. Added axis 12
to `extension_points.md` in the same style as axes 9-11. Added Finding 9 to
`D20_simq_quality_status_review.md` (after Finding 4, before the Full Pillar Health table) plus a
new row C in the Candidate Work Items table, explicitly noting it as the one exception to that
section's "none filed yet" framing. Added item 5 to `current_state.md`'s Recommended next features.
No code paths touched.

## Test Summary
`python3 tools/validate_frontmatter.py <file> --content-type doc` passed for all 4 changed files.
`make knowledge-index-update` ran successfully (4 files re-embedded, 2443 from cache, 0 deleted).
`run_static_precheck('TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC', 'hotfix', None)` returned
all PASS/NA across all 7 conditions.

## Files Changed
- `docs/simulation_quality/quality_scoring_contract.md` — added `### 7.6 Pillar Completeness Audit
  (2026-08)`
- `docs/simulation_quality/extension_points.md` — added `## 12. Layer-lifecycle trajectory &
  build-capability signals`
- `docs/audits/D20_simq_quality_status_review.md` — added Finding 9, Candidate Work Items row C
- `docs/simulation_quality/current_state.md` — added Recommended next features item 5

## Completion Summary
Recorded the COMBAT/PROGRESSION scope boundary (COMBAT stays resolution-only; PROGRESSION owns
entity capability-trend and life-arc coherence) and the layer-lifecycle-trajectory finding (entity
and faction layers lack a `trauma_hazard_broken`-style trajectory-coherence rule; region and world
layers already have one) across all 4 relevant docs. No new top-level SimQ pillar justified — both
gaps are new scoring rules on existing pillars, tracked by
`TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE` and
`TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY` (both still open in
`tickets/todos/simq-pillar-lifecycle-depth/`). Doc-only change; frontmatter and knowledge-index
checks both passed.
