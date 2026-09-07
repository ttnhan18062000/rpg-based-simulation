---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS
phase: done
date: 2026-09-07
tags: [content, architecture]
---

# TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS

## Title
Record explicit dispositions for ideas 50, 62, and 64 — none silently dropped

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) child 5 of 6. Three
ideas have no real path forward inside this epic's own scope and need an explicit, written
disposition rather than silent omission:
- **Idea 50 (Material-Gated Evolution)** — confirmed unbuilt (M9's own scoping, 2026-09-06): zero real
  code for `alt_outcome_kind`, never assigned to any shipped milestone.
- **Idea 64 (The Empty Chair)** — confirmed unbuilt despite M4's own "12 ideas shipped" PR title
  claiming otherwise: zero real code for `EconomicVacancyEvent`.
- **Idea 62 (Generations Misremember / `FidelityDeriver`)** — blocked on idea 63 (Belief/Religion) not
  existing; idea 63's own schema is flagged genuinely underspecified, confirmed unchanged.

## Scope
- For ideas 50/64: present the roadmap owner with a real decision — schedule as new feature work in a
  future milestone, or explicitly retire from the roadmap. This is not a build ticket; it produces a
  decision, recorded in `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`.
- For idea 62: confirm idea 63's real current schema status is unchanged (still underspecified) during
  Investigate, and record that idea 62 stays blocked pending idea 63's own future design work — not
  re-derive idea 63's design here.
- Correct the roadmap's own M4 section to stop implying idea 64 shipped (a partial correction was
  already made during M9's scoping — confirm it's sufficient, extend if not).

## Out of Scope
- Building ideas 50/64's mechanisms — a product decision, not this ticket's own scope.
- Designing idea 63 — a much larger, separate design question.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [ ] Ideas 50 and 64 each have a real, recorded decision (schedule vs. retire), not left ambiguous.
- [ ] Idea 62's blocked status on idea 63 is confirmed current and clearly recorded.
- [ ] The roadmap doc accurately reflects all three dispositions.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED` (the M9 ticket that originally found ideas 50/64 unbuilt)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
None — this is a documentation/decision ticket, not a code-change ticket.

## Assumptions / Open Questions
- Whether ideas 50/64 get scheduled or retired is a real product decision, not resolved here.

## Implementation Notes

### Investigation, 2026-09-07 (fork, orchestrator-bounded — investigate only, no decisions recorded here)

**Ideas 50 and 64 — confirmed still accurate, unchanged.**
- Idea 50 (Material-Gated Evolution): re-grepped `alt_outcome_kind` across `src/` and `tests/` — zero
  hits, same as M9's 2026-09-06 finding. Never assigned to any shipped milestone's epic doc.
- Idea 64 (The Empty Chair): re-grepped `EconomicVacancyEvent` across `src/` and `tests/` — zero hits,
  same as M9's 2026-09-06 finding.
- Roadmap doc correction already present and sufficient: `docs/plans/rpg_design_roadmap/
  rpg_design_roadmap.md` lines 141-147 (M4 section) and 288-291 both clearly state idea 64 is *not*
  actually among the "12 ideas shipped" in PR #115's headline claim, flagged as a real discrepancy for
  a future audit — accurately worded, does not imply idea 64 shipped. **No further edit needed here.**

**Idea 62 — THIS EPIC'S OWN PREMISE IS STALE AND FACTUALLY WRONG.** Both idea 62 and idea 63 have
**already shipped**, confirmed via `search_docs` + direct doc/code reading:
- Idea 62 (Generations Misremember / Chronicle Fidelity Drift) shipped 2026-09-05 as
  `TCK-20260905-CHRONICLE-FIDELITY-DRIFT` — real `src/domains/fidelity/` (`FidelityState`/
  `FidelityCarryForward`/`FidelityDeriver.derive()`/`FidelityExporter`/`FidelityImporter`), persisted
  in `CampaignState.historical_drift`, documented in `docs/mechanics/05_world_evolution.md` §8 and
  `docs/world/chronicle_fidelity_contract.md`.
- Idea 63 (Belief Grows Around Real History) shipped the same day as
  `TCK-20260905-BELIEF-INSTITUTION-DESIGN` — real `src/domains/belief_institution/` (mirrors the same
  3-layer Deriver/Model/Exporter-Importer pattern), persisted in `CampaignState.belief_institutions`,
  documented in `docs/world/belief_institution_contract.md` (`status: authoritative`,
  `last_verified: 2026-09-05`).
- Source: `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` lines 139-182 — both ideas'
  "Status update, 2026-09-05: shipped as..." entries, plus a documented correction (also dated
  2026-09-05) explicitly retracting the *original* "idea 62 blocked on idea 63" framing this epic's
  own scoping pass re-asserted on 2026-09-07 without re-checking.
- **The real remaining gap for both is NOT "doesn't exist yet" — it's the same "no live
  perception/motivation consumer" shape idea 56/57 had before this epic's own
  `ROUTE-BIAS-SCORING-INFRASTRUCTURE`/`LEGEND-FACT-ROUTE-BIAS-WIRING` tickets bridged them into
  `personality_bias`.** `docs/world/belief_institution_contract.md` even says so explicitly: "the whole
  chain ships with no live perception/motivation consumer yet." Neither `FidelityState`/
  `historical_drift` nor `BeliefInstitution`/`belief_institutions` has any live gameplay reader —
  disclosed, accepted gaps at ship time, structurally identical to what this epic already fixed for
  ideas 56/57.

This means this ticket's own Scope/Acceptance-Criteria text ("idea 62 stays blocked pending idea 63's
own future design work") is written against a false premise and needs re-scoping before
implementation, not straightforward execution as originally written. Handed back to the orchestrator
per my directive — no disposition decided, no doc edited, here.

### Decisions, 2026-09-07 (real user decisions, via `AskUserQuestion`, orchestrator-initiated)

**Ideas 50/64 — schedule for a future milestone**, not retire. Recorded as
`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` §M10 ("Deferred Ideas Backlog", scheduled,
not started) — no tracking epic created yet, no scope/sequencing decided beyond "this stays on the
active roadmap." Also corrected `rpg_dormant_mechanism_closure_plan.md` item 6 to record this.

**Idea 62/63 — stale-premise correction + new wiring ticket, not just a record correction.** The
epic's own scoping premise ("idea 62 blocked on idea 63 not existing") was factually stale — both
had already shipped 2026-09-05. Rather than merely correcting the record and leaving the real "no
live consumer" gap as a disclosed-but-deferred item, the user chose to scope a new child ticket now
— `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING` — matching the idea 56/57 `personality_bias`
pattern this epic already built. Corrected the stale premise in three places: this epic's own
Request Summary, `rpg_dormant_mechanism_closure_plan.md` item 5, and (implicitly, via the new
ticket's own Request Summary) established the real remaining scope.

## Test Summary
No test-affecting code was written directly by this ticket — it resolves to two documented product
decisions plus doc corrections and a new ticket scoped for follow-on implementation. No regression
risk from this ticket's own changes.

## Files Changed
- `tickets/todos/dormant-mechanism-closure/TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS.md` →
  moved to `tickets/done/`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (new §M10 "Deferred Ideas Backlog")
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md` (items 5 and 6 corrected/
  updated with ratified decisions)
- `tickets/inprogress/TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE.md` (Request Summary's stale
  idea-62 claim corrected; `## Related Tickets` and `## Implementation Notes` updated)
- `tickets/todos/dormant-mechanism-closure/TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING.md` (new,
  split ticket)

## Completion Summary
Two of the three ideas this ticket tracks (50, 64) got a real, evidenced disposition (schedule, not
retire) exactly as originally scoped. The third (62) turned out to need a correction, not a
disposition — the epic's own premise that it was blocked on idea 63 was already false when written,
both having shipped 2026-09-05 with a disclosed, deferred "no live consumer" gap. Real user decision
scoped a new child ticket to close that gap now rather than leave it deferred, growing this epic by
one ticket beyond its original 6.
