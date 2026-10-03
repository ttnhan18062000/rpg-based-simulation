---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE
artifact_type: investigation
tags: [simulation-quality, calibration, determinism, corpus]
---

# Investigation — TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE

## Current Behavior

### `_within_score_tolerance()` already supports a per-call override — it is simply
### never used by the two tests this ticket is scoped to fix

`tests/simulation_quality/test_grade_regression.py:172-185`:

```python
def _within_score_tolerance(
    actual_score: float,
    anchor_score: float,
    abs_floor: float = SCORE_TOLERANCE_ABS_FLOOR,
    rel_pct: float = SCORE_TOLERANCE_REL_PCT,
) -> bool:
    return abs(actual_score - anchor_score) <= max(abs_floor, rel_pct * abs(anchor_score))
```

`abs_floor`/`rel_pct` are already keyword-overridable parameters, defaulting to the
global constants (`SCORE_TOLERANCE_ABS_FLOOR = 0.05`, `SCORE_TOLERANCE_REL_PCT = 0.20`,
lines 46-47). **This override capability is already exercised in production code** — by
the parent ticket's own 14 `*_grade_stability` guards in
`tests/unit/worldassembly/test_corpus_diversity.py`, e.g.
`test_urban_political_seed123_1000t_social_economy_grade_stability` (line 933) calls
`_within_score_tolerance(mean_score, target["score"], abs_floor=target["abs_floor"])`
with a per-pillar, evidence-derived `abs_floor` (line 1030), and
`test_frontier_marches_seed42_200t_narrative_grade_stability` (line 1636) does the same
(line 1729). These guards import `_within_score_tolerance` directly from
`test_grade_regression.py` (line 988/1688) — no duplicate implementation exists.

What is **not** overridden: `test_grade_within_anchor_band` (line 230) and
`test_grade_within_anchor_band_long_run` (line 282) both call
`_within_score_tolerance(actual_score, anchor_score)` with **no** `abs_floor`/`rel_pct`
kwargs (lines 260, 314) — every one of the 76 anchors in `FAST_ANCHOR_KEYS`/
`SLOW_ANCHOR_KEYS`, including the 3 named risky ones, is checked against the same global
default width. This is the exact mechanism the ticket's Scope calls "the fixed-width
tolerance formula" — confirmed by direct read, not assumed.

**This resolves the ticket's own Assumption/Open Question #2** ("Whether an
evidence-derived-width mechanism... can be scoped as a per-pillar/per-anchor override...
is assumed but unverified") as **yes, verified, and the mechanism already exists in
`_within_score_tolerance`'s own signature** — remedy (a) does not require inventing a new
mechanism or touching `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT` (the global
defaults `test_within_band_default_tolerance_unchanged`-adjacent guards protect); it only
requires wiring a per-`(run_key, pillar)` override lookup into the two call sites at
lines 260 and 314, defaulting to the existing global constants for every anchor not in
the override table.

### Concrete evidence-derived widths already computed, sitting in the guard tests

The 14 grade_stability guards already computed and hard-coded per-pillar `abs_floor`
values from `repro_sweep.md`'s trial data (Step 14's live-widening rounds,
`repro_sweep.md` Section 8). For the 3 named risky pillars:

| run_key | pillar | committed anchor `score` (`grade_anchors.json`, confirmed via direct read) | guard's own `abs_floor` (test_corpus_diversity.py) | current global-default tolerance = `max(0.05, 0.20*|anchor|)` |
|---|---|---|---|---|
| `urban_political_seed123_1000t` | SOCIAL | 17.9655 | 2.9568 (line 996) | **3.5931** — already wider than the guard's own abs_floor; rel_pct dominates |
| `urban_political_seed123_1000t` | ECONOMY | 0.6564 | 0.2878 (line 997) | **0.13128** — narrower than the guard's own abs_floor by >2x |
| `frontier_marches_seed42_200t` | NARRATIVE | 0.6186 | 0.3351 (line 1696) | **0.12372** — narrower than the guard's own abs_floor by >2.7x |

**Interpretation**: SOCIAL's real risk is already implicitly bounded by the existing
20%-relative default (3.593 > guard's evidence-derived 2.957) — the score-tolerance
single-draw check is not actually under-tolerant for this specific pillar at the current
anchor value, though it remains close to the observed sample edges (Section 3:
15.116–20.454 across 5 samples spans ±2.85–2.49 from center 17.9655, both under 3.593).
ECONOMY and NARRATIVE are the two pillars with a **real, evidenced gap**: their global
default tolerance is materially narrower than the width the parent ticket's own repro
data required for the guard tests themselves to be reliable. These two are the ones a
single unlucky draw is most likely to fail against
`test_grade_within_anchor_band_long_run`/`test_grade_within_anchor_band`.

### CI's `slow` job — confirmed still one sequential in-process run, no isolation flag

`.github/workflows/test.yml:208-239`, the `slow` job:

```yaml
- name: Slow tests (includes 5k behavioral regression)
  run: |
    pytest tests/ -m "slow or extra_slow" --resource-budget large --tb=short -q
```

Single `pytest` invocation, one process, no `-n`/`--dist`/`-p xdist_...`/`--forked` flag
anywhere in this job or any other job in the file (confirmed via grep across
`.github/workflows/*.yml` and `Makefile` — zero matches for `xdist`, `-n auto`,
`pytest-forked`, `dist=`). The ticket's own scoping text ("one sequential in-process run
with no isolation/parallelism flag") is **still accurate** on this checkout.

### `pytest-xdist` / parallelism tooling — confirmed NOT a current dependency

`requirements.txt` (39 lines total) contains `pytest-asyncio==1.4.0` but no
`pytest-xdist`, `pytest-forked`, or any other parallelism/isolation plugin.
`pyproject.toml`'s `[tool.pytest.ini_options]` section registers markers but no
`addopts` referencing `-n`/`--dist`. `pip list` inside the project's venv confirms
`pytest-xdist` is not installed. **This resolves the ticket's Assumptions/Open Questions
first bullet**: the tool is not currently available; adopting remedy (b) via `xdist`
would require adding a new dependency, which is a larger decision (new third-party
dependency, CI image change) than a same-repo subprocess-splitting alternative described
below.

### `tests/conftest.py`'s `--resource-budget` hook — relevant constraint for remedy (b)

`pytest_runtest_setup` (`tests/conftest.py:50-84`) sets a **per-process** memory limit
(`resource.setrlimit(RLIMIT_AS, ...)`, 8 GB at `large`) and a **per-test** wall-clock
`SIGALRM` timeout (600s at `large`) before every test. Both mechanisms are
process-and-thread scoped (`SIGALRM` only fires in the process's main thread). This means:
- A `pytest-xdist`-based remedy (b) would run each worker as its own subprocess with its
  own independent `RLIMIT_AS`/`SIGALRM` state — the hook would work unmodified in each
  worker, but N workers each claiming up to 8 GB `RLIMIT_AS` needs headroom-checking
  against the CI runner's actual memory (GitHub-hosted `ubuntu-latest` runners are
  7 GB RAM as of standard tier — **a hard constraint worth flagging**: `-n 2` at
  `--resource-budget large` could already approach or exceed default runner memory,
  though `RLIMIT_AS` is a ceiling not a reservation, so this is a risk not a certainty).
- A no-new-dependency alternative — splitting the `-m slow` invocation into **multiple
  separate `pytest` subprocess calls** within the same CI step (e.g., one `pytest -k
  "grade_stability"` call per anchor, or a small number of batched calls) — achieves the
  same "fresh process, no cumulative session-load carryover" property without adding
  `pytest-xdist` as a dependency, since each subprocess starts a fresh interpreter and
  fresh `Kernel`/`RLIMIT_AS` state. This is not full parallelism (still sequential
  wall-clock, unless combined with backgrounding), but it directly targets the ticket's
  own hypothesized mechanism ("cumulative wall-clock compute pressure across a long
  sequential *in-process* session") since process boundaries reset any
  cross-test accumulation the current single long-lived interpreter carries (import
  caches, GC state, OS-level scheduler history/priority within that PID, etc.).

## Mechanics / Engine Constraints

- `docs/engine/kernel.md` §"Emergency Throttling", `docs/engine/performance_contract.md`
  §7 "Adaptive Phase Budget Governor" — govern the watchdog/throttle mechanism (F6) that
  is the root cause of the variance both remedies exist to accommodate or eliminate the
  observation conditions for. Confirmed unchanged since the parent ticket's
  investigation (read-only reference; this ticket's Out of Scope explicitly forbids
  touching `src/engine/kernel.py`).
- `docs/audits/D06_longrun_health.md` §F6 — the parent ticket's Section 4/6 repro data
  (200t-tier anchors showing genuine variance) already sharpened this section's ~tick
  300-320 onset hedge; this ticket does not need to re-derive that finding, only decide
  whether/how to harden test infrastructure against its consequences.
- No Mechanics Bible chapter governs SimQ scoring-tool test-infrastructure correctness
  (confirmed, consistent with both precedent investigations) — this remains a
  tooling-reliability concern, not a simulation-law concern.

## Parity Ledger Overlap

- **`docs/parity_ledger/infrastructure.yaml::INFRA-273`** (P2, `verified`) — directly
  documents the F6-blast-radius confirmation this ticket's residual-risk finding derives
  from. Its `v2_evidence` cites `repro_sweep.md` Sections 2-7 and the eval-matrix "Part 2"
  subsection; its `test_path` cites the 14 `grade_stability` guards
  (`-k "grade_stability"`), all green in isolation. **This entry does not yet document
  the two residual risks this ticket investigates** (single-draw fixed-tolerance risk;
  session-load flake in the 32-test `-m slow` file) — those live only in INFRA-272's
  `test_path` NOTE (below) and this ticket's own inprogress ticket text. Whichever
  remedy is adopted should either extend INFRA-273's `v2_evidence`/`test_path` or add a
  new entry, per the ticket's own AC #4.
- **`docs/parity_ledger/infrastructure.yaml::INFRA-272`** (P1, `verified`) — its
  `test_path` field already carries a `NOTE` (lines 4260-4268) stating the exact residual
  risk this ticket investigates almost verbatim: "the single-draw parametrized
  `test_grade_within_anchor_band`/`test_grade_within_anchor_band_long_run` cases for a
  handful of these 14 anchors' most-volatile pillars (confirmed:
  `urban_political_seed123_1000t`/SOCIAL and /ECONOMY,
  `frontier_marches_seed42_200t`/NARRATIVE) have residual, inherent single-draw failure
  risk against `test_grade_regression.py`'s fixed ±0.05/20% tolerance." This is the exact
  three-pillar list the ticket names, confirmed to match. If remedy (a) is adopted, this
  NOTE becomes resolved and should be updated (not deleted — the honest history of why
  the anchor values are what they are should stay) to reference the new override
  mechanism and its `test_path`.
- No parity entry currently documents the 32-test `-m slow` file's ~1-in-16 session-load
  flake rate itself (the two full-sequential-run failures from Step 14) as a
  general CI-process property — this is new ground for this ticket to record, whichever
  remedy is chosen (including "neither, documented as accepted risk").

## Prior Work

- `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` (done, this session's immediate
  parent) — `repro_sweep.md` (Sections 2-8) is the direct evidentiary source for this
  ticket's Scope; `plan.md`'s Deviations #5 documents the exact 3-pillar residual-risk
  finding and the two full-sequential-run guard failures that motivated this follow-up
  ticket. The 14 `grade_stability` guards it added are the concrete precedent proving
  remedy (a)'s override mechanism already works in practice (see Current Behavior above)
  — this ticket's remedy (a), if adopted, is best understood as *extending an already-
  proven pattern* to two more call sites, not inventing a new one.
- `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` (done) — established the F6
  root-cause finding and the idle-vs-load repro methodology both this ticket and its
  parent build on. Its `repro_sweep.md` is the template `TCK-20260715`'s and any future
  repro work should continue to follow if additional live sampling is needed.
- `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` (done) — originated the tolerance-guard
  pattern (`test_generated_frontier_3_42_extended_population_stability`) that all 14 of
  the parent ticket's guards, and by extension this ticket's evidence base, are modeled
  on.

## Risks and Open Questions

1. **Blocking for remedy (a) scope decision**: whether an override table should cover
   only the 3 named pillars (`urban_political_seed123_1000t` SOCIAL/ECONOMY,
   `frontier_marches_seed42_200t` NARRATIVE) as the ticket's Scope literally states, or
   whether the same evidence (`repro_sweep.md`) implies other anchors among the 14 are
   at similar residual risk but were not flagged because they didn't fail during the
   parent ticket's specific Step 14 live-widening rounds. The ticket's Out of Scope
   section forbids "adding coverage for anchors/pillars not already named" — so this
   investigation treats the 3-pillar scope as fixed, but flags that a narrower
   evidence-derived-width fix leaves the other 11 anchors' single-draw checks at
   whatever residual risk they individually carry (unmeasured here, out of scope).
2. **Blocking for remedy (b) go/no-go**: whether CI runner memory headroom is sufficient
   for any parallelism approach that spawns multiple concurrent `--resource-budget large`
   processes (each claims up to 8 GB `RLIMIT_AS`). This was not empirically tested in
   this investigation (no CI run performed) — the Plan phase must either run a controlled
   comparison (per the ticket's AC #3) before adopting parallelism, or select the
   no-new-dependency subprocess-splitting alternative (which does not concurrently hold
   multiple 8 GB ceilings) to sidestep this risk entirely.
3. **The ~1-in-16 observed flake rate is still based on exactly 2 full-sequential-session
   samples** (2 failures across 2 runs of the 32-test file, both during the parent
   ticket's Step 14, not repeated independently by this investigation). This
   investigation did not add a 3rd/4th sequential run to firm up the estimate (would cost
   ~13 minutes each, non-trivial); the ticket's own AC #3 requires "at least one
   controlled comparison run" if remedy (b) is adopted — that comparison run doubles as
   an opportunity to gather a 3rd data point on the base rate.
4. **Whether the guard tests' own per-anchor `abs_floor` values (2.9568, 0.2878, 0.3351)
   are the correct override values to reuse in `test_grade_within_anchor_band`/
   `_long_run`, or whether the single-draw check (no trial-averaging, unlike the guards'
   3-trial mean) needs a wider floor than the guards' mean-of-3 tolerance to hold for a
   single draw.** The guards check `mean_score` across 3 trials against `abs_floor`; the
   fixed-tolerance tests check a **single** `actual_score` (no averaging) against
   whatever override is chosen. A single draw has higher variance than a 3-trial mean, so
   directly reusing the guards' `abs_floor` values verbatim may still be too narrow for
   the single-draw case — this needs an explicit decision at Plan time (e.g., widen by a
   further factor, or accept the guards' values as-is with a documented rationale for why
   single-draw and averaged-3-trial variance are treated as comparable here). Not
   resolved by this investigation — flagged for the Plan phase.
5. **`test_grade_anchor_file_exists_and_valid` and
   `test_within_band_default_tolerance_unchanged` are the two closest-adjacent existing
   guards any remedy (a) implementation must not break** — confirmed both exist and pass
   on the current checkout (lines 486, 547 of `test_grade_regression.py`); neither
   references `abs_floor`/`rel_pct` directly, so a per-run_key/per-pillar override table
   added alongside `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT` should not
   interact with either, but this must be re-verified at Implement/Verify time, not just
   assumed from this reading.

## Anti-Drift Hazards

- **Do not widen `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT` globally** as a
  shortcut — `test_within_band_default_tolerance_unchanged`
  (`test_grade_regression.py:547-553`) only guards `_within_band`'s default, not these
  two constants directly, but the ticket's own Scope and both precedent tickets'
  Anti-Drift Hazards are explicit that a global widening is out of bounds; any remedy (a)
  implementation must add a **narrow, per-`(run_key, pillar)` override**, not touch the
  module-level constants.
- **Do not silently expand the override table beyond the 3 named pillars** without an
  explicit, evidenced call-out (Out of Scope, restated from the ticket text) — even
  though this investigation found the mechanism trivially generalizes to any of the 14
  anchors, doing so unprompted is scope creep the ticket explicitly forbids.
- **Do not touch `src/engine/kernel.py`** — same hard constraint as both parent tickets;
  nothing in this investigation's findings implicates or requires touching it.
- **Do not modify any of the 14 `grade_stability` guards' own anchors, `abs_floor`
  values, or the 2 pre-existing precedent guards** — this ticket's remedy, if it reuses
  the guards' `abs_floor` values as a reference, must read them, not edit them at their
  source; any override table lives in `test_grade_regression.py`, not
  `test_corpus_diversity.py`.
- **If remedy (b) is adopted via `pytest-xdist`, do not overlook the `--resource-budget
  large` per-process 8 GB `RLIMIT_AS` interaction** — a naive `-n auto` addition to the
  `slow` CI job without checking runner memory headroom risks trading a rare score-flake
  for a much more disruptive OOM-killed CI job. This is a concrete new risk this
  investigation surfaces that the ticket text itself did not anticipate in this specific
  form.
- **Do not conflate "isolation" with "parallelism"** — the ticket's own Scope names both
  as candidate remedies for the same CI surface, but this investigation found they have
  different risk profiles (subprocess-splitting-for-isolation has no new-dependency or
  memory-headroom risk; `pytest-xdist`-for-parallelism has both). The Plan phase should
  treat these as two distinct options under remedy (b), not a single bundled decision.
