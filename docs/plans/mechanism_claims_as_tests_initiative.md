---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, documentation, schema]
---

# Plan — Mechanism Claims as Tests

**Status, scoped 2026-09-16.** The mechanism registry currently records 75 mechanisms whose state is
entirely hand-authored. This plan makes those claims **executable and consumed by a live process**,
so the registry cannot drift and cannot become the thing it was built to detect.

---

## 1. The governing constraint

**No orphan document data.** Every artefact this plan produces must be wired into a running
process — CI, a test, or the agent ticket workflow. Nothing here may be a file that someone is
expected to read or remember to update.

This is not a stylistic preference. The registry exists because this repository accumulated
mechanisms that were *built, correct, and observed by nothing*. Building a detection system that is
itself unobserved would reproduce the defect one layer up. The arc has already produced two
in-house instances of exactly that: `COMBAT_ARENA_*` tests that never touched the real compile path,
and `tests/mechanic_scenarios` which ran locally forever and in CI zero times.

**Corollary:** a generated file that nothing consumes is orphan data. Generation is not wiring.

---

## 2. Prior art

Three approaches exist. Two transfer; one mostly does not.

### Data-driven definition — does not transfer

RimWorld's Defs are its primary content definition source, and Factorio's prototype registry lets
Wube publish *generated* prototype documentation rather than writing it. Neither project has our
problem for content, because **a thing cannot exist without being declared**.

But both handle *behaviour* in code — C# and Lua respectively. Our registry catalogues mechanisms,
which is the half those projects also leave in code. This is not retrofittable, and we should stop
treating it as the aspiration. (One property *is* stealable — see §4.3.)

### Dead-code and flag debt — transfers directly

Industry measurements: codebases in active development beyond two years typically carry **10–30%
dead code**, and an analysis of 40,000 web pages found a median **70% of JavaScript functions
unused**. Our 12 orphan/gated of 75 (~16%) sits inside the normal band — this is an ordinary
problem, not a uniquely broken codebase.

The documented method is static analysis **plus** coverage, and the documented limitation is that
static analysis yields false positives and cannot simulate every execution path. That limitation is
already confirmed here: no call graph would find `camp`'s real defect, which is that no world seeds
`state.camps`.

### Architecture fitness functions — the model to follow

From *Building Evolutionary Architecture*: encode architectural rules as automated tests that run
continuously. The sharpest form of the rule is that **every decision record that is not deprecated
should map to at least one fitness function** — do not document the rule, execute it.

This repo already does this without naming it: the registry validator, the wiring-map drift test
that re-derives on every run, and the CI-coverage meta-test that caught an entire test directory
never running.

---

## 3. What is detectable, declared, and unknowable

| Field | Source | Why |
|---|---|---|
| existence, caller count | **detected** | AST / call graph |
| `orphan` | **detected** | *is* the assertion "zero callers" |
| `gated` | **detected** | a flag check on the entry path |
| `skeleton` | **detected** | body is `pass` / `NotImplementedError` |
| branch reached in a run | **detected** | execution census |
| `done` / `partial` | **declared** | a judgement about completeness |
| `depends_on` | **declared**, detector-corroborated | requires-to-exist is intent; graphify flags unsupported edges |
| what it is for, why it exists | **human** | intent is not in the code |

The point of the table: **roughly half the state vocabulary is a query somebody typed by hand.**
`orphan` does not mean "we think this is orphaned" — it means zero callers, which is executable.

### 3.1 Five shapes of search failure, catalogued 2026-09-19

The table above says existence/caller-count is "detected," as if that were a solved query. It
isn't, in practice — the *search that produces* a caller count can itself be wrong in ways that
look like a clean negative result. This repo has now hit five genuinely distinct failure shapes
across several tickets, each one independently discovered, each one producing **confident absence**
(the searcher concludes "no code exists" and is wrong) rather than an obvious dead end. Catalogued
here because five instances is a real pattern worth reading before the next search-based
investigation, not five separate anecdotes:

1. **Same name, different thing.** `progression_conversion` (the mechanism id) vs `src/progression/`
   (a directory whose contents don't implement it) — a plausible-looking path match that isn't the
   real one.
2. **Docstring concept with no symbol.** `FairShareProtocol` exists only as prose in a docstring,
   never as a class or function grep could find.
3. **A naming convention hides a write.** `succession`'s own false verification verdict
   (`registries/mechanisms.yaml`'s own entry): the search pattern `heir_entity_id=` could not match
   `heir_entity_id_set=`, this codebase's own `_set`-suffix convention for `StateUpdate` patch
   fields (`death_reason_set`, `is_permadeath_set`, same shape). The real write existed one
   character-pattern away from what was searched.
4. **Post-rename terminology drift.** `race_archetype`'s real implementation is `SpeciesDefinition`
   (`src/content/schema.py`) — `TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY` renamed
   `RaceDefinition`/`race_id` repo-wide on 2026-09-04, *after* the search vocabulary
   ("race"/"Race") had already been formed by the mechanism's own registered name. Same shape hit
   `country_lifecycle` (real code is `FactionDecisionPhase`, "Country" and "Faction" are the same
   underlying class) and `city` (real code is `RegionState`, never split into its own class) —
   conflation rather than rename, but the same "the search vocabulary and the real vocabulary
   diverged" root cause.
5. **A concept name that is never a symbol.** The wiring map's own "Directive → Project → Objective
   → Action" (the plain-English definition of the `goal_hierarchy` mechanism) appears nowhere in
   the codebase as a literal string, class, or function — it maps to a cluster of methods
   (`evaluate_project_switch`, `resume_project`, `process_project_outcome`, others) on
   `StrategicIntelligenceSystem`, a class whose own name shares no vocabulary with the concept it
   partly implements. `regional_trauma`'s own real mapping to `TraumaRegionConcernBridge`
   (`src/domains/world_emergence/services.py`) is the same shape, found only via `graphify query
   "trauma"`, not grep — the one directly measured case for why CLAUDE.md's graphify-before-grep
   rule exists, now joined by four more instances of the same underlying failure class.

**Shapes 4 and 5 are the newest and the most dangerous of the five**, because unlike 1-3 (a wrong
match, a docstring-only symbol, a near-miss pattern — each still findable by trying one more
variant), 4 and 5 produce a search that returns cleanly empty and looks exhaustive. Nothing in the
search itself signals "you're searching the wrong vocabulary." The only defenses found so far:
checking a mechanism's own naming/rename history (terminology-drift epics, atlas investigation
notes) before concluding absence, and preferring `graphify query` over raw grep for exactly the
class of query graphify's own AST/fuzzy matching is built for — a preference this doc's own §4.1
detector plan and CLAUDE.md's own Context Scan mandate already assume, now with five concrete
instances behind it instead of one.

Source tickets: `TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION` (shapes 1-3, via
`succession`'s own corrected entry), `TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-
RESOLUTION` (shapes 4-5, via `race_archetype`/`country_lifecycle`/`city`/`goal_hierarchy`),
`TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` (shape 5's first instance,
`regional_trauma`).

---

## 4. The three wirings

### 4.1 Detectors, compared against declarations, in CI

A generated detected-facts set (caller count, flag-gating, stub-ness, census reachability) per
mechanism. **It is not published or read.** Its only consumer is a comparison check that reports
where *detected* and *declared* disagree — for example a mechanism declared `done` with zero
detected callers.

Report-only at first, per the census initiative's own report-first rule. A detector that fires on
legitimate code teaches people to ignore it.

### 4.2 Claims as tests

Each mechanically-checkable claim becomes an executable assertion, so a stale claim **fails** rather
than sitting there looking correct:

- declared `orphan` → assert zero production callers
- declared `gated` → assert a flag check exists on the entry path
- declared `skeleton` → assert the body is a stub
- declared `verified.instrument: scenario` → assert the cited test exists and runs in CI

That last one closes a real hole: a verification note can currently cite a test that has been
deleted or renamed, and nothing would notice.

### 4.3 A registration gate for new mechanisms

The one property worth stealing from Factorio and RimWorld: **nothing new exists without being
declared.** A CI check that new behaviour clusters appear in `mechanisms.yaml`.

This will not fix the existing 75, and it is not meant to. It stops the growth problem: the registry
stays complete by construction rather than by anyone remembering.

**Scope it narrowly** — new modules or domain packages, never every new function. A gate with false
positives on ordinary helpers gets disabled within a week, and then detects nothing.

---

## 5. Agent-workflow wiring

The parity ledger already has this shape in `CLAUDE.md`: *when a behavior changes, find the relevant
entry and update its status and evidence.* The registry needs the equivalent, or it decays exactly
as the five artefacts did.

- a ticket that changes a mechanism updates its registry entry, checked at close
- `done-checker` gains the condition
- the investigation phase consults the registry as the "what exists and does it work" index

**This edits `CLAUDE.md`, which requires the user's direct authorisation** — neither a peer's
agreement nor this plan supplies it. Scope it, do not apply it, until asked.

---

## 6. Non-goals

- **No new document, dashboard, or report to read.** Detector output exists to be compared, not
  browsed.
- **No auto-derived `depends_on`.** graphify corroborates declared edges; it does not generate them.
  35k nodes will not cluster into 75 mechanisms.
- **No blocking gate on agent-working telemetry** — see the deleted attribution ratchet. Hard gating
  is for simulation behaviour.
- **No retroactive data-driven rewrite** of mechanisms into declarative content. §2 explains why.
- **No claim that detection is complete.** `camp` is the standing counter-example: correct, wired,
  reachable code that no static analysis would flag, defeated by world data.

- **No prose consolidation across the atlas, capabilities page and wiring map.** Those three describe
  mechanisms at different levels of abstraction for different readers, and that difference is real
  information, not duplication — *"goblin camps spawn raiders that attack travellers"* and
  *"`CampState` drives spawn scheduling via the raid trigger path"* are different facts about the same
  thing, and neither generates from the other. The genuinely duplicated part is the **status claim**
  embedded in prose. `motivation_doctrine` read *"confirmed live via the always-on Adventure route
  scoring path"* in three documents for eight days after its code was deleted; the description of what
  it did was fair, the claim that it still worked was not. Prose describes what a mechanism does; the
  registry owns whether it works. Enforced by
  `TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION`.

- **No `CLAUDE.md` workflow rule requiring registry updates**, because the repository already ran this
  experiment. The parity ledger carries exactly that rule — *when a behavior changes, find the
  relevant entry and update its status and evidence* — and it decayed: `TCK-20260904` had to be run
  specifically to repair stale parity-ledger `test_path` citations. **A rule that depends on someone
  remembering is the same failure class as a document that depends on someone reading it.** The
  mechanical equivalent, detecting when `implemented_by`-cited code changed without a corresponding
  entry update, is `TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION` and needs no policy
  change.

- **No symbol-level bindings yet.** File-level `implemented_by` first. Symbol-level is more precise
  *and* more brittle — it breaks on every rename — and that brittleness is only a feature once a check
  exists to catch it. Sequence it after detection phase 1 is running, not before, or renames generate
  noise nobody can act on.

---

## 7. Phasing

1. **Detect and compare** — caller-count and stub detection over the existing 75, report-only. This
   immediately measures how much hand-authored state is wrong, which is the cheapest evidence of
   whether the rest is worth building.
2. **Claims as tests** — promote the detectable claims to assertions once phase 1 shows the false
   positive rate.
3. **Registration gate and workflow wiring** — last, and the `CLAUDE.md` portion only on the user's
   authorisation.

Phase 1 is deliberately the smallest thing that produces a number. If it reports that the declared
state is largely accurate, phases 2 and 3 are worth less than they look and should be re-argued.

## Related

- `docs/plans/mechanism_registry_initiative.md` — the registry this enforces
- `docs/plans/simulation_execution_census_initiative.md` — the reachability instrument, report-first rule
- `docs/plans/mechanic_verification_scenarios_proposal.md` — the runtime-verification producer
- `docs/plans/world_composition_precondition_gap_finding.md` — the family detection cannot reach
