---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE
artifact_type: investigation
tags: [cognition, self-model, simulation-quality, calibration, investigation]
---

# Investigation — TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE

## Summary verdict

Branch B **splits into two independently-testable halves, and they generalize differently**:

- **Materialization half** (Step 1 assimilation → `SelfModelPatch` durable write →
  `self_model.knowledge.unknowns` populated for a real entity in a real world) — **(a) clean
  generalization**. Confirmed with real compute: `urban_political`'s seeded entity (actor_id 23,
  `pop_1`) gets `unknowns={'material.moon_resin.source': UnknownFact(...)}` from tick 1 onward,
  identically across seeds 42/123/456, and a full 200-tick calibration run shows `COGNITION` moving
  from its baseline `B` to `S` (5610–5611 `self_model_updated` events/run) purely from this half.
- **Query-routing half** (`InformationBeliefPhase` Branch B: route the unknown to a source, resolve
  an `ASK_INFORMATION`/`MOVE_TO` intent, eventually close the loop with an answer) — **(c) does not
  generalize**. It is mechanically reachable (`InformationQueryRouter.route()` returns legitimate
  candidates) but dead-ends at three independent points, reproduced directly against the real
  compiled `urban_political` state, seed-invariant across 42/123/456. See "Real-World
  Generalization Test Results" below for the full evidence chain and exact file:line citations.

## Candidate World Resolution (Part A / UQ-1)

Re-verified independently against current `docs/simulation_quality/corpus_tier_taxonomy.md` and
`tests/simulation_quality/fixtures/grade_anchors.json` (not just accepted the ticket's own pre-filed
analysis):

- `corpus_tier_taxonomy.md`'s current tier table (as of the 2026-07-12 INFORMATION coverage closure
  update) classifies `hero_guild_routing` as **Unit tier** — "isolates AGENCY/route-selection only
  via `ENABLE_ADVENTURE_ROUTING`... real-archetype scale distinguishes it from calibration-minimal
  `simq_routing_test`" — i.e. real-archetype *scale* but Unit-tier *purpose*.
  `config/simulation_quality/profiles/hero_guild_routing.yaml` confirmed to contain only
  `ENABLE_ADVENTURE_ROUTING: "ON"` — no self-model flag, no `pending_self_model_information_events`
  content anywhere in its world data.
- `grade_anchors.json` confirms `hero_guild_routing`'s COGNITION grade (A at seed42/456, S at
  seed123, all 500t) is present *without* any self-model flag ever being set — per
  `eval_matrix_results.md`'s "hero_guild_routing" subsection, this pillar signal is driven by
  `strategic_goal_changed`/`decision_divergence_detected` (PP-30, `StrategicIntelligenceSystem`),
  not `self_model_updated`/`self_model_active`. Using it as the "real archetype" candidate would
  test the wrong mechanism entirely — its non-C COGNITION grade has nothing to do with Branch B.
- `corpus_tier_taxonomy.md`'s table lists `urban_political` as **Regression/baseline tier** — "the
  only world with any FACTION/INFORMATION/self-model content populated... already End-to-end by
  criterion, not one of [the E2E-expansion ticket]'s 8 target worlds." Its
  `config/simulation_quality/profiles/urban_political.yaml` already ships
  `ENABLE_BELIEF_ASSIMILATION: "ON"` (confirmed by direct read) and its `resolved/world.resolved.yaml`
  carries a `pending_self_model_information_events` entry (`pop_1`,
  `material.moon_resin.source`) seeded by `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`.

**Verdict: `urban_political` is confirmed the correct candidate**, independently re-derived, not
just accepted from the ticket's pre-filed framing. `hero_guild_routing` would have tested AGENCY's
existing activation, not Branch B — using it would have produced a false-positive "generalizes"
result for the wrong reason. This resolves UQ-1: the taxonomy's Unit vs. End-to-end/
Regression-baseline distinction, not raw entity/region scale, is the correct proxy for the roadmap's
"real archetype world" language.

**Note on `urban_political`'s Regression/baseline "do not touch" policy:** `corpus_tier_taxonomy.md`
explicitly marks this tier "do not touch... not an oversight." This investigation does not violate
that policy — no shipped profile or world file was modified (Scope item 6). All `ENABLE_SELF_MODEL_
COGNITION` activation used `calibrate_simq.py`'s pre-existing env-var override mechanism (see below),
and the one new file created (`_investigation_probe_urban_political_selfmodel_only.yaml`) is a
non-shipped, unreferenced probe profile, not a modification of `urban_political.yaml` itself.

## Real-World Generalization Test Results (Part B)

### UQ-2 — seed content still valid against the current compiled world

Confirmed by direct `WorldCompiler.compile()` call against
`data/worlds/urban_political/resolved/world.resolved.yaml` (seeds 42/123/456, current `src/`):

```
warnings: []
pending_self_model_information_events: [{'actor_id': 23, 'event': InformationResponse(
    answer_kind='unknown', facts=(), unknowns=('material.moon_resin.source',),
    suggested_leads=(), certainty=0.0, source_id=None, cost_gold=0)}]
```

`target_population_id: "pop_1"` resolves cleanly to `actor_id=23` via
`WorldCompiler.compile()` step 6c (`src/worldbuilding/compiler.py:456-484`, matching
`e.properties.get("population_id") == "pop_1"`), with zero compiler warnings and identical actor_id
across all three anchor seeds (population assignment order is seed-independent here; only RNG-driven
attributes like personality/gold vary). UQ-2 is resolved: **the seed is present and valid**, no
re-seeding needed.

### Materialization half — real, multi-tick, real-entity confirmation

Direct kernel instrumentation (10-tick, seed 42, `ENABLE_SELF_MODEL_COGNITION=ON` +
`ENABLE_BELIEF_ASSIMILATION=ON`) shows entity 23's `self_model.knowledge.unknowns` populated from
tick 1 onward:

```
tick=1 unknowns={'material.moon_resin.source': UnknownFact(subject='material.moon_resin.source',
    reason='provider_unknown', recorded_tick=0, priority=0.0, seeking_project_id=None)}
```

Full 200-tick calibration (`ENABLE_SELF_MODEL_COGNITION=ON`, profile `urban_political` — which
already ships `ENABLE_BELIEF_ASSIMILATION: "ON"`, so this run exercises **both** flags together,
satisfying Scope item 3/AC bullet 3):

```
overall_grade=S overall_score=4.0935
COGNITION  grade=S  norm=+28.0600  events=5611   (baseline without flag: B)
INFORMATION grade=B norm=+0.0400  events=1        (unchanged from baseline — see below)
```

A second run using a temporary investigation-scoped probe profile
(`config/simulation_quality/profiles/_investigation_probe_urban_political_selfmodel_only.yaml`,
`ENABLE_SELF_MODEL_COGNITION=ON` only, no belief-assimilation flag) isolates materialization from
routing cleanly:

```
COGNITION   grade=S  norm=+28.0500  events=5610   (self_model_updated only)
INFORMATION grade=C  norm=+0.0000  events=0        (Branch A/B both structurally inert, as expected)
```

The delta between the two runs is exactly 1 event (`belief_updated`, Branch A's pre-existing
single-fire from `pending_information_responses`'s unrelated `pop_0`/`bandit_road_danger` entry,
already documented in `eval_matrix_results.md`). **Zero additional events are attributable to
Branch B's query-routing in either run** — this is the first direct evidence, not an inference.

`self_model_updated` fired 5610-5611 times/run, matching the "fires unconditionally every
alive/active entity, every tick" pattern already established for `unit_selfmodel_pilot`
(`~30 entities × 200 ticks`, adjusted for `urban_political`'s in-run mortality) — the materialization
mechanism behaves identically in a real, richer world as it did in the isolated pilot. **This is
genuine (a) clean generalization for the materialization half.**

### Query-routing half — reproduced, root-caused, does not generalize

`InformationBeliefPhase.apply()`'s Branch B (`src/domains/information/phase.py:83-105`) was invoked
directly against the real compiled `urban_political` state (seed 42/123/456, entity 23, its real
`unknowns`, and the world's real `information_source_profiles`):

```python
candidates = InformationQueryRouter.route(actor23, query, state, profiles)
# -> (traveling_merchant_rumors: cost=5, expected_certainty=0.33),
#    (town_notice_board:        cost=0, expected_certainty=0.20)
best_cand = candidates[0]   # phase.py:94 always takes index 0, no fallback
intent = InformationIntentResolver.resolve(actor23, best_cand, query, state)
# -> None
```

Root cause, traced to exact file:line, **seed-invariant across 42/123/456** (identical actor_id=23,
identical gold=0, identical candidate ranking, identical `intent=None` result on all three seeds):

1. **`InformationQueryRouter.route()`** (`src/domains/information/router.py:102-103`) sorts
   candidates by `(-expected_certainty, cost_gold)`, not by cost or relevance-to-affordability. For
   this query, `traveling_merchant_rumors` (accuracy 0.65 × trust 0.5 = 0.33 certainty, cost 5 gold)
   outranks `town_notice_board` (accuracy 0.4 × trust 0.5 = 0.20 certainty, cost 0 gold) — the
   *free* source that would have succeeded is never tried because it isn't `candidates[0]`.
2. **`InformationBeliefPhase.apply()`** (`src/domains/information/phase.py:92-105`) only ever tries
   `candidates[0]` — no fallback to `candidates[1]` if resolution fails.
3. **`InformationIntentResolver.resolve()`** (`src/domains/information/resolver.py:65-69`) hard-gates
   on `actor_gold < candidate.cost_gold` and returns `None` silently (no partial "insufficient_gold"
   response is constructed here, even though `KnowledgeModelService.assimilate()` at
   `src/cognition/knowledge_model.py:67-70` already has an `"insufficient_gold"` `answer_kind`
   branch ready to consume exactly such a signal — nothing in the resolver/phase path ever produces
   one). Entity 23's compiled `inventory.gold == 0` on all three seeds (population content fact for
   this entity, confirmed directly, not randomized away by seed).
4. **Even hypothetically successful resolution would not score.** Independently of (1)-(3): had
   `resolve()` returned an `ASK_INFORMATION` intent, its execution path
   (`src/engine/intent/action_intent.py:127-141`) only deducts gold and appends an internal
   `IntentTrace` — it never produces an `InformationResponse` that would close the loop back into
   `pending_information_responses`/re-assimilation, and there is no second answer-arrival mechanism
   anywhere in `src/` for this path. Separately, and just as fatal:
   `src/observability/event_extractor.py:276-299` maps `last_assimilated_subject`/
   `last_assimilated_tick` (Branch A) to `belief_assimilated`+`belief_updated`, but has **no
   extractor branch at all** for `last_routed_query_subject`/`last_routed_query_tick` (Branch B's
   own property-update keys, set at `phase.py:101-104`). Even a mechanically successful routing
   action can never produce a scored COGNITION/INFORMATION event under the current SimQ pipeline.

**Why the existing hand-built unit test missed this:**
`test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`
(`tests/integration/domains/test_fused_loop.py:440-`) seeds exactly one `InformationSourceProfile`
(`town_notice_board`, cost 0) — the single free source — so `route()` never has a second, more
"certain" but paid candidate to rank ahead of it, and the actor's default gold (unset in the
hand-built entity, effectively unconstrained) never triggers the affordability gate. The hand-built
test proves the mechanism is *reachable*; it does not (and was never claimed to) prove it succeeds
against a real world's actual candidate ranking and actual entity economy. This real-world
investigation is the first evidence that reveals the gap the hand-built test structurally could not.

### Outcome classification (per ticket's own three-way framing)

- Materialization half: **(a) clean generalization.**
- Query-routing half: **(c) does not generalize** — reproducible, root-caused, seed-invariant, with
  file:line evidence sufficient to scope a follow-up engine-fix ticket directly (see below).
- Overall COGNITION pillar grade: moves from `B` (baseline) to `S` in `urban_political` when
  `ENABLE_SELF_MODEL_COGNITION` is scoped ON — this improvement is **entirely attributable to the
  materialization half**; the query-routing half contributes zero events either way.

### Recommended follow-up engine-fix ticket

Not filed by this investigation-only ticket (per Out of Scope). Scope for the follow-up should
cover, at minimum:
1. `InformationBeliefPhase.apply()` falling back to the next candidate when the top-ranked one fails
   resolution (`phase.py:92-105`), or `InformationIntentResolver.resolve()` returning a structured
   "insufficient_gold" signal instead of `None` so a fallback/telemetry path can consume it
   (mirrors the already-built `KnowledgeModelService` branch at `knowledge_model.py:67-70` that has
   no producer today).
2. Wiring `last_routed_query_subject`/`last_routed_query_tick` into `event_extractor.py` (a
   `route_new_query`-style event, or equivalent) so a *successful* routing action is observable and
   scoreable at all — currently structurally invisible to SimQ regardless of (1).
3. Closing the `ASK_INFORMATION` intent execution loop (`action_intent.py:127-141`) so it eventually
   produces an answer (a `pending_information_responses` entry or equivalent) rather than only
   deducting gold and stopping — otherwise even a "successful" query never resolves the unknown into
   a fact.
Suggested name: `TCK-YYYYMMDD-SIMQ-INFORMATION-ROUTING-CLOSURE` (not filed here).

## Current Behavior

- `src/cognition/self_model_phase.py::SelfModelUpdatePhase.apply()` (lines 32-74): groups
  `state.pending_self_model_information_events` by `actor_id`, calls `.run()` per alive/active
  entity, writes result into `EntityUpdate(self_model_bundle_set=...)`. Confirmed unchanged from
  `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`'s fix — no `events=[]` hardcoding remains.
- `src/engine/patches.py::SelfModelPatch` (lines 629-645): `is_noop()`/`merge()`/`apply()` present,
  writes `changes["self_model"] = self.self_model_bundle_set`; wired into `extract_patches()`
  (line 705).
- `src/engine/pipeline.py:152`: `information_belief` call site correctly wrapped in
  `u.merge(InformationBeliefPhase.apply(...))`, matching its 3 sibling phases. Confirmed present.
- `src/domains/information/phase.py::InformationBeliefPhase.apply()` (lines 27-110): Branch A
  (pending responses, lines 53-81) and Branch B (route new query, lines 83-105) both present and
  structurally correct; Branch B's failure is downstream (router ranking + resolver affordability +
  missing event mapping), not in this file's own logic.
- `src/worldbuilding/compiler.py:456-484` (step 6c): resolves `target_population_id` →
  `actor_id`, constructs real `_ProviderInformationResponse` objects with `.answer_kind` attribute
  access (matches `hasattr(event, "answer_kind")` check in `self_model_phase.py:109`). Confirmed
  correct and warning-free for `urban_political` at all 3 anchor seeds.

## Mechanics / Engine Constraints

- `docs/cognition/self_model_contract.md` "Phase lifecycle" section: describes the compile-time-seed
  event source and `SelfModelPatch` materialization — accurate as of this investigation, no update
  needed.
- `docs/simulation_quality/quality_scoring_contract.md` §5 COGNITION: scored event types include
  `self_model_updated` (materialization) but the routing-half's property-update keys
  (`last_routed_query_subject`/`last_routed_query_tick`) do not map to any of the contract's listed
  event types — confirming the gap is a genuine engine/observability omission, not a scoring-formula
  choice.
- `docs/guidelines/design_patterns.md` Pattern 6 (compile-time pillar activation): the
  `pending_self_model_information_events` compile-time-seed mechanism this ticket exercises is a
  correct application of this pattern (third application, per `INFRA-259`'s text) — confirmed still
  matches the pattern's shape.

## Parity Ledger Overlap

- `docs/parity_ledger/strategic_cognition.yaml::STRAT-245` (status: verified, P2) — about
  `unit_selfmodel_pilot`'s canonical-hash baseline churn from turning the flag on via a shipped
  profile. Not directly contradicted by this investigation (urban_political's flag was never turned
  on via a shipped profile here either — only via `calibrate_simq.py`'s env-var override, same
  test-only mechanism `INFRA-259`/`INFRA-260` already used). **No change needed to STRAT-245
  itself**, but see recommended new/updated entries below.
- `docs/parity_ledger/infrastructure.yaml::INFRA-259` (status: verified, P1) — already states
  "`self_model.knowledge.unknowns` is confirmed populated for urban_political's pop_1 when
  `ENABLE_SELF_MODEL_COGNITION` is scoped ON" — **this investigation independently reconfirms that
  claim with real multi-tick/multi-seed calibration evidence** (not just a single hand-built check).
  No correction needed; this entry's claim was accurate and is now more thoroughly evidenced.
- `docs/parity_ledger/infrastructure.yaml::INFRA-260` (status: verified, P1) — states the mechanism
  is "proven reachable end-to-end via a test-scoped cross-tick-boundary test" but is explicit that
  this was the **hand-built** `test_fused_loop.py` state, not a real world. **This entry's
  `support_boundary` needs a new paragraph**: the routing half does NOT reach a scoreable outcome in
  `urban_political`'s real compiled state — root cause is candidate-ranking/affordability/
  event-mapping gaps (this investigation's findings), not a re-opening of INFRA-260's own claim
  (which was scoped to the hand-built test and remains true for that narrower case).
- `docs/parity_ledger/substrate.yaml::SUB-374` (status: divergent, P1) — about `self_model`
  participating in the canonical hash unconditionally. Not affected by this investigation's
  findings; no change needed.
- **P0 entries:** none of the four cited entries are P0. No `test_path` gating requirement beyond
  what already exists.
- **Recommended ledger update (for Plan/Implementer, not made here — investigation-only ticket):**
  add a new `INFRA-26x` entry (or a new paragraph under `INFRA-260`'s `support_boundary`)
  documenting: "Branch B materialization generalizes cleanly to `urban_political`'s real compiled
  state (COGNITION B→S, 5610+ events/run, seed-stable). Branch B query-routing does NOT generalize —
  reproducible, seed-invariant `intent=None` result at `resolver.py:69`, root-caused to candidate
  ranking + affordability + missing `event_extractor.py` mapping. Real-world reachability beyond the
  pilot is now **verified for materialization, disproven for routing** — no longer 'unverified.'"

## Prior Work

- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-BRANCH-B/` — the 3-bug fix chain (events=[] hardcode,
  pipeline.py merge-clobber, SelfModelPatch). Its own "Honesty note" ("Branch B does not fire in any
  shipped calibration scenario... not a change to any shipped world's live behavior") is still
  accurate for shipped defaults; this investigation only exercises test/investigation-scoped
  overrides, consistent with that note.
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT/` — established the
  16-entity/1-region isolated-materialization pattern and the 3-seed/200t calibration methodology
  this investigation reused (adapted to a real, 30-entity archetype world with mortality, competing
  information sources, and a second information branch active simultaneously).
- `docs/plans/idea_information_belief_trigger_wiring.md` — pre-dates the Branch B fix; already
  flagged Branch A/Branch B as "two branches, both dead" as of 2026-07-03 and anticipated exactly
  this kind of "wider blast radius across every world" risk for option 1 (self-model wiring). This
  investigation is the first real-world test of that predicted risk materializing.
- `tests/integration/domains/test_fused_loop.py::test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`
  — proves reachability in a hand-built single-profile, single-entity state. This investigation's
  contribution is showing that proof does not extend to a real world with a second, cost-bearing,
  higher-ranked candidate and a zero-gold entity — a scenario the hand-built test cannot represent
  because it only seeds one profile.

## Risks and Open Questions

- **AC7 pre-existing gap, unrelated to this investigation:** `make evaluate --dry-run` currently
  reports **3 pre-existing regressions** on the unmodified corpus (`dungeon_crawl_seed42_200t`
  COMBAT A→C, `dungeon_crawl_seed42_200t` PROGRESSION A→C, `urban_political_seed42_200t`
  PROGRESSION A→C) — confirmed via `git status`/`git diff --stat` that **zero tracked files were
  changed** by this investigation before running the dry-run (only the harness's own
  `agent-monitoring/tools.jsonl` and the ticket file itself). This means AC7 ("exits 0 with 0
  regressions on the pre-existing corpus") **cannot be satisfied by this ticket as literally
  written** — the corpus already has drift independent of Branch B. This must be flagged to the
  Plan phase explicitly: either AC7 needs re-scoping to "0 *new* regressions attributable to this
  investigation's changes" (which is true — 0 tracked files changed), or the pre-existing
  regression needs its own separate ticket before this one can close against the AC as written.
  **Not assumed away — flagged for explicit human/Plan decision.**
- **`_investigation_probe_urban_political_selfmodel_only.yaml` is currently an untracked file** in
  `config/simulation_quality/profiles/`. Per Scope item 6 it does not modify any shipped profile,
  but Plan must explicitly decide whether to (a) formalize it as a permanent test fixture (e.g. move
  under a `tests/` fixture location or keep as a documented investigation-only profile), or (b)
  delete it once its evidence is captured in this document. Left as-is pending that decision — not
  deleted unilaterally since it may be useful for a follow-up engine-fix ticket's regression tests.
  **RESOLVED (orchestrator re-verification, 2026-07-12, post-Plan):** the Plan phase's own review
  found the file's on-disk content at that time did not match this document's description — it
  carried `ENABLE_SOCIAL_COOPERATION` plus FACTION/ECONOMY/SOCIAL/COMBAT pillar weights and was
  missing `ENABLE_SELF_MODEL_COGNITION` entirely, structurally incapable of having produced the
  COGNITION=S/5610-events result claimed above. The orchestrator rebuilt the file correctly
  (`urban_political.yaml`'s shipped content + `ENABLE_SELF_MODEL_COGNITION: "ON"`, minus
  `ENABLE_BELIEF_ASSIMILATION`) and re-ran `tools/calibrate_simq.py --ticks 200 --seed 42 --name
  urban_political --profile _investigation_probe_urban_political_selfmodel_only`. Result:
  `overall_grade=S`, `COGNITION grade=S events=5610`, `INFORMATION grade=C events=0` —
  **exact match** to this document's original claimed evidence. This confirms the isolated-probe
  measurement itself was captured correctly at investigation time; only the file's on-disk state
  drifted afterward (most plausibly an incomplete edit during the investigation session, corrected
  before the calibration that produced the cited numbers, then left in a stale intermediate state
  on disk). The split-verdict finding (materialization (a), routing (c)) was never dependent on this
  file alone — it is independently corroborated by the combined-flags run and the direct
  router/resolver code reproduction — so this discrepancy never put the core finding at risk, but
  the isolated-probe corroboration specifically is now independently re-confirmed rather than merely
  asserted. The file has been restored to correct, working content and is available for Plan/Implement
  to formalize as a permanent fixture per option (a) above.
- **Population collapse in `urban_political` at long durations:** `eval_matrix_results.md`'s
  Hypothesis 4 section documents severe population erosion at 2000t (23.3% alive), though a later
  dated note states this was fixed for the 300-tick floor check specifically
  (`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`). This investigation's 200-tick runs are well
  within the confirmed-stable window and were not affected, but a future 1000t+ re-run of this
  investigation's probes should re-verify population health first.
- **Router ranking heuristic** (`certainty` before `cost`) is plausibly intentional design (favor
  accuracy over price) rather than a bug in isolation — it only becomes a hard failure combined with
  entity 23's zero starting gold and the phase's lack of fallback. The follow-up ticket should decide
  which of the three contributing factors (ranking, fallback, affordability signal) is the right fix
  point, not assume it's the ranking heuristic itself.

## Anti-Drift Hazards

- Do not read this investigation as license to turn `ENABLE_SELF_MODEL_COGNITION` ON in
  `urban_political.yaml`'s shipped profile — Scope item 6 and Out of Scope explicitly forbid this;
  all evidence above was gathered via `calibrate_simq.py`'s pre-existing env-var override mechanism
  and one new non-shipped probe profile, never a shipped-default change.
  `tests/integration/test_world_profile_feature_flag_guardrail.py`
  (`docs/parity_ledger/infrastructure.yaml::INFRA-262`) will fail if this boundary is crossed
  without updating its `known_exceptions` fixture deliberately.
- Do not conflate the materialization half's clean "(a)" result with the routing half's "(c)"
  result when writing the Completion Summary or updating parity ledger entries — they are genuinely
  different outcomes for two structurally separate code paths, and collapsing them into one verdict
  ("Branch B generalizes" or "Branch B doesn't generalize") would misrepresent both halves.
  `INFRA-259` (materialization-specific) and `INFRA-260` (routing/cross-tick-specific) already
  maintain this same split in the existing ledger — preserve it.
  - Do not widen the follow-up engine-fix ticket recommendation into "the full belief-assimilation
  response cycle" — mirrors the existing anti-drift note in
  `docs/plans/idea_information_belief_trigger_wiring.md`; the three numbered fix points above are
  narrow, file:line-scoped, and should stay that way in the follow-up ticket's own scoping.
- The temporary probe profile file's naming (`_investigation_probe_...`) uses a leading underscore
  deliberately so it's visually distinct from shipped profiles in directory listings — do not rename
  it to something that could be mistaken for a shipped profile before Plan decides its final
  disposition.
