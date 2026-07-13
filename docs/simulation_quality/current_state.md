---
status: active
layer: simulation
authority: P1
audience: developer
tags: [simulation-quality, corpus, calibration]
---

# SimQ Current State Report

**Purpose:** a single, periodically-refreshed snapshot of where the 10-pillar quality corpus
actually stands right now — distinct from `eval_matrix_results.md`, which is an append-only
historical log of every calibration batch since 2026-07-02. That log is the evidentiary record;
this doc is the answer to "what's the current picture," refreshed in place rather than layered
with dated notes. When this doc and `eval_matrix_results.md` disagree, re-run the refresh command
below — this doc should always reflect the latest run, not accumulate history of its own.

**Last refreshed:** 2026-07-13, from the committed `tests/simulation_quality/fixtures/grade_anchors.json`
(72 entries) — each entry independently verified against a live run at the time it was last
committed, spot-checked here via a standalone `calibrate_simq.py` re-run of
`urban_political_selfmodel_probe_seed42_200t` (see Known Issue below for why the full-corpus live
run couldn't be used directly this time).

**To refresh this report:** `python3 tools/evaluate_simq.py --dry-run`, then update the table below
from its output. Prefer `--dry-run` for now — see the known tooling bug below before running the
live (non-dry-run) full-corpus mode. If `--dry-run` reports any `REGRESS` pillars, resolve those
first (stale anchor vs. real regression — see `docs/audits/D20_simq_integration.md` for the
established investigation pattern) before treating this doc's numbers as current.

**Known issue — `tools/evaluate_simq.py`'s live (non-`--dry-run`) mode has a real bug:**
`_run_calibration()` (line 59) never forwards `--profile` to `calibrate_simq.py`; `_parse_run_key()`
(line 45) derives the calibration `--name` purely from the run_key's regex-matched prefix. For any
run_key where the profile name differs from the world name (currently only
`urban_political_selfmodel_probe_seed42_200t`, the probe fixture added this session), this passes
the *profile* name where the *world* name is expected. `calibrate_simq.py`'s world-loading then
silently falls back to a generic synthetic scenario (`world_id: "unknown"`,
`scenario_name: "PROD_SMALL"`, confirmed via that run's `run_manifest.json`) instead of erroring —
producing a near-empty, meaningless result that gets compared against the real anchor. Verified via
a standalone re-run of the same scenario, which reproduces the correct, anchor-matching result
(COGNITION=S/5610 events, FACTION=S/29, SOCIAL=S/770, NARRATIVE=A/11) — confirming this is a tooling
bug, not a quality regression. Evidence preserved in `tmp/evaluate_simq_bug_evidence/`. Not yet
filed as a ticket.

---

## Current grade distribution (72 anchor entries, 17 worlds)

| Pillar | S | A | B | C | D |
|---|---|---|---|---|---|
| WORLD | 0 | 1 | 71 | 0 | 0 |
| NARRATIVE | 7 | 52 | 9 | 4 | 0 |
| COMBAT | 0 | 1 | 46 | 25 | 0 |
| PROGRESSION | 0 | 0 | 38 | 34 | 0 |
| FACTION | 30 | 15 | 6 | 21 | 0 |
| INFORMATION | 0 | 0 | 35 | 37 | 0 |
| COGNITION | 8 | 5 | 37 | 22 | 0 |
| SOCIAL | 15 | 0 | 0 | 57 | 0 |
| ECONOMY | 0 | 0 | 12 | 60 | 0 |
| AGENCY | 0 | 8 | 0 | 64 | 0 |

---

## Per-pillar read

**Discriminative-power check (2026-07-13, prompted by a direct question about whether the scoring
formula itself needs recalibration — not just corpus coverage):** grade letters alone hide a real
problem. Cross-referencing the raw `normalized_score` values from a full live corpus run
(`tmp/evaluate_simq_full_run_20260713.log`) against the S/A/B/C/D band thresholds
(`quality_scoring_contract.md` §4.5: `S >2.0`, `A 0.5-2.0`, `B 0.0-0.5`) shows **4 of 10 pillars
structurally cannot reach A or S under the current weight scale, no matter how good the world is**:

| Pillar | Max normalized score seen (all 72 scenarios) | A threshold | Gap |
|---|---|---|---|
| WORLD | 0.30 (38-event run) | 0.5 | Never halfway there — entire real range (0.0-0.3) fits inside the B band alone |
| ECONOMY | 0.16 (a **69-event** run — genuinely rich activity) | 0.5 | 1/3 of the way even at its richest observed point |
| PROGRESSION | 0.13 (46-event run) | 0.5 | Same shape |
| INFORMATION | 0.04 (1-event run) | 0.5 | ~12x short |

This is a weight/normalization-scale problem, not a corpus-coverage problem — content authoring
alone (see Recommendation 2 below) will not fix it, since even the single richest ECONOMY run in
the whole corpus (69 scored events) still only reached 1/3 of the way to A. See Recommendation 1.

**NARRATIVE, COMBAT** — the other two "always-on" pillars, and by contrast genuinely healthy:
NARRATIVE spans all 4 grades with real spread (7 S / 52 A / 9 B / 4 C), COMBAT spans a narrower but
real range including both B and C outcomes reflecting genuine archetype differences (a combat-only
world scores differently from a low-combat one). Not exhibiting the same ceiling pattern as WORLD.

**FACTION, INFORMATION** — declared structurally complete by the SimQ roadmap's Phase 5 gate
(`TCK-20260713-SIMQ-COVERAGE-DECISION-GATE`, `docs/plans/archive/simq_development_roadmap.md`).
11/17 and 9/17 worlds carry calibrated content respectively; every remaining world has a
documented, tier-appropriate reason to stay inert (Stress/Unit/Regression-tier worlds are
*supposed* to isolate other mechanics). No further content-authoring work is queued for either
pillar.

**SOCIAL** — staged depth declared the permanent bar by the same Phase 5 ruling. 3/17 worlds
activated (`urban_political`, `frontier_living_world`, `highland_traverse`); the one evaluated
non-candidate (`dungeon_crawl`) is structurally incapable (no settlement/civilian module, so the
cooperation gate never opens). Future expansion is opportunistic (if/when a new world is authored
with a qualifying module), not a queued initiative.

**AGENCY** — C in every world except `simq_routing_test`/`hero_guild_routing` is archetype-correct
by design (`ENABLE_ADVENTURE_ROUTING` is opt-in per world, DA-ruled intentional,
`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`). Not a gap.

**COGNITION** — split state, the one pillar with a genuinely unresolved half:
- Self-model *materialization* generalizes cleanly and cheaply to real archetype worlds (proven
  on `urban_political`, `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`) — this is what drives
  the S/A/B signal in the table above.
- Self-model *query-routing* (Branch B asking "what don't I know, who might know it") is verified
  mechanically correct (`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`, direct test-harness
  invocation) but has **zero live-gameplay reach**: no shipped world profile enables the required
  flag combination, and — confirmed directly, `grep -rn "ActionIntentAdapter" src/` — the
  execution entry point (`ActionIntentAdapter.execute()` in
  `src/engine/intent/action_intent.py:32`) has no production call site anywhere. It exists only
  as a class definition and a docstring mention. Every other gated phase in `src/engine/pipeline.py`
  (`cooperation`, `information_belief`, `adventure_decision`) is wired via a `run_phase(...)` call;
  no equivalent line exists for intent execution. This is a real, well-scoped, unstarted gap — see
  Recommendation 3 below.

**ECONOMY** — the pillar with the most headroom, for two separate reasons. `EconomyScorer`
(`src/simulation_quality/scorers/economy.py`) actually listens for 10 distinct event types
(harvesting, crafting, trading, gold flow, scarcity, inflation control, conservation checks,
paid-info transactions, quest rewards) — this is not a thin, single-signal pillar the way it's
sometimes described, so the corpus-wide C-heavy distribution is partly a genuine content gap: most
worlds simply don't have sustained harvest/craft/trade content authored into them (Recommendation
2 below). But the discriminative-power check above shows the ceiling issue is real too — even the
richest observed run (69 events) only reached 1/3 of the way to A (Recommendation 1). Both need
addressing; content authoring alone won't be enough. This pillar was never addressed by the SimQ
roadmap (explicitly out of scope — a Gini-threshold/archetype-composition question, not the
`FeatureMode` gating question the roadmap's 4 pillars shared).

---

## Recommended next features

All four are genuinely open — not previously investigated-and-declined, unlike FACTION/
INFORMATION/SOCIAL depth (closed) or AGENCY rollout (closed). None requires re-litigating any
existing DA ruling. Ordered by priority, not discovery order — 1 and 4 are both measurement-
validity fixes and probably belong before 2 and 3 in any real sequencing, since they affect
whether *any* future content-authoring or engine work would even be visible in the grades.

### 1. Recalibrate the weight/normalization scale for WORLD, ECONOMY, PROGRESSION, INFORMATION

**Why now:** the discriminative-power check above found these 4 pillars structurally cannot reach
A or S under current weights — WORLD's entire observed range across the whole corpus (0.0-0.3)
fits inside the B band alone; ECONOMY tops out at 1/3 of the way to A even at its single richest
observed point (69 events). This means the scorer currently cannot ever tell you a world is
*exceptional* on these 4 dimensions, only "has some activity" vs. "has none" — a real gap against
SimQ's own stated goal of balance/tuning support (`quality_scoring_contract.md` §1), which needs
the top of the scale to be reachable to be useful.

**Shape of the work:** an investigation-tier ticket first — deliberately construct or identify one
genuinely best-case and one genuinely worst-case scenario per affected pillar, run them through the
current formula, and determine whether raising per-event weights or lowering grade thresholds (or
both) restores real discrimination without destabilizing the many already-passing anchors for these
pillars. Changing shared weight constants risks moving grades corpus-wide, so this needs a full
regression sweep and probably a wholesale `grade_anchors.json` re-anchor, not a quiet tweak.

**Effort estimate:** M — mostly analysis and calibration-formula tuning, not new engine code, but
touches every anchor in the corpus so the verification tail is long.

### 2. Author ECONOMY-rich content into 2-3 more archetype worlds

**Why now:** this pillar was never in scope for any prior SimQ initiative — the 2026-07-10 roadmap
covered COGNITION/FACTION/INFORMATION/SOCIAL specifically because they share one gating mechanism
(`FeatureMode` flags); ECONOMY's mechanism is different (Gini-threshold + content presence) and was
explicitly carved out, not investigated. It's the largest remaining pillar-visibility gap in the
corpus by grade-count (60/72 C).

**Shape of the work:** same playbook as the FACTION/INFORMATION depth waves — pick 2-3 archetype
worlds with a plausible in-fiction merchant/crafting economy (e.g. a trade-hub or settlement-heavy
world), author harvest/craft/trade content, recalibrate, verify signal, full regression sweep.
Should start as an investigation-tier ticket (confirm which worlds have a merchant NPC or
crafting-capable population already, per `data/worlds/*/world.yaml`) before any content authoring —
mirrors how Phase 3's investigation found FACTION/INFORMATION already more covered than assumed;
ECONOMY's real gap size should be verified the same way before committing to a multi-world content
pass.

**Effort estimate:** M, by analogy to Phase 2 (SOCIAL) — same "activate a pillar in a few more
worlds via content authoring, no engine work expected" shape. **Depends on Recommendation 1
landing first** (or at least being scoped) — authoring more ECONOMY content into a formula that
caps at 1/3-of-A regardless of volume risks spending real effort for a result that still reads as
C/B corpus-wide.

### 3. Wire `ActionIntentAdapter.execute()` into the production tick pipeline

**Why now:** this is the specific, named blocker the Phase 5 gate identified and explicitly
deferred as "a distinct future initiative if gameplay ever actually needs live self-model
query-routing" — not a re-opening of a closed question, but picking up a thread that was
deliberately left for exactly this kind of follow-up decision.

**Shape of the work:** add a new gated phase to `src/engine/pipeline.py` (matching the existing
`run_phase("cooperation", ...)` / `run_phase("information_belief", ...)` pattern) that takes the
`ActionIntent` routed by `InformationBeliefPhase` Branch B and calls
`ActionIntentAdapter.execute()` on it, merging the resulting `EntityUpdate` back into the tick's
update set. Should start as an investigation ticket — the exact merge point, ordering relative to
the two existing information/cooperation phases, and whether a new feature flag is needed (almost
certainly yes, to keep this off by default in shipped profiles) all need scoping before
implementation.

**Effort estimate:** M-L — this is real engine work (a new pipeline phase, not content authoring),
but narrowly scoped: the routing and execution logic already exist and are already tested in
isolation; the gap is purely the missing call site.

### 4. Persist raw `normalized_score` alongside the letter grade, with its own tolerance check

**Why now:** `grade_anchors.json` stores only the discretized letter (`"S"`, `"B"`, etc.) — never
the raw `normalized_score` that produced it, even though every `quality_report.json` computes and
prints it. Combined with S being an unbounded top band (`>2.0`, no ceiling specified), this makes
the regression-detection goal itself blind in both directions for any pillar already at S: a real
improvement (e.g. norm-score 2.1 → 10.0) shows as "S → S", invisible — but so does a real
*regression* (10.0 → 2.1) that doesn't happen to cross a full band boundary. The anchor system can
currently only catch changes that cross a grade-letter line, not changes in magnitude within one.

**Why this isn't the excluded Non-Goal:** SimQ's §14 explicitly rules out "historical run
comparison" (dashboards, trend charts across runs over time) — that stays out of scope, reaffirmed
2026-07-10. This is narrower: one additional number stored per anchor entry, checked with one
additional tolerance assertion, squarely inside the existing regression-detection goal (§1), not a
new comparison/analytics capability.

**Shape of the work:** extend `grade_anchors.json`'s schema to carry `{"grade": "S", "score":
2.87}` per pillar instead of a bare string (migration needed for all 72×10 existing entries);
extend `test_grade_regression.py`'s comparison to also assert the raw score stays within a
tolerance band (e.g. ±15%) of the anchored value, independent of whether the letter grade moved.
Should start as an investigation ticket to confirm the right tolerance width empirically (too tight
→ false positives from legitimate run-to-run variance already documented in
`docs/audits/D20_simq_integration.md`'s wall-clock-throttle findings; too loose → doesn't actually
catch anything the letter-only check wouldn't).

**Effort estimate:** S-M — schema migration touches every anchor entry, but the logic itself is a
straightforward tolerance check, not new scoring infrastructure.

**Not recommended right now:** re-opening FACTION/INFORMATION/SOCIAL/AGENCY depth (all closed with
real evidence, see Phase 5 ruling), or any of SimQ's explicit MVP Non-Goals (per-entity profiles,
historical run comparison, real-time alerting, ML anomaly detection, automated config suggestion —
`quality_scoring_contract.md` §14, reaffirmed out of scope by explicit user decision 2026-07-10).

---

## Related

- `docs/simulation_quality/quality_scoring_contract.md` — the authoritative scoring spec
- `docs/simulation_quality/eval_matrix_results.md` — full historical calibration batch log
- `docs/simulation_quality/corpus_tier_taxonomy.md` — corpus tier structure and per-world classification
- `docs/plans/archive/simq_development_roadmap.md` — the closed roadmap this report's "declared
  complete" pillars trace back to
- `docs/audits/D20_simq_integration.md` — wiring/calibration history, investigation-pattern precedent
