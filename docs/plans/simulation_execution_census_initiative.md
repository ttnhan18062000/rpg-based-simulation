---
status: active
layer: simulation
authority: P1
audience: agent
tags: [simulation-quality, audit, architecture]
---

# Plan — Simulation Execution Census

**Status, scoped 2026-09-13.** Proposes an automated measurement of *which simulation code actually
has an effect in a real run*, to replace the manual auditing that has been finding these defects
one at a time. Scoped as an initiative, not a ticket. Nothing here is implemented.

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

## 7 · Related

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
