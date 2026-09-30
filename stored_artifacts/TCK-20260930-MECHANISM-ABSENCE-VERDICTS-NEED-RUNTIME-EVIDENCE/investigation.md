---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE
artifact_type: investigation
tags: [data-quality, process-improvement]
---

# Investigation — TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE

## Enumeration (recounted on origin/main 833b60306)
`registries/mechanisms.yaml` has 93 mechanisms. `code_trace`+`contradicted` entries: exactly 7 —
`breakthrough_bonuses` (partial), `commitment_betrayal` (orphan), `betrayal_siege_war` (partial),
`demographic_cohort_cycle` (done), `chronicle` (orphan), `equipment_scoring` (orphan), `camp` (done).
The ticket's count of 7 held.

## Key finding: the registry's own header already forbids this combination
`registries/mechanisms.yaml` header: "`contradicted` is reserved for ... `state: done` with a
*runtime* instrument finding the claimed behavior doesn't actually happen", and "a `code_trace`
confirming an already-`orphan` mechanism really doesn't fire is `verdict: observed`". So
`code_trace`+`contradicted` was never a legal combination by the registry's own semantics; the
validator simply did not enforce it. That makes the Scope 2 rule a one-line validator invariant
keyed on verdict + instrument; no new schema field (`claim:`) is needed.

## Instruments available
`registry.py`: `RUNTIME_INSTRUMENTS = {census, scenario, corpus_run}`, `STATIC_INSTRUMENTS =
{code_trace}`. `tools/execution_census.py corpus-run` (branch coverage over 21 corpus worlds) was
tried first and abandoned: under coverage each world took minutes (watchdog budget trips) and
dataclass construction (`BetrayalRecord`, `Betrayal`) is not visible as line coverage. A counting
probe (`runtime_probe.py`) that wraps the seven mechanisms' entry points ran all 21 worlds x 300
ticks in 54 s and answers the construction/call questions directly.

## Runtime results (21 worlds x 300 ticks, seed 42; raw: `runtime_probe_output.jsonl`)
| Mechanism | Observation | Verdict |
|---|---|---|
| camp | 19 CampState seeded in 14/21 worlds; process_camps ran in all 21; all 19 camps changed state | observed (old claim false) |
| demographic_cohort_cycle | cohorts seeded 21/21; cycle ran 63x; 0 BIRTH/DEATH events; 30 MIGRATION events in 6 worlds; largest bracket seen 8 | contradicted (old reason false; births/deaths never fire) |
| breakthrough_bonuses | apply_bonuses called 0x; 0 entities with breakthroughs | observed (partial confirmed) |
| commitment_betrayal | BetrayalRecord constructed 0x | observed (orphan confirmed) |
| betrayal_siege_war | MilitaryConflictPhase.execute 6300x; Betrayal constructed 0x | observed (partial confirmed) |
| chronicle | ChronicleCompiler constructed 0x in tick runs | observed (orphan confirmed, sim-driven only) |
| equipment_scoring | 0 calls, inside or outside equipment.py | observed (orphan confirmed) |

Compile census (`compile_census.py`, `compile_census_output.txt`): camps in 14/21 worlds, cohorts
in 21/21.

## Pattern check for the `observed` direction (the ticket's "file a follow-up if" clause)
Of 7 static absence verdicts, the 2 about runtime **world data** ("no world seeds X") had a false
premise (`camp` is fully live; `demographic_cohort_cycle` is seeded but its births/deaths still
never fire, for a different reason); the 5 about static **call/construction** absence were all
confirmed at runtime. So the error is
specific to world-data absence claims, which the Scope 2 rule and the Scope 3 scoper rule now
cover. No pattern in `code_trace`+`observed` verdicts was found, so no follow-up is filed.

## Side findings
- `make mechanism-state-caller-check` (report-only, unchanged by this ticket) still flags
  `chronicle` as `orphan_with_callers` (3 caller files); the new note limits the runtime claim to
  tick-driven runs and points at the API-registry ticket for the request-time side.
- Probe correction: the first probe run matched any event category containing "POPULATION" and
  misread 30 `POPULATION_MIGRATION` events as births/deaths (caught by rpg-feature-planning's
  review). The probe now tallies exact category names. Result: 0 BIRTH/DEATH events, which
  matches rpg-feature-planning's `TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO`
  (on `rpg-planning-post-258`; largest bracket ever seen is 8, `net` needs 100).
  The cohort-total changes (dungeon_crawl 32 -> 29) are not attributed to `process_demographics`
  and are left to that ticket's owner.
- Premise-false tickets closed STALE-PREMISE by rpg-feature-planning: `791e6bf6b` (groundwork
  `f70f58706`).

## Docs Requiring Update
- `docs/brainstorm/mechanism_verification_view.md`, `mechanism_registry_view.md`,
  `mechanism_system_rollup_view.md`, `mechanism_registry.html` (regenerated via their generators)
- `docs/brainstorm/simulation_capabilities.html` (2 tier values via
  `make mechanism-capabilities-regenerate`)
