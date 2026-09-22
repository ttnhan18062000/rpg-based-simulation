---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Batch 12 (Magic / Supernatural)

**Generated from canonical sources on 2026-09-22 (revised same day per a targeted
semantic-cleanup follow-up).** Canonical files → this export → external review → feedback →
canonical files updated → export regenerated. Never patch only this file.

**Canonical sources:** `magic-supernatural/supernatural-ontology.md`,
`magic-supernatural/magic-capability.md`, `magic-supernatural/magical-effects.md`,
`magic-supernatural/supernatural-transformation.md`,
`magic-supernatural/supernatural-entities-places.md`. Scenario bank:
`scenarios/magic-supernatural-batch-12.md` (MAG-S01–S29).

**Drafting note.** This batch was first drafted 2026-09-21 as a single file
(`magic-supernatural/supernatural.md`, MAG-01–05) per `tmp/world-rule-batch-12-ext-ai.md`, then
fully redrafted 2026-09-22 as five files per a corrected, richer instruction file
(`tmp/world-rule-batch-12-corrected-ext-ai.md`), before any follow-up review of the original
draft was applied. The original single-file draft is superseded and removed (`git rm`); its own
reasoning is preserved by direct citation where a corresponding conclusion recurs in this
redraft (see the magical-objects Inherited entry below). The redraft was then revised the same
day per a second, targeted semantic-cleanup follow-up
(`tmp/world-rule-batch-12-corrected-followup-ext-ai.md`) — this export reflects that revision.

---

## Rule Admission Accounting

**10 genuine Domain Rules** (SUP-01, SUP-02, SUP-03, MCAP-01, MCAP-02, EFF-01, EFF-02, STR-01,
STR-02, PLC-01) of **31 total catalog entries** — 10 Domain Rules, 16 Inherited/Applied
Foundational Rules, 5 Scope/Deferred Boundaries — across the five family files, **unchanged by
the semantic-cleanup follow-up.** The follow-up's own instruction explicitly warned not to
preserve the count artificially if any admission changed during cleanup — it did not: every
edit was a wording/framing refinement (softening "independent facts," generalizing SUP-03's
causal-chain shape, broadening EFF-02's persistent-state shapes, sharpening STR-02's
required/permitted split, correcting two repository-evidence framings), not a reclassification
of any Rule's own admission status. No Rule was reclassified away from Domain status in this
batch (contrast Batch 11B's BEL-03).

## Rule Inventory

| ID | Family | One-line semantic purpose | Status |
|---|---|---|---|
| SUP-01 | Supernatural Ontology | Objective supernatural truth, evidence, attribution, belief, and knowledge are six semantically distinct facts that must not be silently substituted for one another | ACCEPT — REQUIRED |
| SUP-02 | Supernatural Ontology | Belief never defaults to causing supernatural truth; belief-powered magic is its own declared conversion edge | ACCEPT — REQUIRED |
| SUP-03 | Supernatural Ontology | Magic is never a causality exception; a real declared cause/process and causal path is always required, but the specific process shape (caster-driven, caster-free, ritual, standing condition) is mechanism-declared | ACCEPT — REQUIRED (causal discipline); PERMITTED (specific process shape) |
| MCAP-01 | Magic Capability | Magical knowledge, capability, resource, reach, and authorization are semantically distinct where a mechanism actually uses them; not every mechanism uses all five | ACCEPT — REQUIRED (distinctness where applicable); PERMITTED (which facts apply) |
| MCAP-02 | Magic Capability | Supernatural reach bypassing ordinary topology requires declared supernatural reach semantics; non-bidirectionality permitted; a persistent relation record is one possible implementation, not the Rule itself | ACCEPT — REQUIRED (declared-semantics requirement); PERMITTED (specific reach shape/representation) |
| EFF-01 | Magical Effects | A magical effect's cause is distinct from the resulting consequence's canonical ownership; magic is never the owner of every downstream effect | ACCEPT — REQUIRED (preserved unchanged) |
| EFF-02 | Magical Effects | Persistent supernatural state may be an ongoing cause or a durable property/consequence; either requires declared lifecycle semantics; conflicts must not leave undefined state | ACCEPT — REQUIRED |
| STR-01 | Supernatural Transformation | Transformation preserves identity by default; classification (species/kind/form) ≠ identity | ACCEPT — REQUIRED (default + classification-≠-identity); PERMITTED (specific replacement declarations) |
| STR-02 | Supernatural Transformation | Death, resurrection, and undeath must not be silently collapsed where a domain models any of them | ACCEPT — REQUIRED (distinctness where modeled); PERMITTED (whether either exists at all) |
| PLC-01 | Supernatural Entities/Places | Objective supernatural property, cultural sacredness, institutional declaration, individual knowledge/belief, historical significance, and past supernatural events at a Place are seven semantically distinct facts; no Place need materialize all of them | ACCEPT — REQUIRED |

## Inherited Foundations Summary

16 entries, each direct reuse of an already-established Rule applied to the supernatural case,
with no new claim beyond the application itself:

- **Supernatural Ontology:** declared supernatural laws (reuses SOC-03/PROG-05/Batch 10's
  reclassified open-instability entry).
- **Magic Capability (3):** capability ≠ effect chain (AGENCY-01, Batch 07, SUP-03, Batch 10
  authority-can-fail); resource/cost/capacity (Batch 03's own family); magic ≠ authority
  (AUTH-01, INST-02/03).
- **Magical Effects (4):** resistance/immunity (SUP-01's declared-dimensions entry, Batch
  02/07 capability/authority family); magic and law (LAW-01/03); magic and institutions/
  authority/culture (INST-03/04, BEL-01/02); environment/ecology (this file's own EFF-01/02).
- **Supernatural Transformation (2):** summoning/creation/manifestation/construction (this
  file's own STR-01); souls, as a possible future ontology, never required (Durable State
  Rule, ID-03/06).
- **Supernatural Entities/Places (5):** magical objects (STR-01, Batch 08's OBJ-01); illusion
  (SUP-01, Batch 06 Perception/Knowledge); divination (Batch 06 PERC-01/KNOW-01, with the
  explicit declared-perfect-channel clarification, and — corrected 2026-09-22 — the
  `magic_sense`/`magic_signal` structural-capability finding now stated here in full rather
  than incorrectly cross-referenced to `magic-capability.md`); mind/memory magic and
  compulsion (SUP-01, Batch 06 AGENCY-01/02's own reserved carve-out); observer legibility (a
  synthesis of SUP-01/SUP-03, not independently tested).

## Scenario Inventory

29 scenarios (MAG-S01–S29): S01–S04 added directly to exercise SUP-01/SUP-02 (not otherwise
probed by the corrected instruction's own §34 seed list); S05–S29 are that seed list's own 25
scenarios in original order, including 3 explicit counter-probes (S16 perfect divination, S23
undead new identity, plus S24's covered-by-reuse result acting as a boundary check on PLC-01).
**Revised 2026-09-22:** MAG-S01 gained an extended "Spontaneous Supernatural Phenomenon" clause
(testing SUP-03/MCAP-01 against caster-centric assumptions) and MAG-S19 gained an extended
"Permanent Enchantment Without Ongoing Caster" clause (the direct probe that motivated EFF-02's
own correction) — both added as clauses on existing IDs, not new IDs, per the follow-up's own
explicit preference. Full trajectories, Rules invoked, and results are in
`scenarios/magic-supernatural-batch-12.md`.

| ID range | Family stress-tested | Result shape |
|---|---|---|
| S01–S04 | Supernatural Ontology (SUP-01/02/03) | revealed missing rule (×4); S01's extended clause additionally confirms SUP-03/MCAP-01 are not caster-centric |
| S05–S08 | Magic Capability (MCAP-01) | revealed missing rule (×4) |
| S09–S11 | Magical Effects (EFF-01/02) | revealed missing rule (×3) |
| S12–S13 | Magic Capability (MCAP-02) | revealed missing rule (×2) |
| S14–S18 | Supernatural Entities/Places, Mind/Memory (Inherited) | revealed missing rule (×5) |
| S19–S23 | Supernatural Transformation (STR-01/02), Magical Effects (EFF-02) | revealed missing rule (×5); S19's extended clause confirms EFF-02's own corrected durable-property shape |
| S24–S25 | Supernatural Entities/Places (PLC-01) | covered (S24, direct Batch 11B reuse), revealed missing rule (S25) |
| S26–S27 | Supernatural Ontology (SUP-02) | revealed missing rule (×2) |
| S28–S29 | Cross-domain significance (Inherited) | revealed missing rule (×2) |

## Coverage Summary

The scenario set stress-tests: (1) the six-way truth/evidence/attribution/belief/knowledge/
collective-belief split, now including the caster-free case (S01–S04); (2) knowledge ≠
capability ≠ resource ≠ reach ≠ authority, with authorization explicitly optional (S05–S08);
(3) cross-domain effect ownership and the now-two-shape persistent-state lifecycle (S09–S11);
(4) declared supernatural reach semantics and non-bidirectional portals (S12–S13); (5)
illusion, divination, and mind/memory magic as direct applications of Batch 06 (S14–S18); (6)
transformation identity-continuity, death/resurrection/undeath distinctness, and the
durable-enchantment-without-caster case (S19–S23); (7) the objective-magic/cultural-sacredness
reconciliation with Batch 11A/11B (S24–S25); (8) belief-powered magic as a permission, never a
default (S26–S27); (9) the recurring ordinary-subject → significant-subject trajectory, now
traced for a supernatural-capability driver (S28–S29). One scenario (S24) is fully covered by
direct reuse of already-frozen Batch 11B evidence, not a new investigation — recorded honestly
as such rather than presented as new coverage.

## Deferred Scenario Semantics

- **S05/S06/S08** presuppose a concrete magical-resource/cost model; MCAP-01's own
  distinctness-where-applicable is testable regardless, but the specific resource shape is
  Scope-Deferred.
- **S12/S13** presuppose a concrete portal/teleport mechanism; MCAP-02's own declared-semantics
  requirement and non-bidirectionality permission are testable regardless.
- **S15/S16** presuppose whether this world ever declares a perfect divination channel; both
  outcomes are independently coherent under the Inherited divination entry — not decided here.
- **S22/S23** presuppose whether this world ever declares resurrection/undeath mechanisms at
  all; STR-02's own three-way non-collapse is testable regardless of whether either is ever
  built, per its own revised required-distinctness/permitted-existence split.

## Cross-domain Findings

- **Resolved.** The mandatory Batch 11A/11B reconciliation boundary — PLC-01 states objective
  supernatural property as an eighth semantically distinct fact for Places, alongside the
  already-attribution-relative significance (`places.md`'s PLACE-02) and sacredness (the
  reclassified sacredness entry, originally BEL-03) those batches established. MAG-S24 confirms
  this by direct reuse: Batch 11B's own sacredness evidence already fully answers the cultural
  half of this reconciliation without re-investigation.
- **Positively defined.** The inverse of Batch 11B's own blocked "Real Magic, No Cultural
  Recognition" probe: objective supernatural truth never requires belief, observation,
  recognition, or cultural interpretation (SUP-01, PLC-01), unless a specific mechanism
  declares one as a causal prerequisite.
- **Directly resolves a named deferred boundary from Batch 04.** MCAP-02 states that supernatural
  reach bypassing ordinary spatial topology requires declared supernatural reach semantics,
  with a portal's own connection never assumed bidirectional — the non-physical-movement
  boundary Batch 04 left open. A persistent relation record remains one legitimate
  implementation of that declaration, never the Rule's own requirement.
- **Directly resolves a named deferred boundary from Batch 06.** The mind/memory-magic Inherited
  entry exercises AGENCY-02's own explicit reserved carve-out for reflex/compulsion/mind-control
  overrides by name — not new content, the direct exercise of an anticipated carve-out.
- **Confirms, rather than introduces, the recurring significance gap.** MAG-S28/S29 find the
  same "ordinary subject → historically significant, recognized by name" gap already confirmed
  missing at four prior scales (individual, Batch 07; lineage, Batch 09; organization, Batch
  10; place, Batch 11A) recurs for a supernatural-capability-driven trajectory too. Per §43's
  own cross-domain significance probe: this batch adds no new requirement to that shared
  grammar beyond confirming it applies here — no Universal Significance system was created.

## Repository Findings

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **Confirmed MISSING, the largest single gap this batch found.** No dedicated magic/
  supernatural mechanism of any kind exists anywhere in this repository. Every "magic"-named
  element traced resolves to unrelated flavor/mechanical content: an `ItemDef` category tag
  (`"magic"`, affecting weapon range for `mage`-tagged items), a damage-type multiplier on one
  combat skill ("Fireball," "200% magic damage"), and a content tag (`"magical"`) on one region
  (`moon_cave`) with no behavioral consequence traced. None collapses any of this family's own
  target distinctions — confirmed MISSING, not CONFLICTING, per the standing direction's own
  discipline. Comparable in scope to Batch 10's own Law/Enforcement gap.
- **Confirmed MISSING — no portal, teleport, resurrection, undeath, soul, summoning, illusion,
  divination, or spontaneous/environmental supernatural mechanism of any kind exists anywhere
  in this repository**, each confirmed via direct search.
- **A genuinely positive structural finding, currently INERT/OFF — reframed 2026-09-22 per a
  targeted semantic-cleanup follow-up.** `PerceptionGate`'s own `magic_sense`/`magic_signal`
  channel (`src/world/perception/gate.py`) is real, live, structurally-ready information-
  channel infrastructure, gated by the identical threshold/confidence discipline as vision or
  hearing. This is **existing perception infrastructure structurally capable of hosting a
  supernatural information channel** — an earlier draft of this finding characterized it as
  more than that; corrected here to make clear the channel's own shape exists while its
  content/source semantics remain MISSING (no content anywhere emits a non-default value). This
  finding's canonical home is `supernatural-entities-places.md`'s own divination Inherited
  entry and Repository Findings — a prior version of that file incorrectly cross-referenced it
  to `magic-capability.md`, which never actually contained it; that cross-reference is now
  corrected.
- **A significant, notable finding, not itself a gap.** `TransformationService`
  (`src/world/transformation.py`, region kind-shifting FOREST→BURNT_FOREST→WASTELAND) and
  `EvolutionSystem` (`src/engine/evolution.py`, entity growth-milestone transformation) are
  real, non-supernatural mechanisms already implementing exactly the identity-persists/
  classification-changes shape STR-01 requires — direct, if non-supernatural, evidence that
  this repository's own architecture already supports this Rule's own target shape.
- **A significant, notable finding, not itself a gap.** This repository's own real,
  non-supernatural cross-domain causal producers (e.g., a combat hit producing a Body-owned
  wound, never a `CombatState`-owned one) already demonstrate the exact ownership discipline
  EFF-01 requires — preserved unchanged per the follow-up's own explicit instruction to keep
  EFF-01 strong.
- **No CONFLICT observed for SUP-02's own "belief does not create truth by default"
  requirement; positive supernatural realization remains MISSING — corrected 2026-09-22.**
  No mechanism anywhere derives objective world state from belief or cultural state, so there
  is no existing shortcut to correct — but because this repository has essentially no
  supernatural realization at all, that absence is not, by itself, positive implementation
  evidence for SUP-02's full target semantics. The earlier "SUPPORTED, by absence" framing
  overstated this; absence of an entire domain's realization is not equivalent to positive
  implementation support, and this distinction matters for any future implementation mapping.
- **No CONFLICTING finding was recorded anywhere in this batch** — every traced element is
  MISSING or a non-collapsing structural match, never an active collapse of this family's own
  distinctions.
- **Two stale citations corrected during this follow-up pass, traceability fixes only, no
  substantive change.** `supernatural-ontology.md`'s SUP-03 had cited MAG-S06 under the label
  "failed spell after cost" (the correct scenario for that label is MAG-S08; MAG-S06 is
  "Innate Magic Without Knowledge"); `magic-capability.md`'s magic-and-authority Inherited
  entry cited MAG-S07 twice instead of once.

## Open Questions

Carried forward from all five files (deduplicated):

1. What semantic conditions turn a Place's own objective supernatural property into socially
   meaningful recognition — attribution alone, or a further threshold? Not decided here.
2. Should this world ever declare a perfect divination mechanism, or should every supernatural
   information channel remain bounded/fallible? Not decided here.
3. What constitutes supernatural reach for a given mechanism, beyond "domain-declared"? Not
   decided here.
4. Is a universal `MagicPower` stat ever genuinely required, or should every supernatural
   capability remain mechanism-specific? Not decided here.
5. Which specific magical effects require persistent source state (either shape), versus a
   one-time trigger of an ordinary downstream effect? EFF-02 states the test; applying it
   per-effect is not decided here.
6. Is supernatural state a cause or a durable consequence, in any specific future case? Not
   decided here — the design-semantic question EFF-01/EFF-02 exist to let a future author
   answer correctly.
7. When does a magical transformation preserve identity, versus establish a declared exception?
   STR-01 states the default; which transformations a future domain declares as exceptions is
   not decided here.
8. Does this world require an objective soul concept? Not decided here — Scope-Deferred.
9. What distinguishes a magical species/kind classification from a merely temporary magical
   condition (permanent vampire vs. temporary polymorph)? Not decided here.

## Owner-Attention Semantic Decisions

Design-semantic questions only, per the standing direction's own discipline — none of these are
implementation asks:

- Does this world have one universal category called "supernatural," or multiple unrelated
  mechanisms grouped only for design convenience? (Open Question, Scope-Deferred as a universal
  substrate.)
- Can belief ever causally affect supernatural truth, and if so, is that universal or
  mechanism-specific? (SUP-02 answers the default case; the specific-mechanism case is open.)
- Are gods/divine entities objectively supernatural subjects, socially constructed beliefs, or
  both depending on the entity? Not decided — SUP-01/PLC-01's own distinctions apply regardless
  of which answer a future domain chooses.
- Is there any semantic reason to unify spells, miracles, curses, enchantments, and psychic
  effects beyond repository naming, or should they remain genuinely separate mechanisms? Not
  decided, per the corrected instruction's own explicit anti-collapse discipline.

## Implementation Candidates — Non-Binding

**Nothing here is approved, prioritized, or required for implementation during the World Rule
Catalog phase.**

- **Target semantic:** a supernatural information channel establishes a new, bounded
  information path, gated the same way as any other sense (Inherited illusion/divination
  entries).
  **Current realization:** `PerceptionGate`'s own `magic_sense`/`magic_signal` channel is
  existing perception infrastructure structurally capable of hosting such a channel — not,
  itself, evidence the target semantics are implemented (corrected 2026-09-22). No content
  emits a non-default value.
  **Gap/mismatch:** the gating shape exists; content and source semantics do not.
  **Possible implementation direction:** a declared supernatural event/effect writing a
  non-default `magic_signal` onto the emitting entity/place's own properties, read through the
  existing, unmodified `PerceptionGate` path — no new perception mechanism required.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.
- **Target semantic:** a supernatural property or condition attaches to its subject
  independently of ownership, with its own declared persistence rules, in either the
  ongoing-cause or durable-property/consequence shape (MCAP-01/EFF-02).
  **Current realization:** no supernatural-property field exists anywhere.
  **Possible implementation direction:** a typed supernatural-condition relation (subject,
  source, kind, activation/removal condition), illustrative only — never a universal
  `MagicState` or one global effect hierarchy, per EFF-01's own explicit anti-dumping-ground
  requirement, preserved unchanged.
  **Implementation decision:** DEFERRED.
- **Target semantic:** a Place's own objective supernatural property is semantically distinct
  from attributed sacredness, institutional declaration, and historical significance (PLC-01).
  **Current realization:** no bridge exists between `PlaceState` and any supernatural concept.
  **Possible implementation direction:** consistent with `collective-belief.md`'s own already-
  recorded candidate, a relational (`sacred-to`, `attributed-by`) model rather than a boolean,
  now additionally requiring an independent objective-supernatural-property fact alongside it.
  **Implementation decision:** DEFERRED.
- **Target semantic:** supernatural reach bypassing ordinary topology requires declared
  supernatural reach semantics, of which a persistent relation record is one possible shape,
  not the requirement itself (MCAP-02).
  **Current realization:** no portal/teleport mechanism exists; ordinary Reach (Batch 02/04) is
  real and unbypassed today.
  **Possible implementation direction:** a portal/teleport relation reusing the existing Reach
  contract's own shape (source, target, eligibility) rather than a parallel mechanism — one
  possible representation among others.
  **Implementation decision:** DEFERRED.

## Candidate Disposition

All four Implementation Candidates above: **DEFERRED, non-binding.** No implementation work is
authorized by this review. Each preserves a target semantic and a possible direction only, to
be evaluated on its own merits if and when a future ticket proposes building it.

---

## Explicit call-outs (per §42)

- **Genuine Domain Rule count:** 10, of 31 total catalog entries — unchanged by the
  semantic-cleanup follow-up.
- **Supernatural truth vs. social belief boundary:** stated explicitly and held throughout
  (SUP-01, SUP-02) — objective truth never requires recognition; belief never defaults to
  causing truth.
- **Magic obeys normal causal/state-ownership discipline:** yes — SUP-03 states magic is never
  a causality exception (causal discipline universal, process shape mechanism-specific); EFF-01
  states magic is never the canonical owner of every downstream effect.
- **Supernatural reach and topology:** MCAP-02 requires declared reach semantics; no default
  bypass; non-bidirectionality explicitly permitted; no specific data representation mandated.
- **Magic knowledge and capability distinctness:** yes, both directions, where the mechanism
  uses them — authorization specifically may be inapplicable (MCAP-01).
- **Magical effects write through owning domains:** yes (EFF-01, preserved unchanged), with
  direct, real, non-supernatural repository evidence that this discipline is already
  architecturally sound.
- **Persistent supernatural state lifecycle semantics:** required where such state exists, in
  either an ongoing-cause or durable-property/consequence shape (EFF-02, corrected); not
  assumed permanent or removable by default.
- **Transformation preserves identity coherently:** yes, by default (STR-01), reusing real
  non-supernatural repository analogues (`TransformationService`, `EvolutionSystem`).
- **Resurrection/undeath semantics distinguishable:** yes, wherever modeled at all (STR-02,
  corrected required/permitted split).
- **Culturally sacred vs. objectively magical Places distinct:** yes (PLC-01), directly
  reconciling Batch 11A/11B, with no Place required to materialize all seven distinct facts.
- **Belief-powered magic:** remains explicit and permitted, never accidental or default (SUP-02).
- **Current magic/supernatural state:** confirmed causally MISSING everywhere except one
  structurally-ready, currently INERT/OFF perception channel (`magic_sense`/`magic_signal`) —
  itself only structural capability, not implemented target semantics; no kind-tag branching
  found acting as a supernatural ontology.
- **Supernatural progression and persistent significance:** the ordinary-subject →
  significant-subject trajectory is traced (MAG-S28/S29) and confirmed to recur, not resolved,
  for the supernatural case — same load-bearing gap already found at four prior scales.

---

> **BATCH 12 PASS — READY TO FREEZE**
>
> Major domain semantics are now drafted and coherent. Repository supernatural realization
> remains substantially MISSING. No implementation commitment is implied.
>
> All 14 stop-condition items from `tmp/world-rule-batch-12-corrected-ext-ai.md`'s own §44
> remain satisfied after this semantic-cleanup follow-up: supernatural truth/social belief
> remain distinct; magic is not a causality exception; capability/knowledge/resource/authority
> remain distinct where applicable; supernatural reach has declared semantics; magical effects
> respect canonical state ownership; persistent effects have lifecycle semantics in either
> shape; transformation integrates with identity/history; resurrection/undeath distinctions
> are representable wherever modeled; culturally sacred and objectively magical Places remain
> distinct; law/politics can react to magic without controlling supernatural truth;
> belief-powered magic remains explicit; the ordinary→supernatural-significance trajectory is
> traced; repository findings remain separated from implementation commitments; genuine Rules
> remain distinct from inherited Rules and examples.
>
> Proceed to Final Integration: Cross-Domain History / Significance / Propagation. Do not
> begin implementation mapping yet.
