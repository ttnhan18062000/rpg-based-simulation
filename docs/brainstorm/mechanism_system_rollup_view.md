# Mechanism System Rollup View

Generated from `registries/mechanisms.yaml` + `registries/system_registry.jsonl` — regenerate with `make mechanism-system-rollup-view`. Do not hand-edit.

**What features the simulation actually has, and which are loose versus deep, without reading all 93 mechanisms individually** — declared system membership (`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION`), never derived from `depends_on` or any other edge.

**Counts only, never a single summary status.** A badge reading "combat: partial" would conceal that most members are unverified — the verification axis exists so that unverified renders visibly rather than being summarised away; a badge here would rebuild that failure one tier higher.

**Every rate is shown against the whole-registry baseline, never in isolation** — a raw per-system percentage looked informative in this program's own value investigation until checked against baseline and found statistically indistinguishable from it. The baseline below is computed live from the current registry, not a fixed snapshot.

**Reading caution — a system standing out from baseline may reflect recent attention, not a property of the simulation.** A system this session (or any prior one) spent a week investigating will show a higher bound/verified rate for that reason alone — the view describes where work has concentrated, not an independent discovery that some systems are inherently deeper than others. Read a high rate as "recently worked on," not as "this system is more real."

**"Bound, Unverified" is this view's most actionable column.** It splits `unverified` into two problems with different costs that the per-mechanism view doesn't separate: *bound-but-unverified* (a real `implemented_by` binding exists — the expensive part, locating the code, is already done, so this is the cheapest verification target available) versus *unbound-and-unverified* (`unverified` minus this column — we don't even know where to look yet, and investigation has to happen before verification can start).

**Baseline (all 93 mechanisms)**: 76 bound (81.7%), 82 verified (88.2% — 9 runtime, 73 static, 11.0% of verified is runtime), 11 unverified (0 of those bound-but-unverified). State breakdown: done 48, partial 12, gap 12, orphan 12, gated 7, skeleton 2.

**Runtime Share is a property of the verification method, not of coverage — track it separately.** `Verified` counts mechanisms confirmed by *any* instrument; `code_trace` (the code says it should work) and `scenario`/`corpus_run` (the simulation actually did it) are not interchangeable evidence, and a batch of code_trace-only re-confirmations can raise `Verified` while silently lowering `Runtime Share` — exactly what happened in `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` (batch 3 of the unbound-claims program), whose 20 new `code_trace` verifications moved the registry-wide runtime share from 27% to 11.0% while `Verified` itself grew. Neither number tells the whole story alone.

| System | Mechanisms | Bound (vs baseline) | Verified (vs baseline) | Runtime Share of Verified (vs baseline) | Bound, Unverified | done | partial | gap | orphan | gated | skeleton |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `cognition` | 20 | 18/20 (90.0%, +8.3pt vs baseline) | 20/20 (100.0%, +11.8pt vs baseline) [0 runtime, 20 static] | 0/20 (0.0%, -11.0pt vs baseline) | 0 | 10 | 0 | 1 | 4 | 4 | 1 |
| `combat` | 8 | 8/8 (100.0%, +18.3pt vs baseline) | 8/8 (100.0%, +11.8pt vs baseline) [4 runtime, 4 static] | 4/8 (50.0%, +39.0pt vs baseline) | 0 | 6 | 1 | 0 | 1 | 0 | 0 |
| `economy` | 8 | 7/8 (87.5%, +5.8pt vs baseline) | 7/8 (87.5%, -0.7pt vs baseline) [0 runtime, 7 static] | 0/7 (0.0%, -11.0pt vs baseline) | 0 | 4 | 1 | 1 | 2 | 0 | 0 |
| `faction` | 13 | 9/13 (69.2%, -12.5pt vs baseline) | 9/13 (69.2%, -18.9pt vs baseline) [0 runtime, 9 static] | 0/9 (0.0%, -11.0pt vs baseline) | 0 | 6 | 3 | 3 | 0 | 0 | 1 |
| `progression` | 15 | 13/15 (86.7%, +4.9pt vs baseline) | 14/15 (93.3%, +5.2pt vs baseline) [3 runtime, 11 static] | 3/14 (21.4%, +10.5pt vs baseline) | 0 | 8 | 4 | 1 | 0 | 2 | 0 |
| `social` | 12 | 8/12 (66.7%, -15.1pt vs baseline) | 9/12 (75.0%, -13.2pt vs baseline) [0 runtime, 9 static] | 0/9 (0.0%, -11.0pt vs baseline) | 0 | 5 | 2 | 3 | 2 | 0 | 0 |
| `world` | 25 | 20/25 (80.0%, -1.7pt vs baseline) | 22/25 (88.0%, -0.2pt vs baseline) [2 runtime, 20 static] | 2/22 (9.1%, -1.9pt vs baseline) | 0 | 14 | 2 | 4 | 4 | 1 | 0 |
| `unassigned` | 0 | 0/0 (n/a) | 0/0 (n/a) | 0/0 (n/a) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

`unassigned` mechanism count is 0 — a mechanism with no declared system renders here explicitly rather than being silently dropped, same discipline as `mechanisms_by_system()`'s own `"unassigned"` key.
