---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION
artifact_type: investigation
tags: [simulation-quality, observability, world]
---

# Investigation — TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION

## Docs Requiring Update

- `docs/simulation_quality/entity_lifecycle_score.md`: add the real correlation data (density
  vs. path metrics, tick-length activity profile, minimum-sample threshold sweep) — Implement
  phase
- `docs/guides/entity_lifecycle_score.md`: update the interpretation guidance with the real
  findings (short-run clustering caution, dominant_shape_share-vs-density context) — Implement
  phase

## Item 1 — Density vs. path_length/path_density correlation (real data, n=6 worlds, fixed 500 ticks)

Ran the sibling ticket's own tool on 6 real corpus worlds spanning the real
`entity_density_per_area` range (`docs/world/density_metrics.md`), fixed at 500 ticks,
`SIM_OBS_MODE=NORMAL`:

| World | `entity_density_per_area` | `path_length` mean | `path_density` mean | `dominant_shape_share` |
|---|---|---|---|---|
| `wilderness_survival` | 0.000168 | 602.5 | 1.2051 | 0.909 |
| `resource_dense_basin` | 0.001080 | 565.7 | 1.1313 | 0.391 |
| `crowded_frontier` | 0.001872 | 560.4 | 1.1207 | 0.258 |
| `hero_guild_routing` | 0.002033 | 601.0 | 1.2019 | 0.452 |
| `dungeon_crawl` | 0.002099 | 547.3 | 1.0947 | 0.688 |
| `urban_political` | 0.002970 | 744.2 | 1.4884 | 0.136 |

**Pearson r (density vs. `path_length_mean`/`path_density_mean`): 0.495, n=6.** Real, computed,
not assumed either direction — but a weak-to-moderate correlation at n=6 is not statistically
reliable evidence of a real effect; the raw numbers are non-monotonic (602.5 → 565.7 → 560.4 →
601.0 → 547.3 → 744.2 as density rises), consistent with noise rather than a strong trend.

**Real finding: no density-based correction to `path_length`/`path_density` is justified by this
evidence.** The within-run z-score mechanism (already the tool's own primary cross-entity
comparison method) is not shown to need a density adjustment. This is a legitimate "verified, no
correction needed" outcome, not a failure to find something.

**Real, stronger secondary finding (not this ticket's own primary AC, but directly relevant)**:
**Pearson r (density vs. `dominant_shape_share`): -0.734, n=6** — a real, much stronger negative
correlation. Denser worlds measurably show LESS population-wide path clustering (more diverse).
Not strong enough at n=6 to encode as a hard correction constant, but real enough to document as
interpretive context in the guide (a low `dominant_shape_share` in a low-density world is a more
notable finding than the same value in a high-density world, given this real trend).

## Item 2 — Tick-length activity profile (real data, fixed world `sandbox_world`, seed 42)

| Ticks | `path_length` mean | `path_density` mean | `dominant_shape_share` | `phase_coverage` mean |
|---|---|---|---|---|
| 200 | 191.9 | 0.9597 | 0.500 | 0.239 |
| 500 | 635.4 | 1.2709 | 0.611 | 0.378 |
| 1000 | 1175.9 | 1.1759 | 0.190 | 0.533 |
| 2000 | 1259.0 | 0.6295 | 0.179 | 0.557 |

**Real finding #1 — `path_density` is NOT flat over a run's duration**: it rises from 200→500
ticks, then declines through 1000→2000. Not simply front-loaded or back-loaded — genuinely
non-monotonic. Plausibly consistent with this repo's own existing, precedented finding in
`docs/audits/D05_entity_differentiation.md` F4 ("entities settle into uniform hunger cycling"
after early ticks) — early activity gives way to repetitive routine, which would show up exactly
as declining `path_density` over a longer window. Not independently re-verified here (out of this
ticket's own scope to re-audit D05), but a plausible, disclosed, precedented explanation rather
than an unexplained anomaly.

**Real finding #2 — `phase_coverage` monotonically increases with tick length**, exactly matching
the design conversation's own predicted tick-sensitivity (0.24 → 0.38 → 0.53 → 0.56). Confirms
(not just assumes) that comparing `phase_coverage` across different tick-lengths needs the same
caution already documented for it.

**Real finding #3, actionable — `dominant_shape_share` is artificially HIGH at short tick-lengths
and stabilizes by ~1000 ticks**: 0.50 (200t) → 0.61 (500t) → 0.19 (1000t) → 0.18 (2000t). At
short tick-lengths, entities' paths are too short to differentiate — a real, measured instance of
the design conversation's own predicted confound ("short average path length is itself a
confound for clustering-based diversity metrics"). The value roughly settles between 1000 and
2000 ticks (0.190 vs 0.179 — a small, plausibly-noise-level difference vs. the much larger 500→
1000 swing).

**Real, actionable correction**: add a `clustering_reliable_tick_threshold` config value
(`1000`, derived from where the real sweep above stabilizes) and a corresponding
`clustering_reliable: bool` field to `run_metadata()`'s output, matching the existing
`stall_detector_reachable` pattern — so a `dominant_shape_share` computed on a short run carries
an explicit, honest caveat rather than being read at face value.

## Item 3 — Minimum-sample threshold sweep (real data, `frontier_extended`, 800 ticks)

For 59 entities with ≥30 real events, computed entropy on a truncated prefix of length `L` and
measured the mean absolute deviation from that same entity's own full-length entropy:

| `L` | mean \|entropy(L) − entropy(full)\| |
|---|---|
| 3 | 0.4309 |
| 6 | 0.3596 |
| 10 | 0.3280 |
| 15 | 0.3088 |
| 20 | 0.2782 |
| 25 | 0.2580 |

**Real finding: no clean empirical "knee" exists.** The deviation decreases smoothly and
gradually as `L` increases — there is no sharp inflection point that would justify treating `6`
as a uniquely-correct cutoff over, say, `10` or `15`. Even at `L=25`, mean deviation is still
substantial (0.258) — short-prefix entropy estimates remain noisy well past the inherited `n=6`
threshold.

**Real, honest conclusion: keep `minimum_sample_threshold: 6` unchanged.** The evidence doesn't
justify raising it (no knee to justify a specific higher cutoff either) — it remains a
reasonable, conservative floor, not a precisely-derived one. Documenting this explicitly (smooth
decay, no clean cutoff) is itself the real finding — a legitimate "verified as reasonable,
not raised" outcome, not a failure to find a better number.

## Item 4 — Other structurally-gated detectors

Re-confirmed only `stall_detector_reachable` (300-tick window) has a clean tick-based
reachability proxy. `life_arc_detector_reachable` (Hero generation ≥ 2) still has none — not
resolved by this ticket's own real data collection (none of the 6+ real runs above reached
generation 2 in any entity, consistent with the sibling ticket's own disclosed rarity finding).
Stays `null`, not guessed, matching the sibling ticket's own already-documented decision.
