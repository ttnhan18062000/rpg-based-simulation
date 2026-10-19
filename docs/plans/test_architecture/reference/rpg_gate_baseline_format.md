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
