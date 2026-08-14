---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-COVERAGE-DECISION-GATE
phase: done
date: 2026-07-13
tags: [simulation-quality, corpus, calibration]
---

# TCK-20260713-SIMQ-COVERAGE-DECISION-GATE

## Title
SimQ roadmap Phase 5 — Coverage Decision Gate: rule on staged-vs-full-corpus depth using real Phase 2-4 cost data

## Status
DONE

## Tier
hotfix

## Type
documentation

## Priority
P2

## Request Summary
`docs/plans/simq_development_roadmap.md`'s Phase 5 is explicitly a decision checkpoint, not a work
item — deferred by design until Phases 2-4 landed, per the roadmap's own text: "given the *actual*
observed cost-per-world-per-pillar from the three waves, is continuing toward full 17-world coverage
worth it, or does the corpus's current staged depth constitute the final 'near-perfect' bar for this
feature? Either answer should be recorded the same way the AGENCY-DA ruling was — a documented
decision, not a silent stop or a silent continuation."

Phases 2-4 are now all done (Phase 4 closed today via `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`).
This ticket makes and records that decision, mirroring `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s
pattern: a hotfix-tier, doc-only ticket with no staging artifacts, no code changes.

## Scope
1. Synthesize the real, observed cost/outcome data from all three depth waves (below) into a ruling.
2. Record the ruling in `docs/plans/simq_development_roadmap.md`'s Phase 5 section, replacing the
   "not decided now" language with the actual decision and evidence.
3. Cross-reference the ruling from `docs/plans/idea_simq_near_perfect_roadmap.md` Thread 3 (the
   source thread this roadmap was spawned to resolve) — close that thread's "Progress" note with
   the final outcome.
4. Add a closing note to `docs/simulation_quality/corpus_tier_taxonomy.md` recording the
   ruling for future investigators scanning per-pillar coverage tables (mirrors the existing
   FACTION/INFORMATION coverage-closure notes already in that file).
5. Close out the `tickets/todos/simq-roadmap-phase5-coverage-gate/` folder per the standard
   folder-completion rule (move to `tickets/done/` once this ticket is the only thing in it and
   is itself done).

## Out of Scope
- Any code, content, engine, or test change — this ticket is a documented ruling only, per the
  AGENCY-DA precedent and the roadmap's own Phase 5 framing ("a short decision doc, not a full
  re-plan").
- ECONOMY's separate C-ceiling problem (`gold_sink_fired` requiring Gini > 0.7, an
  archetype-composition question, not a `FeatureMode` gating question like the other four pillars).
  `idea_simq_near_perfect_roadmap.md` Thread 3 explicitly excluded ECONOMY from this roadmap's
  Phases 2-4 scope for exactly this reason — this gate rules on the four pillars the roadmap
  actually addressed (COGNITION, FACTION, INFORMATION, SOCIAL), not a 5th pillar the roadmap never
  took on.
- Reopening or re-scoping any of the 5 closed Phase 2-4 tickets (`TCK-20260710-SIMQ-DEPTH-SOCIAL`,
  `-DEPTH-FACTION`, `-DEPTH-INFORMATION`, `-COGNITION-REALWORLD-GENERALIZE`,
  `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`) or their 2 filed side-effect tickets
  (`TCK-20260712-SIMQ-DUNGEON-URBAN-ANCHOR-DRIFT`, `-COOPERATION-SOCIAL-STALE-TESTS`, both still
  open in `tickets/todos/` — this gate does not touch them).
- Scoping the possible future "wire `ActionIntentAdapter.execute()` into the production tick
  pipeline" initiative this ruling identifies as COGNITION's real blocker — noted as a future
  candidate only, not scoped or ticketed here.

## Acceptance Criteria
- [ ] `docs/plans/simq_development_roadmap.md` Phase 5 section states an explicit, evidence-backed
      decision (not "not decided now")
- [ ] The decision is per-pillar (COGNITION, FACTION, INFORMATION, SOCIAL), not a single blanket
      verdict — the four pillars' actual costs diverged too much for one answer to honestly cover all
- [ ] `idea_simq_near_perfect_roadmap.md` Thread 3 is marked resolved with a final outcome note
- [ ] `corpus_tier_taxonomy.md` has a closing cross-reference note
- [ ] No `src/`, `tests/`, `content/`, or `data/` files touched
- [ ] Folder `tickets/todos/simq-roadmap-phase5-coverage-gate/` moved to `tickets/done/` on close

## Related Tickets
- `TCK-20260710-SIMQ-DEPTH-SOCIAL` (done — Phase 2, evidence source)
- `TCK-20260710-SIMQ-DEPTH-FACTION`, `TCK-20260710-SIMQ-DEPTH-INFORMATION` (done — Phase 3, evidence source)
- `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`, `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE` (done — Phase 4, evidence source)
- `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` (done — the precedent this ticket's format mirrors)

## Related Docs
- `docs/plans/simq_development_roadmap.md` (Phase 5 section — primary edit target)
- `docs/plans/idea_simq_near_perfect_roadmap.md` (Thread 3 — the source question)
- `docs/simulation_quality/corpus_tier_taxonomy.md` (coverage tables — closing cross-reference)
- `docs/simulation_quality/eval_matrix_results.md` (evidence tables cited by the ruling)

## Related Stored Artifacts
None — hotfix tier, doc-only.

## Related Code Areas
None — no code touched.

## Assumptions / Open Questions
None — all evidence needed for this ruling already exists in closed tickets' Completion Summaries
and the docs listed above; this ticket synthesizes, it does not investigate new ground.

## Implementation Notes

**Real cost/outcome data gathered from the three depth waves, per pillar:**

- **SOCIAL (Phase 2):** Cheap. Pure `ENABLE_SOCIAL_COOPERATION` flag activation in calibration
  profile YAML, zero engine/compiler/content changes. Moved 1→3 of 17 corpus worlds SOCIAL C→S
  (`frontier_living_world`, `highland_traverse`) across all 3 anchor seeds. One candidate
  (`dungeon_crawl`) investigated and rejected: structurally incapable (no settlement/civilian
  module, so `HelpNeedEvaluator`'s hard gate never opens — confirmed via live probe, 0
  `cooperation_event`s). 2 of 3 evaluated candidates succeeded — not an "insufficient candidates"
  situation, so no further candidate promotion was needed this wave.
- **FACTION (Phase 3 half):** Already saturated before this roadmap started. Live re-verification
  against current `data/worlds/*/world.yaml` found 11/17 worlds already carry
  `faction_tension_overrides` content (via prior, already-closed Corpus Tiers work); the remaining
  6/17 are FACTION-inert by deliberate tier-purity design (Stress/Unit/Regression worlds
  purpose-built to isolate other mechanics), not by omission. Zero content authored, zero code
  changed — closed as already-satisfied.
- **INFORMATION (Phase 3 half):** Same shape as FACTION. 9/17 worlds already carry
  `information_source_profiles`/`pending_information_responses` content; remaining 8/17 each have a
  documented, pre-existing, tier-appropriate reason to stay inert (2 structurally incapable, 2
  Stress tier-purity, 1 Regression/baseline fixture, 3 Unit single-mechanic isolation). Zero content
  authored, zero code changed.
- **COGNITION / self-model (Phase 4):** The expensive, asymmetric outlier. Materialization
  generalizes cleanly and cheaply — `urban_political` (a real archetype world, not the isolated
  `unit_selfmodel_pilot` pilot) moved COGNITION B→S via the existing capacity-bounded assimilation
  path, no code changes needed. Query-routing does **not** generalize for free: it reproducibly
  dead-ended against `urban_political`'s real compiled state (seed-invariant `intent=None` across
  seeds 42/123/456), root-caused to 4 file:line points across `router.py`/`phase.py`/`resolver.py`/
  `event_extractor.py`, requiring a full **standard-tier engine-fix ticket**
  (`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`) to close — not a documentation-only closure like
  FACTION/INFORMATION. That fix itself surfaced a 5th bug during this session's Architecture-Verify
  pass (a dropped `strategic_update` field in `action_intent.py`'s `ASK_INFORMATION` execution path).
  Even after all of that real engineering cost, query-routing has **zero live-gameplay reach today**:
  no shipped world profile enables `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_BELIEF_ASSIMILATION`
  together, and `ActionIntentAdapter.execute()` (the only call site that would turn a routed
  `ActionIntent` into an actual knowledge update) has no production tick-pipeline call site at all —
  confirmed reachable only via direct test-harness invocation.
- **ECONOMY:** Never in this roadmap's scope (see Out of Scope) — a Gini-threshold/archetype-
  composition problem, not a `FeatureMode` gating problem like the other four pillars, per
  `idea_simq_near_perfect_roadmap.md` Thread 3's own scoping note.

**The ruling (per-pillar, since the four pillars' costs diverged too much for one blanket answer):**

1. **FACTION and INFORMATION: near-perfect bar already reached.** Both pillars are structurally
   saturated at 11/17 and 9/17 respectively — every remaining world has a documented,
   tier-appropriate reason to stay inert. There is no further legitimate content-authoring work
   available; "full 17-world coverage" was never actually a reachable target for these two pillars,
   because a genuine subset of the corpus (Stress/Unit/Regression-tier worlds) is *supposed* to stay
   pillar-inert by design. Declared complete, no further action.
2. **SOCIAL: staged depth is the right permanent bar.** The one clean wave (Phase 2) captured both
   worlds with a qualifying settlement/civilian module among the candidates actually evaluated. There
   is no evidence of a backlog of easy remaining candidates being deliberately left on the table —
   further expansion should happen opportunistically (if/when a new world is authored with a
   qualifying module), not as a dedicated future roadmap wave.
3. **COGNITION self-model query-routing: do not pursue further world-coverage under this roadmap.**
   This is the pillar Phase 5 exists to make a real call on. Its cost already exceeded the roadmap's
   own "L-XL" estimate (a full engine-fix ticket, not a doc-only closure) to reach *zero* live-gameplay
   worlds — the routing mechanism is verified correct in isolation but structurally unreachable in any
   shipped profile today. Extending it to more worlds would require, at minimum, a new and
   currently-unscoped initiative (wiring `ActionIntentAdapter.execute()` into the production tick
   pipeline) before a second world's coverage would mean anything beyond what the first one already
   proved. That is new engineering scope, not incremental corpus depth, and should be decided on its
   own merits as a distinct future initiative if gameplay ever actually needs live self-model
   query-routing — not folded into "add more worlds."
4. **Overall:** the roadmap author's own pre-registered prediction ("staged depth is the right
   permanent bar, full-corpus coverage isn't worth its cost") is confirmed by real three-wave
   evidence, not the guess it was filed as. `docs/plans/simq_development_roadmap.md` is now complete
   — all 6 phases resolved. SimQ's three MVP goals (visibility, regression detection, tuning support)
   are judged adequately served by the corpus's current staged depth; no further pillar-depth
   expansion work is queued.

## Test Summary
Doc-only ticket — no test suite applicable. Confirmed via `git diff --stat` that only files under
`docs/` were touched (no `src/`, `tests/`, `content/`, `data/`, or `tickets/` frontmatter-governed
files requiring pytest coverage).

## Files Changed
- `docs/plans/simq_development_roadmap.md`
- `docs/plans/idea_simq_near_perfect_roadmap.md`
- `docs/simulation_quality/corpus_tier_taxonomy.md`

## Completion Summary
Ruled on the SimQ roadmap's Phase 5 Coverage Decision Gate using real cost/outcome data from all
three depth waves (Phases 2-4). Per-pillar ruling: FACTION and INFORMATION declared complete
(structurally saturated at 11/17 and 9/17, every remaining world documented as tier-appropriately
inert by design); SOCIAL's staged depth (1→3/17) declared the permanent bar, future expansion only
opportunistic; COGNITION self-model query-routing world-coverage explicitly not pursued further —
its real cost (a full standard-tier engine-fix ticket to reach zero live-gameplay worlds) and real
blocker (no production pipeline call site for `ActionIntentAdapter.execute()`) make further
world-coverage a new, unscoped pipeline-wiring initiative, not incremental depth. ECONOMY confirmed
correctly out of scope (Gini-threshold/archetype-composition problem, not `FeatureMode` gating).
The roadmap author's own pre-registered prediction ("staged depth is the right permanent bar") is
confirmed by evidence, not guessed. `docs/plans/simq_development_roadmap.md` is now complete — all
6 phases (0-5) resolved; no further SimQ pillar-depth expansion work is queued.

Recorded the ruling in 3 docs: `simq_development_roadmap.md` (Phase 5 section, primary record),
`idea_simq_near_perfect_roadmap.md` (Thread 3 — the source question — marked RESOLVED), and
`corpus_tier_taxonomy.md` (closing cross-reference note, matching the existing FACTION/INFORMATION
coverage-closure note format). Zero code, content, or test files touched — confirmed via `git
status`. Ran `tests/integration/test_world_profile_feature_flag_guardrail.py` (55 passed) to confirm
no drift. No parity ledger update needed (no behavior change, no `src/` files touched).
