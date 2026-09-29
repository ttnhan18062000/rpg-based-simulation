---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated evidence snapshot supporting `docs/plans/systemic_world/roadmap.md`, copied from the local working file `rpg-core-investigation-synthesis-recognition-standing.md` on 2026-09-27. Where the roadmap has since corrected a claim, the roadmap is authoritative.

# Synthesis — Recognition/Standing: One Shared Architecture or Five Mechanisms?

**Question:** How should an entity's accumulated lived history become recognized by specific
observers and institutions, and how should that recognition change future world reaction and
opportunity? Are entity notability/naming, gossip/knowledge propagation, organization-specific
standing, reputation-sensitive opportunities, and wealth/reputation/office leverage independent
mechanisms, or different downstream realizations of one shared architecture?

**Method:** Synthesis over Pass 1 + Pass 2's existing evidence, plus three targeted direct-code
verifications not covered by either pass (`ReputationUpdateService`, `PublicReputationProfile`,
`KnowledgeModelService`) — not a new broad investigation. No canonical Rule text modified; no
implementation begun.

---

## 1. The minimal causal model

Refining the requested chain against what the repo actually distinguishes today:

```
[1] OBJECTIVE HISTORY        the event happened — entity-owned fact
      ↓
[2] RECORDABLE EVIDENCE      something in the world that COULD be perceived/known about it
      ↓
[3] INFORMATION PROPAGATION  evidence reaches a potential knower (perception, rumor, record)
      ↓
[4] OBSERVER/INSTITUTION BELIEF   a specific other subject or institution now holds a fact about it
      ↓
[5] STANDING                 that belief becomes a durable, THIS-OBSERVER'S-OWN view of the entity
      ↓
[6] REACTION                 standing is consulted at a decision point (access/hostility/trust/price)
      ↓
[7] LEVERAGE / CONVERSION    a reaction of one kind becomes usable for another declared purpose
      ↓
[8] CHANGED OPPORTUNITY      the entity's own future opportunity set differs as a result
      ↓
[9] FURTHER TRAJECTORY       feeds back into Pass 1's decision pipeline
```

The distinctions the user asked to preserve map cleanly onto this: objective history = [1];
information about the history = [2]-[3]; an observer's belief = [4]; social reputation / derived
notability = views computed over [5]; institution-specific standing = [5] scoped to an
institution-as-observer; political/economic leverage = [7].

---

## 2. What already exists, edge by edge

| Edge | Status | Evidence |
|---|---|---|
| [1] Objective history | **LIVE** | `TurningPointState`, death/lineage/displacement, `grudge_history` (Pass 1, Pass 2) |
| [2] Recordable evidence | **Mixed/PARTIAL** | Some events leave a trace on the *directly involved* parties only (`grudge_history` on the victim, `PublicReputationProfile` on the actor) — no general "this happened observably" record independent of the direct participants. Causal Memory domain exists but `INERT-OFF` (Pass 1). |
| [3] Information propagation | **Mostly MISSING, but not architecturally absent** | `BeliefCycleSystem.process_rumor()` exists, region-trauma scoped only (Pass 2). Separately — **new this synthesis** — `InformationProvider → KnowledgeModelService` (`src/cognition/knowledge_model.py`) is a real, live, *correctly architected* propagation pipeline with an explicit stated invariant: "Hidden world truth is NEVER injected. Only what the provider returned is assimilated. This preserves information opacity." It has simply never been fed anything about *other entities'* histories — it only carries world-facts (locations, quests) today. `ReputationUpdateService.process_witnessed_event()` (`src/domains/commitment/reputation.py:15`) is **not genuine propagation** — called directly from `quests.py:227` with only `(profile, event_kind)`, no observer parameter, no perception check, unconditional the instant a quest event resolves. |
| [4] Observer/institution belief | **The right machinery exists, unused for this purpose** | `KnowledgeModelService` is per-entity, perception-gated, opacity-respecting — the correct shape — but has zero entity-reputation content flowing through it. `FactionSentiment` (`src/core/state.py:720`) is a real, directed, faction-to-faction relation, confirmed by this synthesis to have no individual-entity dimension at all — structurally the right *shape*, wrong *scope*. |
| [5] Standing | **MISSING as a directed record; a wrongly-shaped substitute exists** | No per-(institution, individual) or per-(observer, individual) standing field exists anywhere (`IP-S17`, Pass 2, re-confirmed). `PublicReputationProfile`/`public_reputation` (`src/core/cognition.py:502-504`) is the closest existing thing — but it is a **single global scalar + label map owned by the subject**, read directly by every consumer (`shop.py`'s discount, `appraisal.py`'s trust computation, birth-seed inheritance, campaign social_memory, replay fingerprinting) as objective, omniscient truth. This is the exact same shape of defect this session already found and named for `TERR-01`'s `owner_faction_id`: one shared field forced to serve what should be several independently-diverging relations (how *this* guild sees the entity vs. how *that* rival sees the entity are collapsed into one number). |
| [6] Reaction | **PARTIAL, consulting the wrong-shaped input** | Real reactions exist (`shop.py` discount, `appraisal.py` trust, nemesis targeting) — but they read either the globally-omniscient `public_reputation` or the narrow, personal-only `nemesis_ids`/`grudge_history`, never a genuine per-observer/per-institution standing. |
| [7] Leverage/conversion | **MISSING, three independent paths** | `ME-S12`, `politics-authority.md` — Pass 2's central finding, unchanged. |
| [8] Changed opportunity | **MISSING as an input category** | `opportunity_providers_contract.md`'s `RequirementsFilter` is a closed list (inventory/skill/faction/quest-state), never reputation/standing (Pass 2). |
| [9] Further trajectory | N/A — outcome measure, not an edge to verify. |

---

## 3. The first shared missing edge

Not [3] (propagation machinery genuinely exists, just unused for this content) and not really "no
notability concept" (that's a *symptom*, not the root). The earliest true break is **[5] —
a directed, observer-relative standing record about a specific other entity.**

Two things already exist in exactly the right *shape* for this, at the wrong *scope*:
- `FactionSentiment` — directed, relative, per-target — but faction→faction only.
- `KnowledgeModelService` — per-entity, opacity-respecting, perception-gated — but never carries
  entity-reputation facts.

One thing exists that looks like reputation but is the wrong *shape* entirely: `public_reputation`
— subject-owned, global, read as omniscient ground truth by every consumer, with no observer
dimension at all. This is not a missing mechanism to add to — it's an architectural mismatch to
route around, the same way `TERR-01`'s finding didn't ask for a new field, it asked for the existing
one to stop being asked to serve incompatible roles at once.

**This directly answers the user's framing question: the five Pass-2 findings are not five
independent mechanisms. They are five different downstream consumers of one shared, currently-
missing primitive** — a directed `(observer_id_or_institution_id, subject_entity_id) → standing`
record, propagated through the same perception/opacity-respecting pipeline `KnowledgeModelService`
and `FactionSentiment` already establish as this repository's pattern for relational, non-omniscient
state. Not a global notability score. Not a new propagation mechanism. Not a new conversion-edge
framework — `politics-authority.md`'s own Rule already states conversion edges must stay specific
and declared, and this synthesis found no reason to revisit that.

---

## 4. Authoritative state vs. derived views

- **Authoritative (new):** the directed `(observer, subject) → standing` record itself. Its exact
  fields (trust? hostility? notoriety-as-this-observer-sees-it?) are deliberately **not decided
  here** — that's implementation/Rule-drafting work, out of this synthesis's scope.
- **Authoritative (existing, unchanged):** `TurningPointState` and the rest of Pass 1's objective
  history — the source the standing record would be *derived from* via propagation, never
  duplicated by it.
- **Derived, not authoritative:** any global "notability" or "epithet" the user's original
  instruction was right to be suspicious of — these should be *views* computed by aggregating
  directed standing records (e.g., "how many distinct observers hold a strong view, in which
  direction"), never themselves the stored fact. `public_reputation` being global *and*
  authoritative, instead of a derived rollup over directed records, is precisely the mistake this
  synthesis found already made once.
- **Derived, not authoritative:** leverage/conversion outcomes (protection, political influence,
  trusted-contract access) — computed at the moment a specific declared edge fires, consuming
  standing as an input, never new persistent state of their own. Matches `politics-authority.md`'s
  existing Rule exactly.

---

## 5. Which Pass-2 gaps become ordinary implementation candidates once the bridge exists

Once a directed `(observer/institution, subject) → standing` primitive exists and is wired into the
existing propagation pipeline:

- **Entity notability/naming** → a derived-view task (aggregate standing records into a display
  score/epithet), not architecture design.
- **Gossip/knowledge propagation about a specific entity** → extend the *existing, correctly-shaped*
  `InformationProvider → KnowledgeModelService` pipeline to carry entity-standing facts — an
  extension of already-correct machinery, not new architecture.
- **Organization-specific standing (`IP-S17`)** → an institution is just another `observer_id` in
  the same standing-record shape — no separate mechanism needed.
- **Reputation-sensitive opportunities** → add a fifth `RequirementsFilter` category reading the
  relevant standing record — a bounded, already-scoped implementation task.
- **Wealth/reputation/office → leverage (`ME-S12`, `politics-authority.md`)** → concrete, declared
  conversion-edge implementation work that *consumes* standing as one input, exactly matching the
  Rule's own existing "specific, declared edge" requirement.

None of these require new architectural investigation once the one shared primitive lands — they
become ordinary implementation tickets.

---

## 6. Remaining genuine World Rule ambiguity

**Mostly none — consistent with both passes' own conclusion.** The general principle this synthesis
leans on (information must be perception/knowledge-mediated, never omniscient) is already Catalog
law (Batch 06's Agency/Decision framing), and the *pattern* of modeling relations as directed and
specific rather than global (`SOC-01`'s structural/subjective split, `FactionSentiment`'s own
directed shape, `TERR-01`'s seven-relation-type distinctness) is repeated enough across the frozen
Catalog to call this **already covered by composition**, not a new semantic gap.

**One real open question, flagged rather than resolved:** no existing Rule *explicitly* states that
social standing/reputation specifically must follow this same directed, perception-mediated pattern
— it's a strong inference from composing several existing Rules (`SOC-01`, `AGENCY-02`, `KNOW-01/02`,
plus the directed-relation modeling precedent), not something any single Rule says outright. This is
exactly the kind of composition the Catalog's own discipline would rather have traceable than
implicit. Recommend: if/when a real ticket touches this area, cite this composition explicitly (an
Inherited entry, not a new Rule ID) rather than leaving it as an assumption — a small, low-stakes
documentation action, not a blocker to anything else in this synthesis.

---

## Recommendation for routing (Option C, unchanged)

This synthesis does not add a new Catalog action beyond what Pass 1/Pass 2 already recommended — it
reorganizes their five separate "further investigation" items into one shared prerequisite. The
practical effect: whoever picks up "entity notability" (Pass 1 Rec. #1 / Pass 2 Rec. #1) should scope
it as *this* directed-standing primitive specifically, not a notability/epithet system in isolation
— everything else in both reports' findings lists becomes a consumer of it, not a parallel gap to
solve separately.
