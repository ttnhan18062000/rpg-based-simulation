---
status: active
layer: simulation
authority: P1
audience: agent
tags: [roadmap, simulation-quality, calibration, corpus, determinism, planning]
date: 2026-07-10
source: docs/plans/idea_simq_near_perfect_roadmap.md
---

# Simulation Quality (SimQ) — Long-Term Development Roadmap

## Source & Method

This roadmap replaces reactive, per-investigation SimQ work with a top-down sequence. It is
synthesized from `docs/simulation_quality/quality_scoring_contract.md`'s own stated bar (§1, §7.5,
§12, §14), the audit history in `docs/audits/D06_longrun_health.md` and
`docs/audits/D20_simq_integration.md`, the backlog in `docs/plans/audit_fix_plan.md`, and
`docs/plans/idea_simq_near_perfect_roadmap.md`'s five-thread synthesis (2026-07-10) — which this
document supersedes as the actionable plan; that doc remains as the evidence trail for *why* these
threads matter, this doc is *what to do about them, in what order*.

Two scope decisions were made explicitly by the user before this roadmap was drafted (2026-07-10),
and both shape its structure:

1. **Corpus pillar-depth ambition: staged/bounded expansion, not full corpus-wide, not "stay narrow."**
   The roadmap deepens the corpus in validated waves — each wave proves a pillar's activation cost
   on 2–3 worlds before any further commitment — rather than either scoping all 17 worlds × 5 gated
   pillars up front, or declining to deepen the corpus at all.
2. **SimQ's MVP Non-Goals (§14) stay out of scope.** Per-entity quality profiles, historical run
   comparison, real-time push alerts, ML-based anomaly detection, and automated config suggestion are
   **not** part of this roadmap, even though the growing manual "uplift batch" documentation overhead
   makes historical comparison specifically tempting. This roadmap fully realizes the original 3
   goals before entertaining new capability classes.

**Every phase below produces a real ticket when picked up — none of this is pre-scoped in enough
detail to implement directly.** This document sequences and sizes the work; each phase's own
Investigate step still runs against current repo state before implementation, per standard workflow.

> **Ticketing pass completed 2026-07-10.** All 6 phases now have a real ticket (or, for Phase 1,
> two) filed under `tickets/todos/simq-roadmap-phase{0-5}-*/`, per explicit user instruction to
> travel through every proposed phase and pre-file the full roadmap before implementing anything.
> Scoping surfaced substantial corrections to this document's original assumptions — most
> significantly, **Phase 3's premise was largely stale**: most of the corpus already has
> FACTION/INFORMATION content from the since-completed Corpus Tiers epic, which this roadmap's
> first draft did not account for. See the correction notes under Phase 1, Phase 3, and Phase 4
> below for the specific findings — do not trust this document's *original* per-phase prose over
> those correction notes where they conflict; the correction notes reflect verified current repo
> state, the original prose reflected this doc's first-draft assumptions.

---

## The Bar This Roadmap Targets

Per `quality_scoring_contract.md` §1, SimQ has exactly three goals: automated quality visibility,
regression detection, and balance/tuning support. "Complete" does not mean "every non-goal built" —
it means these three goals hold **reliably**, for a **deliberately and visibly bounded** portion of
the corpus, with the module's own Acceptance Criteria (§12) demonstrably true rather than assumed.
This roadmap's five phases map directly onto that bar: Phase 0 makes the *existing* measurement
trustworthy; Phases 1 makes the corpus *stop silently regressing* the same way twice; Phases 2–4 grow
*how much of the corpus* the visibility/tuning goals actually apply to; Phase 5 is the explicit
checkpoint where "how much is enough" gets decided with real data instead of guessed up front.

---

## Phase Summary

| Phase | Goal | Effort | Blocks |
|---|---|---|---|
| **0 — Reliability Foundation** — **DONE 2026-07-11** | Make existing long-run measurements trustworthy | M | Everything — building corpus depth on unverified anchors compounds the risk |
| **1 — Process Hardening** | Stop the same defect classes recurring silently | S | Nothing downstream; runs parallel to Phase 0 |
| **2 — Depth Wave 1: SOCIAL** | Prove the cheap pillar-activation playbook | M | Phase 3 (same playbook shape, higher cost) |
| **3 — Depth Wave 2: FACTION + INFORMATION** | Extend the proven playbook to compiler-construction-gated pillars | L | Phase 4 |
| **4 — Depth Wave 3: COGNITION (self-model)** | Generalize the hardest, least-proven pillar beyond its single pilot world | L–XL | Phase 5 |
| **5 — Coverage Decision Gate** | Decide, with empirical cost data, whether to continue toward full-corpus coverage or declare staged depth the final bar | XS (decision only) | Nothing — terminal checkpoint |

**Effort legend:** XS ≤ 1 day · S = 2–4 days · M = 1–3 weeks · L = 3–8 weeks · XL = 2+ months.

**Critical path:** Phase 0 → (Phase 2 → Phase 3 → Phase 4) → Phase 5. Phase 0 is now complete
(2026-07-11) — Phases 2–4 are unblocked on this dependency. Phase 1 runs in parallel with Phase 0
relative to everything else — but as of ticketing (2026-07-10), 1.1 and 1.2 are **not**
independent of each other; see the correction note under Phase 1 below. Recommended internal order:
1.2 before 1.1.

---

## Estimated Ticket Count

**Original estimate (pre-ticketing) vs. actual, post-scoping (2026-07-10).**

| Phase | Original estimate | Filed | Post-scoping revision |
|---|---|---|---|
| **0 — Reliability Foundation** | 2 (0.1, 0.2) | **2 tickets filed** | Held — no correction needed |
| **1 — Process Hardening** | 2 (1.1, 1.2) | **2 tickets filed** | Held on count, but tier revised up (both standard, not hotfix/XS) and a real 1.1↔1.2 coupling found — see Phase 1 correction note |
| **2 — Depth Wave 1: SOCIAL** | 2–3 | **1 ticket filed** | Premise verified accurate (still single-world), 3 candidates identified, confirmed cheaper content-authoring shape than FACTION/INFORMATION (no compiler-construction gap) — 1 ticket may suffice for all 3 candidate worlds rather than 2–3 |
| **3 — Depth Wave 2: FACTION + INFORMATION** | 5–8 | **2 tickets filed** | **Major correction** — premise was largely stale. 11/17 worlds already have FACTION content, 9/17 already have INFORMATION content (from the since-completed Corpus Tiers epic, which this roadmap's first draft didn't account for). FACTION's own Investigate phase may find 0–1 real candidates remain; INFORMATION's may find **zero**. This phase's actual work may end up closer to "confirm already-adequate coverage and close" than "activate 2–3 more worlds" — do not budget the original 5–8 estimate without re-reading both tickets' own Assumptions/Open Questions first |
| **4 — Depth Wave 3: COGNITION** | 1 firm + 2–4 contingent | **1 ticket filed** | Candidate-world correction: the original text named `hero_guild_routing` — verified **wrong** (it's Unit-tier, isolating AGENCY only). Redirected to `urban_political` (archetype-tier, already has `pending_self_model_information_events` seeded by `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`). Contingent-ticket count still unknowable until this investigation reports back |
| **5 — Coverage Decision Gate** | 0–1 | **0 tickets** (placeholder folder only) | Held — intentionally no ticket yet, per design |

**Revised total: roughly 8 tickets filed so far**, with Phase 3 and Phase 4's real remaining work
likely smaller than the original 12–21 estimate implied — the corpus is closer to "adequately deep"
on FACTION/INFORMATION than this roadmap's first draft assumed. This is a genuinely good-news
correction, not a scope increase: **do not re-inflate the estimate back toward 12–21** without first
reading what each Phase 3/4 ticket's own Investigate phase actually finds.

---

## Phase 0 — Reliability Foundation — **COMPLETE (2026-07-11)**

**Goal:** Confirm that measurements already shipped mean what they claim to mean, before any further
corpus investment makes that question more expensive to answer.

Both 0.1 and 0.2 landed 2026-07-11. Phases 2–4 (corpus depth waves) are now unblocked on this
critical-path dependency; Phase 1 was already running in parallel and is unaffected.

### 0.1 — Long-run calibration reliability verification (the F6 thread) — **DONE (2026-07-11)**

**Problem:** `src/engine/kernel.py`'s tick-budget watchdog and mid-tick emergency throttle measure
real wall-clock compute time, not simulated ticks, and drop resolution work when a tick exceeds
budget. Two identical-seed runs of `generated_frontier_3_42` diverged by 100+ ticks in
floor-violation onset and 2×+ in final population. Every 1000t/2000t anchor in
`tests/simulation_quality/fixtures/grade_anchors.json` (`SLOW_ANCHOR_KEYS`) was captured from a
single run — we don't currently know which, if any, are throttle-timing artifacts.

**Work:** One investigation-tier ticket. For each `SLOW_ANCHOR_KEYS` entry, re-run 2–3× at the same
seed. Stable anchors get a one-line "re-verified stable" note in `eval_matrix_results.md`. Unstable
anchors get converted to a tolerance-based guard (same pattern as
`test_generated_frontier_3_42_extended_population_stability`) or flagged as carrying unquantified
variance. **Do not touch `kernel.py`'s throttle logic** — this is a measurement-verification ticket,
not an engine-fix ticket.

**Acceptance signal:** every `SLOW_ANCHOR_KEYS` entry has a documented reliability status (stable,
converted-to-tolerance, or flagged-unverified) in `eval_matrix_results.md`.

**Ticket filed (2026-07-10):** `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` — standard tier.
Scope confirmed exactly 18 `SLOW_ANCHOR_KEYS` entries across 8 worlds; no conflicts found; reuses the
`generated_frontier_3_42` investigation's exact two-run instrumented-drive methodology as required.

**Result (landed 2026-07-11):** all 18 keys re-run 3 trials each (54 total calibration runs, real
throttled `Kernel`, no `audit_mode`) — **18/18 stable**. Every one of 540 pillar/trial data points
fell within the existing ±1-`GRADE_ORDER` band despite confirmed throttle-timing variance
(`budget_warnings` 41–539/run, `watchdog_trips` 1–3/run, up to ~4× elapsed-time spread for
identical seed/code). Zero anchors required conversion to a tolerance-based guard; zero flagged
unverified. Full evidence: `docs/simulation_quality/eval_matrix_results.md` "Anchor Reliability
Verification" section, `stored_artifacts/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY/raw_calibration_sweep.md`.
`kernel.py` and `grade_anchors.json` left untouched, per scope guard.

### 0.2 — Contract Acceptance Criteria closeout — **DONE (2026-07-11)**

**Problem:** `quality_scoring_contract.md` §12's five checklists (Functional, Performance,
Scalability, Extensibility, Traceability, Testing) have sat as unchecked `[ ]` markdown since
2026-06-28, through ~40 subsequent tickets. Most items are almost certainly true; nobody has gone
and confirmed which.

**Work:** One hotfix-tier ticket. Go through §12 line by line, cite live evidence (a test, a `grep`,
a direct invocation) for each item, check the box or file the gap. Update `quality_scoring_contract.md`
§12 in place.

**Acceptance signal:** every §12 checkbox is either checked-with-citation or has a linked follow-up
ticket for a confirmed gap.

**Dependency note:** 0.1 and 0.2 can run in either order or in parallel — 0.2's Traceability/Testing
items are cleaner to cite if 0.1 has already landed, but neither blocks the other from starting.

**Ticket filed (2026-07-10):** `TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT` — hotfix tier, no conflicts.

**Result (landed 2026-07-11):** 24/25 §12 checkboxes verified and checked with live citations against
current source (both explicit safety-invariant items — `QUALITY_SCORING_DISABLED=1` bit-identical
output and scoring-exception isolation — re-confirmed by direct code read plus a live passing test
run, not by pointing at the 2026-06-28 parity entries). 1 genuine gap found (Traceability item 3, no
end-to-end §9 integration test) and filed as a linked follow-up:
`tickets/todos/TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST.md` (standard tier). A stale
`docs/parity_ledger/infrastructure.yaml` INFRA-233 test-path citation was also found and corrected
in the same session.

---

## Phase 1 — Process Hardening

> **Correction (2026-07-10, after ticketing):** this section originally claimed 1.1 and 1.2 were
> independent and could land in any order — **that was wrong.** Both tickets' own Scope phases
> independently discovered the same coupling: running 1.1's corpus-wide test before 1.2's DA ruling
> lands hits the `town_council`/`bandit_road` case as a live, expected test failure. 1.1's ticket
> already accounts for this with a temporary, explicitly-cited test exception pending 1.2; 1.2's own
> investigation additionally found the ruling is less trivial than estimated (`trading_company_hub.yaml`
> shares the same faction+hazard-region shape, requiring a blast-radius check before granting any
> immunity), which is why it scoped to standard tier, not the hotfix/XS this section originally
> assumed. **Recommended order: land 1.2 before 1.1**, so 1.1 never needs the temporary exception to
> exist at all — but 1.1 is already written to tolerate either order if 1.2 runs second.

Runs in parallel with Phase 0. Both items are already fully scoped in `docs/plans/audit_fix_plan.md`
and need no further investigation before ticketing.

### 1.1 — `hazard_kind` corpus-wide completeness test (P2-O)

The missing-`hazard_kind` bug (region has `hazard_level > 0`, no declared `hazard_kind`, resolver
defaults to `"PHYSICAL"`, which nothing is immune to) has recurred **three times** across
independent sweeps (2026-06-30, 2026-07-04, 2026-07-09). `test_hazard_kind_matches_populating_faction_immunity`
exists but only runs against an explicit allowlist. **Work:** extend it to run corpus-wide,
unconditionally, for every populated hazardous region in every world. Originally estimated as one
S-effort test-only ticket; scoped to standard tier once ticketed (real risk of surfacing further
recurrences requiring judgment).

**Ticket filed (2026-07-10):** `TCK-20260710-HAZARD-KIND-CORPUS-WIDE` — standard tier. Scope
includes the temporary `town_council`/`bandit_road` test exception described above, to be reconciled
once 1.2 lands.

### 1.2 — `town_council`/`bandit_road` DA ruling (P2-Q)

The same two-entity hazard-exposure question has been independently found and silently re-deferred
twice (`urban_political`, then `generated_frontier_3_42`). **Work:** originally estimated as one XS
ticket — a single recorded decision (intentional flavor, documented in `intentional_divergences.md`,
or a genuine gap, fixed with a matching immunity), applicable to both worlds. Real cost turned out
higher — see correction note above.

**Ticket filed (2026-07-10):** `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` — standard tier (bumped up from
the XS/hotfix estimate once scoping found the `trading_company_hub.yaml` blast-radius question).

**Acceptance signal (both items):** the recurrence pattern each documents cannot recur a 4th/3rd time
without the new test or the recorded ruling catching it.

---

## Phase 2 — Depth Wave 1: SOCIAL

**Why SOCIAL first:** per `TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT`'s finding, SOCIAL is pure
feature-flag gating (`ENABLE_SOCIAL_COOPERATION`) with no compiler-level durable-state construction
gap — unlike FACTION and INFORMATION, which required `WorldCompiler` fixes before any content
authoring could matter. SOCIAL is the cheapest pillar to prove the "activate a gated pillar in more
worlds" playbook against, before spending Phase 3/4's larger budget on the harder pillars.

**Work:** One standard-tier ticket. Investigate phase selects 2–3 archetype-appropriate candidate
worlds from the existing 17-world corpus (this roadmap deliberately does not pre-select them — that
judgment call belongs to the ticket's own Investigate phase, working from real per-world content, not
from this document's abstraction). For each selected world: enable `ENABLE_SOCIAL_COOPERATION` in its
calibration profile, author or confirm cooperation-relevant content exists, recalibrate, run a
corpus-wide regression sweep (SOCIAL activation is flag-only, but sweep anyway — Pattern 6 activation
history shows adjacent pillars can shift as a side effect, e.g. COGNITION moved with INFORMATION).

**Acceptance signal:** SOCIAL grade moves measurably off `C` in ≥ 2 additional worlds, with
calibration evidence (not just a flag flip) in `eval_matrix_results.md`, and 0 regressions on
`make evaluate`.

**Decision point for Phase 3 planning (not blocking Phase 2's start):** once this wave's ticket
closes, its actual cost (ticket count, calibration cycles, content-authoring effort) becomes the
first real data point for calibrating Phase 3's size estimate — Phase 3's own Investigate phase
should cite this wave's actual cost, not just this roadmap's estimate.

**Ticket filed (2026-07-10):** `TCK-20260710-SIMQ-DEPTH-SOCIAL` — standard tier, no conflicts.
Scoping re-verified this phase's premise directly (unlike Phase 3, it held): `ENABLE_SOCIAL_COOPERATION`
is genuinely still single-world (`urban_political` only, confirmed by grep across all 14 calibration
profiles), and no side-effect activation occurred during the intervening Corpus Tiers epic work.
Confirmed `CooperationPhase` triggers from live per-tick state (proximity, trust, faction, combat
risk) with no Pattern-6-style pre-seeded schema field required — a materially cheaper
content-authoring shape than FACTION/INFORMATION, flagged explicitly so Phase 3's estimate isn't
applied to this phase by false analogy. Candidates identified (to be re-verified, not committed, at
Investigate time): `dungeon_crawl`, `frontier_living_world`, `highland_traverse`.

---

## Phase 3 — Depth Wave 2: FACTION + INFORMATION

> **Correction (2026-07-10, after ticketing) — this phase's premise was largely stale.** The text
> below assumes FACTION and INFORMATION are each still confined to `urban_political`, matching this
> roadmap's first-draft understanding. **Both scoping tickets independently found that's no longer
> true**, because the since-completed `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` and
> `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` (both part of the Corpus Tiers epic, closed before this
> roadmap was drafted) already authored FACTION content into 8 more worlds and INFORMATION content
> into 6 more:
> - **FACTION**: 11 of 17 corpus worlds already have `faction_tension_overrides` content, calibrated
>   and grade-anchored (S/A). Of the 6 remaining, most have a documented tier-purity reason to stay
>   inert (Stress/Unit/Regression-baseline tiers). `TCK-20260710-SIMQ-DEPTH-FACTION`'s own
>   Investigate phase may find as few as **0–1** legitimate candidates remain, not the 2–3 this
>   section assumed.
> - **INFORMATION**: 9 of 17 corpus worlds already have `information_source_profiles` content,
>   calibrated. All 8 remaining worlds have a pre-existing, already-documented reason to stay inert.
>   `TCK-20260710-SIMQ-DEPTH-INFORMATION`'s own scoping concluded the honest current reading is
>   **zero** undisputed candidates.
>
> **What this means:** this phase's real remaining work is likely much smaller than the "5–8
> tickets" estimate below implied, and may resolve as "confirm the corpus is already adequately deep
> on these two pillars, document that conclusion, close" rather than a multi-world content-authoring
> effort. Both filed tickets carry this finding in their own Assumptions/Open Questions sections
> (flagged high severity) — read those before assuming this section's original framing still holds.

**Why these two, together, second (original framing, kept for context — see correction above for
current reality):** both share the same underlying defect class that had to be
fixed once at the compiler level (`WorldCompiler` never constructed `FactionState.tension_level` or
`information_source_profiles` for any world) — documented as reusable **Pattern 6**
("Compile-Time Pillar Activation Pattern") in `docs/guidelines/design_patterns.md`. The hard,
one-time engine work is already done; what remains per-world is content authoring plus
recalibration, the same shape of work as Phase 2 but with a proven-nontrivial history: activating
INFORMATION in `urban_political` alone surfaced 3 causally-linked kernel bugs
(`SelfModelUpdatePhase` hardcoding `events=[]`, a missing pipeline merge wrapper, a tick-alignment
bug affecting 3 unrelated event types corpus-wide). Budget for **L**, not **M**, on this basis —
Phase 2's actual cost should sanity-check this estimate before committing.

**Work:** Two tickets (FACTION, INFORMATION — can run in parallel, different content domains), each
following Phase 2's shape: 2–3 candidate worlds, seed the Pattern-6 field via the existing
schema/compiler/resolver plumbing (no new engine work expected — if the Investigate phase finds
otherwise, that's new information that should pause the ticket for a plan revision, not be pushed
through), author matching content, recalibrate, full regression sweep given the cross-pillar
side-effect history above.

**Acceptance signal:** FACTION and/or INFORMATION grades move measurably off `C` in the targeted
worlds, 0 regressions, and any newly-discovered engine bugs (if the INFORMATION history repeats) are
tracked as their own tickets rather than silently folded into the content-authoring ticket's scope.
Per the correction note above, "zero new worlds, coverage already adequate, documented and closed"
is also a valid acceptance outcome for either ticket — this phase does not require finding new
candidate worlds if honest investigation finds none remain.

**Tickets filed (2026-07-10):**
- `TCK-20260710-SIMQ-DEPTH-FACTION` — standard tier. No duplicate work; confirmed Pattern-6 plumbing
  reusable as-is; UQ-1 (high severity) flags the stale-premise finding above.
- `TCK-20260710-SIMQ-DEPTH-INFORMATION` — standard tier. No duplicate work; confirmed
  `InformationBeliefPhase` Branch A mechanism intact; UQ-1 (high severity) flags the
  zero-candidates finding above. Both tickets sit in the same folder
  (`tickets/todos/simq-roadmap-phase3-depth-faction-information/`) and reference each other.

---

## Phase 4 — Depth Wave 3: COGNITION (self-model / Branch B)

**Why last:** this is the least-proven pillar. Its only evidence of working at all is
`unit_selfmodel_pilot`, a purpose-built unit-tier world, not a real archetype world — and reaching
even that required fixing 3 more causally-linked bugs
(`SelfModelUpdatePhase.apply()` hardcoded `events=[]`, `self_model_bundle_set` never durably
materialized into `EntityState.self_model` for any entity/world ever, requiring a new
`SelfModelPatch` component-patch class). There is currently **zero evidence** this generalizes
cleanly to a real, already-populated archetype world rather than a small, deliberately-isolated pilot.

**Work:** Start with an investigation-only ticket (not an implementation ticket) — attempt to seed
`self_model.knowledge.unknowns` for one real archetype world and honestly report whether the pilot's
mechanism holds up or whether more engine work is needed first. **Do not commit to a multi-world
rollout until this single-world investigation reports back** — Phase 4 is explicitly the
highest-uncertainty phase in this roadmap and should not be pre-sized past "investigate one world
first."

> **Correction (2026-07-10, after ticketing):** this section originally named `hero_guild_routing`
> as the candidate world — **verified wrong.** `hero_guild_routing` is Unit-tier
> (`docs/simulation_quality/corpus_tier_taxonomy.md:136`), explicitly isolating AGENCY/route-selection
> only; its COGNITION grades come from `strategic_intelligence` signal, not self-model. It is the
> same kind of single-mechanic-isolation world as `unit_selfmodel_pilot` itself — not the
> archetype/End-to-end-tier world this phase actually needs to test generalization against. The
> filed ticket redirects to **`urban_political`** instead — a genuine archetype-tier world that
> already has `pending_self_model_information_events` seeded (by `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`
> Step 8), with `ENABLE_BELIEF_ASSIMILATION` currently off.

**Acceptance signal:** a documented, evidence-based answer to "does Branch B generalize beyond its
pilot world" — either a successful first real-world activation, or a clearly scoped follow-up
engine-fix ticket if it doesn't, or a DA ruling that COGNITION stays pilot-only if the cost proves
disproportionate.

**Ticket filed (2026-07-10):** `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE` — standard tier.
No duplicate work. Scope requires at least one run with *both* `ENABLE_SELF_MODEL_COGNITION` and
`ENABLE_BELIEF_ASSIMILATION` on, to exercise the still-untested query-routing half of Branch B (the
pilot world only exercises the materialization half).

---

## Phase 5 — Coverage Decision Gate

**Not a work item — a decision checkpoint**, explicitly deferred rather than pre-decided, per the
"staged, not full-corpus" scope decision this roadmap was built against.

Once Phases 2–4 have landed (or Phase 4 has reported its investigation-only finding), this roadmap's
job is done and a new, short decision doc (not a full re-plan) should answer: given the *actual*
observed cost-per-world-per-pillar from the three waves, is continuing toward full 17-world coverage
worth it, or does the corpus's current staged depth constitute the final "near-perfect" bar for this
feature? Either answer should be recorded the same way the AGENCY-DA ruling was — a documented
decision, not a silent stop or a silent continuation.

**My recommendation, to be revisited with real data at this checkpoint, not acted on now:** given
Phase 3's history (one world's INFORMATION activation surfacing 3 kernel bugs) and Phase 4's
near-total uncertainty, I expect the honest answer at this gate will be "staged depth is the right
permanent bar, full-corpus coverage isn't worth its cost" — but this is exactly the kind of call that
should be made with three waves of real evidence, not guessed today.

**Update (2026-07-10, after ticketing):** Phase 3's staleness correction (above) makes this
recommendation more likely, not less — if the corpus turns out to already be adequately deep on
FACTION/INFORMATION with little new work needed, that itself is evidence toward "staged depth was
already close to the right bar." Still not decided now; still waiting on real Phase 2–4 outcomes.

**Folder status:** `tickets/todos/simq-roadmap-phase5-coverage-gate/` exists with a `SEQUENCE.md`
explaining why it intentionally holds no ticket yet — filed 2026-07-10 alongside the other 5 phases'
folders so the roadmap's full structure is represented under `tickets/todos/`, per explicit user
instruction.

---

## Explicitly Out of Scope

- Any of `quality_scoring_contract.md` §14's Non-Goals (per-entity profiles, historical run
  comparison, real-time push alerts, ML anomaly detection, automated config suggestion) — reaffirmed
  by explicit user decision, 2026-07-10.
- `docs/plans/audit_fix_plan.md` items not specific to SimQ (P2-K ContentUsageMatrix auto-generation,
  P2-N degraded-mode catalog fallback, P3-A/P3-C) — real backlog items, but general engine debt, not
  part of this feature's own roadmap.
- Touching `src/engine/kernel.py`'s tick-budget throttle/watchdog logic anywhere in this roadmap —
  every phase that touches long-run behavior (0.1, and any Phase 2–4 world that happens to run past
  ~tick 300) treats it as documented, intentional, out-of-scope engine behavior, not something this
  roadmap's tickets are licensed to change.
- Pre-selecting which specific worlds each depth wave targets — deliberately left to each phase's own
  Investigate step, working from live corpus content, not from this document.

---

## Related

- `tickets/todos/simq-roadmap-phase{0,1,2,3,4,5}-*/` — the 6 phase folders this roadmap is filed
  into (all 6 exist as of 2026-07-10; Phase 5's is a placeholder with no ticket yet, per design).
  Each folder has its own `SEQUENCE.md`. This is where the actual, current ticket state lives —
  treat it as more current than this document's prose wherever the two disagree.
- `docs/plans/idea_simq_near_perfect_roadmap.md` — the five-thread evidence synthesis this roadmap
  sequences into phases; read it for the full problem/evidence detail behind Phases 0 and 1.
- `docs/simulation_quality/quality_scoring_contract.md` — §1 (goals), §7.5 (pillar completeness,
  confirms no 11th pillar needed), §12 (Acceptance Criteria, target of Phase 0.2), §14 (Non-Goals,
  reaffirmed Out of Scope).
- `docs/audits/D06_longrun_health.md` F6 — source finding for Phase 0.1.
- `docs/audits/D20_simq_integration.md` — full uplift-batch history; "SimQ Uplift Batch 2" documents
  the FACTION/INFORMATION activation cost this roadmap's Phase 3 estimate is grounded in.
- `docs/guidelines/design_patterns.md` Pattern 6 — the compile-time pillar activation pattern Phase 3
  reuses.
- `docs/plans/audit_fix_plan.md` P2-O, P2-P, P2-Q — the fully-scoped backlog entries behind Phase 0.1
  and Phase 1.
- `docs/guides/feature_flags.md` — the flag/`FeatureMode` mechanism every depth-wave phase activates
  per world.
- `docs/simulation_quality/corpus_tier_taxonomy.md` — the existing tier structure (Unit/End-to-end/
  Stress/Regression) each depth wave's candidate-world selection should respect.

---

*Raised: 2026-07-10, following a user request for a complete, top-down SimQ development roadmap
rather than continued reactive small-fix work. Two scope decisions (staged corpus depth, Non-Goals
held) were made explicitly by the user before drafting. Ticketed the same day, per explicit user
instruction to travel through every phase and pre-file all tickets into `tickets/todos/` — nothing
implemented yet. Phase 5 is the next point at which this document should be revisited, not rewritten
from scratch.*
