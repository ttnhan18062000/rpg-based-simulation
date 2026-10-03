---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE
artifact_type: plan
tags: [simulation-quality, calibration, determinism, corpus]
---

# Implementation Plan — TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE

**Plan Amendment (post first Review round):** architecture-reviewer found one fixable
violation, corrected in place below rather than as a separate addendum: Step 4's Makefile
target collected `-m slow` node IDs dynamically via `--collect-only | grep '::'` but never
asserted a minimum count before looping over them — if collection returned zero matches for
any reason (import error, marker-registration drift, a future rename that drops the `slow`
marker, environment misconfiguration), the `for` loop would iterate zero times, `status`
would stay `0`, and the target would exit success having run none of the file's 32 tests,
while Step 5 simultaneously removed the only other CI path that ran this file via
`--ignore`. This is strictly worse than the pre-amendment state, and Step 6's static
YAML/Makefile text-scan guard cannot catch it — it only detects textual/structural
regressions (hardcoded lists, a missing `--ignore` flag, wrong step ordering), not an empty
runtime collection result. Step 4 now asserts the collected node-ID count is `>= 32` and
fails loudly, before the per-nodeid subprocess loop runs, if collection comes back empty or
short. Step 6 is otherwise unchanged in nature (still static, still correct for what it
actually checks) — only its prose description and the Summary's claim about what it proves
are corrected below to stop overstating its coverage.

## Summary

Investigation confirms both residual risks named in the ticket's Scope are real and
narrow enough to fix directly — **both remedy (a) and remedy (b) are adopted**, neither
is "neither." Remedy (a): `_within_score_tolerance()`
(`tests/simulation_quality/test_grade_regression.py:172-185`) already accepts
`abs_floor`/`rel_pct` override kwargs — the parent ticket's 14 `grade_stability` guards
already use them. `test_grade_within_anchor_band`/`_long_run` (lines 260, 314) simply
never pass them. The fix is a 2-entry lookup table (`urban_political_seed123_1000t`
ECONOMY, `frontier_marches_seed42_200t` NARRATIVE — reusing the guards' own
evidence-derived `abs_floor` values verbatim) wired into those two call sites.
`urban_political_seed123_1000t` SOCIAL is deliberately excluded: its existing 20%-relative
default (3.5931) already exceeds the guard's own evidence-derived floor (2.9568), so no
override is needed there — confirmed by direct arithmetic in investigation.md, not
assumed. Remedy (b): the CI `slow` job (`.github/workflows/test.yml:228-230`) runs
`test_corpus_diversity.py`'s 32 `-m slow` guards as part of one long sequential
in-process `pytest` invocation. Per investigation, `pytest-xdist` is not a current
dependency and would add real, previously-unmitigated CI-runner memory-pressure risk
(each worker independently claims up to 8 GB `RLIMIT_AS` under `--resource-budget large`,
concurrently, against GitHub-hosted runners' ~7 GB). Every test in the file is
self-contained (grep-confirmed: no module/session-scoped fixtures spanning tests), so a
no-new-dependency, sequential subprocess-per-test split fully resets interpreter/OS-level
session state between tests without ever holding more than one 8 GB ceiling at a time —
this sidesteps the memory-pressure risk entirely rather than merely reducing it, which is
why it is chosen over `xdist` parallelism. The plan adds a new Makefile lane
(`simq-corpus-diversity-slow-isolated`) that dynamically collects the file's `-m slow`
node IDs, asserts the collected count is at least 32 (failing loudly rather than silently
running nothing if collection comes back empty or short), and runs each collected node ID
as its own `pytest` subprocess; wires it into the CI `slow` job ahead of the existing
invocation (which gets an `--ignore` flag added so the file isn't double-run); and adds a
static architecture-guard test that catches textual/structural regressions in that wiring
(a hardcoded node-ID list, a missing `--ignore` flag, wrong step ordering) — the guard
against a runtime empty-collection result lives in the Makefile target's own count
assertion, not in this static test. A controlled-comparison artifact records isolated vs.
sequential-baseline run results to firm up the thin 2-sample flake-rate estimate. Parity
ledger (`INFRA-272`, `INFRA-273`) and `eval_matrix_results.md` are updated to close out
both residual risks; none of the 14 guards, `grade_anchors.json`, or
`src/engine/kernel.py` are touched.

## Steps

### Step 1 — Add the evidence-derived score-tolerance override table

**Files:** `tests/simulation_quality/test_grade_regression.py`

**Change:** Immediately below `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT`
(currently lines 46-47), add:

```python
# Evidence-derived per-(run_key, pillar) score-tolerance overrides for anchors with
# confirmed real-world single-draw variance exceeding the global default width.
# Values are reused verbatim from the corresponding tests/unit/worldassembly/
# test_corpus_diversity.py `*_grade_stability` guard's own `abs_floor` — see
# stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md
# Section 8 for derivation. Section 8 shows both floors were widened against
# independent single fresh-draw samples (not only 3-trial means: e.g. ECONOMY's floor
# was set after two independent single-draw evaluate_simq.py runs, not a trial mean),
# so no additional single-draw safety multiplier is applied on top of the guards'
# committed value — TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE investigation.
#
# urban_political_seed123_1000t/SOCIAL is intentionally NOT in this table: its existing
# 20%-relative global default (3.5931) already exceeds the grade_stability guard's own
# evidence-derived floor (2.9568) — the single-draw check is not actually under-tolerant
# for that pillar at the current anchor value, so adding a redundant override would be
# unjustified scope creep. Do not add it without new evidence.
SCORE_TOLERANCE_OVERRIDES: dict[tuple[str, str], float] = {
    ("urban_political_seed123_1000t", "ECONOMY"): 0.2878,
    ("frontier_marches_seed42_200t", "NARRATIVE"): 0.3351,
}


def _score_tolerance_kwargs(run_key: str, pillar: str) -> dict[str, float]:
    """Return abs_floor override kwargs for _within_score_tolerance, or {} for the
    global default (SCORE_TOLERANCE_ABS_FLOOR/SCORE_TOLERANCE_REL_PCT)."""
    abs_floor = SCORE_TOLERANCE_OVERRIDES.get((run_key, pillar))
    return {"abs_floor": abs_floor} if abs_floor is not None else {}
```

**Do NOT touch:** `SCORE_TOLERANCE_ABS_FLOOR`, `SCORE_TOLERANCE_REL_PCT` (module-level
constants) — the override table sits alongside them, it does not replace or parameterize
them. Do not add a third entry for SOCIAL or any anchor outside the 2 named here.

**Verify:** No test yet exercises this table (added in Step 3); at this step, confirm the
file still imports cleanly: `python3 -c "import tests.simulation_quality.test_grade_regression"`.

---

### Step 2 — Wire the override lookup into the two anchor-band call sites

**Files:** `tests/simulation_quality/test_grade_regression.py`

**Change:** In `test_grade_within_anchor_band` (currently line 260) and
`test_grade_within_anchor_band_long_run` (currently line 314), change:

```python
if not _within_score_tolerance(actual_score, anchor_score):
```

to:

```python
if not _within_score_tolerance(
    actual_score, anchor_score, **_score_tolerance_kwargs(run_key, pillar)
):
```

in both places. `run_key` and `pillar` are already in scope in both loops (the
parametrized `run_key` argument and the `for pillar, anchor in anchors.items():` loop
variable respectively) — no new variables needed.

**Do NOT touch:** `_within_band`/the band-tolerance check (`if not _within_band(...)`)
immediately above each edited line — remedy (a) only touches the score-tolerance branch.
Do not touch `test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
`test_urban_political_selfmodel_execution_isolated_grade_anchor`, or
`test_information_intent_execution_fires_through_kernel_tick_once` later in the file —
unrelated, must not regress from a shared-import edit.

**Verify:** `pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_catches_within_band_regression -v`
(uses `_within_score_tolerance` directly with no override — must still fail the synthetic
regression exactly as before, proving the default path is unchanged for calls that don't
pass a run_key/pillar).

---

### Step 3 — Add anti-drift guard tests for the override table + confirm real (non-skip) pass behavior

**Files:** `tests/simulation_quality/test_grade_regression.py`

**Change:** Add two new tests adjacent to `test_within_band_default_tolerance_unchanged`
(line 547) and `test_grade_anchors_entry_count_unchanged`:

```python
def test_score_tolerance_override_table_scoped_to_named_pillars() -> None:
    """Anti-drift guard: the override table contains exactly the 2 evidence-derived
    entries (SOCIAL intentionally excluded, see module comment) and each entry widens
    -- never narrows -- the tolerance relative to the global default for that anchor's
    committed score."""
    assert set(SCORE_TOLERANCE_OVERRIDES.keys()) == {
        ("urban_political_seed123_1000t", "ECONOMY"),
        ("frontier_marches_seed42_200t", "NARRATIVE"),
    }
    anchors = json.loads(FIXTURE_PATH.read_text())
    for (run_key, pillar), abs_floor in SCORE_TOLERANCE_OVERRIDES.items():
        anchor_score = anchors[run_key][pillar]["score"]
        default_width = max(
            SCORE_TOLERANCE_ABS_FLOOR, SCORE_TOLERANCE_REL_PCT * abs(anchor_score)
        )
        assert abs_floor > default_width, (
            f"{run_key}/{pillar}: override abs_floor {abs_floor} does not widen the "
            f"default tolerance {default_width}"
        )


def test_score_tolerance_overrides_do_not_affect_unlisted_anchors(grade_anchors: dict) -> None:
    """Anti-drift guard: for every (run_key, pillar) NOT in SCORE_TOLERANCE_OVERRIDES
    (including urban_political_seed123_1000t/SOCIAL), the lookup helper must fall through
    to the global defaults -- byte-identical to calling _within_score_tolerance with no
    kwargs at all."""
    checked = 0
    for run_key, anchors in grade_anchors.items():
        for pillar in anchors:
            if (run_key, pillar) in SCORE_TOLERANCE_OVERRIDES:
                continue
            assert _score_tolerance_kwargs(run_key, pillar) == {}, (
                f"{run_key}/{pillar} unexpectedly has a tolerance override"
            )
            checked += 1
    assert checked > 0
```

Then regenerate local calibration data for the 2 affected run_keys (gitignored,
`data/calibration/` is empty on a fresh checkout — confirmed via `git ls-files
data/calibration | wc -l` = 0 — so `test_grade_within_anchor_band`/`_long_run` currently
SKIP for these two run_keys rather than pass; this is expected and matches every other
anchor's behavior on a fresh checkout, not a defect):

```bash
python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks 1000
python3 tools/calibrate_simq.py --name frontier_marches --seed 42 --ticks 200
```

**Do NOT touch:** `test_grade_anchor_file_exists_and_valid`,
`test_grade_anchors_entry_count_unchanged`, or `grade_anchors.json` itself — read-only
references for these new tests.

**Verify:**
```bash
pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars -v
pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_overrides_do_not_affect_unlisted_anchors -v
pytest tests/simulation_quality/test_grade_regression.py::test_within_band_default_tolerance_unchanged -v
pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged -v
pytest "tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band[frontier_marches_seed42_200t]" -v
pytest "tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]" -m slow --resource-budget large -v
```
The last two must show `1 passed` (not skipped) after the calibration regen — this is the
concrete proof the override is wired in and does not itself introduce a false pass.

---

### Step 4 — Add the isolated-lane Makefile target for `test_corpus_diversity.py`'s `-m slow` guards

**Files:** `Makefile`

**Change:** Add a new target near `simq-full-audit-slow` (~line 313), following the
repo's existing multi-step-shell-with-exit-code-aggregation pattern (see
`simq-full-audit`, lines 298-305). The minimum-count assertion below is **load-bearing,
not an afterthought** — it must run and be able to abort the target *before* the
per-nodeid subprocess loop starts, so an empty or short collection result fails loudly
instead of the loop silently iterating zero times while the target exits 0:

```makefile
simq-corpus-diversity-slow-isolated: ## [slow] Run test_corpus_diversity.py's -m slow guards as isolated per-test subprocesses (no cumulative-session-load carryover, TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE)
	@nodeids=$$($(PYTHON) -m pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large --collect-only -q | grep '::' || true); \
	nodeid_count=$$(echo "$$nodeids" | grep -c '::' || true); \
	if [ "$$nodeid_count" -lt 32 ]; then \
	  echo "ERROR: expected >=32 tests from test_corpus_diversity.py -m slow, collected $$nodeid_count -- aborting, not silently passing (collection failure, marker drift, import error, or misconfiguration)"; \
	  exit 1; \
	fi; \
	status=0; \
	for nodeid in $$nodeids; do \
	  echo "[isolated] $$nodeid"; \
	  $(PYTHON) -m pytest "$$nodeid" --resource-budget large --tb=short -q || status=1; \
	done; \
	exit $$status
```

Node IDs are collected **dynamically** via `--collect-only` on every invocation — this is
deliberate, not incidental: a hardcoded list of the current 32 test names would silently
stop covering any test added or renamed later (this is the anti-drift risk Step 6's guard
test checks for on the *textual* side — see Step 6's corrected description below). The
`nodeid_count -lt 32` check is a **separate, runtime** protection: it guards against the
collection step itself coming back empty or short for any reason (import error, a future
edit that drops the `slow` marker from some tests, environment misconfiguration, a
`--collect-only` invocation error swallowed by the `|| true` on the first line) — a failure
mode no static text scan can detect, because the Makefile text would look correct right up
until the moment `--collect-only` actually runs and returns nothing. `32` is hardcoded as
the *minimum expected count*, not the node-ID list itself: it is the ticket's own named
total for this file (14 new `grade_stability` guards + 18 pre-existing), so the assertion
is a floor that only needs revisiting if the file's slow-marked test count is deliberately
changed, not something that silently drifts with normal test-list churn the way a
hardcoded node-ID list would. Confirmed via
`pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large
--collect-only -q` → `32/87 tests collected`, and via grep that no test function in the
file relies on a module/session-scoped fixture shared across tests (each
`*_grade_stability`/`*_bit_identical_under_load`/`*_population_stability` test builds its
own engine run and hub internally) — per-test subprocess isolation is architecturally safe
for this file.

**Do NOT touch:** `lane-legacy-regression`, `simq-full-audit`, `simq-full-audit-slow`, or
any other existing Makefile target — this is a new, additive target only.

**Verify:** `make simq-corpus-diversity-slow-isolated` runs to completion locally and
exits 0 when all 32 tests pass (this doubles as the first controlled-comparison sample in
Step 7 — no need to re-run it solely for this step's verification). Additionally, during
implementation, manually verify the count assertion actually trips: run the target's
collection line by hand against a query that returns fewer than 32 matches (e.g.
temporarily substitute a narrower `-k` filter, or point `--collect-only` at a
nonexistent/empty path) and confirm the target prints the `ERROR: expected >=32 tests...`
message and exits non-zero *before* any subprocess in the per-nodeid loop runs. This is a
one-time implementation-time smoke check, not a new permanent automated test (Step 6 stays
static-only, per its corrected description below) — its purpose is to prove the guard
fires in practice, not to add ongoing CI coverage beyond what Steps 4-6 already provide.

---

### Step 5 — Wire the isolated lane into CI's `slow` job, ignore the file in the main invocation

**Files:** `.github/workflows/test.yml`

**Change:** In the `slow` job (currently lines 208-239), insert a new step immediately
before the existing "Slow tests (includes 5k behavioral regression)" step (currently
lines 228-230), and add `--ignore=tests/unit/worldassembly/test_corpus_diversity.py` to
the existing step's command:

```yaml
      - name: Slow tests — corpus diversity (isolated per-test, TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE)
        run: make simq-corpus-diversity-slow-isolated
      - name: Slow tests (includes 5k behavioral regression)
        run: |
          pytest tests/ -m "slow or extra_slow" --resource-budget large --tb=short -q --ignore=tests/unit/worldassembly/test_corpus_diversity.py
```

**Do NOT touch:** the `slow` job's `if:` condition (`github.ref == 'refs/heads/main' ||
github.base_ref == 'main'`), its `needs:` list, or the subsequent `Legacy regression`
(`make lane-legacy-regression`) / `Upload certification report` steps — preserve exactly
as-is. Do not add `-n`/`--dist`/`pytest-xdist` anywhere, and do not add
`pytest-xdist` to `requirements.txt`.

**Verify:** `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"`
succeeds (valid YAML); manually confirm the `slow` job's step list contains both the new
isolated step and the modified `--ignore`-flagged step, in that order.

---

### Step 6 — Add the CI-coverage architecture guard test

**Files:** new file `tests/static/test_corpus_diversity_ci_isolation.py` (follows the
existing precedent `tests/static/test_ci_requirements_no_ml_stack.py` — same directory,
same text/YAML-scanning style, no live pytest execution inside the test)

**Change:** Add a static test module with:

1. `test_slow_ci_job_ignores_corpus_diversity_in_main_invocation()` — parses
   `.github/workflows/test.yml` (via `yaml.safe_load`), locates the `slow` job's steps,
   asserts one step's `run` contains
   `--ignore=tests/unit/worldassembly/test_corpus_diversity.py`.
2. `test_slow_ci_job_runs_corpus_diversity_isolated_lane()` — asserts a step in the same
   job's `run` invokes `make simq-corpus-diversity-slow-isolated`, and that this step
   appears **before** the ignore-flagged step in the job's step list (order matters: the
   isolated lane must not run after the file has already been excluded from an earlier,
   unrelated invocation shape change).
3. `test_isolated_lane_uses_dynamic_collection_not_hardcoded_list()` — reads `Makefile`
   text, locates the `simq-corpus-diversity-slow-isolated:` target body, asserts it
   contains `--collect-only` and does NOT contain any literal
   `test_*_grade_stability`/`test_*_bit_identical_under_load`/`test_*_population_stability`
   function name string (regex `test_\w+_(grade_stability|bit_identical_under_load|population_stability)`
   must not match inside the target body) — catches a future edit that silently swaps the
   dynamic collection for a hardcoded, staleness-prone list.

This guard test is **static/textual only** — it proves the CI YAML and Makefile *text*
have the right shape (the isolated lane is wired in, in the right order, using dynamic
collection syntax rather than a hardcoded list) and catches regressions like a hardcoded
node-ID list, a missing `--ignore` flag, or wrong step ordering. It does **not** execute
pytest collection and therefore cannot detect a *runtime* failure where `--collect-only`
legitimately returns zero or too few node IDs (import error, marker drift, environment
misconfiguration) — that protection is Step 4's own `nodeid_count -lt 32` assertion inside
the Makefile target itself, which runs live on every invocation of
`make simq-corpus-diversity-slow-isolated` (including in CI). Step 6 and Step 4's
assertion are complementary, not redundant: Step 6 catches someone editing the *wiring*
wrong; Step 4's assertion catches the wiring being right but the underlying collection
failing anyway.

**Do NOT touch:** any other file in `tests/static/`. Do not make this test execute
`pytest --collect-only` as a subprocess (keep it static/fast, consistent with the file's
sibling tests — no simulation runs, no `--resource-budget` needed).

**Verify:** `pytest tests/static/test_corpus_diversity_ci_isolation.py -v` (all new tests
pass); `pytest tests/static/ -v` (no regression in `test_ci_requirements_no_ml_stack.py`
or `test_no_direct_dirtyset_candidate_selection.py`).

---

### Step 7 — Run the controlled comparison and record results

**Files:** new artifact
`staging_artifacts/TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE/isolation_comparison.md`

**Change:** Run and record, following `repro_sweep.md`'s precedent format (run
conditions, per-anchor pass/fail, timing):
- At least 2 full runs of `make simq-corpus-diversity-slow-isolated` (isolated
  condition).
- At least 1 fresh full sequential run of
  `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget large -v`
  (sequential-baseline condition, a 3rd sample alongside the parent ticket's existing 2
  — cite `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md`
  Section 8 for those 2 prior samples rather than re-deriving them).

Record per-run: pass/fail per anchor, any budget_warning/watchdog_trip signal if visible
in test output, total wall-clock. Summarize whether the isolated condition shows 0
failures across its samples vs. the sequential condition's continuing ~1-in-16-ish rate
(3 samples: 2 failures from the parent ticket + this step's 1 new sample). State plainly
if the isolated-condition sample count (2) is still too thin for a strong statistical
claim — do not overstate certainty beyond what 2-3 samples support; the important claim
is architectural (subprocess isolation removes the mechanism, not just the symptom), not
purely statistical.

**Do NOT touch:** `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md`
— read-only precedent, cite it, do not edit it.

**Verify:** The artifact file exists and cites concrete run output (not placeholder
text) for every run claimed.

---

### Step 8 — Update the parity ledger (INFRA-272, INFRA-273)

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:**
- `INFRA-272` (line 4202): update the `NOTE` inside `test_path` (lines 4260-4268) to mark
  the single-draw residual risk **resolved**, not delete it — append (do not remove) a
  short pointer: "RESOLVED 2026-07-16 (TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE):
  `SCORE_TOLERANCE_OVERRIDES` in `test_grade_regression.py` now widens
  `urban_political_seed123_1000t`/ECONOMY and `frontier_marches_seed42_200t`/NARRATIVE;
  SOCIAL needed no override (global default already wider than the guard's own evidence
  floor — see that ticket's investigation.md). Guarded by
  `test_score_tolerance_overrides_do_not_affect_unlisted_anchors` and
  `test_score_tolerance_override_table_scoped_to_named_pillars`." Keep the original NOTE
  text above it intact (honest history, per investigation.md's own instruction).
- `INFRA-273` (line 4277): append to `v2_evidence` an "UPDATE 2026-07-16
  (TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE)" block citing
  `isolation_comparison.md` and summarizing the CI-isolation remedy; extend `test_path`
  to add `make simq-corpus-diversity-slow-isolated` alongside the existing `-k
  "grade_stability"` reference.

**Do NOT touch:** `INFRA-270`, `INFRA-271`, or any other entry in this file. Do not
change `status`/`priority` on either entry unless the investigation found the underlying
claim itself wrong (it did not — both remain `verified`).

**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`
succeeds; re-run each entry's cited `test_path` per the project's parity-ledger
discipline (commands from Steps 3, 4, 6, 7 above).

---

### Step 9 — Update `eval_matrix_results.md`

**Files:** `docs/simulation_quality/eval_matrix_results.md`

**Change:** Insert a new subsection immediately after the "Anchor Reliability
Verification, Part 2" subsection ends (currently ends at line 2147, right before "##
FACTION Coverage Closure — Phase 3" at line 2148) — do not edit Part 2's existing text.
New heading: `## Anchor Reliability Verification, Part 3 (TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE)`.
Content: both remedies adopted, the 2-pillar override table (SOCIAL excluded with
rationale), the CI isolation lane, and a pointer to `isolation_comparison.md` and the
parity ledger updates from Step 8 — summary only, not a re-derivation of Part 2's 14
per-anchor writeups.

**Do NOT touch:** Any existing subsection in this file, including "Anchor Reliability
Verification, Part 2" itself.

**Verify:** Manual read-through confirming the new subsection does not duplicate Part
2's per-anchor detail and correctly cross-references it instead.

---

### Step 10 — Record the remedy determination in the ticket and confirm scope guards held

**Files:** `tickets/inprogress/TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE.md`

**Change:** Fill in Implementation Notes with the rationale for adopting both remedy (a)
and (b) (satisfies AC #1), note AC #5 ("if neither adopted") does not apply since both
were adopted with evidence, and fill in Test Summary / Files Changed per the actual diff.

**Do NOT touch:** Scope, Out of Scope, or Acceptance Criteria sections — those stay as
originally filed.

**Verify:** `git diff --stat -- tests/unit/worldassembly/test_corpus_diversity.py
tests/simulation_quality/fixtures/grade_anchors.json src/engine/kernel.py` must be empty
(confirms AC #6 — no change to the 14 guards, `grade_anchors.json`, or the kernel
watchdog/throttle).

## Scope Guards

- No edit to any of the 14 `*_grade_stability` guards in `test_corpus_diversity.py`, or
  to the 2 pre-existing precedent guards (`test_urban_political_seed123_500t_cognition_bit_identical_under_load`,
  `test_generated_frontier_3_42_extended_population_stability`) — only the *invocation
  shape* around the file changes (Steps 4-6), never its content.
- No edit to `tests/simulation_quality/fixtures/grade_anchors.json`.
- No edit to `src/engine/kernel.py` (watchdog/throttle mechanism) — F6 is documented,
  intentional engine behavior; nothing in this ticket's scope touches it.
- No widening of `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT` (the global
  constants) — the override table (Step 1) is additive and per-`(run_key, pillar)` only.
- No override table entry for `urban_political_seed123_1000t`/SOCIAL, or for any anchor
  outside the 2 named — investigation found SOCIAL doesn't need one; adding one anyway,
  or generalizing the mechanism to other anchors "while we're at it," is scope creep the
  ticket's Out of Scope explicitly forbids.
- No `pytest-xdist` (or any other parallelism plugin) added to `requirements.txt` or
  invoked anywhere in `.github/workflows/test.yml` — the memory-pressure risk it
  introduces is exactly what subprocess-splitting was chosen to avoid.
- No change to the `slow` CI job's `if:`, `needs:`, `Legacy regression`, or `Upload
  certification report` steps.
- No change to `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`'s original
  `test_urban_political_seed123_500t_cognition_bit_identical_under_load` guard.
- No re-derivation of `docs/simulation_quality/eval_matrix_results.md`'s existing
  "Anchor Reliability Verification, Part 2" subsection — append a new Part 3, do not
  rewrite Part 2.
- No re-derivation of `INFRA-272`'s or `INFRA-273`'s original `text`/`v2_evidence` — only
  append UPDATE blocks and extend `test_path`, per the project's parity-ledger append
  convention for evolving entries.

## Dependency Map

- Step 2 depends on Step 1 (needs the table + helper to exist).
- Step 3 depends on Step 2 (tests exercise the wired call sites).
- Step 5 depends on Step 4 (CI step invokes the Makefile target added in Step 4).
- Step 6 depends on Steps 4 and 5 (guard test asserts both the Makefile target's shape
  and the CI YAML's step wiring exist).
- Step 7 depends on Steps 4 and 5 (needs the isolated lane runnable; does not require
  Step 6's static guard to already exist, though running it after Step 6 is fine).
- Step 8 depends on Steps 1-7 (cites their concrete evidence/results).
- Step 9 depends on Step 8 (cross-references the parity ledger update).
- Step 10 depends on all prior steps (final rationale + diff check).
- Steps 1-3 (remedy a) and Steps 4-7 (remedy b) are otherwise independent of each other
  and may be implemented in either order or interleaved.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — investigation determines remedy(a)/(b)/both/neither with cited rationale, recorded in Implementation Notes | Step 10 (recording); rationale itself is investigation.md + this plan's Summary | Manual read of ticket Implementation Notes |
| AC #2 — if remedy (a) adopted: mechanism designed, verified not to change outcome for other pillars, `test_within_band_default_tolerance_unchanged`-equivalent protection holds | Steps 1, 2, 3 | `test_score_tolerance_override_table_scoped_to_named_pillars`, `test_score_tolerance_overrides_do_not_affect_unlisted_anchors`, `test_within_band_default_tolerance_unchanged` |
| AC #3 — if remedy (b) adopted: concrete CI isolation/parallelism proposal designed, ≥1 controlled comparison run executed and recorded | Steps 4, 5, 6, 7 | `test_corpus_diversity_ci_isolation.py` (all 3 tests) + `isolation_comparison.md` + Step 4's own `nodeid_count -lt 32` collection-count assertion (manually smoke-verified once during implementation per Step 4's Verify clause, confirming it trips non-zero on a short/empty collection before the per-nodeid loop runs — not a standing automated test) |
| AC #4 — parity ledger + eval_matrix_results.md updated | Steps 8, 9 | YAML parse check + manual read |
| AC #5 — if neither remedy adopted, documented with reasoning | N/A — both adopted; Step 10 states explicitly why AC #5 does not trigger | Manual read of ticket Implementation Notes |
| AC #6 — no change to the 14 guards, `grade_anchors.json`, or `src/engine/kernel.py` unless evidence requires it | All steps (Scope Guards enforce this throughout) | Step 10's `git diff --stat` check |

## Anti-Drift Notes

- `data/calibration/` is gitignored and empty on a fresh checkout — `test_grade_within_anchor_band`/
  `_long_run` SKIP (not fail, not pass) for any run_key without a locally-regenerated
  report. This means remedy (a)'s override wiring is only actually *exercised* (not just
  present) when a developer runs `make calibrate`/`tools/calibrate_simq.py` locally — as
  Step 3 requires — or during a future recalibration sweep like the parent ticket's. It
  is never exercised by CI's `simulation-quality` job as currently configured (no
  calibration-regeneration step exists there). This is a pre-existing property of the
  test file, not something this ticket changes or needs to fix.
- The guards' `abs_floor` values reused verbatim in Step 1 (0.2878, 0.3351) were derived
  in `repro_sweep.md` Section 8 partly from *single* fresh-draw samples, not purely
  3-trial means — this is why no additional single-draw safety multiplier is applied.
  If a future session's evidence shows this reasoning was wrong for either pillar (e.g. a
  fresh single draw outside the current floor), that is new evidence for a future ticket,
  not a reason to silently pad these values now.
- Splitting `test_corpus_diversity.py`'s `-m slow` invocation into per-test subprocesses
  increases total wall-clock (pytest interpreter startup repeated ~32 times) — this is an
  accepted, disclosed tradeoff per investigation, not an oversight. Do not "optimize" it
  by batching multiple tests per subprocess without re-verifying that batching doesn't
  reintroduce the cumulative-session-load mechanism this ticket exists to eliminate.
- The isolated-lane Makefile target must keep using `--collect-only` for dynamic node-ID
  enumeration. A hardcoded list is the single most likely regression an implementer might
  introduce for "simplicity" — Step 6's guard test exists specifically to catch this.
- Sequential subprocess-splitting (chosen) never holds more than one `--resource-budget
  large` 8 GB `RLIMIT_AS` ceiling at a time — this is what makes it safe without live
  GitHub-runner access to verify memory headroom empirically. Do not reinterpret this as
  "memory headroom was tested" — it was structurally avoided, not measured. If a future
  ticket revisits `pytest-xdist` for wall-clock reasons, the memory-headroom question from
  this ticket's investigation remains open and must be answered before adopting it.

## Deviations (recorded during Implement)

1. **Step 3's calibration regen surfaced a 4th, previously-unnamed at-risk pillar**:
   3 independent fresh `urban_political_seed123_1000t` calibration draws (via
   `tools/calibrate_simq.py`) all showed NARRATIVE — no existing `grade_stability` guard,
   not named in investigation.md's 3-pillar list — landing 0.139-0.246 outside the
   default ±0.05/20% tolerance (anchor 0.6603; draws 0.5210/0.4340/0.4144; band check
   unaffected). Per Scope Guards ("No override table entry for ... any anchor outside the
   2 named"), no override was added. This means Step 3's own Verify clause
   ("must show 1 passed, not skipped") could not be achieved for
   `test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` with real
   calibration data on this checkout — the ECONOMY override itself is proven correctly
   wired and comfortably sufficient (deltas 0.0286-0.1237 across all 3 draws, well under
   0.2878), but the parametrized test as a whole fails on the unrelated, unscoped
   NARRATIVE pillar. Not hidden or worked around — disclosed in
   `docs/parity_ledger/infrastructure.yaml::INFRA-272`'s new NOTE block,
   `eval_matrix_results.md` Part 3, and the ticket's Implementation Notes, tracked in a
   named follow-up: `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE`.
2. **Step 7's controlled comparison did not show a clean, unambiguous improvement**: all
   3 of this session's own fresh runs (1 sequential baseline + 2 isolated) came back
   completely clean (0 failures), including the sequential-baseline sample that the
   original ~1-in-16 estimate predicted had roughly even odds of failing. The
   isolated-vs-sequential contrast recorded in `isolation_comparison.md` therefore rests
   on pooling this session's clean isolated samples against the *parent* ticket's 2 older
   failing sequential samples, not on a live within-session A/B difference. This is
   reported honestly in `isolation_comparison.md` and the parity ledger UPDATE rather
   than overstated as a proven fix — the remedy's justification is treated as
   architectural (isolation structurally removes the cross-test session-load carryover
   mechanism), not statistically confirmed by this comparison's thin sample size (5
   sequential-style + 2 isolated observations total).
3. No deviation in the Makefile target's shape, the CI wiring, the static guard test's
   design, or the two override-table entries themselves — all implemented exactly as
   specified in the (already-amended) plan above, including the Step 4 count-assertion
   smoke check (performed for real: temporarily pointed the target's `--collect-only` at
   a nonexistent file, ran `make simq-corpus-diversity-slow-isolated`, confirmed it
   printed the `ERROR: expected >=32 tests...` message and exited non-zero *before* any
   `[isolated]` subprocess line was printed, then reverted the Makefile to its real
   form).
