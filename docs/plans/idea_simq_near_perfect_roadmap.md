---
status: active
layer: simulation
authority: P2
audience: developer
maturity: idea
date: 2026-07-10
tags: [idea, simulation-quality, calibration, corpus, determinism, roadmap]
---

# Idea: SimQ Near-Perfect Roadmap — Closing the Gap Between "Shipped" and "Done"

> **Maturity: IDEA** — Not scheduled. This is a synthesis document, not a ticket. It exists so the
> next SimQ investigation starts from a ranked, evidence-based list of open threads instead of
> re-discovering them one bug report at a time. Five of its six threads already have a concrete
> landing spot in `docs/plans/audit_fix_plan.md` (P2-O, P2-P, P2-Q) or `docs/audits/D06_longrun_health.md`
> (F6) — this doc's job is the cross-cutting synthesis those per-item entries don't carry: why these
> particular five threads, in this particular order, constitute the actual distance between "SimQ
> ships and works" and "SimQ is what its own contract says it should be."
>
> **Superseded as the actionable plan by `docs/plans/simq_development_roadmap.md`** (2026-07-10),
> which sequences these five threads into 6 phases with ticket-count estimates and is where actual
> tickets get filed from. This doc remains the evidence trail for *why* — read it first if you need
> the reasoning behind the roadmap's phase ordering; read the roadmap doc for *what to do next*.

---

## Why This Doc Exists

SimQ has been worked in reactive batches since 2026-06-28: the MVP epic (7 tickets), three "uplift"
batches, a Corpus Tiers epic (10 tickets), a Deep Coverage epic (10 tickets), and — most recently — two
population-collapse bug fixes found as a byproduct of that epic's own long-run anchoring work
(`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`, `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`).
Every one of those batches was individually well-scoped and well-verified. But each was also
triggered by whatever the previous batch happened to surface — nobody has recently stepped back and
asked "against the module's own definition of done, what's actually still missing, and does it matter."

This doc is that step-back. It does not propose new SimQ capability. It inventories the gap between
`docs/simulation_quality/quality_scoring_contract.md`'s own stated bar and the corpus/tooling/process
as they exist today, ranks what's found by leverage (not by how recently it was noticed), and gives
each thread a concrete next action. Where a thread already has a backlog entry, this doc points at it
rather than duplicating it — the value here is the ranking and the "why these five, why this order,"
not re-authoring content that already exists.

---

## The Bar: What "Near-Perfect" Actually Means

Per `quality_scoring_contract.md` §1, SimQ has exactly three goals, no more:

1. **Automated quality visibility** — a developer can run any scenario and immediately see which
   subsystems are healthy and which are degenerate, without manually auditing events.
2. **Regression detection** — grade thresholds catch when a code change silently kills a subsystem.
3. **Balance and tuning support** — concrete per-pillar signal replaces manual observation.

§14 ("Non-Goals for MVP") is explicit that per-entity quality profiles, historical run comparison,
real-time push alerts, ML-based anomaly detection, and automated config suggestion are **out of scope
by design**, not aspirational future work being tracked as debt. "Near-perfect" for this feature does
not mean "build everything §14 excluded" — it means: **the three goals above hold reliably, for every
world in the corpus, and the module's own Acceptance Criteria (§12) are demonstrably true, not just
assumed true because nothing has broken loudly.**

That last clause is where most of this doc's five threads live. Nothing below proposes new pillars,
new scorers, or new infrastructure. Every thread is either (a) verifying a claim the contract already
makes but nobody has re-confirmed, or (b) closing a process gap that has let the same class of defect
recur more than once.

---

## Current State Snapshot (as of 2026-07-10)

For orientation — none of this is new information, it's the baseline the five threads below are
measured against:

| Dimension | State |
|---|---|
| Pillars implemented | 10/10, all calibrated |
| Pillar completeness audit | Closed 2026-07 (`quality_scoring_contract.md` §7.5) — no 11th pillar justified; one narrow gap (`building_sabotage`) found and closed as a WORLD-pillar rule, not a new pillar |
| Calibration corpus | 71 scenarios / 17 worlds, 0 regressions (`SIMQ-AUDIT-20260710T020542Z`) |
| Tooling | `evaluate_simq.py`, `calibrate_simq.py`, `simq_audit_gaps.py`, and the `simq-audit` agent workflow (mechanizes drift classification → anchor update → doc sync → parity check) all exist and were exercised successfully this session |
| Major batches closed | MVP (E1–E7), SimQ Uplift Batches 1–4, SimQ Corpus Tiers Epic (10 tickets), SimQ Deep Coverage Epic (10 tickets) |
| Open backlog items directly relevant | `docs/plans/audit_fix_plan.md` P2-K (unverified since 2026-07-03), P2-N (open), P2-O/P2-P/P2-Q (new, this doc's threads 4/1/5) |
| New finding this session | `docs/audits/D06_longrun_health.md` F6 — wall-clock-dependent tick-budget throttle causes real (not measurement-noise) population divergence past ~tick 300–320; documented, not fixed (intentional engine behavior) |

---

## The Five Threads, Ranked by Leverage

Ranking principle: a thread ranks higher if it calls into question the trustworthiness of work
**already shipped**, and lower if it's forward-looking scope hygiene. A latent correctness question
about existing anchors outranks a well-scoped but purely additive improvement.

### Thread 1 (highest leverage) — Long-run calibration reliability is unverified (F6 / P2-P) — **RESOLVED 2026-07-11**

**Problem.** `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`'s investigation ran the
same seed, same code, same machine, back-to-back, and got population outcomes that diverged by 100+
ticks in floor-violation onset and more than 2× in the tick-1000 endpoint. Root cause:
`src/engine/kernel.py`'s tick-budget watchdog (`kernel.py:420-442`) and mid-tick emergency throttle
(`kernel.py:574-601`) measure **real wall-clock compute time**, not simulated ticks, and drop
resolution-queue work when a tick's measured time exceeds budget. Which entities get dropped depends
on system load and scheduler timing at the moment the run happened to execute — not the deterministic
seed.

**Why it's #1.** Every 1000t/2000t SimQ anchor ever committed —
`TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` and everything before it — was captured from a single
run. This finding means we do not currently know whether any of those grades are a representative
measurement or a lucky/unlucky throttle-timing draw. That's not a missing feature; it's an open
question about whether data already in `tests/simulation_quality/fixtures/grade_anchors.json` means
what it claims to mean. Nothing else on this list touches the validity of already-shipped work.

**What's already known.** The first `"Tick N exceeded budget"` watchdog warning fires at
tick ~300–320 in every observed run; below that, floor assertions have been reliably reproducible (no
existing evidence of divergence within the 300-tick window `test_population_stability` already
covers). The mechanism itself is documented, intentional engine behavior
(`docs/engine/kernel.md` §"Emergency Throttling") — this is explicitly **not** a proposal to touch
`kernel.py`'s throttle logic. `test_generated_frontier_3_42_extended_population_stability`
(`tests/unit/worldassembly/test_corpus_diversity.py`) already demonstrates one working pattern for
measuring a long-run outcome honestly under this constraint: multiple same-seed trials, throttling
left active, tolerance-based floors instead of a tight per-tick assertion.

**Recommended next action.** A single investigation ticket, scoped narrowly to *verification*, not
*fixing*: for each existing 1000t/2000t anchor in `grade_anchors.json` (`SLOW_ANCHOR_KEYS` in
`tests/simulation_quality/test_grade_regression.py`), re-run 2–3 times at the same seed and check
whether the grade is stable. Two possible outcomes, both actionable and neither requiring an engine
change:
- **Stable across re-runs** → document this in `eval_matrix_results.md` per anchor ("re-verified
  stable across N re-runs, throttle-timing-insensitive for this world/tick-count") and the open
  question is closed with evidence, not assumption.
- **Unstable** → convert that specific anchor to a tolerance-based check (same pattern as the
  `generated_frontier_3_42` guard), or explicitly flag it in the doc as carrying unquantified
  variance until it's converted.

**Effort:** M (re-running N slow-tier scenarios 2–3× each is compute-bound, not design-bound; the
`--slow` tier already exists via `make simq-full-audit-slow`).

**Resolution (`TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`, 2026-07-11):** ran the recommended
action exactly — all 18 `SLOW_ANCHOR_KEYS` re-run 3 times each at the same seed. Outcome: **18/18
stable**, zero required conversion to a tolerance-based guard. Documented per-key in
`docs/simulation_quality/eval_matrix_results.md`. The open question this thread raised is now closed
with evidence.

---

### Thread 2 — The contract's own Acceptance Criteria have never been formally closed out — **RESOLVED 2026-07-11**

**Problem.** `quality_scoring_contract.md` §12 lists five checklists — Functional, Performance,
Scalability, Extensibility, Traceability, Testing — as the module's own definition of done. Every
single checkbox in every list is still literal markdown `[ ]`, unchecked, as authored on
2026-06-28. Nothing in any of the seven MVP tickets, three uplift batches, or two corpus epics closed
this out — because none of them were scoped as "go confirm §12 and check the boxes," they were each
scoped to a specific feature or fix.

**Why this matters.** This is not a cosmetic gap. Some of these criteria are genuinely uncertain
against current state — e.g. "`QUALITY_SCORING_DISABLED=1` produces bit-identical simulation output"
and "scoring exceptions are caught and logged; they do not propagate to simulation" are safety
invariants that, if silently violated by any of the ~40 tickets that have touched this module since
MVP, would be exactly the kind of regression SimQ itself exists to catch — but nothing currently
checks *SimQ's own* acceptance criteria the way SimQ checks the simulation's health.

**Recommended next action.** A single audit pass (not a fix-everything ticket) that goes through §12
line by line, cites current evidence for each item (an existing test, a `grep` result, a direct
invocation), and either checks the box with a citation or files it as a genuine gap. Most items are
almost certainly already true — this is closer to a paperwork pass than new engineering — but "almost
certainly" is exactly the gap between shipped and near-perfect. Suggested split: this pass should be
its own hotfix-tier ticket updating `quality_scoring_contract.md` §12 in place (check boxes + cite
evidence inline), not folded into an unrelated feature ticket.

**Effort:** S–M (mostly verification-and-citation, not implementation; some items may surface a real
small gap worth a follow-up ticket).

**Resolution (`TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT`, 2026-07-11):** ran the recommended action
exactly as a hotfix-tier ticket. 24/25 items verified true and checked with live citations against
current source, including both explicit safety invariants (re-confirmed by direct code read of
`feed.py::build_feed_from_env` and `quality_hub.py::QualityHub.on_envelope`, plus a live passing
test run — not a pointer to the old MVP parity entries). 1 genuine gap surfaced (Traceability item
3, no end-to-end §9 integration test) and filed as a linked follow-up:
`tickets/todos/TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST.md`. A stale parity-ledger
citation (`infrastructure.yaml` INFRA-233) was also found and corrected in the same session.

---

### Thread 3 — Corpus grew wide, not necessarily deep: the 5-pillar C-ceiling — **RESOLVED 2026-07-13**

**Problem.** COGNITION, ECONOMY, FACTION, INFORMATION, and SOCIAL are C by design (feature-flag-gated
off) across nearly the entire 17-world corpus. Only `urban_political` and the purpose-built unit-tier
worlds (`unit_faction_tension`, `unit_information_source`, `unit_selfmodel_pilot`,
`hero_guild_routing`) exercise these pillars richly. Every batch since the Corpus Tiers Epic has grown
the corpus by adding **new** worlds (stress-tier worlds, `generated_frontier_3_42`'s anchors,
long-run anchors for already-rich worlds) rather than **richening** the existing archetype worlds
(`dungeon_crawl`, `frontier_extended`, `wilderness_survival`, etc.) that still sit at the structural
C-ceiling.

**Why this is a question, not a finding.** This may be entirely correct — `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`
and the DA-documentation pattern established for AGENCY explicitly rule that C in a non-flagged
archetype world is *archetype-correct*, not a gap, and the same reasoning plausibly extends to the
other four gated pillars. But that reasoning has been applied pillar-by-pillar and world-by-world as
each investigation happened to touch it; nobody has asked the aggregate question directly: **is a
17-world corpus where 12+ worlds are permanently capped at C on half the pillars actually the
"honest diagnostic across the whole corpus" the Corpus Tiers Epic was scoped to deliver, or did the
epic's own goal quietly narrow from "every world exercises every mechanic" to "at least one world
exercises every mechanic"?**

**Recommended next action.** This is a scope/product question for you, not something to resolve by
further investigation — the technical facts (which pillars are gated, which worlds have flags on) are
already fully documented in `docs/simulation_quality/corpus_tier_taxonomy.md` and
`eval_matrix_results.md`. The actionable choice is: (a) accept the current wide-not-deep shape as
correct and close this thread with a documented rationale (mirroring the AGENCY-DA precedent, one
doc update, cheap), or (b) scope a follow-up epic to activate 1–2 more gated pillars in 2–3 more
archetype worlds, deliberately trading corpus width growth for corpus depth growth for a cycle.

**Effort:** XS to close as a documented decision; L (epic-scale) if (b) is chosen.

**Progress (option (b) chosen, epic underway as `docs/plans/simq_development_roadmap.md` Phases 2-4):**
Phase 2 (SOCIAL, `TCK-20260710-SIMQ-DEPTH-SOCIAL`, done 2026-07-11/12) genuinely deepened the corpus:
`frontier_living_world` and `highland_traverse` both moved SOCIAL C→S via real flag activation on
previously-inert worlds — a clean instance of (b) as originally proposed. Phase 3 (FACTION +
INFORMATION, both done 2026-07-12) took an unexpected but honest turn: both `TCK-20260710-SIMQ-DEPTH-FACTION`
and `TCK-20260710-SIMQ-DEPTH-INFORMATION` independently found, via live re-verification against
current `data/worlds/*/world.yaml` (not this thread's 2026-07-10 snapshot), that the corpus had
already been deepened past this thread's original premise by intervening work
(`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` and siblings) — 11/17 worlds for FACTION, 9/17 for
INFORMATION, with every remaining world carrying a documented, tier-appropriate reason to stay
pillar-inert. Both tickets closed as already-satisfied with zero new content authoring, which is
effectively option (a)'s outcome (accept + document) arrived at empirically rather than decided
up front — the "C-ceiling" this thread worried about had already narrowed to COGNITION alone for
2 of the 4 originally-named gated pillars by the time Phase 3 picked them up.

**Final outcome (2026-07-13, `TCK-20260713-SIMQ-COVERAGE-DECISION-GATE`):** Phase 4 (COGNITION,
`TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE` + follow-up
`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`) closed with a split verdict — materialization
generalizes cleanly and cheaply, query-routing required a full engine-fix ticket to reach zero
live-gameplay worlds (no shipped profile enables it, no production pipeline call site exists for
the intent-execution path). The roadmap's Phase 5 gate ruled on all four pillars using this real
cost data: FACTION/INFORMATION declared complete (structurally saturated), SOCIAL's staged depth
declared the permanent bar (opportunistic-only future expansion), and COGNITION query-routing
world-coverage explicitly not pursued further (its real blocker is a separate, unscoped
pipeline-wiring initiative, not corpus depth). See
`docs/plans/simq_development_roadmap.md`'s Phase 5 section for the full ruling. ECONOMY remains
correctly out of scope — its C-ceiling is a Gini-threshold/archetype-composition question, not a
`FeatureMode` gating question like the other four pillars, and was never part of this roadmap's
Phase 2-4 scope.

---

### Thread 4 — `hazard_kind` completeness has recurred three times as a reactive fix (P2-O) — **RESOLVED 2026-07-11**

**Problem.** The same bug class — a world module declares `hazard_level > 0` on a region but never
declares `hazard_kind`, so `src/worldassembly/resolver.py:798` silently defaults it to `"PHYSICAL"`,
which no faction is ever immune to, causing unconditional lethal drain to the region's own populating
faction — has been found and fixed three separate times: 2026-06-30 (`sandbox_world`), 2026-07-04
(7 modules across 5 worlds, `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`), and 2026-07-09 (4 more modules
across `dungeon_crawl`/`urban_political`/`generated_frontier_3_42`). Each fix was correct and narrow;
each sweep's *coverage* was reactive, limited to whatever modules that specific investigation
happened to touch.

**Why this ranks below Threads 1–2 but above Thread 5.** Unlike Thread 1, this doesn't call the
validity of shipped grades into question — the bug, when present, causes an obvious population
collapse that calibration already catches (that's how all three instances were found). But three
independent recurrences of an identical root cause is a real signal that the *prevention* mechanism
is missing, not just that content authoring has been imperfect three times independently.

**Recommended next action.** Already fully scoped in `docs/plans/audit_fix_plan.md` P2-O: extend
`test_hazard_kind_matches_populating_faction_immunity`
(`tests/unit/worldassembly/test_corpus_diversity.py`) from its current explicit allowlist
(`HAZARD_KIND_MATCH_WORLDS`) to run corpus-wide — for every populated region with `hazard_level > 0`
in every world, assert `hazard_kind` is declared and matches the populating faction's
`hazard_immunities` (or is explicitly documented as intentional exposure, see Thread 5). This converts
three reactive fixes into one permanent guarantee.

**Effort:** S (test-only change, no content or engine change required to close the recurrence risk;
existing test infrastructure already does this exact check per-world, just needs to run
unconditionally).

**Resolution (`TCK-20260710-HAZARD-KIND-CORPUS-WIDE`):** ran the recommended action exactly —
`test_hazard_kind_matches_populating_faction_immunity` now runs unconditionally across all 17
corpus worlds, replacing `HAZARD_KIND_MATCH_WORLDS`. Dry run found **zero mismatches** (45
hazardous-populated-region checks, including all 6 `bandit_road` occurrences) — the recurrence
risk is now permanently closed rather than swept per-investigation. `town_council`/`bandit_road`
(see Thread 5) required no runtime exception: the test's region-level "any populating faction"
matching already passes there since `bandit_company`/`merchant_league` are both immune.

---

### Thread 5 (lowest effort, cheapest close) — The `town_council`/`bandit_road` question keeps getting silently re-deferred (P2-Q) — **RESOLVED 2026-07-11**

**Problem.** In both `urban_political` and `generated_frontier_3_42`, `town_council`'s
`merchant_caravan_frontier_guard` entities are stationed at `bandit_road` (a region correctly exempting
its native `bandit_company` occupants) but `town_council` itself has no `hazard_immunities`, so its
guards take slow continuous drain. Both investigations independently found this, both correctly
declined to fix it unilaterally (per the standing guidance against blanket/wildcard immunities), and
both left it as "may be intentional conflict-pressure flavor" — without ever recording an actual
decision. This is the second time the identical question has surfaced and been silently re-deferred.

**Why it's ranked last, not skipped.** It is genuinely the lowest-leverage item on this list — it
affects 2 entities in 2 worlds and has zero bearing on corpus health or measurement validity. It's
included because it's a symptom worth naming: if a two-line, twice-independently-discovered question
can go unresolved for a week without anyone noticing the recurrence, it's a reasonable bet that
smaller open questions elsewhere in the SimQ investigation trail have had the same fate without ever
surfacing as a pattern. Closing this one is nearly free and removes it as a future distraction from a
third investigation.

**Recommended next action.** Already fully scoped in `docs/plans/audit_fix_plan.md` P2-Q: one DA
ruling, recorded once, applicable to both worlds — either rule it intentional flavor (record in
`docs/guidelines/intentional_divergences.md`) or rule it a gap and add the immunity. Either answer
is fine; what's missing is a recorded answer.

**Effort:** XS (a five-minute decision plus a doc entry — the cheapest item in this entire document).

**Resolution (`TCK-20260710-TOWN-COUNCIL-HAZARD-DA`):** ruled intentional — recorded once,
applicable to both worlds, as `docs/guidelines/intentional_divergences.md` §2.30. The recurring
"silently re-deferred" pattern this thread named is now broken: a decision exists and is cited.

---

## Suggested Sequencing

Not a hard dependency chain — these are independent enough to interleave — but if picked up in
priority order:

1. **Thread 1** (F6/P2-P) first. It's the only thread that questions data already shipped; everything
   else is either forward-looking or trivially cheap.
2. **Thread 5** (P2-Q) opportunistically, any time — it's free and unblocks nothing else, so there's
   no cost to doing it whenever convenient, including inline with Thread 1's investigation ticket if
   that ticket happens to touch either world.
3. **Thread 4** (P2-O) next — cheap, purely preventive, no dependency on Thread 1's outcome.
4. **Thread 2** (§12 closeout) — can run any time, ideally after Thread 1 resolves so the Traceability/
   Testing checklist items can cite Thread 1's outcome as evidence rather than needing a second pass.
5. **Thread 3** (depth vs. breadth) last, and only after a direct conversation with you — it's the
   one thread here that is a product decision, not a technical debt item, and shouldn't be resolved by
   an agent unilaterally deciding "wide is fine" or "we need more depth."

---

## What This Doc Deliberately Does Not Propose

Per §14's Non-Goals boundary, this doc does not recommend building historical run comparison,
per-entity quality profiles, real-time alerting, or ML-based anomaly detection, even though the
growing manual "batch" documentation burden (four uplift batches, two epics, all requiring hand-authored
summary sections) is exactly the kind of repeated-by-hand cost that historical comparison
infrastructure would reduce. That trade-off is flagged, not recommended — it's a scope-expansion
decision explicitly reserved for you, consistent with how Thread 3 above is handled. If it's worth
revisiting, it should be its own conversation, not smuggled in as a side effect of any of the five
threads above.

---

## Related

- `docs/simulation_quality/quality_scoring_contract.md` — the authoritative bar this doc measures
  against (§1 goals, §7.5 pillar completeness, §12 Acceptance Criteria, §14 Non-Goals)
- `docs/audits/D06_longrun_health.md` F6 — source finding for Thread 1
- `docs/audits/D20_simq_integration.md` "SimQ Uplift Batch 4" — most recent batch history, source for
  the "current state snapshot" above
- `docs/plans/audit_fix_plan.md` P2-O, P2-P, P2-Q — the three threads with existing backlog entries
  (added 2026-07-09, same session this doc's underlying investigation happened in)
- `stored_artifacts/TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE/investigation.md`,
  `stored_artifacts/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE/investigation.md` —
  primary evidence sources for Threads 1, 4, and 5
- `docs/simulation_quality/corpus_tier_taxonomy.md`, `docs/simulation_quality/eval_matrix_results.md`
  — evidence base for Thread 3
- `tickets/done/simq-deep-coverage/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC.md` — most recent epic
  closure; its own Completion Summary already flags the two population-collapse tickets as
  byproduct-discovered work, the same discovery pattern this doc generalizes from

---

*Raised: 2026-07-10, following a user request to take a "high-level, far-ahead" view of the SimQ
epic to avoid missing leads. Supersedes no prior doc — this is the first cross-cutting synthesis of
its kind for this feature. Should be re-read (not necessarily rewritten) before scoping any future
SimQ batch, the same way `docs/audits/D06_longrun_health.md` and
`docs/simulation_quality/quality_scoring_contract.md` already are.*
