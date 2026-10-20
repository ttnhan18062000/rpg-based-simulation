---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, regression, simulation-quality]
---

# rpg gate baseline: format, staleness and re-baseline

Child 2 of `TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC`. The authoritative description is the docstring of
`tools/test_architecture/rpg_gate_baseline.py`; this page is the short orientation. Testing owns the format and the rules; rpg owns the
content (metric ids, groups, values), the config and the stop lines. The module never names a metric id.

## Files

- One immutable file per version, `rpg_gate_v<N>.json`, in `tests/simulation_quality/rpg_gate/baselines/` (the mutation-baseline convention).
  A re-baseline writes `v<N+1>`; an existing file is never modified (the writer opens with exclusive create).
- Each file carries provenance (commit SHA, harness hash, worlds, seeds, ticks, recorded_at, stale_after), the metric rows, the milestone id and
  a re-baseline record (null for version 1).

## Dual reference

A run is compared with the LAST baseline and the FIRST baseline of the current milestone. Re-baselining every time would otherwise hide a slow drift.

## Thresholds come from the reference

The thresholds recorded in a baseline are the thresholds that baseline is judged with (TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD; the designer's condition for the relative O2.population floor). For each reference (`last` and `milestone-first` separately) the report judges an outcome row's drift with that reference row's own `k` and `floor`, never the candidate's:

- A run row needs a numeric `k` and `floor` in the reference row, a pooled row a numeric `floor`. Without them that reference is `no-data`, reason `contract_error`, detail `reference row has no recorded threshold`; there is no fallback to the candidate's values, and the other reference is judged as usual. The markdown names the cause per reference (`[contract_error] reference row has no recorded threshold`), and when no reference is judged the finding itself carries `contract_error`, so the header's no-data tally counts it.
- When the candidate's `k`, `floor` or `oracle` differ from the reference row's, the reference result carries `threshold_moved: {field: {candidate, reference}}` for the fields that differ, and the markdown shows `threshold moved: floor 3.0 -> 9.0` on the row. An `oracle` counts whenever either side carries one (a missing side is null). A moved threshold is reported, not used, and does not change the state.
- A relative floor (O2.population: `max(3.0, 0.10 * tick-0 population)`) is computed by the metric module from its own run set, so it is fixed once recorded; it changes only through a re-baseline (`baseline_change_policy.md`). The module never reads baseline artifacts.
- The within-run-set rule is unchanged: one `k` / `floor` / `oracle` per (world, id, group) across a world's documents, else `contract_error`. The candidate is unchanged: a new baseline records the candidate's own thresholds.

### A relative floor

A seed document cannot know a floor that depends on the other seeds' outcomes, so a run outcome row may carry a numeric `floor_rel` (`0 < floor_rel <= 1`) beside its absolute `floor`. The module never reads a baseline; the **candidate** applies the relative part once, from the run set it records (TCK-20261020-RPG-GATE-CANDIDATE-RECORDS-A-RELATIVE-FLOOR):

- `floor = max(floor, floor_rel * mean(per_seed))`, recorded together with `floor_base` (the document's own floor) and `floor_rel`. Per-seed values `[40, 50, 60]` with floor 3 and `floor_rel` 0.10 record floor 5.0; `[5, 5, 5]` record 3.0.
- The report judges on the reference row's recorded `floor`, unchanged.
- `threshold_moved` compares the candidate documents' `floor` with the reference's `floor_base` (its `floor` when the reference has no `floor_rel`), and `floor_rel` when either side has one, so a computed relative floor never shows as moved; a changed `floor_rel` or base does.
- Contract errors: `floor_rel` on a pooled row, or outside `(0, 1]` or not a number. The candidate refuses and the report gives `no-data` / `contract_error`. `floor_rel` joins `k`, `floor` and `oracle` in the one-value-per-`(world, id, group)` check. A reference row with `floor_rel` but no numeric `floor` is the existing "no recorded threshold" contract error.
- Baseline lint: `floor_base` and `floor_rel` are optional and numeric and belong to run rows; with `floor_rel`, `floor_base` is required and `floor >= floor_base`.

## Staleness

A baseline is stale past `stale_after`, when its harness hash differs from the current harness (an unknown current hash also counts), or when
its worlds, seeds or ticks differ from the config. A stale baseline never yields a pass (roadmap principle 4).

## Re-baseline

`python -m tools.test_architecture.rpg_gate_baseline rebaseline ...` refuses without a divergence id and/or memo row plus a PR, and refuses a
new value outside a stop line (declared in rpg's config) unless an `owner_ruling` is given. The before/after of every changed row is computed from
the two files and stored in the record.

## Rules added in review

- The row key `(id, scope, world, group, key, tick)` is the pairing key the report (child 4) must use. `scope` is `run` or `pooled`; a pooled outcome row has a `value` and no `per_seed`.
- A baseline holds validity rows only at 0 violations; a validity fail is owned in `rpg_gate_known.yaml` (`state: fail`), never normalised by a re-baseline, and no ruling overrides that.
- `provenance.cites` is required and non-empty on every version; a later version must contain the PR and a divergence id or memo row.
- `owner_ruling` is `{ref, date}`; only the owner's ruling counts (a peer's or designer's message does not; a designer-recorded memo row the owner confirmed does).
- Stop lines are checked on every candidate row, so a ruling is needed at each re-baseline while a value stays past the line.

## Required validity rows

The config may carry `required_validity`, a mapping from a **level** to the ids required there: `{run: [V1, V2, V3, V4, V5, V6, V8], pooled: [V7]}`. The levels are `run` and `pooled` only. A seed document is the `run` level and the pooled document is the `pooled` level; an id is required in the documents of the level(s) it is listed under, and may be listed under both. `load_config` refuses the plain-list form (it does not say which documents carry which id), an unknown level, a non-list value, a duplicate within a level, and an id that is not of the form `V<n>`. The values are rpg's; the format and behaviour are testing's. A metric module that leaves a required row out would otherwise pass silently, so:

- the report gives each id required at a document's level but missing from that document (in every world) the state `no-data`, reason `contract_error`, detail `required validity row <id> missing`, and the markdown names the missing ids in a banner. A row that is not required at that level is not asked for. It never reads as a pass; the job's verdict rule is unchanged (no-data is not red by itself);
- the candidate refuses while any row required at a document's level is missing from it, unless a current, unexpired `state: fail` entry in `rpg_gate_known.yaml` owns that id (then the row is listed in `omitted_validity`, once per world and level, as `<id>:run:<world>:*` or `<id>:pooled:<world>:*`).

## V8: every entity added mid-run has a declared source

Owner ruling D70: a monster spawner with no parent and no cost is nothing-from-nothing, and no V1-V7 row counted entity adds. V8 lands before baseline v1, so v1's row set contains it. Validity is absolute (rule 8 of `baseline_change_policy.md`): it records no value.

| field | value |
|---|---|
| id | `V8` |
| class | `validity` |
| scope | `run` (required at that level). A pooled V8 row is optional; if a module emits one, its `violations` must equal the sum of the seeds' rows |
| group | the kind group (D42, property-based), or `*` for the whole run |
| oracle | `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md#v8-every-entity-added-mid-run-has-a-declared-source` (this section), and D70 |

Every entity put into the world after tick 0 through the authoritative apply path (`entities_add`) must carry a `SpawnSource` (rpg's frozen type, carried beside the entry, not on the entity). The only runtime violation is an **unsourced add**: an add with no SpawnSource. The two other shapes are refused at construction by `SpawnSource.__post_init__` and so cannot reach the tally:

- an `AUTHORED_ARRIVAL` without `rule_kind` and `rule_id` (an authored arrival must name its declaring definition);
- a `BIRTH` with empty `parent_ids` (and parents on any other kind).

`tests/simulation_quality/rpg_gate/test_v8_fires.py` cases (b) and (c) assert that refusal; case (a) asserts the unsourced violation. `INITIAL` (tick-0 worldgen) is not judged. The tally is one closing event per run, keyed `(kind_group, source.kind)` plus an `unsourced` count, with a liveness header. Each example is `{entity_id, tick, kind_group, check}` with `check` = `"unsourced"`. There is no `site` key: the ledger cannot know the call site. The list is bounded by the ledger's `MAX_EXAMPLES`; the violation count stays exact. `test_v8_fires.py` cases (a), (f) and the cap case assert this shape against the real ledger.

No-data rule: a missing or silent tally is `no-data` (`harness_error`), never 0 violations. A required V8 row that the module does not emit is `no-data` (`contract_error`) by the section above.

The stub metric module (`tests/helpers/rpg_gate_stub_metrics.py`) emits a V8-shaped row in three modes through `RPG_GATE_STUB_V8` (`absent`, `clean`, `violations`) so the report and candidate tests can exercise them without rpg's module.

## Open points for rpg

- Config: `tests/simulation_quality/rpg_gate/config.yaml`, rpg's (agreed by rpg-planner). Stop-line shape: `name`, `metric`/`group` free fnmatch patterns (`group` is a property-based kind group, D42, never an EntityRole name), `min`/`max` on a row's value.

## The run row set is declared, not observed

The metric module declares, per world, the run rows `(id, group, key, tick)` it emits, so **every seed document of a world carries the same rows** (TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED).

- A keyed count (`O2.deaths` by cause, `O4.accepted` by source) is emitted for every declared key on every seed, with `value: 0` when no event happened. The key domain is a declared enumeration, never "the keys seen in this run".
- A share or rate whose denominator can be 0 on a seed has a defined value in the module, or it is not a run row. It is never left out on that seed alone.
- Testing's tools **never impute an absent row**, and never read it as 0: a dropped row and a true zero would look the same (the blindness class V1 and V4 had).
- The report shows the mismatch. A row key present in some seeds of a world and absent from others gives one `no-data` / `contract_error` row for that key, detail `row absent from seed(s) [..]; every seed reports the same rows`, in the markdown table and in the tally (`contract_error`). The key is not judged on the seeds that carry it. A required validity row is reported per seed by the required-validity rule instead.
- The candidate refuses on the same condition (`row <id> (group <g>) is absent from seed(s) [..]; every seed must report the same rows`).

### Shares

A share is never a run row. The module carries it as two dense count run rows, a numerator and a denominator, judged like any count, and a **pooled** share row with `value = Σnum/Σden` over the seeds (a seed whose denominator is 0 contributes nothing).

- When `Σden = 0` for a world, the module emits the pooled row with `value: null` and `reason: "empty_denominator"`.
- **Report:** that row is `no-data` with reason `empty_denominator`. It is not a `contract_error`, is tallied under its own reason, and is not a failure. A pooled outcome row with a null value and any other reason, or none, stays a `contract_error`.
- **Candidate:** the row is left out of `metrics` and listed in `undefined_rows: [{row, reason}]`; `rebaseline` carries the list into the baseline (the lint checks each entry and that a listed row is not also in `metrics`). A null value without the reason still refuses.
- **Against a baseline where the row was undefined**, a run in which it is defined reads `no reference (undefined at baseline)`, never drift. Only a re-baseline gives it a reference.

## Candidate and recording v1

A baseline is recorded from a run, never typed. `tools/test_architecture/rpg_gate_candidate.py` (child 6) turns the harness documents into the
candidate that `rebaseline` reads: the baseline shape without `version`, `rebaseline`, `recorded_at`, `stale_after` and `cites` (the last three are filled
by `rebaseline`). Run outcome rows carry `per_seed`, `mean`, `se` and the row's `k`/`floor`; pooled outcome rows `value` and `floor`; validity rows `violations`
(0) and `oracle`. The same inputs give the same bytes.

It refuses (exit 2, nothing written) on any `no-data` document, a missing or unexpected (world, seed), a `sha` / `harness_hash` / ticks disagreement, a
`k` / `floor` / `oracle` mismatch across the documents of one world (floors may differ between worlds, never between the seeds of one), a row absent from a seed, fewer than 2 seeds, and a validity fail with no current owner. A validity
fail with a current, unexpired `state: fail` entry in `rpg_gate_known.yaml` is instead left out of `metrics` and listed in `omitted_validity`
(`{row, known_match, ticket}`), because validity is judged absolutely on every run and never against a baseline. The lint rejects a listed row still present in `metrics`, and `rebaseline --known FILE` re-checks each omission's owner against the current registry (refuses when it is gone, no longer `state: fail`, or expired).

The `RPG gate report` job writes `rpg-gate-candidate.json` into its report artifact on every run where the builder accepts (a refusal is a line in the step
summary, never a job failure). A run that is not main's is built with `--evidence-only`, and `rebaseline` refuses such a candidate.

Recording v1 (rpg, after the metric module and config are on main; the milestone is rpg's to name):

1. Download the `rpg-gate-report-<sha>` artifact of a scheduled or dispatched run of main whose candidate was written.
2. `python -m tools.test_architecture.rpg_gate_baseline rebaseline --candidate rpg-gate-candidate.json --config tests/simulation_quality/rpg_gate/config.yaml --milestone M0 --cite <metric-set ticket>`
   (add `--owner-ruling-ref ... --owner-ruling-date ...` when a stop line is crossed).
3. Commit `tests/simulation_quality/rpg_gate/baselines/rpg_gate_v1.json` in a PR that cites the same ticket.

To rebuild a candidate from a downloaded `gate-docs` directory: `python -m tools.test_architecture.rpg_gate_candidate --config ... --docs gate-docs --known tools/test_architecture/rpg_gate_known.yaml --report rpg-gate-report.json --out candidate.json --milestone M0`.
