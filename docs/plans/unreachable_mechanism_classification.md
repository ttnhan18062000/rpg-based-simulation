---
status: active
layer: simulation
authority: P1
audience: agent
tags: [investigation, root-cause, corpus]
---

# Unreachable-Mechanism Classification — Verdicts for the 14-Ticket Corpus

**Filed 2026-09-30**, closing epic `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` (children
`TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER`, `TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED`,
`TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD`, `TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM`,
`TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY`, `TCK-20260930-UNREACHABLE-CLASSIFY-ROLLUP`). Method precedent:
`TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE` (PR #258). This is a classification, not a fix: **no `src/`, `tests/`, registry,
parity-ledger or other doc was changed by the epic**, and `registries/mechanisms.yaml` is byte-for-byte unchanged against `origin/main`.

Fourteen open tickets each said "real, wired code that does not run in any run we perform". They looked alike and were not:
across the 14 the causes were a dead producer, a live duplicate, a filter mismatch, a stale premise, a design gap and a horizon
condition. Each verdict below is recorded in the covered ticket's own body as well; this document is the index.

## Read this first — what these verdicts do and do not establish

**Every kernel measurement in this epic used one world and one seed: `frontier_living_world`, seed 42.** The verdicts are sound for what
they test, but they are not equally strong, and a reader should not treat the weaker ones as corpus-wide.

| Kind of claim | Verdicts that rest on it | How strong a single sample is |
|---|---|---|
| **Existence proof** — "this thing does exist / does happen" | `camp` and `demographic_cohort_cycle` `STALE-PREMISE` (a real compile produced 2 camps and non-empty cohorts); `PROFILE-API-PAYLOAD` `DEFECT` (the tool fails on import) | **Strong.** One counterexample falsifies "no world ever seeds this". Independently reproduced for the cohort case. |
| **Code-structure claim** — "nothing calls / reads / produces X" | the zero-caller and dead-producer verdicts, `PERCEPTION` | **Strong**, bounded by grep reach (dynamic dispatch was checked for; a runtime-only path could still hide). |
| **Absence / rate claim from a run** — "X did not happen in N ticks" | `COMBAT-GATE` boss-gate `CONDITION` (flag ON vs OFF both give first `world_boss` at tick 2101, peak trauma 21.26); `COGNITION-CAPACITY` (0 over-cap in 10,916 entity-checks); the influence run (59 deaths, 0 influence-shift calls) | **Weak.** One world, one seed, 1,500-3,000 ticks. A single sample cannot show a condition is absent elsewhere. |
| **Arithmetic** — "earliest possible tick is 2000" | `COMBAT-GATE` run-length `CONDITION` (`MATURITY_INTERVAL = 1000`, threshold `2.0`) | **Strong** for the horizon; the trauma side was met only in the one measured world. |
| **Inherited from the wave** — not re-measured here | `LAIR-REGION-TRAUMA` `CONDITION` (world-content), `CALAMITY-INTENSITY` `DEFECT` | As strong as the wave; the lair verdict rests on one region of one world. |

Two further limits: the 59 deaths in the influence run include non-combat deaths, so the `DEFEAT`-versus-`KILL` mechanism rests on
the code reads and the ticket's own earlier 20/20 instrumentation, not on that run; and the boss-gate A/B varies one flag, so it
shows the posture gate does not change the boss chain *in this world*.

## The axis, and the two outcomes it needed

`DEFECT` (a real wiring/guard/filter bug), `CONDITION` (correct and reachable, but our content or run length never supplies the
input), `UNDECLARED` (nothing settles which implementation or design is authoritative), `MISLABEL` (a registry/doc claim overstates
the code). The epic's AC-7 (do not force a ticket into the nearest bucket) was used **twice**:

- `STALE-PREMISE` — the ticket's factual premise is false today. Used for `camp` and `demographic_cohort_cycle`.
- `NO-MECHANISM` — the ticket describes a dead constant, not an unreachable mechanism. Used for `CALAMITY-RANDOM-CHANCE`.

No ticket resolved to `MISLABEL`, though two (`REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN`, `PERCEPTION`) carry a mislabel-shaped doc
mismatch as a symptom of an `UNDECLARED` state. The shared-root-cause hypothesis was tested by the wave and again here and was
**not** supported: the causes differ ticket by ticket.

## Verdict table (all 14)

Ticket IDs are given in full, one per row. "Where" is the covered ticket's own Implementation Notes unless stated.

| # | Covered ticket | Verdict | Evidence in one line | Source |
|---|---|---|---|---|
| 1 | `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` | `DEFECT` | `apply_calamity_consequences` has no production caller (freshness grep re-run) | wave `J1`, PR #258; recorded in `T04` |
| 2 | `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT` | `NO-MECHANISM` | one grep hit (the declaration); introduced 2026-05-18, never connected; docs already say dead | `T01` |
| 3 | `TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS` | `UNDECLARED` | zero callers, but live `TownResolutionSystem.resolve()` (`pipeline.py:339`) does the same taxation and a conquered-region penalty with different cadence and numbers | `T01` |
| 4 | `TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS` | `DEFECT` | executed: `ImportError: cannot import name 'EngineManager'`; `SimulationConfig` undefined | `T01` |
| 5 | `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION` | `STALE-PREMISE` | real compile of `frontier_living_world` yields 2 `CampState` (`goblin_camp_place`, `wolf_den_nest`); content committed 2026-09-08 | `T02` |
| 6 | `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED` | `STALE-PREMISE` | same compile: 6 of 7 regions have non-empty cohorts; `spawn_region` and `RegionSpec.id` agree; reproduced independently | `T02` |
| 7 | `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` | `UNDECLARED` (split) | `enemy_data`: no producer anywhere, symptom of #8; `region_data`: `SCOUT_LOCATION` declared in 3 tables, absent from `generator.py` | `T02` |
| 8 | `TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER` | `UNDECLARED` | `_ENEMY_DANGER` fallback is the live path on every combat estimate; nothing produces per-kind danger; no doc declares it should | `T02` |
| 9 | `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` | `DEFECT` | `lifecycle.py:202` accepts `("KILL","PERMADEATH")`, combat emits `"DEFEAT"`; 59 deaths, 0 influence-shift calls in 1,500 ticks | `T03` |
| 10 | `TCK-20260914-REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS` | `DEFECT` | scar creators have no callers (re-verified); Defect 2 stale as written | `T03` |
| 11 | `TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES` | `UNDECLARED` | behaviour declared in code as PERF-007; consequence unadjudicated; 0 over-cap in 10,916 entity-checks | `T03` |
| 12 | `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` | `CONDITION` (world content) | `moon_cave` spatially isolated from every hostile faction; `trauma_score == 0.0` over 5,000 ticks | wave `J2`, PR #258; recorded in `T04` |
| 13 | `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE` (boss-gate half) | `CONDITION` (corpus run length) | posture flag ON and OFF both spawn the first `world_boss` at tick 2101; earliest possible tick is 2000 | `T04` |
| 14 | `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` | `UNDECLARED` | two authoritative descriptions conflict (Bible §5 vs perception contract); phase also lacks a `world_signals` producer | `T05` |

Totals: `DEFECT` 4, `UNDECLARED` 5, `CONDITION` 2, `STALE-PREMISE` 2, `NO-MECHANISM` 1. Only 2 of the 14 (#5, #6) were the
"never seeded" shape the epic's grouping assumed, and both were false.

## Premises that were wrong or incomplete (worth more than the labels)

1. **#3, the orphaned sovereignty service.** The ticket called it "a real, separate capability never wired in." Taxation and the
   conquered-region penalty are already live in `TownResolutionSystem` with the same tax constants (`2.0` per entity, `10.0` per
   building) on a different cadence. **Wiring the orphan as the ticket implied would double-tax.** This is the single highest-value
   correction in the epic.
2. **#5 and #6.** Both cite a `registries/mechanisms.yaml` verdict dated 2026-09-16 that was contradicted by content and code
   shipped on 2026-09-08 and 2026-08-31 respectively.
3. **#11.** "Undocumented as a design choice" is partly wrong: `capacity_enforcement.py:23-24` declares it (PERF-007). What is
   unadjudicated is the consequence, and the measured run found no over-cap entity.
4. **#10.** Defect 2 no longer holds as written: `generate_crafting_blockers` emits real-material blockers with production
   callers (`blacksmith.py:190,207`). Whether that path is reached alongside a matching lead was not measured.
5. **#14.** "Nothing declares" is replaced by "two authoritative descriptions disagree", and the phase would not work if simply
   wired: its input has no production producer and its output has no reader.

## Ranked fix order — the `DEFECT` subset only

The four `DEFECT`s are **not one kind of fix**, so they are not forced onto one list. Nothing here is scheduled by this document.

**Track A — the diagnosis is complete; the change is small.**
1. `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` — first, because it has the most waiting consumers: `RegionState.influence`
   has never moved, and the sovereignty-threshold unification (`TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT`) already
   tuned constants against it. **Caveat on "one-line filter fix":** the code change is small but the blast radius is not. It would
   make dynamic conquest and liberation fire for the first time in this codebase's history, in every world, and the ticket's own
   open design question (does a non-lethal `DEFEAT` mean the same as a `KILL` for sovereignty?) has to be answered first. It ranks
   first to be *decided*, and it needs a SimQ re-baseline afterwards.
2. `TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS` — trivially small, tools-only, no gameplay effect, independent of everything.

**Track B — a wire-or-delete design call comes first; not comparable to Track A, and not ranked against each other.**
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` — decide whether the dead producer should run. Its registry-side write is
  already routed to `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` (adjacent, not merged). Wiring it changes calamity
  behaviour.
- `TCK-20260914-REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS` — decide where scars should be created (raids, battlefields) or delete the
  chain; re-check Defect 2 before scoping the fix.

## `CONDITION` set — split by owner (epic AC-6)

| Ticket | Kind | Why | Proposed owner |
|---|---|---|---|
| `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` | **world content** | more ticks cannot help; the region records no deaths because of its geometry | the world-content owner of the module defining `moon_cave` and its neighbours; no named person or session exists in the corpus |
| `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE` (boss-gate half) | **corpus run length** | reachable, but a run under ~2,000 ticks cannot spawn a boss | route to `TCK-20260915-SIMQ-CORPUS-BLIND-TO-SCALE-DEPENDENT-BEHAVIOR` (open); do not absorb it here |

**The epic's open question — is a run-length `CONDITION` a finding about the code or about the corpus? Recommendation: the corpus.**
The code is correct and the horizon arithmetic is exact; what is missing is a corpus that runs long enough to see it. The wave's
aging/succession result (~20.16M ticks against 1k-5k-tick runs) is the same kind of finding and belongs with it. This is a
recommendation for the ticket's owner to accept, not a decision taken here.

## `UNDECLARED` set — decisions that need a person

Each of these needs a design decision before any code change; none is made here.

| Ticket | The decision | Note |
|---|---|---|
| #3 `REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN` | keep `TownResolutionSystem` as authoritative and delete the orphan, or reconcile the two | wiring the orphan on top of the live path would double-tax |
| #7, #8 `CAPABILITY-CONTEXT` / `NO-MECHANISM-RECORDS` | build combat-outcome learning for per-kind danger, or document the hardcoded table as accepted; and for `region_data`, build `SCOUT_LOCATION` generation or remove the scaffolding | #7's `enemy_data` half is #8's symptom, not a second question |
| #11 `COGNITION-CAPACITY-ENFORCEMENT` | accept PERF-007's consequence, or make enforcement unconditional | measured impact in the sampled run: none |
| #14 `PERCEPTION-UPDATE-PHASE` | which perception is canonical; five questions written into the covered ticket | needs the user or the roadmap owner; the "Bible wins" rule was deliberately not applied |

## Follow-ups this epic found and deliberately did not do

Named so they are not lost. **None has been actioned and none has a ticket**, except where stated; each is listed with the owner who
should take it.

| # | Follow-up | Proposed owner | Note |
|---|---|---|---|
| F1 | `docs/world/regional_sovereignty_runtime_contract.md` names `regional_sovereignty.py` as the taxation source and cites a test with no tax assertion | owner of the sovereignty docs | **blocked on the #3 decision** — it cannot be corrected truthfully until it is settled which implementation is authoritative |
| F2 | `docs/world/raid_boss_camp_contract.md` still says no content sets `creature_kind` (true at its 2026-09-04 verification, false since 2026-09-08) | owner of the world docs | independent; a straightforward correction |
| F3 | `docs/plans/world_composition_precondition_gap_finding.md` §5 (camp) and §6 (demographic cohort) still read "confirmed"; both are false today, and its "five confirmed instances" headline no longer holds; §2 predates the wave's `DEFECT` verdict | owner of that finding | it is the pattern document this corpus was grouped from, so its thesis needs re-checking, not just two edits |
| F4 | `registries/mechanisms.yaml` `camp` and `demographic_cohort_cycle` entries carry the stale 2026-09-16 verdicts | the registry owner | not verified whether an open ticket already owns verdict corrections for these two; `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` owns `implemented_by` residue, which is a different thing |
| F5 | `TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES` is `P1`; its own measurement (0 over-cap in 10,916 entity-checks, one world/seed) undercuts that | whoever triages that ticket | **recommendation: lower to `P2`, with the single-sample limit stated.** The priority is not changed here |
| F6 | Process finding, corrected by its owner: the two registry verdicts (`camp`, `demographic_cohort_cycle`) were **wrong when written**, not stale — the contradicting changes (2026-08-31 seeding, 2026-09-08 content) predate the 2026-09-16 verdicts and sit outside the entries' `implemented_by` code. Both are `instrument: code_trace` verdicts asserting runtime world-data absence, which reading code cannot prove; the two tickets then quoted them as premises without naming the instrument. `make premise-staleness-check` checks that cited paths resolve, not that the claim is true. | `agent-working-design` | filed by them as `TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE` (re-verify the 7 `code_trace` + `contradicted` entries, require a runtime instrument for absence verdicts); they mark the two premise-false tickets with dated notes, and closing or re-scoping those tickets stays with the RPG side |

## Acceptance criteria — status

| Epic AC | Status |
|---|---|
| 1 — each of the 14 has exactly one verdict | Met (table above). |
| 2 — every verdict cites evidence | Met; strength varies, see "Read this first". |
| 3 — the two wave-assessed tickets recorded, not re-investigated, citing PR #258 | Met (#1, #12). |
| 4 — `registries/mechanisms.yaml` unchanged | Met, verified against `origin/main`. |
| 5 — no `src/` behaviour change | Met, verified against `origin/main`. |
| 6 — `CONDITION` set split by owner | Met (two tickets, two owners). |
| 7 — resistant tickets recorded, not forced | Used for #2, #5, #6 and for the "decision needs a human" outcome of #14. |

## Not done

Fixing anything; choosing a perception model; correcting F1-F4; changing any priority; creating follow-up tickets; pushing or opening
a PR. Whether the state-hash surface would include `PerceptionModel` if it were wired was not checked.
