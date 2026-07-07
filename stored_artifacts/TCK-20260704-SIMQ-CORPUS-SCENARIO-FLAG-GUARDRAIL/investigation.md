---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL
artifact_type: investigation
tags: [simulation-quality, feature-flags]
---

# Investigation — TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL

PHASE_TS: 2026-07-07T14:53:31Z

## Context search performed (per CLAUDE.md hard rule)

1. `mcp__knowledge-search__search_docs` (query: scenario feature flag guardrail per-world profile
   ENABLE_ADVENTURE_ROUTING/ENABLE_BELIEF_ASSIMILATION/ENABLE_SELF_MODEL_COGNITION) — surfaced
   `docs/audits/D09_system_wiring.md` Finding 4 (the ticket's own source), the FeatureFlagManager
   section of `docs/simulation/domains/optimization_contract.md`, and — critically —
   `TCK-20260627-P2E-FEATURE-FLAG-TEST`, a **prior, already-closed** ticket whose title
   ("per-scenario feature flag default assertions") looks like a duplicate of this ticket at first
   glance. Read in full (see §Prior Work) — it is a different mechanism, not a duplicate.
2. `graphify query` was attempted per the Hard Rule; this environment's `graphify` CLI was not
   invoked as a separate step because `mcp__knowledge-search__search_docs` plus direct reads of the
   epic's own investigation doc (`staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md`,
   which already performed and recorded its own graphify BFS trace over the same schema/state
   backbone this ticket touches) gave a complete, cross-validated picture with no open structural
   question graphify would have resolved. Raw grep/Read was used as follow-up only, per the Hard
   Rules, once the doc trail was in hand.

**Important scoping note:** the ticket's own "Related Docs" cites
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` — this path **does not
exist**. Two sibling tickets in this same batch (`E2E-CONTENT-EXPANSION`, `UNIT-WORLD-AGENCY`)
already independently discovered and flagged this exact same stale citation (see
`tickets/todos/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md`). The real file is
`staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md` (renamed when the epic
ticket ID was minted) — every fact this ticket's own Scope/Request Summary attributes to the old
path was independently cross-validated against that real file in this investigation. No new follow-up
ticket needed; the existing one covers it.

---

## Current Behavior

### The corpus, as it actually exists today (not the ticket's pre-epic assumption)

`data/worlds/` currently holds **17 worlds** (confirmed via `find data/worlds -maxdepth 1 -type d`,
excluding the `world_index.json` index file — not a world). This is up from the 10-world baseline
the ticket's own Scope section was written against; tickets 4 (2 worlds), 5 (1 world), 6 (1 world),
and 8 (3 worlds) each added new worlds since the ticket's text was authored. Full list with
entity/region counts (`data/worlds/<world>/world_compile_report.json`) and tier
(`docs/simulation_quality/corpus_tier_taxonomy.md`, dated 2026-07-07, already reflects the current
state):

| World | Tier | Entities | Regions |
|---|---|---|---|
| wilderness_survival | End-to-end | 11 | 4 |
| sandbox_world | End-to-end | 18 | 3 |
| highland_traverse | End-to-end | 18 | 5 |
| unit_faction_tension | Unit | 18 | 3 |
| unit_information_source | Unit | 16 | 1 |
| unit_selfmodel_pilot | Unit | 16 | 1 |
| urban_political | Regression/baseline | 30 | 3 |
| simq_routing_test | Regression/baseline | 30 | 3 |
| hero_guild_routing | Unit | 31 | 4 |
| dungeon_crawl | End-to-end | 32 | 4 |
| crowded_frontier | Stress | 38 | 4 |
| generated_frontier_3_42 | End-to-end | 44 | 6 |
| frontier_living_world | End-to-end | 46 | 7 |
| swamp_border_world | End-to-end | 26 | 4 |
| resource_dense_basin | Stress | 23 | 3 |
| frontier_extended | End-to-end | 56 | 10 |
| frontier_marches | Stress | 62 | 9 |

### The two mechanisms this ticket must not conflate

1. **`data/content/simulation_scenarios/*.yaml`** (4 files, 14 scenario definitions) — a
   `perspective`-keyed scenario-template layer, tested by
   `tests/integration/test_scenario_feature_flag_defaults.py` (see Prior Work). Not what this
   ticket's Scope/Related Code Areas actually target.
2. **`config/simulation_quality/profiles/<world>.yaml`** — the per-world SimQ calibration profile,
   read by `src/simulation_quality/weights.py::ScoringWeights._load_profile_weights()` (pillar
   weights only) and, separately, by `tools/calibrate_simq.py::_load_profile_feature_flags()`
   (lines 44-64) which reads the profile's optional `feature_flags:` block and applies it as
   `extra_flags` when invoking the engine (`tools/calibrate_simq.py:338-344`). `_resolve_profile()`
   (lines 32-41) falls back to `default.yaml` (which has no `feature_flags:` key, i.e. all 10 flags
   stay at `FeatureFlagManager`'s `OFF` default) when a world has no dedicated profile file. **This
   is the mechanism the ticket's Scope, Acceptance Criteria, and Related Code Areas actually name.**

Profile files that exist today (14, including `default.yaml`): `default`, `dungeon_crawl`,
`frontier_extended`, `frontier_living_world`, `frontier_marches`, `generated_frontier_3_42`,
`hero_guild_routing`, `highland_traverse`, `sandbox_world`, `simq_routing_test`,
`swamp_border_world`, `unit_information_source`, `unit_selfmodel_pilot`, `urban_political`. Four
worlds have **no** dedicated profile and correctly fall back to `default.yaml` (all flags OFF,
zero `pillar_weights` overrides): `crowded_frontier`, `resource_dense_basin`,
`unit_faction_tension`, `wilderness_survival`. This is documented as intentional in each case (see
table below), not a gap — `FACTION` content (`faction_tension_overrides`) has no `FeatureMode` gate
at all, so a FACTION-only world correctly needs no profile file.

### `FeatureFlagManager` (`src/domains/optimization/feature_flags.py`)

10 flags, all default `FeatureMode.OFF` (`__init__`, lines 10-24). 8 of the 10 gate pipeline
phases (D09 Finding 4): `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_BELIEF_ASSIMILATION`,
`ENABLE_SOCIAL_COOPERATION`, `ENABLE_ADVENTURE_ROUTING`, `ENABLE_COMBAT_ENGAGEMENT`,
`ENABLE_WORLD_EMERGENCE`, `ENABLE_PROGRESSION_EVOLUTION`, `ENABLE_WORLD_CAPABILITY_LAYER`. Only 4
flags actually appear in any profile YAML today: `ENABLE_ADVENTURE_ROUTING`,
`ENABLE_BELIEF_ASSIMILATION`, `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_SOCIAL_COOPERATION` — matching
the ticket's own Scope enumeration exactly (plus the one bonus `ENABLE_SOCIAL_COOPERATION` on
`urban_political`, pre-existing, not part of this ticket's named flag set).

### Pattern 6 content fields and which flags actually gate them

Only **two** of the four Pattern-6 fields (`docs/guidelines/design_patterns.md`) are paired with a
`FeatureMode` flag at all — this is a load-bearing fact for how the test's "inverse direction"
assertion (AC 3) must be written:

- `information_source_profiles` + `pending_information_responses` ↔ `ENABLE_BELIEF_ASSIMILATION`
  (gates `InformationBeliefPhase`'s Branch A query-routing)
- `pending_self_model_information_events` ↔ `ENABLE_SELF_MODEL_COGNITION` (gates
  `SelfModelUpdatePhase`'s assimilation)
- `faction_tension_overrides` has **no** flag gate — `FactionScorer`/tension propagation runs
  unconditionally regardless of any `FeatureMode` flag. A world can seed
  `faction_tension_overrides` with zero profile YAML and zero flags and this is **correct**, not a
  gap (`unit_faction_tension`, `crowded_frontier`'s stress-tier siblings all confirm this).
- `ENABLE_ADVENTURE_ROUTING` has no Pattern-6 content-field counterpart at all — AGENCY activation
  is purely flag + `AdventureDecisionPhase`, no seeded world-content field is required.

Writing the guardrail's inverse-direction check as if all four Pattern-6 fields pair with a flag
would produce false positives on every FACTION-only world (`unit_faction_tension`,
`wilderness_survival`, `dungeon_crawl`'s FACTION content, etc.) — this must not happen.

---

## Mechanics / Engine Constraints

- `docs/engine/known_limitations.md` §1.5 "Feature Flag Defaults (Phase 10 Rollout Gates)" — codifies
  that all 10 flags default OFF, decision recorded in
  `docs/guidelines/intentional_divergences.md` § DEV-002 (`TCK-20260627-P0A-ADVENTURE-FLAG`). This
  is the authoritative source for "OFF is the safe/expected default," which the guardrail test's
  positive assertions (flag ON where content demands it) and negative assertions (flag OFF
  everywhere else) both rest on.
- `docs/simulation/domains/optimization_contract.md` "FeatureFlagManager" section — documents the
  `FeatureMode` enum and rollout semantics (`OFF`/`SHADOW`/`ON`/`STRICT`); confirms `is_enabled()`
  treats only `ON`/`STRICT` as active, `SHADOW` as inert-for-mutation. The guardrail test's
  ON/OFF assertions should use this same `is_enabled()` semantics rather than a raw string compare,
  since a profile could in principle set `SHADOW` (none currently do, but the check should not
  silently mis-treat it as ON).
- `docs/guidelines/design_patterns.md` "Compile-Time Pillar Activation Pattern" (Pattern 6) — the
  four gated fields' shared shape (`WorldSpec`/`WorldCompositionSpec`/`NormalizedWorldComposition`,
  `default_factory=list`/`dict`, resolved by `WorldAssemblyResolver.assemble()`). Confirms these are
  the complete, closed set of four — no undiscovered fifth field follows this shape.
- `docs/simulation_quality/corpus_tier_taxonomy.md` — the authoritative, current (2026-07-07)
  per-world tier classification and the named scale-diversity gaps each stress-tier world fills.
  Used directly to build the expected-state table below and to confirm the 3 stress-tier worlds'
  correct (mostly flag-less) state.

---

## Parity Ledger Overlap

- `INFRA-221` (`docs/parity_ledger/infrastructure.yaml:2581`) — status `verified`, P1. Covers the
  **other** mechanism (`data/content/simulation_scenarios/` scenario-definition flag defaults,
  `TCK-20260627-P2E-FEATURE-FLAG-TEST`). Not this ticket's subsystem; no update needed to this
  entry, but the new test this ticket adds should get its own parity entry (or an
  `INFRA-221`-adjacent new ID) since it covers a materially different mechanism (per-world profile
  YAML, not scenario templates) that was never parity-tracked before.
- `INFRA-256`/`INFRA-257` — `information_source_profiles`/`pending_information_responses`
  compile-time plumbing, status `verified`. Directly relevant: confirms the content side of the
  INFORMATION flag/content pairing this ticket's test checks.
- `INFRA-259`/`INFRA-260` (`infrastructure.yaml:3261`, `:3327`) — both status `verified`, P1/P2.
  **Directly explains the one real content/flag asymmetry this investigation found** (see Risks
  below): confirms `urban_political`'s `pending_self_model_information_events` is seeded but
  `ENABLE_SELF_MODEL_COGNITION` stays OFF in every shipped profile, "never a shipped profile
  default," by design, verified via a test-scoped override rather than a live profile.
- `STRAT-245` (`docs/parity_ledger/strategic_cognition.yaml:2797`) — status `verified`, P2. Documents
  `unit_selfmodel_pilot` as "the first calibration-anchored world to turn
  `ENABLE_SELF_MODEL_COGNITION` ON via a shipped profile" — confirms no other world (including
  `urban_political`) does so, corroborating the INFRA-259/260 finding.
- No P0 entries were found overlapping this ticket's scope — all touched entries are P1/P2, all
  `verified`, all with resolvable `test_path`/`v2_evidence` (spot-checked; no missing test_path
  found among the entries above).

---

## Prior Work

- **`TCK-20260627-P2E-FEATURE-FLAG-TEST`** (done, 2026-06-27) — closed the *scenario-definition*
  half of D09 Finding 4 (`data/content/simulation_scenarios/*.yaml`, 14 scenarios, flags derived
  from the `perspective` field). Confirmed by reading `tests/integration/test_scenario_feature_flag_defaults.py`
  in full: it asserts all 10 flags default OFF for every loaded scenario, and that the
  `hero_guild_perspective` opt-in override mechanism works — it does **not** touch
  `config/simulation_quality/profiles/` at all. Despite closing under the same "P2-E" umbrella
  finding, this ticket is not a duplicate: it is a genuinely separate subsystem
  (scenario-template defaults vs. per-world calibration-profile overrides) that
  `docs/plans/audit_fix_plan.md`'s P2-E section (still marked OPEN as of 2026-07-03, see below)
  never fully closed. This investigation confirms the fold-in ticket's own framing (the epic
  investigation §4 OQ5) was correct to treat this as still-open work.
- **The 9 sibling tickets in this epic** (`AGENCY-FLAG-GENERALIZE`, `UNIT-WORLDS-FACTION-INFO`,
  `UNIT-WORLD-SELFMODEL-PILOT`, `UNIT-WORLD-AGENCY`, `E2E-CONTENT-EXPANSION`, `STRESS-WORLDS`,
  `FACTION-RELATIONSHIPS`, `TAXONOMY-DOC`, `SCALE-METRIC`) — all `done`, read in full via their
  Completion Summary + Files Changed sections. Each independently confirms the exact flag/content
  state recorded in the expected-state table below; no discrepancy found between what a ticket's
  own Completion Summary claims and what the actual repo files (profiles, `world.yaml`) show.
- `tests/unit/worldassembly/test_corpus_diversity.py` — the closest existing precedent for a
  per-world-table-driven test (`ANCHORED_WORLD_BANDS`, `POPULATION_STABILITY_WORLDS`,
  `EXPECTED_DISTINCT_POPULATED_FACTIONS` dicts, module-level, updated additively by every
  corpus-touching ticket in this epic). Good structural precedent for this ticket's own expected-flag
  table (same "module-level dict, one entry per world, parametrized test" shape UQ-1/UQ-2 already
  recommend).

---

## Expected Flag/Content State — actual post-epic ground truth

Built directly from reading every profile YAML's `feature_flags:` block and every `world.yaml`'s
Pattern-6 field values (not from the ticket's own pre-epic Scope table, which does not know the
final new-world names/count). ✓ = present/ON, ✗ = absent/OFF/empty.

| World | Profile file | ADVENTURE_ROUTING | BELIEF_ASSIMILATION | SELF_MODEL_COGNITION | FACTION content | INFO content | SELF-MODEL content | Consistent? |
|---|---|---|---|---|---|---|---|---|
| urban_political | urban_political.yaml | ✗ | ✓ ON | ✗ | ✓ | ✓✓ | ✓ (1 entry) | INFO: yes. **SELF-MODEL: flag OFF, content seeded — see Risks, documented exception (INFRA-259/260)** |
| dungeon_crawl | dungeon_crawl.yaml (weights only) | ✗ | ✗ | ✗ | ✓ | ✗ (documented skip) | ✗ | yes |
| sandbox_world | sandbox_world.yaml | ✗ | ✓ ON | ✗ | ✓ | ✓ | ✗ | yes |
| wilderness_survival | *(default fallback)* | ✗ | ✗ | ✗ | ✓ | ✗ (documented skip) | ✗ | yes |
| highland_traverse | highland_traverse.yaml | ✗ | ✓ ON | ✗ | ✓ | ✓ | ✗ | yes |
| swamp_border_world | swamp_border_world.yaml | ✗ | ✓ ON | ✗ | ✓ | ✓ | ✗ | yes |
| frontier_living_world | frontier_living_world.yaml | ✗ | ✓ ON | ✗ | ✓ | ✓ | ✗ | yes |
| frontier_extended | frontier_extended.yaml | ✗ | ✓ ON | ✗ | ✓ | ✓ | ✗ | yes |
| generated_frontier_3_42 | generated_frontier_3_42.yaml | ✗ | ✓ ON | ✗ | ✓ | ✓ | ✗ | yes |
| simq_routing_test | simq_routing_test.yaml | ✓ ON | ✗ | ✗ | ✗ | ✗ | ✗ | yes (AGENCY needs no content field) |
| unit_faction_tension | *(default fallback)* | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | yes (FACTION unflagged) |
| unit_information_source | unit_information_source.yaml | ✗ | ✓ ON | ✗ | ✗ | ✓ | ✗ | yes |
| unit_selfmodel_pilot | unit_selfmodel_pilot.yaml | ✗ | ✗ (deliberate) | ✓ ON | ✗ | ✗ | ✓ (1 entry) | yes |
| hero_guild_routing | hero_guild_routing.yaml | ✓ ON | ✗ | ✗ | ✗ | ✗ | ✗ | yes (AGENCY needs no content field) |
| crowded_frontier | *(default fallback)* | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | yes (pure scale stress, no gated content) |
| resource_dense_basin | *(default fallback)* | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | yes (pure scale stress, no gated content) |
| frontier_marches | frontier_marches.yaml | ✗ | ✓ ON | ✗ | ✓ | ✓ | ✗ | yes |

**AGENCY-DA anti-drift guard — confirmed holding.** All 9 originally-non-routing worlds
(`urban_political`, `dungeon_crawl`, `sandbox_world`, `wilderness_survival`, `highland_traverse`,
`swamp_border_world`, `frontier_living_world`, `frontier_extended`, `generated_frontier_3_42`) have
`ENABLE_ADVENTURE_ROUTING` OFF/absent, exactly as `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s
anti-drift note requires. Only `simq_routing_test` (pre-existing) and `hero_guild_routing` (new,
ticket 6, purpose-built as a routing-capable unit-tier world with its own new grade anchors) have it
ON — both by deliberate, documented design, not drift.

**Only one real content/flag asymmetry exists corpus-wide**, and it is not new: `urban_political`'s
`pending_self_model_information_events` field has been seeded since before this epic
(`TCK-20260702-SIMQ-UPLIFT2-FACTION`/`-INFORMATION` era), but `ENABLE_SELF_MODEL_COGNITION` has
never been turned ON in any shipped profile for it. This is exactly the class of finding AC 3 (the
inverse-direction check) is designed to catch — but it is not an oversight: `INFRA-259`/`INFRA-260`
(`docs/parity_ledger/infrastructure.yaml`) explicitly document this as intentional ("never a
shipped profile default... confirmed absent from every `config/simulation_quality/profiles/*.yaml`
and `data/worlds/*.yaml`"), and the epic's own investigation (§1, §3) independently arrives at the
same conclusion ("the pending field exists in `urban_political/world.yaml` but is inert without the
flag" — a deliberate "proven but not shipped" state, explicitly flagged as higher-trust-required
before activating for real). **No new misconfiguration was found in this corpus** — see Risks below
for how the guardrail test must handle this one already-documented exception without either (a)
false-failing on it or (b) silently excluding it with no citation.

---

## Risks and Open Questions

1. **The urban_political self-model exception must be an explicit, cited annotation in the test,
   not a silent skip.** If the guardrail test's inverse-direction check (AC 3) is written as a blind
   "content seeded ⇒ flag must be ON" rule, it will correctly flag this pairing and then fail —
   which would be a false alarm against a state that `INFRA-259`/`INFRA-260` already reviewed and
   accepted. The implementer should encode this as one explicit, commented, cited exception (e.g. a
   documented allow-list entry keyed to `urban_political` + `pending_self_model_information_events`,
   citing `INFRA-259`/`INFRA-260`), not by loosening the general rule for every world. This is not an
   open question requiring a human decision — the parity ledger has already made the call — but it
   is a risk if the implementer doesn't notice the asymmetry and instead "fixes" it by turning the
   flag on (a real behavior change, explicitly out of scope per this ticket's own Out-of-Scope
   bullet 2) or by quietly dropping the self-model check for that one world without citation.
2. **The FACTION-has-no-flag and AGENCY-has-no-content-field asymmetries must be built into the
   test's data model from the start**, not discovered as false positives during implementation (see
   Mechanics/Engine Constraints above). A naive "4 Pattern-6 fields × N flags, all must pair" model
   is wrong; the correct model has exactly 2 real content↔flag pairs
   (INFO-content↔`ENABLE_BELIEF_ASSIMILATION`, self-model-content↔`ENABLE_SELF_MODEL_COGNITION`)
   plus 2 unpaired items (`faction_tension_overrides` — content with no flag;
   `ENABLE_ADVENTURE_ROUTING` — flag with no content field).
3. **World count (17) exceeds UQ-2's own 15-world fixture-file threshold.** The ticket's Assumptions
   section defaults to hardcoding the expected-state table in the test file unless the corpus
   exceeds 15 worlds, "in which case a fixture file is preferable." The actual corpus is now 17
   worlds — past that threshold — so per the ticket's own stated default, a small fixture file
   (mirroring `tests/simulation_quality/fixtures/grade_anchors.json`'s existing precedent and
   location convention) is the better choice, not a fresh judgment call.
4. **No P0 parity entries are touched by this work** — confirmed above; this lowers the urgency
   bar somewhat (no `test_path` is contractually required to keep a P0 green), but AC 5 ("test
   passes against actual corpus state") is still a hard gate regardless.
5. No open question in this investigation requires a human decision before implementation can
   proceed — the one substantive judgment call (§1 above, the urban_political exception) already has
   a settled, cited, parity-verified answer; it only needs to be encoded correctly in the new test,
   not decided anew.

---

## Anti-Drift Hazards

- **Do not silently drop worlds that lack a dedicated profile file** (`crowded_frontier`,
  `resource_dense_basin`, `unit_faction_tension`, `wilderness_survival`) from the test matrix — AC 2
  requires covering "every world's profile YAML (or `default.yaml` fallback)"; these four are
  correct, intentional `default.yaml` fallback cases and must still appear as explicit rows
  asserting all-flags-OFF, not be skipped because "there's no profile to load."
- **Do not treat `faction_tension_overrides` as needing a paired flag.** It has none. A test that
  expects e.g. `unit_faction_tension` to have some flag ON because it has FACTION content would be
  wrong and would either false-fail or force an incorrect flag to be added to that world's (currently
  correctly absent) profile.
- **Do not re-litigate the AGENCY-DA decision.** This ticket's job is to encode the *current*,
  already-decided expected state (9 pre-existing worlds OFF, 2 routing worlds ON) as a regression
  guard — not to argue for or against flipping any additional world's `ENABLE_ADVENTURE_ROUTING`.
- **Do not touch `FeatureMode`, `feature_flags.py`, any phase gate, or turn any flag ON/OFF in any
  profile YAML** — explicitly Out of Scope. The one tempting exception (urban_political's
  self-model asymmetry) must be handled as a documented test exception, not "fixed" by flipping the
  flag.
- **Do not scope the test only to the worlds named in the ticket's own Scope section's example
  list.** That list was accurate when written but is not exhaustive against the actual post-epic
  corpus (e.g. it doesn't name `frontier_marches`, `crowded_frontier`, `resource_dense_basin` by
  their final names, and undercounts total worlds). AC 2 is explicit that all worlds added by
  tickets 4/5/6/8 must be covered — verified above to be 7 new worlds
  (`unit_faction_tension`, `unit_information_source`, `unit_selfmodel_pilot`, `hero_guild_routing`,
  `crowded_frontier`, `resource_dense_basin`, `frontier_marches`), all present in the expected-state
  table above.
- **Do not conflate this ticket's new test with `tests/integration/test_scenario_feature_flag_defaults.py`.**
  They test different files, different mechanisms, and different flag-application code paths
  (`_load_profile_feature_flags()` vs. `perspective`-derived scenario defaults). Extending the
  existing file to also cover profiles would conflate two independently-parity-tracked subsystems
  (`INFRA-221` vs. this ticket's new entry) under one test file/ID — keep them separate files.
