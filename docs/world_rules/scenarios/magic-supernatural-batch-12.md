---
status: authoritative
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# Scenario Bank: Magic / Supernatural (Batch 12)

**Purpose/scope.** Twenty-nine scenarios used to pressure-test the Magic/Supernatural rule
families in `magic-supernatural/{supernatural-ontology,magic-capability,magical-effects,
supernatural-transformation,supernatural-entities-places}.md`, per
`tmp/world-rule-batch-12-corrected-ext-ai.md`'s own §34 seed list (25 named scenarios,
IDs MAG-S05–S29 here) plus four scenarios (MAG-S01–S04) added to directly exercise
SUP-01/SUP-02 — the anchor Rules of this batch's own Supernatural Ontology family, which the
official §34 list does not otherwise probe directly (its own scenarios test capability,
effects, transformation, places, and belief-power, but not the basic truth/evidence/
attribution split itself). Without these four, SUP-01 would have no scenario coverage at all.
Revised 2026-09-22 per a targeted semantic-cleanup follow-up
(`tmp/world-rule-batch-12-corrected-followup-ext-ai.md`): MAG-S01 and MAG-S19 each gained an
extended clause (Spontaneous Supernatural Phenomenon; Permanent Enchantment Without Ongoing
Caster) rather than new IDs, per that follow-up's own explicit preference to reuse/extend
existing scenarios where cleaner; two stale citations elsewhere (a wrong scenario-ID label on
SUP-03, a duplicate citation on the magic-and-authority entry) were also corrected as part of
this same pass.

Per the standing direction (`tmp/world-rule-direction.md`): a scenario failing against the
current repository does not mean the scenario or its Rule fails. Scoring uses the same
vocabulary as prior batches: **covered** / **partially covered** / **blocked** / **revealed
missing rule** / **revealed contradiction**, against current repository behavior, not the
ideal design.

---

## MAG-S01 — Real magic, no witness

A real supernatural event occurs; nobody observes it; nobody believes in it; no institution
recognizes it; no culture assigns significance to it; the supernatural world-state
consequence still occurs.

- **Rules invoked:** SUP-01.
- **Result: revealed missing rule.** No supernatural-event mechanism of any kind exists to
  occur unwitnessed in the first place — confirmed MISSING. SUP-01's own requirement
  (objective truth never requires recognition unless a mechanism explicitly declares it as a
  prerequisite) remains independently coherent regardless.

**Extended clause (added 2026-09-22 per a targeted semantic-cleanup follow-up): Spontaneous
Supernatural Phenomenon.** A supernatural storm or anomaly occurs; there is no caster or actor
of any kind; a declared environmental/supernatural mechanism is the source; real consequences
follow regardless.

- **Rules invoked:** SUP-03, MCAP-01.
- **Result: revealed missing rule, and the Rules' own generalized requirements are confirmed
  coherent against this caster-free case specifically.** Confirmed MISSING — no environmental
  or spontaneous supernatural mechanism of any kind exists. This clause directly tests
  SUP-03's own revised wording (a valid declared cause/process and a real causal path,
  "subject to the semantics relevant to that specific mechanism" — never requiring a caster)
  and MCAP-01's own revised wording (the five candidate facts apply only where a mechanism
  actually uses them; a place-condition-driven or purely environmental mechanism may have no
  "caster" holding capability at all). Both Rules remain coherent against this case without
  modification — this clause exists specifically to confirm neither Rule was accidentally
  drafted as caster-centric.

## MAG-S02 — False magic belief

A population strongly believes a place is cursed; the belief affects travel, economics,
politics, ritual behavior, or settlement behavior; no supernatural curse actually exists.

- **Rules invoked:** SUP-02.
- **Result: revealed missing rule, though the Rule's own permission is confirmed coherent
  regardless.** No mechanism connects any belief record to real settlement-level behavior in
  this specific shape — confirmed MISSING. Separately and positively confirmed: nothing
  anywhere derives objective world truth from belief (SUP-02's own SUPPORTED-by-absence
  finding) — the "no supernatural curse actually exists" half of this scenario holds
  trivially, since no mechanism could make it exist from belief alone even if one tried.

## MAG-S03 — Misattribution, both directions

An observer sees an unexplained phenomenon; the actual cause is ordinary but unknown to that
observer; the observer attributes it to magic. Conversely: objective magic occurs; the
observer's own attribution is wrong (an ordinary cause is assigned instead).

- **Rules invoked:** SUP-01, Inherited (Perception/Knowledge, Batch 06).
- **Result: revealed missing rule, in both directions.** No supernatural-attribution
  mechanism exists for an observer to incorrectly form in either direction — confirmed
  MISSING, since no objective supernatural truth exists for an observer to misattribute to or
  away from. The general "ordinary cause, incomplete/wrong observer belief" pattern this
  scenario needs is otherwise well-supported generically (Batch 06's own belief/knowledge
  machinery), but nothing ties it to a *magic* attribution specifically.

## MAG-S04 — Conflicting explanations of one magical event

The same evidence is available to three observers; observer A believes it was ordinary;
observer B correctly attributes it to magic; observer C believes a different supernatural
explanation; all three observed the same event.

- **Rules invoked:** SUP-01.
- **Result: revealed missing rule.** Confirmed MISSING — no supernatural event/evidence
  mechanism exists for three observers to diverge over. SUP-01's own claim (one objective
  event may support several simultaneously-held, observer-relative explanations without
  changing what happened) remains coherent and testable in principle, reusing the same
  per-observer belief architecture (`BeliefEntry`, `KnowledgeFact`) already confirmed real and
  independent per entity in prior batches.

## MAG-S05 — Knows spell, cannot cast

A subject knows a ritual/spell conceptually; the subject is missing a required capability or
resource; no effect occurs.

- **Rules invoked:** MCAP-01.
- **Result: revealed missing rule.** No magical knowledge or capability field exists on any
  entity — confirmed MISSING. MCAP-01's own knowledge ≠ capability distinction remains
  coherent and testable in principle, reusing the general knowledge/capability machinery
  already established for non-magical cases.

## MAG-S06 — Innate magic without knowledge

A creature has innate supernatural capability; it uses or reacts through a declared
mechanism; it lacks explicit conceptual knowledge of that mechanism.

- **Rules invoked:** MCAP-01.
- **Result: revealed missing rule.** Same underlying gap as MAG-S05, from the opposite
  direction — confirmed MISSING.

## MAG-S07 — Illegal magic still works

A law prohibits a spell; a mage has the capability; the mage casts successfully; a legal
consequence may follow. Capability ≠ authority.

- **Rules invoked:** SUP-03, Inherited (magic and law; magic and institutions/authority).
- **Result: revealed missing rule.** Confirmed MISSING — no law-prohibits-magic or
  capability-independent-of-authorization mechanism exists. The reused target semantics
  (LAW-01's own law/compliance/enforcement distinctness, AUTH-01's own authority ≠
  capability) remain coherent and testable in principle, both already well-established for
  non-magical cases throughout this Catalog.

## MAG-S08 — Spell fails after cost

Casting commits; a cost is incurred; the effect fails.

- **Rules invoked:** Inherited (capability ≠ effect; resource/cost/capacity family).
- **Result: revealed missing rule.** Confirmed MISSING — no magic-specific cost or
  attempt-resolution mechanism exists. The general "cost incurred, outcome still uncertain"
  pattern this scenario needs is otherwise well-supported for non-magical cases (Batch 03's
  own resource/cost family, reused directly).

## MAG-S09 — Permanent spell with no ongoing magic

A spell causes an ordinary wound or environmental change; the magical process ends; the
normal resulting state persists with no continuing magical cause.

- **Rules invoked:** EFF-01, EFF-02.
- **Result: revealed missing rule, though the Rule's own permission is confirmed coherent
  regardless.** No magical-effect mechanism exists to exercise this against — confirmed
  MISSING. EFF-02's own core test (does the cause need to keep existing for the consequence
  to continue) remains independently coherent, matching this repository's own real,
  non-magical pattern (an ordinary combat wound persists without the originating attack
  needing to keep occurring).

## MAG-S10 — Persistent curse

A curse is applied; persistent supernatural state results; it continuously affects
capability.

- **Rules invoked:** EFF-02.
- **Result: revealed missing rule.** Confirmed MISSING — no persistent supernatural state
  mechanism exists anywhere in this repository.

## MAG-S11 — Dispel removes curse

A valid counter-process removes supernatural state; the downstream condition recalculates.

- **Rules invoked:** EFF-02.
- **Result: revealed missing rule.** Same underlying gap as MAG-S10 — confirmed MISSING; no
  dispel/removal mechanism exists to check lifecycle semantics against.

## MAG-S12 — Teleport across blocked space

An ordinary path is unavailable; a valid supernatural reach relation is declared; movement
succeeds.

- **Rules invoked:** MCAP-02.
- **Result: revealed missing rule.** Confirmed MISSING — no portal, teleport, or
  supernatural-reach mechanism of any kind exists, confirmed via direct search. MCAP-02's own
  requirement (a declared relation, never a default bypass) remains coherent regardless.

## MAG-S13 — Portal is one-way

An A → B supernatural connection exists; a B → A connection is unavailable.

- **Rules invoked:** MCAP-02.
- **Result: revealed missing rule.** Same underlying gap as MAG-S12 — confirmed MISSING.
  MCAP-02's own explicit non-bidirectionality permission (a portal's own connection is never
  assumed bidirectional) remains coherent regardless, directly resolving Batch 04's own
  directional-topology permission for the supernatural case.

## MAG-S14 — Illusion causes real action

An illusion changes perception; a false belief forms; the subject reacts; a real consequence
follows.

- **Rules invoked:** Inherited (illusion, reusing SUP-01 and Batch 06 Perception/Knowledge).
- **Result: revealed missing rule.** Confirmed MISSING — no illusion mechanism exists. The
  general evidence-manufactured-by-a-real-process pattern this scenario needs is otherwise
  fully covered by SUP-01's own evidence ≠ truth distinction, reused directly.

## MAG-S15 — Divination without omniscience

A subject invokes a valid divination; bounded supernatural information is received;
uncertainty remains where declared.

- **Rules invoked:** Inherited (divination, reusing Batch 06 PERC-01/KNOW-01).
- **Result: revealed missing rule.** Confirmed MISSING — no divination mechanism exists. The
  reused information-channel discipline (a supernatural channel is gated exactly like any
  other) remains coherent regardless.

## MAG-S16 — Perfect divination where declared (counter)

A world rule explicitly grants an exact answer; the subject receives exact relevant truth.

- **Rules invoked:** Inherited (divination).
- **Result: revealed missing rule, and the Rule's own permission is confirmed not
  prohibited by any general Rule.** Confirmed MISSING — no divination mechanism exists to
  declare exact. Checked directly: no general Rule in this Catalog (including the
  "no silent omniscience" requirement) forbids a domain from explicitly declaring a channel
  perfectly reliable — the prohibition is specifically against *unstated* reliability.

## MAG-S17 — Memory alteration

Magic changes memory; world history remains unchanged; later decisions change as a result.

- **Rules invoked:** Inherited (mind/memory magic), EFF-01.
- **Result: revealed missing rule.** Confirmed MISSING — no memory-altering magic mechanism
  exists. The reused five-way distinctness (belief ≠ memory ≠ motivation ≠ compelled action ≠
  relationship) and cross-domain ownership (Knowledge owns the resulting memory/belief state)
  remain coherent regardless.

## MAG-S18 — Compelled action

A subject prefers option A; a valid magical compulsion requires option B; B is chosen or
executed within the declared scope.

- **Rules invoked:** Inherited (mind/memory magic, exercising Batch 06's own AGENCY-02
  compulsion carve-out).
- **Result: revealed missing rule.** Confirmed MISSING — no compulsion mechanism exists. The
  carve-out this scenario would exercise (AGENCY-02's own explicit reservation for reflex/
  compulsion/mind-control overrides) remains coherent and already anticipated by name in
  Batch 06's own evidence.

## MAG-S19 — Enchanted sword

An ordinary sword is enchanted; it remains the same object with a new supernatural
capability.

- **Rules invoked:** STR-01, Inherited (magical objects, reusing OBJ-01).
- **Result: revealed missing rule.** Confirmed MISSING — no enchantment mechanism exists.
  STR-01's own default-continuity claim, and the Inherited magical-objects entry's own
  ownership/identity distinctness, both remain coherent regardless, reusing already-real
  non-magical evidence (`TransformationService`, `EvolutionSystem`, Batch 08's OBJ-01).

**Extended clause (added 2026-09-22 per a targeted semantic-cleanup follow-up): Permanent
Enchantment Without Ongoing Caster.** The caster who enchanted the sword completes the
enchanting ritual, then leaves or dies; the sword remains objectively enchanted as its own
current property regardless.

- **Rules invoked:** EFF-02 (corrected).
- **Result: revealed missing rule, and EFF-02's own corrected two-shape distinction is
  confirmed coherent against exactly the case that motivated the correction.** Confirmed
  MISSING — no enchantment-persistence mechanism exists. This clause is the direct probe
  EFF-02's own follow-up correction was written to satisfy: the enchantment is genuinely
  persistent supernatural state (magic's own to own, per EFF-01), yet it is not an "ongoing
  cause" in the original narrower sense — the caster is gone and the enchanting action is not
  re-executing. EFF-02's own corrected "durable supernatural property/consequence" shape
  covers this case directly; the original, narrower wording ("requires the cause to remain
  active") would have wrongly implied no persistent supernatural state remains once the
  caster is gone.

## MAG-S20 — Artifact recreated

An ordinary object is destroyed in a ritual; a magical artifact is created; a new identity
results, with provenance links remaining to the destroyed original.

- **Rules invoked:** STR-01, Inherited (magical objects).
- **Result: revealed missing rule.** Confirmed MISSING — no ritual-destruction-creates-new-
  artifact mechanism exists. STR-01's own declared-exception half (identity replacement, not
  continuity) remains coherent regardless — this is the declared-replacement counterpart to
  MAG-S19's own declared-continuity case, both resolved by the same Rule's own two permitted
  outcomes.

## MAG-S21 — Human → vampire

A living human undergoes a supernatural transformation; identity continuity holds by default;
lifecycle/body/capability changes result.

- **Rules invoked:** STR-01.
- **Result: revealed missing rule.** Confirmed MISSING — no human-to-vampire or comparable
  supernatural-transformation mechanism exists anywhere in this repository. STR-01's own
  default-continuity claim remains coherent regardless, reusing the same real, non-magical
  evidence as MAG-S19/S20.

## MAG-S22 — Resurrection

A subject dies; death remains a real historical fact; a valid supernatural process occurs;
the subject becomes active again. Whether the same identity persists is governed by the
declared rule.

- **Rules invoked:** STR-02.
- **Result: revealed missing rule.** Confirmed MISSING — no resurrection mechanism exists
  anywhere in this repository. This repository's own real death/lifecycle machinery
  (`LifecycleSystem`) already treats death as permanent with no reversal path, consistent
  with — though narrower than — STR-02's own permitted-but-not-required reversal case.

## MAG-S23 — Undead new identity (counter)

A corpse undergoes necromancy; a new undead subject results, rather than the original person
being revived. Resurrection ≠ undead creation by default.

- **Rules invoked:** STR-02.
- **Result: revealed missing rule.** Confirmed MISSING — no necromancy mechanism exists.
  STR-02's own explicit non-collapse (resurrection and undead-creation are two distinct,
  separately-declared operations) remains coherent regardless.

## MAG-S24 — Sacred but not magical place

A culture treats a site as sacred; no supernatural property exists there.

- **Rules invoked:** PLC-01, Inherited (sacredness entry, reusing `collective-belief.md`'s
  BEL-03).
- **Result: covered, by direct reuse of Batch 11B's own evidence.** BEL-03's own confirmed
  finding (a place may become sacred through cultural interpretation alone, with no
  supernatural component) already establishes this half of PLC-01's own seven-way split —
  reused directly, not re-investigated, since Batch 11B already confirmed the target
  semantics coherent even though no sacred-place mechanism of any kind is realized (MISSING,
  cross-referenced).

## MAG-S25 — Magical but unknown place

A place has an objective supernatural condition; society is unaware; no cultural significance
has yet formed.

- **Rules invoked:** PLC-01.
- **Result: revealed missing rule.** This is the specific half of PLC-01's own seven-way
  split that Batch 11B's own "Real Magic, No Cultural Recognition" boundary probe explicitly
  left blocked rather than positively defined. Confirmed MISSING: no objective
  supernatural-property field exists on `PlaceState` — but PLC-01's own positive requirement
  (objective supernatural truth never requires cultural recognition) is now stated as this
  family's own target semantics, closing the boundary Batch 11B could only block.

## MAG-S26 — Belief-powered effect (permission probe)

A declared supernatural rule consumes collective belief; a magical effect changes as a
result. This world is not assumed to use this mechanism.

- **Rules invoked:** SUP-02.
- **Result: revealed missing rule, and the Rule's own permission is confirmed coherent
  regardless.** No belief-powered-magic mechanism exists — confirmed MISSING, consistent with
  SUP-02's own explicit statement that no such mechanism is assumed to exist. SUP-02's own
  requirement (if such a mechanism is ever declared, it must be its own specific causal
  conversion edge, never a universal "belief = truth" collapse) remains coherent and
  architecturally unblocked.

## MAG-S27 — False religious belief, real magic elsewhere

A culture holds an incorrect cosmology; the real supernatural system behaves differently; the
culture remains wrong until valid evidence spreads.

- **Rules invoked:** SUP-01, Inherited (Collective Belief, Batch 11B's BEL-01/02).
- **Result: revealed missing rule.** Confirmed MISSING — no supernatural system exists for a
  culture's own cosmology to diverge from. SUP-01's own six-way distinctness (a false
  collective belief may coexist indefinitely with a different objective truth, correctable
  only through a real information path) remains coherent regardless, directly reusing Batch
  11B's own already-established belief ≠ truth machinery.

## MAG-S28 — Magic creates political consequence

An ordinary individual acquires supernatural capability; this affects conflict, resources, or
place; organizations begin reacting to that named individual.

- **Rules invoked:** EFF-01, Inherited (Organizations, Batch 10; Lineage/Descent, Batch 09;
  Capability/Progression, Batch 07 — the recurring significance pattern).
- **Result: revealed missing rule.** Confirmed MISSING — no supernatural-capability-
  acquisition mechanism exists to feed the already-confirmed-missing "ordinary individual →
  organizational recognition by name" gap this Catalog has now found at four prior scales
  (individual, Batch 07; lineage, Batch 09; organization, Batch 10; place, Batch 11A). This
  scenario confirms the identical gap recurs for a supernatural-capability-driven case too,
  rather than resolving it.

## MAG-S29 — Ordinary creature → supernatural regional threat

An ordinary creature undergoes supernatural transformation or adaptation; a real capability
change results; persistent local consequences follow; named recognition or world reaction may
emerge, but is never scripted automatically.

- **Rules invoked:** STR-01, Inherited (the same recurring significance pattern as MAG-S28).
- **Result: revealed missing rule.** Confirmed MISSING — no creature-transformation-to-
  regional-threat mechanism exists. STR-01's own identity-continuity default remains coherent
  regardless (the creature's own identity persists through the transformation by default);
  the "named recognition may emerge, never scripted automatically" half directly reuses this
  Catalog's own already-established discipline against a `UniversalSignificanceSystem`.

---

## Cross-batch note

MAG-S24's own "covered, by direct reuse" result is this batch's own distinctive shape,
matching the same pattern Batch 12's own earlier, superseded draft already found: Batch 11B's
own already-frozen sacredness content fully answers the "cultural" half of PLC-01's own
required boundary without needing re-investigation — the new content this batch adds is
specifically the *objective supernatural* half (SUP-01, PLC-01) those Rules deliberately left
open pending this batch's own arrival.

MAG-S28/S29 together confirm the recurring "ordinary subject → historically significant,
recognized by name" gap — already found at four prior scales across four separate batches
(individual, lineage, organization, place) — recurs identically for a supernatural-capability-
driven trajectory, rather than resolving it. Per this batch's own §43 cross-domain
significance probe, this batch adds no new requirement to that shared grammar beyond
confirming it applies here too; no Universal Significance system was created as a result.

Every scenario except MAG-S24 confirms the same pattern Batch 10's own Law/Enforcement family
first established at this scale: an entire rule family with essentially no in-world
repository counterpart to check against, recorded honestly as a load-bearing semantic gap per
the standing direction, not as evidence against the target semantics themselves.

**Follow-up note (2026-09-22).** A targeted semantic-cleanup follow-up added two extended
clauses to already-existing scenarios rather than new scenario IDs — MAG-S01's own
"Spontaneous Supernatural Phenomenon" clause confirms SUP-03/MCAP-01 are not accidentally
caster-centric; MAG-S19's own "Permanent Enchantment Without Ongoing Caster" clause is the
direct probe that motivated EFF-02's own correction to recognize a durable-property/
consequence shape of persistent supernatural state, distinct from an ongoing-cause shape. The
same follow-up corrected two stale citations found during this pass: SUP-03 had cited
MAG-S06 under the label "failed spell after cost" (the correct scenario for that label is
MAG-S08; MAG-S06 is "Innate Magic Without Knowledge") and the magic-and-authority Inherited
entry in `magic-capability.md` cited MAG-S07 twice. Neither correction changes any Rule's own
substance — both are traceability fixes.
