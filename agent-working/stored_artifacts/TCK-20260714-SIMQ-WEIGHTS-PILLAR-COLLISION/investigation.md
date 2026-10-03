---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION
artifact_type: investigation
tags: [simulation-quality, bug, calibration]
---

# Investigation — TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION

## Current Behavior

### The collision mechanism

`src/simulation_quality/weights.py::ScoringWeights._build_flat_index()` (lines 26-33) is a
pydantic `model_validator(mode="after")` that iterates `self.pillar_rules.values()` — a
`dict[str, dict[str, float]]` keyed by pillar name, in the insertion order YAML gave it
(Python dicts preserve insertion order; `yaml.safe_load` preserves declaration order) — and
writes every `(rule_key, value)` pair into one shared `_flat_rules: dict[str, float]` with no
pillar qualifier. Later pillars silently overwrite earlier ones for any reused key name.
`__getitem__` (lines 91-98) reads only from this single collapsed dict.

`config/simulation_quality/scoring_weights.yaml` declares 10 pillar sections in this order:
`COGNITION → AGENCY → COMBAT → FACTION → ECONOMY → PROGRESSION → SOCIAL → INFORMATION →
WORLD → NARRATIVE`. I independently re-derived the collision set with a script comparing
every key across all 10 sections — **exactly the 7 keys the ticket lists, no more, no
fewer**:

| Key | Declared in (value) | Declared in (value) | Effective (flat dict winner) |
|---|---|---|---|
| `belief_active` | COGNITION 2.0 | INFORMATION 10.0 | INFORMATION (declared later) |
| `subjective_divergence` | COGNITION 5.0 | INFORMATION 30.0 | INFORMATION |
| `knowledge_rot` | COGNITION -3.0 | INFORMATION -2.0 | INFORMATION |
| `omniscience_collapse` | COGNITION -20.0 | INFORMATION -20.0 | INFORMATION (values identical today) |
| `ecology_cycling` | ECONOMY 8.0 | WORLD 6.0 | WORLD |
| `ecology_broken` | ECONOMY -25.0 | WORLD -20.0 | WORLD |
| `knowledge_economy_active` | ECONOMY 8.0 | INFORMATION 15.0 | INFORMATION |

### Per-scorer call-site audit (does any scorer rely on cross-pillar lookup?)

Read all 10 scorer files (`src/simulation_quality/scorers/*.py`) and extracted every
`self.weights["..."]` key each one queries (via `grep -oP 'self\.weights\["\K[^"]+'`), then
diffed each scorer's key set against its own pillar's YAML section:

- `CognitionScorer` (cognition.py) queries exactly the 10 keys in COGNITION's YAML section
  — no more, no less. Same for `InformationScorer` (12/12 keys match INFORMATION's section)
  and `FactionScorer`, `AgencyScorer`, `CombatScorer`, `ProgressionScorer`, `SocialScorer`,
  `NarrativeScorer` against their own sections.
- `EconomyScorer` (economy.py) queries 13 keys, **all within** ECONOMY's 18-key YAML
  section, but never queries `ecology_cycling`, `ecology_broken`, `gold_frozen`,
  `monetary_paralysis`, or `ecology_cadence_broken` — `EconomyScorer`'s own docstring
  (line 14) states `ecology_cycle_completed` is "intentionally NOT scored here... owned by
  WorldDynamicsScorer", and `ecology_cycle_completed` is absent from `EconomyScorer.EVENT_TYPES`.
  So **`ecology_cycling`/`ecology_broken`'s ECONOMY-declared values (8.0/-25.0) are pure dead
  config today — no code path reads them, collision or not.**
- `WorldDynamicsScorer` (world_dynamics.py) queries `ecology_cycling`/`ecology_broken` for
  its own `ecology_cycle_completed` event handling (lines 125-136), and because WORLD is
  declared *after* ECONOMY in the YAML, WORLD's own value already wins in the flat dict —
  **this scorer already gets its own correct value today, by coincidence of declaration
  order, not by design.** This is a *dormant* landmine, not a live bug: if ECONOMY's section
  were ever reordered after WORLD's (e.g. during an unrelated future edit), `WorldDynamicsScorer`
  would silently start reading ECONOMY's dead 8.0/-25.0 instead of its own 6.0/-20.0, with zero
  test signal, because no test exercises declaration-order sensitivity.
  → **Conclusion: no scorer intentionally depends on cross-pillar lookup.** Every scorer's
  key set is a strict subset of its own pillar's YAML section. Pillar-scoping the lookup is a
  pure bug fix with one exception worth flagging (see Risks): `knowledge_economy_active` is
  a **live** bug (see below), not a dormant one like the ecology pair.

### Is `knowledge_economy_active`'s ECONOMY side actually live?

Confirmed via `event_extractor.py:378` that the engine really emits `paid_info_transaction`
(economy-side event, distinct from `paid_information_transaction`, the information-side
event — these are two different, both-real event type strings, not a typo). `EconomyScorer.
EVENT_TYPES` includes `"paid_info_transaction"` and `EconomyScorer.score()` (lines 130-135)
returns a real `ScoreRecord(pillar=PillarId.ECONOMY, delta=self.weights["knowledge_economy_active"], ...)`
for it — this is a genuine, reachable, currently-mis-valued lookup: `EconomyScorer` receives
INFORMATION's `15.0` instead of its own declared `8.0` whenever a `paid_info_transaction`
event fires. Unlike the ecology pair, this collision has live behavioral impact today.

### Documented design intent — §7.3/§6 of the scoring contract (important correction to the ticket's own framing)

The ticket states: "neither section [§4.8, §7.2] documents the shared-flat-namespace
behavior as an intentional design choice, so this is treated as a genuine bug." That is true
of §4.8/§7.2, but **§7.3 "Conflict Detection Rules" and §6 "Scenario Registry"
(`docs/simulation_quality/quality_scoring_contract.md` lines 1043-1054, 982-1006) directly
document dual-pillar scoring for exactly these keys as *intentional*, with an explicit
primary/secondary ownership model**:

- §6 SQ-15 ("Is information asymmetry creating decision divergence?"): Primary
  `INFORMATION`, Secondary `COGNITION` — "COGNITION is secondary because belief feeds
  cognition; INFO is the source." This is precisely the `belief_active` /
  `subjective_divergence` / `omniscience_collapse` (and by the same theme, `knowledge_rot`)
  relationship. The design *intends* COGNITION's weight to be a distinct, deliberately lower
  secondary-signal magnitude than INFORMATION's primary magnitude (which is exactly what
  COGNITION's own declared values are — 2.0/5.0/-3.0 vs. INFORMATION's 10.0/30.0/-2.0) — the
  bug is that the mechanism collapses two *intentionally different* values into one, not that
  someone forgot to consider the collision.
- §6 SQ-16 ("Is the knowledge economy active (paid information)?"): Primary `INFORMATION`,
  Secondary `ECONOMY` — "Paid info has gold cost (ECONOMY secondary) but is primarily
  INFORMATION." §7.3 states the general rule for this pattern explicitly: *"exactly one
  pillar owns the primary score; the secondary is documentary only."* **This is a real
  divergence worth flagging to the planner**: `EconomyScorer.score()` currently returns a
  real `ScoreRecord` that is added to the ECONOMY accumulator's `raw_score` for
  `paid_info_transaction` — i.e., ECONOMY's role is NOT "documentary only" in the running
  code, it is a real second scored contribution. Compare to the ecology pair (SQ-08/SQ-18,
  same Primary/Secondary shape), where "documentary only" is implemented correctly: `EconomyScorer`
  declares `ecology_cycling`/`ecology_broken` in YAML but its code never reads them — the
  YAML entry is genuinely inert. `knowledge_economy_active` is the one case where the YAML
  entry is NOT inert — it's live-scored, contradicting §7.3's own stated pattern for its
  documented exception case.
- No collision key is undocumented as unintentional dual-pillar scoring; all 7 map either to
  SQ-15 (4 keys) or SQ-08/SQ-16/SQ-18 (3 keys, of which only 1 is live).

This does not change the ticket's core fix (pillar-scoping the lookup so each pillar reads
its own declared value is correct and necessary either way), but it reframes *why* the values
differ (deliberate primary/secondary design, not oversight) and surfaces a second, narrower
question: should `EconomyScorer`'s `paid_info_transaction` handling keep contributing a real
`ScoreRecord` to ECONOMY's `raw_score` post-fix (current behavior, just now reading the
correct `8.0`), or should it become non-scoring/"documentary only" per §7.3's literal text
(a strictly larger change, and arguably a separate ticket's scope — see Risks).

## Mechanics / Engine Constraints

This is SimQ tooling (quality-scoring infrastructure), not a gameplay mechanic. No
`docs/mechanics/` chapter or gameplay-domain parity ledger file
(`combat_movement`, `faction`, `progression`, `social_narrative`, `strategic_cognition`,
`substrate`, `town_resource`) references `scoring_weights.yaml` or `ScoringWeights` — this
was confirmed in the ticket's own scoping and re-confirmed here. The only authoritative
constraint document is `docs/simulation_quality/quality_scoring_contract.md`:

- §4.8 "Data-Driven Scoring Weights" — establishes that deltas live in config, not code, and
  that `ScoringWeights` raises `pydantic.ValidationError` on bad config at load time (this
  must be preserved — see Parity Ledger below).
- §7.1/§7.2 "Extensibility Protocol" — instruct future authors to add new rule keys/pillars
  using `self.weights["rule_key"]` (bare-string lookup). Any fix that changes this call
  syntax invalidates these sections' example code and must update them (ticket's own AC
  #6 anticipates this).
- §7.3 "Conflict Detection Rules" + §6 "Scenario Registry" — as detailed above, these
  sections already document the *intended* primary/secondary relationship for all 7
  colliding keys. They do not document (and arguably prohibit, per "No duplicate signals:
  the tag for the new rule doesn't already exist in another pillar") the *mechanism* of a
  shared flat index — the exception clause is about one event scoring in two pillars via two
  distinct, independently-configured deltas, not about them colliding to the same value.

## Parity Ledger Overlap

- **`docs/parity_ledger/infrastructure.yaml::INFRA-234`** — the only parity entry that
  references `ScoringWeights` directly. Its text claims `ScoringWeights` "raises
  `pydantic.ValidationError` at startup if any required key is missing or malformed" and
  cites `test_path: tests/simulation_quality/test_weights.py::test_missing_key_raises_validation_error,
  test_malformed_value_raises_validation_error`. **Gap found**: neither test function exists
  in the current `tests/simulation_quality/test_weights.py` (verified by reading the full
  file — it has `test_missing_file_raises` instead, which asserts `FileNotFoundError`, not
  `ValidationError`, and covers a different failure mode — a missing *file*, not a missing
  *key* within a present file). **INFRA-234's `test_path` is currently broken/stale** —
  flagged per the "cross-reference test_path" instruction. Priority `P1`. This ticket's AC
  #3 requires these two tests to "still pass," but they do not currently exist to run;
  this needs an explicit decision (see Open Questions).
- No other parity ledger entry (`world_dynamics.yaml`'s WORLD-section rescale citation, per
  the ticket's own scoping note) references the collision mechanism itself.
- **New entry likely needed**: no existing entry documents the pillar-scoping guarantee this
  ticket establishes ("each pillar's scorer reads its own declared weight, never another
  pillar's"). The planner/parity-updater should add a new `INFRA-*` entry for this guarantee
  once implemented, with a `test_path` pointing at the new dedicated collision-regression
  test (AC #1/#2).

## Prior Work

- `stored_artifacts/TCK-20260713-SIMQ-SCORE-CEILING-FIX/` (done) — rescaled positive weights
  per-pillar (COGNITION untouched; INFORMATION's `subjective_divergence` raised 6.0→30.0,
  widening this collision's blast radius without introducing it). Grepped its investigation/
  plan/test_plan for any mention of the collision mechanism (`_flat_rules`, `_build_flat_index`,
  "collision", "pillar-scop*", "shared namespace") — **no hits**. Confirms the ticket's own
  claim that this ticket predates and is independent of that one's methodology.
- `docs/REGISTRY.yaml` query for tickets with `related_code_areas` touching `weights.py` /
  `scoring_weights.yaml` or `simulation-quality` tags found ~60 SimQ tickets, none of which
  touch the flat-index/collision mechanism — the closest are `TCK-20260628-SIMQ-E1-FOUNDATION`
  (where `weights.py` was originally built; registry has no `related_code_areas` for it,
  pre-dates that field) and `TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC` (documents a
  different completeness gap — building-sabotage signal, unrelated to weight collisions).
- No stored artifact anywhere in the repo addresses this specific collision before this
  ticket — confirmed via the registry pass above plus a direct grep of
  `stored_artifacts/*/investigation.md` and `plan.md` for `_flat_rules`/`_build_flat_index`
  (no hits outside this ticket's own directory).

## Risks and Open Questions

1. **Blocking: exact fix mechanism has a large, easily-underestimated test blast radius if
   `ScoringWeights.__getitem__`'s call signature changes.** `grep` across
   `tests/simulation_quality/*.py` shows **11 test files** (`test_agency_scorer.py`,
   `test_cognition_scorer.py`, `test_combat_scorer.py`, `test_economy_scorer.py`,
   `test_faction_scorer.py`, `test_information_scorer.py`, `test_narrative_scorer.py`,
   `test_progression_scorer.py`, `test_timegate_penalties.py`, `test_social_scorer.py`,
   `test_weights.py`) use the bare `scoring_weights["key"]` `__getitem__` syntax directly,
   most as the *expected-value oracle* for a scorer's `rec.delta` assertion (e.g.
   `test_cognition_scorer.py:40: assert rec.delta == scoring_weights["belief_active"]`).
   None of these are colliding keys' scorers except the 4 exactly named in the ticket (see
   below), but if the fix changes `__getitem__`'s signature (e.g. to require a pillar
   argument, or namespaces the returned mapping), **every one of these 11 files needs a
   mechanical call-site update even though only 2 of them (`test_cognition_scorer.py`,
   `test_economy_scorer.py`) have an actual *value* bug to fix.** Recommend (for planner):
   keep `ScoringWeights.__getitem__(key: str)` bare-string-compatible for
   generic/back-compat use, and give scorers a *separate*, pillar-bound accessor (e.g. a
   `PillarWeightsView`/`weights.for_pillar(pillar_id)` wrapper constructed once at
   `QualityHub`/`PillarScorer.__init__` time) so production scorer code's `self.weights["key"]`
   call sites change meaning (now pillar-scoped) without changing syntax, and the 9
   non-colliding test files need zero changes. This is an implementation-shape decision,
   correctly left to planning per the ticket's own scope note, but the blast-radius delta
   between the two shapes is large enough that it should be decided explicitly, not
   discovered mid-implementation.
2. **Blocking (partially): AC #3 references two test functions that do not exist.**
   `test_missing_key_raises_validation_error` and `test_malformed_value_raises_validation_error`
   are named in the ticket's AC and in `INFRA-234`'s `test_path`, but neither exists in
   `tests/simulation_quality/test_weights.py` today (see Parity Ledger). The plan must decide:
   (a) write these two tests now as part of this ticket (closing the INFRA-234 gap as a
   byproduct), or (b) treat AC #3 as "no regression" only and file the INFRA-234 test_path
   fix as its own follow-up. Do not assume (a) without stating it — this is new test-writing
   work not scoped by the ticket's own text, which only says these tests "still pass."
3. **Non-blocking design question surfaced, not this ticket's to resolve**: §7.3's literal
   text says the secondary pillar's role in a documented dual-pillar scenario should be
   "documentary only," but `EconomyScorer`'s `paid_info_transaction` handling is live-scored
   today (not documentary-only) — a pre-existing divergence from §7.3, independent of the
   flat-index bug. Fixing the *lookup* (this ticket) will make `EconomyScorer` correctly
   read its own declared `8.0` instead of INFORMATION's `15.0`, but does not resolve whether
   `EconomyScorer` should be scoring this event at all. Flag for a future ticket or an
   explicit divergence note in `docs/guidelines/intentional_divergences.md`; do not silently
   fold a "stop scoring this in ECONOMY" behavior change into this ticket's diff — that would
   violate the ticket's own explicit Out-of-Scope ("re-tuning... weight values... this ticket
   fixes the lookup mechanism... does not change what any pillar's intended weight should be").
4. **`omniscience_collapse`'s "identical value today" is not actually benign long-term** —
   confirmed via the flat-index mechanism: nothing prevents a future recalibration of either
   COGNITION's or INFORMATION's `omniscience_collapse` from silently diverging again, because
   the mechanism doesn't distinguish them; it's coincidence, not correctness, that they match
   today. The fix must correct this key's lookup path exactly like the other 6, even though
   no anchor's score will change for this specific key at today's values (see grade_anchors
   analysis below) — this is exactly the "latent collision" framing the ticket itself uses,
   confirmed correct.
5. **Anchor blast radius is real and larger than a first glance at "colliding keys ⊂ 2
   pillars" suggests**, because two of the four colliding pillars (INFORMATION, WORLD) are
   provably *unaffected* by the fix (they were always the flat-dict's "winner" and already
   read their own correct declared values), while the other two (COGNITION, ECONOMY) are the
   only pillars whose *scores* can actually change. See the dedicated analysis below — this
   halves the pillar surface the planner needs to worry about relative to "4 pillars touch
   collisions."

### Anchor blast-radius analysis (`tests/simulation_quality/fixtures/grade_anchors.json`)

`test_grade_anchors_entry_count_unchanged` (`test_grade_regression.py:556`) pins the anchor
count at **76 real scenario entries** (not 75 — corrected from the task brief's estimate;
79 total JSON keys minus 3 metadata keys `_note`/`_instructions`/`_grade_order`).

**Structural finding (the most important scoping fact for the planner):** because the flat
dict always resolves to whichever pillar is declared *later* in YAML, and later-declared
pillars are exactly the ones whose scorers already read correct values today, **only
COGNITION and ECONOMY pillar scores can change post-fix — INFORMATION and WORLD pillar
scores cannot change for any anchor, for any of the 7 keys**, because those two pillars were
always the "winner" already.

I cross-referenced all 76 anchors against their persisted `data/calibration/<run_key>/
quality_report.json` (one report missing:
`urban_political_selfmodel_execution_probe_seed42_200t` has no calibration file on disk —
cannot verify that single anchor at all from persisted artifacts):

- **22 of 76 anchors have `COGNITION.event_count == 0`** — provably unaffected by this fix
  (COGNITION never scored anything, so nothing to change).
- **53 of 76 anchors have `COGNITION.event_count > 0`** — pillar-level *possible* risk.
  Of these, `loop_flags`/negative `worst_events` tags directly confirm `subjective_divergence`
  fired prominently in **10 anchors** (`simq_routing_test_*`, `hero_guild_routing_*`,
  `sandbox_world_seed42_1000t`, `sandbox_world_seed42_2000t`,
  `unit_faction_tension_seed42_{1000t,2000t}`, `generated_frontier_3_42_seed42_1000t`) —
  these are **certain** to have their COGNITION score drop once `subjective_divergence`
  correctly resolves to COGNITION's own `5.0` instead of INFORMATION's currently-collapsed
  `30.0` (a 6x-per-event reduction).
  The remaining ~43 show only `self_model_active` as their loop flag (a non-colliding key),
  but **this is not proof of no collision exposure**: I manually reconstructed
  `urban_political_seed42_200t` (`COGNITION.raw_score=11.0`, `event_count=2`,
  `loop_flags=["self_model_active"]`) and the only combination of COGNITION's own declared
  weights that sums to `11.0` over 2 events is `self_model_active (1.0) + belief_active
  (currently-collapsed 10.0, i.e. INFORMATION's value)` — a single `belief_active` hit at
  1-of-2 events (50%) falls *below* the 70% loop-detection threshold and so never surfaces in
  `loop_flags`, meaning **the loop-flag/worst-events proxy under-counts collision exposure**;
  low-frequency single-event hits are invisible to it. This strongly suggests the true
  COGNITION-affected count is close to the full 53, not just the 10 confirmed via loop
  flags — but confirming each of the other ~43 exactly requires either raw per-event-type
  telemetry (not persisted in `quality_report.json`, which only stores per-pillar totals and
  negative-delta `worst_events`) or literally re-running calibration with the fix applied and
  diffing, which is what `test_grade_regression.py` does automatically and what AC #5 already
  requires.
- **18 of 76 anchors have `ECONOMY.event_count > 0`** — possible risk via
  `knowledge_economy_active`. None show any `knowledge_economy_active`-tagged loop flag or
  worst-event across the whole corpus (all show `inflation_controlled` instead, a
  non-colliding key), which is weaker evidence of "definitely unaffected" than it looks (same
  under-counting caveat as above — positive-delta single hits are invisible to both
  `loop_flags` and `worst_events`, since `worst_events` only stores negative-delta records).
  Cannot rule these 18 out from persisted artifacts alone.
- **Every anchor with `ECONOMY.event_count > 0` also has `COGNITION.event_count > 0`** in
  this corpus (no anchor is ECONOMY-only-affected), so the "at-risk" set for re-anchoring is
  bounded by the union of the two counts: **53 of 76 anchors are POSSIBLY at risk (COGNITION
  and/or ECONOMY exercised), 22 of 76 are PROVABLY unaffected (both pillars zero-event), and
  1 of 76 cannot be evaluated at all (missing calibration report)**.
- **Recommendation for planning**: do not attempt to hand-verify all 53 by reconstructing
  arithmetic (as I did for 1 anchor above, at real but bounded effort) — this ticket's own
  AC #5 already prescribes the correct mechanism: implement the fix, re-run `make calibrate`
  (or targeted per-scenario runs) for at least the 53 at-risk keys, run
  `test_grade_regression.py`, and enumerate every diff. Given 10 are already certain
  (`subjective_divergence`-driven, most likely large swings since it's a 6x per-event
  factor), expect this to be a real, non-trivial re-anchoring pass — not a rubber-stamp — and
  it should very likely be its own follow-up ticket rather than folded into this one, given
  the ticket's own Out-of-Scope note ("full re-anchoring... not assumed in-scope by
  default").

## Anti-Drift Hazards

- **Do not accidentally fix the `EconomyScorer`/`paid_info_transaction` "documentary only"
  divergence from §7.3 while fixing the lookup mechanism** — these are two different bugs
  (one is "wrong value read," the other is "should this even score at all") and conflating
  them would silently change ECONOMY's live scoring behavior beyond what this ticket's scope
  allows. If the implementer notices this while touching `economy.py`, it must be raised
  explicitly, not silently patched.
- **Do not widen the fix into a weight re-tuning pass.** The ticket is explicit that the 7
  keys' *values* are not being re-derived, only their *lookup*. Any temptation to "fix" the
  now-visible large swings in COGNITION's raw_score (once `subjective_divergence` stops
  reading INFORMATION's inflated 30.0) by bumping COGNITION's own declared 5.0 upward is
  out of scope — that is a SCORE-CEILING-FIX-shaped decision, not this ticket's.
  Re-anchoring the *test fixtures* to match the corrected (lower) COGNITION scores is in
  scope (per AC #5); changing the *weight values themselves* to compensate is not.
  Recalibration or non-trivial rescoping should be run through create-tickets rather than an
  ad hoc mid-ticket decision (this is exactly the kind of decision the create-tickets skill
  exists to route rather than being decided silently mid-flight).
  If evidence during implementation suggests the values genuinely need retuning, stop and
  raise it rather than deciding unilaterally.
- **Do not let the `__getitem__` signature change silently break `int_param()` or
  `pillar_weight()`** — these are separate accessor methods on `ScoringWeights`
  (`weights.py` lines 100-110) that do not touch `_flat_rules` at all (`int_param` reads
  `self.detection.time_gates`, `pillar_weight` reads `self._pillar_weights`). They are
  unaffected by this bug and must stay unaffected by the fix — any refactor of
  `ScoringWeights`'s internals should leave these two methods' behavior byte-identical.
- **Do not touch the WORLD/ECONOMY `ecology_cycling`/`ecology_broken` pair's runtime
  behavior** — confirmed dead config on the ECONOMY side; `WorldDynamicsScorer` already
  reads correct values today. The fix should still separate these two correctly in the data
  structure (closing the "future YAML reorder" landmine described above), but no anchor's
  score changes from this specific pair, and no scorer's call site needs behavior changes for
  it beyond the mechanical pillar-scoping.
- **Watch for `PillarAccumulator`/`QualityHub` construction order dependencies** — `QualityHub.
  __init__` (`quality_hub.py` lines 103-111) builds `SCORER_REGISTRY` from each scorer's
  `EVENT_TYPES` and separately builds `self._accumulators: dict[PillarId, PillarAccumulator]`
  for all `PillarId` members — neither depends on `ScoringWeights`'s internal representation
  beyond the constructor call `ScoringWeights.load(...)`, so a pillar-scoped internal
  refactor should not require `QualityHub` changes unless the chosen mechanism also changes
  how scorers are *constructed* (e.g., if `PillarScorer.__init__` needs to know its own
  `PillarId` to request a scoped view — currently `PillarScorer.__init__` only takes
  `weights: ScoringWeights`, with each subclass hardcoding its own `PillarId` only inside
  `_rec()` closures, not as a stored `self.pillar_id` attribute. This is worth confirming
  explicitly in planning: **no scorer class currently exposes `self.pillar_id`** — if the fix
  needs each scorer to know its own pillar to request a scoped weights view, that attribute
  must be added to `PillarScorer.__init__` (or each subclass), which touches all 10 scorer
  `__init__`s, not just the 4 with actual collisions.
