---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Organizations

**Purpose/scope.** What makes a group of individuals a persistent collective subject rather
than merely a set of individuals who happen to interact, and what a collective subject's own
action requires beyond individual desire. Does not decide institutional roles/offices (see
`roles-institutions.md`), political succession (see `politics-authority.md`), or law/
enforcement (see `law-enforcement.md`).

**Standing direction (2026-09-22, `tmp/world-rule-direction.md`).** Applied from this batch
onward: Rule statements below describe only target world semantics, independent of current
repository realization. Repository classification (SUPPORTED/PARTIAL/CONFLICTING/MISSING/
INERT-OFF) records how the current implementation relates to the target, never a delivery
priority — MISSING is not a feature requirement, and a Rule may be fully valid while its
implementation remains deferred indefinitely. Where a Rule permits rather than requires a
behavior, this is stated explicitly.

**Status.** Batch 10 (Organizations/Institutions/Politics/Law), first draft, per
`tmp/world-rule-batch-10-ext-ai.md`. Structured per the normalized five-category methodology,
plus a non-binding Implementation Candidates section per the standing direction above.

---

## Domain Rules

## ORG-01 — An organization's own identity persists independently of its current members' identities and of membership composition

> An organization — a persistent collective subject formed by a group of individuals — has its
> own identity, distinct from the identity of any member, founder, or leader. Membership
> changing, including the departure or death of a founder or every original member, never by
> itself destroys or recreates the organization's own identity. Whether an organization's
> identity ends is a question its own declared lifecycle answers (see ORG-04), never an
> automatic consequence of who currently belongs to it.

**Disposition: ACCEPT — REQUIRED.** The target simulated world cannot support persistent
collective actors (guilds, armies, merchant houses, factions) without this — without it, every
membership change would risk being indistinguishable from the organization's own death. Passes
the admission test: Batch 01's ID-06 named organizations as a domain that would need this kind
of identity-continuity treatment but explicitly deferred drafting it; this Rule is the first
statement of that content, not a restatement.

**Repository evidence: SUPPORTED, by construction, for two independent organizational
subjects.** `FactionState` (`src/core/state.py`) is keyed by its own `faction_id: str`, with no
member-entity-identity field anywhere in its own shape — a faction's own state (`territory`,
`resources`, `diplomatic_relations`, `military_strength`) exists and is addressed independently
of any individual entity. `ClanState` is likewise keyed by its own `clan_id`, and its own
`leader_entity_id` is explicitly a *replaceable* pointer, not the clan's own identity —
`ClanLifecycleService.process_succession()` replaces a dead/inactive leader with a new member's
id while `clan_id` itself never changes, and `process_dissolution()` only ends the clan when
*both* membership and assets are empty, never merely when the founder or leader is gone.

**Scenarios:** [IP-S01](../scenarios/institutions-politics-batch-10.md#ip-s01) (founder dies,
organization persists), [IP-S02](../scenarios/institutions-politics-batch-10.md#ip-s02) (member
leaves, organization persists).

---

## ORG-02 — Membership is a distinct fact from loyalty, obedience, employment, legal citizenship, functional role, and ownership; none is automatically implied by any other

> Belonging to an organization is its own fact, separate from whether the member is loyal to
> it, obeys its directives, is employed by it, holds legal citizenship through it, occupies any
> particular functional role within it, or owns any of its resources. A member may disagree,
> disobey, betray, leave, hold relationships that conflict with membership, or (where the
> organization's own rules permit) belong to more than one organization at once. Membership
> is never, by itself, a universal override of a member's own decision-making.

**Disposition: ACCEPT — REQUIRED for the distinctness; the multi-membership/disobedience
possibilities themselves are PERMITTED, not required of every organization.** Passes the
admission test: no earlier Rule states this specific six-way distinction for the concept of
membership — the closest existing content, Batch 09's FAM-01, drew an analogous multi-way
distinction for family-structural facts, but membership in a voluntary/institutional
organization is a genuinely different fact pattern (a family fact is rarely revocable by the
member; organizational membership routinely is).

**Repository evidence: PARTIAL.** Nothing in this repository automatically derives loyalty,
obedience, or resource ownership from membership itself — `ClanState.member_entity_ids` is a
bare set of ids, and `ClanLifecycleService.process_leave()` is unconditional (no appraisal
gate), confirming leaving requires no permission and membership does not by itself bind a
member's own choices. Multiple simultaneous organization kinds are real for the same entity
(a `Clan` membership, a `Group`/party membership, and a `Faction` affiliation may all apply to
one entity at once) — but multi-membership *within* the same organization kind is neither
positively modeled nor explicitly forbidden: `ClanLifecycleService.find_clan_id_for_entity()`'s
own reverse lookup returns the first clan found in sorted order and would silently mask a
second membership if one ever existed, since nothing prevents constructing one.

**Scenarios:** [IP-S03](../scenarios/institutions-politics-batch-10.md#ip-s03) (member
disobeys), [IP-S19](../scenarios/institutions-politics-batch-10.md#ip-s19) (conflicting
memberships).

---

## ORG-03 — An organization's own action requires a valid collective decision mechanism, an authorized actor or process to execute it, and a resulting committed action; collective desire alone never directly changes world state

> For a proposition of the form "the organization decided/did X" to be valid, a real chain must
> hold: some collective or institutional state produces a decision through a valid mechanism,
> an authorized actor or process carries it out, and a committed action results. An
> organization's own goals, pressures, or priorities are legitimate coarse-grained inputs to
> this chain — organizations need not share individual agents' own cognition architecture — but
> they are never, by themselves, sufficient to change world state without an executing
> mechanism in between.

**Disposition: ACCEPT — REQUIRED.** This is the "Hybrid Agency" principle the batch instruction
locks for collective subjects, and it is genuinely new content: Batch 06's AGENCY-01/02
establish an analogous decision/execution distinction, but only for an *individual* agent's own
cognition; extending the same discipline to a *collective* subject (which may have no unified
cognition at all) requires stating what a valid collective decision chain consists of, which no
earlier Rule does.

**Repository evidence: PARTIAL — real for the resource-extraction side, absent for anything
resembling a deliberative collective decision.** `TownResolutionSystem`'s tax/maintenance pass
(`src/engine/town_resolution.py`) is a real, fully automatic collective-resource-state
transition (`state.global_resources`) with no per-decision authorized actor at all — it is a
declared systemic process, which satisfies "valid mechanism → committed action" without ever
needing an individual authorized actor, a legitimate instance of this Rule's own permitted
shape (a process, not necessarily a person, may be the authorized executor). No mechanism in
this repository resembles an organization *choosing among options* (a goal-weighing,
deliberative collective decision) — `FactionState.active_doctrines`/`military_strength`/
`tension_level` are read by `src/engine/faction_decision.py` as inputs to some downstream
process, which is evidence toward the "goals/pressures as coarse-grained inputs" half of this
Rule, though a full decision→authorization→execution trace through that file was not
exhaustively confirmed this batch.

**Scenarios:** [IP-S01](../scenarios/institutions-politics-batch-10.md#ip-s01),
[IP-S18](../scenarios/institutions-politics-batch-10.md#ip-s18) (organization wealth,
authorized vs. unauthorized spending).

---

## ORG-04 — Organization split, merger, or dissolution each require their own declared process to determine identity continuity, asset/control transfer, membership transfer, role continuity, and history; none is automatic

> When an organization splits, merges with another, or dissolves, a declared process — specific
> to that transition — must determine which resulting organization (if any) continues the
> original's identity, how control of assets transfers, how membership transfers, whether roles
> continue, and what happens to the organization's own history. No single universal answer
> applies to every case; each transition requires its own explicit semantics where a domain
> chooses to model it. This is a domain refinement of ID-06's own split/merge/succession
> deferral, specific to collective subjects.

**Disposition: ACCEPT — PERMITTED, with a REQUIRED procedural constraint.** Whether any
organization ever splits, merges, or dissolves is permitted, not required, of every
organization; but wherever a domain does model one of these transitions, this Rule requires
that a real, declared process determine the five listed facts, rather than any one of them
following automatically from the others. Passes the admission test: ID-06 explicitly deferred
"organizations & institutions" as one of the domains that would need its own split/merge/
succession semantics; this Rule is the first statement of that content, per the batch
instruction's own explicit framing ("one of the important domain refinements of ID-06").

**Repository evidence: MISSING.** No mechanism for faction or clan split, merger, or
succession-driven dissolution beyond `ClanLifecycleService.process_dissolution()`'s own
empty-membership-and-empty-assets condition exists anywhere in this repository — confirmed
directly via broad search for split/merge/dissolve terms across faction- and clan-related
modules. `ClanState.dissolved_tick` records that a clan *ended*, but nothing carries its own
history, remaining assets (there are none once dissolution's own precondition is met), or
membership forward to a successor organization. This is a load-bearing semantic gap, not a
present violation — the target requirement (a declared process must exist wherever this
transition is modeled) has nothing yet to check it against.

**Scenarios:** [IP-S09](../scenarios/institutions-politics-batch-10.md#ip-s09) (organization
split), [IP-S10](../scenarios/institutions-politics-batch-10.md#ip-s10) (organization merge).

---

## Inherited / Applied Foundational Rules

### An organization owns its own resources distinctly from any member owning them; a member's access to organizational resources requires its own declared authority

> An organization's own resources are its own fact, never automatically the personal property
> of any member. A member drawing on organizational resources requires a declared access or
> authority grant connecting that member to that specific use — organizational ownership does
> not by itself grant every member unrestricted access.

**Disposition: INHERITED — direct reuse of Batch 01's OWN-01/OWN-02 (state ownership is a real,
singular fact; participation ≠ ownership) and Batch 02's AUTH-02 (authority is distinct from
ownership), applied to collective ownership specifically. No new claim beyond instantiating
these for an organizational owner rather than an individual one.**

**Repository evidence: SUPPORTED for organizational ownership as its own fact; MISSING for any
member-access/authority mechanism.** `state.global_resources` (a faction-keyed vault) and
`FactionState.resources`/`ClanState.asset_ids` are real, collectively-owned resource pools,
confirmed structurally distinct from any individual entity's own `inventory.gold`/`items`.
`TownResolutionSystem`'s taxation/maintenance pass is the *only* mechanism found that touches
`global_resources` — a fully automatic systemic process, never an individual member's own
authorized draw. No mechanism was found anywhere by which an authorized member spends from a
faction or clan's own pool. AUTH-02's own evidence (governance extracts tax into a vault without
becoming the owner) already establishes the ownership/authority-to-govern distinction generally;
this batch's own investigation adds that the *member-access* half of the pattern remains
unrealized.

**Scenarios:** [IP-S18](../scenarios/institutions-politics-batch-10.md#ip-s18).

### Organizational/institutional knowledge is distinct from any individual member's own knowledge, in both directions

> What an organization collectively knows or holds on record is not automatically known by
> every individual member, and what an individual member privately knows is not automatically
> known by the organization. Either direction requires a real, declared information path —
> observation, report, or record access — connecting the individual's own knowledge state to
> the organization's own knowledge state, or vice versa.

**Disposition: INHERITED — direct reuse of Batch 06's PERC-01 (perception bounded by declared
constraints, default of partiality) and KNOW-01/KNOW-02 (knowledge ≠ truth; belief does not
auto-resync), applied to an organization as a knowledge-holding subject rather than only an
individual one. No new claim beyond extending an already-settled boundary to a new kind of
subject.**

**Repository evidence: INERT/OFF, for the one real candidate mechanism found; otherwise
MISSING.** `ENABLE_INFORMATION_HUB_ACCUMULATION` (`src/domains/optimization/feature_flags.py`)
gates a real code path in `src/engine/quests.py` that would feed a completed quest's own
information toward some accumulation point — the flag defaults `OFF`, so this repository's one
concrete attempt at an individual→institutional information path exists but does not currently
run. No mechanism in the reverse direction (an institution's own record becoming a specific
member's own knowledge) was found at all.

**Scenarios:** [IP-S11](../scenarios/institutions-politics-batch-10.md#ip-s11) (law exists but
nobody knows — the law-specific instance of this same boundary, see `law-enforcement.md`).

### Institutional memory persists through member/occupant turnover via the organization's own declared record-keeping, never through an individual's own memory transferring automatically

> What persists when an individual leaves or dies is whatever the organization's own rules,
> records, policies, obligations, or claims declare persist at the organizational level — never
> a magical transfer of that individual's own personal memories into the collective.

**Disposition: INHERITED — direct reuse of the foundational History/Provenance family's HP-01
(historical continuity survives ordinary change) and Batch 09's SOC-03 (persistence occurs only
per declared semantics), applied to a collective subject's own persistence rather than an
individual's or a relationship's. No new claim: this is ORG-01's own identity-persistence claim
restated from the angle of *what specifically persists*, not a third principle.**

**Repository evidence: SUPPORTED for the negative claim (no individual-memory-to-institution
magic transfer exists); PARTIAL for genuine institutional record-keeping.** No mechanism reads
an individual entity's own `cognition.knowledge_model` and writes it into `FactionState`/
`ClanState` — confirmed by direct inspection, ruling out the "magical transfer" failure mode
this Rule forbids. What the organization itself durably retains is limited to its own declared
fields (`FactionState.diplomatic_relations`, `military_strength`, `tension_level`,
`ClanState.clan_reputation`) — real, but a narrow slice of the "rules, records, obligations,
claims" the batch instruction's own item 12 lists as candidates.

**Scenarios:** [IP-S20](../scenarios/institutions-politics-batch-10.md#ip-s20) (institutional
memory).

### An organization's relationship to another organization is its own domain-specific representation, never simply a reuse of individual-to-individual relationship fields

> Alliance, hostility, trade relations, obligation, or competition between two organizations is
> its own fact, represented independently of any individual member's own personal relationships
> — and is not required to exist merely because individual-scale relationship modeling exists.

**Disposition: INHERITED — direct reuse of Batch 05's ECOL-01/ECOL-02 (individual and aggregate
representations are distinct) and Batch 09's SOC-01 (structural relation vs. subjective
attitude), applied at organization scale. No new claim: this batch's own investigation found
the repository already satisfies this distinction by construction, which is itself confirming
evidence for an already-established pattern, not new content.**

**Repository evidence: SUPPORTED, cleanly, by construction.** `FactionSentiment`
(`src/core/state.py`) is explicitly documented as "a first-class directed faction-to-faction
relationship record," deliberately mirroring `SocialBond`'s shape while omitting its `role`
field — `FactionState.diplomatic_relations` already plays the categorical role at faction scope
instead. The two representations (individual `SocialBond`, faction-to-faction
`FactionSentiment`) are confirmed structurally separate, non-overlapping fields, exactly as
this Rule requires, and the docstring shows this was a deliberate design choice rather than an
accident.

**Scenarios:** none newly traced; confirmed by direct code inspection of the field
definitions themselves.

### Membership does not determine action; conflicting obligations from multiple memberships are resolved through the member's own decision-making layer, never automatically

> Where an individual holds memberships in two organizations whose obligations conflict, which
> obligation is honored is resolved by the individual's own decision-making process — weighing
> both as inputs — never automatically by a fixed membership-priority rule the world imposes
> unconditionally.

**Disposition: INHERITED — direct reuse of Batch 06's AGENCY-01/AGENCY-02, applied to
multi-membership conflict specifically. No new claim beyond ORG-02's own "membership is never a
universal behavior override" restated for the specific case of two memberships conflicting.**

**Repository evidence: MISSING, for any positive multi-organization-conflict mechanism —
consistent with ORG-02's own finding that multi-membership within one organization kind is
unmodeled.** No scenario was found in which one entity's simultaneous `Clan` and `Group`
memberships (the one confirmed-real multi-membership case) produce a conflicting obligation
that any decision system resolves — the two membership kinds were not found to issue
conflicting directives to the same entity anywhere in the current implementation.

**Scenarios:** [IP-S19](../scenarios/institutions-politics-batch-10.md#ip-s19).

---

## Scope / Deferred Boundaries

### Concrete membership-formation and departure event catalog

> This family states that membership is a real, distinct fact (ORG-02) but does not design the
> concrete catalog of qualifying join/leave events, conditions, or ceremonies for every
> organization kind — that remains implementation-level content, per this family's own scope.

**Disposition: SCOPE BOUNDARY.**

### Concrete resource-allocation policy catalog

> This family states that member access to organizational resources requires a declared
> authority (Inherited, above) but does not design the concrete catalog of access rules,
> spending limits, or allocation policies any specific organization might use — deferred, per
> this family's own scope.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority — MISSING/INERT-OFF here means only "not currently realized," per the standing
direction above.**

- **A significant, notable finding: two structurally separate "faction" representations exist,
  deliberately bridged, not accidentally duplicated.** The legacy `Faction` IntEnum
  (`src/core/enums.py`: `HERO_GUILD`, `MONSTER_HORDE`, `TOWN_COUNCIL`, `NEUTRAL` — four fixed
  values, used for `entity.identity.faction`, `region.owner_faction_id`, and the
  `global_resources` vault keys) is a small, closed affiliation tag, while `FactionState`/the
  content-catalog `faction_id` string (E53) is a rich, open-ended per-faction durable state
  (territory, diplomacy, tension). `src/content_semantics/faction.py`'s own
  `get_legacy_faction_bucket()` explicitly converts the open-ended catalog id into one of the
  four legacy buckets — a real, already-resolved compatibility shim between the two, the same
  shape as Batch 09's own resolved `public_reputation`-vs-`labels` naming-collision finding.
- **This repository already uses the word "role" for at least three unrelated concepts.**
  `SocialBond.role` (a `RelationshipRole` like `FRIEND`, Batch 09 evidence), `GroupRecord.roles`
  (an entity-keyed combat/functional role like a tactical position, read by
  `src/engine/tactical.py`), and this batch's own institutional "role/office" concept
  (`roles-institutions.md`) are three separate namespaces sharing one English word — worth a
  future author's attention before assuming any two of them are the same field.
- **Confirmed MISSING — no per-(organization, specific individual) standing exists.**
  `FactionSentiment` is faction-to-faction only; `SocialBond` is individual-to-individual only;
  no field anywhere tracks a faction's or clan's own standing toward one *named* individual
  distinct from that individual's population-wide `public_reputation` scalar. This is the
  organizational analogue of the "ordinary individual becomes historically significant" gap
  already found in Batches 07/09.
- **Confirmed MISSING — no organization split/merge mechanism exists.** See ORG-04 above.
- **Confirmed MISSING — no authorized-member-access path to collective resources exists.** See
  the resource-ownership Inherited entry above; preserved in more detail under Implementation
  Candidates below.
- **Confirmed INERT/OFF — `ENABLE_INFORMATION_HUB_ACCUMULATION`.** See the organizational
  knowledge Inherited entry above.

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** a member's access to organizational resources requires its own declared
  authority (Inherited, above).
  **Current realization:** `state.global_resources` is touched only by
  `TownResolutionSystem`'s automatic tax/maintenance pass; no entity-initiated draw exists.
  **Gap/mismatch:** authorized-member access is entirely unrealized, not merely partial.
  **Possible implementation direction:** a declared spend-authorization check (e.g.,
  role/office-gated, per `roles-institutions.md`) before any entity-initiated draw from a
  faction or clan resource pool.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.
- **Target semantic:** an organization may accumulate standing toward one specific named
  individual, distinct from that individual's population-wide reputation (ORG's own knowledge/
  decision chain, cross-referenced from the "no per-organization individual standing" finding
  above).
  **Current realization:** no field or mechanism exists for this at all.
  **Possible implementation direction:** a per-(faction, entity) record analogous in shape to
  `FactionSentiment`, populated by a declared witnessed-event process paralleling
  `ReputationUpdateService`.
  **Implementation decision:** DEFERRED.

## Cross-domain links recorded here

- ORG-01, ORG-04 → Identity (ID-06, Batch 01 — the deferred split/merge/succession question this
  batch begins answering for collective subjects)
- ORG-02 → Family/Kinship (`social-lineage/family-kinship.md`'s FAM-01, Batch 09 — an analogous
  multi-way distinctness pattern, applied to a different kind of fact)
- ORG-03 → Agency/Decision (Batch 06's AGENCY-01/02 — the individual-scale analogue)
- Inherited resource-ownership entry → State Ownership (OWN-01/02, Batch 01), Authority
  (AUTH-02, Batch 02)
- Inherited knowledge entry → Perception/Knowledge (PERC-01/KNOW-01/02, Batch 06)
- Inherited institutional-memory entry → History/Provenance (HP-01, Foundational), Social
  Relations (SOC-03, Batch 09)
- Inherited org-relationship entry → Ecology/Population (ECOL-01/02, Batch 05), Social
  Relations (SOC-01, Batch 09)

## Open questions carried forward

1. Whether multi-membership *within* the same organization kind should ever be positively
   modeled or explicitly forbidden is an open design-semantic question, not decided here —
   `find_clan_id_for_entity()`'s own single-match assumption is a repository fact, not a Rule.
2. Whether "Organization" needs its own durable-state category distinct from "Institution" (see
   `roles-institutions.md`'s INST-01) is carried forward as an owner-attention question below.
