# Mechanism System Rollup View

Generated from `registries/mechanisms.yaml` + `registries/system_registry.jsonl` — regenerate with `make mechanism-system-rollup-view`. Do not hand-edit.

**What features the simulation actually has, and which are loose versus deep, without reading all 93 mechanisms individually** — declared system membership (`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION`), never derived from `depends_on` or any other edge.

**Counts only, never a single summary status.** A badge reading "combat: partial" would conceal that most members are unverified — the verification axis exists so that unverified renders visibly rather than being summarised away; a badge here would rebuild that failure one tier higher.

**Every rate is shown against the whole-registry baseline, never in isolation** — a raw per-system percentage looked informative in this program's own value investigation until checked against baseline and found statistically indistinguishable from it. The baseline below is computed live from the current registry, not a fixed snapshot.

**Reading caution — a system standing out from baseline may reflect recent attention, not a property of the simulation.** A system this session (or any prior one) spent a week investigating will show a higher bound/verified rate for that reason alone — the view describes where work has concentrated, not an independent discovery that some systems are inherently deeper than others. Read a high rate as "recently worked on," not as "this system is more real."

**"Bound, Unverified" is this view's most actionable column.** It splits `unverified` into two problems with different costs that the per-mechanism view doesn't separate: *bound-but-unverified* (a real `implemented_by` binding exists — the expensive part, locating the code, is already done, so this is the cheapest verification target available) versus *unbound-and-unverified* (`unverified` minus this column — we don't even know where to look yet, and investigation has to happen before verification can start).

**Baseline (all 93 mechanisms)**: 34 bound (36.6%), 33 verified (35.5% — 9 runtime, 24 static), 60 unverified (20 of those bound-but-unverified). State breakdown: done 52, partial 11, gap 11, orphan 9, gated 8, skeleton 2.

| System | Mechanisms | Bound (vs baseline) | Verified (vs baseline) | Bound, Unverified | done | partial | gap | orphan | gated | skeleton |
|---|---|---|---|---|---|---|---|---|---|---|
| `cognition` | 21 | 10/21 (47.6%, +11.1pt vs baseline) | 7/21 (33.3%, -2.2pt vs baseline) [0 runtime, 7 static] | 7 | 10 | 0 | 1 | 4 | 5 | 1 |
| `combat` | 7 | 5/7 (71.4%, +34.9pt vs baseline) | 5/7 (71.4%, +35.9pt vs baseline) [4 runtime, 1 static] | 1 | 5 | 1 | 0 | 1 | 0 | 0 |
| `economy` | 8 | 1/8 (12.5%, -24.1pt vs baseline) | 0/8 (0.0%, -35.5pt vs baseline) [0 runtime, 0 static] | 1 | 5 | 1 | 1 | 1 | 0 | 0 |
| `faction` | 13 | 3/13 (23.1%, -13.5pt vs baseline) | 4/13 (30.8%, -4.7pt vs baseline) [0 runtime, 4 static] | 1 | 7 | 2 | 3 | 0 | 0 | 1 |
| `progression` | 15 | 4/15 (26.7%, -9.9pt vs baseline) | 8/15 (53.3%, +17.8pt vs baseline) [3 runtime, 5 static] | 0 | 9 | 3 | 1 | 0 | 2 | 0 |
| `social` | 12 | 4/12 (33.3%, -3.2pt vs baseline) | 1/12 (8.3%, -27.2pt vs baseline) [0 runtime, 1 static] | 4 | 6 | 2 | 3 | 1 | 0 | 0 |
| `world` | 25 | 11/25 (44.0%, +7.4pt vs baseline) | 9/25 (36.0%, +0.5pt vs baseline) [2 runtime, 7 static] | 9 | 15 | 3 | 3 | 2 | 2 | 0 |
| `unassigned` | 0 | 0/0 (n/a) | 0/0 (n/a) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

`unassigned` mechanism count is 0 — a mechanism with no declared system renders here explicitly rather than being silently dropped, same discipline as `mechanisms_by_system()`'s own `"unassigned"` key.
