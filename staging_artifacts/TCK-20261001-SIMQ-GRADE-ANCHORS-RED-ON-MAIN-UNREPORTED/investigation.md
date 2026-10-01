---
status: active
layer: testing
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED
phase: open
date: 2026-10-01
tags: [simulation-quality, grade-thresholds]
---

# Investigation — TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED

Scope item 1 (the count) was already complete in the ticket body: **13 of 15 grade anchors red** on
`origin/main` @ `e9db40f0a`. This investigation addresses the remaining three: **age of redness**, the
per-anchor **(a)/(b)/(c) classification**, and what those imply for the **reporting path**.

**Method note: zero new simulation runs were needed for what follows.** The anchor file already carries
an extensive, evidence-backed, per-anchor history in its module docstring and in each test's own
docstring. Reading it first was cheaper than re-measuring and — as recorded below — it overturned the
conclusion I was about to reach from the counts alone.

## A correction I have to record, because it is the ticket's own named risk

Working from the red list plus the module docstring's enumeration of the 2026-08-29 failures, I inferred
that **five** anchors were *newly* red (absent from every previously-documented failure list, in a file
unmodified since 2026-08-31, therefore genuine September simulation drift — class (b)).

**That inference was wrong.** Each of the five carries its own documented history:

- `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` measured them under idle-vs-load and found the
  drifted pillars **genuinely variable**, in the anchors' own words: "COMBAT event_count 8 (both idle) vs
  10-13 (load); PROGRESSION 5 (idle, grade A) vs 6-7 (load, grade B); NARRATIVE ranged 32-53. All three
  drifted pillars are genuinely variable"; "NARRATIVE event_count ranged 23-40 … monotonic-with-load
  pattern, genuinely variable"; "SOCIAL event_count ranged 710-770 across trials".
- `TCK-20260817-STANDARD-SIMQ-COGNITION-BIT-IDENTICAL-GUARD-TOLERANCE-CONVERSION` then converted them
  from bit-identical guards into **3-fresh-trial tolerance assertions** precisely *because* of that
  variability (tolerance = 1.3× the largest single-sample deviation seen in the repro).

So these anchors were never bit-identical guards that regressed; they are long-known load-sensitive
anchors. The ticket warns in its own Assumptions: "**Do not assume stale anchors** — that is the
comfortable conclusion". The symmetric trap is assuming *regression*, and the raw counts walk you into
it. For a class-(c) anchor, "green on 2026-08-29, red on 2026-10-01" is **not evidence of anything** — it
is the expected behaviour of a non-deterministic assertion.

**This also means "how long have they been red" is not a well-formed question for most of this family**,
and that is itself an answer to the acceptance criterion rather than a failure to meet it. A flaky anchor
does not have an onset date. The criterion is satisfiable only for the anchors that are *not* class (c).

## Per-anchor classification (13 grade + 2 population)

Classes per the ticket: **(a)** anchor value stale, behaviour correct; **(b)** genuine regression, anchor
right; **(c)** non-deterministic / flaky by construction, never protected anything.

| # | Anchor | Class | Evidence |
|---|---|---|---|
| 1 | `urban_political_seed123_500t_cognition` | **(c)** | Re-anchored by `TCK-20260817` tolerance conversion; `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` lineage; its docstring records 10 fresh same-seed trials proving a prior stability assumption "empirically false" |
| 2 | `simq_routing_test_seed42_500t_cognition` | **(c)** | Docstring §5: "did not reproduce as failures at all in a clean re-run"; own docstring records a 17/18-trial majority value — i.e. a known 1-in-18 minority outcome |
| 3 | `unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative` | **out of scope** | Owned by `TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE` |
| 4 | `urban_political_seed42_1000t_social` | **(c), escalated** | Re-baselined against fresh evidence by `TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE`; **red again ~1 month later** |
| 5 | `urban_political_seed123_1000t_social_economy` | **(c) / infra** | Docstring §5 resource-budget group → `CalibrationIntegrityError` (observability queue overflow / SURVIVAL mode-shed); §6 says it was *not* fixed by `TCK-20260829` and "remain their own separate, already-tracked concern" |
| 6 | `urban_political_selfmodel_probe_seed42_200t_social_world` | **(c) / infra** | Same `CalibrationIntegrityError` class |
| 7 | `generated_frontier_3_42_seed123_200t_combat_narrative` | **(c)** | `TCK-20260715` sweep: "All three drifted pillars are genuinely variable"; `TCK-20260817` tolerance conversion |
| 8 | `urban_political_seed42_200t_social` | **(c)** | `TCK-20260715`: SOCIAL 710-770 across trials; "the original sustained-session drift is reproducible even in this smaller repro shape" |
| 9 | `frontier_extended_seed42_200t_narrative` | **(c), escalated** | Re-centered with fresh 3-trial evidence 2026-08-29 (docstring §5); **red again ~1 month later** |
| 10 | `frontier_extended_seed123_200t_combat_progression_narrative` | **(c)** | `TCK-20260715`: all three drifted pillars genuinely variable |
| 11 | `frontier_living_world_seed42_200t_social` | **(c), escalated** | Re-centered with fresh 3-trial evidence 2026-08-29 (docstring §5); **red again ~1 month later** |
| 12 | `frontier_living_world_seed123_200t_combat_narrative` | **(c)** | `TCK-20260715`: "monotonic-with-load pattern, genuinely variable" |
| 13 | `frontier_marches_seed42_200t_narrative` | **UNKNOWN — recorded reason is stale** | Docstring: crashes `TypeError: can only concatenate tuple (not "list") to tuple` at `lifecycle.py:122`. **That bug is fixed** — the concat now reads `list(entity.inventory.items) + heirloom_stacks` at `lifecycle.py:252`. Still red, so it is red for a *new, undiagnosed* reason |
| P1 | `test_population_stability[frontier_marches]` | **out of scope** | Ticket's Out of Scope: confirmed noise via 5-vs-5 trials |
| P2 | `generated_frontier_3_42_extended_population_stability` | **UNKNOWN — recorded reason is stale** | Same fixed `TypeError` as #13 |

**Tally: 10 of 13 grade anchors are class (c)** (6 documented load-sensitive + 3 re-baselined-and-red-again
+ 1 `simq_routing` minority-outcome), **2 need fresh diagnosis** (#13, P2), **1 is out of scope**. **Zero
anchors are currently supported as class (a) or class (b).** No anchor value was touched.

## The finding that should drive the decision

**Both available repairs have already been tried on this family, and neither held.**

1. **Tolerance widening** — `TCK-20260817` converted bit-identical guards to 3-trial tolerance bands
   derived from observed deviation. Anchors #1, #7, #8, #10, #12 are red *through* those bands.
2. **Re-anchoring against fresh evidence** — `TCK-20260828` (2026-08-29) re-centered #9 and #11 on fresh
   3-trial evidence; `TCK-20260830` re-baselined #4. All three are red again within about a month.

That is two distinct, competent, evidence-backed repair strategies failing on overlapping sets. The
common cause is recorded in the file's own docstring: `Kernel`'s wall-clock mid-tick throttle breaks
strict determinism under variable system load with `audit_mode=False` — described there as
"already-known, already-deferred … tracked separately, not a new issue". Related records:
`docs/audits/D06_longrun_health.md` F6 and `docs/plans/audit_fix_plan.md` P2-P (the latter marked
**RESOLVED (verified 2026-07-11)**, which sits oddly against the docstring still treating it as live on
2026-08-29 — flagged as a discrepancy, not resolved here).

**I am not re-raising the determinism root cause.** It is parked by user decision, and this ticket does
not need it reopened. The point is narrower and decision-relevant: **while it stands, "repair the
anchors" is not an available outcome for ~10 of 13**, because the thing they assert against is not
stable. Re-baselining them again would be the third attempt at a strategy that has already failed twice,
and would additionally destroy the record the ticket's Out of Scope exists to protect.

**Therefore the reporting path is not merely the cheapest of the ticket's deliverables — it is the only
one currently achievable**, and the ticket's own framing supports this: "visibility (not gating) is the
minimum bar", because "an unread assertion and an absent assertion are the same thing operationally".

## Fresh diagnosis of #13 and P2 — RUN, 2026-10-01

Conditions: `HEAD = 71c4aa321`, `src/` and `tests/` verified clean (asserted by the runner before
starting, so the result is attributable). `--resource-budget large` to prevent the known 60s SIGALRM cap
from masquerading as the answer. Wall clock 3m17s. **Result: 1 failed, 1 passed.**

### P2 `test_generated_frontier_3_42_extended_population_stability` — **PASSES**

It was red in the ticket's own 2026-10-01 measurement and is green here. **This is not yet proof of
flakiness, and must not be recorded as such:** that measurement ran under the default
`--resource-budget medium`, this run under `large`. The resource budget is a live confound — the module
docstring records five anchors in this very family hitting the `medium` 60s SIGALRM cap, and reaching a
different failure mode (`CalibrationIntegrityError`) once the cap was lifted. **Open question:** re-run
P2 under `medium` to separate "flaky" from "budget-limited". Until then its class is **(c)-or-infra,
undetermined**, which is still a strict improvement on the stale `TypeError` reason.

### #13 `test_frontier_marches_seed42_200t_narrative_grade_stability` — **FAILS, and it is class (a)**

Not a crash. The recorded `TypeError` reason is confirmed dead. The real assertion:

```
NARRATIVE: mean_score=0.2665 across 3 trials outside tolerance of anchor_score=0.0 (abs_floor=0.05)
           per-trial values: [0.41818181818181815, 0.22916666666666666, 0.15204678362573099]
```
(`test_corpus_diversity.py:2071`)

**The anchor expects a NARRATIVE score of `0.0`.** It was set when this world produced *no* narrative at
all. The simulation now produces narrative on every trial. So the anchor's expected value is **stale and
the current behaviour is better** — this is the family's **first evidence-backed class (a)**, and the
drift direction is *improvement*, not regression. It is precisely the case the ticket's "do not assume
stale anchors" warning exists to protect against assuming — and here the evidence actually supports it.

A secondary class-(c) component is visible in the same output: per-trial values span 0.152→0.418, a
~2.75× spread, so even a correctly re-centred anchor needs a tolerance wide enough to cover it.

**Recommended routing:** this anchor warrants **its own re-baseline ticket**, exactly as the ticket's Out
of Scope prescribes ("Re-baselining a specific anchor against evidence is legitimate and is handled per
`docs/testing/regression_policy.md` §9-11 in its own ticket") and exactly as
`TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE` was handled. **Do not re-baseline it
inside this ticket** — that is the blanket-adjustment this ticket forbids, and the 3 trials here are
below the evidence bar §9-11 sets.

### What this changes in the classification

The tally above becomes: **10 of 13 class (c)**, **1 class (a) with evidence** (#13), **1
(c)-or-infra undetermined** (P2), **1 out of scope** (#3). Still **zero** anchors supported as class (b)
— no evidence of genuine simulation regression anywhere in this family. The headline conclusion is
unchanged and now better supported: the anchors are not watching a regression, they are failing to be a
stable instrument.

### P2 settled, 2026-10-01: **budget-limited, fully deterministic — not flaky**

Positive control run, 3 trials under the **default `medium`** budget (the condition the ticket's own
measurement used), same clean tree at `71c4aa321`:

- **3 of 3 failed, each at ~61s** (61.12s / 60.86s / 60.63s) — the known **60s SIGALRM
  `--resource-budget medium` cap**, not an assertion failure.
- Under `--resource-budget large` it **passes** (previous section).

So P2 is **deterministic under each condition** and the variable is the resource budget, not chance. It
is not class (c), not class (a), and not a regression. Its tick profile shows `persistence: 120.6ms`
dominating a 139ms tick that trips the watchdog, consistent with the docstring's recorded
`CalibrationIntegrityError` (observability queue overflow / SURVIVAL mode-shed) family rather than
anything about population balance.

**Consequence: the ticket's own measurement produced a false red for P2**, because it ran under `medium`
while CI runs this family under `large`. P2 should be removed from the red list for CI purposes.

---

# THE TICKET'S CENTRAL PREMISE IS WRONG — the reporting lane already exists and already works

This supersedes the ticket's framing that "`CI` does not gate on `@slow`. So these anchors can be red on
`main` indefinitely with no signal to anyone" and "their failure is only observable to someone who runs
them deliberately". **Verified at `71c4aa321`:**

- `.github/workflows/test.yml:7-11` already has a **nightly schedule**, `cron: "0 3 * * *"`.
- The **`slow` job** (`:806-845`) runs `if: github.ref == 'refs/heads/main' || github.event_name ==
  'schedule' || github.event_name == 'workflow_dispatch'` — added by
  `TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH` precisely so the slow suite remains "a real safety
  net" off the PR path.
- Its **first step is dedicated to this exact family**: `make simq-corpus-diversity-slow-isolated`
  (`:833`), from `TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE`. The `Makefile:539-551` target
  runs **each anchor as an isolated per-test subprocess** with `--resource-budget large`, **guards
  against silent collection drift** (`if nodeid_count -lt 32 ... exit 1`, explicitly "not silently
  passing"), and **propagates failure** (`|| status=1` … `exit $$status`). The workflow step has no
  `continue-on-error`.

**So a red anchor does fail a scheduled CI job, every night, isolated, at the right budget.** The
mechanism the ticket asks to be built is already built — and built more carefully than the ticket
assumes.

## Age of redness — answered with hard evidence

`gh run list --workflow=test.yml --event=schedule --limit 25`: **zero successful scheduled runs** between
2026-09-06 and 2026-09-30 (18 `failure`, 7 `cancelled`). Per-run job/step attribution confirms the
corpus-diversity step specifically:

| Night | Failing job → step |
|---|---|
| 2026-09-07, 09-08, 09-09, 09-15, 09-16, 09-21, 09-29 | **Slow regression → "Slow tests — corpus diversity (isolated per-test)"**, and it is the *only* failing job those nights |
| 2026-09-10, 09-14 | `Unit · infra / observability → Run` (different job) |
| 2026-09-13, 09-06 | `API / tools / logging → Run` (different job) |

**The anchors have been failing the nightly lane at least since 2026-09-07 — about 3.5 weeks.** That
satisfies the "at least to the nearest few weeks" acceptance criterion with CI evidence rather than
inference, and it is independent of the class-(c) "a flaky anchor has no onset date" caveat above,
because it dates *when the lane started reporting red*, not when any individual anchor drifted.

**Important non-inference:** on the nights a different job failed, the `slow` job **never ran at all** —
it `needs:` eleven upstream jobs. Those nights are **not** evidence the anchors were green. Absence from
the sample is not evidence of absence.

## What the real gap is, and what it means for the chosen deliverable

Not "nothing reports it". **Twenty-five consecutive scheduled runs reported it and nobody acted.** The
ticket's own argument turns out to be more precisely right than its diagnosis: "an unread assertion and
an absent assertion are the same thing operationally" — the assertion here is not absent, it is
**unread**.

This changes the deliverable. Building a scheduled non-gating lane would **duplicate existing
infrastructure**. The achievable work is making the existing lane's result *reach someone*:

1. **Notification/readership**, not execution — route the nightly `slow` job's failure somewhere a human
   or the agent retro cadence actually reads, rather than relying on anyone opening GitHub Actions.
2. The AC "a test or check proving the mechanism reports a seeded failure" is **still worth doing** and
   is cheap: the `Makefile` target's status propagation and its `-lt 32` collection guard are the two
   things that must not silently rot, and neither is currently covered by a test.
3. **Remove P2 from the red list** (false red under `medium`; green in CI under `large`).

**Recommendation: do not build a new lane.** Re-scope this ticket to notification + a guard test, and
record that the execution half was already solved by `TCK-20260818` and `TCK-20260715`. Filing a
duplicate lane would be the "patch around it" failure mode, and it would also bury the real finding:
this project's slow-lane reporting works, and has been ignored for three and a half weeks.

## What remains genuinely open

1. **The notification/readership design** (above) — now the ticket's substantive deliverable, and it
   needs a user decision since the originally-chosen option is already implemented.
2. **File the #13 re-baseline ticket** per `regression_policy.md` §9-11 with enough trials to meet the
   evidence bar. **Done:** `TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE`.
3. **The other-`@slow`-families audit** — still untouched, and now sharper: the question is not whether
   other families are unrun, but whether any are excluded from the `slow` job's own steps.
4. Narrowing the onset before 2026-09-07 (the 25-run window's edge) if a more precise date is wanted.
2. **Reporting-path design** — a non-gating scheduled lane, a periodic report, or promoting a
   deterministic subset out of `@slow`. Design call, not pre-decided. Note the AC requires a **test
   proving the mechanism reports a seeded failure**, which is the part that makes it real.
3. **The other-`@slow`-families audit** — untouched.
4. **The `QueueDrainWorker` teardown leak** — the docstring already root-causes it (a mid-`_run_engine()`
   `TimeoutError`/`CalibrationIntegrityError` skips `kernel.shutdown()`, leaking that run's worker
   thread; a later unrelated test's teardown sentinel then reports it against itself) and concludes it
   "does not need its own ticket beyond" the backpressure ticket. **Recommend not filing a ticket for
   it** — the ticket body floats that it "may deserve" one; the recorded root cause says otherwise, and
   per the check-recorded-decisions discipline that existing analysis should stand unless re-measured.

## Honest statement of limits

- Single run per anchor in the ticket's own measurement; **flakiness was not re-tested by me either**.
  For class-(c) anchors that is not a gap in the conclusion — their variability is what the cited sweeps
  already measured — but it does mean I have not independently reproduced any individual failure.
- My classification is **documentary**: it rests on the anchors' own recorded evidence plus the current
  red list, not on fresh trials. That is the right first pass (it cost no runs and corrected my own
  wrong inference), but any anchor whose value eventually changes must still follow
  `docs/testing/regression_policy.md` §9-11 with its own fresh evidence.
- The `audit_fix_plan.md` P2-P "RESOLVED" vs docstring "deferred" discrepancy is unresolved and I have
  not determined which is current.
