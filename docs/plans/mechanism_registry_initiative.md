---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, documentation, schema]
---

# Plan — Mechanism Registry

**Status, scoped 2026-09-15.** Proposes a single generated source of truth for *which simulation
mechanisms exist, what they depend on, and whether anyone has ever observed them working* — so that
"what is wrong", "what should we harden", "what is the priority", and "how do we know" can be
answered from data rather than from whichever artifact was opened first.

This plan covers four gaps raised together. One dissolves into another, so the deliverable is **one
registry and four tickets**, not four parallel features.

---

## 1. Why this exists

The RPG brainstorm corpus is unusually good at recording *findings*. It is structurally unable to
answer *aggregate* questions, for one reason: **there is no place where a mechanism's state is
written once.**

### Finding 1 — three artifacts independently record mechanism state; two record something else

**Corrected 2026-09-16 by `TCK-20260915-ARTIFACT-STATE-CONVERGENCE`** — the original version of this
finding claimed all five artifacts below record mechanism state and disagree about it. That claim
was wrong for two of the five, and wrong in a specific, instructive way: it was reached by grepping
`simulation_design_taxonomy.html` for a handful of *guessed* vocabulary words (`Implemented`,
`Partial`) and reporting the absence of those guesses as absence of vocabulary, without ever
checking what the file's dominant value actually was or what its 108 cards' titles named. A direct
re-count found 108 cards across **six** values (`na` 47 — the largest, never checked for —
`implemented` 35, `partial` 15, `unconfirmed` 6, `candidate` 4, `planned` 1), and the titles
(*Deterministic Simulation*, *Lamport Clocks*, *CRDT-Based State Convergence*, *Discrete-Event
Simulation*) are generic simulation-engine architecture patterns, not gameplay mechanisms — a
zero-overlap check against every mechanism id currently `orphan`/`gated` in the registry confirmed
none of them appear anywhere in the taxonomy's text. This is the same methodology error as
Foundation's own original mechanism seeding (reading a card's badge/title and missing a caveat
sitting in its description) — a structural pattern across this epic's own scoping and seeding work,
not a one-off. See `TCK-20260915-ARTIFACT-STATE-CONVERGENCE`'s investigation.md for the full
re-derivation.

Measured against `origin/main`, 2026-09-15 (mechanism-domain artifacts only — see below for why
taxonomy and scorecard are excluded):

| Artifact | State vocabulary | Volume |
|---|---|---|
| `rpg_feature_atlas.html` | badge `cls` — `gap` 58, `done` 43, `partial` 25, `orphan` 12, `gated` 7, `skeleton` 2 | 139 cards |
| `simulation_capabilities.html` | 3-tier plain language | 77 cards |
| `rpg_simulation_wiring_map.html` | mermaid `classDef live` / `classDef bug` | 3 flowcharts, 28 edges |

Three hand-maintained mechanism-state surfaces, no shared source. They already disagree: the atlas
carries `orphan` and `gated` — the built-but-never-runs distinction this arc spent weeks
establishing — while the wiring map and capabilities page each derive their own colouring/tier by
hand, independently.

Two further artifacts carry their own, genuinely different, independently-correct axes and are
**not** part of this convergence:

| Artifact | What it actually tracks | Volume |
|---|---|---|
| `simulation_design_taxonomy.html` | which known simulation-engine architecture patterns are implemented (a software-architecture catalogue, not a mechanism catalogue) | 108 cards, 6 values |
| `design_merit_scorecard.html` | design-idea merit (Groundedness / Efficiency / Leverage, etc.), keyed by idea number 1–65, not mechanism id | ideas 1–65 |

### Finding 2 — the corpus is keyed by *idea*, and this needs to be keyed by *mechanism*

`docs/brainstorm/idea_index.json` already exists, is **generated** by
`tools/generate_brainstorm_idea_index.py` via `make brainstorm-idea-index`, and cross-indexes five
documents by idea number. The pattern this plan needs is therefore already established in-repo and
should be followed, not reinvented.

But its key is the **design idea** (68 numbered proposals — *things we might build*). What the four
gaps need is keyed by **mechanism** (*things that exist and may or may not work*). Different node
sets: `combat` is a mechanism with no originating idea; many ideas map to no mechanism yet. A
verification status is only meaningful on a mechanism.

So: a sibling generated file, same pattern, different key — not an extension of `idea_index.json`.

### Finding 3 — the chart half of the priority tree is ~70% pre-built

`rpg_simulation_wiring_map.html` already contains three mermaid flowcharts with subgraph **lanes**
(`L1 INDIVIDUAL` → `L4 WORLD`), labelled edges, and a state vocabulary baked into the diagram
(`classDef live` / `classDef bug`). Hand-authored.

Two consequences. The rendering approach is already validated in this repo, so the priority chart is
a *generation* problem, not a design problem. And those `classDef` assignments are a fifth place
state is written by hand — Finding 1's problem, sitting inside the artifact that would otherwise be
the fix.

The existing lanes are **containment** (Individual / Organization / Geography / World). The priority
tree needs **frequency** lanes and **dependency** edges. Containment is not dependency: a Faction
*contains* Entities, whereas war *depends on* combat. Only the latter drives priority.

### Finding 4 — two hypotheses tested and rejected, so do not build for them

- **Evidence decay.** All 19 distinct `src/`/`tests/` paths cited in the atlas resolve on
  `origin/main`. File-level citation rot is not a real problem here. **Do not build a link checker.**
  (Function- and constant-level claims — "zero callers", "flat 5.0" — are not covered by that check
  and remain unverified; that is what the verification axis is for, not a path validator.)
- **Census as a frequency source.** The execution census measures **branch coverage — binary**. It
  reports whether a branch was ever taken, never how often, so it cannot supply frequency. It is also
  not on `main` yet: `tools/execution_census.py` lives in unmerged PR #205, only the initiative doc is
  on `main`.

### Finding 5 — the dependency graph is hand-authored; graphify validates it

`graphify-out/` holds 35,290 nodes and 101,042 edges at code granularity. That will not cluster
reliably into a 30–50 node mechanism DAG. Hand-author the edges — 30–50 nodes is human-scale — and
use graphify as a **validator**: a declared `depends_on` edge with no supporting call/import path is
flagged as suspicious, never auto-generated.

---

## 2. The four gaps, and what each becomes

### Gap 1 — priority has no home

Nothing in any artifact carries the stated priority rule (lower layers first, ranked by execution
frequency and dependency-by-other-count). Every batch ordering so far was reconstructed from session
context and did not survive the session.

**Becomes:** the registry's `layers` + `depends_on`, with priority *derived*. → **T1, T3**

**Frequency is a property of the layer, not of each mechanism.** Entities act every tick; factions on
a slow cadence; world calamities rarely. ~5 values assigned once, rather than an argument per
feature — which also sidesteps Finding 4's dead end entirely.

### Gap 2 — state is prose, not data

147 badge instances, roughly 100 distinct texts.

The important observation is *what the bespoke texts say*: `"Built correctly, OFF by default"`,
`"Proven mechanic, narrow trigger"`, `"Succession never triggers"`. **None are build-status
statements.** They are verification and behaviour statements crammed into a build-status badge,
because there is nowhere else to put them.

**Becomes:** nothing. This gap gets **no ticket of its own** — it dissolves once Gap 4 exists,
because the overloaded prose migrates into `(state, verified)` pairs. What remains is genuine
per-card colour, which should stay prose.

**Explicitly rejected:** adding more badge classes. Six is enough. Expanding a status vocabulary to
carry meaning belonging in a different field is exactly the failure mode the 147 overloaded badge
texts above already show inside this domain — no need to reach for the taxonomy as an example of it,
and doing so was itself Finding 1's own correction: the taxonomy's vocabulary problem, on inspection,
turned out to belong to a different domain (engine architecture patterns) entirely, not evidence of
mechanism-status vocabulary creep.

### Gap 3 — the artifacts disagree

**Becomes:** artifacts render state from the registry. → **T4**

**Scope limit: share the *state*, not the *prose*.** The capabilities page is deliberately non-dev
plain language; the taxonomy carries design verdicts; the atlas carries per-feature detail. Merging
their prose would destroy what makes each useful. Only `state` and `verified` converge.

### Gap 4 — no verification axis

Every status in every artifact answers *is it built?* Nothing answers *has it been observed working,
by what instrument, when?*

That distinction is the arc's central finding and its most expensive miss: combat judgement was
correctly marked implemented and was write-only across four test conditions.

**Becomes:** a `verified` block per mechanism. → **T2**

Two load-bearing constraints:

- **One row per mechanism, never per test.** The scenario component emits one verdict per mechanism —
  dozens of rows, not thousands. Latest verdict only; history lives in git.
- **A mechanism with no verification renders as `unverified`, never absent.** If unverified
  mechanisms simply do not appear, the artifact reproduces the exact failure this arc was about: a
  real state showing up as silence. The default must be visible.

---

## 3. Shape

Two blocks. Layers carry frequency; mechanisms carry dependency and verification.

```yaml
layers:
  entity:  { cadence: per_tick, rank: 1 }
  group:   { cadence: per_tick, rank: 2 }
  faction: { cadence: daily,    rank: 3 }
  region:  { cadence: slow,     rank: 4 }
  world:   { cadence: rare,     rank: 5 }

mechanisms:
  - id: combat_judgement
    layer: entity
    depends_on: [combat, perception]
    state: done
    verified:
      instrument: scenario
      verdict: observed
      date: 2026-09-15
      note: >-
        Differential confirmed at scenario scale: posture risk-rejected -> 0 attacks,
        no posture -> attack proceeds, all else identical
        (tests/mechanic_scenarios/test_combat_judgement_withdrawal.py).
        Same comparison at corpus scale gave 1960 -> 837.
  - id: war
    layer: faction
    depends_on: [faction_sentiment, military_strength]
    state: gap
    verified: null    # renders as "unverified", never hidden
```

Three invariants that keep it from rotting:

1. **`depends_on` is the only hand-authored edge.** Dependent-count is *computed by traversal, never
   stored*. Store both and they disagree within a month — and the stored one is the one people read.
2. **Frequency lives on the layer, never on the mechanism.**
3. **Validated on commit:** every `depends_on` id resolves, the graph is acyclic, every `layer` is
   declared, every `state` is one of the six classes. Without this a `depends_on` pointing at a
   renamed mechanism fails silently — precisely the pattern this arc kept finding.

### Chart generation

`flowchart BT` puts foundations at the bottom, so reading upward *is* build order — the bottom-up
rule becomes the shape of the picture rather than a note beside it. Lanes are the frequency tiers.

**Never render the whole graph.** Mermaid stops being readable near 40 nodes. Charts are generated
*per view*: one layer, the ancestors of one mechanism ("what does war actually need?"), or the top N
by dependents. The registry is complete; charts are slices. A single all-mechanisms diagram would be
technically correct and unreadable, which is how most architecture diagrams die.

> **Addendum, 2026-09-20** (`TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`,
> per direct peer review): "the registry is complete" above is about chart slicing, not about
> coverage of the real codebase — worth flagging explicitly since it reads as a stronger claim than
> that in isolation. The registry's own completeness check
> (`tools/mechanism_registry/mechanism_registry_completeness_check.py`) covers `src/domains/` and
> `src/systems/` only; other source trees (`src/world/`, `src/engine/`, `src/cognition/`, and
> roughly a dozen more) have not yet been swept, and a manual sizing pass found real, wired,
> unregistered code there (`src/world/perception/gate.py::PerceptionGate` was the first instance,
> not the only one — see `docs/plans/mechanism_claims_as_tests_initiative.md` §3.4 for the full
> finding and `TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP` for the tracked follow-up). "93
> mechanisms" is a real count of what has been catalogued, not yet a claim about everything that
> exists.

---

## 4. Open questions for implementation

1. Does `flowchart BT` lay subgraphs out as clean lanes? Direction and subgraphs sometimes fight in
   mermaid. The wiring map uses `TB`/`TD`/`LR` — check whether `BT` was avoided for a reason.
2. How are the existing mermaid blocks rendered — client-side script, or committed images? Determines
   whether generated charts inject the same way.
3. What is the real mechanism count once seeded? The 30–50 estimate is unverified. If it lands near
   100, the per-view slicing rule matters more, not less.
4. Do the atlas's 139 cards map cleanly onto mechanism ids, or is the relation many-to-one with a
   remainder belonging to no mechanism?

---

## 5. What this plan deliberately does not do

- **No link checker** (Finding 4).
- **No new badge classes** (Gap 2).
- **No prose merging across artifacts** (Gap 3).
- **No auto-derived dependency edges** (Finding 5).
- **No blocking on the census.** T1–T4 stand alone; the census adds an exercised/never-exercised flag
  when PR #205 lands. Nothing here waits on it.

## Related

- `docs/plans/simulation_execution_census_initiative.md` — the branch-coverage instrument
- `docs/plans/mechanic_verification_scenarios_proposal.md` — per-mechanism scenario verdicts, the
  primary producer for the verification axis
- `docs/plans/world_composition_precondition_gap_finding.md` — the scenario-does-not-arise pattern
- `tickets/done/TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX.md` — the generated-index precedent
