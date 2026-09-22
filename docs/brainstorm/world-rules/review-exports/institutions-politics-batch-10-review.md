---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Batch 10 (Organizations / Institutions / Politics / Law)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the
fix for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Standing direction applied (2026-09-22, `tmp/world-rule-direction.md`)

This is the first batch drafted under the standing direction: Rule statements describe only
target world semantics; repository classification (SUPPORTED/PARTIAL/CONFLICTING/MISSING/
INERT-OFF) records realization only, never delivery priority — **MISSING is not a feature
requirement.** Where a Rule permits rather than requires a behavior, this is stated
explicitly. This export adds the new required **Implementation Candidates — Non-Binding**
section and reframes **Owner-attention decisions** toward design semantics rather than
implementation choices, per that direction's own items 8/9/17.

## Batch scope

The seventh domain-facing batch, and the first in Milestone C's own broadening toward
collective/institutional subjects rather than individual ones — how groups of individuals
become persistent collective actors, how roles and institutions carry authority beyond
individual occupants, and how political/legal structures create real constraints and
opportunities. Four rule families: Organizations, Roles/Institutions, Politics/Authority,
Law/Enforcement. Files live under `institutions-politics/`, per the batch instruction's own
directory suggestion. No target Rule count was set, per the batch instruction's own explicit
"Do not target any particular Rule count."

## Canonical files included

- `institutions-politics/organizations.md` (ORG-01–04)
- `institutions-politics/roles-institutions.md` (INST-01–04)
- `institutions-politics/politics-authority.md` (POL-01–02)
- `institutions-politics/law-enforcement.md` (LAW-01–03)
- `scenarios/institutions-politics-batch-10.md` (IP-S01–S21)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds or
refines target world semantics beyond Rules already defined elsewhere. This batch's 31 total
catalog entries break down as:

- **13 genuine Domain Rules**: ORG-01, ORG-02, ORG-03, ORG-04; INST-01, INST-02, INST-03,
  INST-04; POL-01, POL-02; LAW-01, LAW-02, LAW-03.
- **10 Inherited/Applied Foundational Rules**: in `organizations.md` — organizational resource
  ownership ≠ member ownership (OWN-01/02, AUTH-02), organizational knowledge ≠ member
  knowledge (PERC-01, KNOW-01/02), institutional memory persists via declared record-keeping
  (HP-01, SOC-03), organization-to-organization relationships are their own representation
  (ECOL-01/02, SOC-01), membership conflicts resolve via the decision layer (AGENCY-01/02); in
  `roles-institutions.md` — role/office persists across occupant change, unchanged for
  political roles (AUTH-06, resolving its own carried-forward open question), authority ≠
  capability/ownership/knowledge/reach (AUTH-01–04); in `politics-authority.md` — authority
  never guarantees compliance (AGENCY-01/02), power-conversion edges are specific and declared
  (PROG-07, EXCH-01); in `law-enforcement.md` — sanction execution requires a real causal
  mechanism (CAUSE-01, AUTH-01).
- **8 Scope/Deferred Boundaries**: concrete membership-formation catalog, concrete
  resource-allocation-policy catalog, in `organizations.md`; concrete office/institution
  catalog, concrete delegation-policy catalog, in `roles-institutions.md`; concrete
  political-resolution-mechanism catalog, territorial sovereignty depth, in
  `politics-authority.md`; concrete criminal-justice content catalog, territorial jurisdiction
  depth, in `law-enforcement.md`.

**Genuine new-Rule count for this batch: 13.** **Inherited/reused foundation count: 10
entries, citing OWN-01/02 (Batch 01), ID-06 (Batch 01), AUTH-01–06 (Batch 02), CAUSE-01
(Foundational), HP-01 (Foundational), ECOL-01/02 (Batch 05), PERC-01/KNOW-01/02/AGENCY-01/02
(Batch 06), PROG-07 (Batch 07), EXCH-01 (Batch 08), SOC-01/SOC-03 (Batch 09).**

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| ORG-01 | Domain Rule | Organization Identity ≠ Member Identity | Persists independently of membership composition. | Accepted — REQUIRED |
| ORG-02 | Domain Rule | Membership ≠ Loyalty/Obedience/Employment/Citizenship/Role/Ownership | Six-way distinctness; multi-membership permitted where declared. | Accepted — distinctness REQUIRED, multi-membership PERMITTED |
| ORG-03 | Domain Rule | Organizational Action Requires Decision → Authorization → Execution | Collective desire alone never directly changes world state. | Accepted — REQUIRED |
| ORG-04 | Domain Rule | Split/Merge/Dissolution Require Their Own Declared Process | Deepens ID-06 for collective subjects. | Accepted — procedure REQUIRED, occurrence PERMITTED |
| INST-01 | Domain Rule | Organization ≠ Institution ≠ Role/Office | Three distinct concepts, not synonyms. | Accepted — REQUIRED |
| INST-02 | Domain Rule | Delegated Authority ≠ Permanent Transfer ≠ Capability ≠ Membership | Delegation may be scoped/temporary/revocable/conditional. | Accepted — distinctness REQUIRED, delegation PERMITTED |
| INST-03 | Domain Rule | Authority / Capability / Power / Legitimacy Are Four Independent Facts | Introduces Power and Legitimacy as new concepts. | Accepted — REQUIRED |
| INST-04 | Domain Rule | Legitimacy ≠ Belief ≠ Reputation ≠ Compliance | Legitimacy not required for authority to exist. | Accepted — distinctness REQUIRED, legitimacy modeling PERMITTED |
| POL-01 | Domain Rule | Political Succession ≠ Kinship ≠ Property Inheritance | Resolves Batch 09's own deferred boundary. | Accepted — REQUIRED |
| POL-02 | Domain Rule | No Default Political Stability | Instability outcomes permitted; counterforces must be declared. | Accepted — REQUIRED |
| LAW-01 | Domain Rule | Law Existence / Knowledge / Compliance / Detection / Judgment / Sanction Are Six Distinct Facts | Any link may fail independently. | Accepted — REQUIRED |
| LAW-02 | Domain Rule | Institutional Record ≠ World Truth ≠ Individual Belief | False records can cause real consequences. | Accepted — REQUIRED |
| LAW-03 | Domain Rule | Law/Authority Applicability Has a Declared Scope | Never globally universal by default. | Accepted — scoping REQUIRED, specific mechanism PERMITTED |

## Inherited Foundations Summary

| Entry (as stated in its own file) | Foundational Rule(s) reused | File |
|---|---|---|
| Organizational resource ownership ≠ member ownership | OWN-01, OWN-02 (Batch 01); AUTH-02 (Batch 02) | `organizations.md` |
| Organizational/institutional knowledge ≠ member knowledge | PERC-01, KNOW-01, KNOW-02 (Batch 06) | `organizations.md` |
| Institutional memory persists via declared record-keeping | HP-01 (Foundational); SOC-03 (Batch 09) | `organizations.md` |
| Organization-to-organization relationships are their own representation | ECOL-01, ECOL-02 (Batch 05); SOC-01 (Batch 09) | `organizations.md` |
| Membership conflicts resolve through the decision layer | AGENCY-01, AGENCY-02 (Batch 06) | `organizations.md` |
| Role/office persists across occupant change, unchanged for political roles | AUTH-06 (Batch 02) — resolves its own open question | `roles-institutions.md` |
| Authority ≠ capability/ownership/knowledge/reach | AUTH-01, AUTH-02, AUTH-03, AUTH-04 (Batch 02) | `roles-institutions.md` |
| Authority never guarantees compliance; power without authority is possible | AGENCY-01, AGENCY-02 (Batch 06) | `politics-authority.md` |
| Power-conversion edges are specific and declared, never universal | PROG-07 (Batch 07); EXCH-01 (Batch 08) | `politics-authority.md` |
| Sanction execution requires a real causal mechanism | CAUSE-01 (Foundational); AUTH-01 (Batch 02) | `law-enforcement.md` |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Result |
|---|---|---|---|---|
| IP-S01 | Founder Dies | guild persists past founder's death | Organizations | Covered |
| IP-S02 | Member Leaves | individual and org both persist | Organizations | Covered |
| IP-S03 | Member Disobeys | valid order, member refuses | Organizations (inherited) | Partial |
| IP-S04 | Office Outlives Occupant | authority vacant, later refilled | Roles/Institutions (inherited) | Partial |
| IP-S05 | Unauthorized Actor Succeeds | power without authority, compliance | Roles/Institutions (inherited) | Partial |
| IP-S06 | Invalid Claimant | conditions unmet, authority withheld | Roles/Institutions, Politics | Revealed gap |
| IP-S07 | Contested Claim | two claimants, divergent recognition | Roles/Institutions | Revealed gap |
| IP-S08 | Kinship Does Not Grant Office | child exists, another candidate chosen | Politics | Covered (analogue) |
| IP-S09 | Organization Split | fracture, continuity undeclared | Organizations | Revealed gap |
| IP-S10 | Organization Merge | combination, identity undeclared | Organizations | Revealed gap |
| IP-S11 | Law Exists but Nobody Knows | unknowing violation | Law/Enforcement | Revealed gap |
| IP-S12 | Violation Undetected | no observer, no enforcement | Law/Enforcement | Revealed gap |
| IP-S13 | False Accusation | false report, real institutional action | Law/Enforcement | Revealed gap |
| IP-S14 | Unauthorized Spending | access without authority | Organizations (inherited) | Revealed gap |
| IP-S15 | Enforcement Fails | valid sanction, execution fails | Law/Enforcement (inherited) | Revealed gap |
| IP-S16 | Law Is Ignored | repeated disobedience, law stays valid | Law/Enforcement | Revealed gap |
| IP-S17 | Individual Becomes Institutionally Significant | ordinary person, org reacts by name | Organizations (inherited) | Revealed gap |
| IP-S18 | Organization Wealth | authorized member spend | Organizations, Organizations (inherited) | Partial |
| IP-S19 | Conflicting Memberships | two orgs conflict, individual chooses | Organizations (inherited) | Revealed gap |
| IP-S20 | Institutional Memory | declared record survives official's departure | Organizations (inherited) | Partial |
| IP-S21 | Powerful/Illegitimate & Legitimate/Weak | both directions of the authority/power split | Roles/Institutions | Partial |

## Coverage Summary

**Organizations**
- identity persists independent of members — IP-S01, IP-S02
- membership ≠ six other concepts — IP-S02, IP-S03, IP-S19
- decision → authorization → execution chain — IP-S18
- split/merge/dissolution require declared process — IP-S09, IP-S10

**Roles/Institutions**
- organization/institution/role distinctness — IP-S04
- delegation distinctness — (no scenario; absence is the finding)
- authority/capability/power/legitimacy quadruple — IP-S05, IP-S21
- legitimacy ≠ belief/reputation/compliance — IP-S06, IP-S07

**Politics/Authority**
- succession ≠ kinship/property — IP-S08
- no default stability — (no scenario; the real diplomatic-tension channel is standing
  evidence, not a probe)

**Law/Enforcement**
- six-way law chain distinctness — IP-S11, IP-S12, IP-S15, IP-S16
- institutional record ≠ truth/belief — IP-S13
- jurisdiction has a declared scope — IP-S11

## Deferred Semantics

- Concrete membership-formation/departure event catalog, resource-allocation-policy catalog —
  `organizations.md`.
- Concrete office/institution catalog, concrete delegation-policy catalog —
  `roles-institutions.md`.
- Concrete political-resolution-mechanism catalog; territorial sovereignty depth (deferred to
  Batch 11) — `politics-authority.md`.
- Concrete criminal-justice content catalog; territorial jurisdiction depth (deferred to
  Batch 11) — `law-enforcement.md`.

## Cross-domain findings

- Organizations ↔ Identity (Batch 01): ORG-01/ORG-04 are the first drafted content answering
  ID-06's own deferred "organizations & institutions" split/merge/succession question.
- Roles/Institutions ↔ Authority (Batch 02): the role/office-persists Inherited entry directly
  resolves AUTH-06's own carried-forward open question — political/institutional roles inherit
  AUTH-06 unchanged, confirmed by AUTH-06's own pre-existing `ClanLifecycleService` evidence,
  not by new evidence this batch found.
- Politics ↔ Lineage/Descent (Batch 09): POL-01 directly resolves the succession boundary
  `lineage-descent.md` explicitly deferred to this batch.
- Politics ↔ Capability/Progression (Batch 07), Economy/Exchange (Batch 08): the
  power-conversion Inherited entry reuses PROG-07/EXCH-01's own already-established
  "conversion edges are specific, never universal" pattern for political conversion.
- Organizations ↔ Capability/Progression (Batch 07), Lineage/Descent (Batch 09): IP-S17
  confirms the "ordinary individual becomes historically significant by name" gap recurs at
  the organizational scale, the third scale (individual, lineage, organization) at which this
  same shape has now been found.
- Law/Enforcement ↔ Social Relations (Batch 09): LAW-02's institutional-record concept is
  related to, but distinct from, the reputation-reach CONFLICTING finding `social-relations.md`
  already recorded — the two are different failure modes (institution holding a fallible
  record vs. reputation being read as ungated global truth), not the same finding restated.

**Explicit call-out — genuine Domain Rule count:** **13.**

**Explicit call-out — organization identity vs. member identity:** **Distinct, confirmed by
construction.** `FactionState`/`ClanState` are keyed by their own ids; leadership is a
replaceable pointer, not the organization's own identity (ORG-01).

**Explicit call-out — organization vs. institution vs. role semantics:** **Kept distinct as
target concepts (INST-01); only Organization is realized in the current repository.**
Institution and Role/Office, as concepts independent of the specific hosting organization, are
confirmed MISSING.

**Explicit call-out — whether roles survive occupant turnover:** **Yes, both outcomes
(survival and ending) are real, per AUTH-06's own evidence, reused unchanged for this batch's
own institutional/political subject matter.**

**Explicit call-out — authority vs. power vs. legitimacy distinction:** **All four (adding
Power and Legitimacy to AUTH-01's existing authority/capability split) are stated as
independent target facts (INST-03); Power has a real partial proxy
(`FactionState.military_strength`), Legitimacy has no realization at all.**

**Explicit call-out — whether membership actually affects decisions without forcing them:**
**Yes, confirmed by absence of any forcing mechanism** — `ClanLifecycleService.
process_leave()`'s own unconditional shape and the absence of any behavior-override tied to
`member_entity_ids` (ORG-02).

**Explicit call-out — whether organizational resources can be used by authorized members:**
**No — confirmed MISSING.** Only a fully automatic systemic process (`TownResolutionSystem`)
touches `state.global_resources`; no member-initiated, authorized or unauthorized, spend path
exists.

**Explicit call-out — whether organizational knowledge is distinct from member knowledge:**
**Yes as a target requirement (reusing Batch 06); realized only as one INERT/OFF candidate
path** (`ENABLE_INFORMATION_HUB_ACCUMULATION`) **in one direction, and confirmed MISSING in the
reverse direction.**

**Explicit call-out — whether law existence is distinct from knowledge/compliance/
enforcement:** **Yes as target semantics (LAW-01); entirely MISSING as a repository
realization** — no in-world law/crime/violation/sanction subsystem exists at all.

**Explicit call-out — whether enforcement respects perception/reach/capability/authority:**
**Not independently testable — no enforcement mechanism exists to check this against.** The
target requirement (LAW-01, the Inherited sanction-execution entry) is stated regardless.

**Explicit call-out — whether political succession is distinct from property inheritance:**
**Yes, confirmed by the same structural pattern found for kinship at Batch 09's own lineage
scale** (`_select_default_heir()`) **now reconfirmed at the group-leadership scale**
(`ClanLifecycleService.process_succession()`) **— neither ever reads kinship or property
facts.** Whether this is itself "political succession" or a distinct, unrealized concept one
scale up remains an open question (POL-01).

**Explicit call-out — whether institutions retain history across occupant/member turnover:**
**Partially.** No magical individual-memory transfer exists (confirmed by absence, the
correct outcome); genuine declared institutional record-keeping is real but narrow
(`FactionState`/`ClanState`'s own retained fields), not populated by any specific official's
own act of "learning and recording."

**Explicit call-out — whether ordinary individuals can become institutionally significant by
name:** **No — confirmed MISSING, the third scale (after individual and lineage) at which this
identical flagship gap has now been found (IP-S17).**

**Explicit call-out — which political/institutional state is inert or omniscient:**
`ENABLE_INFORMATION_HUB_ACCUMULATION` is INERT/OFF; nothing checked was found to be
omniscient in this batch's own new territory (unlike Batch 06's `ResourceOpportunityProvider`
or Batch 09's reputation-reach finding), because the mechanisms that would need to respect an
information boundary (organizational knowledge of a specific individual, law enforcement
detection) are themselves confirmed MISSING rather than present-and-ungated.

## Repository Findings

Classified per the CONFLICTING/INERT-OFF/MISSING distinction Batch 06/07/08/09 established.
**These are repository/implementation facts, not World Rule decisions, and per the standing
direction, imply no delivery priority.**

**No CONFLICTING finding was identified this batch.** Unlike Batches 06/08/09, this batch's
own new territory is dominated by MISSING realization (no mechanism exists to conflict with
the target semantics) rather than a present, ungated violation of them.

**INERT/OFF (1 finding):**
1. `ENABLE_INFORMATION_HUB_ACCUMULATION` gates the one real candidate individual→
   institutional information path found (`src/engine/quests.py`); defaults OFF.

**MISSING (11 findings):**
2. No organization split or merger mechanism exists (ORG-04).
3. No authorized-member-access path to collective resources exists (organizations.md's own
   Inherited entry).
4. No per-(organization, specific individual) standing exists, distinct from population-wide
   reputation (organizations.md; IP-S17).
5. No institution or role/office concept exists independently of its hosting organization
   (INST-01).
6. No delegation mechanism of any kind exists (INST-02).
7. No legitimacy/recognition concept exists, distinct from belief or reputation (INST-04).
8. No political office concept exists for POL-01's own succession rule to apply to (POL-01).
9. Every named political power-conversion edge checked is unrealized (politics-authority.md's
   own Inherited entry).
10. No in-world law, crime, violation, detection, judgment, or sanction subsystem exists at all
    (LAW-01) — the largest single gap this batch found, spanning an entire rule family.
11. No institutional-record concept, distinct from world truth and individual belief, exists
    (LAW-02).
12. No law-specific jurisdiction-scoping mechanism exists, though the general
    location-plus-affiliation pattern is real elsewhere (LAW-03).

**A significant, notable finding, not itself CONFLICTING/INERT/MISSING but worth its own
category:**
13. Two structurally separate "faction" representations exist in this repository (the legacy
    `Faction` IntEnum and the E53 `FactionState`/catalog `faction_id`), deliberately bridged
    via `get_legacy_faction_bucket()` — a real multiplicity, already resolved, the same shape
    as Batch 09's own reputation-naming-collision finding. This repository also uses the word
    "role" for at least three unrelated concepts (`SocialBond.role`, `GroupRecord.roles`, and
    this batch's own institutional role/office concept) — worth a future author's attention.

Key evidence, all confirmed by direct code/doc inspection: `src/core/state.py` (`FactionState`,
`ClanState`, `GroupRecord`), `src/core/enums.py` (`Faction`), `src/content_semantics/
faction.py`, `src/systems/social_systems/clan_lifecycle.py`, `src/engine/town_resolution.py`,
`src/engine/tactical.py`, `src/domains/faction/diplomatic_state_machine.py`,
`src/domains/optimization/feature_flags.py`, `src/engine/quests.py`,
`src/observability/{hard_law_monitor,anomaly}/*` (confirmed unrelated meta-level tooling),
`docs/brainstorm/world-rules/foundations/authority.md` (AUTH-01–06, reused directly),
`docs/brainstorm/world-rules/foundations/identity.md` (ID-06).

## Owner-attention decisions (design semantics, per the standing direction)

- Does "Organization" need its own durable-state category distinct from "Institution," or can
  Institution remain a purely conceptual label layered over existing Organization + Role state
  with no dedicated field (INST-01's own open question)?
- Is `ClanLifecycleService.process_succession()` a genuine instance of "political succession"
  (POL-01), or does political succession name a distinct concept one scale above ordinary
  group leadership, currently entirely unrealized?
- Does "Power" (INST-03) deserve its own tracked field distinct from
  `FactionState.military_strength`, or is the current proxy adequate until a real
  authority-vs-power divergence case is found?
- Should LAW-02's institutional-record concept ever unify with Batch 06's individual
  belief-modeling data shape (`BeliefEntry`/`LeadState`), or remain conceptually related but
  structurally separate?
- Is multi-membership *within* one organization kind (e.g., two Clans) something the target
  model should positively support or explicitly forbid — `find_clan_id_for_entity()`'s own
  single-match assumption is a repository fact, not yet a decided Rule (ORG-02's own open
  question)?
- Does LAW-03's jurisdiction concept belong fully to this batch, or should its own depth wait
  until Batch 11 supplies real spatial/territorial primitives to ground it against?

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** a member's access to organizational resources requires its own declared
  authority.
  **Current realization:** only a fully automatic tax/maintenance system touches the vault.
  **Gap/mismatch:** authorized-member access is entirely unrealized.
  **Possible implementation direction:** a declared spend-authorization check (role/
  office-gated) before any entity-initiated draw from a collective resource pool.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.
- **Target semantic:** an organization may accumulate standing toward one specific named
  individual, distinct from population-wide reputation.
  **Current realization:** no field or mechanism exists.
  **Possible implementation direction:** a per-(faction, entity) record analogous to
  `FactionSentiment`, populated by a declared witnessed-event process.
  **Implementation decision:** DEFERRED.
- **Target semantic:** delegated authority may be scoped, temporary, revocable, or conditional.
  **Current realization:** none — only permanent succession exists.
  **Possible implementation direction:** a `DelegationGrant`-shaped typed record checked
  alongside existing authority checks.
  **Implementation decision:** DEFERRED.
- **Target semantic:** legitimacy/recognition, where modeled, is distinct from belief,
  reputation, and compliance.
  **Current realization:** no field represents this concept.
  **Possible implementation direction:** a claim/recognition record analogous in shape to
  `PublicReputationProfile`, read independently of `public_reputation`.
  **Implementation decision:** DEFERRED.
- **Target semantic:** political succession requires its own declared eligibility/validity
  rule, distinct from kinship and property.
  **Current realization:** only group-leadership-scale succession exists; no larger
  political-office concept.
  **Possible implementation direction:** an `OfficeState`-shaped record with its own
  succession-rule declaration, if investigation later confirms group-leadership succession is
  not itself sufficient.
  **Implementation decision:** DEFERRED.
- **Target semantic:** a law's existence, knowledge, compliance, detection, judgment, and
  sanction are six distinct, independently-failing facts.
  **Current realization:** none of the six exist as in-world concepts.
  **Possible implementation direction:** a minimal declared-rule/violation-record mechanism,
  potentially reusing the `ReasonCode`/legality-check machinery's own shape (Batch 02's AUTH
  family) alongside a typed violation record analogous to `BetrayalRecord` (Batch 09).
  **Implementation decision:** DEFERRED.

## Candidate disposition

Thirteen Domain Rules were drafted across four families (4 Organizations, 4 Roles/
Institutions, 2 Politics/Authority, 3 Law/Enforcement) — **all 13 accepted, 0 rejected, 0
split, 0 merged.** No target rule count was set in advance, per the batch instruction's own
explicit guidance. Ten further entries were identified as Inherited/Applied Foundational Rules
and eight as Scope/Deferred Boundaries — none required a new Rule ID.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/institutions-politics-batch-10-report.md` (local review report, not part of this catalog).

---

> **BATCH 10 (ORGANIZATIONS / INSTITUTIONS / POLITICS / LAW) READY FOR HIGH-LEVEL EXTERNAL
> REVIEW.**

All required artifacts exist: four rule-family files (13 genuine Domain Rules; 31 total
catalog entries), one scenario file (21 scenarios covering every named seed scenario in the
batch instruction's own §25), this review export with all required sections including the new
Implementation Candidates — Non-Binding section, and a local disposition report. No
contradiction was found against any prior batch's own Rules; this batch's own dominant finding
is breadth of MISSING realization (an entire rule family, Law/Enforcement, has no in-world
counterpart at all) rather than a present violation of accepted semantics — consistent with
the standing direction's own framing that a batch may PASS even where the repository contains
major missing implementations, since PASS means target semantics are coherent and honestly
evaluated, not that the repository fully implements the domain. Fifteen of the batch
instruction's own sixteen stop-condition checklist items are satisfied by target-semantic
design and cross-checked against available evidence; the sixteenth (ordinary-individual →
institutional recognition has been probed) is satisfied in the negative — probed, and confirmed
MISSING, which the standing direction confirms is itself a complete, valid answer.

Do not begin Batch 11 (Places / Settlements / Territory / Culture / Belief) until Batch 10
receives high-level review.
