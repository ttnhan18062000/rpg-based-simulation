---
status: active
layer: performance
authority: P1
audience: developer
---

# Engine Performance Baseline Policy

## 1. Purpose and Scope

This document is the **lifecycle policy** for performance baselines: how one is created, promoted, invalidated, migrated and
rejected. It is not where performance is defined, measured, compared or claimed: since PERF-D4 (approved 2026-10-03) that is
`docs/engine/performance_contract.md`, the single clause-level authority. The record a baseline is made of, and the rule for comparing two,
are `docs/performance/benchmark_identity_schema.md` (schema 1.0, §4). Hardware classes are defined once, in
`docs/engine/contracts/certification_contract.md` §3.

The repository-wide rules for changing any baseline (versions are never overwritten, a change cites its cause and its PR, a stale or
mismatched baseline never passes) belong to the shared baseline change policy,
`docs/plans/test_architecture/reference/baseline_change_policy.md`. **That document does not exist yet (pending, testing-owned, agreed on
#475); this policy cites it as a forward reference and adds only the performance preconditions in §3.** When it lands, its wording wins
for the shared rules and this section is reduced to a link.

Measurements stay provisional and no performance check is blocking (`PERF-M2` lift, OD-8). Nothing here makes one blocking.

What this document used to contain, and where it went:

| Earlier content | Now |
|---|---|
| Benchmark protocol (100 warmup, 1,000 sampled ticks) | `performance_contract.md` §3.2, as capacity-run minimums |
| Hardware-class table (`CLASS_A`/`B`/`C` by cores and RAM) | Removed. It contradicted `certification_contract.md` §3. The per-class entity targets moved to `performance_contract.md` §5.1 |
| CI regression thresholds and the `UnacceptableRegressionError` rule | `performance_contract.md` §5 and §5.1 as documented targets that no check enforces yet |
| The five-step "refresh a tripwire reference" calibration procedure | Replaced by the lifecycle in §2 and §3, run by `tools/perf/baseline_lifecycle.py` |

---

## 2. Lifecycle

A baseline is a reference for a comparison made by a projection of the performance contract (`performance_contract.md` §3.3). Which
projection it serves decides what it may be used for.

| Stage | Rule |
|---|---|
| **Create** | Measure with `BenchHarness` on an isolated machine. The run yields a `BenchmarkRecord` (`harness.last_record`; schema 1.0). A record that is not a clean, `NORMAL`, current-accounting run is not a baseline candidate (§3). |
| **Promote** | `python3 tools/perf/baseline_lifecycle.py promote --candidate <record.json> --name <baseline> --cause <cause>`. It writes the next `<baseline>.vNNNN.json` in `tests/perf/baselines/` and never touches an earlier version. The file is the record, with `identity.baseline_ref` pointing at the previous version (`{id, schema_version, record_digest}`), plus a `promotion` object holding the cause, the note, the time, the **before** identity and the **after** identity. |
| **Invalidate** | A baseline stops being comparable when a blocking field of the schema (§4) changes. The tool does not delete it. `compare()` reports `INCONCLUSIVE` naming the field, which is the visible state of an invalidated baseline. `docs/performance/baseline_invalidation_ledger.md` lists which committed baselines the M1 corrections invalidated. |
| **Migrate** | A MAJOR `schema_version` bump invalidates every baseline of the older MAJOR for comparison (schema §4). They stay readable and are re-recorded by a promotion that cites the cause, not converted: a converter would invent identity the old file never recorded. |
| **Reject** | A missing baseline, an incompatible one, one without `cost_accounting_version`, or one whose cause cannot be shown is `INCONCLUSIVE`, never a pass and never a skip that reads as success. |

`python3 tools/perf/baseline_lifecycle.py check` verifies the directory: every `tests/perf/baselines/*.json` is a valid `BenchmarkRecord` or
is named in the legacy list (`LEGACY_TRIPWIRE_REFERENCES`, §4), and the version chain of each promoted baseline is intact (each version's
`baseline_ref` matches the digest of the previous file, so an edited earlier version is found). `tests/unit/perf/test_baseline_lifecycle.py`
runs it on the committed tree.

---

## 3. Preconditions for a promotion (performance-specific)

`promote` refuses, prints `REFUSED: <code>: <message>` for every reason that applies, writes nothing and exits 2, when the candidate:

| Code | Refused when |
|---|---|
| `invalid_candidate` | it is not a valid `BenchmarkRecord` |
| `dirty_src` | `identity.engine.dirty_src` is true: a baseline comes from a clean `src/` tree |
| `mode_not_normal`, `mode_sequence_empty` | `runtime_mode_sequence` left `NORMAL`, or is empty: the run does not prove it did the nominal work (`performance_contract.md` §3.1) |
| `cost_accounting_version_missing`, `cost_accounting_version_stale` | `result.cost_accounting_version` is absent or is not the current one (DEV-017): tick and phase costs are not comparable |
| `no_cause`, `unknown_cause` | it cites no cause, or a cause that does not exist here |
| `bad_name` | the baseline name is not lower-case `[a-z0-9_]` |

**The cause.** A baseline change is a reviewed change of evidence, not a way to make a build pass. The cause is one of: a ticket id
(`TCK-YYYYMMDD-...`, which must exist under `agent-working/tickets/`), a divergence id (`DEV-nnn`, which must be recorded in
`docs/guidelines/intentional_divergences.md`), or a behaviour PR (`PR #n`; a PR number cannot be checked offline and is accepted by shape).
Under the canonical signal contract a deliberate behaviour change reads as `REGRESSION` (schema §4, OD-3), so the re-baseline that follows it
cites the behaviour PR or the divergence id that caused the change. Raising a baseline to silence a regression, without a cause that
explains the change, is not a promotion this policy allows.

**Owner approval.** The promotion tool checks the preconditions, not authority. The owner approves a baseline (`perf-implementer` role card),
and the approval is the review of the PR that adds the file.

---

## 4. What baselines exist today

- The 15 JSON files in `tests/perf/baselines/` are **tripwire references with no recorded identity**. They are not schema records, they
  carry no capacity claim, and they are named in `LEGACY_TRIPWIRE_REFERENCES`. 12 of them are 20-tick samples taken by the smoke
  benchmark; only the three `simq_corpus_*` files record 1,000 sampled ticks. Their percentiles use the old `sorted[int(n * q)]` method,
  and most of them predate DEV-017, so most are listed as needing a rerun or incomparable in the invalidation ledger.
- The synthetic-scenario files (`idle_100_local.json`, ...) have the shape and file names produced by `tools/perf/run_benchmarks.py`. No
  script copies them into `tests/perf/baselines/`; the only tool that writes there besides `baseline_lifecycle.py` is
  `tools/bench_corpus_world.py --commit` (§6).
- The live comparison (`tests/perf/test_perf_regression_baseline.py`) reads the committed JSON directly and compares `avg_tick_compute_ms`
  only, and a missing file is skipped. Under the performance contract that is `INCONCLUSIVE`; `PERF-M2-T03` makes the live comparison use
  `compare()`.
- `PERF-M2-T08` re-records them as schema records under the canonical variants, through `promote`, and then retires the legacy list.
- No capacity-run baseline exists (`PERF-M2-T04`).

The **known-debt ledger** (a baseline lane that is already red, with an owner and an expiry) is `PERF-M2-T05b`
(`TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER`). It waits for the shared known-reds module and is not part of this policy yet.

---

## 5. Named benchmark results


- **SimQ mode isolation overhead** (`QUALITY_SCORING_DISABLED=1` vs. in-process vs. broker):
  `docs/performance/simq_isolation_overhead.md`, produced by
  `tests/perf/test_simq_isolation_overhead.py`. This is a **comparative** result in the sense of
  `performance_contract.md` §3.3.

---

## 6. SimQ Corpus World Baselines (`TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION`)

Prior to 2026-08-08, all committed baselines (`tests/perf/baselines/*.json`) covered only
synthetic scenarios (`combat_10`, `idle_100`, `mixed_200`, `movement_100`, `resource_100`,
`strategic_100`, via `src/perf/scenarios.py`'s raw `State` builders) — none of the real, authored
SimQ world corpus (`data/worlds/`) had ever been perf-measured.

`tools/bench_corpus_world.py --world {name} [--commit]` benchmarks a real corpus world: reuses
`tools/calibrate_simq.py::_load_world_state()` to build the same real, `WorldCompiler`-compiled
`AuthoritativeState` SimQ calibration uses (no synthetic content, no separate authoring), then runs
`BenchHarness(PERF_PROFILES["PERF_512MB_LOCAL"]).run_benchmark(...)` — a genuinely separate,
dedicated benchmark execution (NOT a free byproduct of a calibration run — `BenchHarness` runs its
own warmup+sample tick loop). Writes the same raw-dict JSON shape as the existing baselines
(`avg_tick_compute_ms`, `tick_ms{}`, `mem_rss_mb{}`, `phase_breakdown{}`), so
`tests/perf/test_perf_regression_baseline.py`'s own real, live comparison logic applies unchanged
— committed baselines are added as new `(scenario_id, builder_fn, kwargs)` rows in that file's own
`parametrize` list.

**Coverage so far**: `simq_corpus_frontier_extended` (59 entities), `simq_corpus_frontier_marches`
(62 entities), `simq_corpus_crowded_frontier` (38 entities) — the corpus's largest 3 worlds by
entity count at the time this ticket ran. Extending coverage to the remaining corpus worlds, or to
`TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION`'s own new large world once it exists, is a
natural follow-up using the same `tools/bench_corpus_world.py --commit` command — not automated in
this ticket.
