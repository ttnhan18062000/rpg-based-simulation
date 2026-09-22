---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Scenario Bank: Organizations / Institutions / Politics / Law (Batch 10)

**Purpose/scope.** Twenty-one scenarios used to pressure-test the Organizations, Roles/
Institutions, Politics/Authority, and Law/Enforcement rule families in
`institutions-politics/organizations.md`, `roles-institutions.md`, `politics-authority.md`,
and `law-enforcement.md`, per `tmp/world-rule-batch-10-ext-ai.md`'s own §25 seed list, plus
five adversarial probes added by the 2026-09-22 follow-up
(`tmp/world-rule-batch-10-followup-ext-ai.md`'s §10) — extended in place onto IP-S04, IP-S07,
IP-S15, IP-S18, and IP-S21 rather than as new IDs, per that follow-up's own explicit
instruction to reuse/extend existing scenarios where possible.

Per the standing direction (`tmp/world-rule-direction.md`): a scenario failing against the
current repository does not mean the scenario or its Rule fails — it may simply show target
semantics are valid while repository realization is MISSING/PARTIAL/CONFLICTING. Scoring uses
the same vocabulary as prior batches: **covered** / **partially covered** / **blocked** /
**revealed missing rule** / **revealed contradiction**, against current repository behavior,
not the ideal design.

---

## IP-S01 — Founder dies, organization persists

A founder creates a guild; the guild develops members, resources, and history; the founder
dies; the guild continues.

- **Rules invoked:** ORG-01, ORG-03.
- **Result: covered.** `ClanState` is keyed by its own `clan_id`, never by its founder's
  entity id. `ClanLifecycleService.process_succession()` replaces a dead leader with a new
  member chosen by sociability score, and `process_dissolution()` only ends the clan once
  membership *and* assets are both empty — a founder's own death, by itself, neither field
  nor function treats as clan-ending.

## IP-S02 — Member leaves

A member exits the organization; the individual persists; the organization persists;
historical membership remains a true fact.

- **Rules invoked:** ORG-01, ORG-02.
- **Result: covered.** `ClanLifecycleService.process_leave()` removes the entity from
  `member_entity_ids` unconditionally — no appraisal gate, no side effect on the clan's own
  identity or the departed entity's own continued existence. Whether "historical membership
  remains true" as its own queryable fact was not confirmed — no code path was found that
  retains a *former*-membership record after departure; this is a narrower gap than the
  scenario's own full claim, recorded as a repository finding rather than a Rule violation
  (ORG-01/02 do not require a former-membership record to exist, only that departure not undo
  the organization's or individual's own identity).

## IP-S03 — Member disobeys

A leader issues a valid order; the member has a real authority relationship to the leader;
the member refuses.

- **Rules invoked:** ORG-02, Inherited (authority never guarantees compliance, Batch 06's
  AGENCY-01/02).
- **Result: partially covered.** `ClanState.leader_entity_id` is a real authority relationship
  the repository recognizes structurally, and nothing in `ClanLifecycleService` forces member
  behavior from it — membership is confirmed not to be a universal behavior override,
  consistent with ORG-02. A specific "leader issues an order, member's own decision process
  evaluates it and can refuse" causal path (as opposed to the general AGENCY-01/02 machinery
  this Rule reuses) was not independently confirmed to exist for the Clan/leader relationship
  specifically.

## IP-S04 — Office outlives occupant / institution hosted by organization

An officeholder dies; the office remains; authority becomes vacant; a successor later occupies
the same office. **Extended per the 2026-09-22 follow-up's own §10 "Institution Hosted by
Organization" probe:** the guild persists; the guild hosts an office and institutional rules;
organization, institution, and role remain conceptually distinguishable; no requirement exists
for three separately-materialized subjects.

- **Rules invoked:** INST-01 (revised), Inherited (role/office persists across occupant
  change, AUTH-06).
- **Result: partially covered.** `ClanLifecycleService.process_succession()` is the clearest
  real instance of authority surviving occupant change (AUTH-06's own evidence, reused). The
  "office" half of this scenario is not independently confirmed as a *governing-rule* concept,
  since no institutional-semantics content beyond the bare occupant pointer was found — but per
  INST-01's own revision, this is no longer itself a gap: `ClanState` embodying its own
  leadership role directly, with no separate "Institution"/"Role" object anywhere, is exactly
  the permitted shape this Rule's own revision describes. **Extended clause: covered.** The
  conceptual distinction (organization/institution/role are not the same idea) holds regardless
  of `ClanState` never materializing them separately — nothing in the repository conflates a
  clan's own identity with its leadership slot's own identity, confirming the two concepts
  remain distinguishable even when embodied in one object.

## IP-S05 — Unauthorized actor succeeds

An actor lacks formal authority, has coercive capability, and others comply anyway.

- **Rules invoked:** INST-03, Inherited (authority never guarantees compliance).
- **Result: partially covered.** `FactionState.military_strength` is a real, tracked coercive
  capacity independent of any formal-authority field (INST-03's own PARTIAL evidence) — the
  data shape permits this scenario. A specific causal trace of "others comply *because of* an
  unauthorized actor's coercive capability, despite that actor lacking authority" was not
  independently confirmed as a live decision-time mechanism.

## IP-S06 — Invalid claimant

A person claims an office; institutional succession conditions are unmet; the claim exists;
authority is not automatically granted.

- **Rules invoked:** INST-04, POL-01.
- **Result: revealed missing rule.** No office/claim concept exists for a "claim" to be made
  against at all (INST-01's own finding) — confirmed MISSING directly. INST-04's own target
  semantics (a claim existing ≠ authority being granted) remain coherent and testable in
  principle, but this repository has nothing for the scenario to exercise.

## IP-S07 — Contested claim / legitimacy constitutes authority where declared

Two claimants exist; different subjects/institutions recognize different claimants; canonical
institutional status stays separate from belief where applicable. **Extended per the
2026-09-22 follow-up's own §10 "Legitimacy Constitutes Authority Where Declared" probe:** a
claimant satisfies most office conditions; a recognition procedure is incomplete; authority is
not yet valid; the recognition procedure completes; authority becomes valid — without this
being treated as a universal rule for every institution.

- **Rules invoked:** INST-04 (revised).
- **Result: revealed missing rule.** Same underlying gap as IP-S06 — confirmed MISSING. No
  canonical institutional-status field exists for two beliefs to diverge around. **Extended
  clause: revealed missing rule, same underlying gap.** INST-04's own revision permits a
  domain to declare "authority becomes valid only once recognition completes" as one legitimate
  pattern among several — but with no institutional-claim or legitimacy concept realized at
  all, no mechanism exists to exercise even one such declared pattern, let alone confirm this
  repository chooses it over the alternative (appointment alone establishes authority).

## IP-S08 — Kinship does not automatically grant office

A ruler dies; a child exists; the succession rule chooses another candidate.

- **Rules invoked:** POL-01.
- **Result: covered, by a structurally close analogue, with an important qualifier.**
  `ClanLifecycleService.process_succession()` never reads `parent_a_entity_id`/
  `parent_b_entity_id` — kinship is confirmed never automatically sufficient for succession,
  continuing Batch 09's own `lineage-descent.md` finding one domain further. The qualifier:
  this is evidence at the *group-leadership* scale, not a confirmed "political office" scale
  succession, since no office concept exists independently (POL-01's own open question).

## IP-S09 — Organization split

A guild fractures into faction A and faction B; continuity, history, and assets require
declared semantics.

- **Rules invoked:** ORG-04.
- **Result: revealed missing rule.** No faction or clan split mechanism exists anywhere —
  confirmed MISSING directly, via broad search. ORG-04's own target requirement (a declared
  process must determine the five listed facts) has nothing to check yet.

## IP-S10 — Organization merge

Two groups combine; a new or continued identity must be declared.

- **Rules invoked:** ORG-04.
- **Result: revealed missing rule.** Same underlying gap as IP-S09 — confirmed MISSING.

## IP-S11 — Law exists but nobody knows

An institution adopts a rule; a distant or new subject has not received the information; the
subject violates it unknowingly.

- **Rules invoked:** LAW-01, LAW-03, Inherited (organizational knowledge ≠ member knowledge,
  `organizations.md`).
- **Result: revealed missing rule.** No in-world law concept exists for a rule to be "adopted"
  by at all (LAW-01's own finding) — confirmed MISSING. The organizational-knowledge-boundary
  half this scenario would also exercise (a subject not having received institutional
  information) is separately confirmed real in principle via `ENABLE_INFORMATION_HUB_
  ACCUMULATION`'s own INERT/OFF status (`organizations.md` evidence), but with no law concept
  to attach it to, the scenario's own full trajectory cannot be exercised.

## IP-S12 — Violation goes undetected

An act violates a valid law; no observer or report exists; no enforcement follows.

- **Rules invoked:** LAW-01.
- **Result: revealed missing rule.** Same underlying gap as IP-S11 — confirmed MISSING; no
  law/violation concept exists to go undetected.

## IP-S13 — False accusation

No violation occurred; a false report is accepted; an institutional process begins; a real
consequence becomes possible.

- **Rules invoked:** LAW-02.
- **Result: revealed missing rule, with a related but distinct real counter-example
  elsewhere.** No institutional-record/accusation mechanism exists — confirmed MISSING. Batch
  09's own individual-scale analogue (`social-lineage/scenarios/social-lineage-batch-09.md`'s
  SL-S05, false accusation causing lasting individual hostility) is real and covered at the
  individual scale; this scenario confirms the same pattern has no institutional-scale
  counterpart yet.

## IP-S14 — Unauthorized spending

A member can physically access a treasury but lacks institutional authority; an attempted
spend has different semantics from an authorized allocation.

- **Rules invoked:** Inherited (organizational resource ownership ≠ member ownership,
  `organizations.md`).
- **Result: revealed missing rule.** No member-initiated spend path of any kind exists —
  authorized or unauthorized — confirmed MISSING via `organizations.md`'s own investigation.
  The scenario's own distinction (authorized vs. unauthorized spend having different
  semantics) cannot yet be exercised, since neither case is realized.

## IP-S15 — Enforcement fails / enforcement without a separate judgment stage

A valid sanction is ordered; the enforcing agent lacks capability, reach, or resources; the
sanction is not executed. **Extended per the 2026-09-22 follow-up's own §10 "Enforcement
Without Separate Judgment" probe:** a declared rule exists; a violation is detected; a declared
automatic consequence executes with no separate adjudication stage — testing that LAW-01
(revised) does not accidentally require every intermediate stage.

- **Rules invoked:** LAW-01 (revised), Inherited (sanction execution requires a real causal
  mechanism, `law-enforcement.md`).
- **Result: revealed missing rule.** No sanction-ordering or sanction-execution mechanism
  exists — confirmed MISSING. The target semantic (execution may fail independently of the
  order's own validity) remains coherent; nothing realizes either half yet. **Extended clause:
  revealed missing rule, same underlying gap — but the Rule's own permission is confirmed
  coherent even without repository evidence.** LAW-01's own revision explicitly permits
  "detected violation → automatic declared consequence" as one legitimate shape with no
  separate judgment stage; this repository has no detection or consequence mechanism to
  exercise the pattern against, but the target semantics themselves impose no requirement that
  a judgment stage exist, so this scenario finds no tension between the Rule and what a future
  minimal implementation could look like.

## IP-S16 — Law is ignored

A law applies; subjects repeatedly disobey; the law remains formally valid unless a declared
process changes it.

- **Rules invoked:** LAW-01.
- **Result: revealed missing rule.** Same underlying gap — confirmed MISSING; no law exists to
  be ignored or to remain formally valid.

## IP-S17 — Individual becomes institutionally significant

An ordinary non-HERO individual takes repeated meaningful actions; an organization records
this history; the organization changes access, hostility, role, or opportunity toward this
individual specifically.

- **Rules invoked:** Inherited (organizational knowledge, `organizations.md`); cross-references
  Batches 07/09's own ordinary-individual-significance findings.
- **Result: revealed missing rule.** Confirmed MISSING directly: `FactionSentiment` is
  faction-to-faction only; no per-(organization, specific individual) standing field exists
  anywhere (`organizations.md`'s own Repository Findings). This is the organizational-scale
  continuation of the same flagship gap Batches 07 (PROG-06/CP-S15) and 09 (LIN-02/SL-S15)
  already found at the individual and lineage scales.

## IP-S18 — Organization wealth / standing policy without a fresh decision

An organization owns a treasury; an authorized member spends a subset; personal ownership does
not arise automatically from the spend. **Extended per the 2026-09-22 follow-up's own §10
"Standing Policy Without Fresh Decision" probe:** the organization establishes a valid standing
policy; a recurring process executes later; an organization-attributed consequence occurs; no
fresh collective decision is made each time.

- **Rules invoked:** ORG-03 (revised), Inherited (organizational resource ownership ≠ member
  ownership).
- **Result: partially covered.** Organizational ownership of `state.global_resources` as its
  own fact, distinct from any member's personal `inventory.gold`, is confirmed real
  (`organizations.md`'s own evidence). The "authorized member spends a subset" half is
  confirmed MISSING — the only mechanism that touches the vault is `TownResolutionSystem`'s
  own fully automatic tax/maintenance pass, never an individual member's own authorized draw.
  **Extended clause: covered.** That same automatic tax/maintenance pass is exactly the
  "standing policy, no fresh decision" shape ORG-03's own revision permits — `is_tax_tick`
  triggers a real, organization-attributed resource change on a declared schedule with no
  per-occurrence authorization check, confirming this Rule's own revised requirement (a real
  process + a real execution path, not necessarily a fresh authorized decision) is already
  satisfied here rather than merely permitted in the abstract.

## IP-S19 — Conflicting memberships

An individual belongs to organization A and organization B; A and B enter conflict; the
individual receives incompatible obligations; a decision, and later history, follows.

- **Rules invoked:** ORG-02, Inherited (membership does not determine action;
  multi-membership conflict resolves through the decision layer).
- **Result: revealed missing rule.** Multi-organization membership across different kinds is
  real (an entity may hold Clan + Group + Faction affiliation simultaneously), but no scenario
  was found where two of an entity's own memberships issue conflicting directives that any
  decision system resolves — confirmed MISSING for the conflict-resolution half specifically,
  distinct from the underlying multi-membership capacity, which is real.

## IP-S20 — Institutional memory

An official learns and records an important fact; the official later dies or leaves; the
institution retains the record through a declared mechanism, not a magical transfer of the
official's own memory.

- **Rules invoked:** Inherited (institutional memory persists through declared record-keeping,
  `organizations.md`).
- **Result: partially covered.** The negative half (no magical individual-memory-to-
  institution transfer exists) is confirmed SUPPORTED by absence — no such mechanism was found.
  The positive half (an official's own learned fact becoming a real, declared institutional
  record) is confirmed MISSING — `FactionState`/`ClanState`'s own retained fields
  (`diplomatic_relations`, `military_strength`, `tension_level`, `clan_reputation`) are real
  but are not populated by any individual official's own act of "learning and recording" a
  specific fact.

## IP-S21 — Powerful but illegitimate / legitimate but weak (both directions) / power without a power stat

A warlord controls forces and resources, can cause outcomes, but lacks a recognized office.
Separately: a recognized ruler holds office but lacks resources or forces, and orders often
fail. **Extended per the 2026-09-22 follow-up's own §10 "Power Without a Power Stat" probe:**
an actor controls soldiers, resources, and information; the actor can cause outcomes others
cannot; practical power exists; no canonical numeric Power field is required for this to hold.

- **Rules invoked:** INST-03 (revised).
- **Result: partially covered, in both directions.** `FactionState.military_strength` gives a
  real, tracked practical-capacity fact independent of any formal-authority field — the data
  shape supports "powerful but illegitimate" in principle. The "legitimate but weak" direction
  is confirmed MISSING on the legitimacy side specifically (no legitimacy/recognition concept
  exists at all, INST-04's own finding), though "holds a role but has low practical capacity"
  is representable in principle via the same independent `military_strength` field simply
  being low rather than high. **Extended clause: covered.** INST-03's own revision explicitly
  permits power to be derived relationally rather than requiring a canonical scalar; while this
  repository's own one real proxy happens to be a tracked field (`military_strength`), nothing
  in this Rule's own target semantics required that shape — a future domain modeling power as
  derived purely from `resources + capabilities + relationships` without any dedicated field
  would satisfy this Rule exactly as well, confirming the permission is genuine and not merely
  theoretical.

---

## Cross-batch note

IP-S08's own finding (clan succession never reads kinship fields) is the organizational-scale
continuation of Batch 09's own `lineage-descent.md` finding (`_select_default_heir()` never
reads `parent_a/b_entity_id` either) — the same repository pattern, now checked at a second,
independent succession mechanism, both confirming the target boundary (kinship ≠ automatic
eligibility) holds cleanly wherever it has been checked.

IP-S17's own finding continues the same flagship gap Batch 07 (PROG-06/CP-S15, individual
scale) and Batch 09 (LIN-02/SL-S15, lineage scale) already found — this batch confirms the
identical shape holds at the organizational scale too: real, narrow, individual-history
channels exist at smaller scales, but nothing yet lets a collective institution track and
react to one specific ordinary individual by name.

IP-S06/S07/S09/S10/S11/S12/S13/S15/S16 together show this family's own realization is not
merely partial in the way earlier batches found (a real mechanism with a specific resolver gap
or an inert flag) — the entire Politics/Law territory these nine scenarios probe has **no
in-world realization to check against at all**. Per the standing direction
(`tmp/world-rule-direction.md`), this is recorded honestly as a load-bearing semantic gap, not
as evidence against the target semantics themselves, and implies no delivery priority.

The 2026-09-22 follow-up's own five extended clauses (IP-S04, IP-S07, IP-S15, IP-S18, IP-S21)
each confirm the same shape: none revealed a genuine tension between the revised Rules'
own broadened permissions and the repository's own real evidence. IP-S18's extended clause is
the one case where the extension turned a previously-"MISSING-adjacent" reading into a clean
**covered** result — `TownResolutionSystem`'s automatic tax pass was already exactly the
"standing policy, no fresh decision" shape ORG-03's own revision anticipated, simply not
recognized as such under the original, more mandatory wording.
