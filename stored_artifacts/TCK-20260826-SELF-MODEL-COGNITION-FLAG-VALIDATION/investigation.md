---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION
artifact_type: investigation
tags: [feature-flags]
---

# Investigation — TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION

## Method
`mcp__knowledge-search__search_docs` (query: "ENABLE_SELF_MODEL_COGNITION flag validation rollout
decisions urban_political self-model self_model") returned `{"error":"index not found","action":"run
make knowledge-index"}` — index unavailable this session. Fallback
`python3 tools/knowledge_search.py query "ENABLE_SELF_MODEL_COGNITION flag validation" --top-k 5`
(run with the venv interpreter) returned `knowledge index not found — run make knowledge-index` —
also unavailable. Both semantic-search paths are confirmed down this session (matching the
orchestrator's own prior-session confirmation cited in the sibling ticket's investigation.md), so
per CLAUDE.md's own fallback design this proceeded directly to `graphify query
"ENABLE_SELF_MODEL_COGNITION self_model_phase feature flag validation"` (261 nodes returned via
BFS depth=2 from `self_model_phase.py`/`feature_flags.py`/`FeatureFlagManager` — confirmed
`SelfModelBundle`, `KnowledgeModelComponent`, `test_phase2_self_model_phase.py`,
`test_phase2_self_model_scenarios.py` as primary code/test targets, consistent with what direct
reads below independently confirm), then to the explicit file list and targeted grep/reads below.

## Current Behavior

### `SelfModelUpdatePhase` (`src/cognition/self_model_phase.py`)
`apply(state, update)` (lines 32-74) groups `state.pending_self_model_information_events` by
`actor_id` (lines 45-50 — the `INFRA-259` events-sourcing fix), then for every alive+active entity
calls `SelfModelUpdatePhase.run()` (lines 76-220) and writes the resulting `SelfModelBundle` onto
`EntityUpdate.self_model_bundle_set` (lines 64-71). `run()` performs 4 steps: (1) knowledge
assimilation from any `InformationResponse`-shaped events (lines 103-141, via
`KnowledgeModelService.assimilate()`), (2) self-assessment + a dirty-check short-circuit (lines
143-161 — skips need-interpretation/capability-estimation work when nothing changed, a real
performance optimization, not a correctness gate), (3) need interpretation (lines 175-196), (4)
capability estimation, only if a `capability_context` is supplied (lines 198-213). This orchestrates
`SelfAssessmentService`, `NeedInterpretationService`, `CapabilityEstimateService`,
`KnowledgeModelService` — confirmed as described in `feature_flags.py`'s own comment ("real call
site... 10 test files").

### `FeatureFlagManager` (`src/domains/optimization/feature_flags.py`)
`ENABLE_SELF_MODEL_COGNITION` defaults `FeatureMode.OFF` (line 19), with an inline comment already
citing this exact ticket as the deferred follow-up (lines 15-18). `FeatureMode` is
`OFF | SHADOW | ON | STRICT`; `is_enabled()` (line 132-133) treats `ON`/`STRICT` as enabled. Of the
8 flags `TCK-20260824-ROLLOUT-FLAG-DECISIONS` reviewed, this is one of 5 kept `OFF, deferred`, each
with a named per-flag follow-up ticket (this one, `COMBAT-ENGAGEMENT`, `WORLD-EMERGENCE`,
`PROGRESSION-EVOLUTION`, `INFORMATION-INTENT-EXECUTION`).

### `tests/integration/test_world_profile_feature_flag_guardrail.py` — T5
`test_self_model_flag_content_pairing_both_directions_with_documented_exception` (lines 186-228)
asserts, per world, `pending_self_model_information_events` seeded ⇔ `ENABLE_SELF_MODEL_COGNITION`
ON, **except** `urban_political`, which is allow-listed via
`tests/simulation_quality/fixtures/expected_world_flag_state.json`'s
`known_exceptions.self_model_content_without_flag` block (cited to `INFRA-259`/`INFRA-260`,
`content_seeded=True, flag_on=False`, "verified via a test-scoped override only... never a shipped
profile default"). Re-ran this file directly this session (`.venv/bin/python3 -m pytest
tests/integration/test_world_profile_feature_flag_guardrail.py -q` → **67 passed**), confirming the
exception and all 7 guardrail test functions still hold today, not just per the doc's prose.

### Why `urban_political` has seeded-but-unflagged self-model content — independently re-confirmed
`pending_self_model_information_events` was seeded in `data/worlds/urban_political/world.yaml`
(`pop_1`, `material.moon_resin.source`, `answer_kind=unknown`) as part of
`TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`'s Step 8 (`INFRA-259`/`INFRA-260`: the events=[] sourcing fix
and the `information_belief` pipeline-wiring merge fix, both required together for "Branch B" —
self-model materialization + query-routing — to compose correctly). `INFRA-259`'s text confirms
this reaches the real actor when `ENABLE_SELF_MODEL_COGNITION` is scoped ON via a test-only
override, but the flag "stays OFF everywhere" in shipped `config/simulation_quality/profiles/*.yaml`
and `data/worlds/*.yaml` — confirmed still true by direct read of every profile YAML this session
(only `unit_selfmodel_pilot.yaml` ships the flag ON, in its own dedicated Unit-tier world).
`INFRA-266` (`TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`) later ran a **real 200-tick,
3-seed (42/123/456) calibration trial with `ENABLE_SELF_MODEL_COGNITION` scoped ON via
`calibrate_simq.py`'s env-var override**, directly against `urban_political`'s real compiled state
(`actor_id 23`, `pop_1`): a **split verdict** — the materialization half generalizes cleanly (grade
B→S, ~5610-5611 `self_model_updated`/`self_model_active` events/run, seed-invariant), but the
query-routing half did not reach a scoreable outcome at that time (router ranks a paid candidate
ahead of a free one by certainty; `InformationBeliefPhase.apply()` had no fallback past
`candidates[0]`; the affordability gate silently returned `None`). `INFRA-267`
(`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`) subsequently fixed all 3 routing-half root causes
plus a 4th observability gap — confirmed still present and correct in `phase.py`/`router.py`/
`resolver.py`/`event_extractor.py` per `INFRA-267`'s `v2_evidence` citations (not independently
re-read line-by-line this session, since this ticket's own Out of Scope excludes touching
`InformationBeliefPhase`'s logic).

**Two permanent grade-anchor probe profiles now exist**, formalizing this evidence chain:
- `config/simulation_quality/profiles/urban_political_selfmodel_probe.yaml` — rebuilt from
  `urban_political.yaml`'s real shipped profile with `ENABLE_SELF_MODEL_COGNITION: "ON"` added and
  `ENABLE_BELIEF_ASSIMILATION` (which `urban_political.yaml` itself ships `ON`) explicitly
  **removed**, isolating materialization from query-routing. Backs
  `test_urban_political_selfmodel_cognition_isolated_grade_anchor`
  (`tests/simulation_quality/test_grade_regression.py:424-464`): anchors `COGNITION=S`,
  `INFORMATION=C`/`event_count=0` (Branch A/B never run, by design).
- `config/simulation_quality/profiles/urban_political_selfmodel_execution_probe.yaml` — adds
  `ENABLE_BELIEF_ASSIMILATION: "ON"` and the new `ENABLE_INFORMATION_INTENT_EXECUTION: "ON"` on top,
  so a routed `ActionIntent` actually executes through `InformationIntentExecutionPhase`. Backs
  `test_urban_political_selfmodel_execution_isolated_grade_anchor`
  (`test_grade_regression.py:466-505`) — its own docstring discloses honestly that
  `urban_political`'s real compiled state, at this specific seed/window, does **not** route a query
  within 200 ticks (0 `ActionIntentAdapter` traces, matching `INFRA-266`'s "does NOT generalize"
  finding for this exact corpus/seed) — this anchor proves the new phase does not regress the
  calibration pipeline when wired in and gated ON, not that Branch B routes in this specific corpus.
  The deterministic, guaranteed proof of `ActionIntentAdapter.execute()` firing through a real
  `Kernel.tick_once()` loop is a separate, minimal hand-built scenario test
  (`test_information_intent_execution_fires_through_kernel_tick_once`, same file, lines 507-616).

**Re-run this session**: `.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py
-k selfmodel -q` → **6 skipped** (not failed). Both grade-anchor probe tests, plus 4 other
`selfmodel`-matched tests, skip because `data/calibration/{run_key}/quality_report.json` does not
exist locally — `data/calibration/` is gitignored/ephemeral, confirmed empty
(`ls data/calibration/` → 0 entries) in this worktree. The tests' own guard logic
(`if report is None: pytest.skip(...)`) is intact and correctly distinguishes "not yet run
locally" from "failing" — this is expected, not a regression, but it means this session did **not**
independently re-verify the actual grade numbers (`COGNITION=S`, `INFORMATION=C`) without running
`tools/calibrate_simq.py` for those two profiles; it only confirmed the test scaffolding/assertions
and the fixture data (`grade_anchors.json`) are intact and unskipped-by-default. Separately re-ran
`tests/unit/cognition/test_phase2_self_model_phase.py` + `tests/unit/config/test_phase10_feature_flags.py`
together (**12 passed**) and `tests/integration/domains/test_fused_loop.py -k "self_model or branch_b
or belief"` (**7 passed, 3 deselected** — includes the cross-tick-boundary Branch B proof).

`unit_selfmodel_pilot` (`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`) remains **the only
world whose own default profile ships `ENABLE_SELF_MODEL_COGNITION: "ON"`**
(`config/simulation_quality/profiles/unit_selfmodel_pilot.yaml`, confirmed 2 lines, flag only) — a
dedicated, purpose-built, single-mechanic-isolation Unit-tier world (16 entities), not a real
archetype world. Its 3-seed/200t run measured `COGNITION=S` at all 3 seeds,
`event_count=3200 = 16 entities × 200 ticks` exactly (`self_model_updated` fires unconditionally
every tick for every alive/active entity — confirmed by `SelfModelUpdatePhase.run()`'s own
unconditional per-entity loop, `self_model_phase.py:52-71`, no probability/threshold gate anywhere
in that loop). `STRAT-245` records this as the "first calibration-anchored world" to do so.

### The `ENABLE_SELF_MODEL_COGNITION` + `ENABLE_ADVENTURE_ROUTING` combination — resolved
Independently confirmed via `grep -rn "ENABLE_ADVENTURE_ROUTING" src/ tools/`: the only matches are
(1) `feature_flags.py:25` — the flag's own registration, default `OFF`; (2)
`adventure_scorer.py:120` — a comment *stating* the flag no longer gates anything; (3)
`scenario_runner.py:103` — a test-weight dict entry (`"ENABLE_ADVENTURE_ROUTING": 1.0`) used only
to construct scenario perspective weightings, not a live gate; (4) three `tools/*.py` references
(`calibrate_simq.py`'s comment/allow-list, `balance_measure.py`, `personality_audit.py`) that set
the flag to `1.0`/`ON` for their own legacy CLI convenience, but nothing downstream in `src/` reads
it as a gate anymore. **Zero live `is_enabled("ENABLE_ADVENTURE_ROUTING")` or
`get_flag_mode("ENABLE_ADVENTURE_ROUTING")` call site exists anywhere in `src/`.**
`AdventureDecisionPhase` — the phase the flag used to gate via
`run_phase(..., feature_flag="ENABLE_ADVENTURE_ROUTING")` — was deleted in full by
`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE` (confirmed: ticket's own AC2, "grep for
AdventureDecisionPhase in src/engine/pipeline.py returns no matches... src/domains/adventure/
phase.py deleted entirely"). Its replacement, `AdventureGoalScorer.score()`
(`src/ai/goals/adventure_scorer.py:87-`, read directly this session) runs **unconditionally** every
tick as a tier-5 `GoalScorer` candidate inside the always-on `StrategicIntelligenceSystem`
pipeline — its own comment (lines 119-121) states explicitly: "reached unconditionally, every tick,
for every entity eligible per `_supports_adventure_routing()`... not gated behind
`ENABLE_ADVENTURE_ROUTING` or any other flag (see `docs/parity_ledger/strategic_cognition.yaml
STRAT-252`)." `docs/engine/known_limitations.md` §1.5 (read directly, lines 33-65) already documents
this exact inertness in prose: "flipping it ON or OFF no longer changes any live behavior... The
flag entry still exists in `FeatureFlagManager`... for backward compatibility."

**Conclusion**: the "untested combination" framing in `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s own
Assumptions/Open Questions is now a non-issue as a *behavioral interaction* risk — there is no
runtime code path where `ENABLE_ADVENTURE_ROUTING`'s value can affect anything
`ENABLE_SELF_MODEL_COGNITION`-gated code does, or vice versa, because `ENABLE_ADVENTURE_ROUTING`
gates nothing at all today. Static analysis (this grep + `known_limitations.md`'s existing
citation) is sufficient evidence to resolve this specific sub-question; no corpus trial combining
both flags is needed to prove a negative that the code itself already guarantees structurally. This
is a distinct question from "does `ENABLE_SELF_MODEL_COGNITION` alone generalize to a real
archetype world" (INFRA-266/267 already answer that with real trial evidence, see above) — Plan
should resolve AC2 by citing this static finding, not by scheduling a combination trial that cannot
produce a different structural answer.

## Mechanics / Engine Constraints
- **Kernel 7-phase loop** (`docs/engine/kernel.md`): `self_model` runs inside the Resolution phase
  of `AuthoritativeApplyPipeline.refine()` (`pipeline.py` line ~143 per
  `TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md`'s own confirmed call-site census — not
  independently re-read line-by-line this ticket since `pipeline.py`'s self_model registration is
  out of this ticket's edit scope).
- **Durable State Rule**: `EntityUpdate.self_model_bundle_set` materializes only through the
  authoritative apply path (`SelfModelPatch`, `src/engine/patches.py`, per `SUB-374`) —
  `self_model` participates unconditionally in `EntityState.to_canonical_dict()` /
  `CanonicalStateHasher.to_canonical_data()`, so flipping this flag ON for any world changes that
  world's committed canonical-hash baseline (`STRAT-245`'s own disclosed baseline-churn note). Any
  future flip-ON ticket must account for this, though flipping is explicitly Out of Scope here.
- **Strategic/Tactical Rule**: `SelfModelUpdatePhase` is purely a strategy/perception-layer system
  (self-awareness, need interpretation, capability estimation) — it does not authoritatively mutate
  combat/economy state, consistent with the boundary this rule draws.
- **Mechanics Bible** §4 (`docs/mechanics/04_strategic_cognition.md`) covers "Knowledge management,
  perception" generally; this ticket's evidence-gathering scope does not require a formula-level
  parity check against that chapter (no formula changes proposed).

## Docs Requiring Update
- `docs/architecture/rollout_flag_decisions_m1.md`: this file's own `ENABLE_SELF_MODEL_COGNITION`
  table row (`| ENABLE_SELF_MODEL_COGNITION | **Kept OFF, deferred** | No production evidence...
  Follow-up: TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION. |`) explicitly names this ticket as
  the open follow-up that must update it. Per the exact sibling precedent
  (`ENABLE_COMBAT_ENGAGEMENT — Validation Trial Result (TCK-20260826)`), this ticket must update the
  row's Verdict/Rationale cell in place and add a new `## ENABLE_SELF_MODEL_COGNITION — Validation
  Trial Result (TCK-20260826)` section documenting: the corpus-profile trial evidence already on
  file (`unit_selfmodel_pilot`'s shipped-profile 3-seed run, the two `urban_political_selfmodel*`
  probe grade anchors, and `INFRA-266`'s real-world-generalization trial) plus whatever
  confirming/fresh trial Plan decides to run, and the resolved `ENABLE_ADVENTURE_ROUTING` combination
  finding (static, not empirical) documented above. Leaving the row unchanged after this ticket
  closes would make the decision artifact stale and undiscoverable — the exact failure mode
  `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s own precedent exists to prevent.

Whether `docs/guidelines/intentional_divergences.md` needs a new `DEV-00N` entry depends on the
final recommendation, which this investigation does not pre-decide (Uncertainty Rule — "vague leads
stay vague until evidence narrows them"; this is Implement's call once Plan commits to a
recommendation). If the recommendation is "keep OFF, deferred" (the evidence assembled here points
this way — see Risks below — matching every one of the other 4 sibling deferred-flag tickets'
expected pattern), no new divergence entry is needed: the flag's behavior versus the Mechanics Bible
does not change either way, only the evidentiary basis for staying deferred does, which lives in
`rollout_flag_decisions_m1.md` per the sibling's own precedent. If the real trial instead drives a
flip recommendation, a new `DEV-00N` entry (`DEV-003`-shaped) would be required — not written here.

The `docs/parity_ledger/infrastructure.yaml` entries (`INFRA-259`, `INFRA-260`, `INFRA-266`,
`INFRA-267`, path: `docs/parity_ledger/infrastructure.yaml`) and `docs/parity_ledger/
strategic_cognition.yaml` (`STRAT-245`, `STRAT-252`, path: `docs/parity_ledger/
strategic_cognition.yaml`) are **not** required to change for this ticket: all 6 entries were
re-read directly this session and are already accurate to the current code/config state (confirmed
by the grep/pytest re-verification above) — this ticket's own Out of Scope explicitly forbids
resolving `urban_political`'s `INFRA-259`/`INFRA-260` exception "unless this ticket's own trial
directly requires it," and nothing found so far requires it. If Plan's chosen confirming trial
surfaces a genuinely new finding (not expected, given how much prior evidence already exists), the
relevant entry would need a new `v2_evidence`/`support_boundary` addendum then — not assumed here.

## Parity Ledger Overlap
- `INFRA-259` (`status: verified`, `priority: P1`) — the events=[] sourcing fix. Still accurate.
- `INFRA-260` (`status: verified`, `priority: P1`, implied by context — not independently re-quoted
  for status/priority fields, only its `text` was grepped) — the `information_belief` merge-wiring
  fix. Still accurate per `INFRA-266`'s superseding real-world confirmation.
- `INFRA-266` (`status: verified`, `priority: P1`) — the real-world generalization split verdict.
  Still accurate; this ticket's trial (whatever Plan scopes) should be read as *additional*
  confirming evidence layered on top of this entry, not a replacement for it.
- `INFRA-267` (`status: verified`, `priority: P1` implied) — the query-routing closure fix. Still
  accurate; `ENABLE_INFORMATION_INTENT_EXECUTION` is a separate, still-deferred flag with its own
  named follow-up ticket (`TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION`), out of this
  ticket's scope.
- `STRAT-245` (`status: verified`, `priority: P2`) — `unit_selfmodel_pilot`'s shipped-ON canonical
  hash baseline-churn note. Still accurate.
- `STRAT-252` (`status: verified`, `priority: P2`) — `AdventureGoalScorer` unconditional/unflagged
  materialization, directly supporting the `ENABLE_ADVENTURE_ROUTING` combination resolution above.
  Still accurate.
- No `P0` parity entry names `ENABLE_SELF_MODEL_COGNITION` specifically (all 6 entries found above
  are `P1`/`P2`) — no `test_path` requirement blocks this ticket per the P0 rule.

## Prior Work
- **`TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`** — the original 3-bug fix chain (events=[] sourcing,
  merge-wiring, `SelfModelPatch` materialization) that made Branch B mechanically correct and
  reachable. `INFRA-259`/`INFRA-260`/`SUB-374`.
- **`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`** (read directly, `tickets/done/`) — first
  calibration-anchored world to ship `ENABLE_SELF_MODEL_COGNITION: "ON"` by default, real 16-entity/
  3-seed/200-300-tick evidence, `COGNITION=S` across all seeds, 100% population stability through
  300 ticks. Deliberately isolated from `ENABLE_BELIEF_ASSIMILATION` (kept OFF) to avoid
  re-triggering the original Finding-4 interaction bug. `STRAT-245`.
- **`TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`** — the real-world generalization trial
  against `urban_political`'s actual compiled state (not a dedicated new world); split verdict,
  `INFRA-266`.
- **`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`** — fixed the 4 routing-half root causes
  `INFRA-266` found, formalized `urban_political_selfmodel_probe.yaml` as a permanent grade-anchor
  fixture and its backing test. `INFRA-267`.
- **`TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE`** — added `ENABLE_INFORMATION_INTENT_EXECUTION` and
  the `urban_political_selfmodel_execution_probe.yaml` permanent grade-anchor fixture proving the
  new phase doesn't regress calibration when wired in and gated ON.
- **`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`** — deleted `AdventureDecisionPhase`, cut over to
  `AdventureGoalScorer`, the fact this investigation's `ENABLE_ADVENTURE_ROUTING` resolution rests
  on. `STRAT-252`/`STRAT-253`.
- **`TCK-20260824-ROLLOUT-FLAG-DECISIONS`** — reviewed all 8 Phase-10 flags including this one,
  deferred it specifically because "no production evidence" was the stated rationale at the time —
  this investigation shows that framing understated what already existed (a shipped-profile world,
  two formalized grade-anchor probes, and a real cross-tick 3-seed generalization trial all predate
  that ticket's own review), a nuance Plan should weigh when writing the final recommendation.
- **`TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION`** — the sibling ticket this investigation
  mirrors in format/rigor. Its own recommendation ("Keep OFF, deferred — real trial evidence now on
  file, but still no standing production profile usage") used the same DEV-003 standard
  (`rollout_flag_decisions_m1.md`'s own "## The Precedent This Sets": flip requires a *shipped*
  profile already exercising the flag in production, not a one-off/probe-only trial) this
  investigation's evidence should be measured against.

## Risks and Open Questions
- **Open question (Plan's job, not pre-decided here): does the existing probe-profile/real-world
  evidence already satisfy AC1 ("a real corpus-profile ON trial is run and documented"), or does
  this ticket need to run a genuinely new/fresh trial?** The two `urban_political_selfmodel*_probe`
  profiles and `INFRA-266`'s trial are real corpus-profile trials against `urban_political`'s actual
  compiled state, already documented in `eval_matrix_results.md`/parity-ledger entries — but they
  predate this ticket and were not run *by* it. Two legitimate options for Plan: (a) regenerate the
  two probe profiles' `data/calibration/` reports fresh under this ticket's own run (cheap, reuses
  the already-established mechanism, directly re-confirms the still-`skipped`-locally grade-anchor
  tests) or (b) run an entirely fresh trial mirroring `INFRA-266`'s original env-var-override method
  independently. Given how much real evidence already exists (materially more than the combat-
  engagement sibling had at the same review point — 3 independent real trials vs. that sibling's 0),
  a fresh confirming run (option a) is likely sufficient and proportionate; committing to a brand-new
  experiment design is not required by the evidence gap itself.
- **Resolved, not open**: the `ENABLE_ADVENTURE_ROUTING` combination question (AC2) — see "The
  combination — resolved" above. Static analysis is sufficient; do not schedule an empirical
  combination trial, since no runtime path exists for the two flags to interact.
- **Risk**: per DEV-003's own stated flip standard (a *shipped* profile already exercising the flag
  in real production, not a probe-only fixture), `unit_selfmodel_pilot` is the sole flag-ON shipped
  profile, and it is a dedicated Unit-tier isolation world (16 entities), not a real archetype world
  like `urban_political`/`sandbox_world`. The two `urban_political_selfmodel*_probe` profiles are
  explicitly **not** shipped as `urban_political`'s own default profile — they exist solely to back
  `test_grade_regression.py`'s regression guards. This is a materially weaker "shipped production
  usage" case than `ENABLE_BELIEF_ASSIMILATION`/`ENABLE_SOCIAL_COOPERATION`'s own flip evidence
  (both already `ON` in `urban_political.yaml`'s and/or `sandbox_world.yaml`'s *own* default
  profile). The expected recommendation, absent a surprising fresh-trial finding, is therefore
  "Keep OFF, deferred" — same class of outcome as the combat-engagement sibling — not a flip. This is
  Plan's judgment call to state explicitly, not assumed as fixed here.
- **Risk**: the 6 `selfmodel`-matched `test_grade_regression.py` tests are currently `skipped`
  locally (no `data/calibration/` reports present) — Plan/Implement must actually run
  `tools/calibrate_simq.py` (or `make evaluate`) to produce fresh reports before these tests can
  meaningfully re-verify the anchored grades, rather than relying on their `skip`-passing status as
  evidence of correctness.

## Anti-Drift Hazards
- **Do not conflate this ticket with fixing or extending `SelfModelUpdatePhase`/
  `KnowledgeModelService`/`InformationBeliefPhase` themselves.** Out of Scope excludes flipping the
  flag's default and resolving `urban_political`'s `INFRA-259`/`INFRA-260` exception "unless this
  ticket's own trial directly requires it" — a fresh confirming trial reproducing already-known
  results does not, by itself, require resolving that exception.
- **Do not add `ENABLE_SELF_MODEL_COGNITION` to any `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist copy**
  (`tests/unit/config/test_phase10_feature_flags.py`,
  `tests/integration/test_scenario_feature_flag_defaults.py`,
  `tests/certification/test_phase10_enhanced_determinism_parity.py`) under the expected "keep OFF"
  outcome — that only happens in a future, separate flip ticket, exactly as the combat-engagement
  sibling's own Scope Guards state for its own flag.
- **Do not create or edit any `config/simulation_quality/profiles/*.yaml` to make `urban_political`
  itself ship the flag ON** — that would fabricate the "shipped production evidence" this ticket
  exists to honestly assess, not find.
- **Do not treat the two probe profiles' existing grade-anchor `S`/`C` results as this ticket's own
  new finding** — they are prior work (`TCK-20260712`/`TCK-20260713`), to be cited and (if Plan
  chooses) re-confirmed with a fresh run, not re-presented as newly discovered.
- **Do not schedule or attempt an empirical `ENABLE_SELF_MODEL_COGNITION` + `ENABLE_ADVENTURE_ROUTING`
  combination trial** — the static-analysis finding above (zero live gating call sites for the
  latter) already resolves this; an empirical trial would burn real compute to re-confirm something
  the code structure already guarantees, and risks the sibling's own documented "0 vs 0 passes
  trivially" false-confidence trap for a flag that has no live effect either way.
- **Clean up `data/runs/*`/`data/calibration/*` trial output at Finalize**, per Definition of Done —
  same as the combat-engagement sibling's own precedent.
