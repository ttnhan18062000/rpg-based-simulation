---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ
phase: done
date: 2026-08-24
tags: [information, feature-flags]
---

# TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ

## Title
Scope Secrets, Confidence & Selective Disclosure, Sequenced After Belief Assimilation Goes Live

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
This idea extends the Information Sourcing/Trust system almost exactly, but that whole system is flag-gated OFF (ENABLE_BELIEF_ASSIMILATION-adjacent) with a documented trap where flipping the flag alone activates a phase with nothing to process. The author wants this ticket scoped now, sequenced after whatever ticket gets that system live.

## Scope
- Scope schema extensions for secrecy/confidence-tier metadata and selective-disclosure logic, extending the Information Sourcing/Trust system (src/domains/information/)
- Land scope/design artifacts only -- no implementation until ENABLE_BELIEF_ASSIMILATION is confirmed live by TCK-20260824-ROLLOUT-FLAG-DECISIONS' flag decision
- Name TCK-20260824-ROLLOUT-FLAG-DECISIONS as a blocking dependency in Related Tickets, with SEQUENCE.md placing this strictly after it
- State whether any DECEPTIVE_DETECTED wiring reuses trust.py's existing delta (-0.25, currently zero callers) or needs a new writer
- Document that idea 13/C14's SocialBond.sentiment ledger and this concern's SourceTrustEntry/source_trust ledger are structurally separate, with no shared implementation

## Out of Scope
- Any implementation before C1's flag decision lands and actually activates the system generally (not just per-world compile-time seeding, which today only populates Branch A for the urban_political profile)
- Idea 12's flag-free alternative path (wiring BeliefContradictionService into an always-on strategic_intelligence phase, bypassing the flag) -- if C1 or a related ticket takes that path instead, this ticket's sequencing premise needs re-evaluation

## Acceptance Criteria
- [x] Ticket scope is limited to design/plan artifacts (schema extension for secrecy/confidence-tier metadata, selective-disclosure logic) -- no implementation lands until ENABLE_BELIEF_ASSIMILATION is confirmed live by C1's flag decision
- [x] Related Tickets explicitly names C1's resulting ticket ID as a blocking dependency, and SEQUENCE.md places this strictly after it
- [x] Any DECEPTIVE_DETECTED wiring states whether it reuses trust.py's existing delta or needs a new writer
- [x] Ticket documents that SocialBond.sentiment (C14) and SourceTrustEntry/source_trust are structurally separate ledgers with no shared implementation

## Related Tickets
- TCK-20260702-SIMQ-UPLIFT2-INFORMATION
- TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER
- TCK-20260703-SIMQ-UPLIFT3-BRANCH-B
- TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE
- TCK-20260817-HOTFIX-BELIEF-ASSIMILATED-TESTS-BYPASS-SHADOW-SHAPERS
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (blocking dependency -- this ticket must not be scheduled for implementation before C1's ENABLE_BELIEF_ASSIMILATION decision lands)
- TCK-20260824-AFFECTION-CONTRACT-GATE

## Related Docs
- docs/audits/D19_domain_phase_inventory.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/information/schema.py
- src/domains/information/trust.py
- src/domains/information/contradiction.py
- src/domains/information/phase.py
- src/domains/information/router.py
- src/domains/information/assimilation.py
- src/core/strategic.py
- src/domains/optimization/feature_flags.py

## Assumptions / Open Questions
- Hard sequencing dependency on TCK-20260824-ROLLOUT-FLAG-DECISIONS (C1) -- must not be scheduled for implementation before C1's ENABLE_BELIEF_ASSIMILATION decision lands and actually activates the system generally
- What "system live" precisely means (flag ON alone vs. a generalized non-compile-time-seed writer for Branch A) needs precise definition before real work starts
- If C1 or a related ticket takes idea 12's flag-free alternative path instead, this ticket's sequencing premise needs re-evaluation
- `layer: strategy` chosen because the Information Sourcing/Trust system implements knowledge management/perception within strategic cognition (Mechanics Bible ch04); no `information`-specific layer is registered in `registries/layer_registry.jsonl` as of this ticket's creation

**Resolved during Implement (this session), citations in Implementation Notes below:**
- **C1 blocker status — RESOLVED.** `TCK-20260824-ROLLOUT-FLAG-DECISIONS` is done and `ENABLE_BELIEF_ASSIMILATION` is confirmed `FeatureMode.ON` (`src/domains/optimization/feature_flags.py:37`). See Implementation Notes Step 1.
- **"System live" definition — RESOLVED.** Not just flag-ON-alone and not just Branch A's per-world compile-time seed: `TCK-20260824-LEAD-CONTRADICTION-WIRING` added a real, general, non-compile-time-seed per-tick production writer inside `InformationBeliefPhase.apply()` (phase.py branch 4, lines 110-166, derives observations from live entity/world state every tick the phase runs) plus an always-on upstream writer for Branch B's `unknowns` input (`LeadContradictionSystem.enforce()`, `pipeline.py:356`, no feature flag). Caveat carried forward: this resolves the contradiction-detection slice only: the full router/trust-update cycle's live query volume outside `urban_political` remains comparatively thin (Branch A still compile-time-seeded for that one profile only; Branch B still routes one "first unknown" per actor per tick). See Implementation Notes Step 2.
- **Idea-12 flag-free-path re-evaluation trigger — RESOLVED, not taken.** `TCK-20260824-LEAD-CONTRADICTION-WIRING` built a structurally separate, orthogonal always-on system (state-scan based, for `resource`/`location`/`person`/`object`/`event` lead kinds only) while leaving `BeliefContradictionService`/`InformationBeliefPhase` exactly where they were: gated behind `ENABLE_BELIEF_ASSIMILATION` (`pipeline.py:173`). This is not idea 12's flag-free alternative path, so this ticket's sequencing premise does not need re-evaluation. See Implementation Notes Step 2.
- **`DECEPTIVE_DETECTED` reuse-vs-new-writer product-calibration question** — left open, unchanged. This ticket's AC only requires *stating* the reuse decision (done, Step 4 below); whether the existing unvalidated `-0.25` delta is acceptable as shipped or needs recalibration is a human/product decision for a future implementation ticket, not resolvable by this scope-only ticket.
- **`layer: strategy` registry note** — left exactly as originally written; still accurate, no registry change needed for a scope-only ticket.

## Implementation Notes

### Step 1 — C1 (TCK-20260824-ROLLOUT-FLAG-DECISIONS) status confirmed live

`ENABLE_BELIEF_ASSIMILATION` is `FeatureMode.ON` (`src/domains/optimization/feature_flags.py:37`,
confirmed by direct read). `TCK-20260824-ROLLOUT-FLAG-DECISIONS` (C1) is in
`tickets/done/TCK-20260824-ROLLOUT-FLAG-DECISIONS.md`. `docs/guidelines/intentional_divergences.md`'s
DEV-003 entry (~line 1445) records this decision as rationale class **Stabilized**, status
**ACTIVE**.

`src/engine/pipeline.py:173` shows `InformationBeliefPhase.apply()` remains invoked via
`run_phase("information_belief", ..., "ENABLE_BELIEF_ASSIMILATION")` — i.e. the flag being ON does
not make the phase unconditional; it is a real gate that is currently open, not removed.

Conclusion: this satisfies AC1's and Out of Scope's "confirmed live" condition for *sequencing*
purposes, but does not authorize this ticket itself to implement anything — this ticket's own
Scope section's unqualified "design/scope artifacts only" instruction controls regardless of flag
state. No src/ file was read for edit; feature_flags.py and pipeline.py were cited, not touched.

### Step 2 — TCK-20260824-LEAD-CONTRADICTION-WIRING does not force re-evaluation

Citations: `src/engine/pipeline.py:356` adds a new, always-on, no-flag
`run_phase("lead_contradiction", ...)` call, calling `LeadContradictionSystem.enforce()`
(`src/engine/pipeline_phases/lead_contradiction.py`). That phase's docstring (lines 60-64) is
explicit: "CONCEPT contradiction is observation-shaped ... routed through
`BeliefContradictionService.detect()` instead" — i.e. this always-on phase explicitly does not
cover `concept`/`information` lead kinds. `src/domains/information/bridge.py:40`
(`ObservationBeliefBridge.process_observation()`) now calls the real
`BeliefContradictionService.detect()`. `src/engine/pipeline.py:173` confirms
`InformationBeliefPhase.apply()` — which contains this wiring — remains flag-gated, not bypassed.

Conclusion: `TCK-20260824-LEAD-CONTRADICTION-WIRING` built a structurally separate, orthogonal
always-on system for non-concept lead kinds while leaving `BeliefContradictionService`/
`InformationBeliefPhase` flag-gated exactly as before — it did **not** take Out of Scope's named
re-evaluation trigger (idea 12's flag-free alternative path). This ticket's sequencing premise
(blocked on C1, not superseded by an always-on bypass) holds unchanged. No src/ file was edited;
`pipeline.py`, `lead_contradiction.py`, and `bridge.py` were cited only. The already-`tickets/done/`
`LEAD-CONTRADICTION-WIRING` ticket and its `stored_artifacts/` were not reopened or modified.

### Step 3 — Design Sketch (non-binding, for a future implementation ticket)

This subsection is a non-binding design sketch for a future implementation ticket. No `src/` file
is created or modified by this ticket.

**Proposed schema fields.** A `confidence_tier` concept and a `secrecy_level` field, added as
additive dataclass fields in the same pattern `TCK-20260824-RELATIONSHIP-ROLE-FIELD` already used
for `SocialBond` (additive field, authoritative-update-only setter, one real consumer, doc+parity
in the same session). Candidate homes: `InformationSourceProfile`
(`src/domains/information/schema.py` — today's fields are `accuracy`, `freshness`, `bias`,
`cost_gold`; no secrecy/confidence-tier field exists) and/or `SourceTrustEntry`
(`src/core/strategic.py:341-346` — today's fields are `entity_id`, `trust: float = 0.5`,
`interactions: int = 0`, `last_outcome: Optional[str]`; no such field exists there either).

**Composition, not duplication, with existing certainty concepts.** The new "confidence tier"
concept must compose with, not duplicate, the existing `LeadCertainty` enum
(`PRECISE`/`APPROXIMATE`/`VAGUE`/`EXHAUSTED`, `src/core/strategic.py:34-39`) and
`NormalizedInformationResponse.certainty: float`. This is a named schema-collision risk that any
real future design must resolve before implementation — a naive new field could silently overlap
with what `LeadCertainty`/`certainty` already express.

**Selective-disclosure routing sketch (illustrative only, not an applied diff):**

```
# Non-binding sketch — illustrates where a future disclosure gate would live,
# NOT a diff against router.py.
#
# InformationQueryRouter.route() today (src/domains/information/router.py:22-106)
# ranks candidates by expected_certainty = accuracy * trust_score (line 87) and
# returns the top-3, with no disclosure gate. A future design would add a filter
# step before the top-3 selection:
#
#   for candidate in ranked_candidates:
#       if candidate.secrecy_level > requester_trust_or_relationship_standing:
#           exclude_or_redact(candidate)
#
# "requester_trust_or_relationship_standing" would need to be sourced from the
# requester's own SourceTrustEntry / relationship state — NOT from
# SocialBond.sentiment (see AC4 finding below: that ledger is structurally
# separate and must not be reused here).
```

**Live-traffic caveat, carried forward from the investigation.** Branch A's query/response cycle
is still `urban_political`-only per `docs/audits/D19_domain_phase_inventory.md` §3 (PP-04 row),
and Branch B only ever routes one "first unknown" per actor per tick
(`src/domains/information/phase.py:87-107`). A future design must not assume broad live query
volume exists yet outside that one profile.

No `src/domains/information/schema.py`, `router.py`, `trust.py`, or `src/core/strategic.py` file
was created or modified for this sketch; no new `.py` file was added anywhere.

### Step 4 — DECEPTIVE_DETECTED delta-reuse decision (AC3)

Any future `DECEPTIVE_DETECTED` wiring **reuses the existing `-0.25` delta via the existing
`"DECEPTIVE_DETECTED"` outcome branch already in `src/domains/information/trust.py:49-50`**
(`SourceTrustUpdateService.update()`) — no new writer is needed, because the branch already exists
and is semantically correct for the deceptive-source case; it is currently just uncalled
(`grep -rn "DECEPTIVE_DETECTED" src/ tests/` returns exactly one hit, the branch definition itself
— zero production or test callers).

Caveat: the `-0.25` value itself is unvalidated (zero callers, zero balance-measurement history
ever run against it) — a future implementation ticket must treat it as a placeholder needing
balance validation, not a proven constant, even though the branch/delta itself is the one being
reused rather than replaced with a new writer.

`src/domains/information/trust.py` was not touched — the reuse decision is stated in prose only;
no new outcome branch was added, no caller was wired, `SourceTrustUpdateService.update()` remains
uncalled after this ticket.

### Step 5 — SocialBond.sentiment vs. SourceTrustEntry structural-separation finding (AC4)

`SocialBond.sentiment` (`src/core/models/social.py:14-20`: `float`, `-1.0` to `1.0`,
"Bias/Liking"), living in `SocialComponent.bonds: Dict[int, SocialBond]`
(`src/core/models/social.py:32-43`) — a **Social** domain relationship/affection ledger — versus
`SourceTrustEntry`/`StrategicComponent.source_trust` (`src/core/strategic.py:341-346,393`: `float
trust` `0.0`-`1.0`, "Trust score for a specific information source") — a **Strategic Cognition**
domain information-source-reliability ledger.

Conclusion, in the ticket's own AC4 wording: these are **structurally separate ledgers with no
shared implementation** — different component (`SocialComponent` vs `StrategicComponent`),
different dataclass, different semantics, no cross-reference or shared update path between the two
files. Corroborating evidence: `TCK-20260824-AFFECTION-CONTRACT-GATE` (still `OPEN`,
`tickets/todos/m1-quick-wins/`) already independently excludes "idea 25's separate trust ledger
(PP-04-adjacent)" from its own scope, treating the two ledgers as separate concerns.
`TCK-20260824-RELATIONSHIP-ROLE-FIELD` (done) added a third, also-separate concept
(`RelationshipRole` enum on `SocialBond`) without touching `source_trust` at all, reinforcing the
separation.

Forward-looking constraint: any future secrecy/disclosure design must not reach into
`SocialBond.sentiment`.

`src/core/models/social.py` and `src/core/strategic.py` were not touched — citation only, no field
added to either dataclass by this ticket.

## Test Summary

N/A — no code changes. Per `test_plan.md`'s Regression Surface finding, no `src/` file is created,
modified, or deleted by this ticket, so no regression surface exists to protect. No pytest command
was run.

## Files Changed

- `tickets/inprogress/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ.md`
- `staging_artifacts/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ/investigation.md`
- `staging_artifacts/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ/test_plan.md`
- `staging_artifacts/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ/plan.md`

No `src/`, `docs/`, or `config/` file was created, modified, or deleted.

## Completion Summary

All four Acceptance Criteria are satisfied by design/scope artifacts only, with zero `src/` or
`config/` changes. AC1 is satisfied because C1 (`TCK-20260824-ROLLOUT-FLAG-DECISIONS`) is
confirmed done and `ENABLE_BELIEF_ASSIMILATION` is confirmed `FeatureMode.ON`
(`feature_flags.py:37`), while this ticket's own deliverable stays scoped to prose/design content
in its own Implementation Notes (Step 3's non-binding design sketch). AC2 is satisfied because
`## Related Tickets` already names C1 as a blocking dependency and
`tickets/todos/m1-quick-wins/SEQUENCE.md` already places this ticket strictly after it. AC3 is
satisfied by Step 4's explicit statement that any future `DECEPTIVE_DETECTED` wiring reuses the
existing `-0.25` delta/branch in `trust.py:49-50` rather than adding a new writer. AC4 is satisfied
by Step 5's explicit citation-backed finding that `SocialBond.sentiment` and
`SourceTrustEntry`/`source_trust` are structurally separate ledgers with no shared implementation.
Any real implementation of the secrecy/confidence-tier schema extension and selective-disclosure
logic sketched in Step 3 requires a new, separate, not-yet-created future ticket.
