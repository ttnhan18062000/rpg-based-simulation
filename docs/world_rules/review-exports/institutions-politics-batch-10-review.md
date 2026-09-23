---
status: authoritative
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# Review Export: Batch 10 (Organizations / Institutions / Politics / Law)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the
fix for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Standing direction applied (2026-09-22, `tmp/world-rule-direction.md`)

Rule statements describe only target world semantics; repository classification
(SUPPORTED/PARTIAL/CONFLICTING/MISSING/INERT-OFF) records realization only, never delivery
priority — **MISSING is not a feature requirement.** Owner-attention decisions are framed as
design semantics, not implementation choices; storage/data-shape questions live only under
Implementation Candidates — Non-Binding.

## Follow-up revision summary (2026-09-22)

A targeted semantic cleanup follow-up (`tmp/world-rule-batch-10-followup-ext-ai.md`) was
applied directly to the canonical files, not merely to this export:

1. **ORG-03 generalized.** Reworded from a mandatory "decision mechanism → authorized actor →
   committed action" chain to "a valid organizational process + a real execution/commit path;
   authorization is required only where the declared process makes authority relevant" —
   explicitly permitting standing policy, automatic recurring process, delegated procedure, or
   individual/collective decision as equally valid process shapes, while still prohibiting bare
   organizational desire becoming true with no process at all.
2. **INST-01 refined.** The three concepts (Organization/Institution/Role) remain
   semantically distinct, but separate persistent-state materialization is now explicitly NOT
   required — an organization may itself embody an institution and its roles with no separate
   objects.
3. **INST-03 refined.** Reworded from "four independent facts... none implies another" to
   "semantically distinct dimensions; none may be substituted for another merely because they
   are correlated" — explicitly permitting real causal relationships between them (legitimacy
   → authority, wealth → power, office → authority, military capability → coercive power), and
   explicitly removing any requirement that Power have its own canonical scalar (it may be
   derived relationally).
4. **INST-04 refined.** Removed the universal claim "legitimacy is not required for authority
   to exist" — different institutions may validly declare either "appointment alone
   establishes authority" or "authority requires recognition first"; this Rule no longer picks
   between them.
5. **POL-02 reclassified to Inherited** (originally a Domain Rule, "No Default Political
   Stability"). Re-tested against the admission discipline and found to add no
   Politics-specific content beyond applying Batch 09's SOC-03 and Batch 07's PROG-05 —
   moved rather than kept for the sake of preserving the Politics-family Rule count.
6. **LAW-01 generalized.** Reworded from a mandatory "six distinct facts in a causal chain" to
   nine listed semantic facts (rule existence, applicability, subject action, compliance/
   violation, knowledge/belief, detection, adjudication, sanction decision, sanction
   execution) that do not automatically imply one another, with no legal system required to
   use every stage — explicitly permitting "violation never detected" and "detection →
   automatic declared consequence, no separate judgment" as valid shapes, while keeping
   "sanction decided ≠ sanction executed" as the one constraint that always holds.
7. **LAW-02 preserved unchanged** — confirmed strong and non-duplicative on re-inspection.
8. **LAW-03 refined.** Explicitly lists "explicitly global" as one legitimate declared scope
   among several (territorial, membership-based, role-based, contractual, event-specific,
   temporal) — the prohibition is against *accidental* universality, not global applicability
   itself.
9. **Owner-Attention semantics cleaned.** Storage-shaped questions ("does Power deserve its
   own tracked field," "should institutional record reuse `BeliefEntry`'s shape," "does
   Institution need a dedicated field") replaced with design-semantic ones ("is practical power
   authoritative state or a derived relation," "what semantic facts make an institution
   distinct from its hosting organization," "can one record simultaneously serve institutional
   and individual epistemic roles without violating ownership," "under what declared
   conditions does legitimacy affect authority").
10. **Five adversarial probes added**, extended onto existing scenarios rather than as new IDs:
    IP-S18 (standing policy without a fresh decision), IP-S04 (institution hosted by
    organization), IP-S07 (legitimacy constitutes authority where declared), IP-S21 (power
    without a power stat), IP-S15 (enforcement without a separate judgment stage).
11. **Major findings preserved prominently**, per the follow-up's own explicit list (below).

Net effect on counts: genuine Domain Rules **13 → 12** (POL-02 reclassified); Inherited
entries **10 → 11** (POL-02 reclassified in); Scope Boundaries unchanged at **8**; total
catalog entries unchanged at **31**.

## Batch scope

The seventh domain-facing batch, and the first in Milestone C's own broadening toward
collective/institutional subjects rather than individual ones — how groups of individuals
become persistent collective actors, how roles and institutions carry authority beyond
individual occupants, and how political/legal structures create real constraints and
opportunities. Four rule families: Organizations, Roles/Institutions, Politics/Authority,
Law/Enforcement. Files live under `institutions-politics/`, per the batch instruction's own
directory suggestion. No target Rule count was set, per the batch instruction's own explicit
"Do not target any particular Rule count" — reconfirmed by the follow-up's own explicit
"do not preserve the current 13 genuine Rule count artificially."

## Canonical files included

- `institutions-politics/organizations.md` (ORG-01–04)
- `institutions-politics/roles-institutions.md` (INST-01–04)
- `institutions-politics/politics-authority.md` (POL-01; POL-02 now Inherited)
- `institutions-politics/law-enforcement.md` (LAW-01–03)
- `scenarios/institutions-politics-batch-10.md` (IP-S01–S21, five extended in place)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds or
refines target world semantics beyond Rules already defined elsewhere. This batch's 31 total
catalog entries break down as:

- **12 genuine Domain Rules**: ORG-01, ORG-02, ORG-03, ORG-04; INST-01, INST-02, INST-03,
  INST-04; POL-01; LAW-01, LAW-02, LAW-03.
- **11 Inherited/Applied Foundational Rules**: in `organizations.md` — organizational resource
  ownership ≠ member ownership (OWN-01/02, AUTH-02), organizational knowledge ≠ member
  knowledge (PERC-01, KNOW-01/02), institutional memory persists via declared record-keeping
  (HP-01, SOC-03), organization-to-organization relationships are their own representation
  (ECOL-01/02, SOC-01), membership conflicts resolve via the decision layer (AGENCY-01/02); in
  `roles-institutions.md` — role/office persists across occupant change, unchanged for
  political roles (AUTH-06), authority ≠ capability/ownership/knowledge/reach (AUTH-01–04); in
  `politics-authority.md` — authority never guarantees compliance (AGENCY-01/02),
  power-conversion edges are specific and declared (PROG-07, EXCH-01), **political stability
  is never a default outcome (new this follow-up: reclassified from POL-02, reusing SOC-03
  and PROG-05)**; in `law-enforcement.md` — sanction execution requires a real causal
  mechanism (CAUSE-01, AUTH-01).
- **8 Scope/Deferred Boundaries**: concrete membership-formation catalog, concrete
  resource-allocation-policy catalog, in `organizations.md`; concrete office/institution
  catalog, concrete delegation-policy catalog, in `roles-institutions.md`; concrete
  political-resolution-mechanism catalog, territorial sovereignty depth, in
  `politics-authority.md`; concrete criminal-justice content catalog, territorial jurisdiction
  depth, in `law-enforcement.md`.

**Genuine new-Rule count for this batch: 12** (was 13 before this follow-up reclassified
POL-02). **Inherited/reused foundation count: 11 entries**, citing OWN-01/02 (Batch 01), ID-06
(Batch 01), AUTH-01–06 (Batch 02), CAUSE-01 (Foundational), HP-01 (Foundational), ECOL-01/02
(Batch 05), PERC-01/KNOW-01/02/AGENCY-01/02 (Batch 06), PROG-05/PROG-07 (Batch 07), EXCH-01
(Batch 08), SOC-01/SOC-03 (Batch 09).

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| ORG-01 | Domain Rule | Organization Identity ≠ Member Identity | Persists independently of membership composition. | Accepted — REQUIRED |
| ORG-02 | Domain Rule | Membership ≠ Loyalty/Obedience/Employment/Citizenship/Role/Ownership | Six-way distinctness; multi-membership permitted where declared. | Accepted — distinctness REQUIRED, multi-membership PERMITTED |
| ORG-03 | Domain Rule | Organizational Action Requires a Valid Process + Real Execution Path | Reworded 2026-09-22: authorization required only where the declared process makes it relevant; standing policy permitted. | Accepted (revised) |
| ORG-04 | Domain Rule | Split/Merge/Dissolution Require Their Own Declared Process | Deepens ID-06 for collective subjects. | Accepted — procedure REQUIRED, occurrence PERMITTED |
| INST-01 | Domain Rule | Organization ≠ Institution ≠ Role/Office (Conceptually, Not Structurally) | Reworded 2026-09-22: semantic distinction, separate materialization NOT required. | Accepted (revised) |
| INST-02 | Domain Rule | Delegated Authority ≠ Permanent Transfer ≠ Capability ≠ Membership | Delegation may be scoped/temporary/revocable/conditional. | Accepted — distinctness REQUIRED, delegation PERMITTED |
| INST-03 | Domain Rule | Authority / Capability / Power / Legitimacy Are Distinct, Not Independent | Reworded 2026-09-22: correlated and causally related, never substitutable; Power need not be a scalar. | Accepted (revised) |
| INST-04 | Domain Rule | Legitimacy ≠ Belief ≠ Reputation ≠ Compliance | Reworded 2026-09-22: removed universal "never required for authority" claim; causal relationship is institution-declared. | Accepted (revised) |
| POL-01 | Domain Rule | Political Succession ≠ Kinship ≠ Property Inheritance | Resolves Batch 09's own deferred boundary. | Accepted — REQUIRED |
| ~~POL-02~~ | *(reclassified)* | *(was: No Default Political Stability)* | Moved to Inherited — fully covered by SOC-03 + PROG-05. | Reclassified (see Inherited) |
| LAW-01 | Domain Rule | Law/Knowledge/Compliance/Detection/Adjudication/Sanction Are Distinct Facts | Reworded 2026-09-22: nine listed facts, no mandatory pipeline; decision ≠ execution always holds. | Accepted (revised) |
| LAW-02 | Domain Rule | Institutional Record ≠ World Truth ≠ Individual Belief | False records can cause real consequences. Preserved unchanged. | Accepted |
| LAW-03 | Domain Rule | Law/Authority Applicability Has a Declared Scope | Reworded 2026-09-22: explicitly-global scope is one legitimate declared scope; prohibition is against accidental universality only. | Accepted (revised) |

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
| Political stability is never a default outcome *(new this follow-up, originally POL-02)* | SOC-03 (Batch 09); PROG-05 (Batch 07) | `politics-authority.md` |
| Sanction execution requires a real causal mechanism | CAUSE-01 (Foundational); AUTH-01 (Batch 02) | `law-enforcement.md` |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Result |
|---|---|---|---|---|
| IP-S01 | Founder Dies | guild persists past founder's death | Organizations | Covered |
| IP-S02 | Member Leaves | individual and org both persist | Organizations | Covered |
| IP-S03 | Member Disobeys | valid order, member refuses | Organizations (inherited) | Partial |
| IP-S04 | Office Outlives Occupant / Institution Hosted by Organization | authority vacant, later refilled; three concepts distinguishable without separate objects | Roles/Institutions | Partial + covered (extended) |
| IP-S05 | Unauthorized Actor Succeeds | power without authority, compliance | Roles/Institutions (inherited) | Partial |
| IP-S06 | Invalid Claimant | conditions unmet, authority withheld | Roles/Institutions, Politics | Revealed gap |
| IP-S07 | Contested Claim / Legitimacy Constitutes Authority Where Declared | two claimants; recognition completing makes authority valid | Roles/Institutions | Revealed gap (both clauses) |
| IP-S08 | Kinship Does Not Grant Office | child exists, another candidate chosen | Politics | Covered (analogue) |
| IP-S09 | Organization Split | fracture, continuity undeclared | Organizations | Revealed gap |
| IP-S10 | Organization Merge | combination, identity undeclared | Organizations | Revealed gap |
| IP-S11 | Law Exists but Nobody Knows | unknowing violation | Law/Enforcement | Revealed gap |
| IP-S12 | Violation Undetected | no observer, no enforcement | Law/Enforcement | Revealed gap |
| IP-S13 | False Accusation | false report, real institutional action | Law/Enforcement | Revealed gap |
| IP-S14 | Unauthorized Spending | access without authority | Organizations (inherited) | Revealed gap |
| IP-S15 | Enforcement Fails / Without Separate Judgment | valid sanction, execution fails; automatic consequence needs no judgment stage | Law/Enforcement | Revealed gap (both clauses) |
| IP-S16 | Law Is Ignored | repeated disobedience, law stays valid | Law/Enforcement | Revealed gap |
| IP-S17 | Individual Becomes Institutionally Significant | ordinary person, org reacts by name | Organizations (inherited) | Revealed gap |
| IP-S18 | Organization Wealth / Standing Policy Without Fresh Decision | authorized member spend; automatic tax process is a valid standing-policy shape | Organizations | Partial + covered (extended) |
| IP-S19 | Conflicting Memberships | two orgs conflict, individual chooses | Organizations (inherited) | Revealed gap |
| IP-S20 | Institutional Memory | declared record survives official's departure | Organizations (inherited) | Partial |
| IP-S21 | Powerful/Illegitimate & Legitimate/Weak / Power Without a Power Stat | both directions of the authority/power split; power derivable without a canonical field | Roles/Institutions | Partial + covered (extended) |

## Coverage Summary

**Organizations**
- identity persists independent of members — IP-S01, IP-S02
- membership ≠ six other concepts — IP-S02, IP-S03, IP-S19
- organizational process + execution path, standing policy permitted — IP-S18 (both clauses)
- split/merge/dissolution require declared process — IP-S09, IP-S10

**Roles/Institutions**
- organization/institution/role distinctness without mandatory materialization — IP-S04 (both
  clauses)
- delegation distinctness — (no scenario; absence is the finding)
- authority/capability/power/legitimacy, correlated not substitutable, power derivable — IP-S05,
  IP-S21 (both clauses)
- legitimacy ≠ belief/reputation/compliance, causal relationship institution-declared — IP-S06,
  IP-S07 (both clauses)

**Politics/Authority**
- succession ≠ kinship/property — IP-S08
- no default stability — (no scenario; the real diplomatic-tension channel is standing
  evidence, not a probe)

**Law/Enforcement**
- distinct law/knowledge/compliance/detection/adjudication/sanction facts, no mandatory
  pipeline — IP-S11, IP-S12, IP-S15 (both clauses), IP-S16
- institutional record ≠ truth/belief — IP-S13
- jurisdiction has a declared scope, including explicitly-global — IP-S11

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
  AUTH-06 unchanged.
- Politics ↔ Lineage/Descent (Batch 09): POL-01 directly resolves the succession boundary
  `lineage-descent.md` explicitly deferred to this batch.
- Politics ↔ Social Relations (Batch 09), Capability/Progression (Batch 07): the reclassified
  open-instability Inherited entry (originally POL-02) confirms this batch's own "stability is
  never a default" content was already fully covered by SOC-03 and PROG-05 — a clean
  application, not new territory.
- Politics ↔ Capability/Progression (Batch 07), Economy/Exchange (Batch 08): the
  power-conversion Inherited entry reuses PROG-07/EXCH-01's own already-established
  "conversion edges are specific, never universal" pattern for political conversion.
- Organizations ↔ Capability/Progression (Batch 07), Lineage/Descent (Batch 09): IP-S17
  confirms the "ordinary individual becomes historically significant by name" gap recurs at
  the organizational scale, the third scale (individual, lineage, organization) at which this
  same shape has now been found.
- Law/Enforcement ↔ Social Relations (Batch 09): LAW-02's institutional-record concept is
  related to, but distinct from, the reputation-reach CONFLICTING finding `social-relations.md`
  already recorded — confirmed still distinct on re-inspection this follow-up, per item 7's own
  instruction to keep LAW-02 unless canonical inspection revealed duplication; none was found.

**Explicit call-out — genuine Domain Rule count:** **12** (was 13 before this follow-up
reclassified POL-02).

**Explicit call-out — organization identity vs. member identity:** **Distinct, confirmed by
construction.** `FactionState`/`ClanState` are keyed by their own ids; leadership is a
replaceable pointer, not the organization's own identity (ORG-01).

**Explicit call-out — organization vs. institution vs. role semantics:** **Kept distinct as
target concepts (INST-01, revised); separate persistent-state materialization is explicitly
NOT required** — an organization may embody its own institution and role with no separate
objects, confirmed as the actual shape `ClanState` already uses.

**Explicit call-out — whether roles survive occupant turnover:** **Yes, both outcomes
(survival and ending) are real, per AUTH-06's own evidence, reused unchanged for this batch's
own institutional/political subject matter.**

**Explicit call-out — authority vs. power vs. legitimacy distinction:** **All four remain
semantically distinct dimensions (INST-03, revised) — but not independent; real causal
relationships between them (legitimacy → authority, wealth → power) are explicitly permitted,
and none may substitute for another merely because they correlate.** Power is never required
to be a canonical scalar; it may be derived relationally.

**Explicit call-out — whether membership actually affects decisions without forcing them:**
**Yes, confirmed by absence of any forcing mechanism** — `ClanLifecycleService.
process_leave()`'s own unconditional shape and the absence of any behavior-override tied to
`member_entity_ids` (ORG-02).

**Explicit call-out — whether organizational resources can be used by authorized members:**
**No — confirmed MISSING.** Only a fully automatic systemic process (`TownResolutionSystem`)
touches `state.global_resources`; no member-initiated, authorized or unauthorized, spend path
exists. That same automatic process is, however, confirmed as a clean positive instance of
ORG-03's own revised "standing policy" permission (IP-S18's extended clause).

**Explicit call-out — whether organizational knowledge is distinct from member knowledge:**
**Yes as a target requirement (reusing Batch 06); realized only as one INERT/OFF candidate
path** (`ENABLE_INFORMATION_HUB_ACCUMULATION`) **in one direction, and confirmed MISSING in the
reverse direction.**

**Explicit call-out — whether law existence is distinct from knowledge/compliance/
enforcement:** **Yes as target semantics (LAW-01, revised — now nine distinct facts, no
mandatory pipeline); entirely MISSING as a repository realization** — no in-world law/crime/
violation/sanction subsystem exists at all.

**Explicit call-out — whether enforcement respects perception/reach/capability/authority:**
**Not independently testable — no enforcement mechanism exists to check this against.** The
target requirement (LAW-01's own "sanction decided ≠ sanction executed" constraint, which
this follow-up confirmed as the one part of the chain that always holds regardless of which
other stages a system uses) is stated regardless.

**Explicit call-out — whether political succession is distinct from property inheritance:**
**Yes, confirmed by the same structural pattern found for kinship at Batch 09's own lineage
scale** (`_select_default_heir()`) **now reconfirmed at the group-leadership scale**
(`ClanLifecycleService.process_succession()`) **— neither ever reads kinship or property
facts.** Whether this is itself "political succession" or a distinct, unrealized concept one
scale up remains an open question (POL-01).

**Explicit call-out — whether institutions retain history across occupant/member turnover:**
**Partially.** No magical individual-memory transfer exists (confirmed by absence, the
correct outcome); genuine declared institutional record-keeping is real but narrow.

**Explicit call-out — whether ordinary individuals can become institutionally significant by
name:** **No — confirmed MISSING, the third scale (after individual and lineage) at which this
identical flagship gap has now been found (IP-S17), reconfirmed as a still-open, still-visible
gap by this follow-up's own item 11.**

**Explicit call-out — which political/institutional state is inert or omniscient:**
`ENABLE_INFORMATION_HUB_ACCUMULATION` is INERT/OFF; nothing checked was found to be
omniscient in this batch's own new territory, because the mechanisms that would need to
respect an information boundary are themselves confirmed MISSING rather than present-and-
ungated.

## Repository Findings

Classified per the CONFLICTING/INERT-OFF/MISSING distinction Batch 06/07/08/09 established.
**These are repository/implementation facts, not World Rule decisions, and per the standing
direction, imply no delivery priority.** The follow-up's own item 11 asked that six major
findings stay prominent regardless of any rewording elsewhere — they are the first six items
below.

1. **Organizations already have persistent identity independent of members.** ORG-01,
   confirmed SUPPORTED by `FactionState`/`ClanState`'s own construction.
2. **Institution/role/legitimacy/law are largely unrealized.** INST-01/03/04, LAW-01–03 —
   confirmed MISSING across the board, with one narrow exception (`ClanState.
   leader_entity_id` as a bare occupant pointer).
3. **Organization-member resource access is missing.** See the resource-ownership Inherited
   entry — no authorized-member draw path exists, though the *organization-level* automatic
   process is itself a confirmed positive instance of ORG-03's own revised permission.
4. **Institutional knowledge transfer is mostly unrealized.** One INERT/OFF candidate path
   exists in one direction (`ENABLE_INFORMATION_HUB_ACCUMULATION`); the reverse direction is
   confirmed MISSING entirely.
5. **Ordinary individual → named institutional recognition remains missing.** IP-S17 — the
   third scale (after Batch 07's individual scale and Batch 09's lineage scale) at which this
   identical, now-recurring, cross-domain structural gap has been found. Kept visible per the
   follow-up's own explicit instruction, since this is no longer an isolated missing feature.
6. **Law/enforcement has essentially no in-world repository realization.** LAW-01–03 — the
   largest single gap this batch found, spanning an entire rule family.

**INERT/OFF (1 finding):**
7. `ENABLE_INFORMATION_HUB_ACCUMULATION` gates the one real candidate individual→
   institutional information path found (`src/engine/quests.py`); defaults OFF.

**MISSING (6 further findings, beyond items 2–6 above):**
8. No organization split or merger mechanism exists (ORG-04).
9. No delegation mechanism of any kind exists (INST-02).
10. No political office concept exists for POL-01's own succession rule to apply to.
11. Every named political power-conversion edge checked is unrealized.
12. No law-specific jurisdiction-scoping mechanism exists, though the general
    location-plus-affiliation pattern is real elsewhere (LAW-03).
13. Multi-organization-kind conflict resolution (IP-S19) is unrealized, distinct from the real
    multi-membership *capacity* itself.

**A significant, notable finding, not itself CONFLICTING/INERT/MISSING but worth its own
category:**
14. Two structurally separate "faction" representations exist in this repository (the legacy
    `Faction` IntEnum and the richer `FactionState`/catalog `faction_id`), deliberately
    bridged via `get_legacy_faction_bucket()` — the same shape as Batch 09's own resolved
    reputation-naming-collision finding. This repository also uses the word "role" for at
    least three unrelated concepts.

Key evidence, all confirmed by direct code/doc inspection: `src/core/state.py` (`FactionState`,
`ClanState`, `GroupRecord`), `src/core/enums.py` (`Faction`), `src/content_semantics/
faction.py`, `src/systems/social_systems/clan_lifecycle.py`, `src/engine/town_resolution.py`,
`src/engine/tactical.py`, `src/domains/faction/diplomatic_state_machine.py`,
`src/domains/optimization/feature_flags.py`, `src/engine/quests.py`,
`src/observability/{hard_law_monitor,anomaly}/*` (confirmed unrelated meta-level tooling),
`docs/world_rules/foundations/authority.md` (AUTH-01–06, reused directly),
`docs/world_rules/foundations/identity.md` (ID-06).

## Owner-attention decisions (design semantics, per the standing direction)

Revised 2026-09-22 per the follow-up's own item 9 — storage/data-shape questions moved to
Implementation Candidates below; only design-semantic questions remain here:

- **Is practical power authoritative state or a derived relation?** (Revised from "does Power
  deserve its own tracked field.")
- **What semantic facts make an institution distinct from its hosting organization, given
  that INST-01 no longer requires separate materialization?** (Revised from "does Organization
  need its own durable-state category distinct from Institution.")
- **Can one record simultaneously serve institutional and individual epistemic roles without
  violating ownership?** (Revised from "should institutional record reuse `BeliefEntry`'s data
  shape.")
- **Under what declared conditions does legitimacy affect authority?** INST-04's own revision
  leaves this open by design — not decided here.
- Is `ClanLifecycleService.process_succession()` a genuine instance of "political succession"
  (POL-01), or does political succession name a distinct concept one scale above ordinary
  group leadership, currently entirely unrealized?
- Is multi-membership *within* one organization kind (e.g., two Clans) something the target
  model should positively support or explicitly forbid?
- Does LAW-03's jurisdiction concept belong fully to this batch, or should its own depth wait
  until Batch 11 supplies real spatial/territorial primitives to ground it against?

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.** Per the
follow-up's own item 12: possible implementation shapes are preserved here without feeding
backward into Rule wording.

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
  reputation, and compliance, with its causal relationship to authority declared per
  institution.
  **Current realization:** no field represents this concept.
  **Possible implementation direction:** a claim/recognition record analogous in shape to
  `PublicReputationProfile`, read independently of `public_reputation`, with a per-institution
  declared rule for how (or whether) it gates authority.
  **Implementation decision:** DEFERRED.
- **Target semantic:** political succession requires its own declared eligibility/validity
  rule, distinct from kinship and property.
  **Current realization:** only group-leadership-scale succession exists; no larger
  political-office concept.
  **Possible implementation direction:** an `OfficeState`-shaped record with its own
  succession-rule declaration, if investigation later confirms group-leadership succession is
  not itself sufficient.
  **Implementation decision:** DEFERRED.
- **Target semantic:** rule existence, applicability, subject action, compliance/violation,
  knowledge/belief, detection, adjudication, sanction decision, and sanction execution are
  distinct, independently-failing facts.
  **Current realization:** none of these exist as in-world concepts.
  **Possible implementation direction:** a minimal declared-rule/violation-record mechanism,
  potentially reusing the `ReasonCode`/legality-check machinery's own shape (Batch 02's AUTH
  family) alongside a typed violation record analogous to `BetrayalRecord` (Batch 09) — shaped
  so a domain can choose to skip stages (e.g., detection → automatic consequence, no separate
  adjudication) rather than requiring every stage.
  **Implementation decision:** DEFERRED.
- **Target semantic:** practical power may be derived relationally rather than tracked as its
  own canonical scalar (INST-03, revised).
  **Current realization:** `FactionState.military_strength` is the one real proxy, and it is a
  tracked field, not a derived relation.
  **Possible implementation direction:** a power-scoring function reading
  resources/capabilities/relationships/authority/reach/information according to declared
  causal paths, as an alternative to (or validation of) the existing tracked-field approach.
  **Implementation decision:** DEFERRED.

## Candidate disposition

Thirteen Domain Rules were originally drafted across four families; this follow-up
reclassified one (POL-02) to Inherited after re-testing it against the admission discipline,
leaving **12 accepted Domain Rules, 1 reclassified, 0 rejected, 0 split, 0 merged.** No target
rule count was set in advance, per the batch instruction's own explicit guidance and the
follow-up's own explicit instruction not to preserve the original count artificially. Eleven
entries are now Inherited/Applied Foundational Rules (10 original + 1 reclassified) and eight
remain Scope/Deferred Boundaries.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/institutions-politics-batch-10-report.md` (local review report, not part of this
catalog).

---

> **BATCH 10 (ORGANIZATIONS / INSTITUTIONS / POLITICS / LAW) — PASS, READY TO FREEZE.**
>
> Target semantics are coherent. Repository realization is substantially incomplete in
> institutional, political, and legal domains. No implementation commitment is implied by
> this freeze.

All required artifacts exist and are current: four rule-family files (12 genuine Domain
Rules; 31 total catalog entries), one scenario file (21 scenarios, five extended in place per
this follow-up's own five adversarial probes), this review export with all required sections
including the Implementation Candidates — Non-Binding section, and a local disposition
report. No target-semantic contradiction remains: this follow-up's own eleven numbered items
were each resolved — ORG-03 generalized to permit standing policy; INST-01 refined to remove
the mandatory-materialization implication; INST-03 refined from independence to
non-substitutability; INST-04 refined to remove a universal legitimacy-authority claim;
POL-02 reclassified after failing the admission test on stricter re-examination; LAW-01
generalized from a mandatory six-stage chain to nine distinct, optionally-used facts; LAW-02
preserved unchanged after confirming no duplication; LAW-03 refined to permit an
explicitly-global declared scope; Owner-Attention cleaned of storage-shaped questions; five
adversarial probes added by extension; and the six major findings kept visible per the
follow-up's own explicit list. This batch's own dominant finding remains breadth of MISSING
realization (an entire rule family, Law/Enforcement, has no in-world counterpart at all)
rather than a present violation of accepted semantics — consistent with the standing
direction's own framing that PASS means target semantics are coherent and honestly evaluated,
never that the repository fully implements the domain.

Batch 11 (Places / Settlements / Territory / Culture / Belief) has no instruction file yet in
`tmp/` at the time of this freeze. Per this Catalog's own discipline against guessing at
content the user has not yet supplied, Batch 11 does not begin until its own instruction file
is provided.
