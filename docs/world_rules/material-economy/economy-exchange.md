---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-10-09"
---

# World Rule Family: Economy / Exchange

**Purpose/scope.** What economic value represents, under what conditions a price becomes
meaningful, what makes an exchange legitimate and causally complete, and what wealth actually
means in world terms. Does not require one universal objective value, does not build a
universal transaction engine, and avoids one universal `Power`/`Wealth` interpretation.
Entity-centred: economic systems matter through their effect on what a specific entity can
afford, acquire, reach, and become.

**Status.** Batch 08 (Objects/Ownership/Resources/Economy), first draft. Candidates below
originated as external-reviewer hypotheses (`tmp/world-rule-batch-8-ext-ai.md`); each carries
this session's disposition and repository evidence. Structured per the normalized five-category
methodology.

---

## Domain Rules

## EXCH-01 — Value, price, cost, and wealth are four distinct facts; price may be influenced by several factors without any single universal objective value

> Value, price, cost, and wealth are four separable facts, never automatically identical: an
> object's value to a specific subject need not equal its market price; a price need not equal
> the cost of producing it; wealth is an aggregate holding, not a price or a value. A world may
> let price be influenced by any combination of scarcity, local demand, utility, risk,
> transport/access, information, relationships, or institutions — no single universal,
> objective value is required to underlie all of them.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule distinguishes value/
price/cost/wealth as four separate facts, or states that price may legitimately derive from a
plural, non-universal set of influences — Batch 03's COST-01 addresses cost specifically
("broader than currency"), not this broader plurality including value/price/wealth.

**Repository evidence: SUPPORTED for cost/price as separate, real mechanisms; PARTIAL for
value; SUPPORTED for wealth as a distinct aggregate.** `calculate_price()`
(`src/systems/economy_systems/market.py`) computes a real buy price from `base_val *
region_mod * building_mod * type_bias` — several real, independent multiplicative influences,
not one universal value. Sell price is a separately-computed, largely static `50%` of base
value plus a regional-trauma surcharge (`docs/mechanics/03_economic_laws.md` §4) — confirming
buy and sell price are not simply inverses of one shared "value," a real asymmetry consistent
with this Rule's own plurality claim. `entity.inventory.gold` (wealth, an aggregate holding) is
tracked entirely separately from any specific item's own price or value. **"Value" to a
specific subject** (as opposed to market price) was not found to have its own dedicated
mechanism distinct from price — recorded as PARTIAL: the Rule's own distinction between price
and subjective value is architecturally available (nothing forces them to be equal), but this
repository does not yet implement a separate subject-relative value computation that could
diverge from price in practice.

**Scenarios:** [ME-S09](../scenarios/material-economy-batch-08.md#me-s09) (price without
objective scarcity), [ME-S10](../scenarios/material-economy-batch-08.md#me-s10) (wealth
converts to capability), [ME-S12](../scenarios/material-economy-batch-08.md#me-s12) (wealth
does not automatically mean power).

---

## EXCH-02 — A person earns money from someone who pays it: by selling goods, working for a wage, or a task's reward

> A person who has no money may earn it in several ordinary ways: by selling goods it gathered,
> hunted, made or looted to a buyer; by working for a wage at a place that employs people (a
> shop, an inn, a smithy); or by the reward of a task or quest someone offers. Every coin
> earned comes out of the payer's own purse or treasury, which must hold it. Money never
> appears because someone needs it.

**Disposition: ACCEPT — decided by the owner directly, 2026-10-08** (row 34 of
`docs/plans/systemic_world/owner_decision_memo.md`). Applies decision 31 (common-sense ways, each
with a real cost) to money. Passes the admission test: EXCH-01 separates value, price, cost and
wealth, but no Rule said how a person comes to hold money at all.
- **People only, by its nature (decision 42):** money, wages and rewards belong to kinds that
  trade. Animals meet their needs by their own kinds' ways (SURV-06), not by earning.
- **Who is a person here (decided by the owner directly, 2026-10-09; row 43 of the memo):** a
  species declares, as an explicit authored trait, whether its kind keeps coin and trades. This
  is not inferred from another flag: `intelligence_tier` measures wits, not a trading culture.
  Whether a given place serves or hires a given subject is a separate question decided by their
  relationship. A goblin may hold coin and trade, but a town does not sell a meal to, or hire, a
  raider hostile to it.
  - **Why not the tier flag** (Lane B's read, relayed 2026-10-09): `intelligence_tier` "high"
    covers human, goblin, orc, elf, dwarf, lizardfolk, dragonkin and spirit. A spirit is "high"
    but uses no tools, and a troll is "low" but carries the humanoid hunger profile.
  - **Alternatives not taken:** the `intelligence_tier` flag; humans only for now.
- **The ways are plural:** no single one is required. Being paid by fellow townsfolk for small
  jobs (social contracts) is a further way, left for later.
- **Conservation:** a sale moves coins from the buyer to the seller and goods the other way. A
  wage moves coins from the employer's purse to the worker for time worked. A reward moves coins
  from whoever offers it. A purse that is empty cannot pay.
- **Engineering and content, not this Rule:** sale prices (EXCH-01), wage amounts and working
  hours, which places employ how many people, and how an employer's purse refills (its own
  sales).
- **Alternatives not taken:** a starting purse in place of earning (it stands in for the way and
  runs out); money that appears when someone needs it (engine charity).

- **Amendment, who holds the first coin (decided by the owner directly, 2026-10-09; row 37 of
  the memo):** coin exists from world creation, in the hands that would plausibly hold it, in
  three ways at once. Shops and inns start with a till and stock (an inn has food to sell).
  Merchants and shopkeepers start with trade capital. A faction's treasury pays wages for town
  work. How much each holds follows the place (a shop's size, a faction's wealth), never an
  acceptance target. Starting coin is declared world content, so its provenance is world
  creation, not engine charity, and from then on every coin moves only between purses.
  - **Why:** Lane B's read (seed 42, three measured worlds) found that no purse held coin at
    all. Every building had 0 gold and 0 stock, and every person had 0 gold, merchants included.
    The only coin was 1000 per faction treasury (`global_resources`), held by no one. SHOP_SELL
    rejects on an empty purse (`LIQUIDITY_EXHAUSTED`) and SHOP_BUY on empty stock
    (`OUT_OF_STOCK`), so neither selling nor wages could ever start.
  - **Alternatives not taken:** only shops and merchants (no wages until a shop earns); only the
    treasury (selling waits until a shop has earned coin).
- **Amendment, a reward needs a payer (decided by the owner directly, 2026-10-09; row 38 of the
  memo):** a kill bounty is paid from the treasury of the faction that posted it, a quest reward
  from the quest giver's purse, and loot is whatever the dead body carried. A reward that no
  purse pays is minted coin and breaks this Rule. It is its own ticket, after first coin lands.
  Until then, the minted kill and quest rewards are recorded as a known exception (an
  intentional divergence, class Bounded, naming that ticket).
  - **Today:** `COMBAT`/`KILL_REWARD` and `QUEST_REWARD` grant gold with no payer debited. All
    coin that reached town workers in Lane B's runs was minted kill reward (5 to 35 gold).
  - **Alternative not taken:** accept a bounty paid by "the world" as a lasting exception.
  - **Scenario:** [ME-S23](../scenarios/material-economy-batch-08.md#me-s23) (bounty from a
    treasury, quest reward from a giver, loot only what the body carried; unfunded controls).

- **Amendment, tax is a share of income or trade (decided by the owner directly, 2026-10-09; row
  51 of the memo):** a treasury is paid a small share when coin changes hands in its place, from
  a sale or a wage. Someone who earns nothing pays nothing, and a busy trader pays more. A
  periodic levy on everyone present is not a tax this world uses. The share moves from the
  payer's purse to the treasury, never minted. Its size is content, light and plausible
  (decision 33).
  - **Why:** Lane B's four-arm measurement (5000 ticks, three worlds, relayed by rpg-planner):
    the regional tax took 2 gold every 20 ticks from anyone present, about 144 gold a game-day.
    Subjects holding under 10 gold paid 50 to 150 gold per run per world. In the city world's
    wage arm, the poor paid about what they earned (146), and most sales were taxed away before
    a meal.
  - **Alternatives not taken:** a levy with an exemption below a threshold and a lower rate; a
    lower flat rate only; leave as is.
  - **Evidence: CONFLICTING** until the levy is retired (`src/engine/town_resolution.py`).
  - **Scenario:** [ME-S22](../scenarios/material-economy-batch-08.md#me-s22) (a share of a sale
    and of a wage reaches the treasury; an idler pays nothing).
- **Amendment, how the treasury's coin moves (decided by the owner directly, 2026-10-09; row 58
  of the memo; asked by rpg-planner on Lane B's treasury design):**
  - **The tax share is a tenth, rounded down on each transaction.** It is declared once in the
    world's economy rules, and outsiders pay the same for now. Rounding down is "someone who
    earns nothing pays nothing": a 6-gold wage pays nothing and a 20-gold sale pays 2. Treasury
    income comes mostly from larger trades. That is reported, never tuned.
  - **Upkeep pays for town work.** The owning treasury pays each building's maintenance into
    that building's own purse, and the building pays wages from it. Town work (decision 37) is
    work at a building the treasury owns, at the same pay as an inn shift. Coin goes round:
    treasury, building, worker, tax, treasury. The coin buildings created from nothing each tax
    tick is removed (decision 38). A building whose upkeep goes unpaid is disabled. No town hall
    is added, and paid guards stay unplanned (roadmap §12.4).
  - **A repair is paid once, to the smith.** Away from a smith, repair is offered only to a
    subject carrying a repair kit, which is used up and moves no coin. Repair that charged twice,
    or paid nobody, goes.
  - **A reward the payer cannot pay is owed.** It becomes a recorded debt (who is owed, which
    treasury owes it, how much, since when), paid oldest first when the treasury can, and visible
    until then.
  - **Applied from decisions already made (rpg-designer, same day):**
    - kill gold is no longer minted: the looter takes what the body carried, and a bounty is paid
      only where a faction posted one, from its treasury, while experience stays;
    - an heir takes the dead's coin and goods, moved and never copied, and the body keeps only
      what no heir claims;
    - a faction vault starts with its members' declared starting gold, each coin counted once.
  - **Disclosed:** only one guild holds regions in all 20 worlds, so other treasuries receive no
    tax. That is world content for later, not a reason to change the share. Most kills stop
    paying coin; a hunter earns by selling meat or hides (decisions 31 and 34).
  - **Alternatives not taken:** rounding half up, or a daily tax on takings; maintenance as a
    sink with a separate treasury wage, or a new town hall; no repair away from a smith; a reward
    lost, or a quest refused unless its reward is reserved at posting.
  - **Amended: a building pays its own upkeep first (decided by the owner directly, 2026-10-11;
    row 61 of the memo).** Under the first text, every town shut by about tick 750. The treasury
    paid all upkeep, but its only income was the share of sales and wages, which barely run
    while the free meal stands. Meanwhile its buildings held about 2,000 gold idle. A business
    keeps itself up:
    - each building meets its upkeep from its own purse, and the owning treasury tops up only a
      shortfall;
    - a building closes only when neither can pay, and reopens when paid;
    - meeting upkeep sends no coin to nowhere: coin leaves a building only as wages for the work
      that maintains it, and as tax on its own sales (a meal or bed sold is a sale, decision 51).
  - **A quest is paid only by its real giver (owner, row 61):** whoever posted it pays, from its
    own purse or its own faction's treasury, or owes it. Neither the claimant's local holder nor a
    neutral reserve pays for a quest it never offered. A quest with no identifiable giver carries
    no coin reward.
  - **Coin on an unclaimed corpse stays where it fell (owner, row 61):** coin does not rot. It
    lies as a purse to be found. A lord claiming unclaimed goods waits for a law Rule.
  - **Fees and taxes retired (rpg-designer, applying decisions 51 and 58):** a repair fee or
    service fee charged on top of the price, and a wealth-triggered tax (`GoldSinkSystem`, about
    50 coin per 100 ticks destroyed), are retired rather than re-routed.
  - **Measured on the batch** (Lane B, pinned, five seeds, three worlds, relayed by rpg-planner):
    coin drift goes from +6,000 to +8,600 per run on main (minting) to about 0; tax on the poor is
    0; debts end at 0. A building disabled for unpaid upkeep reopens when paid.
  - **Evidence: CONFLICTING** until Lane B's treasury batch lands. Scenarios:
    [ME-S21](../scenarios/material-economy-batch-08.md#me-s21),
    [ME-S22](../scenarios/material-economy-batch-08.md#me-s22),
    [ME-S23](../scenarios/material-economy-batch-08.md#me-s23) and
    [ME-S24](../scenarios/material-economy-batch-08.md#me-s24).

**Repository evidence: MISSING for wages; PARTIAL for selling and rewards.** Lane B's
feasibility read (relayed by rpg-planner, 2026-10-08): every town worker starts with 0 gold, and
over a run 14 workers together take in 5 to 40 gold, against a 5-gold meal. Selling exists as a
price rule (sell at 50 percent of base, `docs/mechanics/03_economic_laws.md` §4), but no worker
is seen selling. Decision 27's earn opening step is a stub, and there is no paid-work concept.
Quest rewards exist for adventurers. Shops, inns and a smithy exist in all three measured worlds,
so earning is the only way to eat present in every one of them. **CONFLICTING for first coin
and for rewards** (decisions 37 and 38): no purse but a faction treasury holds coin at compile,
and kill and quest rewards are minted.

**Scenarios:** [ME-S19](../scenarios/material-economy-batch-08.md#me-s19) (sell gathered
wood or ore, the shop's purse pays, buy a meal; an empty-purse control) and
[ME-S20](../scenarios/material-economy-batch-08.md#me-s20) (an inn shift paid from the inn's
purse, then a meal; an empty-purse control) and
[ME-S21](../scenarios/material-economy-batch-08.md#me-s21) (town work paid from the faction treasury;
an empty-treasury control; decision 37). Kernel specs, owed as tests with Lane B's batch 2.

---

## Inherited / Applied Foundational Rules

### An exchange's legitimacy and completeness depend on whichever preconditions a domain's own rules declare, never a universal transaction requirement

> What makes a specific exchange legitimate and causally complete (authority, knowledge,
> consent, ownership, reach, resources) is declared per exchange type by the domains that
> govern those preconditions — not one universal set every exchange must satisfy identically.

**Disposition: INHERITED — direct reuse of Capability (CAP-01–05), Authority (AUTH-01–06),
Reach (REACH-01–06), and this batch's own PROP-01 (ownership/possession/access distinctness)
and OWN-04 (proposed ≠ committed state, Batch 01). No new claim: an exchange is simply an
ownership transfer with each side's own preconditions checked, and those preconditions'
plurality is already established by the foundational families named above — stating that
again for "exchange" specifically would restate, not refine.**

**Repository evidence: SUPPORTED.** `docs/mechanics/03_economic_laws.md`'s Market Law
requires, for buying, that the building actually hold the item in stock and the entity have
sufficient gold (a resource/capability precondition); for selling, that the building hold
sufficient liquidity (gold) to pay. Both are real, checked preconditions that gate whether the
`ResourceTransferIntent` the exchange constructs is ever accepted by `src/core/
conservation.py`'s resolver — the same commit-only-if-preconditions-hold pattern OWN-04
already requires, and the same resolver whose `source_kind` dispatch PROP-02 (in
`ownership-possession.md`) already found to reject an unhandled case.

**Scenarios:** none newly traced; reuses the Market Law evidence directly.

### Power/wealth conversion edges are specific, never automatic; the existence of one edge does not imply any other

> Wealth converting into any other form of effective power (capability, protection, influence,
> production) requires its own real, declared conversion mechanism — the existence of one such
> edge never implies any other exists.

**Disposition: INHERITED — direct reuse of Batch 07's PROG-07 (power conversion edges are
specific, never automatic), applied here to wealth specifically. No new claim: PROG-07 already
states the general principle this family's own §9 investigation instantiates for wealth.**

**Repository evidence: SUPPORTED for wealth → capability; MISSING for wealth → protection,
wealth → political influence, and wealth → supply-chain control — checked directly against
each named example, not assumed uniform.** Wealth → capability is real: gold buys equipment
(`BUY_UPGRADE` route family, Batch 06 evidence) and equipment is a real, confirmed capability
channel (Batch 07's PROG-01). **Checked directly, per `docs/brainstorm/
2026-09-19-core-rpg-lived-history-growth-brainstorm.md`'s own verified investigation ("Scenario
B: a poor merchant becomes a power"), cross-checked against source**: `ContractKind.
PROTECTION` exists and is appraised, but is constructed only in `src/certification/
scenarios.py` — confirmed never created by real production gameplay code, DORMANT rather than
live (contrasted with `RECRUITMENT`, which has a real employment cost and is live).
Faction gold vaults (`faction_{id}_gold`) accumulate via taxation but individual wealth never
reaches faction-level decisions — wealth → political influence is confirmed MISSING. No
mechanism translates accumulated wealth into control over a supply chain or resource monopoly
beyond a SimQ-only scoring flag (`faction_monopoly`, not a real mechanism) — confirmed MISSING.

**Scenarios:** [ME-S10](../scenarios/material-economy-batch-08.md#me-s10),
[ME-S12](../scenarios/material-economy-batch-08.md#me-s12).

---

## Scope / Deferred Boundaries

### Universal transaction engine

> This family does not build a universal transaction engine at the semantic level — each
> exchange type's own preconditions remain declared per-domain, per the batch instruction's
> own explicit "do not build a universal transaction engine at the semantic level" instruction.

**Disposition: SCOPE BOUNDARY.**

### Equilibrium / stabilizing counterforces for economic feedback loops

> This family does not require economic feedback loops (scarcity ↔ price ↔ behavior,
> wealth ↔ opportunity) to reach equilibrium or to be stabilized by a declared counterforce —
> open instability is an explicitly legitimate outcome, per the batch instruction's own
> explicit "do not require equilibrium. Open instability remains valid" instruction. This is a
> scope statement about what this family does not require designed, not a world-semantic claim
> in its own right — PROG-05's own "must declare a scaling/limiting stance" requirement
> (Batch 07) still applies to any specific repeatable economic source that exists; this
> boundary only says a *stabilizing* answer is never mandatory.

**Disposition: SCOPE BOUNDARY.**

### Later-domain wealth-conversion downstream semantics

> This family confirms which wealth-conversion edges are real and which are missing, but does
> not design the downstream Social/Politics content those edges would feed (how protection
> translates into safety, how political influence is spent) — those remain future domains.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions.** EXCH-01 and the
Inherited power-conversion entry above state what value/price/wealth semantics permit; the
findings below report which of those permitted conversion edges this repository actually
implements. Whether to build the missing edges is an implementation-planning decision this
Rule Catalog identifies but does not make.

- **CONFLICTING — economic decisions read raw registry/world state without a perception gate,
  reconfirming Batch 06's own finding from the market/service side.** See
  `ownership-possession.md`'s own Repository Findings for `ServiceOpportunityProvider`'s own
  evidence — cross-referenced here since it is this family's own decision-making surface
  (shop/service opportunities), not duplicated in full.
- **MISSING — wealth → protection, wealth → political influence, wealth → supply-chain
  control.** See the inherited power-conversion entry above. Of the batch instruction's own six
  named merchant-to-power steps (per the design brainstorm's own verified table), this chain
  breaks earliest of any lived-history trajectory checked across this whole Rule Catalog so
  far — wealth accumulates but has almost nothing real to convert into beyond goods and
  equipment.
- **PARTIAL — "value" to a specific subject has no dedicated mechanism distinct from market
  price.** See EXCH-01 above.

## Cross-domain links recorded here

- EXCH-02 → Life/body/survival (SURV-06 and decision 31: buying food needs money), Resources
  (RES conservation: coins move from a real purse), Institutions (employers)
- EXCH-01 → Resources/Production (`resources-production.md`'s PROD-02, scarcity ≠ price),
  Cost (COST-01, Batch 03)
- Inherited exchange-preconditions entry → Capability, Authority, Reach (Batch 02/03),
  Ownership/Possession (`ownership-possession.md`'s PROP-01)
- Inherited power-conversion entry → Capability/Progression (`capability-progression.md`'s
  PROG-07, Batch 07), History/Provenance (fame/legend tracking, the parallel combat-side
  finding)

## Open questions carried forward

1. Whether this repository should build a real opportunity-seeking mechanism, a real
   protection-market, a real wealth-to-political-influence channel, or a real supply-chain-
   control mechanism is flagged for future batches/tickets (most plausibly Social relations,
   Politics) — not decided here, consistent with this batch's own explicit non-goal against
   designing those downstream semantics.
2. Whether "value" (subject-relative) should gain its own mechanism distinct from market price
   is flagged, not decided here.
