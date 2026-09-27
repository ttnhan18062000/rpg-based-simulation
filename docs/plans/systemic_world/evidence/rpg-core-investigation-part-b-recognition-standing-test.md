---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated evidence snapshot supporting `docs/plans/systemic_world/roadmap.md`, copied from the local working file `rpg-core-investigation-part-b-recognition-standing-test.md` on 2026-09-27. Where the roadmap has since corrected a claim, the roadmap is authoritative.

# Part B — Stress-Test of the Recognition/Standing Synthesis

**Repo revision:** `f15587b4579d4c835189e7b3d9c43420569f110d` (2026-09-24, `semantic-control-plane-epic-tickets` branch, worktree `design-review-rpg-suggestion`).

**Verdict up front, since it overturns the synthesis's central framing:** the synthesis's claim —
"a directed `(observer, subject) → standing` record is the one shared missing primitive" — is
**wrong in a specific, well-evidenced way for the individual-observer case, and correct for the
institutional case.** A directed, per-target, authoritatively-applied relational record **already
exists** (`SocialComponent`'s `trust_history`/`bonds`/`familiarity_history`/`grudge_history`/etc.,
`src/core/state.py`, applied via `RelationshipService.process_update`,
`src/systems/social_systems/relationships.py:24-130`), is real, live, and **deliberately separated
from global `public_reputation`** — confirmed by an explicit code comment citing its own logic ID:
`# Logic ID: SOC-193 (Public reputation and private relationship are separate)`
(`relationships.py:126`). The actual bottleneck is not the standing record — it's **edge 3,
propagation**: that directed state can only be written through **direct interaction between the two
specific parties** (`# Logic ID: SOC-196 (Trust/sentiment changes through interaction evidence)`,
`relationships.py:40`), never through secondhand/witnessed information about a third party. For
*institutional* standing, the synthesis's finding stands uncorrected: no primitive exists there at
all, individual or aggregate.

---

## Investigation report

### Test scenario, adapted to real production paths

The literal "shopkeeper witnesses a deed" scenario has **no live production path** — traced and
confirmed absent (see edge 3 below). The closest real, live, code-traced scenario, adapted to what
actually exists:

> A hunter directly transacts with Shopkeeper A (a real interaction, producing a real `bond`/
> `trust_history` entry). Shopkeeper B has never interacted with the hunter at all. Both later
> evaluate a contract offer from the hunter via `ContractAppraisalService`/`SocialAppraisalSystem`.

This is the scenario this pass could actually trace end-to-end with evidence. The
witnesses-a-deed-secondhand variant is traced as a **code path with each link marked unproven**,
per the source instruction's own "do not fabricate a runtime result" rule — see edge 3.

### Edge-by-edge trace

**1. Objective event/history — PROVEN CURRENT.** `TurningPointState` (Pass 1's own baseline,
reused unchanged) plus direct-interaction events processed via `SocialUpdate` →
`RelationshipService.process_update()`. Evidence level: runtime-firing, confirmed by this pass's own
read of the authoritative apply path (`relationships.py:24-130`).

**2. Recordable evidence — PROVEN CURRENT, narrow.** A direct interaction between two parties
produces real, typed evidence on **both parties' own state** (each entity's `SocialComponent`
records its own view of the other via `bonds[target_id]`, `trust_history[target_id]`, etc.).
Evidence for a *third party who did not participate* — no recordable-evidence mechanism found this
pass beyond `BeliefCycleSystem.process_rumor()` (see edge 3). Evidence level: symbol + reachability
confirmed for direct-interaction case; `UNKNOWN`/likely-absent for third-party evidence.

**3. Propagation — THE CONFIRMED FIRST FAILED EDGE, more precise than either prior pass or the
synthesis stated.**

- `ReputationUpdateService.process_witnessed_event()` — **re-verified, narrower than the synthesis's
  own citation implied.** Confirmed called from exactly one site, `src/engine/quests.py:224-231`,
  gated by `project.quest_kind == QuestKind.ESCORT` specifically (not "any quest event" as the
  synthesis's summary phrased it) — only escort-quest completion triggers it, unconditionally, no
  observer/perception parameter, writing to the **escorted entity's own** `PublicReputationProfile`
  (a global, subject-owned label map). This is not propagation to anyone; it's a self-attribute
  update triggered by one specific event kind. Evidence level: runtime-firing confirmed by direct
  code read of the call site and its guard condition.
- `BeliefCycleSystem.process_rumor()` (`src/systems/strategic_systems/belief.py:127-158`) —
  **genuinely mischaracterized by Pass 2 as inherently "region-trauma-scoped."** The function's own
  signature is fully generic: `rumor_subject: str, rumor_detail: str, source_entity_id: int` — it
  can carry a belief about *any* subject, entity or region alike, and it writes into
  `entity.strategic.beliefs`, a genuinely per-entity (per-observer) dict. **What is actually
  region-scoped is its one production caller**, not the mechanism: `GuildIntelSystem.update()`
  (`src/systems/social_systems/guilds.py:31-52`) hardcodes `rumor_subject = target.id` where
  `target` is always the highest-trauma **region**, never an entity. Confirmed by grep: this is the
  *only* call site of `process_rumor()` in the codebase. Correction recorded: Pass 2's finding is
  accurate for **current production behavior** but overstated as a property of the mechanism itself
  — this is a `TARGET SEMANTIC NEED` already representable by `EXPANSION SPACE` this thin (a new
  producer feeding an existing, unmodified function an entity subject instead of a region subject),
  not a new mechanism to design.
- `SocialComponent`'s own per-target dicts (`trust_history`, `bonds`, `familiarity_history`,
  `grudge_history`, `fear_history`, `debt_history`, `salience_history`) — confirmed **directed,
  authoritative, and real** — but confirmed, via the SOC-196 logic-ID comment and this pass's own
  read of every write path into `RelationshipService.process_update()`, to update **only through
  direct interaction evidence between the two specific parties.** No write path was found from a
  witnessed-but-not-personally-experienced event into any of these fields. `InformationAccumulationService.record_quest_reported_back()` (`src/domains/information/accumulation.py:29-34`,
  gated `ENABLE_INFORMATION_HUB_ACCUMULATION`, confirmed `FeatureMode.OFF` in
  `feature_flags.py:198`) was checked as a possible counterexample and ruled out — it increments a
  generic `knowledge_accumulated` freshness counter on a quest-giver's `InformationProviderState`,
  carrying no entity-specific reputation content at all, and is feature-flagged off regardless.

**Conclusion for edge 3, stated precisely:** the propagation gap is not "no propagation machinery
exists." It's "propagation into the *already-correct, already-directed* relational state
(`SocialComponent`) exists only for direct participants; propagation from a witnessed-but-uninvolved
observer's perspective, into that same already-correct state shape, has no producer at all."

**4. Observer/institution knowledge or belief — re-confirms Pass 1/Pass 2/synthesis baseline,
unchanged.** `KnowledgeModelService` (`src/cognition/knowledge_model.py`) remains per-entity and
opacity-respecting; this pass found no additional entity-reputation content flowing through it
beyond what prior passes already confirmed absent. `FactionSentiment` (`src/core/state.py:720`)
re-confirmed faction-to-faction only — `target_faction_id`, `familiarity`, `sentiment`, no
individual-entity field of any kind. No correction to this edge.

**5. Interpretation and standing — MAJOR CORRECTION TO THE SYNTHESIS.** The synthesis asked "is a
durable observer-relative record causally required, or can the decision consume belief and local
policy directly?" — and the evidence answers: **the durable observer-relative record already
exists and is already consumed**, for the individual-observer case. `SocialAppraisalSystem`'s
contract-trust computation (`src/systems/social_systems/appraisal.py:38-54`) reads, in explicit
priority order: (a) `entity.social.bonds.get(source_id)` — a real, private, directed per-pair
sentiment record — used directly as `trust_score` if present; (b) only if no bond exists, falls back
to `entity.social.trust_history.get(source_id, 0.5)` — still a private, directed, per-(observer,
source) value — blended with global `public_reputation` as a secondary "guilt-by-association" bias
for **strangers specifically**, per the code's own comment ("Idea 54/M5: guilt-by-association — a
stranger's clan_reputation..."). Global `public_reputation` is the fallback of a fallback, not the
primary signal, for this consumer. Evidence level: runtime-firing confirmed by direct code read of
`appraisal.py:38-54`. **Institutional standing is a genuinely different case** — `IP-S17`
(re-confirmed, not re-litigated) still finds no per-(organization, individual) field of any kind;
this half of the synthesis's finding is correct and unchanged.

**6. Reaction — differentiated finding, not the single omniscient-read pattern the synthesis
implied for every consumer.** `shop.py`'s discount (`src/engine/shop.py:84`,
`apply_reputation_discount(legal_price*quantity, entity.social.public_reputation)`) reads the
**buyer's own** global `public_reputation` — confirmed this is not even the right test case for
"does shopkeeper A treat the hunter differently from shopkeeper B," since it's the customer's own
reputation affecting the price *they* get, with no shopkeeper-identity input at all; the synthesis's
own prior citation of this as the go-to "wrong-shape" example was accurate for what it actually
tests, but it is the *wrong scenario* to test the observer-relative claim against. `appraisal.py`'s
contract trust (edge 5 above) is the correct, better-evidenced consumer, and it already
differentiates by observer wherever a bond/trust_history entry exists.

**7. Future opportunity and trajectory — re-confirms Pass 2, unchanged.**
`opportunity_providers_contract.md`'s `RequirementsFilter` remains a closed four-category list
(inventory/skill/faction/quest-state); not re-traced further this pass, no new evidence found either
way.

### Two contrasting cases, evaluated against the proposed standing representation

- **One-off witness reaction (Shopkeeper A directly transacted with the hunter; Shopkeeper B did
  not):** **already producible today**, with real, differentiated A-vs-B treatment, entirely through
  existing `bonds`/`trust_history` + `appraisal.py` — no new primitive required. The scenario as
  originally phrased ("A *witnesses or reliably learns*, B does not") is **not yet reachable**,
  because "reliably learns" (secondhand, non-participant) has no write path into this same,
  already-correct state shape (edge 3).
- **Durable institutional judgment (a guild forms its own view of the hunter):** **confirmed
  unreachable in any form** — `IP-S17`'s MISSING finding stands. No per-institution, per-individual
  record exists to be durable in the first place.

### Recheck: are the five Pass-2 gaps downstream of one shared primitive?

| Gap | Classification | Reason |
|---|---|---|
| Entity notability/naming | `MAY CONSUME STANDING` | Would be a derived aggregate view over the *individual*-level directed records once propagated into (edge 3) — not blocked on a new standing primitive, since one already exists at the individual scale. |
| Gossip/knowledge propagation | **Not "downstream of standing" — this IS the actual confirmed bottleneck (edge 3 itself)**, not a separate consumer of a missing standing primitive. Reclassifying the synthesis's own framing here specifically. |
| Institutional treatment (`IP-S17`) | `REQUIRES STANDING` | Genuinely needs the institution-scoped directed primitive, which does not exist at any level (unlike the individual case). |
| Reputation-sensitive opportunities | `MAY CONSUME STANDING` | A wiring question (add a 5th `RequirementsFilter` category reading existing or aggregated standing) — independent of whether new standing design is needed. |
| Wealth/reputation/office → leverage (`ME-S12`, `politics-authority.md`) | **Split — the synthesis over-folded this.** `politics-authority.md`'s own Rule names three separate declared edges: "wealth → coercive capacity" and "office → resource access" name inputs (`wealth`, `office`) that are `INDEPENDENT CAUSAL EDGE`s, unrelated to standing at all; only "reputation → leverage" specifically is `REQUIRES STANDING`-adjacent (`MAY CONSUME STANDING`, since even that could consume the *global* scalar rather than directed standing, depending on how the edge is eventually designed). The synthesis's framing of this whole gap as "downstream of standing" overreached for two of its three named edges. |

---

## Architecture decision table — Recognition question

| Option | Supporting evidence | Counterexamples / risk | `UNKNOWN` | Confidence |
|---|---|---|---|---|
| **A. No new standing primitive — wire propagation into existing `SocialComponent` directed state** (PROPOSED, this pass's own lean) | `bonds`/`trust_history`/etc. already real, authoritative, directed, deliberately separated from global reputation (SOC-193); already consumed correctly by `appraisal.py` | Institutional standing still has nothing to wire into — this option alone doesn't cover `IP-S17` | Whether extending direct-interaction-only write semantics to witnessed/secondhand events is architecturally sound without violating SOC-196's own "interaction evidence" invariant, or needs a distinct, lower-confidence "secondhand belief" tier | Medium-high for the individual case specifically |
| **B. New institution-scoped standing primitive (synthesis's original proposal, narrowed to institutions only)** (PROPOSED) | `IP-S17` confirms no primitive exists at any level for institutions; `FactionSentiment`'s directed shape is a plausible template to specialize downward from faction-to-faction to institution-to-individual | Risk of re-deriving `FactionSentiment`'s own shape rather than extending it | Whether an institution-to-individual record should be its own type or a specialization of `FactionSentiment` | Medium — genuine design work needed, not yet a repo-evidenced answer |
| **C. Global `(observer, subject) → standing` primitive for BOTH individual and institutional cases, as originally proposed** | None found this pass — evidence points toward two different realization states, not one uniform gap | Directly contradicted by edge 5's finding for the individual case (a working, differentiated primitive already exists there) | — | **Low — this pass's evidence argues against it as stated** |
| **D. No architectural change; treat all five Pass-2 gaps as independent** | None — `IP-S17`/`ME-S12`'s own Rule text explicitly describes a shared, general conversion-edge/recognition shape | Ignores real evidence of shared structure (`bonds`/`trust_history` genuinely serving both notability and reputation-sensitive-opportunity consumers once wired) | — | Low |

**Recommendation, `PROPOSED` not `DECIDED`:** Option A for the individual-observer case (extend
propagation into existing state — an `INTERPOSE`/`WIRE`-shaped change, not an `INTRODUCE`), Option B
for the institutional case (a genuinely new, smaller-scoped primitive). This is a **narrower, cheaper
finding than the synthesis's own proposal** — most of what looked like "design a new authoritative
state shape" is actually "wire an existing, already-correct, already-tested state shape to a new
information source." Confidence: medium-high for A, medium for B, both pending the owner's own
review — not routed through Option C's Catalog-integration buckets by this pass, since neither
option rises to a new World Rule candidate (both are realization/wiring questions under Rule content
`politics-authority.md`/`SOC-01`/`AGENCY-02` already cover).

**Calibrated final verdict:** `public_reputation` is proven to be exactly what the synthesis said —
a global, subject-owned, omniscient-read field, confirmed by direct code trace, no correction needed
there. `KnowledgeModelService` is proven to be correctly architected but unused for this purpose,
also unchanged from the synthesis. What the synthesis got wrong: **directed, observer-relative
standing is not "missing" — it already exists, is authoritative, and is already correctly consumed,
for the individual-to-individual case specifically.** The real, confirmed, narrowest missing edge is
propagation of witnessed/secondhand information into that already-correct state — a smaller,
cheaper, more precisely locatable gap than "design a new architectural primitive." No Catalog
clarification is needed beyond what Pass 2 already flagged (the composition-not-explicit-Rule
question) — this pass found no new semantic ambiguity, only a realization-detail correction to the
prior synthesis.
