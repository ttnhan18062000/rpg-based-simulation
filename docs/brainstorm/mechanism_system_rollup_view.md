# Mechanism System Rollup View

Generated from `registries/mechanisms.yaml` + `registries/system_registry.jsonl` — regenerate with `make mechanism-system-rollup-view`. Do not hand-edit.

**What features the simulation actually has, and which are loose versus deep, without reading all 93 mechanisms individually** — declared system membership (`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION`), never derived from `depends_on` or any other edge.

**Counts only, never a single summary status.** A badge reading "combat: partial" would conceal that most members are unverified — the verification axis exists so that unverified renders visibly rather than being summarised away; a badge here would rebuild that failure one tier higher.

**Every rate is shown against the whole-registry baseline, never in isolation** — a raw per-system percentage looked informative in this program's own value investigation until checked against baseline and found statistically indistinguishable from it. The baseline below is computed live from the current registry, not a fixed snapshot.

**Baseline (all 93 mechanisms)**: 33 bound (35.5%), 25 verified (26.9% — 9 runtime, 16 static), 68 unverified. State breakdown: done 53, partial 11, gap 11, orphan 8, gated 8, skeleton 2.

| System | Mechanisms | Bound (vs baseline) | Verified (vs baseline) | done | partial | gap | orphan | gated | skeleton |
|---|---|---|---|---|---|---|---|---|---|
| `cognition` | 21 | 9/21 (42.9%, +7.4pt vs baseline) | 5/21 (23.8%, -3.1pt vs baseline) [0 runtime, 5 static] | 11 | 0 | 1 | 3 | 5 | 1 |
| `combat` | 7 | 5/7 (71.4%, +35.9pt vs baseline) | 5/7 (71.4%, +44.5pt vs baseline) [4 runtime, 1 static] | 5 | 1 | 0 | 1 | 0 | 0 |
| `economy` | 8 | 1/8 (12.5%, -23.0pt vs baseline) | 0/8 (0.0%, -26.9pt vs baseline) [0 runtime, 0 static] | 5 | 1 | 1 | 1 | 0 | 0 |
| `faction` | 13 | 3/13 (23.1%, -12.4pt vs baseline) | 3/13 (23.1%, -3.8pt vs baseline) [0 runtime, 3 static] | 7 | 2 | 3 | 0 | 0 | 1 |
| `progression` | 15 | 4/15 (26.7%, -8.8pt vs baseline) | 6/15 (40.0%, +13.1pt vs baseline) [3 runtime, 3 static] | 9 | 3 | 1 | 0 | 2 | 0 |
| `social` | 12 | 4/12 (33.3%, -2.2pt vs baseline) | 0/12 (0.0%, -26.9pt vs baseline) [0 runtime, 0 static] | 6 | 2 | 3 | 1 | 0 | 0 |
| `world` | 25 | 11/25 (44.0%, +8.5pt vs baseline) | 7/25 (28.0%, +1.1pt vs baseline) [2 runtime, 5 static] | 15 | 3 | 3 | 2 | 2 | 0 |
| `unassigned` | 0 | 0/0 (n/a) | 0/0 (n/a) | 0 | 0 | 0 | 0 | 0 | 0 |

`unassigned` mechanism count is 0 — a mechanism with no declared system renders here explicitly rather than being silently dropped, same discipline as `mechanisms_by_system()`'s own `"unassigned"` key.
