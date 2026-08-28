---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ
artifact_type: investigation
tags: [information, feature-flags]
---

# Investigation — TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ

## Context-Search Step (mandatory, run before any grep/file read)

Both required semantic tools were attempted first, per CLAUDE.md's hard rule, and both are
confirmed unavailable in this environment — this is a pre-existing environment gap, not a skipped
step:

- `mcp__knowledge-search__search_docs` (query: "Scope Secrets, Confidence & Selective Disclosure,
  Sequenced After Belief Assimilation Goes Live secrets disclosure selective information trust")
  returned `{"error":"index not found","action":"run make knowledge-index"}`.
- `python3 tools/knowledge_search.py query "secrets disclosure selective information trust
  confidence tier" --top-k 5` returned `knowledge index not found — run make knowledge-index`.
- `graphify query "secrets disclosure selective information trust"` and a follow-up `graphify
  query "belief contradiction lead concept information source trust deceptive detected"` both
  succeeded and returned real code nodes (`SourceTrustEntry`, `SourceTrustUpdateService`,
  `TrustBoundaryPhase`, `BeliefContradictionService`, `ObservationBeliefBridge`,
  `_is_lead_contradicted()`), which were used as the primary file targets below, consistent with
  the orchestrator's own prior graphify results.

Neither search tool surfaces anything for "secrets"/"confidence-tier"/"selective disclosure" as
concepts — because, confirmed below, no such mechanism exists in `src/` today. This is expected:
this ticket's own AC is to scope a *new* schema extension, not find an existing one.

## Current Behavior

**Information Sourcing/Trust system** (`src/domains/information/`) is a Phase 5 subsystem with no
secrecy/confidence-tier/selective-disclosure concept anywhere in it today:

- `src/domains/information/schema.py` — `InformationSourceProfile` (source capabilities:
  `accuracy`, `freshness`, `bias`, `cost_gold`), `InformationQuery`, `NormalizedInformationResponse`
  (`answer_kind`: `KNOWN_FACT`/`PARTIAL_LEAD`/`RUMOR`/`UNKNOWN`/`CONTRADICTION`),
  `InformationAssimilationResult`. No field anywhere carries a secrecy level, confidence tier
  distinct from `certainty`, or a disclosure-eligibility flag.
- `src/domains/information/trust.py:16-59` — `SourceTrustUpdateService.update()`: static method
  taking `(entity, source_entity_id, outcome, current_tick)`, `outcome` one of `"CONFIRMED"`
  (delta `+0.08`, line 44), `"PARTIALLY_CONFIRMED"` (`+0.03`, line 46), `"CONTRADICTED"`
  (`-0.12`, line 48), `"DECEPTIVE_DETECTED"` (`-0.25`, line 49-50). Returns a new
  `SourceTrustEntry` (clamped `[0.0, 1.0]`, `interactions+1`).
  **`DECEPTIVE_DETECTED` has zero production or test callers anywhere.** Confirmed by
  `grep -rn "DECEPTIVE_DETECTED" src/ tests/` — the string appears exactly once, in the branch
  definition itself (`trust.py:49`). `grep -rln "SourceTrustUpdateService"` likewise returns only
  `trust.py` itself plus two test files (`tests/unit/domains/information/
  test_phase5_source_trust_update.py`, `tests/integration/scenarios/
  test_phase5_information_belief_scenarios.py`) — `SourceTrustUpdateService.update()` has **zero
  production callers** at all (`CONFIRMED`/`CONTRADICTED` included), not just the
  `DECEPTIVE_DETECTED` branch. `InformationAssimilationService.assimilate()`
  (`src/domains/information/assimilation.py:100`) explicitly sets `source_trust_update=None` with
  the comment "Will be resolved by trust service" — the wiring point exists but nothing calls
  through it yet.
- `src/domains/information/contradiction.py:26-76` — `BeliefContradictionService.detect()`:
  matches an observation dict (`kind`, `subject`, `position`) against active
  (non-`EXHAUSTED`) leads on `entity.strategic.leads`, handling exactly two `obs_kind` values:
  `"claim_failed_search"` and `"region_danger_seen"`. No secrecy/confidence-tier signal is read
  or produced.
- `src/domains/information/router.py:22-106` — `InformationQueryRouter.route()`: matches source
  profiles to a query by `knowledge_scopes`, ranks by `expected_certainty = accuracy * trust_score`
  (line 87), returns top-3 candidates. No disclosure gate exists — every matched, affordable
  candidate is returned; there is no concept of a source declining to answer or partially
  withholding based on a secrecy tier.
- `src/domains/information/phase.py` (`InformationBeliefPhase.apply()`) — coordinates 4 branches
  per active actor per tick: (1) assimilate pending responses, (2) route new queries from
  `self_model.knowledge.unknowns` (Branch B), (3)/(4) — see "System-Live" finding below — a
  per-tick observation-synthesis loop over `actor.strategic.leads` that builds
  `claim_failed_search`/`region_danger_seen` observation dicts from live
  `actor.navigation.last_failure_reason`/`region_id` and `state.local_scars`, then routes them
  through `ObservationBeliefBridge.process_observation()` (lines 110-166).
- `src/domains/information/bridge.py:20-68` — `ObservationBeliefBridge.process_observation()`: for
  `claim_failed_search`/`region_danger_seen`, now calls the real `BeliefContradictionService.detect()`
  (line 40) and, on a hit, marks the lead `tested=True`/`test_outcome="FAILURE"` via a typed
  `StrategicUpdate`. (Prior to `TCK-20260824-LEAD-CONTRADICTION-WIRING` this branch hand-built a
  fake `CONTRADICTION` result and never called the real service — confirmed by reading the current
  file; the ticket description's characterization matches what is now in the file.)
- `src/core/strategic.py:341-346` — `SourceTrustEntry` (`entity_id`, `trust: float = 0.5`,
  `interactions: int = 0`, `last_outcome: Optional[str]`). Lives on
  `StrategicComponent.source_trust: Dict[int, SourceTrustEntry]` (`src/core/strategic.py:393`).
- `src/domains/optimization/feature_flags.py:37` — `"ENABLE_BELIEF_ASSIMILATION":
  FeatureMode.ON`. Confirmed by direct read. `docs/guidelines/intentional_divergences.md`'s
  DEV-003 entry (~line 1445) documents this decision (`TCK-20260824-ROLLOUT-FLAG-DECISIONS`,
  rationale class **Stabilized**, status **ACTIVE**), citing real, already-ON usage in
  `config/simulation_quality/profiles/sandbox_world.yaml` and `urban_political.yaml` as the
  evidence basis (not a fresh `tools/balance_measure.py` run — stated explicitly in DEV-003 itself
  as a deliberate, non-glossed-over deviation from DEV-002's literal unblock condition).
- `src/engine/pipeline.py:173` — `InformationBeliefPhase.apply()` is still invoked via
  `run_phase("information_belief", update, ..., "ENABLE_BELIEF_ASSIMILATION")` — i.e. it remains
  gated behind the same flag this ticket's blocker names. It is **not** an always-on bypass.

### Sibling ticket interaction: `TCK-20260824-LEAD-CONTRADICTION-WIRING` (commit `704c14a6`)

This ticket already landed on this branch and does two structurally separate things, confirmed by
reading the actual current files (not just the prior ticket's own notes):

1. Adds a new, **always-on, no-feature-flag** `run_phase("lead_contradiction", ...)` call in
   `AuthoritativeApplyPipeline.refine()` at `src/engine/pipeline.py:356`, calling
   `LeadContradictionSystem.enforce()` (`src/engine/pipeline_phases/lead_contradiction.py`). This
   is a pure state-scan contradiction checker for `resource`/`location`/`person`/`object`/`event`
   lead kinds, checked directly against world state (`_is_lead_contradicted()`,
   `lead_contradiction.py:43`). Its own docstring (lines 60-64) explicitly excludes `"concept"`/
   `"information"` lead kinds: *"CONCEPT contradiction is observation-shaped ... routed through
   BeliefContradictionService.detect() instead."* Confirmed: this phase never imports or calls
   `BeliefContradictionService`.
2. `ObservationBeliefBridge.process_observation()` was fixed to call the real
   `BeliefContradictionService.detect()` (see bridge.py above), and `InformationBeliefPhase.apply()`
   gained the new per-tick observation-synthesis branch (phase.py lines 110-166, described above).
3. **`InformationBeliefPhase.apply()` — which contains this new wiring — remains gated behind
   `ENABLE_BELIEF_ASSIMILATION`** at `pipeline.py:173`, confirmed by direct read. It is not an
   always-on bypass of the flag.

**Conclusion (agrees with the orchestrator's pre-verified assessment): `TCK-20260824-LEAD-
CONTRADICTION-WIRING` did NOT take idea 12's flag-free alternative path.** It built a structurally
separate, orthogonal always-on system (state-scan-based, for 5 non-concept lead kinds) while
leaving `BeliefContradictionService`/`InformationBeliefPhase` exactly where they were:
flag-gated. This ticket's sequencing premise (gate on `ENABLE_BELIEF_ASSIMILATION`, blocked on
`TCK-20260824-ROLLOUT-FLAG-DECISIONS`) still holds and does not need re-evaluation.

### "System live" resolution (the ticket's own open question)

The ticket's Assumptions/Open Questions section asks: *"What 'system live' precisely means (flag
ON alone vs. a generalized non-compile-time-seed writer for Branch A) needs precise definition
before real work starts."*

Resolution, with evidence: **"system live" is now true in a stronger sense than flag-ON-alone, and
stronger than just Branch A's per-world compile-time seed** — for two independent reasons:

1. **A new, non-compile-time-seed production writer exists for the contradiction-detection slice.**
   `InformationBeliefPhase.apply()`'s new branch (phase.py:110-166) derives `claim_failed_search`/
   `region_danger_seen` observations from **live per-tick entity state**
   (`actor.navigation.last_failure_reason`, `actor.navigation.region_id`, `state.local_scars`
   proximity to the actor's current region bounds) — not from any precomputed/seeded data. This
   runs for every actor with an untested, non-`EXHAUSTED` lead, in every world, every tick the
   `information_belief` phase runs (i.e. whenever `ENABLE_BELIEF_ASSIMILATION` is ON, which per
   DEV-003 it now is by default). This is a real, general writer, not per-world compile-time
   seeding.
2. **Branch B's input (`self_model.knowledge.unknowns`) is fed by the always-on
   `lead_contradiction` phase, independent of the flag.** `LeadContradictionSystem.enforce()`
   (`lead_contradiction.py:194-207`) regenerates a real `UnknownFact` into
   `entity.self_model.knowledge.unknowns` via a typed `KnowledgeModelComponent` replace whenever a
   lead is state-scan-contradicted — this phase is unconditional (`pipeline.py:356`, no feature
   flag argument), confirmed by grep showing `lead_contradiction.py` among the non-test writers of
   `UnknownFact(`. `InformationBeliefPhase.apply()`'s Branch B (phase.py:86-107) reads exactly this
   field to route a new query. So even d19's characterization of Branch B as "still dead" (see
   below) is now stale for the *feeding* side — Branch B has a real, always-on upstream writer; it
   is `InformationBeliefPhase` itself (the *consumer* of that write) that remains flag-gated.

Net effect: with `ENABLE_BELIEF_ASSIMILATION` defaulted `ON` (DEV-003) and both the contradiction
consumer (`phase.py` branch 4) and the Branch-B unknowns producer (`lead_contradiction.py`, always
on) now real and non-compile-time-seed-dependent, this ticket's blocking dependency
(`TCK-20260824-ROLLOUT-FLAG-DECISIONS`) is **satisfied**, and the previously-noted "trap" (flag ON
alone activates a phase with nothing to process) no longer applies to the contradiction-detection
slice of the system. **Caveat, scoped precisely:** this resolution covers the
contradiction-detection path (`contradiction.py`, `bridge.py`, the phase.py branch-4 loop, and
Branch B's routing trigger). It does **not** establish that the full query/candidate-routing/
trust-scoring machinery this ticket's own scope also touches (`router.py`'s candidate ranking,
`trust.py`'s `SourceTrustUpdateService`, `assimilation.py`'s fact/lead merge) has any comparably
general non-compile-time-seed *input* path beyond Branch B's single-query-at-a-time routing
(`phase.py:87-107`, which only ever selects "first unknown" per actor per tick) and Branch A's
per-world compile-time-seeded `pending_information_responses` (still `urban_political`-only per
`docs/audits/D19_domain_phase_inventory.md` §3, PP-04 row — not re-verified as changed by this
investigation since no code under `src/worldbuilding/`/`src/worldassembly/` was touched by
`LEAD-CONTRADICTION-WIRING`). A design that assumes the full router/trust-update cycle already has
rich, general live traffic would be overreaching; a design scoped to "the system now has real,
general per-tick output to design against, but query volume may still be structurally thin outside
`urban_political`" is the accurate framing for a future implementation ticket.

### SocialBond.sentiment vs. SourceTrustEntry/source_trust — structurally separate (AC4)

Confirmed by direct read, per this ticket's own AC:

- `SocialBond.sentiment` (`src/core/models/social.py:14-20`): `float`, `-1.0` to `1.0`,
  "Bias/Liking". Lives in `SocialComponent.bonds: Dict[int, SocialBond]`
  (`src/core/models/social.py:32-43`), part of the **Social** domain (relationship/affection
  ledger). `TCK-20260824-AFFECTION-CONTRACT-GATE` (still `OPEN`, `tickets/todos/m1-quick-wins/`)
  proposes reusing this exact field as the basis for a Team-Up/Trade/Paid-Information affection
  gate, explicitly excluding "idea 25's separate trust ledger (PP-04-adjacent)" from its own scope
  — independent confirmation from a sibling ticket that the two ledgers are already understood as
  separate concerns in this codebase's own planning.
- `SourceTrustEntry`/`StrategicComponent.source_trust` (`src/core/strategic.py:341-346,393`):
  `float trust` (`0.0`-`1.0`), "Trust score for a specific information source". Lives in
  `StrategicComponent.source_trust: Dict[int, SourceTrustEntry]`, part of the **Strategic
  Cognition** domain (information-source reliability tracking).

**Different component** (`SocialComponent` vs `StrategicComponent`), **different dataclass**,
**different semantics** (relationship bias/familiarity vs. information-source reliability),
**no shared implementation** — confirmed no cross-reference between the two files, no shared
update path, no shared scoring formula. `TCK-20260824-RELATIONSHIP-ROLE-FIELD` (done) added a
third, also-separate concept (`RelationshipRole` enum on `SocialBond`) without touching
`source_trust` at all, reinforcing the separation.

## Mechanics / Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` §3 ("Strategic Memory: Leads & Blockers") and its
  "Lead Contradiction Testing" subsection (§3, ~line 95, `E42D`/`TCK-20260824-LEAD-CONTRADICTION-
  WIRING`) are the authoritative description of lead certainty/contradiction mechanics that any
  secrecy/confidence-tier design must remain consistent with — in particular the existing
  `LeadCertainty` enum (`PRECISE`/`APPROXIMATE`/`VAGUE`/`EXHAUSTED`,
  `src/core/strategic.py:34-39`) is the only certainty-tier concept that exists today; a new
  "confidence-tier" concept must be designed to compose with, not duplicate or conflict with,
  `LeadCertainty`.
- No Mechanics Bible chapter currently documents `SourceTrustUpdateService`'s delta table
  (`CONFIRMED +0.08` / `PARTIALLY_CONFIRMED +0.03` / `CONTRADICTED -0.12` / `DECEPTIVE_DETECTED
  -0.25`) or the `InformationQueryRouter`/`InformationAssimilationService` formulas at all — this
  is a real doc gap that predates this ticket (STRAT-073's parity-ledger entry is
  `legacy_verified`/checklist-only, with no `v2_evidence` citing current source, and no mechanics
  chapter section exists for it). Not something this scope-only ticket must fix (see "Docs
  Requiring Update" below), but any future implementation ticket for the actual secrecy/disclosure
  feature will need to document both the pre-existing trust-delta table and the new
  secrecy/confidence-tier mechanics together in one pass.
- Per CLAUDE.md's Durable State Rule: any new secrecy/confidence-tier metadata must be a typed
  field on a frozen dataclass (mirroring `InformationSourceProfile`/`SourceTrustEntry`'s existing
  pattern), applied only through the authoritative update path (`StrategicUpdate`/`EntityUpdate`),
  never a `reason` string or free-form dict key — the existing `NormalizedInformationResponse.reason:
  Optional[str]` field must not become a dumping ground for secrecy state.

## Docs Requiring Update

None. This ticket's own deliverable (per its Scope/AC) is a design/scope artifact —
schema-extension design for secrecy/confidence-tier metadata and selective-disclosure logic — not
shipped `src/` behavior. No `src/` file is created or modified by this ticket, and no doc
describes behavior that this ticket changes, because no behavior changes. The ticket's four AC
items (limit scope to design artifacts; name the blocking dependency in Related Tickets +
SEQUENCE.md; state the DECEPTIVE_DETECTED delta-reuse decision; document the
SocialBond/SourceTrustEntry separation) are all satisfied by the ticket body and this
investigation/test_plan pair themselves — none of them require editing a docs/ file to be true.

Candidates considered and rejected (not written as bulleted docs/ paths, to avoid this section's
required "None." machine-parsed format being misread as flagging them required): a future
mechanics-chapter section in the strategic-cognition chapter would be the natural home for a
secrecy/confidence-tier mechanic once real logic ships, but this ticket ships no logic, so there
is no new mechanic to document yet; a new parity-ledger entry in the strategic-cognition shard is
warranted only once source code implements the behavior it would describe, since P0/P1 entries
require a passing test_path that cannot exist for undesigned code — premature entry creation would
create an unfollowable/unfalsifiable ledger row; and this ticket's own Related Docs audit entry
(D19, domain phase inventory, PP-04's row) was read for context but is a point-in-time snapshot,
not a living contract this ticket is expected to keep current — updating it is out of scope.

## Parity Ledger Overlap

`docs/parity_ledger/strategic_cognition.yaml` entries touched by the *area* (none require edits
from this ticket itself, since no behavior ships):

- `STRAT-073` — `status: legacy_verified`, `priority: P0`. Text: `test_source_trust_behavioral_impact`
  (source trust changes future weighting). `v2_evidence` is checklist-only ("Implementation proven
  via exhaustive checklist audit Phase 1-11"), `test_path: null`. **Flag for a future
  implementation ticket**: if/when `SourceTrustUpdateService` gets a real production caller (this
  concern's likely deliverable), this `P0` entry's `legacy_verified` status and missing
  `test_path` should be revisited — `P0` entries require a passing `test_path` per CLAUDE.md, and
  this one currently has none.
- `STRAT-230` — `status: verified`, `priority: P1`. The `lead_contradiction` phase contract,
  already citing both `TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS` and `TCK-20260824-LEAD-CONTRADICTION-
  WIRING` in its `text`/`v2_evidence`. Current and accurate; no edit needed by this ticket.
  Relevant as evidence for the "system live" resolution above.
- `STRAT-204` — `status: verified`, `priority: P0`. Text: "Leads have source trust." Already
  covers the existing `LeadState.source_entity_id`/trust-adjacency concept generally; a future
  secrecy/confidence-tier design should check this entry doesn't already claim coverage the new
  design would need to extend precisely (not duplicate).
- No `P0` entry anywhere in `strategic_cognition.yaml` currently covers `DECEPTIVE_DETECTED`
  specifically or any secrecy/disclosure concept — confirmed by grep; none exists to flag as
  needing a `test_path`.

## Prior Work

- `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` / `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` —
  original Phase 5 build-out; established the flag-gated-but-input-starved state that D19 §3
  documents and that DEV-003 + `LEAD-CONTRADICTION-WIRING` have since substantially closed.
- `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` — Branch B (`self_model.knowledge.unknowns` routing)
  original build.
- `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE` — router/candidate closure work.
- `TCK-20260817-HOTFIX-BELIEF-ASSIMILATED-TESTS-BYPASS-SHADOW-SHAPERS` — hotfix in the same
  subsystem; no design-relevant carryover for secrecy/disclosure found in its scope (test-bypass
  fix, not a mechanics change).
- `TCK-20260824-ROLLOUT-FLAG-DECISIONS` (C1) — flips `ENABLE_BELIEF_ASSIMILATION` to `ON`
  (DEV-003). **This ticket's named blocking dependency; already landed, decision confirmed ACTIVE.**
- `TCK-20260824-LEAD-CONTRADICTION-WIRING` — see "Sibling ticket interaction" above. Already
  landed (`tickets/done/`, `stored_artifacts/TCK-20260824-LEAD-CONTRADICTION-WIRING/`). Directly
  changes the "system live" premise this ticket depends on, in this ticket's favor (does not
  invalidate scope, and resolves the open question about generalized non-compile-time-seed
  writers, as documented above).
- `TCK-20260824-RELATIONSHIP-ROLE-FIELD` — done; confirms `SocialBond` extension pattern
  (additive enum field, authoritative-update-only setter, one real consumer, doc+parity in the
  same session) as the template this ticket's own eventual design should follow if it extends
  `SourceTrustEntry`/`InformationSourceProfile` similarly.
- `TCK-20260824-AFFECTION-CONTRACT-GATE` — still `OPEN` (`tickets/todos/m1-quick-wins/`), not yet
  implemented. Its own Out of Scope explicitly excludes "idea 25's separate trust ledger
  (PP-04-adjacent)" — i.e. it already treats `SourceTrustEntry` as a separate concern from
  `SocialBond.sentiment`/affection, corroborating this ticket's AC4 finding independently.
- No `stored_artifacts/` investigation specifically addresses secrecy tiers or selective
  disclosure — confirmed by grep across `stored_artifacts/*/investigation.md` and
  `docs/REGISTRY.yaml` for "secrecy"/"disclosure"/"confidence-tier"; none exists. This is genuinely
  new design territory, not a rediscovery of prior work.

## Risks and Open Questions

- **Resolved by this investigation** (was previously open in the ticket): "what does 'system live'
  mean" — see the dedicated section above. Answer: real per-tick non-compile-time-seed output now
  exists for the contradiction-detection slice; the full router/trust-update cycle's live query
  volume outside `urban_political` remains comparatively thin and should be verified with a live
  run before an implementation ticket assumes rich traffic.
- **Still open, requires a human/product decision, not resolvable by more investigation**: whether
  a future `DECEPTIVE_DETECTED` wiring reuses the existing `-0.25` delta as-is or needs a new,
  differently-calibrated writer. This ticket's own AC only requires *stating* which — this
  investigation's finding is that the delta itself is unvalidated (zero callers, zero balance
  measurement ever run against it), so "reuse as-is" carries the specific risk of shipping an
  arbitrary, never-empirically-checked number into new deceptive-source gameplay. A future
  implementation ticket should treat `-0.25` as a placeholder needing balance validation, not a
  proven constant, regardless of which option is chosen.
- **Schema-collision risk**: a naive "confidence tier" field could collide semantically with the
  existing `LeadCertainty` enum (`PRECISE`/`APPROXIMATE`/`VAGUE`/`EXHAUSTED`) or
  `NormalizedInformationResponse.certainty: float`. Any future design must explicitly state how
  the new field composes with (not duplicates) these two existing certainty concepts.
- **Router live-traffic assumption risk** (flagged above): a future implementation ticket's design
  should not assume the full `InformationQueryRouter`/`SourceTrustUpdateService` cycle has broad
  live traffic just because `ENABLE_BELIEF_ASSIMILATION` is ON — Branch A's query/response cycle
  is still `urban_political`-compile-time-seeded per D19, and Branch B only ever routes one
  "first unknown" per actor per tick (phase.py:92).

## Anti-Drift Hazards

- This ticket must not implement any `src/` change — its own Scope and Out of Scope are explicit
  that only design/scope artifacts land until `TCK-20260824-ROLLOUT-FLAG-DECISIONS`' flag decision
  is confirmed live (now true) *and* SEQUENCE.md places it strictly after. Producing working code
  here would violate the ticket's own AC1 and Out of Scope ("Any implementation before C1's flag
  decision lands and actually activates the system generally") — do not read the "system live"
  finding above as license to start implementing in this ticket; that finding only resolves the
  sequencing premise for a *future* ticket.
- Do not conflate `SocialBond.sentiment`/affection (Social domain) with
  `SourceTrustEntry`/`source_trust` (Strategic Cognition domain) in any future design — AC4 exists
  specifically because this codebase has a track record (per `TCK-20260824-RELATIONSHIP-ROLE-
  FIELD`'s own Request Summary) of adding near-duplicate ledgers. `TCK-20260824-AFFECTION-CONTRACT-
  GATE` already claims `SocialBond.sentiment` for its own affection-gate concern — a future
  secrecy/disclosure design must not reach into that ledger.
- Do not treat `LeadContradictionSystem`'s always-on state-scan phase (`lead_contradiction.py`) as
  a place to add secrecy/disclosure logic — its own docstring is explicit that `concept`/
  `information` lead kinds are deliberately excluded and routed through
  `BeliefContradictionService` instead. Mixing the two systems would re-create the exact ambiguity
  `LEAD-CONTRADICTION-WIRING` was built to resolve.
- `DECEPTIVE_DETECTED`'s existing `-0.25` delta must not be silently treated as "already proven" —
  it has zero callers and zero balance validation history (see Risks above).
