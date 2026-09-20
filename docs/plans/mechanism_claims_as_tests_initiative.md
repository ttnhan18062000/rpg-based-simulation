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

### 3.1 Six shapes of search failure, catalogued 2026-09-19, extended 2026-09-20

The table above says existence/caller-count is "detected," as if that were a solved query. It
isn't, in practice — the *search that produces* a caller count can itself be wrong in ways that
look like a clean negative result. This repo has now hit six genuinely distinct failure shapes
across several tickets, each one independently discovered, each one producing **confident absence**
(the searcher concludes "no code exists" and is wrong) rather than an obvious dead end. Catalogued
here because six instances is a real pattern worth reading before the next search-based
investigation, not six separate anecdotes:

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
6. **A search correctly executed inside a scope that was itself wrong, added 2026-09-20.** The
   `commitment_betrayal`/`commitment_pressure_consequences` merge candidate
   (`TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION`'s own #7/#17) concluded "no
   distinct implementation of its own anywhere in `src/`" after searching
   `src/domains/commitment/` — every file in that directory, matched thoroughly, correctly. The
   search itself had no defect. What was wrong was the boundary: a real, distinct, purpose-built
   `BetrayalRecord` type lived in `src/core/models/social.py`, a directory nobody thought to check
   because the sibling mechanism's own binding lived entirely inside `src/domains/commitment/`, and
   that made the directory look like the whole territory. Found
   (`TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION`) only because the merge
   candidate itself was re-investigated rather than executed on the strength of its own prior
   conclusion. This is a **different shape from all five above**, and a different defense: shapes
   1-5 are all failures of the *query* — the search covered the right ground and still missed or
   misread something. Shape 6 is a failure of *scope* — the query would have worked fine if aimed
   at the right ground, and the boundary that excluded the right ground was invisible in the
   result (a clean, confident "not found" looks identical whether the scope was right or wrong).
   The defense is different too: not "try another query variant" or "check for a rename," but
   **before accepting a merge/absence conclusion, ask what the search's own boundary was and
   whether anything justified it being that boundary** — here, nothing did; the boundary was
   inherited from where the *other* mechanism's code happened to live, not from any property of
   the mechanism actually being searched for.

**Shapes 4 and 5 are the newest and most dangerous of the first five**, because unlike 1-3 (a wrong
match, a docstring-only symbol, a near-miss pattern — each still findable by trying one more
variant), 4 and 5 produce a search that returns cleanly empty and looks exhaustive. Nothing in the
search itself signals "you're searching the wrong vocabulary." The only defenses found so far:
checking a mechanism's own naming/rename history (terminology-drift epics, atlas investigation
notes) before concluding absence, and preferring `graphify query` over raw grep for exactly the
class of query graphify's own AST/fuzzy matching is built for — a preference this doc's own §4.1
detector plan and CLAUDE.md's own Context Scan mandate already assume, now with five concrete
instances behind it instead of one. Shape 6 needs its own defense, above, since none of these
five's own mitigations would have caught it — the query was never wrong.

Source tickets: `TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION` (shapes 1-3, via
`succession`'s own corrected entry), `TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-
RESOLUTION` (shapes 4-5, via `race_archetype`/`country_lifecycle`/`city`/`goal_hierarchy`; also the
original, wrongly-scoped search behind shape 6), `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-
AUDIT` (shape 5's first instance, `regional_trauma`), `TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-
CLAIMS-RESOLUTION` (shape 6, found via `commitment_betrayal`'s own re-investigation).

### 3.2 A different failure class: confident misattribution, not confident absence

§3.1's five shapes are all **search failing to find code**, producing a confident **false
negative** — "no implementation exists." This one is the inverse: **attribution finding the wrong
code and believing it**, producing a confident **false positive** — "this code is that mechanism."
It is not a sixth shape of the same failure; it is a different failure with a different mitigation,
and belongs in its own section rather than a sixth bullet in §3.1, or the catalogue's single
mitigation there ("search harder — graphify, multiple patterns, check for renames") would read as
covering a case it cannot touch. Searching better does not fix this one: the search that produced
it was not sloppy. It found real, correctly-identified orphan code that was genuinely, honestly
describable as "trauma" in plain English.

**The instance**: resolving edge #4 of `TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-
RESOLUTION`, `trauma`'s `state` was corrected `done` → `orphan` and its `implemented_by` bound to
`RecoveryReadinessService.register_near_death()` (`src/domains/emotion/recovery_service.py`) — real
code, genuinely orphaned (zero callers), genuinely about near-death psychological state. It was the
wrong mechanism. `trauma`'s real identity, discovered the same day while building this ticket's own
status-language detector: the atlas's `entity-modification#0` card, titled "Trauma: A Lasting
Physical Consequence" — the Wound→Scar physical combat-consequence system, implemented by
`WoundService` (`src/engine/rpg_depth.py`), live, with real callers in `combat.py` and
`tactical.py`. Full correction on `trauma`'s own `verified` block.

**The mitigation is a discipline, not a tool: check the entry's existing citation trail before
replacing it.** `trauma`'s own original citation
(`stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md:199`) named
`combat_resolution` as the dependency and `entity-modification#0` as the atlas card — both correct,
both sitting there unread when the replacement was made. **The registry already held the correct
answer.** The data that would have prevented the error was in the entry being overwritten, not
missing from the codebase — the strongest available argument for this registry's own citation
convention: not that citations are tidy record-keeping, but that an entry's existing evidence is
the first thing to check before replacing it, precisely because a plausible-sounding new candidate
is most dangerous when it is real code. A `code_trace` that finds real, correct, orphaned code
proves that code is real and orphaned — it proves nothing about which registry entry it belongs to,
and that question has its own evidence, already on file, every time an entry already carries one.

Source ticket: `TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION` (where the error was found and
self-corrected the same day).

### 3.3 A third failure class: a confirmation rate measures the selection as much as the system

§3.1 is the search failing to find code. §3.2 is attribution finding the wrong code and believing
it. This one is neither — the search finds the right code, the attribution is correct, and the
check still tells you less than its own pass rate implies, because **which candidates got checked
was never a neutral sample.**

**The instance**: `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` (batch 3 of the
unbound-claims program) ran a `code_trace` instrument against 20 mechanisms that already had a real
`implemented_by` binding and reported all 20 `observed` — a 100% confirmation rate, in a program
that had just corrected 7 of 47 claims in its own immediately preceding batch, and in an arc whose
other batches had found three orphans, two dead branches, and a real misattribution (§3.2 itself).
Challenged directly (peer review, same day): the 20 were not a random or adversarial sample. They
were selected *because* they already carried a real caller citation from an earlier ticket in this
epic — the check then re-confirmed that citation still resolved. **The population being checked was
pre-filtered for exactly the property being tested for.** A 100% pass rate on a population selected
for its own prior evidence of passing is close to guaranteed before any checking happens; it is not
independent confirmation, and reporting it in the same prose register as a batch that corrected real
defects (`equipment_scoring`, `chronicle`, `commitment_betrayal`) implied a rigor the check never
exercised.

**Compounding this, and only found because someone computed the number by hand under challenge**:
all 20 were verified with `instrument: code_trace` — none with `scenario` or `corpus_run`. The
registry's own runtime-verified share (what fraction of `verified` mechanisms were confirmed by the
simulation actually doing the thing, not the code merely saying it should) moved from 27% to 11% in
the same batch that raised the raw `verified` count. Neither the PR description nor the ticket's own
summary said this plainly; the number existed nowhere as a rendered figure until a peer asked "what
instrument did each of the 20 get?" and it had to be computed live
(`TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY`, the same review cycle, added
`runtime_verified_share` as a first-class rollup metric so this stops requiring a challenge to
surface).

**The mitigation is not "verify more" — the check itself was accurate, and re-running it would not
change the finding.** It is two things, neither of which is re-verification: (1) **state the
selection explicitly whenever a batch's own candidates were chosen because they already had
evidence** — "these 20 were pre-filtered for prior citation, so a high pass rate was expected before
checking" is one sentence, and its absence is what made the number read as stronger than it was; (2)
**report the instrument mix alongside the pass rate, not just the pass rate** — `code_trace` and
`scenario`/`corpus_run` are not interchangeable evidence, and a verification batch that shifts the
registry's own runtime share needs that shift visible in the same report as its headline count, not
recoverable only by hand-computing it from raw fields under direct challenge.

**A confirmation rate is not free evidence — it costs exactly as much scrutiny as picking the sample
did, and a sample selected for its own prior evidence has already spent that scrutiny before the
check runs.** This generalizes past this one batch: the next verification pass over a
pre-filtered population will produce a high rate again, for the same structural reason, and will
need the same two disclosures to be read honestly rather than as unqualified progress.

Source: peer review of `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN`, same session as
this batch's own landing, PR #229.

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
