---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, regression, simulation-quality]
---

# Baseline change policy

The rules for every recorded test baseline: what a baseline file must carry, when it may change, and who may approve the change. Testing owns
these rules. Each baseline's owner owns its content. This page generalises the rpg gate model
(`reference/rpg_gate_baseline_format.md`, `tools/test_architecture/rpg_gate_baseline.py`), which already implements all of them. Promised on
#488, and it applies to perf's PERF-M2-T05b.

It applies roadmap principles 4 (honest states) and 5 (never make red green by weakening tests) to baselines.

## Scope

A **baseline** is any committed value that a test or a report compares a fresh run against, where the value came from an earlier run rather than
from the Mechanics Bible or an Engine Contract. Current baselines:

| Baseline | Files | Writer | Content owner |
|---|---|---|---|
| rpg gate | `tests/simulation_quality/rpg_gate/baselines/rpg_gate_v<N>.json` | `rpg_gate_baseline.py rebaseline` | rpg |
| Perf benchmarks | `tests/perf/baselines/<name>.vNNNN.json` | `tools/perf/baseline_lifecycle.py promote` | perf (lifecycle detail: `docs/performance/perf_baseline_policy.md`) |
| Mutation | `tests/mutation/baselines/<target>_v<N>.json` | the mutation run record | testing |
| SimQ grade anchors | `tests/simulation_quality/fixtures/grade_anchors.json` | `tools/test_architecture/simq_reanchor.py` (TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE) | rpg (values), testing (method) |
| 5k behavioural regression | `tests/regression/baseline_5k.json` | `tools/generate_regression_baseline.py` | rpg |

A baseline that is not yet listed falls under this policy as soon as it is committed. Its owner adds the row in the PR that introduces it.

A value that the Bible or a contract defines is **not** a baseline. You change it by changing the document first (principle 1), never by re-recording a run.

A domain may keep its own lifecycle document, as perf does. It may add preconditions, but it may not relax a rule here. Where the two
disagree, this page holds until the testing planner and that domain's planner agree a change.

## Rules

1. **Recorded, never typed.** A baseline value comes from a run, through the baseline's writer. Hand-editing a value is refused in review. When there
   is no writer yet, the PR that changes the baseline adds one; the grade anchors are the current case.
2. **Provenance on every version.** Each file (or, for a single-file baseline, a provenance record committed beside it) carries:
   - the commit SHA it was measured on, and whether the `src/` tree was clean;
   - the run identity: worlds, seeds, ticks, harness or command hash, and the runtime mode (for example audit_mode or the governor sequence);
   - `recorded_at` and, where staleness by age applies, `stale_after`;
   - a non-empty `cites` (see rule 4).
3. **Immutable versions where the format allows.** A change writes version N+1 next to version N and never edits N. A version chain must be
   intact. A single-file baseline that predates this policy (grade anchors, 5k regression) may be rewritten in place, but the change must commit a
   before/after table for every changed row with its provenance. A new baseline uses versioned files.
4. **A cause, cited.** A change cites a ticket, a divergence id (`DEV-nnn`) or memo row, and the PR. "The test was red" is not a cause. The
   before/after of every changed row is stored with the change, computed by the writer from the two versions.
5. **The owner rules on moved values.** When a re-record moves a value, the content owner rules on whether the move is intended, in writing,
   before the change is committed. The ruling is recorded as `owner_ruling {ref, date}`. Only the owner's ruling counts. A peer's or designer's
   message does not, though a designer-recorded memo row that the owner confirmed does. A move the owner cannot explain is a finding for that owner,
   not a baseline change: the row is excluded from the re-record and owned in a known-reds registry (rule 8).
6. **Stop lines.** An owner may declare limits on a baseline's values. A candidate past a stop line is refused unless it has an `owner_ruling`,
   and that ruling is needed again at every re-record while the value stays past the line.
7. **Determinism before recording.** A baseline is recorded only from runs that reproduce. At least two isolated processes on the same SHA must
   give identical values. A key that does not reproduce is a determinism finding for its owner and is left out. Noise is never absorbed by
   widening a tolerance. A tolerance or band widened to make a run pass falls under principle 5 and is refused.
   For the SimQ grade anchors the run's own manifest must record it: `simq_reanchor` refuses a pair unless both runs record `audit_mode` and `signals_zeroed` as True at write
   time, and `simq_pillar_compare` (and `evaluate_simq`) refuse a live run whose record (`quality_report.run_determinism.json`, copied from the run manifest) is not
   `signals_zeroed` True at compare time. A missing or null field is not recorded; there is no override (TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT,
   on rpg's TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR). The committed anchors carry no manifest: their
   host independence is the write-time guarantee.
8. **Validity is absolute.** Rows that check a law (0 violations, conservation, a contract bound) are never normalised by a re-record, and no
   ruling overrides that. A validity failure is owned in the matching known-reds registry (`tools/test_architecture/known_reds.py`), with a
   ticket, an owner and an expiry.
9. **Stale is reported, never passed.** A baseline is stale when it is past `stale_after`, when its harness or command hash differs from the
   current one (an unknown hash counts as different), or when its run identity differs from the current config. A stale baseline yields a
   `stale` state, never `pass`. Where staleness is a report state (mutation), the test does not fail on it but the report shows it.
10. **Drift guard.** A report compares a run with the latest version and also with a fixed earlier reference: the first version of the current
    milestone, or the version a milestone owner names. Successive small re-baselines cannot then hide a slow drift.
11. **Evidence-only runs cannot record.** A run of a non-main ref, a dirty tree or a non-nominal runtime mode (a perf record that left `NORMAL`,
    for example) can be shown as evidence, but the writer refuses it as a baseline.
12. **Review.** A baseline change is its own reviewed change of evidence. Its PR names the baseline, the cause, the moved rows and the ruling.
    The testing planner reviews the method (these rules) by PR comment. The content owner approves the values. A PR that changes a baseline
    together with the behaviour that moved it must still list the moved rows. It is the owner's call whether to split it.

## What each writer enforces today

| Rule | rpg gate | perf `promote` | mutation | grade anchors | 5k regression |
|---|---|---|---|---|---|
| 1 recorded | yes | yes | yes | after TCK-20261011 | yes (script) |
| 2 provenance | yes | yes (identity) | yes (target contents, stale_after) | after TCK-20261011 | partial |
| 3 immutable | yes | yes | yes (`_vN`) | in place + table | in place |
| 4 cause | yes (`cites`) | yes (ticket/DEV/PR) | review only | after TCK-20261011 | review only |
| 5 owner ruling | yes | review only | n/a (testing owns) | review only | review only |
| 7 determinism | harness, fresh pinned processes | review only | n/a | yes (pair identity) | review only |
| 9 staleness | yes | `cost_accounting_version` | report state | no | no |

A "review only" or "no" cell is a gap, not an exemption. The reviewer checks that rule by hand until the writer enforces it. Closing a gap is
the baseline owner's ticket. Testing reviews it.

## Related

- `docs/plans/test_architecture/roadmap.md` §3 (principles 1, 4, 5, 8)
- `reference/rpg_gate_baseline_format.md`
- `tools/perf/baseline_lifecycle.py` (docstring)
- `tools/test_architecture/known_reds.py`, `tools/test_architecture/slow_known_reds.yaml`
- TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE
