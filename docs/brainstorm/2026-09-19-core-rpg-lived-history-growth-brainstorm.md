---
status: active
layer: mechanics
authority: P2
audience: agent
tags: [progression, social, world, content]
---

# Core RPG: Lived History & Systemic Growth, a Scenario-Driven Proposal

Date: 2026-09-19. Checked against `origin/main` @ `74c11ceb7`.

## What this document is

A brainstorm-stage **program proposal** for the core RPG system: entities, progression, relationships, recognition, institutions, places and factions. It starts from the scenarios in an outside design suggestion (written by an external AI without repo access): an ordinary wolf becoming a regional legend, a poor merchant becoming more dangerous than warriors, a preacher founding a movement, a weapon becoming a relic, a village growing into a capital, a beggar becoming a ruler.

It asks one question: **do we already have enough mechanisms for those stories to happen on their own, and if not, what exactly is missing?** Similar systemic games are used as reference points throughout.

The compass is [`the_unwritten_world.html`](the_unwritten_world.html). Every capability proposed here names the principle it serves. Nothing here is approved. Each capability still needs the normal path: an atlas card, scorecard scores, a spec, and a ticket.

**Structure:**
- §1 guardrails
- §2 the scenario traces (the evidence)
- §3 diagnosis: the missing *link types*
- §4 the proposed program, as capabilities in waves
- §5 counterforces
- §6 the scenarios re-traced with the program in place
- §7 architecture and implementability
- §8 what is not adopted
- §9 open decisions

---

## 1. Guardrails

1. **Observed world, not a player's game.** From the founding pitch: "a living world you observe rather than control." Every scenario is about NPCs acting on each other.
2. **Principle 1 governs.** Every scenario step must come from independent systems colliding. No step may be authored ("spawn legendary wolf"). The test for each capability is: *does it create a new intersection other systems can stumble into?*
3. **Principle 7: coarse and felt, not precise and invisible.** Each capability ships the smallest version an observer would notice.
4. **Principle 8 is part of done.** Each capability names how it surfaces: the Chronicle, a rumor, a name, a readable event.
5. **Principle 3: no reskins.** Capabilities share a *shape*, not a *meaning*. A wolf's significance is dread and territory; a preacher's is belief and followers.
6. **Rarity by construction.** From the suggestion's own §24: *"every entity can become significant" must never mean "should"*. Thresholds, competition and counterforces keep significance rare.
7. **Existing rules apply:**
   - build bottom-up (movement, combat, interaction first);
   - wire before adding;
   - core mechanisms ship unflagged;
   - durable state gets typed fields and an authoritative write path;
   - all randomness is seeded;
   - verify with focused production-like scenarios; SimQ is for balance.

---

## 2. Scenario traces: what exists at each link

Each scenario from the suggestion is traced link by link through today's mechanisms.

**Status legend**

| Status | Meaning |
|---|---|
| **LIVE** | Runs in real play |
| **STARVED** | Live, but rarely or never reached in real runs |
| **OFF** | Built, flag default OFF |
| **DORMANT** | Built, no live caller or consumer |
| **CAMPAIGN** | Live, but only at Campaign episode boundaries (one corpus profile) |
| **DESIGNED** | Carded or proposed, not built |
| **MISSING** | Nothing exists |

### Scenario A: an ordinary wolf becomes "the Ash Fang"

| # | Step | Mechanism today | Status |
|---|---|---|---|
| A1 | Exposed to something rare (a corrupted region or corpse) | Regions carry `hazard_kind`, and entities take drain there. Nothing tracks *what an entity was exposed to*. Corpses exist, but only as decaying objects: no scavenging or consumption. | Exposure LIVE, **memory of exposure MISSING** |
| A2 | Develops an adaptation | Endurance to a hazard is declared per *faction*, never earned per entity. Idea 50 (material-gated evolution branch) is carded. | **MISSING** (idea 50 DESIGNED, M10) |
| A3 | Grows stronger and changes form | Levels come from XP. `EvolutionSystem` changes `kind` at levels 10/25/50 (WOLF→DIRE_WOLF), but nothing reads the new kind. | LIVE but STARVED and hollow |
| A4 | Survives the hunters | Combat plus causal memory (`CausalMemoryEntry` on a *loss*). Surviving is never recorded as an experience. | Combat STARVED, **survival memory MISSING** |
| A5 | Preys on caravans | There are no caravans. `TRADE_ROUTE` is only a faction directive label. | **MISSING** |
| A6 | Establishes territory | `CreatureTerritoryService` (maturity → spawns kin). Lairs exist, but only on authored LAIR Places. | OFF / authored only |
| A7 | Other predators gather | Nest spread (same kind). `GroupSystem` forms groups, not predator gatherings. | OFF |
| A8 | Settlements give it a name | `ChronicleNamer` names *events* (wars, eras), never individual entities. | **MISSING** |
| A9 | Trade routes move | Route scoring penalises dangerous regions (−2.0 via `RegionThreatClassifier`), but by region trauma, not by a specific threat. | Partial (region-level only) |
| A10 | The regional economy changes | Cross-region scarcity propagation is computed, then discarded before reaching the economy. | Built but not wired (P1 ticket open) |
| A11 | Rulers organise an expedition | `COMMISSION_QUEST` only boosts hero quest routing in general. `BOUNTY` quests are generic templates ("Bandit Leader"). `QuestState` has no typed target entity (only free-form `metadata`). | Partial. **A named target is MISSING** |
| A12 | Expeditions fail and stories spread | Rumors are created only by guild intel, about the most traumatised *region*. There is no gossip between entities. Paid information is a contract. | **Entity-to-entity spread MISSING** |
| A13 | A cult worships it | `BeliefInstitution` forms only around *hero* legends (fame counts only quests and hero deaths), per clan, at episode boundaries. | CAMPAIGN, heroes only |

**Verdict:** about 3 of the 13 links are live and reached. The chain breaks at A1/A2 (no individual memory of exposure), A4 (no memory of surviving), A8 (no naming) and A11–A12 (the world cannot refer to a *specific* entity). Of the six scenarios, this is the one closest to the vision's Principle 1 example.

### Scenario B: a poor merchant becomes a power

| # | Step | Mechanism today | Status |
|---|---|---|---|
| B1 | Spots a market opportunity | Buy/sell prices react to global pressure (`calculate_buy_price`, `market.py`). Scarcity is derived per region. NPCs don't reason about price differences. | Pricing LIVE, **opportunity-seeking MISSING** |
| B2 | Accumulates wealth | Entities hold `inventory.gold`. Selling loot for gold is a goal. Merchant NPC modules exist (`trading_company_hub`). | LIVE (thin) |
| B3 | Controls the supply chain | Nothing. | **MISSING** |
| B4 | Pays for armed protection | `ContractKind.PROTECTION` exists and is appraised, but is only created in certification scenarios. `RECRUITMENT` has an employment cost and is live. | PROTECTION DORMANT, RECRUITMENT LIVE |
| B5 | Gains political influence | Faction taxation fills a per-faction vault (`faction_{x}_gold`). Individual wealth never reaches faction decisions. The faction importance signal is scoping-only. | **MISSING** (importance signal DESIGNED) |
| B6 | Monopolises a strategic resource | Only as a SimQ threshold flag (`faction_monopoly`), not a mechanism. | **MISSING** |

**Verdict:** wealth accumulates but has almost nothing to *buy* except goods. Of the six scenarios, this one's chain breaks earliest.

### Scenario C: a local preacher founds a movement

| # | Step | Mechanism today | Status |
|---|---|---|---|
| C1 | Gains followers | Groups have leaders (a sociability election) and membership. There's no "follow a charismatic individual" mechanism. `RECRUITMENT` needs an employer. | Partial |
| C2 | Receives donations | No donation or tithe transfer exists. | **MISSING** |
| C3 | An organisation forms | Clans have a live lifecycle (membership, succession on death, dissolution; `clan_lifecycle.py`). There's no founding *by a living individual's appeal*. | Partial |
| C4 | Belief spreads | `BeliefInstitution` exists, but only derived from a dead-or-questing *hero's* fame, per clan, at episode boundaries. There's no belief about a *living* figure and no conversion. | CAMPAIGN, narrow |
| C5 | Challenges existing authority | Faction sentiment, affiliation mutation (idea 39) and loyalty drift (idea 56) exist. A belief institution never touches politics. | Parts LIVE; the link is **MISSING** |

**Verdict:** the institutional endpoints exist (clans, belief institutions, loyalty drift). What's missing is the *individual → following → institution* growth path. Belief is only ever derived after the fact from Chronicle history.

### Scenario D: an ordinary sword becomes a relic

| # | Step | Mechanism today | Status |
|---|---|---|---|
| D1 | Used in a famous battle | `ItemInstanceService` (idea 30, item history). You deferred it because it has no consumer. | OFF / DORMANT |
| D2 | Associated with a hero | There's no link between an item and its owner's deeds. | **MISSING** |
| D3 | Inherited | Heirlooms transfer to the heir on death (live, with default heir selection). | **LIVE** |
| D4 | Becomes a symbol or relic | Nothing. | **MISSING** |
| D5 | Wars are fought over it | Nothing. | **MISSING** |

**Verdict:** inheritance exists, and history is built but switched off. The item needs a *consumer*: something that reads its history.

### Scenario E: a village becomes a capital

| # | Step | Mechanism today | Status |
|---|---|---|---|
| E1 | Trade success | Taxation fills the faction vault. Nothing ties it to one settlement's trade. | Partial |
| E2 | Population grows | Cohort births and deaths, three reproduction paths (flagged OFF), and the birth nudge. | LIVE / OFF |
| E3 | Cultural influence | Culture drift per region. | CAMPAIGN |
| E4 | Political importance, regional dominance | `EXPAND_TERRITORY` is gated on population pressure (idea 51). Conquest thresholds exist but are unreachable in practice (faction proposal §2.2). | LIVE but STARVED |
| E5 | Settlement tiers (village → town → city) | Settlement capacity landed in a different shape. There are no qualitative tiers. | **MISSING** |
| E6 | Internal instability, fragmentation or empire | Loyalty drift (idea 56) and affiliation mutation exist. Countries can't be founded or split (atlas: "Country Lifecycle" absent). `faction_destroyed` is consumed by culture and chronicle, but no code ever emits it. | Partial. **Founding/splitting MISSING** |

### Scenario F: a beggar becomes a ruler

| # | Step | Mechanism today | Status |
|---|---|---|---|
| F1 | Beggar → thief | `THEFT` exists only as a legality check and a reputation weight. There is no theft action. `SabotageAction` is an orphan (idea 1). | **MISSING** |
| F2 | Thief → gang leader | Group leadership election by sociability. | LIVE |
| F3 | Leader → political fixer → ruler | Clan succession exists. There is no faction leadership, office or title. | **MISSING** |

### Summary

| Scenario | Links | LIVE and reached | Partial / OFF / DORMANT / CAMPAIGN | MISSING |
|---|---|---|---|---|
| A Wolf | 13 | ~3 | 6 | 4–5 |
| B Merchant | 6 | 1 | 2 | 3 |
| C Preacher | 5 | 0 | 4 | 1–2 |
| D Artifact | 5 | 1 | 1 | 3 |
| E City | 6 | 0 | 5 | 1–2 |
| F Beggar | 3 | 1 | 0 | 2 |

**Answer to the question:** **no, we don't yet have enough mechanisms for these stories to happen on their own.** But the gap is **not** a lack of systems. The endpoints the scenarios need already exist: legends, belief institutions, clans, culture, loyalty drift, displacement, `EXPAND_TERRITORY`, heirlooms and taxation. What's missing is a small set of recurring **link types** (§3). Together these would turn many isolated endpoints into connected chains.

### 2.7 Expanded scenario set

The outside suggestion offered six arcs. The fifteen below are written in the same spirit: an ordinary starting point and no authored beat, where each step is one system's output landing in another system's input. Several are taken directly from the vision's own examples. Each is traced the same way, and the last line names the missing link types (§3) that break it.

#### G. The feud that outlived its founders (Principles 2, 4, 6)

A clan warrior is killed by a rival. Their heir inherits the hostility and a dying wish. A marriage between the two clans is tried as a truce, and a betrayal at the union reignites the feud for another generation.

| Link | Mechanism | Status |
|---|---|---|
| Death passes the feud to the heir | Idea 55 `_transfer_inherited_feud` (weakened hostility), inside death dispatch | **LIVE** |
| The deceased leaves a wish naming the antagonist | Idea 58 `_seed_dying_wish` (names a Campaign-mode Nemesis, otherwise a generic remembrance) | LIVE (named only in Campaign mode) |
| The heir pursues it | A betrayal spawns an `AVENGE` directive. Whether the wish drives behaviour is unverified. | Partial |
| Marriage as a truce | `MARRIAGE` contract (live producer). It changes nothing *between the clans*. | **MISSING effect** |
| Betrayal reignites it | The betrayal branch of `resolve_contract_outcome` is a disclosed dead path | DORMANT |
| The feud gets a name | Chronicle names wars and eras, never feuds | **MISSING** |

Reveals **L12**. Death and lineage are the *richest* live area; what's missing is kinship acting between groups.

#### H. The goblin camp that became a spider ruin (the vision's "strongest single idea", Principle 5)

| Link | Mechanism | Status |
|---|---|---|
| A camp is founded beside an old battlefield | `CampState` is constructed only by the world compiler. No camp is ever founded at runtime. | **MISSING** |
| It grows and raids | Camp maturity, raids at maturity 80 | LIVE |
| Heroes clear it | Camp clear → trauma −10 | LIVE (STARVED by combat rarity) |
| The structure stays, abandoned | There is no abandoned/ruin state. `PlaceState.kind` has no runtime update path, and idea 48's place transitions weren't found at Place level (verify). Region biome shifts exist (e.g. FOREST→BURNT_FOREST at trauma 50). | **MISSING** |
| Spiders move in | Nest spread (flag OFF) spawns same-kind offspring and never colonises an empty place | **MISSING** |
| It's remembered as a spider ruin | No place history or place name | **MISSING** |

Reveals **L9** and **L17**. Principle 5's headline example is currently unreachable.

#### I. The refugee who came home (Principles 5, 2)

| Link | Mechanism | Status |
|---|---|---|
| A calamity strikes | Calamity at minimum/forced intervals | LIVE |
| People are displaced | Idea 65 `DisplacementService`: relocates entities and keeps `home_region_id` as the *original* home | **LIVE** |
| They put down roots elsewhere | Bonds form normally. Place attachment is DORMANT (no caller). | Partial |
| They grieve the lost home | Principle 5's "characters remember places too", flagged unaddressed by the alignment audit | **MISSING** |
| The homeland recovers | Biome recovery (`trauma_less` thresholds) | LIVE |
| They return and find it occupied | Idea 59 home/exile route bias (verify reach). No occupancy history. | Partial, needs L9 |

Reveals **L9** (political and personal place memory) and **L1** (`DISPLACED` as a formative experience).

#### J. The master smith and the line of apprentices (Principles 2, 5, 8)

| Link | Mechanism | Status |
|---|---|---|
| A smith crafts | The live crafting registry has **3 recipes**. The richer legacy item catalog with place-tied materials is disconnected (idea 49). | Thin |
| The smith teaches apprentices | `TEACH` contract (live producer; recipe learned, no gold) | **LIVE** |
| A lineage of craft forms | No record of who taught whom | **MISSING** |
| The master's work carries a maker's mark | Item history (idea 30) is OFF | OFF |
| Masterworks become sought after | No item notability | **MISSING** |

Reveals **L11** and depends on idea 49's content.

#### K. The coward's redemption (Principle 2)

| Link | Mechanism | Status |
|---|---|---|
| A young hero keeps fleeing | Bravery-driven engage/flee bias | LIVE |
| The party's grievances pile up; they defect or are pushed out | `grievance_log`, defection (notoriety +2.0, faction→NEUTRAL) | LIVE |
| They carry a reputation | `notoriety_score` | LIVE |
| They make one stand when a bond is at stake | Needs `LOST_BOND` or a threat-to-bond experience moving bravery **up** | **MISSING** (L2) |
| They're renowned | Notability `RENOWN` | **MISSING** (L3) |

Shows W1.2's drift must move **both ways** and be reversible by later events.

#### L. The rivals (Principles 4, 2)

| Link | Mechanism | Status |
|---|---|---|
| Two heroes compete for the same targets | Shared quest/route opportunities | LIVE |
| Harm accumulates | `grudge_history` (no decay) | LIVE |
| The bond becomes RIVAL | Derived from sentiment ≤ −0.8 (since 2026-09-07) | LIVE |
| Nemesis promotion | `check_nemesis_promotion()`, no caller | DORMANT |
| The rivalry steers what they do | `RIVAL` is read only by party-composition scoring | **MISSING** consumer |

Reveals **L5** at a personal scale: targeted response should include personal rivals, not only notable threats.

#### M. The creeping blight (Principles 6, 5)

| Link | Mechanism | Status |
|---|---|---|
| A calamity corrupts a region | `ARCANE_CORRUPTION` `hazard_kind` (authored), calamity intensity | LIVE |
| The corruption spreads to neighbouring regions | Only *scarcity* propagates across regions (single hop, and it's discarded). Hazards never spread. | **MISSING** |
| Creatures adapt or flee | Adaptation (W1.3); fleeing via threat routing | MISSING / LIVE |
| Farmland fails, then famine | Node depletion → scarcity | LIVE |
| People migrate | Migration law | LIVE |

Reveals **L10**. The same missing primitive would carry disease, fire and blight.

#### N. The famine and the bread riot (Principles 6, 4)

| Link | Mechanism | Status |
|---|---|---|
| Harvests collapse | Depletion, scarcity | LIVE |
| Prices climb | Global pressure pricing. Region-aware pricing isn't implemented. | Partial |
| The hungry steal | No theft action (legality check and reputation weight only) | **MISSING** |
| Guards respond | `GUARD` role exists. No enforcement against crime. | **MISSING** |
| Loyalty frays | Loyalty drift (idea 56, Campaign-only reach) | CAMPAIGN |

Reveals **L16**.

#### O. Deserters become a bandit clan, then mercenaries (Principles 4, 1)

| Link | Mechanism | Status |
|---|---|---|
| Soldiers desert | Defection → faction NEUTRAL | LIVE |
| The deserters band together | `GroupSystem` | LIVE |
| They prey on the roads from a hideout | No runtime camp founding. The "Bandit Leader" bounty is an authored template. | **MISSING** (L17) |
| The band becomes a durable named organisation | Clan founding by a group | **MISSING** (L7) |
| A warring faction hires them | No faction-hires-company path | **MISSING** (L13) |

Reveals **L13** and **L17**.

#### P. The dragon and its hoard (Principles 3, 5)

| Link | Mechanism | Status |
|---|---|---|
| A dragonkin holds a lair | Lair occupant spawning on authored LAIR Places | LIVE (authored) |
| It hoards wealth from raids | `drive_profile` has `territorial_predator` / `opportunistic_raider`, but no hoarding drive | **MISSING** |
| Word of the hoard spreads | Gossip (W2.2) | **MISSING** (L4) |
| Adventurers are drawn to it | Quest/opportunity route scoring | LIVE |
| The dragon falls and the hoard floods the local economy | Gold is conserved. Pricing is global. | Partial |

Reveals **L15**: Principle 3's creature-specific drives, beyond two raider/predator profiles.

#### Q. The veteran's last campaign (Principle 2 plus time)

| Link | Mechanism | Status |
|---|---|---|
| A hero ages into an elder | Age brackets exist. The real elder threshold is about **17.28M ticks**, so no normal run has ever observed it (M9). | LIVE but **never observed** |
| Elders gain wisdom and charisma and lead | Elder modifier; sociability-based leadership | LIVE |
| They die of old age, leaving a legacy | Death dispatch, feud/wish/heir, legend | LIVE (Campaign reach) |

Reveals **L14**: life-arc stories can't be seen at any observable run length.

#### R. The myth that outgrew the man (Principles 8, 1)

| Link | Mechanism | Status |
|---|---|---|
| A modest hero dies | HERO `entity_death` → fame | CAMPAIGN |
| The retelling drifts from the truth | Chronicle Fidelity Drift | CAMPAIGN |
| A belief forms around the distorted legend | `BeliefInstitution` scaled by fidelity | CAMPAIGN |
| Believers act on it | Route bias for `QUEST_OPPORTUNITY` | CAMPAIGN |

**Almost fully built.** Its only limit is reach: Campaign mode, one corpus profile. It's the best evidence that the per-tick notability bridge (W2.1) is worth building.

#### S. The border marriage (the vision's Principle 1 example)

| Link | Mechanism | Status |
|---|---|---|
| Two people from rival countries marry | `MARRIAGE` (both parties free to refuse) | LIVE |
| War moves the border | Conquest is unreachable in practice | STARVED |
| The spouses end up on opposite sides | Affiliation is independent of marriage by design (idea 39) | LIVE |
| Small frictions: reluctance to raid the region where one's spouse lives | Bonds never push on combat or war-route decisions | **MISSING** |

Reveals **L12**: loyalties from bonds pushing on political action (Principle 4's "quiet version").

#### T. The haunted battlefield (Principles 5, 3)

| Link | Mechanism | Status |
|---|---|---|
| A great battle kills many | Deaths → trauma | LIVE (STARVED) |
| The land sickens | Biome shift (e.g. PLAINS→DESERT at trauma 80, →WASTELAND at 150) | LIVE |
| The dead rise | Magical/demonic spawning at calamities (flag OFF). Undead are an "Excluded" species with no population concept. | OFF / **MISSING** |
| It's remembered as haunted | Place history and name | **MISSING** (L9) |

Reveals **L15** and **L9**.

#### U. The trading post at the crossroads (Principles 5, 6)

| Link | Mechanism | Status |
|---|---|---|
| Travellers repeatedly pass one spot | No traffic measure | **MISSING** |
| A market forms there | Places are created only at world compile time | **MISSING** (L17) |
| It grows into a town | Settlement tiers | **MISSING** (L8) |

Reveals **L17**.

#### V. The tamed beast (Principle 3, cross-species bonds)

| Link | Mechanism | Status |
|---|---|---|
| A hunter spares a wolf cub | No non-lethal outcome that creates a bond | **MISSING** |
| A bond forms across species | `SocialBond` is species-agnostic in shape | Structure LIVE; no producer |
| The companion fights beside them | Party membership is humanoid-assumed (verify) | Unverified |

Low priority. Listed because it tests Principle 3: a wolf's loyalty should be territorial and instinctive, not an oath.

### 2.8 Expanded set: summary

| Scenario | Strongest existing support | Missing link types |
|---|---|---|
| G Feud | Lineage death dispatch (feud, wish, heir) | L12 |
| H Spider ruin | Camps and raids | L9, L17 |
| I Refugee | Displacement, original home | L9, L1 |
| J Smith lineage | `TEACH` contract | L11 (+ idea 49 content) |
| K Coward's redemption | Flee bias, defection, notoriety | L2, L3 |
| L Rivals | `RIVAL` role, grudges | L5 (personal) |
| M Blight | Hazard kinds, migration | L10 |
| N Bread riot | Scarcity, pricing, migration | L16 |
| O Bandit clan | Defection, groups | L7, L13, L17 |
| P Dragon hoard | Authored lairs | L15, L4 |
| Q Veteran | Age brackets, legacy | L14 |
| R Myth | Fame, fidelity, belief (nearly complete) | reach only (W2.1) |
| S Border marriage | Marriage, affiliation independence | L12 (+ L0) |
| T Haunted field | Biome shifts | L15, L9 |
| U Trading post | — | L17, L8 |
| V Tamed beast | `SocialBond` shape | L15 |

The expanded set shows two things the original six didn't:

1. **Death and lineage (M5) and displacement (idea 65) are this project's strongest emergent substrate.** The best near-term stories start from a death, not a level-up.
2. **Places are the weakest layer.** They can't be founded, change kind, be abandoned, or remember anything at runtime. That breaks the vision's own headline example (H).

---

## 3. Diagnosis: the recurring missing link types

| # | Missing link type | Breaks scenario steps | Why it matters |
|---|---|---|---|
| **L1** | **Individual lived history.** An entity durably records what happened to *it* (survived, exposed, killed someone notable, was betrayed, was displaced). | A1, A2, A4, C1, D2, F1 | Everything downstream needs a per-entity cause to point at. Today only *losses* are remembered, as tactical advice. |
| **L2** | **History → lasting change.** Recorded history changes disposition or capability, not only XP. | A2, A3 | Principle 2's own open "worth building toward". |
| **L3** | **Being known as an individual.** A per-entity notability with a *kind of fame* (dread, renown, reverence, infamy) and a **name**. | A8, A13, C4, D4 | The world can't react to someone it can't refer to. Fame exists, but only for heroes and only in Campaign mode. |
| **L4** | **Knowledge travelling between entities.** Gossip about a notable entity, with distortion. | A12, C4 | Without it, reaction is either omniscient or absent. |
| **L5** | **Targeted response.** Systems that act on a *specific* notable entity: a named bounty, a hunting party, avoidance, pilgrimage. | A9, A11, D5 | Turns recognition into consequences and feeds back into L1 (the wolf survives the hunters). |
| **L6** | **Leverage.** Accumulated means (wealth, followers) buying *capabilities*: protection, labour, influence. | B3–B6, C2, F3 | The suggestion's "power conversion", reduced to its coarse, observable core. |
| **L7** | **Individual → institution.** A notable living entity attracts followers who become a durable organisation. | C1, C3, C5, F3 | The endpoints (clans, belief institutions) exist; the growth path doesn't. |
| **L8** | **Settlement and polity standing.** Qualitative tiers, founding and splitting. | E5, E6 | The top of the "village → capital" and "fragmentation" arcs. |
| **L9** | **Place succession and memory.** Places change kind or owner at runtime, persist when abandoned, get colonised, and carry a history and a name. | H, I, T | The vision's headline Principle-5 example is unreachable without it. `PlaceState.kind` has no runtime update path. |
| **L10** | **Spatial contagion.** A condition (blight, corruption, disease, fire) spreads across region adjacency. | M | Only scarcity propagates today. One primitive would serve several scenarios. |
| **L11** | **Lineage of skill.** Who taught whom; a maker's mark on items. | J | Teaching already exists; recording it is cheap. |
| **L12** | **Kinship politics.** Marriage and feuds act *between groups*, and bonds push on political and combat choices. | G, S | Principle 4's "quiet version". The lineage mechanics exist, but their effect stays inside a single entity. |
| **L13** | **Persistent companies.** Groups become organisations with income and employers (mercenaries, bandits, guild crews). | O | The bridge between groups and factions. |
| **L14** | **Life-scale pacing.** Lifespans and generations become observable in runs. | Q | About 17.28M ticks to reach elder age: no run ever sees a life arc. This is the Against the Storm lesson. |
| **L15** | **Species drives.** Creature-specific motives and life shapes (hoarding, reanimation, taming instinct), beyond two raider/predator profiles. | P, T, V | Principle 3: different creatures, not reskins. |
| **L16** | **Crime and order.** A theft action, and enforcement that responds to it. | N, F1 | The counterforce to wealth, and the source of infamy. |
| **L17** | **Runtime founding.** Camps, hideouts, trading posts and settlements founded during play. | H, O, U | Today every camp and Place is authored at compile time. |
| **L0** | **The *right* combat actually happening** (the root gate). | A3, A4, A11, E4 | Now root-caused; see §3.1. Every combat-driven link waits on it. |

### 3.1 Update on L0 after merging `main` (2026-09-19)

Two results landed on `main` while this doc was being written. Both sharpen the gate.

1. **Why the decision-driven attack never fires** (`TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`, closed, #219): the strategic layer almost never points entities at combat objectives. When the tactical brain does run (throttled by a three-layer sticky-task/cadence stack), it almost never finds a hostile that is in range *and* perceived. Decisions that are made execute and persist; nothing is lost. **Whether this should change is a design question left to the user**, and it is exactly the question this program depends on. The scenarios above need entities that *choose* conflict for reasons (hunting a named threat, avenging, raiding for a hoard). They don't need more incidental collisions.
2. **Most real combat is decided by the wrong hostility source** (`TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION`, P1, open). Opportunity attacks (`resolve_multi_attack()`) produce nearly all combat. They decide hostility from the raw 4-value legacy `Faction` enum, not the authored per-pair catalog (`is_hostile_compat()`) that the decision path uses. Measured disagreement: **34% of legacy-triggered hostile pairs in `crowded_frontier` and 97% in `hero_guild_routing`** are not hostile under the authored model.

**Implications for this program:**
- **W1.1's combat-derived experience kinds** (`SURVIVED_NEAR_DEATH`, `KILLED_NOTABLE`, `SURVIVED_HUNT`) should wait for hostility unification. Otherwise entities will accumulate lived history, and later epithets and feuds, from fights the authored world says shouldn't happen. That would give Principle 8 a false story to tell.
- **Non-combat kinds are unaffected:** `DISPLACED`, `LOST_BOND` (from any death), `BETRAYED`, `SUSTAINED_EXPOSURE`. This strengthens §9 decision 7 (start from death, bonds and displacement).
- **W3.1 (named bounties) and W3.5 (rival-seeking routes) are strategic-layer answers** to finding (1): they give the strategic layer reasons to point entities at a specific combat objective. They could be scoped as part of the design response to #219 rather than after it.

---

## 4. The proposed program

Twenty-three capabilities in five waves (plus Wave 0). Each wave produces a *complete, observable* chain on its own; nothing waits for the whole program before anyone can see it. Each capability lists:

- the principle it serves;
- a precedent from a similar game;
- the existing hook it extends;
- a minimal slice;
- durable state;
- how an observer sees it;
- a proof;
- its gate;
- a size estimate.

### Wave 0: gate and honesty (no new mechanics)

| Item | Why it comes first |
|---|---|
| `progression-starvation-chain` (its P0 attack-path investigation is closed, see §3.1) and `TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION` (P1) | L0. Without the *right* combat, A3/A4/A11/E4 never fire, or fire from the wrong fights, however much else is built. The design answer to #219 ("should the strategic layer point entities at combat more?") is where W3.1/W3.5 can enter. |
| Evolved-kind audit | Hypothesis, unverified: evolved kinds (`WOLF_EVOLVED`, `DIRE_WOLF`, `ORC_SCOUT`) may fall out of lookups keyed by kind (`NEST_RACE_KINDS`, `TERRITORY_MATURITY_RATES`, catalog/faction resolution). Needs a decision: add a stable `base_kind`, or drop the form change. Wave 1 builds on this mechanism. |
| Keep-or-delete decisions on the flagged-OFF growth loops (territory, nest spread, three reproduction paths) | A6/A7/E2 depend on them, and flags rot. |
| `WIRE-REGIONAL-PRESSURE-ECONOMY` (P1, open) | A10. Makes danger reach the economy. |
| Nemesis-promotion live caller; fix the stale `src/progression/evolution.py` reference in `lifecycle_systems_contract.md` | Dormancy the vision's Principle 7 already names. |
| **Life-scale pacing decision (L14)** | Before building any generational arc (Q, G), decide how a lifespan becomes observable: compressed life-stage clocks for named entities, a "life-arc" corpus tier with long cadences, or accept Campaign episodes as the generation unit. This is a decision, not code. |
| Fix the stale transformation description in `docs/world/threat_and_consequences_contract.md` | It describes a PEACEFUL→TROUBLED→…→FORSAKEN state machine. The live `TransformationService` is a biome-shift table (e.g. FOREST→BURNT_FOREST at trauma 50). |

### Wave 1: individual lived history (L1, L2)

**W1.1 Formative Experience Record** (foundation for everything after)
- **Principles:** 2, 8.
- **Precedent:** the Nemesis system (enemies remember *how* they survived); Wildermyth (transformations tied to named events); Dwarf Fortress historical-figure records.
- **Hook:** `CausalMemoryEntry` (bounded, live, loss-only) and `NarrativeLedger` (chronicle events).
- **Slice:** a typed, bounded per-entity list of `FormativeExperience(kind, tick, region_id, counterpart_id, magnitude)`. Only a few kinds are recorded:
  - `SURVIVED_NEAR_DEATH`
  - `KILLED_NOTABLE`
  - `SURVIVED_HUNT` (was targeted and lived)
  - `SUSTAINED_EXPOSURE` (N ticks inside a `hazard_kind`)
  - `BETRAYED`
  - `DISPLACED` (idea 65)
  - `LOST_BOND` (a bonded entity died)
  - `RIVAL_FELL` (a rival or nemesis died)
  - `STOOD_FOR_BOND` (fought while a bonded entity was threatened)

  It applies to **every entity kind**. Older entries are compressed into per-kind counters, which is the "bounded history" answer to the suggestion's §9.
- **Durable state:** a typed component and update type, applied through the authoritative path.
- **Legibility:** each entry can emit a narrative event. This is the raw material for W3.3.
- **Proof:** a scripted scenario where each kind fires once and the record survives a save round-trip.
- **Gate:** none for the record itself. Combat-driven kinds wait on L0.
- **Size:** M.

**W1.2 Scarred by Experience** (disposition drift)
- **Principles:** 2 (quoted directly: "survived three near-deaths and grown visibly warier… not higher level"), 6.
- **Precedent:** CK3 traits earned from events; Dwarf Fortress dwarves hardened by repeated exposure to death.
- **Hook:** `PersonalityComponent` (greed, bravery, sociability, industry) is frozen today, with no update type. The existing bravery-driven engage/flee bias does the behavioural work.
- **Slice:** a deterministic drift derived from W1.1 counters. Examples:
  - `SURVIVED_NEAR_DEATH` → bravery steps down to a floor;
  - `KILLED_NOTABLE` → bravery up;
  - `BETRAYED` → affects the trust baseline for new contracts.

  Species framing (Principle 3): for non-humanoids, the same counter feeds *territorial caution* or *aggression*, not trust.
- **Decide first:** finish idea 8's orphaned `MotivationModel`/`ValuePreferenceProfile`, or extend `PersonalityComponent` and prune idea 8. Never build a third model.
- **Legibility:** "grew warier after surviving the ambush at Red Ford".
- **Proof:** two entities from one template; one survives a scripted near-death; their engage/flee decisions measurably diverge afterwards.
- **Size:** M.

**W1.3 Adaptation by Exposure** (history-driven capability, the wolf's A1→A2)
- **Principles:** 2, 3, 5 (a place changes the creature that lives in it).
- **Precedent:** Wildermyth transformations; Caves of Qud mutations. The suggestion's "survives poison repeatedly → resistance".
- **Hook:** `EnvironmentService.calculate_hazard_drain` and the faction-level `hazard_immunities` vocabulary.
- **Slice:** a per-entity earned endurance to a `hazard_kind` after a `SUSTAINED_EXPOSURE` threshold. It is additive to faction immunity and uses the same check. Observable consequence: the entity can now **live in the corrupted place** where others can't, so it becomes that place's resident. That is territorial differentiation, not a stat bonus.
- **Then idea 50 (M10):** the alternate evolution branch at level 10/25/50 fires if the entity carries an earned endurance or a place-tied material. This gives idea 50 the numeric anchor its card lacks: *the branch is anchored to the hazard kind*.
- **Rarity:** the thresholds are long. Most entities flee hazards, so only survivors adapt.
- **Gate:** Wave 0's evolved-kind audit (for the idea 50 half only).
- **Size:** S (endurance) + M (idea 50).

**W1.4 Living Relationship Decay**
- **Principle:** 6. This is the alignment audit's candidate G.1, which the vision itself calls "genuinely open".
- **Slice:** trust and grudge between living pairs drift toward neutral with inactivity (`last_interaction_tick`). Grudges backed by recent `fear_history` may curdle instead. It surfaces through `SocialBond.role` crossings, which are already derived from sentiment.
- **Size:** S–M.

### Wave 2: being known (L3, L4)

**W2.1 Notability & Epithets** (per-tick, any entity kind)
- **Principles:** 1, 3, 8.
- **Precedent:** Dwarf Fortress named megabeasts and legends; Nemesis rank and titles.
- **Hook:** the fame pipeline (`FameDeriver` → `LegendFact`) proves the shape, but it is heroes-only and Campaign-only, and that reach is too narrow.
- **Slice:** a per-entity **notability** scalar with a *kind*, derived per tick (at a low cadence) from W1.1 counters:

  | Kind of notability | Driven by |
  |---|---|
  | `DREAD` | killing notables, surviving hunts (the wolf) |
  | `RENOWN` | quests, victories (the hero) |
  | `REVERENCE` | followers, W4.2 (the preacher) |
  | `INFAMY` | betrayal, theft (the thief) |

  - Crossing a high threshold grants an **epithet** from `ChronicleNamer`-style templates keyed by kind, species and region: "the Ash Fang of Red Valley", "Mara the Oathbreaker".
  - The epithet is a durable, typed field, written once and never regenerated.
  - Only the top-K entities per region can hold an epithet. That keeps significance rare, bounds cost, and creates competition.
- **Relation to M5:** at episode boundaries, notability feeds the existing fame → legend → belief chain, which is then no longer heroes-only.
- **Legibility:** the epithet itself, plus the chronicle event "Red Valley begins calling it the Ash Fang".
- **Proof:** a scripted wolf with injected formative experiences crosses the threshold and gets an epithet that is stable across a save round-trip.
- **Size:** M.

**W2.2 Gossip: knowledge travelling between entities**
- **Principles:** 8 (the world tells on itself, *to its own characters*), 1.
- **Precedent:** Dwarf Fortress rumors; Caves of Qud distorted histories; the fidelity drift idea we already have.
- **Hook:** `BeliefEntry` and `BeliefCycleSystem.process_rumor()` (live, but only guild intel calls it); the `PAID_INFORMATION` contract; `nearby_entities()` spatial queries.
- **Slice:** at a low cadence, entities near each other share beliefs **about notable entities only** (W2.1 holders): where the entity was last seen, its kind of notability, and its danger. Each hop lowers confidence and may blur the position.
  - The vision's Uncertainty Rule applies: vague leads stay vague.
  - Bounded: only a few beliefs per entity, only about notables, and only between entities within a set distance of each other.
- **Legibility:** "heard from a traveller that the Ash Fang hunts the north road".
- **Size:** M.

### Wave 3: the world acts on a specific entity (L5)

**W3.1 Named bounties and hunting parties**
- **Principles:** 1, 6.
- **Precedent:** the Nemesis hunt; Kenshi bounties.
- **Hook:** `BOUNTY` quest kind (generic today); `QuestGenerator` weighting bounties by trauma; the faction `COMMISSION_QUEST` directive; `FORM_PARTY` routes.
- **Slice:**
  - Add a **typed** `target_entity_id` to `QuestState`. It's free-form metadata today, which the durable state rule forbids for this purpose.
  - A faction or settlement whose region hosts a `DREAD` notable generates a named bounty.
  - Heroes who believe (W2.2) where the target is pursue it, and parties form around it.
  - Outcomes feed back: the hunters die, and the wolf records `SURVIVED_HUNT`, so its dread rises. **This is the suggestion's escalation loop, closed with existing parts.**
- **Gate:** L0 (the starvation chain).
- **Size:** M.

**W3.2 Avoidance and economic ripple**
- **Principles:** 1, 6.
- **Hook:** `RegionThreatClassifier` (today by region trauma only) and the Wave-0 pressure-economy wiring.
- **Slice:**
  - The classifier also reads known notable threats in a region from the entity's own beliefs, so avoidance is per-entity and information-dependent.
  - Merchant/shopkeeper supply routing avoids them.
  - Supply scarcity propagates to neighbouring regions through the now-wired pressure model.
  - There are no caravans. The "trade routes move" beat emerges as *who is willing to travel where*.
- **Size:** S–M.

**W3.3 "Why is it like this?": cause lists and biographies**
- **Principle:** 8.
- **Precedent:** RimWorld's per-mood cause list; Dwarf Fortress legends mode.
- **Slice:** a read-only per-entity biography presenter (never a raw domain model). It shows formative experiences, disposition drift with causes, earned endurances, notability kind and epithet, and belief or following memberships. It extends the existing entity-timeline surface (check D15 first).
- **Rule:** ship this *with* W1.2 and W2.1, not after them.
- **Size:** S–M.

**W3.4 Crime and order** (L16; scenarios N and F)
- **Principles:** 4, 6.
- **Precedent:** Kenshi's law and bounty system; Dwarf Fortress justice.
- **Hook:** `THEFT` in the legality table and the reputation weights; the `GUARD` role; notoriety.
- **Slice:**
  - A theft action (take from an inventory or a shop stock), appraised by greed, need (hunger/scarcity) and the region's legality.
  - A witnessed theft becomes `INFAMY` (W2.1) plus a belief held by the witness (W2.2).
  - Guards pursue *known* offenders (belief-driven). A caught thief loses the goods and gains notoriety; an escaped one records a `SURVIVED_HUNT` experience.
- **Counterforce role:** this is the natural resistance to W4.1's wealth accumulation (§5).
- **Note:** idea 1's orphaned `SabotageAction` is a sibling. Decide whether to wire or prune it in the same card.
- **Size:** M.

**W3.5 Personal rivalry that steers behaviour** (scenario L)
- **Principles:** 4, 2.
- **Hook:** the `RIVAL` bond role (live) and nemesis promotion (dormant).
- **Slice:**
  - Wire `check_nemesis_promotion()` to a live cadence.
  - A nemesis or rival raises the value of routes where the other is believed to be, for confrontation or competition depending on bravery.
  - A rival's death is a formative experience (`RIVAL_FELL`).
- **Size:** S.

### Wave 4: leverage and institutions (L6, L7)

**W4.1 Wealth buys capabilities (coarse leverage)**
- **Principles:** 1, 4, 7.
- **Precedent:** Norland and CK wealth → retainers → influence. The suggestion's merchant scenario, deliberately reduced to a coarse core.
- **Hook:** `inventory.gold`; the `PROTECTION` contract (DORMANT, appraisal exists); `RECRUITMENT` (live, with an employment cost); faction vault gold (taxation).
- **Slice:**
  1. An entity with surplus gold and a known threat (W2.2) offers `PROTECTION` contracts. This wires the dormant contract kind to a real producer.
  2. It becomes a patron (a coarse `patronage` link) of the entities it pays. Patrons appear in their loyalty pushes (Principle 4: one more independent loyalty, not a resolver).
  3. Donations to a clan add to its asset footprint, which clan dissolution already reads.
- **Explicitly not built:** a general power-conversion framework or ten power axes.
- **Size:** M.

**W4.2 Followings and founding** (the preacher, the gang leader)
- **Principles:** 2, 4, 1.
- **Precedent:** Norland (individual → institution); CK3 factions.
- **Hook:** group leadership election; `ClanLifecycleService` (succession, dissolution); `BeliefInstitution` (legend-derived, Campaign-only today); clan founding path (verify what triggers new clan creation today).
- **Slice:**
  - An entity with `RENOWN` or `REVERENCE` notability can **attract followers**. A follow decision is appraised by each candidate's own trust, bond and disposition (Principle 2: they can refuse).
  - A following that persists past a threshold founds a clan with that entity as leader.
  - Reverence-type followings create a `BeliefInstitution` around a *living* figure, per tick. That extends idea 63 beyond the dead-hero Campaign path.
  - Donations (W4.1) fund it; followers carry its belief into their loyalty pushes.
  - **Conflict with authority emerges through existing sentiment and loyalty drift.** No new conflict system.
- **Size:** L.

**W4.3 Provenance with a consumer** (the relic)
- **Principles:** 5 (object-level memory), 8.
- **Hook:** idea 30 `ItemInstanceService` (OFF, deferred for lack of a consumer) and live heirloom transfer.
- **Slice:**
  - Turn item history on **only** for items carried by an entity with an epithet (W2.1). This bounds cost to the rare few.
  - Consumer 1: an heir carrying a notable ancestor's item inherits a share of their renown or reverence.
  - Consumer 2: a reverence institution (W4.2) values its founder's relic, so its members appraise recovering it as a goal.
  - Wars over relics are deferred (Wave 5, if ever).
- **Size:** M.

**W4.3b Lineage of skill** (L11; scenario J; extends W4.3)
- **Hook:** the `TEACH` contract (live) and item history.
- **Slice:**
  - Record `taught_by` on the recipe a student learns.
  - Items crafted by an epithet-holding smith carry the maker's mark through W4.3's provenance.
  - A student of a famous master starts with a small share of their renown in craft contexts.
- **Content dependency:** idea 49's place-tied recipes. The live registry has only 3 recipes, so lineage has little to pass on without it.
- **Size:** S (+ idea 49).

**W4.4 Kinship politics** (L12; scenarios G and S)
- **Principles:** 4 (loyalties push independently; no resolver), 1.
- **Precedent:** marriage alliances and claims in Crusader Kings.
- **Hook:** `MARRIAGE` (live), inherited feuds and dying wishes (live), clan reputation, faction sentiment.
- **Slice:**
  - A marriage between members of two clans nudges clan-to-clan sentiment warmer. An inherited feud nudges it colder.
  - Bonds (spouse, kin, FRIEND) add a *reluctance push* to combat and raid decisions against a region or faction where the bonded entity lives. This is a loyalty push, never a veto, per Principle 4's quiet frictions.
  - Wire the currently dead betrayal branch, so that a betrayal between clans in a marriage becomes a named chronicle event ("the Broken Vow of …").
- **Size:** M.

**W4.5 Persistent companies** (L13; scenario O)
- **Principles:** 4, 1.
- **Precedent:** mercenary companies in Crusader Kings; squads in Kenshi.
- **Hook:** `GroupRecord`, `RECRUITMENT` with employment cost, clan lifecycle, faction vault gold, and W4.1 `PROTECTION`.
- **Slice:**
  - A group that persists past a threshold with a stable leader becomes a *company*: a clan variant with a treasury.
  - Companies accept `PROTECTION` contracts from wealthy entities, and hire contracts from factions at war paid from the faction vault. Deserter or outlaw companies instead take bounties' targets as their prey.
  - A company whose leader dies goes through clan succession (live).
- **Counterforce:** war exhaustion and unpaid contracts dissolving the company.
- **Size:** M–L.

### Wave 5: structural transformation (L8)

These are high-risk and start only after Waves 1–4 prove observable in real runs.

| Capability | Principles | Slice | Risk |
|---|---|---|---|
| **W5.1 Settlement standing tiers** | 5, 6 | Derive a qualitative tier (hamlet / village / town / city / capital) from population cohorts, Place capacity, trade throughput and clan/institution presence. Crossing a tier changes what the place *does*: service availability, the raid target list, the migration pull. | Moderate. Needs throughput metrics that don't exist yet. |
| **W5.2 Places remember political history** | 5 | A bounded per-region ownership trail plus a "contested" value, consumed by loyalty drift (idea 56) and home/exile (idea 59). A scope extension of ideas 59/66. | Low, but conquest must actually happen (L0). |
| **W5.3 Polity founding and splitting** | 4, 6 | A large following or a W5.1 city whose loyalty drift diverges from its country's can secede, and a new faction is founded. This finally *emits* `faction_destroyed`/founding events that culture and chronicle already consume. | High: faction identity is load-bearing everywhere. Needs its own design spec. |
| **W5.4 Pressure pacing** (a storyteller-lite) | 6 | Only if measured runs show long dead stretches: a pressure evaluator biases calamity *location* toward regions with notable threats or strained polities. | Deferred. Calamity intervals already pace. |
| **W5.5 Place succession and runtime founding** (L9, L17; scenarios H, I, O, T, U) | 5, 6 | (1) A `PlaceUpdate` write path, so a Place can change kind at runtime (idea 48 at Place level: CAMP→ABANDONED_CAMP→NEST, SETTLEMENT→RUIN). (2) An abandoned Place persists and can be claimed by any kind whose settlement shape fits (a nest colonises the ruin). (3) A bounded per-Place history (founded by, cleared by, occupants) plus a place epithet ("the Spider Ruin of Old Fenwick"). (4) Runtime founding of camps and hideouts by persistent groups or companies, and of trading posts where traffic accumulates. Also feeds refugee grief (I): a displaced entity's `home` points at a Place whose later history they can learn through gossip. | Moderate. Place is load-bearing since idea 66, but the change is additive. **Highest-value item in W5**: it unlocks the vision's own headline example. |
| **W5.6 Spatial contagion** (L10; scenario M) | 6, 5 | A generic adjacency spread for a region condition, reusing the shape of `propagate_cross_region()` (factor, gap, cap). First instance: a hazard kind (corruption/blight) spreading into neighbours. Resistance comes from stability and from W1.3 residents. Disease is a later instance, if ever. | Moderate. Runaway risk: needs decay and recovery (biome `trauma_less` recovery already exists). |
| **W5.7 Species drives** (L15; scenarios P, T, V) | 3 | Extend `drive_profile` beyond `territorial_predator` / `opportunistic_raider`. A `hoarder` (dragonkin) accumulates wealth into its lair and defends it. A `reanimator` / undead population concept gives the "Excluded" undead a way to persist (rising from mass-death regions). A taming instinct lets bonds form across species. Each drive must change *behaviour shape*, not just thresholds (the vision's explicit warning). | Moderate. Content-heavy: each drive needs corpus coverage. |

---

## 5. Counterforces: keeping runaway growth from becoming the norm

The suggestion's §31–32 is right that growth loops need natural resistance rather than arbitrary caps. Every loop above is paired with a counterforce that already exists or comes in the same wave.

| Growth loop | Counterforce | Status |
|---|---|---|
| Dread notable grows (A) | Named bounties and hunting parties (W3.1); top-K epithet competition; old age and death | W3.1 new; lifecycle live |
| Adaptation spreads (W1.3) | Long thresholds; most entities flee hazards; hazard drain kills most who try | By construction |
| Wealth concentrates (B) | Taxation (live); theft (**F1 missing**, a candidate for W4.1's sibling); rivals' `PROTECTION` | Partial |
| A following grows (C) | Refusal appraisal; succession on the founder's death (clan lifecycle, live); schism via loyalty drift | Mostly live |
| A settlement grows (E) | Scarcity → migration (live); raids target larger places; disease | Partial (no disease) |
| War escalates | War exhaustion drain (live) | Live |
| A company grows (W4.5) | Unpaid contracts; war exhaustion; the leader's death → succession | New + live |
| Contagion spreads (W5.6) | Decay; stability resistance; biome recovery (`trauma_less`) | New + live |
| Crime spreads (W3.4) | Guards; infamy blocking trust (the trust hard-reject gates, live) | New + live |
| A hoard grows (W5.7) | Hoard gossip draws adventurers | New |

**Design rule:** a new growth loop doesn't ship without its counterforce in the same wave.

---

## 6. Scenarios re-traced with the program in place

| Scenario | Now enabled | Still intentionally absent |
|---|---|---|
| **A Wolf** | Exposure memory (W1.1) → earned endurance and residency (W1.3) → idea 50 form branch → survives hunts (W1.1 + W3.1, after L0) → DREAD epithet (W2.1) → gossip (W2.2) → named bounty and parties (W3.1) → avoidance and supply ripple (W3.2) → at episode boundaries, legend → belief (M5, now not heroes-only). The "cult worships it" step has two sources: fear-reverence at the clan level (existing M5 chain) and W4.2 reverence for a *living* figure. | Caravans as objects; the wolf "leading" other predators (nest spread only) |
| **B Merchant** | Wealth → `PROTECTION` contracts and patronage (W4.1) → loyalty pushes → funding a following (W4.2) | Supply-chain control, monopoly mechanics, a direct political office (deferred; importance signal DESIGNED) |
| **C Preacher** | Renown/reverence (W2.1) → followers who can refuse (W4.2) → donations (W4.1) → a clan and a living-figure belief institution (W4.2) → friction with authority via existing loyalty drift and sentiment | A doctrine model; persecution mechanics |
| **D Artifact** | Carried by an epithet holder → provenance on (W4.3) → heirloom inheritance (live) → renown inheritance and relic-seeking goal (W4.3) | Wars fought over a relic |
| **E City** | Standing tiers (W5.1), political memory (W5.2), secession (W5.3) | Disease; an imperial layer |
| **F Beggar** | Theft (W3.4) → INFAMY epithet (W2.1) → gang leadership (live) → following (W4.2) → company (W4.5) | Rulership and offices (W5.3 + importance signal) |
| **G Feud** | Feud and wish inheritance (live) → clan sentiment and a failed marriage-truce, then the named Broken Vow (W4.4) | Named feuds beyond chronicle events |
| **H Spider ruin** | Camp founded (W5.5) → raids (live) → cleared → ABANDONED_CAMP (W5.5) → nest colonises it (W5.5 + nest spread decision) → place epithet | — |
| **I Refugee** | Displaced (live) + `DISPLACED` experience (W1.1) → learns the home's fate by gossip (W2.2) → return pull (idea 59) → finds a successor occupant (W5.5) | Grief as an emotion model (kept to a route and disposition push) |
| **J Smith** | Teaching (live) + `taught_by` + maker's mark (W4.3b) → masterwork provenance (W4.3) | Needs idea 49's recipes first |
| **K Coward** | Flight (live) → infamy → a `LOST_BOND` stand moves bravery up (W1.2) → renown (W2.1) | — |
| **L Rivals** | RIVAL (live) → nemesis promotion wired, rival-seeking routes (W3.5) | — |
| **M Blight** | Corruption spreads (W5.6) → residents adapt (W1.3) → famine and migration (live) | Disease |
| **N Bread riot** | Scarcity (live) → theft (W3.4) → guard response → loyalty fraying (idea 56) | Riots as a crowd mechanic |
| **O Bandit clan** | Defection (live) → company (W4.5) → hideout founded (W5.5) → hired by a warring faction (W4.5) | — |
| **P Dragon** | Hoarding drive (W5.7) → gossip about the hoard (W2.2) → adventurers (live) → wealth shock (live, global) | Region-local price shocks |
| **Q Veteran** | Only after the L14 pacing decision | — |
| **R Myth** | Already built. W2.1 extends its reach beyond Campaign mode. | — |
| **S Border marriage** | Marriage (live) → reluctance push against the spouse's region (W4.4) → war (after L0) | — |
| **T Haunted field** | Biome shift (live) → reanimation drive (W5.7) → place epithet (W5.5) | — |
| **U Trading post** | Traffic → runtime post founding (W5.5) → settlement tier (W5.1) | — |
| **V Tamed beast** | Taming instinct (W5.7) | Low priority |

---

## 7. Architecture and implementability

- **Durable state (all typed, all through the authoritative apply path):**
  - `FormativeExperience` record plus compressed counters (per entity, bounded)
  - personality/disposition update type
  - earned endurances
  - notability (scalar + kind) and epithet (write-once)
  - gossip beliefs (reuse `BeliefEntry`)
  - `QuestState.target_entity_id`
  - patronage link
  - following membership
  - item provenance (idea 30, gated to notables)
  - settlement tier
  - ownership trail
- **Determinism:** every drift, threshold and epithet choice is a pure function of state plus a seeded draw. No wall-clock time, and dicts are iterated in sorted order.
- **Performance:**
  - Bounded lists everywhere.
  - Notability, gossip and following evaluation run at low cadence.
  - Epithets are limited to top-K per region.
  - Provenance is kept only for notables' items.
  - Gossip runs through the existing spatial index, never all pairs.
  - Most entities never leave the cheap path. This is the Songs of Syx lesson: the named few get detail, the population stays a weather system.
- **Per-tick vs. episode-boundary:** notability runs per tick. The existing fame/belief/culture chain stays at episode boundaries and *consumes* notability. This fixes today's narrow reach, where only one Campaign corpus profile ever sees legends.
- **Pipeline placement:**
  - W1 sits beside the memory/lifecycle phases.
  - W2/W3 sit beside information and quest generation.
  - W4 sits beside cooperation and contracts.
  - All decision logic reads state and emits updates. Per the architecture rule, no domain reads social state directly.
- **Testing:**
  - One focused scenario per capability.
  - One flagship end-to-end corpus world, **"the Ash Fang"**: a corrupted region, a wolf nest, a settlement with a guild and a faction. Its acceptance test is that without authored beats, at least one non-hero earns a DREAD epithet, a named bounty is generated, and a chronicle entry references it, across a seed set.
  - SimQ is used only for balance afterwards.
- **Governance:** register each capability in `registries/mechanisms.yaml` with its `implemented_by` and a live-caller verification. Add atlas cards (new idea numbers, or extensions of 8/30/37/50/57/63/65) and score them before ticketing.
- **Rough size:**

  | Wave | Size |
  |---|---|
  | W0 | Existing work |
  | W1 | ~3M + 1S |
  | W2 | ~2M |
  | W3 | ~1M + 2S |
  | W3 additions (W3.4, W3.5) | ~1M + 1S |
  | W4 | ~2M + 1L |
  | W4 additions (W4.3b, W4.4, W4.5) | ~1S + 1M + 1M–L |
  | W5 | ~1L + 2M + 1S, unscheduled |
  | W5 additions (W5.5, W5.6, W5.7) | ~1L + 2M |

  Roughly two milestones for W1–W3, one to two for W4, and W5 as its own later program.

---

## 8. What was rejected, deferred or corrected from the suggestion

The suggestion called itself "an external design hypothesis, not an approved specification", and asked to be challenged. Section numbers (§N) refer to the suggestion document.

### 8.1 Rejected or deferred directions

| Suggestion | Decision | Reason |
|---|---|---|
| "Progression-Driven World Simulation" / "Evolutionary Systemic RPG" as the project identity (§34) | **Rejected** | Principle 1 ("no one hands down the story") governs, and progression isn't one of the 8 principles. The project's own audit (`docs/audits/D01_rpg_feature_impact.md`) ranks Progression/Rewards Tier 3. This program makes *lived history* the substrate instead of levels. |
| Ten forms of power (physical, knowledge, economic, social, political, spiritual, informational, territorial, technological, cultural) and a general power-conversion framework (§7–8) | **Rejected as a framework** | Principle 7: "prefer one coarse signal an observer can actually feel over three precise ones nobody will ever see." W4.1 keeps the one observable core (wealth buys protection, patronage and loyalty). Wealth → military is already designed in `faction_war_drivers_proposal.md` §3.3 and deliberately parked ("faction war: foundation only"). |
| Deliberate runaway collapse ("unchecked progression can ultimately destroy [the world]", §4, §31) | **Deferred** | Not in the vision. Principle 6 already covers ambient growth and decay, and the existing growth loops (territory, nest spread, reproduction) are deliberately flagged off. §5 pairs every loop with a counterforce. Collapse as a goal needs its own decision. |
| Player-centred sections: Kenshi player trajectory (§19), the player sharing NPC progression logic (§28), no automatic level scaling (§29), bosses as the player's threats (§30) | **Not applicable** | This is an observed world with no player: "a living world you observe rather than control." The one transferable part, a world that evolves unwitnessed, is already the founding premise. |
| A universal progression abstraction shared by all entity types (§14) | **Rejected** | Principle 3 (different creatures, not reskins). The suggestion's own §25 warns against it too. This program shares one *shape* (experience → notability), with a kind-specific *meaning*. |
| A RimWorld-style storyteller (§3) | **Deferred** | Calamity minimum/forced intervals already pace the world, and there's no player experience to pace. Kept as a measurement-gated option (W5.4). |
| Caravans as simulated objects (wolf scenario: "preys on caravans", "trade routes move") | **Deferred** | W3.2 gets the "routes move" beat from avoidance and supply routing, with no new object type. |
| Artifact history for all items (§23D) | **Narrowed** | Item history (idea 30) is recorded only for items carried by epithet holders (W4.3). You deferred it earlier because it had no consumer, and it's bounded here by the rarity of notables. |
| "Wars are fought over ownership" of a relic (§23D) | **Out of scope for now** | A late-stage beat at most, after W4.3 has a real consumer and faction war is reachable. |
| "Everything can become everything" (e.g. a wolf becoming a merchant) | **Out** | The suggestion rules this out itself (§10: "base ontology + world rules + rare exceptions"), and so does Principle 3. |
| Universal XP-free progression replacing levels (§9) | **Not adopted as a replacement** | Levels stay, as the existing structural precedent (the idea 50 card relies on the 10/25/50 thresholds). Lived history is layered *alongside* them, not instead of them. |

### 8.2 Where the suggestion misjudged what already exists

These aren't rejections. The suggestion treated them as missing, but they're already built or designed, so this program builds on them.

| The suggestion says / implies | Actual state |
|---|---|
| World reaction to an entity's history is missing (§13, §27) | **Mostly built** in M5: Living Legend Fame, Belief Institutions, Culture Drift, Chronicle Fidelity Drift. Limit: heroes only, Campaign mode only. W2.1 widens the reach. |
| Ontological transformation is a new idea (§12) | `EvolutionSystem` already changes `kind` at levels 10/25/50, though nothing reads it yet. |
| "Wolf eats a corrupted creature → mutation" (§10) | Idea 50 (material-gated evolution), already carded and scheduled for M10. |
| Territory → resources → military → more territory (§31) | Idea 51 `EXPAND_TERRITORY` is live. Wealth → military is designed and parked. |
| Distorted, mythologised history (Caves of Qud reference) | Chronicle Fidelity Drift (idea 62) is built. |
| Individual → institution (Norland reference) | Clans with a full lifecycle exist. What's missing is only the *growth path* from a living individual (W4.2). |
| Statistical simulation for scale (Songs of Syx reference) | Demographic cohorts are already the aggregate layer. The vision endorses it: "a regional population count is a weather system." |
| The main bottleneck is the *shape* of progression (§6) | The actual bottleneck is that the right combat barely happens (§3.1). Shape matters less until that is fixed. |

---

## 9. Open decisions

1. **W1.2:** finish idea 8's orphaned motivation/value models, or extend `PersonalityComponent` and prune idea 8?
2. **W2.1:** should notability's four kinds be separate scalars, or one scalar with a kind tag? The trade-off is Principle 3 (distinctness) against Principle 7 (bookkeeping).
3. **Numbering:** new atlas ideas (67+) per capability, or scope extensions of ideas 8/30/37/50/57/63/65 where one fits?
4. **Theft (F1):** card it as its own idea (the counterforce to wealth)? It is also idea 1's orphaned `SabotageAction`.
5. **Program shape:** schedule as milestones M11 (W1 + W3.3), M12 (W2 + W3), M13 (W4), with W5 unscheduled until measured?
6. **Pull W5.5 (place succession and runtime founding) forward?** The expanded set shows Places are the weakest layer, and W5.5 unlocks the vision's own headline example (H). Its core (a `PlaceUpdate` path, abandonment, colonisation) depends on camp clearing, which is only partly combat-gated.
7. **Start from death, not levels?** The expanded set shows lineage and death dispatch (M5) and displacement (idea 65) are the strongest live substrate. A first milestone built around them (G, I, K, R: formative experiences from deaths, bonds and displacement) would be visible before the starvation chain lands, while the level-driven arcs (A3, A4) wait.
8. **L14 pacing:** compress life stages for named entities, add a long-run "life-arc" corpus tier, or treat Campaign episodes as the generation unit?

## References

- [`the_unwritten_world.html`](the_unwritten_world.html): the 8 principles
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (M1–M10);
- `rpg_direction_alignment_audit.md` (§E gaps, §G.1 relationship decay);
- `faction_war_drivers_proposal.md`
- `rpg_dormant_mechanism_closure_plan.md`
- [`rpg_feature_atlas.html`](rpg_feature_atlas.html): ideas 1, 8, 30, 37, 39, 40, 47–52, 56–57, 59, 62–63, 65–66
- `docs/mechanics/05_world_evolution.md`, `docs/mechanics/07_social_political_dynamics.md`
- `docs/world/threat_and_consequences_contract.md`, `docs/simulation/domains/memory_contract.md`, `docs/simulation/quest_contract.md`
- Code hooks cited:
  - `src/engine/evolution.py`
  - `src/core/state.py` (`PersonalityComponent`, `ClanState`)
  - `src/core/models/quests.py`
  - `src/domains/memory/`
  - `src/systems/strategic_systems/belief.py`
  - `src/systems/social_systems/{clan_lifecycle,guilds,contracts}.py`
  - `src/world/{displacement,boss,creature_territory,camp}.py`
  - `src/engine/{faction_decision,town_resolution}.py`
- `tickets/todos/progression-starvation-chain/SEQUENCE.md`
- `tickets/done/TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION.md` (#219), `tickets/todos/TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION.md`
