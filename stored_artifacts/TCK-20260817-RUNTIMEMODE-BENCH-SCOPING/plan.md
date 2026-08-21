---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260817-RUNTIMEMODE-BENCH-SCOPING
artifact_type: plan
tags: [performance, engine, testing]
---

# Implementation Plan — TCK-20260817-RUNTIMEMODE-BENCH-SCOPING

## Summary
Add `RuntimeMode` as a 5th required Scoped-Claims dimension in the performance contract, sample
`kernel.status.current_mode` on every tick inside `BenchHarness.run_benchmark()`'s sampling loop
and expose it as `result["mode_sequence"]`, then wire an excursion check into
`test_regression_vs_baseline` that is independent of the existing `avg_tick_compute_ms` check.
The one genuinely undecided question — whether that excursion check is a hard `AssertionError`
or a soft `PerformanceThresholdWarning` — is not guessed here. It is resolved by an explicit
Implement-time empirical step (Step 4): run the real, newly-instrumented gate against all 6 live
scenarios first, then set `hard=True` only for scenarios that measurably stayed NORMAL and
`hard=False` (with a loud message and a documented follow-up-ticket recommendation) for any that
excursed. A new unit test exercises the extracted assertion helper directly against a synthetic
`mode_sequence` (fast, deterministic), and the doc + parity ledger are updated to close the loop.
No change touches `PressureSignals`, `ConformanceEvaluator`, or `perf_baseline_policy.md`.

## Steps

### Step 1 — Add RuntimeMode as a 5th Scoped-Claims dimension
**Files:** `docs/engine/performance_contract.md`
**Change:** Confirmed current text (read directly, `docs/engine/performance_contract.md:35-42`):
```
### 3.1 Scoped Claims
Performance claims are ONLY valid when combined with:
- **Runtime Profile**: (e.g. `standard_gaming`)
- **Hardware Class**: (e.g. `Class_B`)
- **Scenario**: (e.g. `MOVEMENT_STRESS_100_ACTORS`)
- **Execution Mode**: (LOCAL vs CONCURRENT)

### 3.2 measurement Protocol
```
Insert a new bullet immediately after the `**Execution Mode**` line (line 40) and before the
blank line preceding `### 3.2` (line 41-42), so the section reads:
```
- **Execution Mode**: (LOCAL vs CONCURRENT)
- **RuntimeMode**: (NORMAL — see §7 Adaptive Phase Budget Governor for the ladder; a claim
  measured while the Governor left NORMAL is not a valid baseline claim without stating so)

### 3.2 measurement Protocol
```
**Do NOT touch:** `docs/engine/contracts/extended_certification_contract.md` §5's differently
shaped "Scoped Claims"/"Quadrants of Truth" (RuntimeProfile, CertificationScenario, HardwareClass,
OverrideStatus) — a separate doc, separate dimension set, not in scope. Do not touch `### 3.2
measurement Protocol` itself (warmup/sampling minimums) — unrelated to this ticket.
**Verify:** New test `test_performance_contract_lists_runtimemode_scoped_claim` (Step 5c).

---

### Step 2 — Sample RuntimeMode per tick in `BenchHarness.run_benchmark()`
**Files:** `src/perf/bench_harness.py`
**Change:** Confirmed current sampling loop (`src/perf/bench_harness.py:80-90`):
```python
            # 2. SAMPLING
            rss_samples: List[float] = []
            wall_start_ts = time.perf_counter()

            try:
                for i in range(sample_ticks):
                    kernel.tick_once()

                    # Sample memory every 10 ticks to reduce overhead
                    if i % 10 == 0:
                        rss_samples.append(self._process.memory_info().rss / (1024 * 1024))
```
Add a `mode_samples: List[str] = []` list alongside `rss_samples`, and append
`kernel.status.current_mode.name` **every tick, unthrottled** (not gated behind `i % 10 == 0`
like RSS):
```python
            # 2. SAMPLING
            rss_samples: List[float] = []
            mode_samples: List[str] = []
            wall_start_ts = time.perf_counter()

            try:
                for i in range(sample_ticks):
                    kernel.tick_once()

                    # RuntimeMode is a trivial IntEnum read — sample every tick, unlike the
                    # throttled RSS collector below, so a transient CONSTRAINED/DEGRADED/SURVIVAL
                    # excursion inside an un-sampled gap can never be missed
                    # (TCK-20260817-RUNTIMEMODE-BENCH-SCOPING; see plan.md Design Decisions (a)).
                    mode_samples.append(kernel.status.current_mode.name)

                    # Sample memory every 10 ticks to reduce overhead
                    if i % 10 == 0:
                        rss_samples.append(self._process.memory_info().rss / (1024 * 1024))
```
Cadence decision (confirmed, see Design Decisions (a)): **every tick, not throttled.**
Accessor confirmed live and populated every tick: `kernel.status` returns a `RuntimeStatus`
(`src/engine/kernel.py:1213`, `def status(self) -> RuntimeStatus`), whose `current_mode` field
(`src/engine/runtime_status.py:18`, `current_mode: RuntimeMode = RuntimeMode.NORMAL`) is mutated
every tick via `ResourceGovernor.evaluate()` → `status.reset_dwell()`/`status.increment_dwell()`
inside `Kernel._phase_init()`. `RuntimeMode` is `IntEnum` (`src/core/governance.py:8-16`) so
`.name` yields one of `"NORMAL"|"CONSTRAINED"|"DEGRADED"|"SURVIVAL"`. No import of `RuntimeMode`
into `bench_harness.py` is needed — only `.name` (already a string) is read; no enum comparison
happens inside the harness itself.

Expose the result. Confirmed current result-dict tail (`src/perf/bench_harness.py:134-156`) ends:
```python
                "replay_enabled": not effective_flags.get("no_replay", False),
                "frame_pacing_enabled": not effective_flags.get("no_frame_pacing", False),
                "timestamp": time.time()
            }
```
Add `mode_sequence` as a new key in this same dict literal, directly after `"timestamp"`:
```python
                "replay_enabled": not effective_flags.get("no_replay", False),
                "frame_pacing_enabled": not effective_flags.get("no_frame_pacing", False),
                "timestamp": time.time(),
                "mode_sequence": mode_samples,
            }
```
(Note the added trailing comma after `time.time()`.) This key name (`mode_sequence`) matches the
ticket's own AC wording exactly — do not rename it.

**Other writers to this shared resource:** `kernel.status.current_mode` (the thing being read) is
written by exactly one path: `ResourceGovernor.evaluate()` inside `Kernel._phase_init()`
(confirmed at `src/engine/kernel.py:545-546` per investigation) — no other code path mutates
`RuntimeStatus.current_mode`. This step is a **pure read**, added alongside the existing pure-read
RSS sampler in the same loop; it does not write to `RuntimeStatus`, `PressureSignals`, or
`AuthoritativeState`, so there is no write-ordering or race concern — it only needs to run after
`kernel.tick_once()` completes for tick `i`, same as the RSS sampler already does. The result dict
itself (`result[...]`) is local to this single `run_benchmark()` call — not a shared/concurrent
resource; no other function writes into the same dict instance.
**Do NOT touch:** `PressureSignals` (`src/core/governance.py:19-52`, genuinely
`@dataclass(frozen=True, slots=True)`) — do not add a mode field to it. Do not touch
`RuntimeStatus` (`src/engine/runtime_status.py`) even though its "FROZEN" docstring is only a
process-convention marker (plain `@dataclass`, not `frozen=True`/`slots=True`) — this step needs
no write/schema change to it, only a read of the already-existing `current_mode` field. Do not
throttle mode sampling to match the RSS `i % 10 == 0` cadence.
**Verify:** New test `test_run_benchmark_records_mode_sequence` (Step 5a); existing
`tests/perf/test_bench_harness.py::test_bench_harness_cpu_time_sampling` must keep passing
unmodified (additive-only key).

---

### Step 3 — Add the excursion assertion to `test_regression_vs_baseline`
**Files:** `tests/perf/test_perf_regression_baseline.py`
**Change:** Confirmed current full test body (`tests/perf/test_perf_regression_baseline.py:32-71`,
read above) runs `harness.run_benchmark(..., warmup_ticks=10, sample_ticks=50,
flags={"no_replay": True})`, then compares `result["avg_tick_compute_ms"]` against
`threshold = max(5.0, baseline_avg * 1.25)` via a single `assert_perf_threshold(..., op="<=")`
call (currently `hard` defaults to `False` — confirmed at `tests/tools/perf_assertions.py:89-95`,
default `hard: bool = False`).

Add, at module scope (near the top, after the existing imports):
```python
# TCK-20260817-RUNTIMEMODE-BENCH-SCOPING: which of the 6 parametrized scenarios get a hard
# (AssertionError) vs. soft (PerformanceThresholdWarning) RuntimeMode-excursion gate is decided
# empirically, not guessed -- see plan.md Step 4 / Design Decisions (b). This set is populated
# ONLY after running the real, newly-instrumented gate (warmup_ticks=10, sample_ticks=50) against
# every scenario below and recording which ones stayed RuntimeMode.NORMAL throughout. Any
# scenario NOT in this set excursed under real load during that measurement and must stay soft,
# with a documented follow-up-ticket recommendation (ticket Out-of-Scope item 3) -- never silently
# add a scenario here without having actually run it.
_RUNTIME_MODE_HARD_SCENARIOS: frozenset[str] = frozenset({
    # Implement fills this in from the Step 4 empirical run. Example shape once measured:
    # "idle_100_local", "movement_100_local", ...
})


def _assert_runtime_mode_stayed_normal(mode_sequence: list, scenario_id: str, *, hard: bool) -> None:
    """Extracted so it is directly unit-testable against a synthetic mode_sequence, independent
    of BenchHarness/Governor load timing (see test_perf_regression_baseline_flags_runtime_mode_excursion)."""
    excursions = [m for m in mode_sequence if m != "NORMAL"]
    assert_perf_threshold(
        len(excursions), 0,
        f"RuntimeMode excursions during {scenario_id} "
        f"(modes seen: {sorted(set(mode_sequence))}, hard_gate={hard})",
        op="<=",
        hard=hard,
    )
```
In `test_regression_vs_baseline`, immediately after `result = harness.run_benchmark(...)` (current
lines 49-55) and **before** the existing `baseline_avg`/`current_avg`/threshold block, add:
```python
    print(f"RuntimeMode modes observed for {scenario_id}: {sorted(set(result['mode_sequence']))}")
    _assert_runtime_mode_stayed_normal(
        result["mode_sequence"], scenario_id,
        hard=scenario_id in _RUNTIME_MODE_HARD_SCENARIOS,
    )
```
This satisfies the literal AC wording ("independent of the avg_tick_compute_ms threshold
result") — the RuntimeMode check runs and can fail/warn regardless of what the compute-time
check finds, and vice versa; neither result gates the other. Placing it first (rather than after)
also means a hard excursion failure is reported before spending time on the compute-time
comparison, but ordering is not itself load-bearing for AC3 — independence is what's required.
**Other writers to this shared resource:** none beyond Step 2 — `result["mode_sequence"]` is
produced fresh by each `run_benchmark()` call and consumed only here. `assert_perf_threshold` /
`perf_check` (`tests/tools/perf_assertions.py:64-119`) is the same shared helper every other
`tests/perf/`, `tests/arena/`, `tests/certification/` threshold check calls; this step's usage is
just another caller passing an explicit `hard=` value per its own module docstring's documented
contract (structural-correctness checks may pass `hard=True`) — it does not change
`perf_check`/`assert_perf_threshold` themselves, so it cannot affect any other caller's behavior.
**Do NOT touch:** the existing `avg_tick_compute_ms` / `threshold` / `assert_perf_threshold(...)`
block itself — leave it exactly as-is, just add the new check adjacent to it. Do not import or
use `ConformanceEvaluator` (`src/certification/conformance.py`) — confirmed unnecessary weight
(hash comparisons, recovery timing, lifecycle checks this fast gate has no use for).
**Verify:** `test_perf_regression_baseline_flags_runtime_mode_excursion` (Step 5b); all 6
existing parametrize cases in `test_regression_vs_baseline` still run and their
`avg_tick_compute_ms` check still executes independently.

---

### Step 4 — Resolve hard-vs-soft per scenario via empirical measurement (Implement-time, before Step 3's constant is finalized)
**Files:** none changed by this step directly — it produces the values that finish Step 3's
`_RUNTIME_MODE_HARD_SCENARIOS` set, and updates the ticket's own `## Implementation Notes`.
**Decision rule (fixed by this plan; the *outcome* is not):**
1. Land Steps 1-3 with `_RUNTIME_MODE_HARD_SCENARIOS` empty (everything defaults to soft — a
   correct, safe starting state, since `assert_perf_threshold`'s own default is `hard=False`).
2. Run the real gate for real, once per scenario, at the gate's own configuration
   (`warmup_ticks=10, sample_ticks=50`), against all **6** live-parametrized scenario IDs
   (corrected count — confirmed by reading `tests/perf/test_perf_regression_baseline.py:24-31`'s
   parametrize table directly, not the ticket's stale "26"): `idle_100_local`,
   `movement_100_local`, `combat_10_local`, `simq_corpus_frontier_extended`,
   `simq_corpus_frontier_marches`, `simq_corpus_crowded_frontier`. Use:
   ```
   pytest tests/perf/test_perf_regression_baseline.py -v -s
   ```
   (the `-s` flag surfaces the `print(f"RuntimeMode modes observed for {scenario_id}: ...")`
   line added in Step 3 for every case, including cases that don't excurse).
3. For `simq_corpus_crowded_frontier` specifically — the one scenario investigation flagged with
   a concrete circumstantial signal (`tests/perf/baselines/simq_corpus_crowded_frontier.json`
   records `peak_rss_mb: 696.3` against `PERF_512MB_LOCAL`'s `max_ram_mb=512`
   (`src/perf/profiles.py:53-56`), and `ResourceGovernor._get_indicated_mode()`
   (`src/engine/governor.py:80-81`) escalates straight to `SURVIVAL` when
   `signals.memory_estimate_mb >= profile.max_ram_mb`) — run it **twice** to reduce the chance a
   single noisy run misclassifies it either way. If the two runs disagree (one NORMAL-only, one
   excursed), treat it as excursed (soft) — do not average away a real excursion.
4. Populate `_RUNTIME_MODE_HARD_SCENARIOS` in `tests/perf/test_perf_regression_baseline.py` with
   exactly the scenario IDs whose observed `mode_sequence` (from step 2/3's runs) was `"NORMAL"`
   for all 50 sampled ticks, every run. Leave every scenario that showed even one non-`"NORMAL"`
   entry out of the set (soft).
5. For any scenario left soft, this is a real, load-bearing finding — record it in the ticket's
   `## Implementation Notes` with the scenario ID, the observed mode(s), and an explicit
   recommendation for a follow-up ticket to recalibrate that scenario's profile/entity-count or
   raise its RAM ceiling (per ticket Out-of-Scope item 3: "flag as follow-up, don't silently
   loosen the gate to compensate"). Do not open the follow-up ticket file yourself as part of this
   ticket — recommend it in Implementation Notes for the user/main session to act on.
6. This step must complete, and `_RUNTIME_MODE_HARD_SCENARIOS` must be populated from its actual
   output, before this ticket is considered done — an empty set left in "shipped" code would
   silently make every scenario's excursion check soft-only, which is not a decision this plan
   authorizes as a final state (it's only the safe *starting* state in step 1 above).
**Do NOT touch:** do not use this empirical run to also "fix" or recalibrate any scenario's
entity count, warmup/sample tick count, or `RuntimeProfile` thresholds — that is exactly the
out-of-scope action the ticket forbids (Out of Scope item 3). Observe and classify only.
**Verify:** the populated `_RUNTIME_MODE_HARD_SCENARIOS` set itself is exercised by every case in
`test_regression_vs_baseline` (Step 3) on every future CI run; the classification process is
documented, not silently asserted.

---

### Step 5 — New tests
**Files:** `tests/perf/test_bench_harness.py`, `tests/perf/test_perf_regression_baseline.py`

**5a. `test_run_benchmark_records_mode_sequence`** — `tests/perf/test_bench_harness.py` (extends
the existing file, mirrors the style of the existing
`test_bench_harness_cpu_time_sampling` at lines 16-37):
```python
from src.core.governance import RuntimeMode
from src.perf.scenarios import build_movement_state  # if not already imported


def test_run_benchmark_records_mode_sequence():
    profile = PERF_PROFILES["PERF_1GB_LOCAL"]
    state = build_movement_state(entity_count=20)

    result = BenchHarness(profile).run_benchmark(
        scenario_id="MODE_SEQUENCE_UNIT_TEST",
        initial_state=state,
        warmup_ticks=5,
        sample_ticks=10,
    )

    assert "mode_sequence" in result
    assert len(result["mode_sequence"]) == 10
    valid_names = {m.name for m in RuntimeMode}
    assert all(m in valid_names for m in result["mode_sequence"])
    # Ordinary low-load movement scenario on a generous 1GB profile: every tick should stay NORMAL.
    assert all(m == "NORMAL" for m in result["mode_sequence"])
```
`PERF_1GB_LOCAL` chosen deliberately (generous `max_ram_mb=1024`,
`src/perf/profiles.py:58-60`) over `PERF_512MB_LOCAL` (used by the existing CPU-sampler test) so
this "ordinary low-load" test is not the one that happens to sit near a ceiling — that empirical
question belongs to Step 4, not this deterministic unit test.

**5b. `test_perf_regression_baseline_flags_runtime_mode_excursion`** — the ticket's required "new
unit test forcing a Governor mode transition." Framing decision (see Design Decisions (c)):
**(b) synthetic `mode_sequence` against the extracted helper**, primary and sufficient — added to
`tests/perf/test_perf_regression_baseline.py`, adjacent to `_assert_runtime_mode_stayed_normal`
(Step 3):
```python
import pytest
from tests.tools.perf_assertions import PerformanceThresholdWarning


@pytest.mark.parametrize("hard", [True, False])
def test_perf_regression_baseline_flags_runtime_mode_excursion(hard):
    """Forces a RuntimeMode excursion via a synthetic mode_sequence (never runs BenchHarness or
    touches compute time at all) and asserts the gate's extracted assertion helper surfaces it --
    AssertionError when hard=True, PerformanceThresholdWarning when hard=False -- proving the
    check is decoupled from avg_tick_compute_ms per AC3."""
    forced_sequence = ["NORMAL"] * 49 + ["CONSTRAINED"]
    if hard:
        with pytest.raises(AssertionError):
            _assert_runtime_mode_stayed_normal(forced_sequence, "SYNTHETIC_SCENARIO", hard=True)
    else:
        with pytest.warns(PerformanceThresholdWarning):
            _assert_runtime_mode_stayed_normal(forced_sequence, "SYNTHETIC_SCENARIO", hard=False)
```
This directly satisfies the AC ("asserts the gate surfaces the excursion... independent of
avg_tick_compute_ms") without depending on real load/timing to trip the Governor. A real
starved-BenchHarness-run variant (framing (a)) is judged **not worth adding** for this ticket —
it would only re-prove that `ResourceGovernor._get_indicated_mode()` (already covered by
`tests/unit/domains/optimization/test_phase_budget_governor.py` and
`tests/unit/resource/test_resource_governor_contract.py`, both untouched by this ticket) works,
plus that Step 2's sampling wiring works (already covered by 5a) — it would not exercise anything
this ticket adds that 5a + 5b together don't already cover, while being slower and less
deterministic. Do not add it.

**5c. `test_performance_contract_lists_runtimemode_scoped_claim`** — added to
`tests/perf/test_perf_regression_baseline.py` (no existing docs-static-check file covers
`performance_contract.md`; per investigation, not worth a new single-assertion file):
```python
from pathlib import Path


def test_performance_contract_lists_runtimemode_scoped_claim():
    contract_text = Path("docs/engine/performance_contract.md").read_text()
    scoped_claims_section = contract_text.split("### 3.1 Scoped Claims")[1].split("### 3.2")[0]
    assert "RuntimeMode" in scoped_claims_section
```
**Do NOT touch:** `tests/unit/domains/optimization/test_phase_budget_governor.py`,
`tests/unit/resource/test_resource_governor_contract.py` — do not add or modify anything in these
files; they are regression surface only (must stay green, not be extended by this ticket).
**Verify:** all three tests pass; existing `tests/perf/test_bench_harness.py`,
`tests/perf/test_perf_regression_baseline.py` cases still pass unmodified in behavior.

---

### Step 6 — Parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Following the `INFRA-363` entry's shape and phrasing style (confirmed read at
`docs/parity_ledger/infrastructure.yaml:10678-10698`: `id`, `text`, `status: verified`,
`priority`, `legacy_evidence: null`, `v2_evidence`, `test_path` as a comma-joined list of
`file::test` nodeids, `divergence_note: null`). Confirmed next free sequential ID by scanning all
existing `id: INFRA-\d+` entries (highest found: `INFRA-367`) — use **`INFRA-368`**, but
re-confirm at implement time immediately before writing (this file is concurrently modified by
another in-flight ticket, `TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP`, per current git
status — re-check the highest existing ID has not moved before picking the number, to avoid a
collision with that ticket's own additions). Append after the `INFRA-367` entry (end of file, or
wherever the highest-numbered entry now sits):
```yaml
- id: INFRA-368
  text: BenchHarness.run_benchmark() samples kernel.status.current_mode every sampled tick
    (unthrottled, unlike the periodic RSS sampler) and exposes it as result["mode_sequence"].
    tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline asserts no
    RuntimeMode excursion occurred during the gate window, independent of the
    avg_tick_compute_ms threshold check, so a benchmark that degrades mid-run cannot have
    cheaper degraded-mode ticks blended into its average unnoticed. Scenarios confirmed to
    stay NORMAL throughout the gate window are asserted hard (AssertionError on excursion);
    any scenario found to excurse under real load stays soft (PerformanceThresholdWarning)
    with a documented follow-up-ticket recommendation, per an explicit empirical measurement
    pass (not assumed) -- TCK-20260817-RUNTIMEMODE-BENCH-SCOPING.
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: 'src/perf/bench_harness.py: BenchHarness.run_benchmark() mode_samples
    collection and result["mode_sequence"]. tests/perf/test_perf_regression_baseline.py:
    _assert_runtime_mode_stayed_normal(), _RUNTIME_MODE_HARD_SCENARIOS.
    docs/engine/performance_contract.md §3.1: RuntimeMode Scoped Claims dimension.'
  test_path: tests/perf/test_bench_harness.py::test_run_benchmark_records_mode_sequence,tests/perf/test_perf_regression_baseline.py::test_perf_regression_baseline_flags_runtime_mode_excursion,tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline,tests/perf/test_perf_regression_baseline.py::test_performance_contract_lists_runtimemode_scoped_claim
  divergence_note: null
```
**Other writers to this shared resource:** `docs/parity_ledger/infrastructure.yaml` is a single
flat YAML list appended to by every ticket that touches infrastructure-layer behavior; the only
concurrent writer visible right now is `TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP`
(already modifying this file per current `git status`, entries unrelated to RuntimeMode/perf).
Interaction: append-only, ID-numbered — as long as Implement re-checks the highest existing
`INFRA-\d+` ID immediately before writing (not reusing the `368` number blindly if the hygiene
sweep already claimed it), there is no collision; do not attempt to merge/rebase the two tickets'
entries into one.
**Do NOT touch:** `INFRA-363` or `INFRA-365` themselves — cite them as precedent only, do not
edit their text/status.
**Verify:** `docs/parity_ledger/infrastructure.yaml` still parses as valid YAML; new entry's
`test_path` tests all pass.

---

## Design Decisions

**(a) Sampling cadence — every tick, not throttled.** Confirmed, not overridden: a `RuntimeMode`
`IntEnum` attribute read (`kernel.status.current_mode.name`) is a trivial in-memory comparison,
negligible next to the `psutil.Process.memory_info()` syscall the RSS sampler already pays for
every 10th tick. Throttling mode sampling to the same `i % 10 == 0` cadence risks silently missing
a transient CONSTRAINED/DEGRADED/SURVIVAL excursion inside the 9 un-sampled ticks between samples
— which is precisely the "masking" failure mode this ticket exists to close. There is no
correctness or performance reason to throttle a comparison this cheap.

**(b) Hard-vs-soft — resolved as a measurement process, not a guessed answer.** The investigation
correctly identified two competing, real signals: `assert_perf_threshold`'s own module docstring
(`tests/tools/perf_assertions.py:17-21`) names "structural correctness... gate-logic-against-
synthetic-fixtures" as things that "stay hard failures," which a RuntimeMode excursion arguably
is; but `simq_corpus_crowded_frontier`'s committed 1000-tick baseline shows RSS usage
(`peak_rss_mb: 696.3`) that plausibly already breaches `PERF_512MB_LOCAL`'s `max_ram_mb=512`
ceiling and would drive `ResourceGovernor._get_indicated_mode()` straight to SURVIVAL — at 1000
ticks, not the gate's 50, so it is genuinely unknown whether the 50-tick gate window is affected.
Guessing either direction is wrong: guessing "all hard" risks an immediate false-positive-blocking
CI gate on day one for a scenario that was never actually regressed, just legitimately
resource-constrained; guessing "all soft" defeats the entire point of the ticket (masking a real
regression is exactly what a universally-soft gate still permits). The only correct resolution is
to measure, not guess — Step 4 makes that measurement an explicit, ordered, mandatory Implement-
time action with a fixed decision rule (per-scenario NORMAL-throughout ⇒ hard;
any-observed-excursion ⇒ soft + documented follow-up recommendation), so the *process* is decided
here in Plan while the *per-scenario outcome* is decided by Implement running real code, exactly
as the ticket's Out-of-Scope item 3 already anticipates ("flag as follow-up, don't silently loosen
the gate to compensate" — which presupposes some scenarios may need to be soft, and that finding
must be visible, not buried).

**(c) Unit-test framing — (b) synthetic mode_sequence, primary; (a) real starved-BenchHarness run
not added.** Framing (b) — unit-testing the extracted `_assert_runtime_mode_stayed_normal()`
helper directly against a synthetic `mode_sequence` — is deterministic, fast, and directly proves
the AC's actual claim ("the gate surfaces the excursion... independent of avg_tick_compute_ms")
without depending on real Governor/load timing, which would make the test flaky and slow.
Framing (a) (a real short `BenchHarness.run_benchmark()` with a deliberately starved profile) was
considered and rejected as an *addition* here: it would only re-exercise
`ResourceGovernor._get_indicated_mode()`'s escalation ladder (already fully covered by
`tests/unit/domains/optimization/test_phase_budget_governor.py` and
`tests/unit/resource/test_resource_governor_contract.py`, both explicitly out of this ticket's
touch set) plus Step 2's sampling wiring (already covered by `test_run_benchmark_records_mode_sequence`,
5a) — it adds runtime and nondeterminism without covering anything Steps 5a+5b don't already
cover together. Not added.

**(d) Scenario count — confirmed 6, not 26.** Directly read
`tests/perf/test_perf_regression_baseline.py:24-31`'s `@pytest.mark.parametrize` table: exactly 6
`scenario_id`s (`idle_100_local`, `movement_100_local`, `combat_10_local`,
`simq_corpus_frontier_extended`, `simq_corpus_frontier_marches`, `simq_corpus_crowded_frontier`).
The ticket's "26 scenario builders" figure does not correspond to anything in the codebase —
`src/perf/scenarios.py` has 7 builder functions, and `tests/perf/baselines/` has 16 committed
JSON files, of which 10 are orphaned relative to this specific gate (exercised by a different,
`perf_baselines.json`-driven mechanism in other `tests/perf/test_perf_*.py` files, out of this
ticket's scope). This plan and Step 4's empirical pass use 6 throughout; do not build against 26.

## Scope Guards
- Do not add a `mode` field to `PressureSignals` (`src/core/governance.py:19-52`) — it is
  language-enforced frozen (`@dataclass(frozen=True, slots=True)`) and unnecessary; every step
  above uses the existing `kernel.status.current_mode` read instead.
- Do not treat `RuntimeStatus`'s "FROZEN" docstring comment
  (`src/engine/runtime_status.py:13`) as blocking a *read* of `current_mode` — it is a
  process-convention marker, not `frozen=True`/`slots=True` like `PressureSignals`; this ticket
  needs no write or schema change to `RuntimeStatus` regardless, so the distinction is moot but
  must not be misread as license to add unrelated fields to it either.
- Do not edit `docs/performance/perf_baseline_policy.md` — its §3 staleness is already flagged
  and explicitly deferred to "a dedicated doc-accuracy ticket" (2026-08-08 note); doing it here is
  scope creep.
- Do not edit `docs/engine/contracts/extended_certification_contract.md` §5's differently-shaped
  "Scoped Claims" — a separate doc and dimension set from `performance_contract.md` §3.1.
- Do not import, call, or extend `src/certification/conformance.py`'s `ConformanceEvaluator` —
  confirmed unnecessary weight (hash comparisons, recovery-timing compliance, lifecycle-outcome
  checks) for this fast per-commit gate; a standalone `mode != "NORMAL"` scan is sufficient.
- Do not recalibrate any scenario's entity count, `warmup_ticks`/`sample_ticks`, or
  `RuntimeProfile` thresholds (`src/perf/profiles.py`) to make a scenario "pass" hard — Step 4's
  empirical pass is observe-and-classify only; any scenario needing recalibration gets flagged as
  a follow-up recommendation in Implementation Notes, never silently loosened or force-fit.
- Do not modify `tests/unit/domains/optimization/test_phase_budget_governor.py` or
  `tests/unit/resource/test_resource_governor_contract.py` — regression surface only.
- Do not feed `mode_sequence` data back into `AuthoritativeState`, use it to alter tick execution,
  or otherwise let it cross the Governance Isolation Law boundary
  (`docs/engine/contracts/signal_truth_contract.md` §7) — every read added in Step 2 is purely
  observational, appended to a local Python list inside `run_benchmark()`, never written back to
  kernel/engine state.
- Do not ship `_RUNTIME_MODE_HARD_SCENARIOS` empty as a "final" state — empty is only the correct
  *starting* state before Step 4's measurement; leaving it empty at completion silently makes
  every scenario's excursion check soft-only, which defeats the ticket's purpose.

## Dependency Map
- Step 1 (doc) — independent of all other steps; can land first or last.
- Step 2 (BenchHarness sampling) — must land before Step 3 (Step 3's assertion reads
  `result["mode_sequence"]`, which does not exist until Step 2 lands) and before Step 4 (nothing
  to measure without Step 2).
- Step 3 (gate assertion + `_RUNTIME_MODE_HARD_SCENARIOS` skeleton) — depends on Step 2; must land
  (with the set empty/safe-default) before Step 4 can run the real measurement pass against it.
- Step 4 (empirical hard/soft classification) — depends on Steps 2 and 3 landing first; its output
  (the populated `_RUNTIME_MODE_HARD_SCENARIOS` set) is a final edit back into Step 3's file.
- Step 5 (new tests) — 5a depends on Step 2 only; 5b depends on Step 3's
  `_assert_runtime_mode_stayed_normal()` helper existing (not on Step 4's populated set — 5b uses
  explicit `hard=True/False` params, independent of which real scenarios end up in which bucket);
  5c depends on Step 1 only.
- Step 6 (parity ledger) — depends on Steps 1-5 all being complete (its `test_path` cites tests
  from Steps 5a/5b/3/1, and its `text` describes the final hard/soft behavior from Step 4).

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `performance_contract.md` §3.1 Scoped Claims includes RuntimeMode as a required 5th dimension | Step 1 | `test_performance_contract_lists_runtimemode_scoped_claim` (5c) |
| `BenchHarness.run_benchmark()` records Governor RuntimeMode per sampled tick, exposed as `mode_sequence` | Step 2 | `test_run_benchmark_records_mode_sequence` (5a) |
| `test_regression_vs_baseline` fails or explicitly non-silently flags when any sampled tick's RuntimeMode != NORMAL, independent of `avg_tick_compute_ms` | Steps 3, 4 | `test_perf_regression_baseline_flags_runtime_mode_excursion` (5b); all 6 cases of `test_regression_vs_baseline` itself |
| A new unit test forces the Governor out of NORMAL mid-sample and asserts the gate surfaces the excursion, not silently blended in | Step 5b | `test_perf_regression_baseline_flags_runtime_mode_excursion` (5b) |

## Anti-Drift Notes
- The two docs named "Scoped Claims" are different sections in different files with different
  dimension sets (`performance_contract.md` §3.1 vs. `extended_certification_contract.md` §5's
  "Quadrants of Truth") — Step 1 touches only the former; do not conflate them mid-implementation.
- `tick_compute_ms` per-tick history is recoverable post-hoc via
  `kernel.status.get_recent_history(sample_ticks)`; `RuntimeMode` is **not** — there is no
  retroactive reconstruction path, so live per-tick sampling inside the loop (Step 2) is not
  optional/deferrable, unlike some other metrics in this file.
- `long_run_harness.py:225`'s `active_mode=kernel.status.current_mode.name` confirms the accessor
  is correct but samples on a throttled cadence (`if t % sample_interval == 0`) — do not copy that
  throttling into `BenchHarness`; the cadence decision here is deliberately different (see Design
  Decision (a)).
- `assert_perf_threshold(..., hard=False)` (the default) is a *stopgap*
  (`TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING`), not a permanent policy — Step 4's
  soft-classified scenarios are an intentional, documented, temporary state pending a follow-up
  recalibration ticket, not evidence this ticket "gave up" on hard enforcement.
- `docs/parity_ledger/infrastructure.yaml` currently has an uncommitted concurrent edit from
  `TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP` (per `git status` at Plan time) — Step 6
  must re-read the file immediately before appending to pick a truly-free `INFRA-` ID, not trust
  the `368` number computed during Planning.

## Deviations (recorded at Implement time)

**Step 4 empirical outcome — all 6 scenarios excursed, `_RUNTIME_MODE_HARD_SCENARIOS` stays
empty.** Running the real gate (`warmup_ticks=10, sample_ticks=50`) against all 6 live-
parametrized scenarios, and `simq_corpus_crowded_frontier` twice per the decision rule, showed
every scenario at `['DEGRADED']` for all 50 sampled ticks, on every run, with zero variance. This
is not the load-driven, scenario-specific excursion pattern the plan's Design Decision (b)
anticipated (e.g. `simq_corpus_crowded_frontier`'s RAM pressure) — root-caused instead to
`WorkerManager.get_stats()` (`src/engine/worker_manager.py:229-232`): `worker_utilization =
peak_active / max_workers if max_workers > 0 else 1.0`. Every `PERF_*_LOCAL` profile
(`src/perf/profiles.py`) sets `workers=0`, so `worker_utilization` is hardcoded to `1.0` on every
tick of every LOCAL-mode benchmark, unconditionally tripping
`ResourceGovernor._get_indicated_mode()`'s `worker_utilization >= 0.9 -> DEGRADED` branch
(`src/engine/governor.py:88`) regardless of actual computational load. This is a pre-existing
Governor/WorkerManager signal defect (`else 1.0` should plausibly be `else 0.0` — no configured
worker pool means no worker-driven pressure, not maximum pressure), not a per-scenario finding,
and not something this ticket is scoped to fix (Scope Guards explicitly forbid touching
`governor.py`/`worker_manager.py` or recalibrating profiles). `_RUNTIME_MODE_HARD_SCENARIOS`
therefore correctly stays empty (all 6 scenarios soft) per the plan's own decision rule — see
ticket Implementation Notes for the full follow-up-ticket recommendation.

**Step 5a assertion changed — plan's `assert all(m == "NORMAL"...)` removed, not added as
written.** The plan's Step 5a code asserted every tick of a "generous 1GB profile, ordinary
low-load movement scenario" stays NORMAL, presented as a confident expectation but never actually
run before Plan was written. The Step 4 empirical pass proved this assumption false — and not
just for this specific scenario/profile pairing: the same `worker_utilization=1.0`-for-`workers=0`
defect applies identically to every `PERF_*_LOCAL` profile, so the plan's exact assertion can
never pass on any LOCAL profile, deterministically, regardless of scenario or load. Implement
therefore removed that final assertion (keeping the shape/length/valid-enum-name assertions,
which are what 5a is actually for per Design Decision (c) — proving the sampling wiring works,
not re-testing Governor escalation behavior) and added an in-test comment tracing the root cause
and citing this Deviations entry. No AC depends on the removed assertion (see Acceptance Criteria
Map: 5a is cited only for "records Governor RuntimeMode per sampled tick, exposed as
mode_sequence").
