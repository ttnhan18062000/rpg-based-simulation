# Mechanism System Rollup View

Generated from `registries/mechanisms.yaml` + `registries/system_registry.jsonl` — regenerate with `make mechanism-system-rollup-view`. Do not hand-edit.

**What features the simulation actually has, and which are loose versus deep, without reading all 93 mechanisms individually** — declared system membership (`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION`), never derived from `depends_on` or any other edge.

**Counts only, never a single summary status.** A badge reading "combat: partial" would conceal that most members are unverified — the verification axis exists so that unverified renders visibly rather than being summarised away; a badge here would rebuild that failure one tier higher.

**Every rate is shown against the whole-registry baseline, never in isolation** — a raw per-system percentage looked informative in this program's own value investigation until checked against baseline and found statistically indistinguishable from it. The baseline below is computed live from the current registry, not a fixed snapshot.

**Reading caution — a system standing out from baseline may reflect recent attention, not a property of the simulation.** A system this session (or any prior one) spent a week investigating will show a higher bound/verified rate for that reason alone — the view describes where work has concentrated, not an independent discovery that some systems are inherently deeper than others. Read a high rate as "recently worked on," not as "this system is more real."

**"Bound, Unverified" is this view's most actionable column.** It splits `unverified` into two problems with different costs that the per-mechanism view doesn't separate: *bound-but-unverified* (a real `implemented_by` binding exists — the expensive part, locating the code, is already done, so this is the cheapest verification target available) versus *unbound-and-unverified* (`unverified` minus this column — we don't even know where to look yet, and investigation has to happen before verification can start).

**Baseline (all 93 mechanisms)**: 55 bound (59.1%), 48 verified (51.6% — 9 runtime, 39 static), 45 unverified (20 of those bound-but-unverified). State breakdown: done 51, partial 12, gap 11, orphan 10, gated 7, skeleton 2.

| System | Mechanisms | Bound (vs baseline) | Verified (vs baseline) | Bound, Unverified | done | partial | gap | orphan | gated | skeleton |
|---|---|---|---|---|---|---|---|---|---|---|
| `cognition` | 20 | 18/20 (90.0%, +30.9pt vs baseline) | 13/20 (65.0%, +13.4pt vs baseline) [0 runtime, 13 static] | 7 | 10 | 0 | 1 | 4 | 4 | 1 |
| `combat` | 8 | 8/8 (100.0%, +40.9pt vs baseline) | 7/8 (87.5%, +35.9pt vs baseline) [4 runtime, 3 static] | 1 | 6 | 1 | 0 | 1 | 0 | 0 |
| `economy` | 8 | 1/8 (12.5%, -46.6pt vs baseline) | 0/8 (0.0%, -51.6pt vs baseline) [0 runtime, 0 static] | 1 | 5 | 1 | 1 | 1 | 0 | 0 |
| `faction` | 13 | 3/13 (23.1%, -36.1pt vs baseline) | 4/13 (30.8%, -20.8pt vs baseline) [0 runtime, 4 static] | 1 | 7 | 2 | 3 | 0 | 0 | 1 |
| `progression` | 15 | 13/15 (86.7%, +27.5pt vs baseline) | 14/15 (93.3%, +41.7pt vs baseline) [3 runtime, 11 static] | 0 | 8 | 4 | 1 | 0 | 2 | 0 |
| `social` | 12 | 6/12 (50.0%, -9.1pt vs baseline) | 3/12 (25.0%, -26.6pt vs baseline) [0 runtime, 3 static] | 4 | 5 | 2 | 3 | 2 | 0 | 0 |
| `world` | 25 | 12/25 (48.0%, -11.1pt vs baseline) | 10/25 (40.0%, -11.6pt vs baseline) [2 runtime, 8 static] | 9 | 15 | 3 | 3 | 3 | 1 | 0 |
| `unassigned` | 0 | 0/0 (n/a) | 0/0 (n/a) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

`unassigned` mechanism count is 0 — a mechanism with no declared system renders here explicitly rather than being silently dropped, same discipline as `mechanisms_by_system()`'s own `"unassigned"` key.
