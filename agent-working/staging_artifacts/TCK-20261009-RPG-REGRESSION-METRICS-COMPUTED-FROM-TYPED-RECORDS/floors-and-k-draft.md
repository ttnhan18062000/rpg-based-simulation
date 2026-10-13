---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS
artifact_type: investigation
tags: []
---

# Floors and k for the outcome rows (draft for rpg-designer to confirm the fiction reasons)

Lives in code as `OUTCOME_THRESHOLDS` and `POOLED_THRESHOLDS` in `src/observability/rpg_gate_metrics.py`. `k` = standard errors a paired difference must exceed;
`floor` = the smallest change worth tracing, in the row's own unit. Neither is fitted to a measured baseline: the floor is a fiction statement, k = 2 is the
usual two-sigma line. A drift needs BOTH (|paired mean diff| > k x SE AND > floor), so noise on a stable metric and a tiny shift on a noisy one both stay quiet.

| row | unit | k | floor | fiction reason |
|---|---|---|---|---|
| O1.starvation_share | fraction of the group's first-tick population | 2 | 0.05 | a settlement notices when one more in twenty of a kind starves |
| O2.deaths (per cause) | deaths in a run | 2 | 2 | two more deaths of one cause in a run is a story; one is noise |
| O2.population (per sampled tick) | individuals alive | 2 | 3 | three more or fewer of a kind alive is a visible crowd change |
| O2.survivors (per group) | 1 if any alive at the last tick | 2 | 1 | a kind alive or gone in a seed is the whole difference |
| O2.seeds_with_survivors (pooled) | seeds | - | 1 | a seed more or fewer where a kind survives |
| O3.attacks_on_people | hits + kills by a wild meat-eater group on people | 2 | 3 | three more bites on villagers a run is the first sign a hunter stopped judging prey |
| O4.accepted (per source) | accepted resolver transfers | 2 | 5 | five more or fewer uses of a way is a change in how the kind lives |
| O5.coin_net / O5.coin_declared | coin | 2 | 25 | twenty-five coin is a day's wage; less is rounding of the economy |
| O6.feeding_kills | kills made to eat | 2 | 2 | two more kills made to eat in a run is a change in how it hunts |
| O6.kills_not_eaten | kills by wild meat-eaters minus feeding kills | 2 | 2 | two more kills left uneaten in a run is waste a kind would notice |

Groups are kind groups from the declared diet (`kind_group`), e.g. `meat`, `graze+plant`, `meat+plant+prepared`. "People" = a diet that includes `prepared`; "wild meat-eater" = a diet with `meat` and without `prepared`. Both are property tests, never a role or a name (D42, D46).

Questions for rpg-designer: (1) do the fiction reasons read right? (2) is "prepared in the diet" the right property for "people" (a kind that eats the inn's free meal)? (3) O7 (tick time) is the harness's cost document, not a row here: agreed?
