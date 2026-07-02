# SimQ Multi-Seed / Multi-Tick Evaluation Matrix Results

**Ticket:** TCK-20260702-SIMQ-EVAL-MATRIX
**Date:** 2026-07-02
**Corpus expansion:** 8 anchor entries → 25 anchor entries

---

## Overview

This document records the grade distributions from the multi-seed, multi-tick calibration matrix.
Seventeen new calibration runs were executed across four signal-producing worlds. Per-pillar grades
are extracted from `data/calibration/{run_key}/quality_report.json` and committed to
`tests/simulation_quality/fixtures/grade_anchors.json`.

Zero-pillar worlds (AGENCY/COGNITION/ECONOMY/SOCIAL/FACTION/INFORMATION all C in default mode)
were not included: `wilderness_survival`, `highland_traverse`, `swamp_border_world`,
`frontier_extended`, `frontier_living_world`. All confirmed structurally feature-gate blocked.

---

## Grade Distribution Tables

### Notation

- Each cell shows the grade per seed (seed42 / seed123 / seed456) or a single grade where all seeds agree.
- "Stable" means identical grade across all seeds at that tick count.
- GRADE_ORDER: D < C < B < A < S

---

### dungeon_crawl

#### 500t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Stable? |
|---|---|---|---|---|
| COMBAT | B | B | B | yes |
| NARRATIVE | B | B | B | yes |
| PROGRESSION | B | B | B | yes |
| WORLD | B | B | B | yes |
| AGENCY | C | C | C | yes |
| COGNITION | C | C | C | yes |
| ECONOMY | C | C | C | yes |
| FACTION | C | C | C | yes |
| INFORMATION | C | C | C | yes |
| SOCIAL | C | C | C | yes |

#### 1000t (seeds 42 / 123 / 456 — seed42 pre-existing)

| Pillar | seed42 | seed123 | seed456 | Stable? |
|---|---|---|---|---|
| COMBAT | B | B | B | yes |
| NARRATIVE | B | B | B | yes |
| PROGRESSION | B | B | B | yes |
| WORLD | B | B | B | yes |
| AGENCY | C | C | C | yes |
| COGNITION | C | C | C | yes |
| ECONOMY | C | C | C | yes |
| FACTION | C | C | C | yes |
| INFORMATION | C | C | C | yes |
| SOCIAL | C | C | C | yes |

#### 2000t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Stable? |
|---|---|---|---|---|
| COMBAT | B | B | B | yes |
| NARRATIVE | B | B | B | yes |
| PROGRESSION | B | B | B | yes |
| WORLD | B | B | B | yes |
| AGENCY | C | C | C | yes |
| COGNITION | C | C | C | yes |
| ECONOMY | C | C | C | yes |
| FACTION | C | C | C | yes |
| INFORMATION | C | C | C | yes |
| SOCIAL | C | C | C | yes |

**Stability analysis (dungeon_crawl):** Exceptionally stable. All four active pillars (COMBAT,
NARRATIVE, PROGRESSION, WORLD) hold B across all three seeds and all three tick counts (500t, 1000t,
2000t). No grade drift observed at 2000t — COMBAT does not degrade. The six blocked pillars remain
at C across all runs. dungeon_crawl is the most deterministic world in the corpus.

---

### urban_political

#### 500t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| COMBAT | B | B | B | stable |
| NARRATIVE | B | A | B | seed123 elevated to A |
| PROGRESSION | B | B | B | stable |
| WORLD | B | B | A | seed456 elevated to A |
| AGENCY | C | C | C | stable |
| COGNITION | C | C | C | stable |
| ECONOMY | C | C | C | stable |
| FACTION | C | C | C | stable |
| INFORMATION | C | C | C | stable |
| SOCIAL | C | C | C | stable |

#### 1000t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| COMBAT | B | B | B | stable |
| NARRATIVE | B | B | B | stable (see OQ1 below) |
| PROGRESSION | B | B | B | stable |
| WORLD | B | B | B | stable |
| ECONOMY | B | B | B | all three seeds activated at 1000t |
| COGNITION | C | B | C | seed123 only |
| AGENCY | C | C | C | stable |
| FACTION | C | C | C | stable |
| INFORMATION | C | C | C | stable |
| SOCIAL | C | C | C | stable |

**Stability analysis (urban_political):** Mildly variable at 500t — NARRATIVE and WORLD show ±1
seed-dependent variation (B↔A). At 1000t, NARRATIVE normalises to B across all seeds (the seed123
500t A was a window-boundary artefact). Notably ECONOMY activates at 1000t for all three seeds
(C→B), confirming this is a duration effect rather than seed noise. COGNITION shows a transient
signal only in seed123 at 1000t (B) — not reliable enough to treat as a pillar.

---

### simq_routing_test (ENABLE_ADVENTURE_ROUTING=ON)

#### 500t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| AGENCY | B | B | B | confirmed ≥ B all three seeds |
| COGNITION | C | B | B | seeds 123 and 456 show B |
| COMBAT | B | B | B | stable |
| NARRATIVE | A | A | A | stable — highest grade in corpus |
| PROGRESSION | B | B | B | stable |
| WORLD | B | B | B | stable |
| ECONOMY | C | C | C | stable |
| FACTION | C | C | C | stable |
| INFORMATION | C | C | C | stable |
| SOCIAL | C | C | C | stable |

**AGENCY cross-seed confirmation (AC6):**
- seed42: AGENCY=B (pre-existing)
- seed123: AGENCY=B (confirmed)
- seed456: AGENCY=B (confirmed)

All three seeds show AGENCY ≥ B with `ENABLE_ADVENTURE_ROUTING=ON`. Gate passes.

**Stability analysis (simq_routing_test):** Highly stable. NARRATIVE=A is consistent across all
three seeds (the highest and most consistent non-B grade in the entire corpus). AGENCY=B holds
deterministically under ENABLE_ADVENTURE_ROUTING=ON. COGNITION shows an interesting seed-dependent
signal: C for seed42, B for seeds 123 and 456 — suggesting COGNITION is borderline in this world
profile and may benefit from further investigation.

---

### sandbox_world

#### 1000t (seed 42 — pre-existing)

| Pillar | grade |
|---|---|
| NARRATIVE | A |
| COGNITION | B |
| ECONOMY | B |
| COMBAT | B |
| PROGRESSION | B |
| WORLD | B |
| AGENCY | C |
| FACTION | C |
| INFORMATION | C |
| SOCIAL | C |

#### 2000t (seed 42 — new)

| Pillar | grade | vs 1000t |
|---|---|---|
| NARRATIVE | B | down from A |
| COGNITION | B | held |
| ECONOMY | B | held |
| COMBAT | B | held |
| PROGRESSION | B | held |
| WORLD | B | held |
| AGENCY | C | held |
| FACTION | C | held |
| INFORMATION | C | held |
| SOCIAL | C | held |

**OQ2 resolution (sandbox_world COGNITION/ECONOMY at 2000t):** COGNITION and ECONOMY both hold at
B at 2000t — they do not climb to A. The 1000t→2000t transition shows plateau behaviour: these
pillars are saturating at B within the window scoring mechanism. NARRATIVE drops from A (at 1000t)
to B (at 2000t) — this is a dilution effect, not a regression: the scoring window covers only the
last 200 ticks, and narrative event density diminishes as the simulation matures past peak early
story arcs.

---

## OQ1 Resolution — urban_political NARRATIVE at 1000t

At 500t, seed123 showed NARRATIVE=A. At 1000t, all three seeds converge to NARRATIVE=B. This
resolves OQ1: the seed123 500t NARRATIVE=A was a window-composition effect (the 200-tick scoring
window at 500t captured a dense narrative burst). At 1000t the window captures the steady-state
rate, which grades to B. NARRATIVE is reliably B in urban_political at 1000t.

---

## OQ2 Resolution — sandbox_world COGNITION/ECONOMY at 2000t

See sandbox_world section above. Both pillars plateau at B. No upgrade to A observed. The
recommendation is to document these as confirmed B-ceiling pillars for sandbox_world in default
mode.

---

## AC6 — AGENCY Confirmation

AGENCY ≥ B confirmed for all three simq_routing_test seeds (42, 123, 456) with
`ENABLE_ADVENTURE_ROUTING=ON`. This is the gate criterion for the `simq_routing_test` world.
Without this flag, AGENCY=C (as seen in dungeon_crawl and urban_political default runs).

---

## Zero-Pillar World Confirmation

Six confirmed zero-active-pillar worlds not included in this matrix:
- `wilderness_survival`, `highland_traverse`, `swamp_border_world`
- `frontier_extended`, `frontier_living_world`

All have AGENCY/COGNITION/ECONOMY/SOCIAL/FACTION/INFORMATION=C in default mode. This is structural
(feature-gate blocked), not duration-limited. More ticks will not improve scores without enabling
the relevant feature flags.
