---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS
artifact_type: investigation
tags: [simulation-quality, corpus, calibration, agency, faction, cognition, stasis]
---

# Investigation — TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS

## Current Behavior

### Anchor mechanism (data-only, no code path change needed)
- `tools/calibrate_simq.py` (`/home/u24desktop/Working/rpg-based-simulation/tools/calibrate_simq.py`)
  runs the kernel for N ticks against a named world (`_load_world_state`, line 108), replays
  `simulation_events.jsonl` through `QualityHub` (`_replay_jsonl_through_hub`, line 257), and writes
  `data/calibration/{name}_seed{seed}_{ticks}t/quality_report.json`. Profile resolution
  (`_resolve_profile`, line 32) defaults to `config/simulation_quality/profiles/{name}.yaml` if it
  exists, else `default.yaml`.
- `tests/simulation_quality/test_grade_regression.py` has two disjoint key lists:
  `FAST_ANCHOR_KEYS` (line 41, run in the standard/non-slow suite) and `SLOW_ANCHOR_KEYS` (line 102,
  `@pytest.mark.slow`, currently 11 entries: `dungeon_crawl`×3 seeds×{1000t,2000t}=6,
  `sandbox_world`×{1000t,2000t}=2, `urban_political`×3 seeds×1000t=3). Both parametrized tests
  (`test_grade_within_anchor_band` line 172, `test_grade_within_anchor_band_long_run` line 208) share
  identical body logic — `pytest.skip` if no anchor entry or no calibration report exists, else
  assert each pillar grade is within ±1 `GRADE_ORDER` band of the committed anchor
  (`_within_band`, line 127). No 2000t-specific test function exists — 2000t keys already live in
  `SLOW_ANCHOR_KEYS` alongside 1000t keys (`dungeon_crawl_seed*_2000t`, `sandbox_world_seed42_2000t`
  are already present), so this ticket's new 2000t keys need no new test function, only new
  `grade_anchors.json` entries + `SLOW_ANCHOR_KEYS` string additions.
- `tests/simulation_quality/fixtures/grade_anchors.json` currently has 61 non-metadata keys (verified
  by direct load, not the stale "25 entries" figure recorded in `INFRA-250`/`INFRA-252` — see Risks).
- `tools/evaluate_simq.py` (line 103) iterates **every** key in `grade_anchors.json` (`anchor_keys =
  [k for k in all_anchors if not k.startswith("_")]`, line 121) — it does **not** filter to
  fast-only keys. `make evaluate` (`--dry-run`) reads existing `data/calibration/` reports without
  re-running the engine; `make evaluate-full` (no `--dry-run`) re-runs `calibrate_simq.py` for
  **every** anchored scenario, including all 1000t/2000t ones already committed. This means the AC's
  "`make evaluate-full` confirms 0 regressions on the rest of the corpus" will re-simulate the full
  ~61-entry corpus (up to 2000 ticks for several), not just the 5 fast-scenario worlds the Makefile
  comment ("Re-run engine for all fast (≤500t) scenarios") implies — the comment is stale relative to
  the actual code (see Anti-Drift Hazards).

### Current data for the 5 target worlds (verified directly against `grade_anchors.json`, 2026-07-08)
- `unit_selfmodel_pilot` (16 entities, 1 region; `config/simulation_quality/profiles/
  unit_selfmodel_pilot.yaml` sets `ENABLE_SELF_MODEL_COGNITION: "ON"`): COGNITION=S at 200t (all 3
  seeds). No anchor exists past 200t.
- `unit_faction_tension` (18 entities, 3 regions, `data/worlds/unit_faction_tension/world.yaml`
  seeds `faction_tension_overrides: {town_council: 0.5, merchant_league: 0.5}`): FACTION=S at 200t
  (all 3 seeds). **No profile YAML exists** at `config/simulation_quality/profiles/
  unit_faction_tension.yaml` — `_resolve_profile` falls back to `default.yaml`, so all feature flags
  default OFF for this world today (confirmed by direct file-existence check and by
  `INFRA-262`'s fixture, which lists `unit_faction_tension` among the `default.yaml`-fallback
  worlds). This directly answers Scope item 3's live-verification requirement: the FACTION=S grade
  at 200t is generated with **no** dedicated profile.
- `hero_guild_routing` (31 entities, 4 regions; `config/simulation_quality/profiles/
  hero_guild_routing.yaml` sets `ENABLE_ADVENTURE_ROUTING: "ON"`): AGENCY=A, COGNITION=A/S,
  NARRATIVE=S at 500t (all 3 seeds). No anchor exists past 500t.
- `simq_routing_test` (`config/simulation_quality/profiles/simq_routing_test.yaml` sets
  `ENABLE_ADVENTURE_ROUTING: "ON"`): AGENCY=A, COGNITION=A/S, NARRATIVE=S/A at 500t (all 3 seeds). No
  anchor exists past 500t.
- `urban_political`: SOCIAL=S holds at both 500t and 1000t (all 3 seeds). No 2000t anchor exists.
- `dungeon_crawl` (existing `SLOW_ANCHOR_KEYS`, out of scope for new anchors but directly relevant to
  the FACTION-decay hypothesis): FACTION=A at 1000t (all 3 seeds) → FACTION=B at 2000t (all 3 seeds).
  This transition is exact and already committed — verified directly against `grade_anchors.json`,
  not assumed from the (currently-missing) epic investigation doc.

### Ticket's own quantitative claims — independently re-verified against `grade_anchors.json`
Because `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` — the doc this
ticket's Request Summary and Related Docs cite for its evidence table — **does not exist anywhere in
the working tree or git history** (confirmed: `git log --all --diff-filter=A --name-only | grep -i
deep-coverage` finds only the ticket/SEQUENCE files, never an `investigation.md`; this is the exact
citation-rot pattern `TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING` was closed to prevent, and it
has recurred one epic later), every specific factual claim in this ticket's Request Summary was
re-derived directly from `grade_anchors.json` rather than trusted from citation:
- "AGENCY = C×11, COMBAT = B×11, PROGRESSION = B×11, WORLD = B×11" across all 11
  `SLOW_ANCHOR_KEYS` — **confirmed exactly** (dungeon_crawl 6/6, sandbox_world 2/2, urban_political
  3/3, all four pillars, no exceptions).
- AGENCY reaching A in `simq_routing_test`/`hero_guild_routing` at 500t — **confirmed** (all 6
  seed-runs across both worlds).
- COGNITION reaching S in `unit_selfmodel_pilot` at 200t — **confirmed** (all 3 seeds).
- NARRATIVE reaching S in `hero_guild_routing`/`simq_routing_test` at 500t — **confirmed** for
  `hero_guild_routing` (3/3 seeds S) and 2/3 seeds for `simq_routing_test` (seed456 is A, not S).
- FACTION reaching S in `unit_faction_tension` at 200t plus "6 other 200t worlds" — the
  `unit_faction_tension` claim is confirmed, but the count of *other* worlds reaching FACTION=S at
  200t is **undercounted**: direct enumeration finds 9 other worlds (`frontier_extended`,
  `frontier_living_world`, `frontier_marches`, `highland_traverse`, `sandbox_world`,
  `swamp_border_world`, `urban_political` (seed42 only), `wilderness_survival`, `dungeon_crawl`
  (seed42 only)), not 6. This is a minor documentation-accuracy gap in the ticket's own Request
  Summary, not a scope-affecting error — flagged in Risks, not blocking.
- The `dungeon_crawl` FACTION A→B(1000t→2000t) decay claim — **confirmed exactly** (see above).
- `urban_political` SOCIAL holding S through 1000t with no 2000t anchor — **confirmed**.

## Mechanics / Engine Constraints
- `docs/simulation_quality/quality_scoring_contract.md` §4.4 (Normalized Score, lines 268–297,
  parity entry `INFRA-255`): `floor_tick = max(1, current_tick // 4)`;
  `effective_denom = max(floor_tick, last_event_tick)` if the pillar has ever scored an event, else
  `current_tick`; `normalized_score = raw_score / effective_denom`. This is the exact mechanism the
  ticket's FACTION hypothesis rests on: if a pillar's events cluster early (e.g., diplomatic
  transitions settle by tick ~300) and `last_event_tick` stays fixed while `current_tick` (and
  therefore `floor_tick`) keeps growing, `normalized_score` shrinks purely from denominator growth,
  with `raw_score` unchanged — this is architecturally intentional (not a bug) per the contract's own
  rationale note (lines 286–297, `TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY`).
- §5 AGENCY & ACTION (lines 564–610): `stasis_N` penalty is a **one-shot capped escalation** at the
  tick a per-entity DEFER streak first crosses `gate + cap` (streak=10) — not a repeating penalty
  (contract explicitly warns "tag-presence does not imply a repeating penalty", matching the
  `INFRA-237` divergence_note's 2026-07-04 fix). `population_stasis` (−25) fires on zero non-DEFER
  actions population-wide for 20 ticks. Both are legitimate long-run AGENCY-decay mechanisms distinct
  from `effective_denom` dilution — a genuine drift signal in `hero_guild_routing`/
  `simq_routing_test` at 1000t could come from either mechanism, and this ticket's `eval_matrix_
  results.md` write-up (Scope item 5) must distinguish which one (if either) explains any observed
  AGENCY decay, not attribute all decay to normalization by default.
- §5 COGNITION (lines 529–564): `belief_system_dormant` (−15, zero belief updates population-wide in
  a 100-tick window) and `goal_lock_no_cognition` (−2/tick, same goal re-selected >5 consecutive
  ticks with no cognition update) are the two plausible long-run COGNITION-decay mechanisms for
  `unit_selfmodel_pilot` — if `self_model_updated`/`belief_updated` events are front-loaded (world
  init) rather than sustained, 1000t exposes both risks that 200t cannot.
- §5 FACTION & MILITARY (lines 649–690): `diplomacy_dormant` (−20, zero diplomatic transitions over
  200 ticks), `faction_monopoly` (−15, single faction >80% territory by tick 500), and
  `tension_oscillation` (−5, cyclic non-crossing tension) are the genuine-regression mechanisms to
  distinguish from `effective_denom` dilution for `unit_faction_tension` at 1000t/2000t.
- Engine contract: no specific `docs/engine/` contract directly constrains this ticket — it adds
  calibration data only, touches no `authoritative_pipeline.md` phase logic.

## Parity Ledger Overlap
All entries below are in `docs/parity_ledger/infrastructure.yaml`, `status: verified`, and describe
scorer/harness behavior this ticket exercises but does not modify:
- `INFRA-237` (AGENCY & ACTION scorer coverage) — its `support_boundary` field currently states
  AGENCY=C is "archetype-correct" everywhere except `simq_routing_test`/`hero_guild_routing`, and
  cites `hero_guild_routing`'s AGENCY=A "at all 3 measured seeds (42/123/456, 500t)" as the full
  evidence set. **Needs updating** once 1000t data exists, to state whether A holds, decays, or
  reveals a `stasis_N`/`population_stasis` bug at long run.
- `INFRA-240` (COGNITION scorer coverage) — no long-run evidence cited yet for `unit_selfmodel_pilot`;
  should gain a v2_evidence note once this ticket's 1000t anchor lands.
- `INFRA-241` (FACTION scorer coverage) — same gap for `unit_faction_tension`.
- `INFRA-255` (normalized_score / `effective_denom` formula) — this ticket's data either reinforces
  or complicates the existing rationale note; if `unit_faction_tension`'s S-grade decays purely via
  denominator growth (matching the already-documented `dungeon_crawl` A→B pattern), this entry's
  text should cite it as a second confirming data point.
- `INFRA-250` (full SimQ test suite / anchor counts) — text says "25 run keys committed... (14 fast
  ≤500t, 11 slow ≥1000t)". This is **already stale** (actual count today is 61 non-metadata keys,
  `FAST_ANCHOR_KEYS` alone has ~48 entries) — predates several corpus-expansion tickets. This
  ticket's 6 new anchors make it staler still. **Flag for parity-updater**, though fixing the
  pre-existing staleness is not this ticket's Scope (only its own additions are).
- `INFRA-252` (evaluate_simq.py standing harness) — text says "full mode re-runs calibrate_simq.py
  for all fast anchor scenarios," but the actual code (`tools/evaluate_simq.py` line 121-126) re-runs
  **every** anchor key with no fast/slow filter. This is a pre-existing doc/code mismatch, not
  introduced by this ticket, but this ticket's AC directly depends on `make evaluate-full`'s actual
  (not documented) behavior — worth a corrective note in the same parity-update pass.
- `INFRA-262` (per-world calibration-profile feature-flag guardrail, `test_path:
  tests/integration/test_world_profile_feature_flag_guardrail.py`) — its fixture
  (`expected_world_flag_state.json`) already lists `unit_faction_tension` among the
  `default.yaml`-fallback worlds with **zero** feature flags expected ON. If Scope item 3's live
  verification confirms no profile is needed (which the current file-existence check already
  suggests), this guardrail's fixture needs **no change** — but if a profile is added, this fixture
  must be updated in the same session or the guardrail will fail.

No `P0` parity entries were found overlapping this ticket's scope — all touched entries are `P1`,
`status: verified`. This ticket adds calibration evidence; it does not need any entry's `status` to
change (unless Scope item 5 discovers a genuine bug, in which case a new entry, or a `divergent`
status flip, would be needed — but per the ticket's own scope, that's documented and escalated, not
resolved here).

## Prior Work
- `stored_artifacts/TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP/`,
  `stored_artifacts/TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP/`,
  `stored_artifacts/TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT/` — all landed
  (confirmed present in `tickets/done/`); resource-tag/hometown gaps in the two worlds this ticket
  directly anchors are closed.
- `stored_artifacts/TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP/` — landed, but its
  Implementation Notes disclose a **directly relevant, still-open finding**: `urban_political` fails
  `test_population_stability`'s 60%-alive floor at tick 300 (56.7% alive, seed 42) — a genuine,
  unfixed population-erosion defect, escalated (not fixed) to a new ticket,
  `tickets/todos/TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE.md` (standard, P1, OPEN, filed
  2026-07-08 — **not** one of this ticket's 4 listed hard-dependency tickets, because it did not
  exist when this ticket was scoped). See Risks — this is a live threat to the interpretability of
  this ticket's `urban_political` 2000t SOCIAL-persistence hypothesis.
- `tickets/done/TCK-20260702-SIMQ-ANCHORS`, `TCK-20260702-SIMQ-EVAL-MATRIX`,
  `TCK-20260702-SIMQ-EVAL-HARNESS` — established the exact calibrate → commit-fixture →
  add-to-SLOW_ANCHOR_KEYS mechanism this ticket reuses verbatim, and the `evaluate_simq.py`/
  `test_grade_regression.py` machinery this ticket's AC gates on.
- `docs/simulation_quality/eval_matrix_results.md` — the living results doc with an established
  per-world table convention (`| Pillar | seed42 | seed123 | seed456 | Stable? | Note |`) and an
  explicit "supersede, don't rewrite" convention for updated grades (see its
  "FACTION/INFORMATION Content Expansion" section, which documents the exact `dungeon_crawl`
  FACTION C→A(500/1000t)→B(2000t) trajectory this ticket's Hypothesis 2 write-up should extend, not
  duplicate).
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT/` — precedent for the
  "file a follow-up, don't fix in-ticket" pattern this ticket's own Scope item 5 mirrors when a
  genuine bug is found (cited directly in this ticket already).

## Risks and Open Questions
1. **BLOCKING for the Plan phase — `urban_political` population-erosion confound.** This ticket's
   Hypothesis 4 (does `urban_political`'s SOCIAL=S persist to 2000t) will be run against a world with
   a documented, unfixed population-erosion defect (56.7% alive by tick 300, seed 42, per
   `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`, currently OPEN and not a prerequisite of this
   ticket). If population keeps eroding gradually through 2000t, any SOCIAL grade decay observed
   could be attributable to entity-count attrition (fewer live entities → fewer social events)
   rather than a genuine SOCIAL-pillar mechanism or `effective_denom` dilution — a third confound
   this ticket's own Scope item 5 framing (drift bug vs. normalization) does not anticipate. This
   ticket's Plan phase must explicitly decide: (a) proceed and document the confound honestly
   alongside the SOCIAL result, (b) wait for the collapse ticket to land first, or (c) escalate. Do
   not silently attribute a SOCIAL decay to normalization or to a "genuine drift bug" without ruling
   out population erosion first — check entity/alive counts in the 2000t `world_compile_report.json`-
   equivalent run telemetry alongside the grade.
2. **Missing epic investigation.md (non-blocking but must be logged).** As documented above under
   Current Behavior, `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` does
   not exist despite being cited as this ticket's primary evidentiary source and despite
   `TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING` having just closed on the premise that this
   citation-rot pattern was being prevented going forward. Every specific claim has now been
   independently re-verified against `grade_anchors.json` (see Current Behavior) and checks out
   except the minor "6 other worlds" undercount. Recommend a lightweight follow-up note (not a new
   ticket — low severity, already worked around) when this ticket documents its own investigation
   artifacts to `stored_artifacts/`, so the pattern doesn't reset silently a third time.
3. **`unit_faction_tension` at 1000t/2000t is genuinely new territory.** Its FACTION=S grade has only
   ever been observed at 200t on an 18-entity, 3-region world seeded via `frontier_village_core` +
   `wolf_den_near_forest` (the same module pair as `sandbox_world`, "already proven population-stable
   to 2000 ticks" per its own `world.yaml` description) — this is a reassuring population-stability
   signal (unlike `urban_political`), but the FACTION-specific long-run behavior (diplomatic
   transitions settling early vs. sustained) is untested. Scope item 3's "verify live" instruction
   is the correct guard here — do not assume `default.yaml` suffices without running data.
4. **Cost consideration for `make evaluate-full`.** Per Current Behavior, `evaluate_simq.py` re-runs
   the **entire** anchor corpus (all ~61+67 keys once this ticket lands), including every existing
   1000t/2000t scenario, not just this ticket's new keys. The Plan phase should account for this
   runtime cost explicitly (multiple 1000-2000-tick kernel runs) when scoping the AC verification
   step, and should not assume `--scenario`-scoped runs during development substitute for the final
   full-corpus AC check.

## Anti-Drift Hazards
- **Do not touch `src/simulation_quality/scorers/*.py`.** The ticket's own Related Code Areas list
  marks agency.py/cognition.py/faction.py/social.py "not modified, only exercised" — any temptation
  to "fix" a decay pattern found during this ticket's data collection (e.g., adjusting a threshold or
  a `stasis_N` cap) must instead become a follow-up ticket per Scope item 5, exactly like
  `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`'s established precedent.
- **Do not conflate `urban_political`'s population-collapse defect with a SimQ scoring bug.** The
  collapse is a world-content/engine-balance issue (per `TCK-20260708-DUNGEON-URBAN-POPULATION-
  COLLAPSE`'s own scope, likely combat/economy attrition, not a SimQ scorer defect) — any SOCIAL
  decay this ticket observes at 2000t must be triaged against that ticket's root cause before being
  filed as a new SimQ-side follow-up, to avoid duplicate/misattributed tickets.
- **Do not silently under-sample.** Per the ticket's own Assumptions/Open Questions, if the Plan
  phase chooses fewer than 3 seeds per new world/tick combination (departing from the
  `dungeon_crawl`/`urban_political` 3-seed convention), the cost/coverage trade-off must be stated
  explicitly in `plan.md`, not left implicit.
- **Do not exceed the 2000-tick cap.** Explicitly out of scope per both this ticket and its parent
  `SEQUENCE.md` — a 5000t+ tier is a distinct future decision.
- **Do not modify `FAST_ANCHOR_KEYS`.** All of this ticket's new keys are 1000t/2000t and belong
  exclusively in `SLOW_ANCHOR_KEYS`; adding any of the 4 target worlds' new long-run keys to the fast
  list would pull multi-thousand-tick runs into the default (non-`-m slow`) test suite, breaking the
  fast/slow CI split.
- **Do not create `unit_faction_tension.yaml`'s profile speculatively.** Per Scope item 3 and the
  ticket's explicit Out-of-Scope line, only create it if live verification at 1000t/2000t proves
  `default.yaml` insufficient — creating it "just in case" would be undocumented scope creep and
  would also require updating `INFRA-262`'s `expected_world_flag_state.json` fixture.
