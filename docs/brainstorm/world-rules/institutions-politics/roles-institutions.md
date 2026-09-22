---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Roles / Institutions

**Purpose/scope.** What distinguishes an organization, an institution, and a role/office from
one another; what makes a role persist independently of its occupant; and what authority,
capability, practical power, and legitimacy each mean and how they relate. Does not decide
organization-level identity/membership (see `organizations.md`), political succession (see
`politics-authority.md`), or law/enforcement (see `law-enforcement.md`).

**Standing direction (2026-09-22, `tmp/world-rule-direction.md`).** Applied from this batch
onward: Rule statements below describe only target world semantics, independent of current
repository realization. Repository classification records realization only, never delivery
priority.

**Status.** Batch 10 (Organizations/Institutions/Politics/Law), first draft, per
`tmp/world-rule-batch-10-ext-ai.md`.

---

## Domain Rules

## INST-01 — Organization, institution, and role/office are three semantically distinct concepts that must not be accidentally conflated, without requiring each to materialize as its own separate persistent-state object

> An **organization** is a persistent collective actor/group (see `organizations.md`'s ORG-01).
> An **institution** is a persistent role, rule, or authority structure that may outlive any
> particular organization that currently hosts it, or exist without a single organization ever
> having created it. A **role/office** is a specific, occupiable position within either. These
> are semantic distinctions, not a mandatory storage requirement: an organization may itself
> embody or host an institution and its roles without any of the three ever being materialized
> as a separately-tracked entity — a guild (organization) may simply *be* the thing whose
> guildmaster office (role) and governing customs (institutional semantics) live entirely
> within the guild's own state, with no separate "Institution" record anywhere. What this Rule
> forbids is treating the three concepts themselves as interchangeable — an institution
> outliving its hosting organization, or a role persisting past its occupant, are real
> possibilities the concepts must be able to express, whether or not a given implementation
> ever separately stores them.

**Disposition: ACCEPT — REQUIRED for the conceptual distinctness; separate materialization is
explicitly NOT required (revised 2026-09-22 per external follow-up review).** The original
wording risked being read as requiring three separate durable-state objects for every case.
The follow-up correctly distinguished a semantic distinction from a storage/entity-separation
requirement — this revision keeps the conceptual boundary (the three ideas must never be
casually treated as synonyms) while explicitly permitting one organization's own state to
embody all three without separate materialization. Passes the admission test unchanged: no
earlier Rule addresses whether these three concepts are the same or different.

**Repository evidence: PARTIAL — Organization is realized (twice, differently), fully
consistent with this Rule's own revised permission that Institution and Role/Office may live
inside it rather than as separate objects.** `FactionState` and `ClanState` are both real
organization-shaped subjects (ORG-01's own evidence) that embody their own leadership role
(`ClanState.leader_entity_id`) directly, exactly the "no separate materialization required"
shape this Rule permits. What remains unconfirmed is not separate storage (which this Rule no
longer requires) but whether the *conceptual* distinction is ever exercised at all —
`ClanState.leader_entity_id` was not confirmed to carry any institutional semantics (declared
rules/practices governing what the role permits) beyond the bare occupant pointer itself; the
"office outlives occupant" half is real (`ClanLifecycleService.process_succession()`), but a
governing-rule-for-the-role concept, embodied or separate, was not found.

**Scenarios:** [IP-S04](../scenarios/institutions-politics-batch-10.md#ip-s04) (office outlives
occupant, extended — institution hosted by organization, no separate materialization
required).

---

## INST-02 — Delegated authority is distinct from transferred permanent authority, from capability, and from membership; where declared, delegation may be scoped, temporary, revocable, or conditional

> A role, office, or organization holding authority may delegate a bounded portion of it to an
> agent for a specific purpose, without transferring the authority itself permanently. Delegated
> authority is never the same fact as the delegate's own capability to act, nor the same fact as
> the delegate's own membership. Where a domain declares delegation, it may be scoped to a
> specific class of action, temporary, revocable by the delegator, or conditional on some
> declared state — but a domain is not required to build delegation at all.

**Disposition: ACCEPT — PERMITTED (the delegation mechanism itself), REQUIRED (the
distinctness, wherever delegation is used).** Passes the admission test: Batch 02's AUTH-01–06
establish authority's distinctness from capability, ownership, knowledge, and reach in general,
and AUTH-06 covers authority surviving occupant *succession* — but none of them address
*delegation* (a temporary, bounded, revocable handoff distinct from succession, where the
original holder retains the underlying authority). This is genuinely new content.

**Repository evidence: MISSING.** No mechanism resembling scoped, temporary, or revocable
delegation of authority exists anywhere in this repository — confirmed via direct search
(only unrelated "delegate" usages, e.g. Python's own delegation-of-responsibility docstring
language in unrelated modules, were found). `ClanLifecycleService.process_succession()` is a
permanent handoff (a new `leader_entity_id`), not a delegation — it transfers the role itself,
never a bounded subset of its authority while the prior holder retains the rest.

**Scenarios:** none directly traced this batch; the absence itself is the finding.

---

## INST-03 — Authority, capability, practical power, and legitimacy are semantically distinct dimensions; none may be substituted for another merely because they are correlated

> **Authority** is a recognized permission or right to cause a class of transition.
> **Capability** is the mechanical ability to perform it (Batch 02's own AUTH-01 already
> establishes authority ≠ capability). **Power** is the practical capacity to cause outcomes
> through whatever means are actually available, whether or not those means are authorized.
> **Legitimacy** is a socially or institutionally recognized basis for authority, where a domain
> chooses to model such a concept at all. These four are semantically distinct — but not
> causally unrelated: legitimacy may help establish authority, wealth or resources may create
> practical power, holding an office may create authority, military capability may create
> coercive power. None of these causal relationships is universal, and none licenses treating
> one dimension as simply a restatement of another merely because they are frequently
> correlated. Power in particular is never required to be its own canonical scalar or tracked
> field — it may instead be derived relationally from resources, capabilities, relationships,
> authority, reach, or information, according to whatever concrete causal paths a domain
> declares.

**Disposition: ACCEPT — REQUIRED for the distinctness and the non-substitutability claim;
REVISED 2026-09-22 per external follow-up review to remove an overstated independence claim.**
The original wording ("four independent facts... none implies another") was too strong — the
follow-up correctly identified that these concepts routinely have real causal relationships
(legitimacy helping establish authority, wealth producing power) and that stating them as fully
independent would misrepresent the target semantics. This revision keeps the substantive
requirement (never substitute one for another merely because they correlate) while explicitly
permitting declared causal relationships between them, and explicitly removes any implication
that Power needs its own tracked scalar. Passes the admission test unchanged: AUTH-01 already
establishes authority ≠ capability; this Rule's own new content remains introducing Power and
Legitimacy as further distinct dimensions.

**Repository evidence: PARTIAL.** Authority (checked via `LegalityServiceV2`'s
`SELF_ATTACK_ILLEGAL`/`FRIENDLY_FIRE_ILLEGAL`) and capability (`SKILL_ON_COOLDOWN`,
`INSUFFICIENT_READINESS`) are both real and confirmed distinct (AUTH-01's own evidence,
reused). "Power" has a real proxy (`FactionState.military_strength`) that this Rule's own
revision now correctly frames as one legitimate concrete representation among several
possible ones (a tracked scalar is permitted, not required) — no confirmed case of it being
substituted for authority or vice versa was found, consistent with this Rule's own
non-substitutability requirement rather than a violation of it. "Legitimacy" as a tracked
fact is confirmed **MISSING** entirely — see INST-04 below.

**Scenarios:** [IP-S05](../scenarios/institutions-politics-batch-10.md#ip-s05) (unauthorized
actor succeeds — power without authority), [IP-S21](../scenarios/institutions-politics-batch-10.md#ip-s21)
(powerful but illegitimate / legitimate but weak, both directions, extended — power without a
power stat).

---

## INST-04 — Legitimacy or recognition, where a domain models it, is distinct from an individual's own belief about status, from public reputation, and from actual behavioral compliance; its causal relationship to authority is declared by the relevant institution, not fixed by this Rule

> Where a domain chooses to model legitimacy or recognition at all, a claimant's own
> institutional/legal status is a fact independent of whether any specific subject believes it,
> independent of that claimant's own public reputation, and independent of whether subjects
> actually comply with it. A claimant may hold a legitimate institutional status while some
> subjects do not know, do not believe, or do not accept it — and widespread acceptance does
> not, by itself, change the canonical rule defining the status unless a domain declares a
> mechanism by which it does. How legitimacy relates to authority is not fixed by this Rule:
> one institution may declare that office appointment alone establishes authority regardless of
> recognition; another may declare that authority becomes valid only once a recognition or
> confirmation procedure completes. Both are legitimate, and this Rule does not decide between
> them — it only requires that whichever relationship a domain declares, legitimacy itself
> remains a fact distinct from belief, reputation, and compliance.

**Disposition: ACCEPT — REQUIRED for the distinctness; REVISED 2026-09-22 per external
follow-up review to remove an overstated universal claim.** The original wording ("legitimacy
is not required for authority to exist") stated one specific relationship between legitimacy
and authority as if it held universally. The follow-up correctly identified that different
institutional systems may legitimately declare the opposite (authority valid only after
recognition completes) — this revision preserves the four-way distinctness (the genuinely new
content) while removing the universal claim about which relationship holds, leaving that
declared by whichever institution models it. This is the same kind of multi-way-distinctness
content that justified Batch 09's SOC-01 and FAM-01 as Domain Rules rather than pure
applications.

**Repository evidence: MISSING, for the concept itself.** No field anywhere represents
"legitimacy" or "recognition" of an institutional claim as distinct from `public_reputation`
(Batch 09 evidence) or from a belief record (`BeliefEntry`/`LeadState`, Batch 02 evidence) — this
repository has never yet needed the concept, since it has no institutional office/claim
mechanism for legitimacy to attach to in the first place (INST-01's own finding). The Rule's own
target semantics remain independently coherent and testable via scenario even though nothing
currently realizes them; the legitimacy-vs-authority causal question this revision leaves open
has no repository evidence either way, since neither concept is realized.

**Scenarios:** [IP-S06](../scenarios/institutions-politics-batch-10.md#ip-s06) (invalid
claimant), [IP-S07](../scenarios/institutions-politics-batch-10.md#ip-s07) (contested claim,
extended — legitimacy constitutes authority where declared).

---

## Inherited / Applied Foundational Rules

### A role or office persists independently of its current occupant; authority attached to it may become vacant, be filled by a new valid occupant, or end together with the role itself — this applies unchanged to institutional and political roles

> Authority attached to a persistent role or mandate may survive occupant change while that
> role or mandate remains valid. Succession changing who holds the authority is one possible
> outcome; the role or mandate itself ending — taking the authority with it — is another. This
> Rule does not decide which outcome applies for any specific institution.

**Disposition: INHERITED — direct reuse of Batch 02's AUTH-06, which already explicitly
carried forward the open question "does political authority inherit this rule unchanged, or
earn its own refined version?" This batch's own investigation resolves that question: no,
nothing about institutional or political roles specifically requires a refinement — the same
conditional (survives-or-ends) shape holds unchanged.**

**Repository evidence: SUPPORTED, reusing AUTH-06's own evidence directly — and it was AUTH-06's
own evidence, not new evidence found this batch, that already demonstrates the political/
institutional case.** `ClanLifecycleService.process_succession()`'s conditional shape (replace
the leader if a scoreable successor exists; otherwise defer to `process_dissolution()`, ending
the role together with the organization) already is the clearest available instance of an
institutional role's own persistence-or-ending choice in this repository — no further,
institution-specific mechanism was found or was needed to confirm this Rule's own claim holds
without modification.

**Scenarios:** [IP-S04](../scenarios/institutions-politics-batch-10.md#ip-s04).

### Authority is distinct from capability, from ownership, from knowledge, and from opportunity/reach — this applies unchanged to institutional and political authority

> Holding institutional or political authority does not itself grant capability, ownership of
> governed resources, superior knowledge, or opportunity/reach — each remains its own,
> independently-checked fact.

**Disposition: INHERITED — direct reuse of Batch 02's AUTH-01/02/03/04, applied to
institutional/political authority specifically, alongside this batch's own INST-03 (which adds
Power and Legitimacy as two further independent facts AUTH-01–04 did not yet cover). No new
claim beyond confirming the existing four distinctions extend to this batch's own subject
matter without alteration.**

**Repository evidence: SUPPORTED**, reusing AUTH-01–04's own evidence directly; no
institution-specific counter-evidence was found.

**Scenarios:** none newly traced; reuses `foundations/authority.md`'s own TAR-S06–S09 evidence.

---

## Scope / Deferred Boundaries

### Concrete office/institution catalog

> This family states that organization, institution, and role/office are distinct concepts
> (INST-01) but does not design a concrete catalog of specific offices, institutions, or their
> individual authority grants — implementation-level content, deferred per this family's own
> scope.

**Disposition: SCOPE BOUNDARY.**

### Concrete delegation-policy catalog

> This family states delegation's own distinctness (INST-02) but does not design concrete
> delegation policies, scopes, or revocation procedures for any specific role — deferred.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **Confirmed MISSING — no institution or role/office concept exists independently of the
  organization that currently hosts it.** See INST-01 above. The closest realized concepts
  (`ClanState.leader_entity_id`, `GroupRecord.leader_id`, `GroupRecord.roles`) are all
  organization-owned fields, not a separable institutional concept.
- **Confirmed MISSING — no delegation mechanism exists.** See INST-02 above.
- **Confirmed MISSING — no "legitimacy"/"recognition" concept exists, distinct from
  reputation or belief.** See INST-04 above.
- **PARTIAL — "power" has a real proxy (`FactionState.military_strength`) but no confirmed
  independence from authority, since no faction-level formal-authority concept exists to
  diverge from.** See INST-03 above.

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** delegated authority may be scoped, temporary, revocable, or conditional,
  distinct from a permanent transfer (INST-02).
  **Current realization:** none — only permanent succession (`ClanLifecycleService.
  process_succession()`) exists.
  **Gap/mismatch:** the entire delegation concept is unrealized.
  **Possible implementation direction:** a `DelegationGrant`-shaped typed record (grantor,
  grantee, scope, expiry/revocation condition) checked alongside existing authority checks
  (e.g. `LegalityServiceV2`).
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.
- **Target semantic:** legitimacy/recognition, where modeled, is distinct from belief,
  reputation, and compliance (INST-04).
  **Current realization:** no field represents this concept at all.
  **Possible implementation direction:** a claim/recognition record analogous in shape to
  `PublicReputationProfile`, but scoped to institutional-claim validity rather than general
  standing, read independently of `public_reputation`.
  **Implementation decision:** DEFERRED.

## Cross-domain links recorded here

- INST-01 → Organizations (`organizations.md`'s ORG-01)
- INST-02, INST-03 (authority/capability half) → Authority (AUTH-01–06, Batch 02)
- INST-04 → Perception/Knowledge (Batch 06's KNOW-01/PERC-01), Social Relations
  (`social-lineage/social-relations.md`'s reputation-reach Inherited entry, Batch 09)

## Open questions carried forward

1. **Is practical power authoritative state or a derived relation?** (Revised 2026-09-22 per
   external follow-up review, away from the storage-shaped framing "does Power deserve its own
   tracked field.") INST-03's own revision explicitly permits either — this asks the semantic
   question underneath: is power itself a first-class fact a domain declares directly, or
   always a computed function of other declared facts (resources, capabilities, relationships,
   authority, reach, information)? Not decided here.
2. **What semantic facts make an institution distinct from its hosting organization, given
   that INST-01 no longer requires separate materialization?** (Revised 2026-09-22, away from
   "does Institution need a dedicated field.") Not decided here.
3. **Under what declared conditions does legitimacy affect authority?** INST-04's own revision
   leaves this open by design — different institutions may declare office-appointment-alone or
   recognition-gated authority; whether this Catalog should ever name a small closed set of
   legitimate patterns, or leave it fully domain-declared indefinitely, is not decided here.
