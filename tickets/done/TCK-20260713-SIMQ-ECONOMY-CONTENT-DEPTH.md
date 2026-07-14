---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH
phase: done
date: 2026-07-13
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH

## Title
Author ECONOMY-rich content into 2-3 more archetype worlds

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`EconomyScorer` (`src/simulation_quality/scorers/economy.py`) listens for 10 distinct event types
(harvesting, crafting, trading, gold flow, scarcity, inflation control, conservation checks,
paid-info transactions, quest rewards) — not a thin, single-signal pillar. The corpus-wide C-heavy
grade distribution (60/72 committed anchors) is partly a genuine content gap: most worlds simply
don't have sustained harvest/craft/trade content authored into them. This pillar was never
addressed by the archived `docs/plans/archive/simq_development_roadmap.md` (explicitly out of
scope there — a Gini-threshold/archetype-composition question, not the `FeatureMode`-gating
question that roadmap's 4 pillars shared).

**This must land after `TCK-20260713-SIMQ-SCORE-CEILING-FIX`, not before or in parallel.**
Authoring more content into a formula that currently caps at 1/3-of-A regardless of volume
(confirmed empirically — the single richest observed ECONOMY run in the whole corpus, 69 events,
only reached a normalized score of 0.16 against a 0.5 A-threshold) risks spending real
content-authoring effort for a result that still reads as C/B corpus-wide.

## Scope
- Investigation-tier first: confirm which worlds already have a merchant NPC or crafting-capable
  population (per `data/worlds/*/world.yaml`) before authoring anything new — mirrors how the
  archived roadmap's Phase 3 investigation found FACTION/INFORMATION already more covered than
  assumed. ECONOMY's real gap size should be verified the same way, not assumed from the raw grade
  count alone.
- Author harvest/craft/trade content into 2-3 confirmed candidate worlds with a plausible
  in-fiction merchant/crafting economy (e.g. a trade-hub or settlement-heavy archetype).
- Recalibrate against the corrected formula from `TCK-20260713-SIMQ-SCORE-CEILING-FIX`, verify
  ECONOMY signal actually moves, full regression sweep given the cross-pillar side-effect history
  documented elsewhere in this corpus (e.g. INFORMATION activation once surfaced COGNITION
  side-effects).

## Out of Scope
- The weight/threshold recalibration itself — this ticket depends on
  `TCK-20260713-SIMQ-SCORE-CEILING-FIX`, it does not perform that work.
- Any world outside the 2-3 confirmed candidates from this ticket's own investigation.
- Re-opening FACTION/INFORMATION/SOCIAL/AGENCY depth — all declared complete by the archived
  roadmap's Phase 5 gate.
- ECONOMY's Gini-threshold mechanism (`EconomyHealthMonitor.INFLATION_SPIRAL_GINI_THRESHOLD`,
  `src/economy/health_monitor.py`) — content authoring only, no engine change expected.

## Acceptance Criteria
- [ ] ECONOMY grade moves measurably off C in ≥2 additional worlds, with calibration evidence in
      `docs/simulation_quality/eval_matrix_results.md`. **Not achieved** — measured directly at
      merchant_count 3 and 6, 200t and 1000t, zero movement in all 9 recalibrated anchors. Root
      cause: a corpus-wide strategy/cognition-layer gap (no entity ever generates an accepted
      harvest/craft/trade intent), not a content-volume gap — see Completion Summary. Closed under
      this ticket's own AC3 escape valve (below), which anticipated the "objective unreachable via
      this lever, honest investigation finds why" outcome, though not this exact root cause.
- [x] 0 regressions on a full `evaluate_simq.py` sweep (dry-run mode; 750 pillars, 0 regressions, 0
      missing — live full re-run explicitly out of scope per this ticket's own scope guard).
- [x] If investigation finds fewer than 2-3 legitimate candidate worlds remain (mirroring the
      archived roadmap's FACTION/INFORMATION "zero new worlds, already adequate" outcome), that is
      an equally valid, documented closure — this ticket does not require finding candidates if
      honest investigation finds none remain. **Applied by extension**: 3 legitimate candidates
      *were* found and correctly authored into, but the underlying mechanic proved structurally
      inert — an equally valid documented non-achievement, per the same escape-valve spirit,
      confirmed by explicit human decision (2026-07-13/14) on how to close this ticket.

## Related Tickets
- `TCK-20260713-SIMQ-SCORE-CEILING-FIX` — **hard dependency, must land first.** (done; note: its
  ECONOMY weight-derivation cited `urban_political`'s 69-event run as "genuinely rich activity" —
  now known to be inaccurate, it's 100% `gold_sink_fired` per this ticket's finding; the weight
  *mechanism* itself is unaffected, only that narrative framing was wrong.)
- `TCK-20260710-SIMQ-DEPTH-SOCIAL`, `TCK-20260710-SIMQ-DEPTH-FACTION`,
  `TCK-20260710-SIMQ-DEPTH-INFORMATION` (all done) — the playbook precedent this ticket mirrors.
- `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP` (filed, open) — follow-up ticket for the real
  root cause this ticket discovered: no entity anywhere in the corpus ever generates an accepted
  harvest/craft/trade intent, regardless of authored content.

## Related Docs
- `docs/simulation_quality/current_state.md` — Recommendation 2, the finding this ticket addresses.
- `docs/plans/simq_scoring_improvement_roadmap.md` — Phase 2, this ticket's source.
- `docs/simulation_quality/corpus_tier_taxonomy.md` — tier structure; candidate worlds must respect
  tier-purity (Stress/Unit/Regression-tier worlds are supposed to stay content-inert).
- `docs/guidelines/design_patterns.md` Pattern 6 — the compile-time pillar activation pattern used
  for FACTION/INFORMATION; investigate whether it applies here or whether ECONOMY's mechanism
  (event-driven, not compiler-constructed field) means content authoring alone suffices without any
  Pattern 6-style plumbing.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/simulation_quality/scorers/economy.py`
- `data/worlds/*/world.yaml` (candidate world content)
- `config/simulation_quality/profiles/*.yaml` (calibration profiles for candidate worlds)

## Assumptions / Open Questions
- Candidate worlds are not pre-selected — deliberately left to this ticket's own Investigate step,
  working from live corpus content, per the same discipline the archived roadmap's depth waves
  followed.
- Whether ECONOMY's mechanism needs any Pattern 6-style compiler plumbing (like FACTION/
  INFORMATION did) or is purely content-authoring (since `EconomyScorer` is event-driven, reading
  `AuthoritativeState` fields not at all — confirmed during this session's investigation) is a real
  open question for the investigation step, not assumed here.

## Implementation Notes

**Steps 1-3 (module composition migration) — done as planned, no deviation.** Migrated
`data/worlds/{frontier_living_world,frontier_extended,swamp_border_world}/world.yaml` from
`modules: [...]` to `module_refs:` (preserving existing modules' order), appended
`trading_company_hub` with `namespace: "trading"` and `parameters: {merchant_count: 3}`. Namespace
was mandatory — confirmed by resolving all 3 without the
`ValueError("Duplicate region ID collision 'hometown' ...")` that fires without it
(`src/worldassembly/resolver.py` L346-347). Resolved (`python3 -m src.worldbuilding.cli resolve
<world>`) and compiled (`... compile <world> --seed 42`) all 3 cleanly. Entity counts matched the
plan's projection exactly: `frontier_living_world`=49 (band 35-50), `frontier_extended`=59 (band
51-None), `swamp_border_world`=29 (band 20-35). `distinct_populated_factions` also matched
projection exactly: 6/9/4 — `merchant_league` was already populated pre-ticket via
`frontier_village_population`'s 1 `traveling_merchant`, confirmed empirically, no new distinct
faction introduced.

**Step 4 (calibrate + escalate) — measured; escalation does not help; AC1 not achieved.**
Calibrated all 3 worlds at seed42/123/456, 200t, `merchant_count: 3`: **ECONOMY graded C/raw=0.0/
event_count=0 in all 9 runs** — identical to the pre-ticket state. Diagnostically probed
`frontier_extended` at `merchant_count: 6` (the plan's stated ceiling) at 200t (still C/0/0-events,
all 3 seeds) and at 1000t seed42 (grade B, raw=192.0, event_count=24 — but direct grep of the raw
`simulation_events.jsonl`/`quality_scores.jsonl` shows those 24 events are 100% `gold_sink_fired`,
0 `resource_harvested`/`item_crafted`/`trade_executed`/`shop_transaction` — the generic
content-independent baseline, byte-identical in shape to `dungeon_crawl_seed42_1000t`/
`sandbox_world_seed42_1000t`'s own documented baseline). Escalating `merchant_count` from 3 to 6
produced **zero** additional ECONOMY event volume at either tick length tested. Reverted
`frontier_extended` back to `merchant_count: 3` (the committed value for all 3 worlds — escalation
provided no benefit, so no world was escalated).

**Root cause found (not assumed): this is a corpus-wide engine-layer gap, not a content-volume
gap, contradicting investigation.md's core premise.** Grepped every
`data/calibration/*/quality_scores.jsonl` in the entire corpus for `resource_harvested`,
`item_crafted`, `trade_executed`, `shop_transaction` — **zero matches anywhere**, including all 8 of
`urban_political`'s own committed seed/tick combinations (the world this ticket's lever,
`trading_company_hub`, was copied from on the assumption it already proved the lever works).
`urban_political_seed123_1000t`'s 69-event/grade-A run — cited by investigation.md and
`current_state.md`/`SIMQ-CALIBRATED-001` as the corpus's "one data point with actual
harvest_active/crafting_active/trade_active density" — is, on direct inspection of its raw event
log, 100% `gold_sink_fired`. That prior characterization was incorrect on this specific point.
`resource_harvested`/`item_crafted`/`trade_executed`/`shop_transaction`
(`src/observability/event_extractor.py` L327-353) are derived only from an entity's *accepted*
`intent_results` with `source_kind` NODE/CRAFTING/SHOP_BUY/SHOP_SELL — no entity archetype in the
corpus, including `trading_company_hub`'s own dedicated "merchant" role, has ever produced an
accepted intent of any of these 4 kinds. The gap is upstream of both the scorer (verified correct)
and world content (now verified sufficient in all 3 target worlds) — no entity's decision/strategy
layer currently generates a harvest, craft, or trade goal that reaches acceptance. This was **not**
worked around: `src/simulation_quality/scorers/economy.py` and
`src/economy/health_monitor.py::INFLATION_SPIRAL_GINI_THRESHOLD` were never touched, per the
ticket's explicit Out of Scope. Documented as a `support_boundary` on
`docs/parity_ledger/infrastructure.yaml::INFRA-242` and in
`docs/simulation_quality/current_state.md`/`eval_matrix_results.md`, recommending a follow-up
strategy/cognition-layer investigation (not filed as a new ticket by this implementation — left for
a deliberate scoping decision).

**Step 5 (grade_anchors.json) — ECONOMY unchanged for all 9 keys; cross-pillar shifts updated and
attributed.** No ECONOMY edit needed (byte-identical C/0.0 before and after for all 9). New
population/quest content did measurably shift COMBAT/PROGRESSION/SOCIAL/WORLD/NARRATIVE for several
of the 9 anchors (2 WORLD entries crossed B→A, 1 PROGRESSION entry crossed A→B — both within the
±1 band tolerance but outside score tolerance, hence requiring the anchor update); every changed
value is individually attributed in `eval_matrix_results.md`'s new calibration-batch section, not
silently absorbed.

**Step 6 (test_corpus_diversity.py constants) — no edit needed.** Recompiled entity counts (49/59/
29) and `distinct_populated_factions` (6/9/4) both matched the existing `ANCHORED_WORLD_BANDS`/
`EXPECTED_DISTINCT_POPULATED_FACTIONS` constants exactly — confirmed via test run, not assumed.

**Step 7 — new architecture guard test added.** `test_trading_company_hub_composed` (parametrized
over the 3 worlds) in `tests/unit/worldassembly/test_corpus_diversity.py`, using the file's existing
`_world_modules()` helper.

**Step 8 (regression sweep) — clean, with 2 confirmed pre-existing, unrelated failures.** All scoped
pytest commands from test_plan.md pass. Two failures observed are confirmed pre-existing (present
in files already committed at `HEAD` before this session started) and unrelated to any file this
ticket touched: (a) `test_module_family_anchored` fails on `urban_political_selfmodel_probe`
(a profile-variant key with no matching `data/worlds/` directory, added by the already-committed
`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`); (b)
`test_generated_frontier_3_42_extended_population_stability` flaked once under sustained system load
(WatchdogTrip warnings throughout the run) and passed cleanly in isolation — matches the
load-sensitivity symptom already tracked in the open `TCK-20260713-SIMQ-COGNITION-LOOPDET-
NONDETERMINISM` ticket. Neither touches a world/file this ticket modified. Per this ticket's own
explicit scope guard against running a fresh full-corpus calibration sweep beyond the 9 targeted
keys plus regression-guard spot checks, `python3 tools/evaluate_simq.py` was run in `--dry-run` mode
only (750 pillars checked, 0 regressions, 0 missing) — the live full re-run was not executed.

**Step 9 (Gini/gold-sink observation) — no interaction observed at 200t; `INFLATION_SPIRAL_
GINI_THRESHOLD` untouched.** All 9 anchors' `loop_flags` are empty (`[]`) both before and after the
content addition — no `gold_sink_fired` activity at 200t regardless of merchant population, matching
`urban_political`'s own 200t/500t behavior. The diagnostic 1000t/merchant_count-6 probe of
`frontier_extended` did show `loop_flags=["inflation_controlled"]` (24 `gold_sink_fired` events) —
but this is the generic baseline, not evidence of a Gini interaction with the new merchant content
specifically (not compared against a pre-ticket 1000t baseline for this world, since it isn't
anchored at 1000t and this ticket did not commit new anchors at that length).

**Step 10 (docs/parity ledger) — done.** Updated `docs/parity_ledger/infrastructure.yaml`
(`INFRA-242`'s `v2_evidence`/`support_boundary`, `SIMQ-CALIBRATED-001` cross-check addendum),
`docs/simulation_quality/current_state.md` (grade distribution table, ECONOMY prose, Recommendation
2 reframed as "attempted, root cause found"), `docs/simulation_quality/eval_matrix_results.md`
(new calibration-batch section + Zero-Pillar World Confirmation update). Ran
`make knowledge-index-update` after the doc edits (5 files re-embedded).

## Test Summary
All scoped pytest commands from test_plan.md pass (SimQ scorer/weights/report layer: 59 passed;
economy engine substrate: 78 passed; world composition/compilation: 64 passed; grade regression
fast+slow: 61+18 passed; `urban_political` guard: 9 passed; full `tests/simulation_quality/`
fast+slow: 453+24 passed, 2 skipped; `tests/unit/worldassembly/test_corpus_diversity.py` fast+slow:
54+16 passed, plus the 3 new `test_trading_company_hub_composed` cases). 2 pre-existing, unrelated
failures observed and confirmed out of scope (see Implementation Notes). `python3
tools/evaluate_simq.py --dry-run`: 750 pillars checked, 0 regressions, 0 missing.

## Files Changed
- `data/worlds/frontier_living_world/world.yaml`
- `data/worlds/frontier_extended/world.yaml`
- `data/worlds/swamp_border_world/world.yaml`
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/unit/worldassembly/test_corpus_diversity.py`
- `docs/parity_ledger/infrastructure.yaml`
- `docs/simulation_quality/current_state.md`
- `docs/simulation_quality/eval_matrix_results.md`

## Completion Summary
Content authored correctly into all 3 confirmed candidate worlds (`trading_company_hub` composed via
the required `module_refs:`/`namespace` migration, verified compile-clean, entity-count bands and
distinct-populated-factions counts unchanged from projection), full regression sweep clean (0
unattributed regressions; 2 confirmed pre-existing/unrelated failures documented, not touched), and
all cross-pillar side effects individually attributed. **AC1 ("ECONOMY grade moves measurably off C
in >=2 additional worlds") was not achieved** — measured directly across all 9 anchors at
merchant_count 3 and 6, at 200t and (diagnostically) 1000t, with zero movement. This is not an
implementation shortfall: investigation.md's core premise (that `trading_company_hub` already proves
real harvest/craft/trade content works, evidenced by `urban_political`'s 69-event run) is disproven
by direct evidence — that run, and every other ECONOMY-scored run in the corpus, is driven entirely
by the generic `gold_sink_fired` baseline; `resource_harvested`/`item_crafted`/`trade_executed`/
`shop_transaction` have never fired for any entity archetype in this engine. The gap is a
strategy/cognition-layer goal-generation gap, out of this ticket's scope to fix (`src/simulation_
quality/scorers/economy.py` and `src/economy/health_monitor.py` were never touched). AC2 ("0
regressions on a full sweep") is met. This closure is treated as the equivalent of the ticket's own
AC3 escape valve ("documented closure is equally valid if honest investigation/measurement finds
[the objective unreachable via this lever]").

**Disposition confirmed by explicit human decision (2026-07-13/14):** close this ticket as done,
keep the correctly-authored content in the 3 worlds (harmless, ready to be exercised once the real
fix lands), and file a standalone follow-up ticket for the root cause rather than reverting the
content changes or pausing the batch. Filed `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP`
(`tickets/todos/`) — scopes the strategy/cognition-layer investigation into why no entity ever
generates an accepted harvest/craft/trade intent.
