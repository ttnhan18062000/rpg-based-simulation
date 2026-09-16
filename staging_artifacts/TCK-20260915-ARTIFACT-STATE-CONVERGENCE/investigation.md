---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260915-ARTIFACT-STATE-CONVERGENCE
artifact_type: investigation
tags: [architecture, documentation, schema]
---

# Investigation — TCK-20260915-ARTIFACT-STATE-CONVERGENCE

## Starting point

Epic's fourth and last child. Five brainstorm artifacts each hand-maintain mechanism state
independently; converge them on `docs/brainstorm/mechanisms.yaml` (built T1-T3). Per-artifact
findings below, gathered before writing any convergence code, per this epic's own standing
discipline (verify before fixing, flag before force-fitting).

## Finding 1 — camp's first real `contradicted` verdict (done, committed 398a54906)

`camp`'s registry `state: done` is correct (`CampState` is real, wired, correct code). But it has
never been observed doing anything — no compiled or procedurally-generated world seeds
`state.camps`. Initially proposed fixing this as `state: orphan`; **peer corrected**: `orphan`
asserts the code itself is defective, which is false here. The right decomposition is
`state: done` (unchanged) + `verified: {instrument: code_trace, verdict: contradicted}` — the
project's first real instance of this exact combination, which T2 explicitly left unfilled because
no real example existed at the time. Cross-referenced to
`docs/plans/world_composition_precondition_gap_finding.md`'s existing lair-trauma /
calamity-intensity pattern. This is the epic's **third** measured finding (after Foundation's 2
stale atlas badges and Priority-Derivation's 4-of-24 wiring-map drifts), and the **first where the
registry itself was wrong** rather than a downstream artifact — the concentrated-risk cost T3's own
implementation notes flagged, showing up immediately, caught by a systematic check rather than
luck.

Filed `TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT` as a separate follow-up (per peer
instruction) rather than sweeping it into this ticket: camp's own seeding read the atlas card's
badge/title and missed a caveat sitting in the card's own description — a real methodology gap in
Foundation's original 75-mechanism seed, not a one-off specific to camp. That ticket re-reads all
73 mechanism-mapped cards' full descriptions for the same class of caveat; out of scope here.

## Finding 2 — atlas card↔mechanism mapping (scope item 1)

Built `tools/mechanism_atlas_card_mapping.py`, reusing Foundation's own investigation.md citation
table (grep-extracted, not re-derived from scratch) rather than trusting a fresh hand
transcription. Cross-verified programmatically against the real atlas JSON before trusting it: 73
of the registry's 75 mechanism ids map to exactly one atlas card-badge position each (`nest`/`lair`
have no atlas card — sourced from the wiring map only, per Foundation's own investigation); zero
mismatches against Foundation's citations; zero duplicate card-key assignments. Two structural
exceptions, both hand-verified against the real card JSON:
- **Split cards** (2): one card carries 2 badges for 2 genuinely distinct mechanisms
  (`entity-profile#6` → `aging_death`/`succession`; `entity-profile#10` → `xp_leveling`/
  `breakthrough_bonuses`).
- **Partial-coverage card** (1): `entity-cognition#11` has 3 badges for 3 tiers, but only badge
  index 1 (`knowledge_model`) is a distinct registry mechanism — the other two tiers are the *same*
  mechanisms as `goal_hierarchy`/`causal_spatial_memory`, cited from their own separate cards.

This mapping is what `mechanism_atlas_regenerate.py` (to build) will drive off of, mirroring T3's
`mechanism_wiring_map_classdef.py`'s own regenerate-and-drift-check pattern.

**State → badge-cls mapping needed**: the atlas already uses the registry's own 6-class vocabulary
directly as badge classes (`done`/`partial`/`gap`/`orphan`/`gated`/`skeleton` — confirmed by the
ticket's own measured table in its Request Summary), so atlas convergence is the simplest of the
five — no plain-language or architecture-pattern translation layer needed, just
`badge.cls = registry.state` per mapped card, with the split/partial exceptions applied via the
mapping table above.

## Finding 3 — taxonomy is NOT the same domain as the registry (scope item 2)

`simulation_design_taxonomy.html`'s 108 cards classify **generic simulation-engine architecture
patterns** (Agent-Based Modeling, Cellular Automata, Behavior Trees, GOAP, Utility AI, State
Synchronization, Snapshot Interpolation, Event Sourcing, LOD tiers, Replicated State Machine, etc.)
against a 6-value vocabulary (`implemented`/`partial`/`na`/`candidate`/`planned`/`unconfirmed`) that
shares only the word "partial" with the registry's own 6 states. Checked directly, not assumed: the
document's own prose was grepped for every one of the registry's 13 currently `orphan`/`gated`
mechanism ids and their natural-language names (`succession`, `genetics_aptitude`, `self_model`,
`declared_cognition_schema`, `emotion`, `information_trust_deception`, `knowledge_model`,
`causal_spatial_memory`, `committed_intentions`, `cross_episode_social_consequences`,
`demographic_cohort_cycle`, `opportunity_rumor_seeds`) — **zero matches**. The word "mechanism"
does appear repeatedly in the taxonomy's own prose, but always in the generic software-engineering
sense ("a genuine per-entity fidelity mechanism", "checkpoint/resume mechanism"), never referring
to a registry mechanism id.

This is the same shape as the scorecard's own already-settled "different axis, stays independent"
disposition (scope item 5) — the taxonomy answers "which known engine-architecture patterns do we
implement," the registry answers "which gameplay mechanisms exist and work." AC #3's own softened
wording ("at least the known instances show as such") reads like it anticipated a partial mapping
might exist; a real check found none to anchor even a partial one on.

**Flagged to peer before implementing** (per standing discipline — never force-fit a mapping where
none exists). **Peer confirmed and independently re-verified** — re-counted the taxonomy directly
rather than trusting this session's count alone, found 108 cards / 6 values with `na` (47, the
largest bucket) never having been checked for in the original scoping pass, and confirmed the card
titles (*Deterministic Simulation*, *Lamport Clocks*, *CRDT-Based State Convergence*) as
architecture-pattern names, not mechanisms. Peer also traced this to a **specific prior error of
peer's own**: `docs/plans/mechanism_registry_initiative.md`'s own Finding 1 had originally scoped
this epic on the false "five artifacts, 50 taxonomy rows, only Implemented/Partial" claim — reached
by grepping for guessed vocabulary words rather than reading the file, the same shape of error as
Foundation's own badge-not-description seeding mistake. **Corrected as part of this ticket** (not
folded into a separate one — this is squarely T4's own artifact-inventory scope):
`docs/plans/mechanism_registry_initiative.md` Finding 1 and Gap 2, and
`tickets/todos/mechanism-registry/TCK-20260915-EPIC-MECHANISM-REGISTRY.md`'s Request Summary/Scope/
Related Code Areas, all rewritten to the correct 3-mechanism-domain + 2-different-axis framing, with
the correction's own cause recorded in place rather than silently rewritten over.

**Disposition: scope item 2 gets item 5's disposition** — assessed, stays independent, no vocabulary
transplant. AC #3 is satisfied by recording that a real mapping was sought and found not to exist,
not by leaving it silently unaddressed.

This is the epic's **fourth** measured drift finding (after Foundation's 2 stale atlas badges,
Priority-Derivation's 4-of-24 wiring-map drifts, and this same ticket's own `camp` registry-seeding
error above) — and the first one found **inside the epic's own scoping document**, the thing that
justified starting the epic at all. Worth recording plainly, per peer's own instruction: two stale
badges, one wiring-map drift set, one registry seeding error, and now one wrong claim in the plan
doc — every layer of this epic has produced at least one real, measured error, including the
layer that set the epic's own scope. That is evidence the pattern is structural (each layer trusts
the layer below it without an independent check, until this arc's own discipline of re-verifying
directly catches it) rather than about any one pass being careless.

## Finding 4 — capabilities tier needs (state, verified), not state alone (scope item 3)

`simulation_capabilities.html` has a real `<script type="application/json" id="sections-data">`
block (99 cards across 13 sections), with a clean 3-value machine `tier` enum (`live`/`built`/
`planned`) plus a hand-authored, editorial `tierLabel` string per card (e.g. "Built, but never
actually triggers", "Live, but not yet varied") — closer in shape to the registry's own `verified`
axis than to `state` alone.

Found camp's own capabilities card ("Goblin & Orc Camps", `monsters` section) is currently
`tier: planned`, `tierLabel: "Built, but confirmed not working"` — **self-contradictory on its own
terms**: every other `planned`-tier card's label says some form of "not yet built" (confirmed
across all 25 `planned` cards' distinct labels: "Mostly not yet built", "Confirmed not built", "Not
yet built", "Built, but confirmed not working" — the last one is the outlier, admitting "built" in
the same breath as a tier whose own sibling cards all deny it). This is a real, pre-existing data
bug in the capabilities page, independent of the registry — found by the same systematic
cross-check discipline that found Foundation's 2 stale badges and Priority-Derivation's 4
wiring-map drifts.

Checked whether a naive `state`-only mapping (`registry.state == "done" → tier: "live"`) would get
this right: **no** — `camp`'s `state` is `done`, so a state-only mapping would produce `tier: live`,
which is also wrong (camp has never been observed doing anything; "live" overclaims exactly as much
as the current buggy "planned" underclaims). Only `(state: done, verified.verdict: contradicted)`
together produces the correct answer: `tier: built` ("Built, but never actually triggers" — nearly
identical wording already exists on a different card, "Paying for Information", for an unrelated
mechanism in the same shape).

**Flagged to peer before implementing**: the declared mapping (AC #4, "declared in one place") must
be a function of `(state, verified)`, not `state` alone. **Peer accepted as stated**, both directions
of the camp evidence (self-contradictory `planned` label, and a state-only mapping's wrong `live`)
cited as sufficient proof, plus one tightening: **`partial -> live` is the weakest link** — partial
means partly working, `live` asserts players experience it, so make the per-card override
*explicit and reason-recorded specifically for `partial`*, not a general escape hatch that lets
judgement quietly accumulate undocumented elsewhere in the table too.
```
done + verified.verdict != contradicted  -> live
done + verified.verdict == contradicted  -> built
orphan | gated | skeleton                -> built
partial                                  -> live, UNLESS a per-mechanism override is declared with
                                             a recorded reason (required table, not an ad hoc
                                             escape hatch — see plan.md Step 2.3)
gap                                      -> planned
```
Capabilities' own card↔mechanism mapping (99 cards vs. the registry's 75 mechanisms — a different
multiplicity than the atlas's 73-cards-for-73-mechanisms) is separate follow-up work regardless of
the mapping function; accounted for as its own plan.md step.

## Finding 5 — wiring map (scope item 4): already converged, reconfirmed

Peer's own read (T3 already did this work) reconfirmed directly, not assumed:
```
.venv313/bin/python3 tools/mechanism_wiring_map_classdef.py --check
→ OK: Entity Operating Loop diagram's classDef assignments match the registry.
```
No further work needed for this scope item beyond leaving the existing T3-built drift-check target
(`make mechanism-wiring-map-classdef-check`) as the standing verification, which it already is.

## Finding 6 — scorecard (scope item 5): confirmed independent

`design_merit_scorecard.html` scores **design ideas** (1-65, referenced by idea number, not
mechanism id) on 7 axes (Direction Fit, Narrative Generativity, Groundedness, Pillar Reach,
Efficiency, Risk-Adjusted Cost, Leverage) — explicitly stated in its own thesis text as "Not a
replacement for Simulation Quality (SimQ)... measures the *design*, from the documents alone."
Confirms the ticket's own Assumption #3 exactly. No mechanism `state` field exists anywhere in this
document to converge. **Conclusion: stays independent — different axis (design merit vs.
implementation state), different keying (idea number vs. mechanism id).** Recorded here as AC #5
requires ("with its reasoning"), no code changes needed for this scope item.

## Cross-cutting: the "four distinct axes" framing still applies, now at five artifacts

Restating T3's own recorded generalization (`priority()` implementation notes) at the artifact
level, now with two more real instances backing it: not every "state-shaped" surface in this
project is actually the registry's own axis. The taxonomy (engine-architecture-pattern coverage)
and the scorecard (design-idea merit) are both real, useful, *independently* correct axes that
happen to render as badges/tiers, same as the atlas/capabilities/wiring-map do — but only 3 of the
5 artifacts are actually keyed on mechanism id at all. Converging the other 2 would not be fixing a
duplicate; it would be deleting information that has no registry-side equivalent to fall back on.
