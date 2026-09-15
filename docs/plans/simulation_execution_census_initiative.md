---
status: active
layer: simulation
authority: P1
audience: agent
tags: [simulation-quality, audit, architecture]
---

# Plan — Simulation Execution Census

**Status, scoped 2026-09-13, built 2026-09-15.** Proposes an automated measurement of *which
simulation code actually has an effect in a real run*, to replace the manual auditing that has
been finding these defects one at a time. `tools/execution_census.py` implements §7's design
(reachability axis only — see §7.3's own effectiveness-axis scoping note). On-demand only; never
gates.

> [!IMPORTANT]
> **PRECONDITION — census output is provisional until determinism holds.** The tool's own first
> real `stability-check` run (`crowded_frontier`, 300 ticks, seed 42, run twice) reported
> **UNSTABLE**: 382 files showed differing branch-arc coverage between two identical runs, with the
> kernel's own wall-clock watchdog tripping mid-run in both (`Tick N exceeded budget`). This is
> measured, first-hand confirmation — not a hedge or a documented-but-unconfirmed risk — that
> `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` gates whether any census report can be
> trusted at all: coverage.py's own instrumentation overhead appears sufficient to trip the kernel's
> throttle more/differently across identical runs. **A `stability-check` must return STABLE for the
> world(s) in scope before any `report` output from this tool is treated as fact rather than a
> directional lead.** This is the load-bearing reason the earlier plan's §4 flagged this dependency
> at all, now confirmed rather than merely anticipated — the deferred ticket was set aside as CI
> noise; it now gates a diagnostic this arc has since built and invested in, which changes the
> basis that deferral was made on.

**The problem in one sentence:** a mechanism can be unit-tested, parity-verified, registered in the
pipeline, and executed every tick, while never once changing anything — and we currently have no
way to detect that except by someone choosing to look.

---

## 1 · The question is not new. The answer was wrong.

`docs/audits/D09_system_wiring.md` (2026-06-18) asked precisely this question, in its own words:

> *A feature can be unit-tested and parity-verified while never reaching `Kernel.tick_once()` on a
> real run. This audit closes that gap.*

Right question, good taxonomy — five statuses including `tick-live (cond)` for flag-gated code,
which anticipated a case we later hit repeatedly. Its method was `code-read`.

**It got the wrong answer on the exact features this arc later found inert.** Two examples, both
classified by D09 as live:

| D09 classification | Reality found 2026-09 |
|---|---|
| `BossService.check_for_boss_spawn()` — **`tick-live`** (cadence-gated, `world_dynamics.py`) | Runs every tick. Gated on `state.maturity >= 50`, which needs ~50,000 ticks against a corpus of 200–5,000-tick runs. Has never spawned a boss in any run. |
| `PaidInformationTransactionSystem` — **live pipeline phase** (E42C, Phase 6 in `pipeline.py:refine()`) | Runs every tick. Requires a registered `InformationProviderState`, which has zero construction sites anywhere in `src/`. Has never transacted. |

Both classifications are *correct about what they measured*. The function is called. The phase is
registered. Neither fact says anything about whether the mechanism does something, and only the
second question matters to a player.

**This is the core finding: `called` and `effective` are different properties, and every manual
method we have measures the first.** D09 did not fail through carelessness — it failed because
reading a pipeline registration cannot reveal that the collection being iterated is always empty,
or that the threshold being compared is never met. No amount of care fixes that; it needs
observation of a running simulation.

D09 is also three months stale and was never re-run.

---

## 2 · What the measurement should be

**Branch coverage over the SimQ corpus, differenced against test coverage.**

Line coverage is *not sufficient*, and the distinction decides whether this works:

- `PaidInformationTransactionSystem.enforce()` iterates an always-empty collection. The loop body's
  lines never execute → **line coverage catches it.**
- `check_for_boss_spawn()` evaluates `maturity >= 50` every tick and returns early. Every line in
  the function executes → **line coverage reports it as covered.** Only *branch* coverage shows the
  true-branch was never once taken.

The second shape is the more common one and the more dangerous, because it looks maximally alive.
Branch coverage is a requirement, not an optimisation.

**A live validating case, found 2026-09-13 after this document was drafted.** `GuildAction.visit()`
(`src/town/guild.py:27`) tests `if node.kind == "iron":`. The real catalog ID is `"iron_vein"` —
confirmed across 15 corpus worlds, none of which contain a node of kind `"iron"`. Instrumented
300-tick runs show `visit()` firing 4 and 7 times respectively and producing **zero leads on every
call**. The function executes; the guarded branch has never once been taken. Line coverage reports
it healthy; branch coverage reports it immediately. This bug was disclosed nowhere and was found by
hand, which is the cost this initiative exists to remove.

**It also demonstrates why a census must report every unreached branch, not the first one.** That
lead path had *two independent blockers* — a feature flag defaulting OFF and this string mismatch.
Fixing either alone yields no observable change whatsoever, so anyone testing the flag would
reasonably have concluded the flag was not the problem. Independent gates make incremental
verification actively misleading, and only a census that enumerates all of them lets someone see
that two things must change together.

**The signature we are looking for** is a set difference: *covered by the unit suite, never executed
(or never branch-taken) across the entire SimQ corpus.* That is the exact fingerprint of every
mechanism this arc has found dead, and it becomes a query instead of an investigation.

**Ride on the existing corpus, do not define a new one.**
`config/simulation_quality/corpus_registry.yaml` already enumerates the representative worlds with
tiers, seeds and run keys, and is itself generated (`make simq-corpus-registry`). A second
definition of "a representative set of runs" would drift from the first and we would then have two
disagreeing answers.

---

## 3 · Boundary with SimQ — both are needed

SimQ answers *"was this a good run?"*. The census answers *"did this code do anything?"*. Neither
substitutes for the other, and this arc produced a clean failure of each in isolation:

| Defect | Census | SimQ |
|---|---|---|
| Knowledge layer writes zero facts in 500 ticks | **Detects immediately** — the write path never executes | Sees a marginally duller world, cannot localise the cause |
| 235 recruitment contracts expiring unaccepted per run | **Blind** — every line ran, every branch taken, code behaving exactly as written | **Detects** — the outcome is observably wrong |

**The census is necessary and not sufficient.** It finds dead mechanisms. It cannot find live
mechanisms producing bad outcomes. This limitation must be stated in the tool's own output, not
only in this document — an instrument trusted beyond what it measures is how
`docs/parity_ledger/` came to certify ~1300 entries nobody had verified.

---

## 4 · What will make or break it

**False positives will kill adoption.** Error handlers, migration paths, defensive branches and
genuinely rare events will light up legitimately. If the report is mostly noise, people stop
reading it, and the tool becomes a thing that is run and ignored. It needs a suppression list where
every entry carries a **stated reason**, never a blanket ignore.

This repo has already paid for getting this wrong: `docs/audits/D11_dead_code.md` (2026-06-18) used
grep-based import counting and was found to have a **100% false-positive rate** — every flagged
orphan had a real importer, mostly via lazy imports. `tools/audit_unreachable_code.py` was later
built to avoid that failure mode and documents two further methodology bugs found while writing it.
Read that tool before designing this one; it is the same problem one layer down, and it already
encodes hard-won lessons (notably: test-only usage must not count as alive).

**Report first, gate later — if ever.** A gate that fires on legitimately-rare code teaches people
to bypass it. That is exactly the dynamic in `tests/tools/test_parity_index_baseline.py`, where an
equality assertion on a count of known-bad entries means correcting the ledger costs a hotfix ticket
while leaving it wrong costs nothing. A verification mechanism that penalises correction is worse
than none, because it teaches people not to look.

**Determinism is a prerequisite.** Instrumentation must not perturb the run, and the census is only
reproducible if the runs are. `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` has a
twice-confirmed root cause — the kernel's wall-clock mid-tick throttle breaks determinism when
`audit_mode=False`. That ticket is currently deferred. **If it stays deferred, this initiative
needs to know whether the census is stable across repeated identical runs before its output is
trusted** — a census that varies run to run cannot distinguish a dead mechanism from a flaky one.

**`coverage` is not currently a dependency.** It is absent from `requirements.txt`. Adding it is
small but real, and affects CI install time for every job.

---

## 5 · Open decisions

None of these should be resolved unilaterally:

1. **Does the census re-run D09's classification, or replace it?** D09's five-status taxonomy is
   good and should probably be reused — but it needs a sixth status distinguishing *called but never
   effective* from *called and effective*, which is the distinction it lacked and that caused its
   two wrong answers.
2. **Where does it run?** Attached to the existing SimQ corpus run, a separate periodic job, or
   on demand. Frequency trades against cost: instrumented full-corpus runs are not free.
3. **Report-only, or eventually a gate?** Section 4 argues strongly for report-first. Whether it
   ever becomes a gate should be decided after seeing a real false-positive rate, not before.
4. **Scope of instrumentation** — all of `src/`, or the subsystems the Mechanics Bible declares as
   gameplay features. The second is narrower and more meaningful; the first is simpler and catches
   things nobody thought to list.
5. **Does the census cover `tools/` and gate checks, not just `src/`?** It should be considered
   seriously, because **a verification mechanism that never runs is the highest-leverage dead code
   in the repository** — it removes protection silently, and its presence actively discourages
   anyone from looking again.

   This is not hypothetical. Found 2026-09-13: `tools/validate_working_log.py` contains a
   "Duplicate ticket IDs" check, with its own passing tests, whose **only caller is its own test
   file** — no CI job, no Makefile target, no gate-check registration. It has never run against the
   repository. Worse, it *deliberately excludes* exact-duplicate physical lines as "a known,
   tracked defect class", so even once wired in it would skip the precise rows the real defect
   produces. Meanwhile `tickets/working_log.csv` carries 46 duplicate `(ticket_id, title)` pairs,
   22 of them from 2026-09 alone.

   **`tools/` is audited as a caller, never as a subject** — the precise gap, verified against
   source. `audit_unreachable_code.py` walks `SRC_ROOTS = [Path("src")]` for *definitions*, while
   `TEST_TOOL_ROOTS = [Path("tests"), Path("tools")]` is scanned only for *occurrences*, to
   classify an identifier's usage as test-or-tool rather than production. So a zero-caller function
   under `tools/` is invisible by construction, and `tools/` is simultaneously one of the inputs
   deciding whether a `src/` identifier counts as used. The directory that cannot be audited helps
   determine what counts as reachable elsewhere.

   `validate_working_log.py`'s duplicate check sits exactly in that blind spot: defined in
   `tools/`, called by nothing but its own test, and structurally unreachable by the tool built to
   find precisely that.

   The fix direction is adding `tools/` as a scan root while keeping the existing test-only-usage
   split. **The caveat that makes it non-trivial:** `tools/` is full of *legitimate* zero-caller
   code — argparse CLIs run by humans, Makefile targets, workflow scripts invoked from `.claude/`.
   A naive scan flags all of them. Excluding the `main()`-under-`if __name__` pattern and resolving
   Makefile/workflow references would be required, or it is another unlandable gate — the same
   failure mode as the 46-pair content check below.

**A landing constraint that applies to any check built on these findings.** A content check
asserting "no duplicate rows" fires on 46 existing pairs immediately and is therefore unlandable as
a blocking gate — it would be disabled or deleted rather than satisfied. It needs a baseline or a
ratchet, exactly like `tests/tools/test_parity_index_baseline.py` (§4) and for the same reason. Any
detector introduced into a corpus that is already dirty must ratchet from the current state, or it
teaches people to bypass it on day one.

---

## 6 · Why now

This arc has found roughly a dozen mechanisms that were built, tested, documented and inert. Every
one was found by a person choosing to look at the right thing — instrumenting a run by hand,
grepping for callers, reading a pipeline registration closely. That method works and does not
scale, and it has a worse property than not scaling: **it produced confident wrong answers** (D09's
`tick-live` classifications above) that then sat in an authoritative document for three months.

The balance-tuning pass in `docs/plans/deferred_tuning_decisions_register.md` is the concrete
forcing function. Tuning numbers on mechanisms that never execute is waste, and the register's own
⚠️ entries (D-05 lairs/world bosses, D-06 faction war) are exactly the cases where "the number is
large" and "the feature never runs" are indistinguishable without this measurement.

---

## 7 · Proposed Design (2026-09-15 — resolves the Open Decisions in §5)

This section answers peer review's brief: what's instrumented, how the corpus runs, what the
output looks like, and what it cannot see — stated as plainly as what it can. **This is a plan,
not an implementation; nothing below has been built.** Several items below are worked examples
from this week's own combat-engagement investigation, landing after this doc was first drafted.

### 7.1 What's instrumented

**`src/` and `tools/`, both, full scope — not narrowed to Mechanics-Bible-declared features for
v1.** This directly resolves Open Decision #5: `tools/audit_unreachable_code.py` defines
`SRC_ROOTS = [Path("src")]` and scans `TEST_TOOL_ROOTS = [Path("tests"), Path("tools")]` only for
*occurrences* (confirmed by direct read, `tools/audit_unreachable_code.py:86-87`) — so a
zero-caller function under `tools/` is invisible to it by construction, and `tools/` simultaneously
helps decide whether a `src/` identifier counts as used elsewhere. The census must not repeat this
asymmetry: `tools/` is instrumented as a subject with its own branch-coverage report, not only
scanned for callers into `src/`. **A verification mechanism that never runs is the highest-leverage
dead code in the repository** — the census exists to find exactly that class, and excluding its own
neighborhood would be the same blind spot one layer up.

Full-scope (not feature-scoped) is the pragmatic v1 choice per Open Decision #4's own framing —
"simpler and catches things nobody thought to list" — and can narrow later once a first real run's
false-positive rate is known. Narrowing to Mechanics-Bible-declared features first would import an
assumption about what matters before the tool has produced any evidence about where noise lives.

**Branch coverage, not line coverage — non-negotiable, not a v2 refinement.** This week's own
combat-engagement work is a clean worked example of exactly the failure mode §2 already names: the
posture gate this arc built and shipped this week (`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-
WIRED-TO-EXECUTION`) lived, in its first version, inside `tactical.py`'s decision function — every
line of that function executed on every tick, so line coverage would have reported it fully live.
Only branch-level instrumentation (in that case, manual, not this tool) revealed that 93.7% of real
attacks never took the branch that would have re-invoked the gated decision at all. The
`check_for_boss_spawn()`/`GuildAction.visit()` examples already in §1-2 make the same point from a
different subsystem; this week adds a third, independently found.

### 7.2 How the corpus runs

Ride on `config/simulation_quality/corpus_registry.yaml` exactly as §2 already specifies — no
second definition of "a representative set of runs." For each registered world/seed/tier, run the
simulation under `coverage.py` with `branch=True`, producing one coverage-data file per run,
combined via `coverage combine` into a single corpus-wide branch-coverage report. Diff that report
against the unit-test suite's own branch-coverage report (`pytest --cov=src --cov=tools
--cov-branch`) to produce the target set difference: *branch covered by the unit suite, never taken
anywhere in the corpus.*

**A determinism pre-check gates trust in the census, not the census's own execution.** Per §4, this
initiative depends on `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2`'s deferred
kernel wall-clock throttle non-determinism. Before the census's first real run is reported as
fact, run one corpus world/seed twice under identical conditions and diff the two branch-hit sets.
If they differ, the census's own output must say so explicitly (`STABILITY: UNSTABLE — see
TCK-20260822-...`) rather than silently presenting a possibly-flaky diff as a finding — a census
that varies run to run cannot distinguish a dead mechanism from a flaky one, and hiding that
distinction would recreate exactly the "instrument trusted beyond what it measures" failure this
whole initiative exists to avoid.

**Where it runs**: attached to the existing SimQ corpus execution as an instrumentation wrapper,
not a second job with its own world definitions (resolves Open Decision #2's first sub-question).

**Frequency: on-demand only, decided (not a recommendation).** No schedule, no cadence, no
periodic job. Reasoning, recorded here so it reads as deliberate rather than unfinished: this is a
diagnostic tool, not a monitor — the instrumented corpus run is expensive, and there is no evidence
yet for how often its findings actually change between runs. A weekly (or any fixed-cadence) run
producing an identical report to the last one is cost without information. A cadence gets added
once someone can point to a real interval the results justify — e.g. "findings drift meaningfully
every N epics" — not assumed up front because periodic sounds more thorough than on-demand.

### 7.3 What the output looks like

A **report artifact** (JSON for tooling, a rendered markdown/table for humans), never a pass/fail
exit code in v1 — resolves Open Decision #3 in favor of report-only, per §4's own argument and
peer review's fourth point: a gate firing on legitimately-rare code teaches people to bypass it,
and this week gave a fresh instance of that exact dynamic (a decision-point combat gate that
measured zero effect was nearly reported as "the policy doesn't work," when the real fault was
gate placement — the same shape as a false-positive detector teaching people the tool is wrong
rather than that it found something real).

**Gating: never, until a specific, stated condition is met — not an open-ended deferral.** Report-
only is not "for now" left implicit; it becomes gate-eligible only once a real run shows (a) the
suppression list has stabilized (stopped growing run-over-run for reasons other than new real
code) and (b) the false-positive rate is actually known, not guessed. Until both are true, this
tool does not fail a build or block a merge under any configuration. Writing the condition down
here, not just the deferral, is deliberate — "report-only for now" with no exit criterion quietly
becomes someone's unstated TODO to promote it before the evidence exists.

- **Reachability and effectiveness are two separate axes, not one taxonomy with a sixth value**
  (resolves Open Decision #1 — and revises this plan's own earlier draft, which had proposed
  folding a sixth status into D09's list). D09's five reachability statuses answer *is this
  called?* (`never-called`, `test-only`, `tick-live`, `tick-live (cond)`, and its top status for
  code that's both called and doing something) — keep them as-is, unmodified. Add a second,
  orthogonal **effectiveness** axis reported against every reachability status:
  `effective` / `inert` / `not-applicable` (the last for statuses like `never-called` where
  effectiveness doesn't mean anything). **This is not a naming preference — collapsing the two
  axes is exactly the mechanism that made D09 wrong.** D09 measured reachability, reported
  `tick-live`, and stopped there; `check_for_boss_spawn()` and `PaidInformationTransactionSystem`
  were both genuinely `tick-live` by D09's own correct definition, and both conclusions were false
  anyway, because `tick-live` was silently read as "and therefore doing something." A census that
  reports `tick-live / inert` for `check_for_boss_spawn()` and `tick-live / effective` for a real
  working mechanism makes the two facts equally visible instead of one implying the other. This
  week's own combat-engagement gate is the same shape at execution-router scale: `tick-live` (the
  phase ran every tick) and `inert` (700 real attacks a tick, zero of them gated) were both true
  and needed to be seen as two separate facts, not folded into one status value.
- **Enumerates every unreached branch under a mechanism, not the first found** — a hard requirement,
  not a nice-to-have. `GuildAction.visit()`'s own two independent blockers (a feature flag
  defaulting OFF, and a `"iron"` vs `"iron_vein"` string mismatch) is the concrete case: reporting
  only the first would let someone fix the flag, observe no change, and wrongly conclude the flag
  wasn't the problem. Findings are grouped by mechanism so a multi-blocker case is visibly one
  mechanism with N unreached branches, not N unrelated rows.
- **A suppression list with a mandatory stated reason per entry** (`{reason, added_by: ticket_id,
  date}`), never a blanket ignore — per §4's false-positive concern. Seeded by a first-pass human
  triage of the first real run before the report is trusted for anything beyond its own review.
- **A ratchet baseline, never an assert-zero** (resolves the "landing constraint" in §5, now backed
  by three concrete instances rather than one): the first real run's finding count becomes the
  accepted baseline; only new findings beyond it are flagged going forward. The precedent is not
  hypothetical — three separate detectors in this repository already hit exactly this wall: (1)
  `tests/tools/test_parity_index_baseline.py`'s equality assertion on a known-bad entry count,
  where correcting the ledger costs a hotfix ticket and leaving it wrong costs nothing; (2)
  `validate_working_log.py`'s own duplicate-ticket-ID check, which deliberately excludes exact-
  duplicate physical lines as "a known, tracked defect class" rather than requiring zero; (3) the
  `tools/`-as-caller-only scan-root gap itself in §7.1 above, which if fixed naively would flag
  every legitimate zero-caller CLI/Makefile-target function in `tools/` on day one. A detector
  landing in an already-dirty corpus without a ratchet gets disabled or deleted, not fixed.
- **The report's own header states the tool's limitation, unsuppressably, every run** — per peer
  review's explicit instruction that this belongs in the tool's own output, not only this document.
  Fixed preamble text on every generated report, roughly: *"This census finds code that never
  executes, or never takes a branch, across the SimQ corpus. It cannot detect a live mechanism
  producing a wrong outcome — a branch reported as taken here may still be behaving incorrectly.
  See SimQ pillar scores for outcome quality."* This is not decorative: §3's own table shows a
  defect (235 unanswered recruitment offers) that this tool would report as **fully healthy** —
  every line ran, every branch was taken, the code did exactly what it says. A report that doesn't
  say this out loud, every time, invites exactly the over-trust this initiative exists to prevent.

### 7.4 What it cannot see (stated as plainly as what it can)

1. **A live mechanism producing a bad outcome.** Full coverage, every branch taken, wrong result —
   the 235-recruitment-offers case in §3. This is SimQ's job, not this tool's; the two are
   complementary, not overlapping, and neither substitutes for the other.
2. **Genuinely rare-but-correct branches** (error handlers, defensive checks, low-probability
   calamity paths) will look identical to dead code on a finite corpus without a stated-reason
   suppression entry — false positives are expected on the first run, not a sign the tool is
   broken.
3. **A flaky/non-deterministic branch**, unless the §7.2 determinism pre-check confirms stability.
   An unstable census must say so in its own report rather than presenting a possibly-flaky result
   as settled fact.
4. **Control flow outside instrumented Python processes** — Makefile targets, `.claude/` workflow
   scripts, shell orchestration. Only branch coverage inside the corpus run and the unit-test run
   is measured; a mechanism invoked only from one of those surfaces is out of scope for this tool.

### 7.5 Decided (2026-09-15, peer review)

Per §5's own instruction, "none of these should be resolved unilaterally" — the following were
reviewed and confirmed, not asserted unilaterally by this plan:

- **Run frequency: on-demand only** (§7.2). No schedule. Revisit only once a real interval the
  results justify can be named, not before.
- **Gating: never, until both (a) the suppression list has stabilized and (b) the false-positive
  rate is known from a real run** (§7.3). Report-only is not an implicit "for now" — it is the
  state until that named condition is met, with no other exit path.
- **Taxonomy: two orthogonal axes, not a sixth status** (§7.3). D09's five reachability statuses
  are reused unmodified; effectiveness (`effective` / `inert` / `not-applicable`) is reported
  separately against each. This was a substantive correction to this plan's own first draft, not
  a naming choice — folding effectiveness into a single reachability value is the exact ambiguity
  that made D09's `tick-live` classification of `check_for_boss_spawn()` and
  `PaidInformationTransactionSystem` read as "and therefore working" when neither was.

### 7.6 Still open

Whether D09's five reachability *names* themselves need any wording change (independent of the new
effectiveness axis above), and the exact mechanics of the suppression-list stabilization check in
§7.3's gating condition, remain open for whoever scopes the implementation ticket.

---

## 8 · Related

- `docs/audits/D09_system_wiring.md` — asks this question manually; its taxonomy is reusable, its
  answers are stale and, in at least two cases, wrong.
- `docs/audits/D11_dead_code.md` — the 100%-false-positive precedent; read the Post-Audit
  Correction before designing detection.
- `tools/audit_unreachable_code.py` — static caller analysis, correctly excludes test-only usage.
  Complementary: it finds zero-caller code, this finds zero-effect code.
- `docs/simulation_quality/quality_scoring_contract.md` — SimQ's own scope; the boundary in §3.
- `docs/plans/agent_infrastructure/reachability_verification_findings.md` — why test coverage is
  not evidence a feature runs.
- `docs/plans/deferred_tuning_decisions_register.md` — §6's forcing function; D-05/D-06 in
  particular.
- `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION` — worked example for §7.1's
  branch-vs-line distinction, found independently of this document (a decision-point gate with
  full line coverage that measured zero effect because the wrong branch shape was never taken).
- `TCK-20260915-SIMQ-CORPUS-BLIND-TO-SCALE-DEPENDENT-BEHAVIOR` — the same underlying problem from
  the other side: SimQ measuring outcome quality on a corpus too small to exercise a real
  population-scale change, exactly mirroring §3's "necessary and not sufficient" boundary.
- `docs/engine/kernel.md`'s "Sticky-Task Law" section — a structural engine property (a gate at a
  decision point is bypassed by tasks the scheduler re-executes without re-deciding) that makes the
  branch-vs-line distinction in §7.1 concrete rather than hypothetical.
