# RPG regression metric set v1 (rpg-planner + rpg-designer, 2026-10-09)

Principle: outcome neutrality (docs/brainstorm/simulation-rule-taxonomy-evaluation-direction.md §5) plus D33. Every metric is one of two classes:
- **VALIDITY**: a rule contradicted itself. Exact or logical checks; they can FAIL.
- **OUTCOME**: what the world did. Paired against the baseline (5 seeds, k*SE plus a practical floor). Never graded on its own. Crossing the line gives state **DRIFT**, which means "trace the cause". It fails a PR only once the trace finds a validity break; otherwise it's recorded as the world changing.

## VALIDITY (hard, permanent; each cites its rule)
| id | check | oracle |
|---|---|---|
| V1 nothing-from-nothing (food) | zero eaten units without a source item; widens into the M2 ledger (coin, goods, creatures) | Bible 03 atomic conservation; H3 |
| V2 conservation | coin and goods invariants green; the meat balance (body meat at death = eaten + looted + decayed + remaining) from records | Bible 03; H7 |
| V3 no death beside a known untried way | zero starvation deaths where the H6 record's column (a) lists a way never attempted | SURV-06/07; H6; memo rows 54/56 |
| V4 diet and trait gates | zero inn meals by non-people kinds; zero plant forages by meat-only kinds (kept permanently, even once structural) | D43, D44; H4 |
| V5 in-world positions | zero entity-ticks outside world bounds (LAW-POSITION-IN-WORLD) | Bible 06 topology; Bible 02 |
| V6 no minted coin | zero coin created outside declared sources (from batch 3; R4 then moves here) | EXCH-02, D38 |
| V7 no dead way (liveness) | every way SURV-06 declares for a kind, and every earning way EXCH-02 declares, is used at least once in the gate worlds where its preconditions hold (replaces H1/H2/H5; H5 = the hunt instance: FEEDING_KILL joined to a CORPSE_FOOD eat) | SURV-06, EXCH-02, D44/D48 |

## OUTCOME (standing, report-only, drift-watched)
| id | figure |
|---|---|
| O1 | starvation share (people; each kind group) |
| O2 | population over time and deaths by cause, per kind group (D42) |
| O3 | attacks on people by meat-eaters (R3: the earliest sign that appraisal regressed) |
| O4 | ways mix per world and kind group (gather/hunt/buy/receive; earn: sell/wage) |
| O5 | treasury balances and minting volume (until V6) |
| O6 | kills not eaten, by reason (scared off / sated / died) (D48) |
| O7 | tick time (pinned, paired): a perf signal, report only |

## Baselines
- A versioned, immutable file per version (testing-planner's format; mutation-baseline convention), stored as a small summary table.
- Each run is reported against the LAST baseline AND the FIRST baseline of the current milestone (slow drift).
- A re-baseline row must cite a divergence id and/or memo row, plus the PR, plus the before/after on the standing set. Without a citation it's REFUSED. It needs the owner's ruling only when it crosses an R1/R2 stop line or carries an undecided world-semantic change.

## SimQ NEEDS/LIVELIHOOD pillar
It grades CAUSAL VALIDITY, not survival:
- every need met came through a declared way with a real cost;
- nobody died beside a known way;
- each kind eats by its diet;
- declared ways get used where their preconditions hold;
- deaths have causes that fit the world.
Outcome figures appear as descriptive context with NO score and NO bands (a band is a target in disguise, D33). It's graded on pooled seeds and replaces the flapping single-run corpus_diversity anchors.

## Split
- rpg: definitions, oracles, thresholds (k, floors), baseline content, the metric computation from typed records, and the pillar scorer.
- testing: the harness (fresh process per world/seed, everything pinned), the scheduled job (#464 pattern) plus on-demand dispatch on a ref, the baseline file format and staleness, the report states (pass/fail/drift/unstable/stale/no-data), the rerun-same-SHA step, the ownership registry and the rolling issue.
