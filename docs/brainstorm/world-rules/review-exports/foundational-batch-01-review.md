---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Foundational Batch 01 (Identity, State Ownership, Causality)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the
fix for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Batch scope

Three foundational law families — Identity, State Ownership, Causality — the load-bearing layer
every later per-domain batch (Space, Life/Body, Economy, etc.) will build on. Not a per-domain
batch; deliberately domain-agnostic. Originally drafted with 12 seed scenarios; expanded once with
9 adversarial probe scenarios (FND-S13–S21) before being treated as ready for high-level external
review, per `tmp/world-catalog-expand-scenario-and-review-layer-ext-ai.md`. Most recently, this
batch's own open semantic questions and owner-attention decisions were explicitly dispositioned
(deferred / cross-domain-link / implementation-gap / resolved-by-naming-a-family), and a fourth
foundational family — **History / Provenance** — was introduced at scope level only (not drafted,
not part of Batch 01's own rule count).

## Canonical files included

- `foundations/identity.md` (ID-01–09)
- `foundations/state-ownership.md` (OWN-01–06)
- `foundations/causality.md` (CAUSE-01–07)
- `foundations/history-provenance.md` (scope only — no numbered rules yet; not part of Batch 01's
  own rule set, included here because CAUSE-05/CAUSE-06 now forward-reference it)
- `scenarios/foundational-batch-01.md` (FND-S01–S21)

## Rule Inventory

One row per Rule — semantic territory only. Full preconditions, ownership analysis, repository
evidence, and rationale stay in the canonical files linked above.

### Identity (`foundations/identity.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| ID-01 | Persistent Identity | A first-class subject retains its identity across ordinary state changes. | Accepted |
| ID-02 | Identity ≠ Classification | Identity is distinct from kind, type, role, faction, or current form. | Accepted |
| ID-03 | Transformation Preserves Continuity (default) | A transformation preserves identity unless a domain rule explicitly says otherwise. | Accepted, refined |
| ID-04 | Creation Establishes Identity | A newly created subject begins a distinct identity and may carry provenance. | Accepted |
| ID-05 | Destruction Doesn't Erase History | Termination ends active state, not historical meaning. | Accepted |
| ID-06 | Split/Merge/Succession Need Explicit Semantics | Splits, merges, and successions must not silently assume identity behavior. | Accepted (unresolved dependency) |
| ID-07 | Aggregate Membership ≠ Individual Identity | Participating in an aggregate does not erase individual identity. | Accepted |
| ID-08 | Identity Applies Uniformly Across Scale | The Identity family applies to any first-class subject at any scale, not only entities. | Accepted (added locally) |
| ID-09 | Name/Epithet ≠ Identity | A name, title, or epithet may change without changing identity. | Accepted (added locally) |

### State Ownership (`foundations/state-ownership.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| OWN-01 | One Authoritative Source of Truth | Every durable state concept has exactly one unambiguous canonical owner. | Accepted |
| OWN-02 | Participation ≠ Ownership | Reading, reacting to, or causing a change doesn't make a domain the owner. | Accepted |
| OWN-03 | Derived Views ≠ Duplicate Truth | Derived views, classifications, or scores don't become additional owners. | Accepted, refined |
| OWN-04 | Proposed Change ≠ Committed State | An intent or proposal isn't authoritative world state until accepted. | Accepted |
| OWN-05 | Cross-Domain Transitions Preserve Ownership | A causal chain may cross owners without collapsing them into one domain. | Accepted |
| OWN-06 | Historical Reference ≠ Present Ownership | History or belief referencing state doesn't make the reference authoritative. | Accepted |

### Causality (`foundations/causality.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| CAUSE-01 | Real Causal Path Required | A durable consequence should trace to a real producer, not a narrative label. | Accepted |
| CAUSE-02 | Cross-Domain Causal Chains | A cause in one domain may produce a consequence in another and continue downstream. | Accepted |
| CAUSE-03 | Correlation ≠ Causal Connectivity | Statistical or temporal association alone is not a causal claim. | Accepted |
| CAUSE-04 | Preconditions Must Be Real, Not Narrative | A claimed precondition must be checked against real state. | Accepted (major gap noted) |
| CAUSE-05 | Causal History Traceable Within Declared Reach | History must be reconstructable within whatever reach a system declares. | Accepted |
| CAUSE-06 | Compression Must Not Fabricate Causal Links | Summarization may drop detail but must not invent a causal relation; a fact's significance may legitimately fade without that being erasure or fabrication. | Accepted, partial-move, refined |
| CAUSE-07 | World Outcomes Carry No Inherent Polarity | Outcomes aren't inherently good or bad; only the causal validity producing them is evaluated. | Accepted |

### History / Provenance (`foundations/history-provenance.md`) — scope only, not part of Batch 01's rule count

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| — | (none drafted) | Persistence within a declared reach, provenance, compression, and significance-fading semantics — CAUSE-05/CAUSE-06's persistence-specific substance is anticipated to migrate here once drafted. | Scope defined 2026-09-21; no numbered rules yet |

## Scenario Inventory

One row per scenario, including all eight counter-scenarios (marked **counter**). Full traces stay
in `scenarios/foundational-batch-01.md`.

| Scenario ID | Short name | Trajectory (initial → consequence) | Rule families challenged | Deferred domain dependencies | Result |
|---|---|---|---|---|---|
| FND-S01 | The Dead Don't Fight Back | defeated → corpse looted → "cannot resist" assumed | Causality, Identity | Objects, Agency/decision | Partial |
| FND-S02 | Ingots Become a Sword (counter) | ore → smelted → forged sword | Identity | Objects & material culture | Covered |
| FND-S03 | Camp, Settlement, Ruin | camp → settlement → ruin | Identity | Places & territory | Blocked |
| FND-S04 | The Chronicle Remembers What the World Doesn't | event → chronicled in Campaign mode → lower fidelity outside it | State Ownership, Causality | History/significance | Partial |
| FND-S05 | Feared and Hated Are Not the Same Field (counter) | reputation drops ↔ separately labeled "oathbreaker" | State Ownership | Social relations & identity | Finding |
| FND-S06 | A Famine Doesn't Rewrite Every Name (counter) | regional famine → aggregate shift → (org/clan founding sub-probe) | Identity | Organizations, Places | Core covered; sub-probe finding |
| FND-S07 | A Wound Becomes a Debt | combat → injury → capability loss → economic loss → relationship reaction | State Ownership | Economy, Social relations, Capability | Partial |
| FND-S08 | Two Systems, One Field | hypothetical dual write on `readiness` | State Ownership | none | Covered |
| FND-S09 | A Rumor That Never Became True (counter) | rumor spreads → believed → betrayal never occurs | State Ownership | Perception/knowledge/information | Covered |
| FND-S10 | Drought to Ruin | drought → scarcity → migration → abandoned settlement → ecological takeover | Causality | Ecology, Places | Partial |
| FND-S11 | Two Omens, No Connection (counter) | shop burns ↔ rival opens stall, same week | Causality | none | Covered |
| FND-S12 | A Kingdom Falls, and That's Not the Point | region's authority collapses over a long run | Causality | Politics/authority & war | Covered |
| FND-S13 | Growing into a New Form | creature → repeated exposure → capability/form change | Identity | Capability & progression | Covered |
| FND-S14 | Something Wears a Human Shape | human → supernatural transformation → vampire-like being | Identity | Magic, Life/body | Covered (boundary check) |
| FND-S15 | Death, Then Succession | ruler dies → succession eligible → heir acquires role/authority → (property untransferred) | State Ownership | Life/body, Family/lineage, Politics, Objects | Partial |
| FND-S16 | The Heir Is Not the Ruler (counter) | successor acquires role/authority ≠ predecessor's own identity | Identity, State Ownership | Family/lineage, Politics | Covered |
| FND-S17 | One Organization, Two Successors | organization → internal division → two successor organizations | Identity | Organizations & institutions | Blocked/deferred |
| FND-S18 | A Lie That Moves an Army | false claim → believed → acted on → real consequence | Causality, State Ownership | Perception/knowledge, Agency/decision, Economy | Partial |
| FND-S19 | A Rumor That Went Nowhere (counter) | belief held → decays/goes stale → triggers nothing | Causality | Perception/knowledge/information | Covered |
| FND-S20 | The King Is Dead, the Feud Is Not | entity dies → participation ends → others react → later changes | Identity, State Ownership, Causality | Family/lineage, Politics, History/significance | Covered |
| FND-S21 | A Name the World Forgets (counter) | dead entity's relevance → should be able to fade over time | Causality | History/significance (future family) | Finding (new) |

## Scenario Coverage Summary

What the batch, as expanded, actually stress-tests — coverage shape, not scenario count.

**Identity continuity**
- ordinary state change — FND-S01
- qualitative transformation — FND-S02, FND-S13
- identity-ending transformation boundary — FND-S14
- death — FND-S15, FND-S16, FND-S20
- split / merge / succession — FND-S06, FND-S15, FND-S16, FND-S17
- aggregate vs. individual — FND-S06, FND-S11
- naming / epithet — FND-S01

**State ownership**
- direct ownership — FND-S08
- derived state — FND-S05
- proposal vs. committed state — FND-S09, FND-S18
- cross-domain consequences — FND-S07, FND-S15
- historical reference — FND-S04, FND-S20
- succession / transfer chains — FND-S15, FND-S16

**Causality**
- direct cause — FND-S01
- cross-domain chains — FND-S10
- false belief as real cause — FND-S18, FND-S19
- correlation without causation — FND-S11
- compressed / fading history — FND-S20, FND-S21
- outcome neutrality — FND-S12

## Deferred Scenario Semantics

An unresolved later-domain question is not the same thing as an incomplete foundational rule.
These are intentionally left to future domain batches, not hidden gaps:

- `human → supernatural transformation` → Magic & supernatural, Life/body/survival (FND-S14)
- Organization split semantics → Organizations & institutions (FND-S06, FND-S17)
- Succession law — office and especially property/wealth transfer → Family/lineage & succession,
  Politics/authority & war, Objects & material culture (FND-S15, FND-S16)
- Corpse identity as a future Objects-domain subject → Objects & material culture (FND-S01,
  and `identity.md`'s own ID-05 open question)
- Belief acquisition and distortion → Perception/knowledge/information (FND-S09, FND-S18, FND-S19)
- Settlement lifecycle (camp → settlement → ruin) → Places, settlements & territory (FND-S03,
  FND-S10, FND-S17's same-shaped gap)
- Historical-significance fading mechanism → a future History/Provenance family, not yet named in
  the world-rule design order (FND-S21)

## Design intent

Establish, before any per-domain rule is written, what "the same thing across change" means
(Identity), who is allowed to hold durable truth about a concept and how that truth relates to
proposals, derived views, and history (State Ownership), and what makes one event a real cause of
another rather than a coincidence or fabricated narrative link (Causality). These three answer
questions every later domain would otherwise have to re-derive independently and inconsistently.

## Rules/law families introduced or materially changed

All three families are newly introduced (first draft, no prior version exists). 20 external
starter candidates were reviewed; 2 rules were added locally (ID-08, ID-09). After the adversarial
scenario expansion, exactly one further refinement was made: CAUSE-06 gained one sentence
distinguishing legitimately fading historical significance from erasure/fabrication (FND-S21) — no
other rule changed as a result of the expansion. No rule from a prior batch was changed, since
this is the first batch.

**Most recently (2026-09-21):** a fourth family, **History / Provenance**, was introduced at
scope level only — no numbered rules, no rule count added to this batch. It is not a new batch
and implies no change to the world-rule design order (`simulation-rule-world-law-design-
preparation.md` §3.1's item 19 keeps its position; §3.2's already-anticipated `Persistence` and
`Provenance` entries are what this family now names explicitly). Identity, State Ownership, and
Causality's own accepted rules were not reopened by this — CAUSE-05/CAUSE-06 gained
forward-reference notes pointing to the new family, not semantic changes.

## Major scenario findings

Of 21 scenarios (12 seed + 9 adversarial expansion), including 8 counter-scenarios: 10 covered
outright, 7 partially covered (real design gaps, not contradictions), 2 blocked/deferred (no
mechanism exists at all — FND-S03, FND-S17, both the same settlement/organization-lifecycle
gap-shape), 2 revealed a finding rather than a contradiction (FND-S05, and FND-S21's newly-named
significance-fading gap). **Zero scenarios, across both passes, revealed a genuine semantic
contradiction between two accepted rules.**

The adversarial expansion's own headline result: the original 20-candidate acceptance survives
stronger pressure. Every new scenario either reconfirmed an existing rule's disposition
(ID-01/02/03/05/06, OWN-01/02/04/05/06, CAUSE-01/03/05/06) or surfaced a repository-completeness
gap already consistent with the batch's existing pattern (unbuilt downstream consequences, not
architectural contradictions) — with one exception: FND-S21 surfaced a genuinely new semantic gap
(no mechanism lets historical significance legitimately fade), which prompted CAUSE-06's one-
sentence refinement rather than a new rule.

The single most load-bearing gap found across both passes remains: **no general-purpose
capability/precondition detector exists anywhere in the repository** (CAUSE-04) — every future
domain that gates an action on a precondition inherits this gap until it's addressed.

## Important cross-domain links

- `impaired capability → economic loss → relationship reaction` (OWN-05, FND-S07): a cross-domain
  semantic link question, not an ownership problem — resolve once Capability/progression and
  Economy/resources rules actually exist.
- Settlement lifecycle (camp → settlement → ruin): surfaced independently by Identity (ID-03) and
  Causality (CAUSE-02), then a third time by Organizations (ID-06, FND-S17's same-shaped gap) —
  DEFERRED to future Places and Organizations batches respectively.
- Organization/clan founding and splitting: no mechanism exists at all (ID-04, ID-06) — DEFERRED
  to a future Organizations/Politics batch.
- Reputation scalar vs. reputation labels: two legitimately separate owned fields with an
  undocumented narrative relationship (OWN-03, FND-S05) — flagged for a future Social relations
  batch (unchanged by this disposition pass).
- Capability/precondition detector (CAUSE-04): treated as an implementation/repository gap, not a
  world-rule design-order question — does not argue for reordering the design order, only for
  building the detector once, generally, whenever it's built.
- Succession property/wealth transfer: role/authority succession is real, but nothing transfers
  objects or wealth to an heir (OWN-05, FND-S15) — DEFERRED across Family/lineage, Politics, and
  Objects/Economy jointly; canonical state ownership stays separate across all three.
- Compression-tier design and significance-fading design for history/chronicle (CAUSE-06):
  RESOLVED by naming the family — see `foundations/history-provenance.md` (scope only, not fully
  designed).

## Open semantic questions

All six carry an explicit disposition as of 2026-09-21 — none are bare open questions anymore.

1. **DEFER, no universal test invented.** What, in general (not per-domain), makes a
   transformation identity-ending? (ID-03) — `human → vampire` and `camp → settlement → ruin`
   both deliberately stay open, deferred to Magic and Places respectively; ID-03's own
   default+exception shape is unchanged. The adversarial expansion (FND-S14) confirmed this
   deferral is sound rather than resolving it, and this disposition closes it as a question for
   this batch — it should not be reopened without a domain actually needing the answer.
2. **DEFER to Organizations / Places.** How do split/merge/founding resolve for organizations and
   settlements? (ID-06) — reconfirmed a third time by FND-S17.
3. **DEFER to Objects & Material Culture.** Is a corpse's own identity (as a future
   Objects-domain subject) related to the deceased entity's identity, or fully independent?
   (ID-05)
4. **Cross-domain semantic link question, not an ownership problem.** Where does "impaired
   capability → economic loss" get designed? (OWN-05) — resolve once Capability/progression and
   Economy/resources rules exist; OWN-05 already establishes that crossing owners is legitimate.
5. **DEFER across Family/Lineage, Politics, Objects/Economy jointly; ownership stays separate.**
   Where does succession's property/wealth-transfer link get designed? (OWN-05, FND-S15) —
   whichever domain batch is reached first should cite this rather than deciding it alone.
6. **RESOLVED by naming a family.** CAUSE-06's compression-tier and significance-fading
   constraints are both stated; their actual mechanism design belongs to the now-named History /
   Provenance family (`foundations/history-provenance.md`) — scope defined, not fully designed,
   not yet a numbered part of the world-rule design order's build sequence (only its name is now
   attached to design-preparation §3.1's item 19 and §3.2's already-anticipated entries).

## Known tensions / contradictions

None found, across either pass. This batch's own headline result is that the existing architecture
(typed Update→Patch pipeline, single-owner durable state) already satisfies nearly every proposed
semantic rule by construction — the gaps found are unbuilt downstream consequences, not
architectural contradictions with the proposed rules.

## Expected-depth implications

None. This batch operates below the per-domain depth-priority map
(`simulation-rule-world-law-design-preparation.md` §4) — it doesn't rate any of the 19 domains,
and nothing found here (in either pass) argues for revising an existing depth/priority rating.

## Repository evidence that materially changed the design

One external candidate's own worked example was factually wrong and was corrected rather than
kept: OWN-03 cited `entity.combat.readiness` as a derived-state example; direct inspection showed
it is a directly owned, authoritative field, written through the normal Combat-domain patch path.
The example list was replaced (scarcity ratio, threat classification, a reputation-derived
discount, economic opportunity) — the rule itself needed no change, only its illustration.

The adversarial expansion produced one further piece of evidence that materially changed a rule's
text (not merely its illustration): direct inspection of `src/domains/chronicle/` and
`src/domains/fame/legend.py` confirmed no importance-decay mechanism exists for historical
significance, which is what motivated CAUSE-06's one-sentence refinement (FND-S21).

## Decisions that need owner/external-reviewer attention

**All four decided 2026-09-21 — none remain open for this batch.**

- **Decided: DEFER, keep ID-03 as-is.** The two open transformation cases (`human → vampire`,
  `camp → settlement → ruin`) stay deferred to their future domains; no general-purpose
  identity-ending test was invented.
- **Decided: implementation/repository gap, no design-order change.** CAUSE-04's
  precondition-detector gap is not treated as a reason to reorder the world-rule design order —
  it is a repository-completeness gap to fix once, generally, whenever it's built.
- **Decided: RESOLVED NOW — History / Provenance added, scope only.** A fourth foundational/
  cross-cutting Rule family, History / Provenance, is introduced explicitly
  (`foundations/history-provenance.md`) to give CAUSE-05/CAUSE-06's persistence, provenance,
  compression, and significance-fading semantics a named home. Its rules are not drafted, and no
  change to the world-rule design order or implementation sequencing is implied by naming it.
- **Decided: DEFER across Family/Lineage, Politics, Objects/Economy jointly.** Succession's
  property/wealth-transfer gap (FND-S15) is not scoped to whichever domain batch happens to come
  first — each of the three retains its own separate canonical state ownership, and whichever is
  reached first should cite this open question rather than deciding it alone.

## Starter-candidate disposition summary

20 of 20 external candidates accepted (0 rejected, 0 split, 0 merged, 0 moved out of family). 3
refined beyond a plain accept in the original pass: ID-03 (explicit default/exception split
added), OWN-03 (factual correction to its example list), CAUSE-06 (constraint kept here, detailed
mechanism design partial-moved to a future family). 2 rules added locally: ID-08 (identity applies
uniformly across scale), ID-09 (a name/epithet is not identity). One additional candidate (a
same-tick domain read/write ordering rule) was drafted and deliberately rejected as an
implementation concern, not a world-semantic one — recorded in `state-ownership.md` so it isn't
re-proposed without context.

The adversarial scenario expansion (9 further scenarios, 3 further counters) did not overturn this
disposition. It produced exactly one additional refinement — CAUSE-06 gained a one-sentence
clarification distinguishing legitimate significance-fading from erasure/fabrication — and zero
new rejections, splits, merges, or additions. The original acceptance of all 20 external
candidates is judged to survive this stronger adversarial coverage.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/world-rule-foundational-batch-01-report.md` (local review report, not part of this catalog).

## Open-question disposition pass (2026-09-21)

The six open semantic questions and four owner-attention decisions listed above are no longer
open — each carries an explicit disposition (DEFER / cross-domain-link-question /
implementation-gap / RESOLVED-by-naming-a-family), recorded in full in this export's own "Open
semantic questions" and "Decisions that need owner/external-reviewer attention" sections, and in
the relevant canonical files (`identity.md`, `state-ownership.md`, `causality.md`, and the new
`history-provenance.md`). This did not reopen Identity, State Ownership, or Causality's own
accepted semantics — the one exception (CAUSE-06's forward-reference wording, already made in the
prior pass) is a citation update, not a new semantic change. Deferred domain questions remain
exactly as deferred as before; they are simply no longer *ambiguously* deferred.

---

> **FOUNDATIONAL BATCH 01 READY FOR HIGH-LEVEL EXTERNAL REVIEW.**

All required artifacts exist and reflect both the expanded scenario set and the open-question
disposition pass: four foundational files (three drafted with 22 rules total, one — History /
Provenance — scope-only), one scenario file (21 scenarios including 8 counters), this review
export with both inventories, coverage/deferred-semantics summaries, and fully dispositioned open
questions, and the local disposition report. No contradiction was found across any pass.

```text
Foundational Batch 01 remains PASS at high level.

Identity / State Ownership / Causality remain accepted.
Deferred domain questions stay explicit.
History / Provenance is added as an explicit foundational/cross-cutting Rule family.
No implementation-order change is implied.
```

Do not begin the next foundational batch, any per-domain batch, or draft History / Provenance's
own rules, until this batch is reviewed at this level.
