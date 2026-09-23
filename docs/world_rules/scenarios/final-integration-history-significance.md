---
status: authoritative
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# Scenario Bank: Final Integration — Cross-Domain History / Significance / Propagation

**Purpose/scope.** Per `tmp/world-rule-integration-ext-ai.md`, this is not a new domain batch —
it tests whether the frozen/freeze-ready Rules from Foundations and Batches 04–12 actually
*compose* into the intended persistent, systemic world, rather than remaining individually
coherent but disconnected domain semantics. Each scenario below is a deep, end-to-end
trajectory, not a shallow probe — per the instruction's own explicit preference for fewer deep
scenarios over many shallow ones. Every important stage is traced against **Current
authoritative state / Producer or cause / Canonical state owner / Information path /
Downstream consumer / Persistent consequence**, and every trajectory carries at least one
explicit failure point where it can legitimately stop short (per §32/§33). Rule citations are
verified against the actual canonical files (`grep`-checked against every `## <ID> —` header
across `foundations/`, `space-environment/`, `life-body/`, `knowledge-agency/`,
`capability-progression/`, `material-economy/`, `social-lineage/`, `institutions-politics/`,
`places-culture/`, `magic-supernatural/`), not recalled from memory.

**ID-collision fix (2026-09-22, applied per a targeted follow-up review).** An earlier pass of
this export found that `foundations/capability.md` and `magic-supernatural/magic-capability.md`
each independently defined a `CAP-01`/`CAP-02`, and treated file-scope disambiguation as
sufficient. The follow-up correctly identified this as unsafe for global citation once Rule IDs
become references in Implementation Mapping, gap reports, and tickets — a bare `CAP-01` must
identify one Rule without requiring context. `magic-supernatural/magic-capability.md`'s own two
Domain Rules are therefore renamed to `MCAP-01`/`MCAP-02` throughout the Catalog (canonical
files, scenarios, and review exports), leaving `foundations/capability.md`'s own `CAP-01`–
`CAP-05` untouched. This scenario file's own citations below use `MCAP-01`/`MCAP-02` for the
magic-capability Rules and plain `CAP-0N` (marked "foundational") for the foundational ones.

---

## FI-PER-01 — Ordinary Individual → Historically Significant, No HERO Role Required

An unremarkable villager survives a violent regional crisis through a combination of decision,
capability growth, and circumstance; their actions affect specific named others; those effects
propagate through real information channels; the villager's own future opportunities and
constraints change as a causal result; eventually they become a subject other communities
have heard of — without ever being authored with a `HERO`/`LEGENDARY` classification.

**Trajectory trace:**

1. **Initial state.** An ordinary individual with unremarkable capability, no organizational
   rank, no settlement-wide reputation. *Owner:* the individual's own entity record (Identity,
   ID-01/02). *Rules:* ID-01 (persistent identity), ID-02 (identity ≠ classification — nothing
   about this stage requires a `HERO` tag to exist at all, addressing the required-answer
   directly).
2. **Consequential event.** A raid or calamity threatens a settlement; the individual makes a
   real decision (AGENCY-01: decision stages causally distinct — deciding to act is not the
   same fact as succeeding) and acts, using whatever capability they currently hold (CAP-01
   foundational: capability ≠ authority; CAP-04 foundational: capability never guarantees
   success — the individual may fail this stage entirely, see Failure Point 1). *Producer:*
   the individual's own decision + capability. *Owner:* the event itself becomes a real
   historical fact the instant it occurs (CAUSE-01: a consequence requires a real causal path;
   TIME-04: each occurrence is its own traceable event), owned by History/Provenance
   (HP-01/02), not by the individual.
3. **Capability/state change.** Surviving and acting successfully produces a real capability or
   body-state change (PROG-01: capability acquisition occurs through declared causal
   mechanisms; BODY-04: body condition creates real capability consequences; LEARN-01: an
   experience's epistemic effect and capability effect are distinct, independently-declared
   outputs). *Owner:* Capability/Progression (`capability-progression.md`) for the capability
   axis, Life/Body for any bodily consequence — never a single fused record, per PROG-03
   (Capability and Level are independent axes).
4. **Effect on named others.** The individual's action changes what happens to specific other
   entities — someone is protected, someone is defeated, a resource is redirected. *Producer:*
   the individual's own committed action. *Owner:* whichever domain the effect targets (Body
   for injury, Ownership/Possession for redirected resource, Social Relations for a rescued
   party's own relationship state) — never the acting individual, exactly the cross-domain
   ownership discipline `magical-effects.md`'s own EFF-01 states explicitly for magic and
   which this scenario confirms generalizes to ordinary causation too (OWN-05: cross-domain
   transitions preserve ownership boundaries).
5. **Information propagation — the critical link.** For anyone beyond direct witnesses to learn
   of this, a real information path must exist: a surviving witness (PERC-01: perception is
   bounded by declared constraints, no default omniscience), a report reaching an institution
   or settlement record (INFO-01: source trust is distinct from claim certainty; LAW-02: an
   institutional record's own correctness is independent of world truth), or rumor propagation
   through Social Relations (SOC-01/03). *Producer:* the witnessing/reporting act itself, a real
   causal event distinct from the original deed (CAUSE-02: causal chains may cross domains
   without breaking). *Owner:* Knowledge/Belief for each individual hearer's own resulting
   belief (KNOW-01/02 — belief revises only through a declared process, never silently
   re-syncing with truth), Collective Belief (BEL-01) for any settlement/culture-wide version,
   which may diverge from what actually happened. **This is exactly the recurring gap this
   Catalog has found missing at every prior scale (Batches 07–12) — see Failure Point 2.**
6. **Standing/relationship/reputation change.** Where the information path above actually
   completes, specific consumers change specific state: a grateful settlement changes its own
   social relation toward the individual (SOC-01/02 — reciprocal only where declared), a
   faction updates a targeted disposition (ORG-03: an organizationally-attributed change
   requires a real execution/commit path), an institution updates a record (LAW-02, INST-04).
   *Owner:* each reacting subject's own relationship/standing state — never a single global
   "fame" field, matching §5/§9's own explicit prohibition on a `UniversalSignificanceScore`.
7. **Changed future opportunity/reaction.** A merchant later extends credit because of the
   individual's now-known reputation (PROG-06: progression may change how the world reacts to
   an individual through declared causal channels — this Rule is the direct foundational
   anchor for the entire trajectory); a rival faction becomes specifically hostile to this
   named individual, not to villagers in general. *Consumer:* the specific reacting agent/
   organization, per the reach that agent actually has to this individual's own record (REACH
   family, foundational).
8. **Further history.** The changed relationship itself becomes a further historical fact
   (HP-01), available to feed a subsequent trajectory (e.g., a rival's later retaliation, or a
   future institutional appointment) — the loop closes without requiring any new Rule.

**Failure points:**

- **FP1 — the individual fails or dies at stage 2.** No capability change, no effect on named
  others follows; the event may still become a historical fact (a failed defense is still
  real history, HP-01), but the individual's own trajectory stops here. Legitimate, not a gap.
- **FP2 — no information path completes at stage 5.** The deed happened, capability changed,
  even named others were affected — but no witness survived, no report reached anyone beyond
  the immediate participants, no institution recorded it. Recognition never forms; the
  individual's own capability change persists (owned correctly by Capability/Progression) but
  no reputation, standing, or future-reaction consequence follows. **This is the load-bearing
  gap this Catalog has already found repeated at every prior scale — see the Final Integration
  review's own Recurring Repository Gap section.** Target semantics fully support this failure
  mode as legitimate (nothing requires recognition to form); the repository's own realization
  gap is that even where a path *could* exist, nothing currently implements it.
- **FP3 — information reaches only a narrow scope.** A faction learns and reacts; a neighboring,
  unconnected settlement never does. This is not a failure but the correct target outcome per
  §29 (local vs. global significance) — the individual is significant within one network,
  irrelevant elsewhere, with no monotonic significance ladder implied.

**Rules invoked:** ID-01/02, AGENCY-01, CAP-01/04 (foundational), CAUSE-01/02, TIME-04, HP-01/
02, PROG-01/03/06, BODY-04, LEARN-01, EFF-01 (reused generally, not just for magic), OWN-05,
PERC-01, INFO-01, KNOW-01/02, LAW-02, BEL-01, SOC-01/02/03, ORG-03, INST-04, REACH family.

**Assessment against §4's A/B/C test:** **(B) derivable, but missing one or more explicit
cross-domain semantic links is the wrong diagnosis — re-examined, this is actually (A) fully
derivable.** Every stage above composes from an already-established Rule; the recurring gap
(FP2) is a repository-realization gap, not a missing semantic link — no existing Rule
prevents this trajectory, and no new cross-domain Rule is required to state it. Confirmed via
the admission discipline in §34: "Rule already supports it; repository implementation
missing" is the correct category for the entire trajectory, not "genuinely missing target
semantic."

**Repository realization:** MISSING for the information-propagation and standing-change
consumer steps specifically (stages 5–7) — matches the individual-scale finding already
recorded in Batch 07's own review export. PARTIAL/SUPPORTED for stages 1–4 (capability,
body-condition, and ownership mechanisms are real and correctly scoped per prior batches'
own evidence). No CONFLICTING finding — nothing collapses these stages into one shortcut.

---

## FI-PER-02 (counter) — Great Deed, No Witness → No Significance

Identical setup to FI-PER-01 through stage 4 (the deed occurs, capability changes, named
others are affected), but every witness dies in the same event and no record, rumor, or
institutional report is ever created.

- **Current authoritative state:** the deed remains a real historical fact (HP-01) forever —
  History/Provenance does not require anyone to know a fact for it to have occurred.
- **Producer/cause:** the same real causal event as FI-PER-01.
- **Canonical state owner:** History/Provenance owns the fact; no Knowledge/Belief/Collective
  Belief record is ever created because no information path exists.
- **Information path:** **none — this is the deliberate failure point, not a gap.**
- **Downstream consumer:** none exists to react.
- **Persistent consequence:** the individual's own capability change (if any) persists,
  correctly owned by Capability/Progression; no reputation, standing, or recognition consequence
  ever forms, and none is required to.

**Result:** confirms HP-05 (significance may legitimately fade, distinct from erasure or
fabrication) implies the stronger case directly — significance may never form at all. A major
event may be permanently forgotten by construction, exactly as §25 requires this Catalog to
represent. No Rule gap; this is the target semantics working correctly.

---

## FI-CRE-01 — Ordinary Creature → Named Regional Threat

A creature with no special narrative role undergoes real adaptation/capability change through
lived events, produces repeated local consequences, and becomes identified by name/description
as a specific regional threat — without ever becoming culturally famous at continental scale.

**Trajectory trace:**

1. **Initial state.** An unremarkable creature within Ecology/Population's own aggregate model
   (ECOL-03: aggregate population change currently evolves independently of actual individual
   births/deaths — confirming this creature need not even be individually tracked at first).
2. **Individual differentiation.** Through repeated survival events, this specific creature
   accumulates a real capability change (PROG-01/PROG-05: repeatable accumulation must declare
   scaling/limiting semantics, unlimited repeatability must not arise accidentally — bounding
   this creature's own growth is required, not automatic). *Owner:* Capability/Progression for
   this specific creature's own record, once individually differentiated from the aggregate
   population (ECOL-04: aggregate pressure may feed back into individual behavior through a real
   causal path — the reverse direction, individual differentiating from aggregate, requires the
   same real-path discipline).
3. **Repeated local consequence.** The creature attacks settlements, damages resources, or
   displaces population — each a real causal event (CAUSE-01/02) with its own consequence owned
   by the targeted domain (Body for casualties, Resources/Production for destroyed resources,
   `settlements.md`'s SETT-02 for any settlement-state decline this causes).
4. **Identification as *this specific* threat.** Survivors, a settlement's own institutional
   record, or an organization (a hunters' guild, a regional authority) must form a record that
   ties repeated incidents to one specific creature (INFO-01/02: information content, not only
   certainty, may change through transmission — early reports may misattribute incidents to
   several different creatures before converging, or never converge at all). *Owner:*
   whichever institution or organization forms the record (LAW-02, ORG-03) — never the creature
   itself, which has no belief/knowledge machinery of its own to "know" it is famous.
5. **Changed regional behavior.** Settlements raise defenses (SETT-02: growth or decline
   requires a real declared causal path connecting hazard conditions to settlement-state
   change), an organization dispatches hunters (ORG-03), territorial control may contract
   (TERR-02: territorial control is real only through a declared causal requirement — a hazard
   may causally reduce administrative reach). *Consumer:* each specific reacting settlement/
   organization, not "the region" as an undifferentiated whole.
6. **Regional (not continental) significance.** Nothing in this trajectory requires the creature
   to become culturally famous — §12's own explicit instruction. The trajectory can complete
   fully at regional scope, matching §29 (local vs. global significance) directly.

**Failure points:**

- **FP1 — killed early**, before repeated incidents converge into an identified threat record.
  No regional-threat trajectory forms; individual capability change (if any occurred) simply
  becomes an unremarkable historical fact. Confirms §25's own named counter-example directly.
- **FP2 — incidents never converge to one record.** Multiple unconnected reports, never
  identified as the same creature — the creature remains an unidentified nuisance pattern
  rather than a named threat. This is a legitimate outcome per INFO-02's own "content may
  legitimately change through transmission" — misattribution and non-convergence are permitted
  target semantics, not failures of the Rule Catalog.

**Rules invoked:** ECOL-03/04, PROG-01/05, CAUSE-01/02, SETT-02, TERR-02, INFO-01/02, LAW-02,
ORG-03, HP-01.

**Repository realization:** MISSING for individual-creature differentiation from aggregate
population, for incident-to-creature identification, and for any settlement/organization
reaction keyed to a specific named creature — matches this Catalog's own recurring gap,
confirmed here at the creature scale specifically (previously confirmed missing at individual,
lineage, organization, place, and supernatural-capability scales across Batches 07–12; this is
the sixth confirmed instance, not a new discovery). ECOL-03/04's own aggregate-vs-individual
feedback machinery is real and already-established target semantics; nothing currently
realizes the individual-creature-differentiation half of it.

---

## FI-CRE-02 (counter) — Powerful Creature Killed Early → No Threat Trajectory

A creature with real innate capability is killed in its first hostile encounter, before any
repeated local consequence accumulates.

- **Current authoritative state:** one real, historical combat event (CAUSE-01, HP-01).
- **Producer/cause:** whichever party killed the creature.
- **Canonical state owner:** History/Provenance owns the single event; no threat-identification
  record is ever created because there is no *repeated* pattern for one to describe.
- **Information path:** a report of one dead creature may exist, but nothing consumes it as a
  "regional threat," since the target semantic (§12) explicitly requires repeated local
  consequences, not a single incident.
- **Persistent consequence:** none beyond the ordinary combat-outcome consequences already
  owned by Body/Objects (any loot, any injury to the killer).

**Result:** confirms §25's own named counter-example ("powerful creature, killed early, no
regional threat trajectory") is already representable without any new Rule — the trajectory
simply does not reach the stage that would require one.

---

## FI-OBJ-01 — Ordinary Object → Relic Through Provenance Alone

An unremarkable object passes through consequential events; provenance accumulates; social/
cultural meaning changes; later subjects treat it differently — all without the object ever
becoming magically enchanted.

**Trajectory trace:**

1. **Initial state.** An ordinary object with identity distinct from ownership, holder, value,
   and quantity (OBJ-01). *Owner:* Objects/Material-Culture for the object's own identity
   record; Ownership/Possession (PROP-01) for who currently holds/owns/controls it — kept
   separate from the start.
2. **Consequential use.** The object is used in a real event (a weapon in a decisive battle, a
   seal used to ratify a treaty) — a real causal event (CAUSE-01) that the object was a real
   participant in, not merely present for.
3. **Provenance accumulation.** Each consequential use adds a real, traceable causal link back
   to the object (HP-02: provenance requires a real causal ancestor, distinct from truth;
   RES-06's own analogous discipline for resource conversion — "preserve a real provenance
   link, not treat the output as spontaneously new" — generalizes here even though this is not
   a resource-conversion case). *Owner:* History/Provenance for the accumulated provenance
   chain, cross-referenced to the object's own OBJ-01 identity — never re-derived from the
   object's current material properties alone.
4. **Information/record propagation.** For the object's provenance to matter to anyone beyond
   direct witnesses, a real information path connects events to *this specific object*
   (INFO-01/02, LAW-02 for any institutional registry, or CULT-04 for oral-tradition
   transmission with no durable artifact required). Without this link, the object accumulates
   real history that nobody can attach to it — exactly FI-OBJ-02's own failure point.
5. **Social/cultural meaning change.** A culture or institution attributes new meaning — reverence,
   fear, value, ritual use (CULT-01/02: culture is a real collective pattern, never reducible to
   individual belief or a durable-artifact requirement alone; PLACE-02's own attribution
   discipline, generalized: significance is always attributed, never intrinsic, applying
   equally to an object as to a Place). *Owner:* Culture/Collective-Belief for the attributed
   meaning — distinct from the object's own OBJ-01 identity and from its current owner's own
   PROP-01 possession fact.
6. **Later differential treatment.** Later subjects value, protect, seek, or fear the object
   differently because of its now-known provenance (PROG-06's own general pattern: declared
   causal channels change how the world reacts). *Consumer:* whichever specific subject/
   institution/culture actually has an information path to this object's provenance.
7. **Historical relic ≠ magical artifact.** Nothing above requires the object to be
   supernaturally enchanted — `magic-supernatural/supernatural-transformation.md`'s own
   Inherited magical-objects entry and `supernatural-entities-places.md`'s PLC-01 both
   establish this distinction generally (culturally/historically significant ≠ objectively
   supernatural); the same object could later *also* become magically enchanted (STR-01,
   EFF-02) without collapsing the two facts into one.

**Failure points:**

- **FP1 (= FI-OBJ-02) — records/witnesses destroyed.** Provenance is lost or fades even though
  the object's own identity persists (OBJ-01, ID-05: destruction/lifecycle termination does not
  erase history — but here it is the *record* of history being lost, not the object).
- **FP2 — the object changes owner and provenance is never re-attached to it.** This is the
  specific accidental-disappearance failure mode §19 warns against by name ("object changes
  owner → provenance disappears") — target semantics explicitly forbid this (OBJ-01's own
  identity ≠ ownership split means provenance, owned by History/Provenance and keyed to the
  object's own identity, must never be silently keyed to its current owner instead).

**Rules invoked:** OBJ-01, PROP-01, CAUSE-01, HP-02, RES-06 (analogously), INFO-01/02, LAW-02,
CULT-01/02/04, PLACE-02 (generalized), PROG-06, ID-05, STR-01/EFF-02 (magic-supernatural, for
the ≠-magical-artifact distinction).

**Repository realization (corrected 2026-09-22 per a targeted follow-up review):** SUPPORTED
for stage 1 — `ItemInstance` (Batch 08's own evidence) already separates object identity from
ownership correctly, a real, positive structural match for this trajectory's own foundation.
**For provenance accumulation itself (stage 3), the classification is PARTIAL/INERT-OFF, not
MISSING** — Batch 08's own already-established evidence found `ItemInstance` carries real
history/provenance machinery that is feature-gated and never triggered in production; the
mechanism exists but is dormant, which is a materially different fact from "does not exist."
MISSING remains the correct classification only for stages 4–6 (provenance-to-record,
record-to-cultural-meaning, and meaning-to-differential-treatment) — no mechanism of any kind
connects even an *active* provenance chain to cultural meaning or later differential treatment.

---

## FI-OBJ-02 (counter) — Provenance Lost, Rediscovered

An object with real accumulated provenance loses its record entirely (a fire destroys an
institutional archive, the only witnesses die); the object persists as an ordinary item; much
later, new evidence (an inscription, a matching record found elsewhere) reconnects the object
to its original history.

- **Current authoritative state (loss):** the object's own OBJ-01 identity persists unchanged;
  the *record* of its provenance is destroyed — History/Provenance's own HP-03 (persistence is
  bounded by an honestly declared reach) applies directly: the provenance chain's own declared
  reach was exactly as far as the surviving records, and no further.
- **Rediscovery:** new evidence creates a fresh information path (INFO-01) connecting the
  object's own persistent identity to the historical fact that never stopped being true.
- **Result — the critical distinction (§27):** the **past fact is unchanged**; only **current
  significance** changes, the moment the new information path completes. This is a strong
  History ↔ Knowledge ↔ Culture integration test, and it passes: HP-01 (historical continuity
  survives ordinary change) plus KNOW-01/02 (belief revises only through a declared process)
  together already fully support rediscovery without needing a new Rule — belief/significance
  may be revised upward by new evidence exactly as it may be revised downward or corrected by
  any other evidence, per the same mechanism.

**Repository realization (corrected 2026-09-22):** MISSING for a loss-and-rediscovery
*mechanism* specifically — nothing currently models an archive being destroyed or new evidence
resurfacing. This is distinct from FI-OBJ-01's own corrected finding that `ItemInstance`'s
underlying provenance machinery is PARTIAL/INERT-OFF rather than absent; loss-and-rediscovery
is a further mechanism this repository has not attempted at all, on top of that dormant one.
No Rule gap either way: HP-03 + INFO-01 + KNOW-01/02 already compose to fully support this without any
addition.

---

## FI-PLC-01 — Ordinary Place → Historic/Culturally Significant, With Multiple Simultaneous Interpretations

A location hosts a consequential event (a battle); the Place's own history persists; multiple
factions and a neutral historian attribute different meanings to the same event; travel,
avoidance, ritual, and political reactions differ by attributor.

**Trajectory trace:**

1. **Initial state.** An ordinary Place with its own declared identity (PLACE-01), distinct
   from any Region, Settlement, owner, or occupant.
2. **Consequential event.** A battle occurs at this Place — a real causal event (CAUSE-01),
   which becomes part of the Place's own persistent history the instant it occurs (HP-01), owned
   by History/Provenance keyed to the Place's own PLACE-01 identity, which survives the battle
   regardless of any resulting damage (PLACE-03: identity continuity is the default outcome of
   any declared transformation).
3. **Attribution, not one fact.** Per PLACE-02 (significance is never intrinsic, always
   attributed by some specific actor/group/culture/institution, and different attributors may
   attribute conflicting significance to the same Place simultaneously): Faction A's own
   institution declares the Place a sacred victory site (INST-04: legitimacy/recognition is
   institution-declared); Faction B's own culture treats it as a site of tragedy/mourning
   (CULT-01/02); a neutral historian's own record states the factual event without either
   attribution (HP-01/02, kept as a third, independent record). **All three coexist without
   contradiction** — this is §28's own required test, and PLACE-02 alone already fully supports
   it with no new Rule needed.
4. **Objectively supernatural, kept separate.** Should this same Place also later acquire a real
   objective supernatural property (`supernatural-entities-places.md`'s PLC-01), that would be
   an eighth, independent fact from both factions' own cultural attributions — historically
   significant ≠ culturally sacred ≠ objectively supernatural remain three separately-
   representable facts throughout, per §14's own explicit requirement.
5. **Differential downstream reaction.** Faction A's pilgrims travel to the site (a real
   Movement/Navigation event, MOV-01/02, caused by that faction's own belief); Faction B's
   population avoids it (ENV/Movement, an avoidance decision caused by that faction's own
   attribution); the neutral historian's record has no travel consequence at all, only an
   informational one. *Consumer:* each specific population/institution with its own actual
   attribution — never "the world" reacting uniformly.

**Failure points:**

- **FP1 — forgotten (= FI-PLC-02).**
- **FP2 — one attribution dominates and suppresses the others** (a conqueror's institution
  erases the losing faction's own commemorative practice). This is representable as a real,
  declared causal event (an institutional act of suppression, CULT-04's own "suppression" as
  one of its named transmission-change causes) — not an automatic default, and not a gap.

**Rules invoked:** PLACE-01/02/03, CAUSE-01, HP-01/02, INST-04, CULT-01/02/04, MOV-01/02,
`supernatural-entities-places.md`'s PLC-01.

**Repository realization:** PARTIAL for Place identity/transformation persistence (`places.md`'s
own already-confirmed `PlaceState.prior_kind` evidence); MISSING for multi-attributor
significance representation (no relational `attributed-by` model exists — matches the already-
recorded Implementation Candidate from Batch 11A/11B's own review exports) and for any travel/
avoidance behavior actually keyed to attributed significance.

---

## FI-PLC-02 (counter) — Historically Significant Place, Forgotten, Then Rediscovered

A Place hosted a consequential event; the population that knew of it dies out or migrates away
with no record surviving; centuries later, archaeological/narrative evidence resurfaces.

- **Current authoritative state (forgotten):** the Place's own identity and the historical fact
  of the event both persist (PLACE-01, HP-01) — being forgotten changes no authoritative past
  fact, only removes the currently-active information path to it (HP-05: significance may
  legitimately fade, distinct from erasure or fabrication — the fact is never erased, only
  unattended).
- **Rediscovery:** new evidence re-establishes an information path (INFO-01), and current
  significance changes while the past fact remains exactly what it always was — the same
  History ↔ Knowledge ↔ Culture composition already confirmed sufficient in FI-OBJ-02, now
  confirmed at Place scale too.

**Repository realization:** MISSING, same pattern as FI-OBJ-02; no Rule gap.

---

## FI-LIN-01 — Family → Lineage → Descendant Consequence Without Automatic Inheritance

An individual becomes historically significant; generations later, a descendant's own
treatment changes as a specific, traceable causal consequence of that ancestry becoming known
— never automatically, never merely by biological descent.

**Trajectory trace:**

1. **Family/lineage structure.** FAM-01 (biological parentage, social parenthood, marriage,
   household co-residence, and lineage membership are distinct facts; none automatically
   implies affection, loyalty, inheritance eligibility, or legal authority) and LIN-01 (lineage
   membership conveys only the consequences explicitly defined for that relationship) together
   establish that mere biological descent, by itself, produces **no** automatic consequence at
   all — directly answering §15's own "ancestry ≠ automatic reputation" check.
2. **Ancestor becomes significant.** The ancestor's own trajectory follows FI-PER-01 above,
   independently of any descendant.
3. **The critical link — LIN-02.** "An ancestor's own historical significance may affect a
   descendant's later social treatment **only through a real, declared causal channel**." This
   Rule is the direct, already-existing answer to §15's entire required check — no new Rule is
   needed, and the Catalog explicitly forbids the shortcut §15 warns against (automatic
   inheritance of reputation).
4. **The channel, concretely.** A real channel might be: the descendant's own ancestry becoming
   known through a genealogical/institutional record (LAW-02, INFO-01) reaching a specific
   consumer (an institution granting or denying office per POL-01: political succession is
   distinct from kinship eligibility — a descendant is not automatically a legitimate successor
   absent a declared political rule connecting them, the direct authority-scale analogue of
   LIN-02). *Owner:* the reacting institution's own decision record — never the lineage itself,
   which owns only the ancestry graph (LIN-01), not any downstream social consequence.
5. **Descendant treatment changes.** A merchant extends or withholds credit because the
   descendant's ancestry is now known and matters to that merchant specifically (PROG-06's
   general pattern, applied one generation removed).

**Failure points:**

- **FP1 — ancestry never becomes known to the relevant consumer.** No channel completes; the
  descendant's treatment is unaffected. This is the correct default per FAM-01/LIN-01/LIN-02
  together — not a gap, the explicitly required default.
- **FP2 — ancestry known, but no institution or individual treats it as relevant.** The channel
  exists informationally but has no actual consumer; again, no automatic consequence — matches
  §15's own required check exactly.

**Rules invoked:** FAM-01, LIN-01, LIN-02, POL-01, LAW-02, INFO-01, PROG-06 (analogously).

**Repository realization:** PARTIAL — Batch 09's own already-confirmed evidence shows family/
lineage structural facts (FAM-01) are real and correctly separated from automatic consequence;
LIN-02's own declared-channel requirement remains MISSING in realization (no mechanism connects
a known ancestor's significance to any living descendant's own treatment) — but, as with every
other flagship trajectory here, this is a repository-realization gap, not a semantic one:
LIN-02 was purpose-built by Batch 09 to answer exactly this question and already does.

---

## FI-ORG-01 — Group → Organization → Institution, Persisting Beyond Member Turnover

A group of individuals forms a persistent organization; roles and history develop; every
founding member eventually leaves or dies; the organization's own institutional identity and
historical reputation persist regardless.

**Trajectory trace:**

1. **Formation.** ORG-01 (an organization's own identity persists independently of its current
   members' identities and membership composition) is the direct foundational anchor — the
   organization's own identity is established the moment it forms, not derived from its
   founders' own identities.
2. **Roles/rules develop.** INST-01 (organization, institution, and role/office are three
   distinct concepts) and INST-02 (delegated authority is distinct from capability and
   membership) together allow roles to persist independently of who currently holds them.
3. **Membership turnover.** ORG-02 (membership is distinct from loyalty, obedience, employment,
   role, and ownership) means a founding member leaving changes only the membership fact, never
   automatically erasing the organization's own history or the specific roles that member held
   (which INST-02's own delegation semantics keep separately trackable — a role may be
   reassigned without the organization's own identity or history being touched at all).
4. **Institutional history persists.** The organization's own accumulated historical record
   (battles fought, treaties signed, reputation earned) is owned by History/Provenance keyed to
   the organization's own ORG-01 identity — never keyed to any specific member, and therefore
   never disappearing when a member (even a founding or leading one) leaves. This directly
   answers §19's own named accidental-disappearance failure mode ("organization leader changes
   → institutional history disappears") — target semantics explicitly forbid it.
5. **Later actors react to the institution's own identity.** A rival faction's hostility, a
   client's trust, a regulator's oversight — all attach to the organization's own ORG-01
   identity (INST-03: authority/capability/power/legitimacy are correlated but not
   substitutable — an institution's own accumulated legitimacy is a real, separately-tracked
   fact), not to whichever individual currently leads it.

**Failure points:**

- **FP1 — dissolution before institutional identity solidifies (= FI-ORG-02).**
- **FP2 — a role's own authority does not survive occupant change**, unless AUTH-06
  (foundational: authority attached to a role/mandate may survive occupant change, only while
  that role/mandate remains valid) is satisfied — this Rule is the precise foundational anchor
  making member-turnover-survival possible at all; where a mandate itself lapses, authority
  legitimately ends too, and that is not a gap.

**Rules invoked:** ORG-01/02/03, INST-01/02/03, AUTH-06 (foundational), HP-01.

**Repository realization:** SUPPORTED for organization-identity-persists-independent-of-members
as a *structural* fact (Batch 10's own already-confirmed `FactionState` evidence: identity
persists across membership changes) — a genuinely positive match, not a gap. MISSING for any
mechanism connecting an organization's own accumulated historical reputation to later reactive
consumers (the same recurring gap, now confirmed at organization scale, consistent with Batch
10's own review export).

---

## FI-ORG-02 (counter) — Organization Collapses Before Institutional Persistence Forms

A small group forms, acts briefly, and dissolves (ORG-04: dissolution requires its own declared
process for identity continuity, asset/membership transfer, and history — none automatic)
before any role, rule, or historical reputation has time to solidify independently of its
founding members.

- **Current authoritative state:** ORG-01's own identity-persistence claim never gets tested
  against a real turnover event, because none occurs before dissolution.
- **Result:** the group's brief history persists as an ordinary historical fact (HP-01) but
  produces no institutional-persistence trajectory — confirming §25's own named counter-example
  ("organization collapses before institutional persistence") is already representable: ORG-04
  governs dissolution explicitly, and nothing forces every organization to reach institutional
  maturity.

---

## FI-SET-01 — Settlement Historical Trajectory: Growth, Institutions, Disaster, Decline, Place Persistence, Resettlement

A small settlement grows economically and socially, develops institutions, suffers a disaster
or conflict, declines and is abandoned, yet the underlying Place persists and is later
resettled or culturally remembered — the strongest available whole-catalog persistence test,
per §17's own framing.

**Trajectory trace:**

1. **Growth.** SETT-02 (settlement growth/decline requires a real, declared causal path
   connecting population/resource/safety/hazard conditions to settlement-state change) governs
   the growth phase; any tier/scale value materialized must carry declared consequences
   (SETT-02's own explicit "never a bare incrementing counter" requirement).
2. **Institutions emerge.** ORG-01/INST-01 apply exactly as in FI-ORG-01 — a settlement-scale
   organization or institution (a council, a guard) forms with its own persisting identity.
3. **Disaster/conflict.** A calamity or war damages the settlement — a real causal event
   (CAUSE-01) with consequences owned by the domains it actually targets (Body for casualties,
   Environment for terrain/hazard change per `environment.md`'s own ENV-01/03, Resources for
   destroyed production per PROD-01/02).
4. **Decline/abandonment.** SETT-01 (a settlement's own status — active, temporarily
   depopulated, abandoned, ruined-former, resettled — may change independently of the
   underlying Place's own identity, which by default persists throughout per PLACE-03) is the
   exact Rule this stage requires. Settlement status ends; the Place does not, unless a
   transformation explicitly declares identity replacement (which SETT-01/PLACE-03 both
   require to be an explicit exception, never a silent default).
5. **What persisted, what ended (§17's own explicit question).** *Ended:* the settlement's own
   active status, its population, its currently-functioning institutions (unless those
   institutions themselves persisted elsewhere, per ORG-01, independent of this specific
   Place). *Persisted:* the Place's own identity (PLACE-03), the historical record of what
   happened here (HP-01), and — where a real information/cultural path exists — the Place's own
   attributed significance (PLACE-02) even while depopulated.
6. **Resettlement or remembrance.** SETT-03 (settlement transformation does not follow one
   universal linear progression — ruin → resettled is one legitimate declared transformation
   among several, never assumed automatic) governs any later resettlement; independently,
   pilgrimage/avoidance/ritual behavior toward the historically significant ruin (per FI-PLC-01's
   own pattern) may occur with no resettlement at all.

**Failure points:**

- **FP1 — Place identity itself is treated as ending with the settlement.** Explicitly forbidden
  by SETT-01/PLACE-03's own default; a domain must explicitly declare Place-identity-replacement
  as its own separate fact, never inferred from settlement abandonment alone. This is exactly
  the accidental-disappearance failure §19 warns against ("settlement abandoned → place identity/
  history disappears") — and it is explicitly, correctly forbidden by name.
- **FP2 — resettlement never occurs; the ruin remains permanently abandoned.** A fully legitimate
  outcome; SETT-03 never requires resettlement, only that *if* it occurs, it follows its own
  declared transformation semantics.

**Rules invoked:** SETT-01/02/03, PLACE-02/03, ORG-01/INST-01, CAUSE-01, ENV-01/03, PROD-01/02,
HP-01.

**Repository realization:** SUPPORTED for the Place-persists-through-settlement-status-change
core (`PlaceState.prior_kind`/`transformed_tick`, already-confirmed Batch 11A evidence — this is
a genuinely strong, already-realized piece of exactly this trajectory, not a gap). MISSING for
settlement-scale institutional persistence independent of the settlement's own active status,
and for cultural-remembrance-without-resettlement.

---

## FI-X-01 — Cross-Domain Power Conversion Sampling

Per §18, four sampled conversion edges, each traced against source owner / mechanism / target
owner / reach / cost / downstream consumer, confirming the Catalog supports concrete conversion
paths without a generic `Power` framework.

| Edge | Source owner | Conversion mechanism | Target owner | Reach | Cost/conditions | Downstream consumer | Rules |
|---|---|---|---|---|---|---|---|
| Wealth → equipment → capability | Ownership/Possession (PROP-01) | A declared purchase/crafting transaction (EXCH-01: value/price/cost/wealth are four distinct facts) | Objects (equipment identity, OBJ-01) then Capability/Progression (PROG-01, once equipped) | Economic reach (must have access to a seller/market) | Price paid, per EXCH-01 | The wielding individual's own future capability checks | PROP-01, EXCH-01, OBJ-01, PROG-01 |
| Knowledge → better decisions → economic advantage | Knowledge/Belief (KNOW-01) | A real decision informed by that knowledge (AGENCY-01: decision stages causally distinct) | Ownership/Possession or Resources (whatever the decision's own commit path targets) | Requires the knowledge to actually be held by the decider — no silent omniscience (PERC-01) | The decision's own declared cost, if any (COST-01/02) | Whoever the decision affects | KNOW-01, AGENCY-01, COST-01/02 |
| Office → authority → resource access | Roles/Institutions (INST-01, the office itself) | A declared delegation (INST-02: delegated authority is distinct from capability/membership) | Resources/Production (access rights) | Institutional/jurisdictional reach (LAW-03: scope is declared, never universal by accident) | Whatever the office's own mandate declares | Anyone the office-holder authorizes | INST-01/02, LAW-03 |
| Magic capability → political consequence | Magic Capability (magic-supernatural's own MCAP-01) | A real declared supernatural effect (magic-supernatural's own EFF-01: magic is never the canonical owner of every downstream effect) reaching Authority/Organizations | Roles/Institutions or Organizations (INST-03: power/authority correlated, never substitutable) | Whatever reach that specific supernatural mechanism declares (magic-supernatural's own MCAP-02) | Whatever cost/resource that mechanism declares | The reacting institution/faction | magic-supernatural's own MCAP-01/02, EFF-01, INST-03 |

**Result:** all four edges are already fully derivable from existing Rules (§4 category A) —
none required a new cross-domain Rule. PROG-07 (foundational: "different forms of effective
power do not automatically convert into each other; each conversion edge requires its own real,
declared mechanism") is the single foundational Rule that already generalizes over every row
in this table; no edge is ever automatic, and each row's own "conversion mechanism" column is
exactly the "own real, declared mechanism" PROG-07 requires.

**Repository realization:** PARTIAL for wealth→equipment→capability (Batch 08's own
`ResourceTransferIntent`/`ItemInstance` evidence is real); MISSING for the other three edges'
own full chains, though each edge's own component Rules (INST-01/02, LAW-03, magic-supernatural
MCAP-01/02/EFF-01) are individually confirmed MISSING or PARTIAL by their own prior batch's
review export, not newly discovered here.

---

## FI-X-02 — Aggregate ↔ Individual Feedback (One-Way-Only Check)

Tests §21's own required feedback-loop check across two sampled directions.

**Direction 1 (individual → aggregate → individual, full loop):** an individual's own resource
extraction contributes to regional scarcity (ECOL-04: aggregate pressure may feed back into
individual decision/behavior through a real causal path — the aggregation half); that regional
scarcity then creates a new individual economic opportunity or hardship for a *different*
individual (PROD-02: scarcity is a fact about real availability, distinct from price/value/
desire — the feedback half). **Both halves are governed by already-existing Rules** (ECOL-04
explicitly, PROD-02 by direct application) — the loop is not one-way by construction.

**Direction 2 (individual action → organization reputation → individual opportunity/
constraint):** an individual's action changes an organization's own reputation (ORG-03: an
organizationally-attributed change requires a real execution/commit path — attributing one
member's act to the whole organization's reputation is itself a declared step, never
automatic); the changed reputation then creates or removes opportunity for a *different*
individual dealing with that organization (INST-03/04's own correlated-but-not-fixed
authority/legitimacy/reputation relationship). **Also fully derivable** — no one-way-only
system is implied by existing Rules; whether any specific repository implementation is
one-way-only is a separate, repository-scoped question (see Repository Reality Check below),
not a Rule gap.

**Result:** confirms §21's own required check passes as a target-semantic matter — the Catalog
never structurally forecloses feedback in either sampled direction; it only requires the
feedback, like every other causal step in this Catalog, to be its own real, declared mechanism
rather than automatic.

**Repository realization:** PARTIAL for Direction 1 (`ECOL-04`'s own already-confirmed
aggregate-to-individual feedback mechanism is real per Batch 05's own evidence; the reverse,
individual-extraction-to-aggregate-scarcity, is the half more likely realized via ordinary
resource accounting, though not independently re-verified here). MISSING for Direction 2's own
full loop (no mechanism attributes one member's act to organizational reputation, per Batch
10's own already-confirmed finding).

---

## FI-X-03 — Local vs. Global Significance Scope Comparison

A single comparison table testing §29's own explicit requirement that significance not form a
monotonic universal ladder.

| Subject | Scope of recognition | Unaware parties | Rules that already support this without collapse |
|---|---|---|---|
| Local hero (FI-PER-01's own individual) | One settlement + immediate faction | Neighboring settlements, other factions | REACH family (foundational) — recognition requires reach, and reach is never assumed universal |
| Regional threat (FI-CRE-01's own creature) | Settlements/organizations within the creature's own actual range of consequence | Distant settlements never affected | TERR-02 (control/reach is real only through a declared causal requirement) |
| Faction enemy | Specifically the opposing faction(s) | Neutral or unrelated factions | ORG-03 (organizationally-attributed reactions require their own real commit path — a rival faction's hostility never automatically becomes every faction's hostility) |
| Religious saint (a person whose sacredness a specific culture/institution declares) | That culture/institution's own adherents | Other cultures, who may never have heard of this person at all | `collective-belief.md`'s own reclassified sacredness entry (originally BEL-03) — sacredness is always attributed by a specific attributor, never universal |
| Continent-wide legend | The largest scope this Catalog samples — still requires a real, if long, information-propagation chain, never a single "everyone knows" shortcut | Isolated populations with no actual information path, however unlikely | INFO-01/02 + REACH family — even the largest-scope case still composes from the same declared-path discipline, just with more links |

**Result:** confirms no monotonic ladder is implied — a subject may occupy any of these scopes
independently of the others, and moving from local to a wider scope is never automatic; it
requires exactly as many additional real information-propagation links as the actual distance
being crossed, per REACH-05 (foundational: mediated reach means reach through explicit
intermediary links, each with its own constraints and failure modes) — REACH-05 alone already
fully generalizes over every row in this table, including the "continent-wide legend" case,
without treating it as qualitatively different in kind from the "local hero" case.

---

## Cross-scenario summary

**Corrected 2026-09-22 per a targeted follow-up review** — an earlier version of this summary
claimed every trajectory dead-ends at exactly one of two points, which collapsed
target-semantic completion together with current repository realization. Kept separate:

**At the target-semantic level**, across all 12 flagship/counter scenario groups (FI-PER,
FI-CRE, FI-OBJ, FI-PLC, FI-LIN, FI-ORG, FI-SET, FI-X), every trajectory that legitimately stops
short does so at one of two points: **(1) no information path is declared to exist**, or
**(2) a downstream consumer exists informationally but never actually reacts** — both
legitimate defaults, never gaps. No trajectory failed because of an actual Rule contradiction,
and no trajectory required a new cross-domain Rule to complete — see the Final Integration
review export's own Rule Gap Admission accounting for the full disposition.

**At the current-repository-realization level**, the picture is not uniform, and this summary
does not claim it is: the *consistently shared late-stage* gap, confirmed here at person,
creature, object, place, lineage, and organization scale (six of the seven subject types
listed in §3, settlement being the seventh and itself dependent on the same underlying gap via
its own institutions), is the absence of a complete history → propagated recognition →
consumed reaction chain. This coexists with real, partial upstream realization that differs by
domain — most notably, object provenance is PARTIAL/INERT-OFF (a real, feature-gated
`ItemInstance` mechanism, not an absent one; see FI-OBJ-01's own corrected finding), not
MISSING like most of the other upstream stages. Additional domain-specific realization gaps
(individual-creature differentiation, settlement-scale institutional persistence, lineage
declared-channels) remain classified in their own originating batches rather than restated
here. Nothing in this Final Integration pass supersedes any previously established
CONFLICTING finding from a prior batch (see the review export's own Rule Contradictions
section) — this pass's own scenarios simply did not re-exercise those specific mechanisms.
