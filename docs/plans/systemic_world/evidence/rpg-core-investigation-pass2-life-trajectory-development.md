---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated evidence snapshot supporting `docs/plans/systemic_world/roadmap.md`, copied from the local working file `rpg-core-investigation-pass2-life-trajectory-development.md` on 2026-09-27. Where the roadmap has since corrected a claim, the roadmap is authoritative.

# Investigation Report — Pass 2: Life Trajectory & Development

**Scope:** capability/skill growth, profession/role/class/organizational evolution, equipment/
material progression, wealth/economic mobility, relationships and social-network development,
reputation/recognition propagation, faction/institutional access, opportunity generation,
geographic access/migration, failure/regression/injury/debt/exclusion/loss-of-status, long-term
feedback from lived history, trajectory lock-in/reversal/branching.

**Method:** `search_docs` first, then direct file reads/grep, every claim cited to a file:line, a
ticket ID, or a Catalog Rule. `UNKNOWN` used explicitly where evidence didn't resolve a question.
This pass leans heavily on one piece of prior art `search_docs` surfaced that was not previously
known to this investigation track: `docs/brainstorm/2026-09-19-core-rpg-lived-history-growth-
brainstorm.md` — a near-complete, 22-scenario, repo-grounded trace of exactly this pass's central
question, checked against `origin/main@74c11ceb7` six days before this pass. Rather than re-derive
that tracing from scratch, this report verifies its highest-stakes claims against current code
(§ "Verification of the brainstorm doc's claims, six days later") and builds Pass 2's own required
sections on top of the combined, corrected evidence.

**Two classification axes, kept separate, per Pass 1's convention:**
- **Semantic assessment** (does a Rule exist for this at all): *already covered* / *covered but
  realization incomplete* / *semantically ambiguous* / *genuine World Rule gap* / *derived-narrative
  only*.
- **Existing Rule realization status**: `SUPPORTED` / `PARTIAL` / `CONFLICTING` / `MISSING` /
  `INERT-OFF` / `UNKNOWN`.

**Constraint honored:** `docs/world_rules/capability-progression/*.md`, `institutions-politics/*.md`,
`material-economy/*.md`, `social-lineage/*.md` and siblings were read-only throughout (M4 of the
Semantic Control Plane may still be live against the Capability/Progression/Conflict family). All
potential Rule changes below are prose findings, never draft Rule text.

---

## A. Executive finding

**The decision-conditioning half (Pass 1) is real and compositional. The world-reaction half (Pass
2's job) is confirmed thin — not absent, but thin in a very specific, well-evidenced way: the
*individual* side of lived history is comparatively rich (death, lineage, displacement, personal
grudges), while the *conversion-to-leverage* and *institutional-recognition* sides are almost
uniformly `MISSING`, confirmed independently by three separate sources that agree with each other:**
the Catalog's own frozen Rules (Batch 07's PROG-07, Batch 08's EXCH-01/ME-S12, Batch 10's own
politics-authority.md and `IP-S17`), the `docs/brainstorm/2026-09-19-core-rpg-lived-history-growth-
brainstorm.md` scenario trace (22 scenarios, 6 days old, independently checked against
`origin/main`), and this pass's own direct code verification.

The clearest way to state the finding: **an entity can become different, but the world mostly
cannot notice.** `TurningPointState` (Pass 1), death/lineage dispatch, and `DisplacementService`
give an entity a rich, typed, persistent internal history. But almost nothing downstream converts
that history into a *changed relationship with the world* — no per-(institution, individual)
standing field exists (`IP-S17`, confirmed MISSING directly); wealth converts into no political or
combat capability (`ME-S12`, three separate conversion paths — protection, political influence,
supply-chain control — all confirmed MISSING); reputation converts into no leverage
(`politics-authority.md`'s power-conversion-edges Rule, MISSING for every named edge checked); and
no entity can be referred to by an epithet, a name, or a notability score at all (`FormativeExperience`/
`notability`/`epithet` — zero hits anywhere in `src/`, confirmed by this pass's own grep, unchanged
from the brainstorm doc's finding 6 days ago).

**This is the same gap Pass 1 and the Final Integration Batch already named, now confirmed a fourth
and fifth time, at two more subject scales the earlier passes hadn't individually traced:**
organizational recognition of a specific individual (`IP-S17`) and economic power-conversion
(`ME-S12`). The pattern is now evidenced at five subject scales total (person, creature, object,
place, organization — Final Integration Batch) plus lineage (Batch 09) plus, now, the specific
economic and institutional-recognition mechanisms that would carry it.

**What is stronger than expected:** death and lineage are this repository's own richest, most
load-bearing lived-history substrate — not combat, and not levels. Feud inheritance, dying wishes,
displacement with an original-home marker, and heirloom transfer are all confirmed **LIVE**. The
brainstorm doc's own diagnosis (§2.8, restated here as this pass's own independent conclusion after
verification): *"the best near-term stories start from a death, not a level-up."* The 17-item
missing-link taxonomy that document derives (L0–L17) is, on this pass's own re-verification, still
accurate as a map of exactly what's missing — this pass did not find it materially stale.

**One correction to the brainstorm doc, found by this pass:** its claim that "conquest is
unreachable in practice" (Scenario E, Scenario S) is **now out of date** — not because conquest
became reliable, but because this session's own separate investigation two days ago
(`TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT`) found conquest fires via **two
independent, disagreeing threshold paths** (`FactionInfluenceService` at ±50, `WorldDynamicsSystem`
at ±100), meaning territorial conquest *does* happen, just non-deterministically — a different,
more concerning failure mode than "never fires," now queued for a quick fix. See §G.

---

## Life-development causal map (repo-grounded, replacing the brief's conceptual sketch)

```
BIOLOGY/BODY (Life-stage, Pass 1)
       ↓
DISPOSITION (Personality, fixed at spawn — Pass 1) + LIVED HISTORY (TurningPointState,
FormativeExperience-shaped events: death, betrayal, displacement — real for death/lineage/
displacement; MISSING as a generalized typed record for most other kinds)
       ↓
DECISION (ScoreModifierSystem — Pass 1, fully verified compositional)
       ↓
ACTION → SUCCESS/FAILURE (combat outcome vocabulary — Pass 1's §B; contract outcomes; harvest/
craft outcomes)
       ↓
PERSISTENT CONSEQUENCE, INDIVIDUAL SCALE — LIVE:
  - capability (XP/level, class tier — largely unverified at runtime this pass, see §G)
  - relationship (grudge_history → nemesis_ids, LIVE, verified this pass — see below)
  - wealth (inventory.gold — LIVE, thin, almost nothing to spend it on)
  - lineage (feud inheritance, dying wishes, heir selection — LIVE)
  - notoriety_score (defection, theft's reputation weight — LIVE, narrow)
       ↓
[THE GAP — L3/L4/L5/L6/L7 in the brainstorm doc's own taxonomy, independently reconfirmed by
IP-S17/ME-S12/politics-authority.md this pass]
  - no per-entity notability/name/epithet the world can refer to (MISSING, confirmed by grep)
  - no gossip/knowledge propagation about a specific notable entity (MISSING)
  - no per-(institution, individual) standing/access field (MISSING, IP-S17)
  - no wealth→leverage, reputation→leverage, office→resource-access conversion edge (MISSING,
    ME-S12 + politics-authority.md, three separate paths each independently confirmed)
       ↓
CHANGED OPPORTUNITIES/CONSTRAINTS — mostly absent as a consequence of the gap above:
  opportunity providers (resources/services/requirements — §"Opportunity-generation mechanisms"
  below) are real and live, but gate on STATE (inventory, skill level, faction, quest flags), never
  on ACCUMULATED REPUTATION or INSTITUTIONAL STANDING — a skilled, renowned entity and an
  anonymous, identical-stat entity see the same opportunity pool.
       ↓
CHANGED FUTURE DECISIONS → DIVERGENT LIFE TRAJECTORY: divergence is real at the *decision* layer
(Pass 1) but starved at the *opportunity* layer, because the opportunity layer never learns what
happened.
```

---

## Currently supported trajectory loops

| Loop | Status | Evidence |
|---|---|---|
| Death → feud inheritance → heir pursues antagonist | **LIVE** | Idea 55 `_transfer_inherited_feud`, idea 58 `_seed_dying_wish` (brainstorm doc, Scenario G) |
| Betrayal/grudge → `nemesis_ids` promotion → combat targeting priority | **LIVE, verified this pass independently of the brainstorm doc** | `src/systems/social_systems/relationships.py:96-120` — the real, wired promotion path (`grudge_history >= 3.0` → `nemesis_ids`, applied via `SocialUpdate`). `nemesis_ids` is consumed live in `src/engine/cognition.py:47,94` (targeting) and `party_composition.py:157` (role assignment) and `adventure/generator.py:143-154` (route candidate filtering). **Correction to the brainstorm doc**: it names `check_nemesis_promotion()` (`memory.py:38`) as the promotion path and marks it DORMANT — that specific function is indeed still uncalled (confirmed by this pass's own grep — only its own definition and one comment-reference exist), but it is a dead duplicate of the real, live promotion logic in `relationships.py`, which the brainstorm doc did not find. The *outcome* the doc cared about (does grudge-driven targeted response exist) is **LIVE**, contrary to the doc's own DORMANT verdict for that specific code path. |
| Calamity → displacement → original-home marker persists | **LIVE** | Idea 65 `DisplacementService` (brainstorm doc, Scenario I) |
| Death → heirloom inheritance to default heir | **LIVE** | Confirmed by brainstorm doc (Scenario D3) and this session's own earlier Pass 1 cross-reference to `material-economy/ownership-possession.md`'s PROP-02 |
| Group membership → sociability-driven leadership election → succession on leader's death | **LIVE** | `party_lifecycle.py` (Pass 1's own citation), `ClanLifecycleService` (brainstorm doc) |
| `TurningPointState` (betrayal/near_death/first_kill/great_victory/loss) → future goal-utility bias | **LIVE** | Pass 1's own central finding, fully re-affirmed here |
| Territorial conquest via influence threshold | **LIVE but non-deterministic** | Two disagreeing threshold paths confirmed by this session's own `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` investigation — see §G |

---

## Non-combat development evidence

The brainstorm doc's own Scenario J (Smith lineage) and C (Preacher) are the clearest non-combat
traces available; this pass verified their two strongest claimed-live links directly:

- **`TEACH` contract (skill lineage)**: brainstorm doc claims LIVE ("recipe learned, no gold
  transferred"). **Not independently re-verified at the code level this pass** — flagged `UNKNOWN`,
  inherited from the brainstorm doc's own citation rather than re-traced.
- **Group leadership election by sociability** (the substrate for a preacher/leader-type trajectory):
  confirmed **LIVE** by Pass 1 directly (`PartyLifecycleService`, `party_lifecycle.py:45`).
- **Crafting recipe registry**: brainstorm doc states "the live crafting registry has **3
  recipes**." Not re-verified this pass — if still accurate, this alone caps how much non-combat
  economic/craft trajectory depth is currently reachable regardless of any other mechanism's
  health, since there is very little to craft toward.

**Overall verdict on non-combat development**: the *decision*-layer substrate for a non-combat
trajectory (goal scoring covers `GoalKind` values beyond combat — Pass 1 confirmed `SocialScorer`
exists, even if its base utility is a stub) is present, but the *institutional-endpoint* substrate
(clans, belief institutions, culture) that a non-combat trajectory would terminate in is real and
LIVE — it is specifically the **growth path connecting an individual's non-combat actions to those
endpoints** that is missing (brainstorm doc's L7, `IP-S17`'s own MISSING finding, and Batch 09's own
lineage-scale version of the same gap). This is not a combat-vs-noncombat asymmetry in raw
mechanism count; it's the same recognition/propagation gap recurring regardless of domain.

---

## Opportunity-generation mechanisms

`docs/world/opportunity_providers_contract.md` (read in full this pass) is the real, live
opportunity-pool pipeline:

```
ResourceOpportunityProvider (resource nodes → gather/harvest opportunities)
ServiceOpportunityProvider  (town/structure affordances → craft/repair/trade/rest opportunities)
PerceptionGate              (7-channel sense-based filter, score < 0.2 gated out)
MotivationPressureResolver  (8 pressure dimensions: survival/comfort/social/achievement/
                              curiosity/safety/greed/purpose)
RequirementsFilter          (inventory/skill/faction/quest-state gating)
→ adventure domain consumes the filtered pool
```

**Central finding for this pass's own central question**: every gate in this real, live pipeline
operates on **current state** (what you have, what you can sense, what faction you belong to, what
quest you're on) — **none of the five stages reads accumulated reputation, notability, or
institutional standing**. This is the mechanical reason the world-reaction loop is thin: it's not
that opportunity generation is broken or missing outright (it's real, tested, and live), it's that
its *inputs* structurally exclude the one thing this pass was asked to trace — whether lived history
changes what becomes available. `RequirementsFilter`'s four gate categories (inventory, skill,
faction, quest-state) are a complete, closed list; reputation/notability is not a fifth category
today, and nothing in the contract doc suggests it was ever meant to be — extending it would be a
deliberate widening, not a bug fix.

`QuestOpportunityGenerator` (`TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION`) and the Guild
service (`TCK-20260425-PH7-M2-GUILD`, "strategic lead generation and world intelligence") were
identified as further opportunity sources by `search_docs` but **not independently re-traced this
pass** — flagged `UNKNOWN` whether either reads any reputation/history signal; worth a targeted
follow-up before any Rule action is taken here, since if either already does, the "opportunity never
responds to who you are" finding above would need narrowing.

---

## Recognition/reputation/world-reaction mechanisms

This is the pass's central question, and the evidence is now converged from three independent
angles:

1. **No entity-level notability/name mechanism exists at all.** `grep -rln "notability\|epithet"
   src/` → zero hits, confirmed by this pass directly. Matches the brainstorm doc's W2.1 proposal
   being just that — a proposal, not yet built, 6 days later still unbuilt.
2. **No per-(institution, individual) standing exists.** `IP-S17` (Batch 10's own scenario,
   Catalog-authoritative): "Confirmed MISSING directly: `FactionSentiment` is faction-to-faction
   only; no per-(organization, specific individual) standing field exists anywhere." This is the
   Catalog's own independent confirmation of the brainstorm doc's L7.
3. **No conversion edge from any advantage into political/social leverage.** `politics-
   authority.md`'s own Domain Rule text: "Repository evidence: MISSING, for every named political
   conversion edge checked... `FactionState.military_strength` is the one real, already-existing
   coercive-capacity proxy, but nothing converts it *from* another advantage... through a declared
   edge — it is seeded and adjusted directly, not derived." `ME-S12` (Batch 08): wealth→protection,
   wealth→political-influence, wealth→supply-chain-control are *each independently* confirmed
   MISSING — not one gap, three parallel gaps in the same conversion family.
4. **What partial reaction machinery does exist is narrow and hero/Campaign-scoped.** The Living
   Legend Fame / Belief Institution / Chronicle Fidelity Drift chain (brainstorm doc's "M5") is real
   and, per the doc's own Scenario R trace, "almost fully built" — but scoped to HERO-role entities
   and Campaign-mode episode boundaries only, per-tick reach never confirmed for ordinary entities.
   This matches Pass 1's own finding about `BeliefInstitution` (§H, "Already covered — MEM-02...").
5. **The one genuinely live, general-purpose reaction mechanism found**: `nemesis_ids` (see
   "Currently supported trajectory loops" above) — but it is *personal*, not *social/institutional*:
   it changes how the specific nemesis-holder treats one other specific entity, never how a third
   party or an institution treats either of them. It does not propagate.

**Conclusion for the central question**: the recognition/reaction half is not universally absent —
it exists narrowly (nemesis-to-one-other-entity, hero-fame-at-episode-boundaries) — but every
*general-purpose, cross-domain* form of it (naming, gossip, institutional standing, power
conversion) that would let an *ordinary* entity's history change what the world offers it is
confirmed MISSING, independently, at every subject scale traced so far across this Catalog and
this pass.

---

## Regression/counterforce mechanisms

| Mechanism | Status | Evidence |
|---|---|---|
| War exhaustion drain | **LIVE** | Brainstorm doc §5, cited as a real counterforce |
| Taxation (wealth extraction) | **LIVE** | `regional_sovereignty_runtime_contract.md` (already cross-checked this session, 2026-09-23/24 work) |
| Scarcity → migration | **LIVE** | Brainstorm doc §5, node depletion → scarcity |
| Succession on leader/founder death | **LIVE** | `ClanLifecycleService`, brainstorm doc |
| Loyalty drift / schism | **LIVE** (idea 56) | Brainstorm doc, "mostly live" for following-growth counterforce |
| Theft / crime as a counterforce to wealth concentration | **MISSING** | Brainstorm doc's F1/L16: "`THEFT` exists only as a legality check and a reputation weight. There is no theft action." Not re-verified by this pass at the code level — inherited citation. |
| Injury/permanent capability loss | **`UNKNOWN`** | Not traced this pass; Pass 1 flagged `HP recovery mechanism` gaps at the Life/Body layer (Batch 05) but this pass did not independently re-check |
| Debt | **`UNKNOWN`** | Not traced this pass |
| Organizational expulsion / exclusion | **`UNKNOWN`** | Not traced this pass; plausible candidate for a future targeted check given clan dissolution is confirmed live |
| Non-deterministic regional loss of sovereignty (the ±50/±100 bug) | **Confirmed live, but a bug, not a designed counterforce** | See §G |

**Overall**: counterforces exist for economic/institutional growth (taxation, war exhaustion,
succession, loyalty drift), but the brainstorm doc's own explicit design rule — "a new growth loop
doesn't ship without its counterforce in the same wave" — has no matching audit for *regression*
paths specifically (injury, debt, exclusion) in this pass's evidence. This is flagged as an open
question for whoever continues this investigation, not resolved here.

---

## Broken or unproven causal edges

| Edge | Status | Evidence |
|---|---|---|
| Wealth → any form of leverage (protection, political influence, supply-chain control) | **Confirmed MISSING, three independent paths, same Catalog scenario (`ME-S12`)** | `ContractKind.PROTECTION` only constructed in `src/certification/scenarios.py` (confirmed by this pass's own grep — zero production call sites), faction vaults never read by faction decisions, no supply-chain mechanism beyond a SimQ-only flag |
| Reputation/office → political leverage | **Confirmed MISSING** | `politics-authority.md`'s own Domain Rule, repository evidence section |
| Individual history → organizational standing toward that individual | **Confirmed MISSING** | `IP-S17` |
| Entity notability/naming | **Confirmed MISSING** (grep, this pass) | No `notability`/`epithet` concept anywhere in `src/` |
| Gossip/knowledge propagation about a specific notable entity | **Confirmed MISSING** | Brainstorm doc L4; `BeliefCycleSystem.process_rumor()` exists but is called only by guild intel about the most-traumatised *region*, never about a specific entity (brainstorm doc, not re-verified by this pass) |
| Opportunity pool gating on reputation/notability | **Confirmed MISSING by design, not by omission** | `opportunity_providers_contract.md`'s own `RequirementsFilter` categories are a closed list (inventory/skill/faction/quest-state) — read in full this pass |
| Regional sovereignty threshold | **CONFLICTING (two disagreeing live authorities)** | Already fully investigated and resolved (user-decided quick-fix scope) two days before this pass — see §G, not re-litigated here |
| `nemesis_ids` propagation beyond the one bonded pair | **Confirmed absent, narrower than it first appears** | This pass's own trace: `nemesis_ids` is read by the nemesis-holder's own targeting/role logic and nothing else — it never reaches a third party's or an institution's decision-making |

---

## PROVEN CURRENTLY / TARGET SEMANTIC NEED / EXPANSION SPACE

**1. Individual lived-history recording**
- PROVEN CURRENTLY: death/lineage (feud, dying wish, heir), displacement (original-home marker),
  grudge→nemesis promotion, and (Pass 1) `TurningPointState`'s five kinds — real, typed, live.
- TARGET SEMANTIC NEED: a generalized, bounded, typed lived-history record covering more kinds of
  formative events than the current ad hoc set (survival, exposure, teaching, betrayal beyond what
  `TurningPointState` already covers).
- EXPANSION SPACE: the brainstorm doc's own `FormativeExperience(kind, tick, region_id,
  counterpart_id, magnitude)` shape is a plausible target — not adopted or endorsed as Rule text
  here, just noted as existing, evidence-grounded design language already in the repo that a future
  Rule-drafting pass could evaluate.

**2. Entity notability / being known**
- PROVEN CURRENTLY: nothing — zero implementation.
- TARGET SEMANTIC NEED: the world needs to be able to refer to a *specific* entity's reputation
  (not just aggregate faction sentiment) for any recognition/reaction loop to close at all — this is
  the load-bearing prerequisite under almost every other gap in this report.
- EXPANSION SPACE: four current personality dimensions and the current turning-point kind set are
  explicitly not the final ontology (per this pass's own design discipline) — a notability
  mechanism, if built, should not be assumed to need a fixed enum of "kinds" (dread/renown/
  reverence/infamy, per the brainstorm doc's own W2.1) as a permanent constraint; that's one
  plausible shape among others.

**3. Power/advantage conversion (wealth, reputation, office → leverage)**
- PROVEN CURRENTLY: nothing converts. Each form of advantage is a dead end for every purpose except
  its own narrow original use (gold buys goods; military_strength is seeded/adjusted directly, never
  derived from anything else).
- TARGET SEMANTIC NEED: `politics-authority.md`'s own Rule already states the *shape* this should
  take precisely — "a specific, declared edge — never computed from one universal Political Power
  score." This is already-covered Rule content; the gap is purely realization.
- EXPANSION SPACE: the brainstorm doc's W4.1 sketch (wealth → `PROTECTION` contracts → patronage →
  loyalty push) is one coarse, already-designed candidate for the *first* such edge, explicitly
  scoped against "a general power-conversion framework or ten power axes" (rejected by the doc's own
  §8.1, consistent with the Catalog's own admission discipline against inventing universal
  frameworks).

**4. Organizational recognition of a specific individual**
- PROVEN CURRENTLY: nothing. `FactionSentiment` is faction-to-faction only.
- TARGET SEMANTIC NEED: `IP-S17`'s own scenario already states it precisely — "an organization
  records this history; the organization changes access, hostility, role, or opportunity toward this
  individual specifically."
- EXPANSION SPACE: not evaluated this pass — a real design question (per-org standing field vs. a
  derived read from lived-history + notability, once notability exists) rather than an
  implementation detail.

---

## Life-trajectory stress tests

**1. Combat/adventure — novice → skilled fighter → renowned specialist → elite opportunity/leadership/setback**

`novice fighter → repeated combat → capability growth (level/skill) → survives notable fights
(TurningPointState) → nemesis grudges form against specific rivals → [FIRST WEAK EDGE: no
notability/name forms, so no one outside the fighter's own personal grudge network ever learns of
their skill] → opportunity pool never changes (gated only on inventory/skill/faction/quest-state,
never reputation) → the fighter's growing skill produces zero new opportunities, only zero-sum
personal rivalries.`

First weak edge: **capability growth → institutional/world recognition** (the notability gap,
confirmed missing).

**2. Economic/professional — worker/apprentice → skilled professional → network/resources →
merchant/master → institutional or political influence**

`worker → gold accumulates (LIVE, thin) → [FIRST WEAK EDGE: nothing to convert gold into except
goods] → even with substantial wealth, no PROTECTION contract is ever offered in production (zero
call sites outside certification scenarios), no political influence accrues (faction vaults never
read by decisions), no supply-chain control exists beyond a SimQ scoring flag → the trajectory
terminates at "has more gold than average," never reaching institutional or political influence.`

First weak edge: **wealth → any leverage at all** (the ME-S12 gap — the earliest-breaking of any
trajectory family traced in this report, matching the brainstorm doc's own verdict: "this one's
chain breaks earliest").

**3. Social/organizational (non-combat) — ordinary member → trusted actor → office/authority/
leadership**

`member → sociability drives group participation (LIVE, Pass 1) → group leadership election by
sociability (LIVE) → leader dies → succession fires (LIVE, ClanLifecycleService) → [FIRST WEAK EDGE:
the *path into* leadership eligibility is sociability-only, never a function of the member's own
lived history, demonstrated trust, or recorded deeds] → once in a leadership role, no mechanism
converts that office into resource access or political leverage beyond the organization's own
ordinary resource pool (politics-authority.md's own MISSING finding for office→resource-access).`

First weak edge: **lived history/trust → eligibility for standing/leadership**, and secondarily
**office → any leverage beyond ordinary membership** (both independently Catalog-confirmed MISSING).

All three trajectories break at essentially the same structural point — the conversion from
*individual accumulated state* (skill, wealth, trust) into *world-recognized standing* — not at
three unrelated points. This is the single most load-bearing conclusion of this pass.

---

## World Rule assessment

- **Already covered adequately**: power-conversion edges must be specific and declared, never a
  universal score (`politics-authority.md`, direct reuse of PROG-07/EXCH-01); organizational
  knowledge/access changing based on recorded history is the *target* shape `IP-S17` already
  describes — the Rule content covering this exists; realization does not.
- **Covered but realization incomplete**: every finding in §"Recognition/reputation/world-reaction
  mechanisms" above falls here — `SUPPORTED`-in-principle Rule content (via PROG-07/EXCH-01/
  organizational-knowledge Inherited entries), `MISSING` in the repository.
- **Semantically ambiguous**: whether entity notability/naming is itself a genuine gap in the
  Catalog's own Rule coverage, or whether it's purely an *implementation prerequisite* for
  already-covered Rules (recognition, reputation-as-leverage) to become realizable at all — not
  resolved this pass, flagged for whoever integrates this report.
- **Genuine World Rule gap candidate**: none newly identified this pass beyond what Pass 1 and the
  Final Integration Batch already flagged. Every gap found here is a realization gap under Rule
  content that already exists (PROG-07, EXCH-01, IP-S17's organizational-access framing,
  politics-authority.md's power-conversion Rule) — consistent with Pass 1's own conclusion that
  nothing found so far rises to "new Rule required."
- **Derived/narrative only**: the brainstorm doc's own rejected/deferred items (§8.1) — a universal
  ten-forms-of-power framework, deliberate-apocalypse-as-design-goal, a RimWorld-style storyteller —
  remain correctly out of scope, consistent with both this Catalog's admission discipline and the
  brainstorm doc's own explicit reasoning.

---

## G. Note: the regional-sovereignty threshold finding, cross-referenced not re-litigated

This session separately investigated and fully resolved (with the user, two days before this pass)
`TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT`: two independent, live code paths
(`FactionInfluenceService` at ±50, `WorldDynamicsSystem` at ±100) can each flip regional ownership on
the same field, with only the ±50 path able to liberate. The user-approved quick-fix scope (lock to
±100 per the Mechanics Bible's own precedence, delete the competing block, widen "Contested" to fill
the resulting gap) is already recorded and handed off — not repeated here. It is cited in this
report only because it directly corrects the brainstorm doc's "conquest is unreachable in practice"
claim (Scenario E, S): conquest is *reachable*, just currently non-deterministic, which is a more
specific and more actionable finding than the brainstorm doc had six days ago.

---

## Recommendations (individually bucketed, Option C — no global integration decision made)

1. **Entity notability/naming (the load-bearing prerequisite under nearly every other finding in
   this report) — further investigation only, not yet a Catalog action of any kind.** This pass
   couldn't determine whether it's a genuine new-Rule candidate or purely an implementation
   prerequisite for already-covered Rules. Recommend this be the next thing scoped, specifically
   because so much else in this report depends on it.
2. **Wealth/reputation/office → leverage conversion edges (ME-S12, politics-authority.md) — no new
   Rule; realization gap under already-covered Rules.** Recommend routing to the Semantic Control
   Plane's M3 triage once M4's own Combat-slice mapping work has landed (same sequencing Pass 1
   recommended for `SocialScorer`), since the Rule content (PROG-07/EXCH-01) already exists and is
   already correctly classified `MISSING` in the Catalog's own review exports.
3. **Organizational recognition of a specific individual (`IP-S17`) — no new Rule; realization gap,
   same bucket as #2.** `IP-S17`'s own scenario already states the target shape precisely; nothing
   here requires new Rule drafting.
4. **`nemesis_ids`'s narrow propagation (personal-only, never reaching a third party or institution)
   — no Catalog action; a scoping note only.** Worth flagging to whoever eventually works on
   notability/recognition, since `nemesis_ids` is the one real, live precedent for "history changes
   how the world treats this entity" and could plausibly inform that design, but this pass makes no
   recommendation about whether it should.
5. **The `check_nemesis_promotion()` dead code (`memory.py:38`, uncalled, duplicate of the live
   `relationships.py` logic) — no Catalog action; a code-hygiene note only**, outside this
   investigation's remit entirely.
6. **Counterforce/regression coverage gap (injury, debt, exclusion left `UNKNOWN` this pass) —
   further investigation only.** Not enough evidence gathered this pass to classify one way or the
   other.
7. **The brainstorm doc itself (`docs/brainstorm/2026-09-19-core-rpg-lived-history-growth-
   brainstorm.md`) — recommend treating it as load-bearing prior art for whichever integration path
   is chosen**, not a document to re-derive from scratch. Its own §9 "Open decisions" (personality
   model consolidation, notability scalar-vs-kind-tag shape, atlas numbering, sequencing) are
   real, still-open design questions independent of this report's own findings — worth carrying
   forward together rather than as two separate backlogs.

No finding in this pass rose to "new World Rule required." Every genuine gap found is a realization
question under Rule content that already exists somewhere in the frozen Catalog — consistent with
Pass 1's own conclusion, now confirmed at the life-trajectory/institutional layer as well as the
decision layer.
