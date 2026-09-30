# Mechanism System Rollup View

Generated from `registries/mechanisms.yaml` + `registries/system_registry.jsonl` — regenerate with `make mechanism-system-rollup-view`. Do not hand-edit.

**What features the simulation actually has, and which are loose versus deep, without reading all 93 mechanisms individually** — declared system membership (`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION`), never derived from `depends_on` or any other edge.

**Counts only, never a single summary status.** A badge reading "combat: partial" would conceal that most members are unverified — the verification axis exists so that unverified renders visibly rather than being summarised away; a badge here would rebuild that failure one tier higher.

**Every rate is shown against the whole-registry baseline, never in isolation** — a raw per-system percentage looked informative in this program's own value investigation until checked against baseline and found statistically indistinguishable from it. The baseline below is computed live from the current registry, not a fixed snapshot.

**Reading caution — a system standing out from baseline may reflect recent attention, not a property of the simulation.** A system this session (or any prior one) spent a week investigating will show a higher bound/verified rate for that reason alone — the view describes where work has concentrated, not an independent discovery that some systems are inherently deeper than others. Read a high rate as "recently worked on," not as "this system is more real."

**"Bound, Unverified" is this view's most actionable column.** It splits `unverified` into two problems with different costs that the per-mechanism view doesn't separate: *bound-but-unverified* (a real `implemented_by` binding exists — the expensive part, locating the code, is already done, so this is the cheapest verification target available) versus *unbound-and-unverified* (`unverified` minus this column — we don't even know where to look yet, and investigation has to happen before verification can start).

**Baseline (all 104 mechanisms)**: 93 bound (89.4%), 95 verified (91.3% — 45 runtime, 50 static, 47.4% of verified is runtime), 9 unverified (0 of those bound-but-unverified). State breakdown: done 54, partial 14, gap 11, orphan 16, gated 9, skeleton 0.

**Runtime Share is a property of the verification method, not of coverage — track it separately.** `Verified` counts mechanisms confirmed by *any* instrument; `code_trace` (the code says it should work) and `scenario`/`corpus_run` (the simulation actually did it) are not interchangeable evidence, and a batch of code_trace-only re-confirmations can raise `Verified` while silently lowering `Runtime Share` — exactly what happened in `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` (batch 3 of the unbound-claims program), whose 20 new `code_trace` verifications moved the registry-wide runtime share from 27% to 47.4% while `Verified` itself grew. Neither number tells the whole story alone.

| System | Mechanisms | Bound (vs baseline) | Verified (vs baseline) | Runtime Share of Verified (vs baseline) | Bound, Unverified | done | partial | gap | orphan | gated | skeleton |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `cognition` | 22 | 21/22 (95.5%, +6.0pt vs baseline) | 22/22 (100.0%, +8.7pt vs baseline) [14 runtime, 8 static] | 14/22 (63.6%, +16.3pt vs baseline) | 0 | 10 | 0 | 1 | 6 | 5 | 0 |
| `combat` | 8 | 8/8 (100.0%, +10.6pt vs baseline) | 8/8 (100.0%, +8.7pt vs baseline) [4 runtime, 4 static] | 4/8 (50.0%, +2.6pt vs baseline) | 0 | 6 | 1 | 0 | 1 | 0 | 0 |
| `economy` | 12 | 11/12 (91.7%, +2.2pt vs baseline) | 11/12 (91.7%, +0.3pt vs baseline) [5 runtime, 6 static] | 5/11 (45.5%, -1.9pt vs baseline) | 0 | 8 | 1 | 1 | 2 | 0 | 0 |
| `faction` | 14 | 11/14 (78.6%, -10.9pt vs baseline) | 11/14 (78.6%, -12.8pt vs baseline) [3 runtime, 8 static] | 3/11 (27.3%, -20.1pt vs baseline) | 0 | 7 | 3 | 3 | 1 | 0 | 0 |
| `progression` | 15 | 15/15 (100.0%, +10.6pt vs baseline) | 15/15 (100.0%, +8.7pt vs baseline) [8 runtime, 7 static] | 8/15 (53.3%, +6.0pt vs baseline) | 0 | 8 | 5 | 0 | 0 | 2 | 0 |
| `social` | 12 | 9/12 (75.0%, -14.4pt vs baseline) | 9/12 (75.0%, -16.3pt vs baseline) [2 runtime, 7 static] | 2/9 (22.2%, -25.1pt vs baseline) | 0 | 5 | 2 | 3 | 2 | 0 | 0 |
| `world` | 34 | 30/34 (88.2%, -1.2pt vs baseline) | 31/34 (91.2%, -0.2pt vs baseline) [15 runtime, 16 static] | 15/31 (48.4%, +1.0pt vs baseline) | 0 | 20 | 3 | 4 | 5 | 2 | 0 |
| `unassigned` | 0 | 0/0 (n/a) | 0/0 (n/a) | 0/0 (n/a) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

`unassigned` mechanism count is 0 — a mechanism with no declared system renders here explicitly rather than being silently dropped, same discipline as `mechanisms_by_system()`'s own `"unassigned"` key.
