---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES
artifact_type: investigation
tags: [simulation-quality, content]
---

# Investigation — TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES

## Current Behavior (file:line refs)

- `docs/brainstorm/design_merit_scorecard.html` — 65 idea rows (`<tr id="score-N">`, added by
  `TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX`), each with a Pillar Reach cell rendered as a raw
  count `N/10` (confirmed via direct parse of all 65 rows), no named pillars anywhere.
- `docs/simulation_quality/quality_scoring_contract.md` §5 (lines 542-1067) — the 10 real pillars
  confirmed exact: COGNITION, AGENCY & ACTION, COMBAT, FACTION & MILITARY, ECONOMY, PROGRESSION,
  SOCIAL, INFORMATION & BELIEF, WORLD DYNAMICS, NARRATIVE. Each pillar section has a fixed shape:
  Question / Pipeline / Event types scored / Signal-Delta-Tag table / (optional) Loop signal /
  (optional) Real producer notes / (optional) Traceability path.
- `src/observability/event_extractor.py` — 90 real, distinct `event_type=` string literals
  confirmed via direct grep (ground truth for "what event types actually exist in shipped code").
- `docs/simulation_quality/event_type_coverage.md` (Certified Level 1 — Authoritative,
  `last_verified: 2026-08-13`) — a pre-existing, already-complete audit of every one of those 90
  event types, classified `scored` (84), `no_engine_path` (1), `p0_a_blocked` (3), or
  `unscored_intentional` (26), each with an evidence-grounded reason. This doc already contains the
  "explicit, written reason it's intentionally excluded" disposition the ticket's own AC #2 asks
  for, for the large majority of the event types §5's own tables don't reference — it is simply not
  cross-referenced FROM `quality_scoring_contract.md` §5, which is the doc the ticket names as
  needing the update.
- `docs/brainstorm/idea_index.json` (built by `TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX`) —
  confirms all 65 scored ideas are owned by M1-M6 (M1=20, M2=16, M3=5, M4=12, M5=8, M6=4), matching
  the epic ticket's own "M1-M6, all confirmed DONE" framing — item 2 (event-type confirmation)
  genuinely applies to the full 65, not a subset.

## Real, Corrected Finding: Scope Item 3 Is Mostly Cross-Referencing, Not New Rule Authoring

Cross-referencing the real 90 event types against every backtick-quoted term in
`quality_scoring_contract.md` §5 found 15 real event types with zero mention anywhere in that
document: `attribute_changed`, `belief_contradiction`, `biological_state_changed`,
`entity_faction_changed`, `entity_role_changed`, `equipment_durability_changed`, `item_equipped`,
`item_unequipped`, `recipe_learned`, `route_new_query`, `scar_gained`, `skill_cooldown_started`,
`stamina_changed`, `wound_healed`, `wound_sustained`.

Checking each against `event_type_coverage.md` (not assuming the gap was real just because §5 was
silent) found:

- **14 of the 15 are already fully dispositioned** in `event_type_coverage.md` §5 "Unscored
  Intentional" (lines 341-370), each with a real, specific, evidence-grounded reason (e.g.
  `biological_state_changed`/`stamina_changed` are "high-volume, same class as `movement`";
  `entity_role_changed`/`entity_faction_changed` are explicitly noted as having gained real live
  producers this session — `TCK-20260824-OCCUPATION-CHANGE-TRIGGER` and
  `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE` — with the disposition explicitly unchanged by
  either landing, since it reflects SimQ-scorer wiring, not producer existence). These 14 satisfy
  AC #2's "explicit, written reason it's intentionally excluded" already — the real gap is that
  `quality_scoring_contract.md` §5 doesn't say so.
- **1 of the 15 — `route_new_query` — is a genuine, previously undocumented gap**, missed even by
  the authoritative `event_type_coverage.md` audit. Confirmed real (`src/observability/
  event_extractor.py:662`, `src/observability/event_shapers.py:814`, both citing
  `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`), and confirmed NOT in
  `InformationScorer.EVENT_TYPES` (`src/simulation_quality/scorers/information.py:19-27`) — it is a
  real, live, unscored INFORMATION & BELIEF-pillar signal (a new information-seeking query started,
  the natural sibling of the already-scored `belief_assimilated`/`belief_updated`/`belief_stale`).
  This is the one genuinely new rule this ticket authors.

**Resolution for Scope item 3:** author the one real new rule (`route_new_query` →
InformationScorer), and add a single cross-reference note in `quality_scoring_contract.md` §5
pointing at `event_type_coverage.md` §5 for the other 14 already-dispositioned event types — not 14
redundant, duplicated rule-authoring passes that would fork the single source of truth
`event_type_coverage.md` already is.

## Named-Pillar Mapping for All 65 Ideas (Scope item 1)

Full mapping table authored directly into `docs/brainstorm/design_merit_scorecard.html`'s Pillar
Reach column (Implement phase). Methodology: for the ~45 ideas this session directly implemented
(M2-M6 — ideas 32-65 plus M2's own 14-ticket batch), pillar assignment is grounded in first-hand
knowledge of the real shipped mechanism (e.g. idea 39 → FACTION & MILITARY/COMBAT/SOCIAL, confirmed
against `entity_faction_changed`'s real semantics from this same session's own M6 work). For the 20
M1 ideas (small wiring fixes/investigations predating this session, e.g. "Wire the nine orphans",
"Prune dead cognition schema"), assignment uses the scorecard's own title + "take" column text
(already-established short mechanism summaries) rather than a fresh per-idea code investigation —
disclosed here as a real, deliberate scope boundary given 65 ideas is too broad for exhaustive
fresh code verification of items this ticket didn't itself implement. Idea 9's own documented
precedent (`Pillar Reach` axis note: "found by an independent calibration check surfacing a real
split reading on idea 9, 0/10 originally vs. 6/10 independently derived") establishes that this
axis's own count is expected to be corrected by a fresh, independent derivation, not force-matched
to the original — so where my named-pillar judgment genuinely differs in count from the original
raw number, the count is corrected to match the named list, not the reverse (same disposition
already applied to idea 9 itself). 8 of 65 ideas (8, 9, 15, 16, 17, 18, 19, 42) are 0-1/10 raw
governance/doc-fix/investigation-only cards with no real event surface — these keep their
near-zero Pillar Reach unchanged (0 or the one pillar the doc fix directly concerns).

## Disposition: Ideas 56/57/62 (the 3 Flagged Dormant Ideas)

Confirmed via direct grep (`event_type=`, `SimulationEvent`, `ObservabilityEvent` across
`src/domains/fame/`, `src/domains/fidelity/`, `src/systems/social_systems/loyalty_drift.py`): **none
of the 3 emit any `SimulationEvent`/`ObservabilityEventEnvelope` of their own at all** — not even an
unscored one. `FameDeriver`/`FidelityDeriver` operate entirely at the episode-boundary
`CampaignState` derivation layer (`CampaignOrchestrator._advance_state()`), and
`LoyaltyDriftService.compute_loyalty_pressure()` is a pure function whose output feeds directly into
`PartyLifecycleService.effective_defection_threshold()` as a parameter — neither layer touches the
per-tick `event_extractor.py`/`event_shapers.py` machinery SimQ's whole event-based architecture is
built on. This is a structurally different, and more fundamental, gap than the 15 real-but-unscored
event types found above: those 15 are real engine events with no scorer wiring; these 3 ideas have
no event of any kind to wire in the first place. **Disposition:** "no live event type exists yet,
tracked as a known gap" (per the ticket's own Request Summary framing) — not silently dropped from
the 65-idea list (each still receives a real named-pillar mapping above, reflecting the pillars they
would strengthen "once actually built and running", per the axis's own forward-looking question
text) and not fabricated a placeholder SimQ rule for an event that structurally cannot fire. Building
the per-tick↔episode-boundary bridge these 3 would need is out of this ticket's scope (already
flagged as a real, disclosed follow-up gap by the M5/M6 tickets that shipped them).

## Docs Requiring Update

- `docs/brainstorm/design_merit_scorecard.html`: Pillar Reach column, all 65 idea rows — count
  replaced with named pillar list.
- `docs/simulation_quality/quality_scoring_contract.md`: §5 INFORMATION & BELIEF section gains a
  new `route_new_query` signal row; a new cross-reference note added near the top of §5 pointing
  future readers at `event_type_coverage.md` §5 for already-dispositioned unscored-intentional
  events.
- `docs/simulation_quality/event_type_coverage.md`: `route_new_query` moves from "not documented at
  all" to a new §1.1 row (now genuinely scored).

## Parity Ledger Overlap

**Correction, found during Parity phase:** this ticket's `src/` change has no Mechanics Bible law or
gameplay-outcome impact (SimQ is explicitly out-of-band instrumentation —
`quality_scoring_contract.md` §1's own "Zero Simulation Impact" contract), but `docs/parity_ledger/
infrastructure.yaml`'s `INFRA-245` already exists as a real, tracked entry documenting
`InformationScorer`'s full rule coverage by name ("InformationScorer covers all contract §5
INFORMATION & BELIEF rules: belief_active, ..."). Adding an 8th rule to that same class makes
INFRA-245's own text stale (it no longer lists all real rules) — updated via
`tools/parity_ledger_writer.py::write_entry()` to add `information_seeking_active` to the list and
note `route_new_query`'s addition in `v2_evidence`. `test_path` (the whole
`test_information_scorer.py` file, not a specific method) already covers the new tests without
needing its own update. No new parity ID needed — this is an amendment to an existing, still-accurate-
in-spirit entry, not a new behavior class.

## Prior Work

- `TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS` — the ticket that added `belief_stale`/
  `decision_diverged_by_belief`/etc. to InformationScorer; this ticket's own `route_new_query`
  addition follows the exact same shape.
- `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE` — the ticket that added `route_new_query`'s real
  emission in the first place, apparently without ever registering it with InformationScorer or
  this coverage doc — the actual root cause of the gap this ticket closes.
- `TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX` — built `idea_index.json`, used above for milestone
  ownership verification.

## Risks and Open Questions

- The 20 M1-idea pillar assignments (title/take-based, not fresh-code-verified) are a lower-
  confidence tier than the 45 M2-M6 assignments — disclosed above, not silently presented as
  equally rigorous. A future session revisiting any specific M1 idea's real pillar reach should
  re-verify against real code, not just trust this pass.
- `route_new_query`'s calibration_hits will very likely be 0 in every existing calibration profile
  (same `ENABLE_ADVENTURE_ROUTING`-adjacent gating class as several sibling INFORMATION events) —
  this is expected and does not block adding the scoring rule itself; `TCK-20260906-SIMQ-
  CALIBRATION-AND-COMPLETENESS` (the next child ticket) is where a real calibration run confirms or
  disproves this.

## Anti-Drift Hazards

- Do not duplicate `event_type_coverage.md`'s own disposition text into `quality_scoring_contract.md`
  verbatim — cross-reference it, so future edits to the disposition only need to happen in one
  place (the existing, actively-maintained coverage doc).
- Do not force every idea's named-pillar count to exactly match its pre-existing raw count when
  the assignment's own judgment disagrees — idea 9's own precedent in the same document explicitly
  permits and expects correction.
