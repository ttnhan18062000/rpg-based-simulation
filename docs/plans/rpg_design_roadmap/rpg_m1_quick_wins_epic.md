---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content, feature-flags]
---

# Epic Plan — RPG Design Roadmap, Milestone 1: Quick Wins & Housekeeping

**Status: DONE (2026-08-30).** 22/22 child tickets complete, folder archived to
`tickets/done/m1-quick-wins/` (`SEQUENCE.md` preserved). All work landed on branch `m1-quick-wins`,
PR'd as [#90](https://github.com/ttnhan18062000/rpg-based-simulation/pull/90) with all 13 CI checks
green as of 2026-08-31. See **Implementation Summary** below for what actually shipped, what was
decided, and what real follow-up work the batch's own changes surfaced. The rest of this document
(Problem/Scope/sections A-F onward) is preserved as the original planning record — read the
Implementation Summary first for the current, authoritative picture.

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M1-QUICK-WINS` (never created as a formal epic ticket — the
batch was tracked directly via the ticket folder instead, per the note above)
**Source:** `docs/brainstorm/rpg_feature_atlas.html` Rev 60+ (Design Ideas 1, 3, 7, 9, 10, 12, 13, 15-19, 20,
21, 22, 24, 25, 26, 29, 42), cross-checked against Cross-Cutting Risk, Shared Implementation Opportunities,
Phase Placement & Testing Strategy, and `docs/brainstorm/design_merit_scorecard.html`.
**Priority:** P1 — this is the milestone the roadmap itself has zero dependencies on; every other milestone
gates on something upstream of it.

**2026-08-29 review note**: this section was reconciled against
`docs/brainstorm/codex/2026-08-27-core-rpg-plan-brainstorm-update-request.md` for documentation accuracy
only (ticket count, lane grouping, idea 16/7/17 bookkeeping below). **No ticket content, scope, or sequence
was changed** — the 21 tickets already in flight under `tickets/todos/m1-quick-wins/` are being implemented
as originally scoped, and this review deliberately did not touch them. The confirmed final-permadeath
lifecycle defect is explicitly **not** part of this batch — see the parent roadmap's M5 section for its
owner.

## Implementation Summary (2026-08-31)

**Final count**: 22 tickets done (19 scoped ideas, idea 7 and idea 17 each split into two tickets by
responsibility, idea 16 needed none) — matches the epic's own Acceptance Signal exactly. Full landed
list (chronological): `ROLLOUT-FLAG-DECISIONS`, `ALLOCATE-AP-BRANCH-DECISION`,
`BREAKTHROUGH-BONUS-APPLICATION`, `CAUSAL-MEMORY-ROUTE-SCORING`, `DEFAULT-HEIR-ASSIGNMENT`,
`GRIEF-NEMESIS-REACHABILITY`, `LEAD-CONTRADICTION-WIRING`, `LIFE-STAGE-TRANSITIONS`,
`NEMESIS-MEMORY-UNIT-TESTS`, `OCCUPATION-CHANGE-TRIGGER`, `RELATIONSHIP-ROLE-FIELD`,
`ROUTE-KIND-COUNT-FIX`, `SECRETS-DISCLOSURE-SCOPE-SEQ`, `TOWN-CENTER-POINTER-FIX`,
`WIRE-ORPHANED-MECHANISMS`, `WOUND-PENALTY-FORMULA-WIRING`, `AFFECTION-CONTRACT-GATE`,
`PERSONAL-ECONOMY-SCOPE-BLOCK`, `WOUND-HEALING-DECISION`, `WOUND-THRESHOLD-DECISION`,
`TACTICAL-WOUND-SCAR-WIRING`, and `TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING` (all
`TCK-20260824-*` unless noted). One-paragraph summaries for each are in `tickets/working_log.csv`.

**Key governance decisions actually made:**
- **Idea 9 (flag governance)**: of the 8 flags reviewed, `ENABLE_BELIEF_ASSIMILATION` and
  `ENABLE_SOCIAL_COOPERATION` were flipped **ON** by default with real corpus evidence (DEV-003);
  1 (`ENABLE_ADVENTURE_ROUTING`) kept OFF with a formalized existing rationale (later confirmed
  structurally inert — zero live gating call sites — by follow-up work); 5 (`ENABLE_COMBAT_ENGAGEMENT`,
  `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_WORLD_EMERGENCE`, `ENABLE_PROGRESSION_EVOLUTION`,
  `ENABLE_INFORMATION_INTENT_EXECUTION`) kept OFF pending real trial evidence — all 5 were
  subsequently validated by dedicated follow-up tickets (below), each confirmed **keep OFF,
  deferred** with real corpus-trial evidence on file.
- **Idea 17 (wound/scar)**: severity-scaled penalty formula wired in for real
  (`WOUND-PENALTY-FORMULA-WIRING`), and wounds were decided to be **permanent until scarred** — no
  healing mechanism exists or was added (`WOUND-HEALING-DECISION`).
- **Idea 15 (wound threshold)**: confirmed the live 25% gate was correct; the dead 40% code path was
  deleted, not reconciled (`WOUND-THRESHOLD-DECISION`).
- **Idea 24/25 (personal economy, secrets disclosure)**: both correctly scope-blocked as planned
  (section F) rather than built on an acknowledged-broken foundation.

**Real bugs found and fixed along the way** (not part of the original 19-idea scope, discovered while
implementing it): `event_extractor.py`'s wound/scar event blocks were `isinstance(x, list)`-blind to
tuple-shaped state (`HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND`); an import-boundary pin drifted
across two files from the same root commit (`HOTFIX-REDIRECTION-CADENCE-IMPORT-BOUNDARY-VIOLATION`,
`HOTFIX-INTELLIGENCE-CADENCE-PIN-LINENO-DRIFT`); a pre-existing `TypeError` in heirloom transfer for
tuple-typed inventories (`LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR`); two static gate-checker
functions were pattern-presence-blind rather than content-aware, the same bug class in two different
files (`PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS`, `DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED`).

**Follow-up tickets the batch's own real behavior changes required** (all landed on the same
`m1-quick-wins` branch, 2026-08-26 through 2026-08-31, after the 22-ticket batch itself closed):
- **5 flag-validation tickets** (`COMBAT-ENGAGEMENT`, `SELF-MODEL-COGNITION`, `WORLD-EMERGENCE`,
  `PROGRESSION-EVOLUTION`, `INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION`) — each ran a real
  corpus-profile trial and confirmed **keep OFF, deferred** for its flag, per idea 9's own named
  follow-up requirement. The `PROGRESSION-EVOLUTION` trial found and disclosed a real pipeline crash
  (below); the `SELF-MODEL-COGNITION` trial found and disclosed a real grade-anchor drift (below).
- **`M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE`** — the batch's own real behavior changes (flags now ON,
  several dormant mechanisms now wired live) made 63/71 fast-tier SimQ corpus tests fail against
  never-updated anchors; re-baselined with fresh evidence, 0 confirmed real regressions among the 61
  investigated.
- **`SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`** — re-anchored the 2 `urban_political_selfmodel*`
  probe run keys the corpus rebaseline above deliberately excluded (a distinct root cause).
- **`URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE`** — re-baselined the one slow-tier (1000t)
  test the persistence-backpressure fix (below) unblocked.
- **`HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH`** — real crash fix: `ProgressionConversionPhase`
  stored a raw dataclass where `CanonicalStateHasher` needed JSON-serializable data.
- **`HOTFIX-WORLD-EMERGENCE-VESTIGIAL-GATE-CLEANUP`** — removed a dead, undocumented second feature
  gate that violated the project's Durable State Rule.
- **`HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES`** — the SimQ calibration tool's env-var
  override allowlist was silently dropping overrides for 6 of 17 live flags.
- **`SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION`** — root-caused and fixed a real persistence-
  phase I/O bottleneck (a redundant synchronous re-serialization, and unconditional per-record
  flushing) that was causing real calibration-integrity failures on long/heavy runs.
- **`COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`** / **`COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST`**
  — a cooperation-offer bug pair (no post-expiry retry cooldown, no pending-offer creation gate) found
  via SimQ grade-anchor investigation; both fixed with real corpus-trial evidence.
- **`KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD`** — `Kernel.shutdown()` stopped
  `QualityPersistence` before `EventRecorder`'s drain worker, risking silently-dropped in-flight
  writes; reordered, with a loud-warning backstop.
- **`HOTFIX-EVENT-RECORDER-BATCH-FLUSH-VISIBILITY-REGRESSION`** — the persistence-backpressure fix's
  own flush-batching change broke low-volume-writer visibility (a real regression, caught via CI);
  fixed by moving to a per-drain-cycle flush.
- **`HOTFIX-AGENTS-MD-37-TO-39-PHASE-COUNT-DRIFT`** / **`STALE-37-PHASE-REFERENCES-SWEEP`** — the
  authoritative pipeline's real phase count grew from 37 to 39 across this batch's work; synced
  `AGENTS.md` and its generator (CI-blocking) plus 9 other live docs/skills (non-blocking sweep).
- **`ENTITY-EVENT-LEDGER-COGNITION-BUNDLE-SET-MISSING`** — `EntityUpdate.cognition_bundle_set` had no
  event-ledger entry; documented as genuinely silent (no observed event exists), not fixed.
- **`HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT`** — a hardcoded parity-ledger test baseline
  drifted from this batch's own real `test_path` additions; updated with fresh evidence.

**Verification**: PR #90 ran CI for the first time ever on 2026-08-31 (previously zero runs across its
whole lifetime) after the `origin/main` merge triggered it; all 13 checks are green. The 2 real
regressions CI surfaced (the flush-visibility bug and the phase-count drift) were both found and fixed
the same day, alongside the sole remaining real (non-environment) gap
(`cognition_bundle_set`'s missing ledger entry).

## Problem

20 real, already-investigated gaps sit in the engine today with no design work left to do — half-finished
formulas, orphaned systems with a working consumer already waiting, two confirmed bugs, and five technical
questions that were genuinely unresolved until a follow-up trace answered them directly. None of this needs
new mechanism design; all of it needs someone to actually build the small thing the investigation already
specified. This epic exists to turn "well-understood gap" into "ticketed."

## Scope

**21 child tickets now exist** under `tickets/todos/m1-quick-wins/` for 19 of these 20 ideas (idea 16
required no behavior-change ticket — see item B below); ideas 7 and 17 were each split into two tickets by
responsibility. Grouped by shape below (see Acceptance Signal for the one real sequencing note), and by
these four execution lanes for review/scheduling purposes only (the committed build order remains
`SEQUENCE.md`, not this grouping):

- **Correctness repairs** — items 2-5 (wound threshold/penalty, route count) and 11-12 (heir assignment,
  town center) below.
- **Activation and governance** — item 1 (flag decisions) and items 6-10 (wiring the real orphans).
- **Player-visible RPG improvements** — items 13-17 (affection gate, life stages, occupations, relationship
  roles, wound/scar wiring).
- **Scope-only decisions** — items 18-19 (personal economy, secrets disclosure — both blocked, see section F).

### A — Governance decision (do this first within M1)

1. **Idea 9 — Decide the eight rollout flags on purpose.** Self-Model, World Emergence, Progression
   Conversion, Combat Engagement, Social Cooperation, Belief Assimilation, Information Intent Execution,
   and Guild Quest Generation are all real, correctly-built, and flag-gated OFF. This ticket is a per-flag
   keep/cut/flip decision, not new code — but M2 onward adds 38 more flagged ideas on top of this precedent,
   so deciding it first, not last, is the point.

### B — Now-resolved technical questions (each needs a real fix or an explicit keep-as-is decision, not just documentation)

2. ~~**Idea 15 — Wound threshold: 25% is the live value, 40% is dead code.**~~ **Resolved** by
   `TCK-20260824-WOUND-THRESHOLD-DECISION` (done): `WoundService.should_inflict_wound()` and
   `WOUND_THRESHOLD_RATIO` deleted as confirmed zero-real-caller dead code — the live 25% gate in
   `src/engine/combat.py` was never touched. `docs/mechanics/01_entity_anatomy.md`'s pseudocode
   identifier renamed `WOUND_THRESHOLD_RATIO` → `WOUND_INFLICTION_RATIO` (value unchanged, 0.25);
   `docs/mechanics/02_combat_laws.md` needed no change (already used the raw `0.25` literal, no
   identifier collision). No `intentional_divergences.md` entry — deleting dead code that never
   diverged from documented law is not itself a divergence.
3. **Idea 17 — Wound/Scar penalty mechanics.** The severity-scaled formula this card originally described
   is dead code; live combat uses a flat `penalty=5.0` for attack/defense only, and no wound has ever
   healed in production (`WoundUpdate.wounds_heal` has zero producers). Two real decisions bundled: wire
   the severity-scaled formula in for real (replacing the flat one), and decide whether healing should ever
   fire, or whether "wounds are permanent until a Scar forms" is the intended design.
4. **Idea 18 — Route/activity kind count.** `docs/mechanics/adventure_routing_contract.md`'s table is stale
   by exactly 3 entries (16 real values, not 13). Doc fix.
5. **Idea 19 — ALLOCATE_AP reachable but never invoked.** A real, unconditional branch exists with two live
   entry points; nothing has ever constructed a payload that reaches it. Decide: wire a real producer, or
   leave it as intentionally-dormant AI-proposal-path scaffolding and document why.

Idea 16 (Ranger doctrine) needs no ticket — already answered by a separate, already-published atlas card
(the "Class" finding); this item is closed by cross-reference.

### C — Wire the real orphans

6. **Idea 1 — Wire the remaining orphans.** Nine originally, now seven after two folded into items 13 and
   (M3's) Reproduction per Shared Implementation Opportunities — see the atlas card for the full checklist.
7. **Idea 3 — Finish `BreakthroughService.apply_bonuses()`.** A literal `pass`; three real breakthroughs
   with real attribute bonuses already sit in the registry, earned but never applied.
8. **Idea 7 — Extend Grief/Nemesis past episode boundaries.** `GriefUrgencyImporter`/`NemesisRelationImporter`
   are real and live, called only from `CampaignOrchestrator._build_initial_state()` — extend the same
   trigger to fire on an in-episode death, not just at Campaign start. **Depth-audit correction:** this idea
   fails on three axes at once, not just the trigger-point gap above — Campaign mode has zero scenario
   content wiring it in anywhere (may only ever run via manual CLI), no SimQ event type exists for it (this
   idea's own success can't be measured once built), and `check_nemesis_promotion()`/`tick_place_attachment()`
   (the functions doing the real work) have zero test coverage. Scope this ticket as "make it reachable,
   measurable, and tested, then extend it" — see Depth Beneath "Done" in the atlas and this idea's own card.
9. **Idea 12 — Wire contradiction detection into the live Leads system.** Skips the flag trap by hanging
   off `BeliefContradictionService` directly — but Phase Placement & Testing Strategy found a sibling
   orphan (`LeadContradictionSystem`) that must be wired in the same ticket, or 3 of 4 lead kinds stay
   permanently unable to resolve via world-state contradiction.
10. **Idea 26 — Expertise Earned Through Living.** `MemoryUpdatePhase` has zero call sites; its consumer
    (`AdventureRouteScorer.score()`) already reads 2 of 10 possible advice values from causal memory that
    never populates. Proposed insertion point (Phase Placement): between `PP-02` and `PP-03`.

### D — Confirmed bugs

11. **Idea 10 — Assign heirs from what already exists.** `heir_entity_id`'s transfer mechanic is fully
    wired and confirmed live; only assignment is missing. `RelationshipService`'s per-pair `SocialBond` data
    is sufficient to pick a default.
12. **Idea 42 — Fix the `town_center` pointer bug.** Deepened past the original finding: two more broken
    consumers found (`FlowFieldService`, a second parallel `town_center` field on the worker-protocol
    dataclass), plus a second, subtler bug in the two consumers that DO have a fallback — both pick one
    arbitrary tile across every town in the world, not the nearest one to the entity asking.

### E — New small mechanisms

13. **Idea 13 — Gate Team-Up/Trade/Paid-Information on affection.** Build this as the shared
    `appraise_contract()` threshold-gate helper Shared Implementation Opportunities identifies — a 6-idea,
    3-milestone cluster (this idea, Conversation, and later M6's ideas 39/40) all converge on the identical
    formula. Building the helper once here means M6 extends it later instead of re-deriving it.
14. **Idea 20 — Life Stages & Rites of Passage.** The consumer (`LifeStageService.get_goal_multipliers()`)
    already runs unflagged inside the Strategic Intelligence Core. What's missing: `identity.life_stage`
    has no writer anywhere — no `life_stage_set` field exists on `IdentityUpdate` today. New typed field +
    apply-path work required before any transition trigger can fire.
15. **Idea 21 — Careers, Apprenticeships & Changing Occupations.** `IdentityUpdate.role_set` already has a
    full live apply path with 12 confirmed consumers (routine, adventure scoring, crafting, combat/rewards,
    movement/spawn priority, legality, military conflict, cooperation, evolution) — the largest confirmed
    blast radius of any Milestone 1 idea. Only the transition trigger is missing.
16. **Idea 22 — Relationship Roles, Not Just Relationship Scores.** `SocialBond` has exactly three fields
    today; adding a role concept is additive. Real risk (Merit Scorecard): a label with no consumer is
    invisible — this codebase has a track record of adding fields nothing ever reads (see idea 8's cognition
    schema). Scope the consumer alongside the field, not as a follow-up.
17. **Idea 29 — Injury That Changes a Life, Not Just a Number.** The Tactical Decision System already
    reacts to raw HP ratio; it never reads structured `WoundState`/`ScarState` data. Wire the real data in.

### F — Scope-ready but with a real upstream blocker (list here for completeness, don't start until noted)

18. **Idea 24 — Personal Economy & Material Ambition.** Wants to attach to `MotivationModel.values`
    (`ValuePreferenceProfile`), which is independently confirmed dead-on-arrival — never populated above
    its 0.5 defaults. Building on top of a dead foundation inherits nothing. **Do not start this ticket
    until that foundation ticket exists and is scoped** (not part of this epic — flag as a dependency to
    resolve first, likely worth its own idea/ticket outside the current 65).
19. **Idea 25 — Secrets, Confidence & Selective Disclosure.** Extends the Information Sourcing/Trust system
    almost exactly, but that whole system is flag-gated OFF (`ENABLE_BELIEF_ASSIMILATION`-adjacent) with a
    documented "flipping the flag alone activates a phase with nothing to process" trap (idea 12's own
    finding). Scope this ticket, but sequence it after whatever ticket actually gets that system live.

## Out of Scope

- Any idea numbered 2, 4-6, 8, 11, 14, 23, 27, 28, 30-41, 43-65 — all belong to Milestones 2 through 6,
  tracked in their own sibling epics per `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`. (Idea 42 is in M1's own scope,
  section D above — deliberately excluded from this range, not an oversight.)
- Actually flipping any of the 8 flags idea 9 evaluates — that's the outcome of item 1's ticket, not a
  decision made in this planning doc.
- Fixing `MotivationModel.values`/`ValuePreferenceProfile`'s dead-on-arrival state (item 18's real
  blocker) — that's a prerequisite this epic surfaces, not a task it owns.

## Acceptance Signal for This Epic

- All 21 child tickets exist under `tickets/todos/m1-quick-wins/` (19 ideas, with ideas 7 and 17 each split
  into two tickets; idea 16 needs none), each referencing its source idea number in the atlas — **confirmed
  as of 2026-08-29**.
- Idea 9's flag-governance ticket lands before any other M1 ticket that adds new flag-gated behavior, per
  the sequencing note in section A and `SEQUENCE.md`.
- Items 24 and 25 (section F) are either explicitly deferred with their blocker ticket referenced, or their
  blocker is resolved first — not silently built on a foundation already known to be broken.
- `docs/brainstorm/rpg_feature_atlas.html`'s own Roadmap section estimate (roughly 18 tickets) was superseded
  by the real 21-ticket split once idea 7 and idea 17 were each broken into two tickets by responsibility —
  not a discrepancy, an expected refinement.

## Open Questions

- Does idea 24's motivation-framework blocker get its own ticket inside this epic, or does it belong to a
  different milestone/epic entirely? Not resolved here — flagged for whoever scopes item 18's child ticket.
- Should idea 13's shared threshold-gate helper be built to already anticipate M6's ideas 39/40 consumers,
  or built minimally for its own three consumers (Team-Up/Trade/Paid-Info) and extended later? Leaning
  toward anticipating it, since the shape is already fully specified in Shared Implementation Opportunities
  — but not decided here.

## References

- `docs/brainstorm/rpg_feature_atlas.html` — ideas 1, 3, 7, 9, 10, 12, 13, 15-22, 24-26, 29, 42; Cross-Cutting
  Risk & Blast Radius; Shared Implementation Opportunities; Phase Placement & Testing Strategy
- `docs/brainstorm/design_merit_scorecard.html` — per-idea scores
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, sequencing rules, temporal axis
- `tickets/todos/m1-quick-wins/SEQUENCE.md` — the real, executable ticket ordering
- `docs/brainstorm/codex/2026-08-27-core-rpg-plan-brainstorm-update-request.md` — documentation-sync review
  this section was reconciled against, 2026-08-29 (scope/tickets unchanged)
