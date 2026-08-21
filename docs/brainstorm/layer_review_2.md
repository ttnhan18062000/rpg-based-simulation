I reviewed the current Revision 43 atlas, focusing on revisions 37–43 and the exact cards/ideas you named. The batch is **materially stronger than the version from the earlier discussion**, but I found a few places where the new work overstates what the evidence establishes or where one correction was not propagated everywhere.

## 1. Corrected topology — **Mostly holds up, but the shorthand is now the weak part**

The actual diagram is coherent. It now distinguishes:

* Entity **located in** City
* City **geographically inside** Region
* City **owned by** Country
* Entity **affiliated with** Country
* Clan **spanning membership**
* Race **distributed across** Countries/World

Those are different relationships rather than a forced containment ladder. That is a real improvement. 

Where it becomes shaky is the prose shorthand:

> `Entity → City → Region ≍ Country ≍ Clan → Race → World`

`≍` is doing useful explanatory work only if it means **“roughly comparable reach/scale.”** It is not itself a relationship. Region, Country, and Clan are not peers in the same structural sense:

* Region is geographic.
* Country is sovereign/political.
* Clan is membership-based.

So the detailed graph holds together better than the “spine” sentence does.

There is an additional small honesty problem at the top. The Layer Model still introduces itself as a hierarchy “already encoded” in durable-state classes, while the same page now correctly says City has no dedicated state class and Clan/Race have none at all. The diagram is honest about that with gap styling, but the opening claim is now too broad. 

And I would no longer call `→ Race → World` part of a spine at all. The atlas itself previously established Race as **cross-cutting reach**, not something Region/Country/Clan are contained in. Revision 37's compact notation partially slips back toward ladder-thinking.

**Verdict:** the corrected topology is sound; its compressed verbal representation is not quite as precise as the model it summarizes.

---

## 2. Non-contiguous Country territory — **Plausible, but currently overstated as verified**

This is the clearest overreach in the batch.

The composite says:

> Kingdom of Ember holds two Cities in two different Regions; its territory is “genuinely non-contiguous, exactly what `FactionState.territory` already supports as a tuple today.” 

A tuple/list of territory IDs proves **multiple holdings**. By itself, it does **not** prove non-contiguous holdings unless the investigation also established there is no adjacency/contiguity invariant elsewhere.

More importantly, the City/Region correction changes the semantics underneath the field. Today `FactionState.territory` holds **Region IDs**. In the corrected target model, sovereignty belongs at **City scale**, while biome Region becomes geographically separate. So the existing tuple shape is certainly *compatible with* multiple holdings, but it does not by itself prove that the future City-based ownership model already supports:

> City A in Region X + City B in Region Y, with no intervening territory.

The map can absolutely use that as an illustrative consequence of the target model. What is too strong is **“exactly what the current tuple already supports.”**

I would classify the evidence as:

> Existing state already supports a Country referencing multiple territorial units; nothing shown here establishes that those units must be contiguous.

That is slightly weaker than “verified non-contiguous territory,” but more defensible.

**Verdict:** conceptually sound; evidence claim one notch too strong.

---

## 3. Real vs. illustrative visuals — **Mostly excellent, but the inset contains one genuine contradiction**

The main visual distinction is handled unusually well.

The first city map explicitly says:

> **Real — drawn to scale from world.resolved.yaml bounds**

and shows the actual Hometown / Trading Hometown / bandit-road scenario with real counts. 

The second says:

> **Illustrative target — not yet buildable** 

The composite says:

> **Illustrative composite — every layer, one scenario**

and its surrounding text explicitly says Race markers are schematic and everything above City scale is illustrative. 

So I do **not** think the common visual style by itself creates a serious truth-status problem. A reader who reads the badges/captions will know what is real.

The zoomed inset is where a real inconsistency appears.

Its prose is careful:

> 5 buildings and 13 spawned entities are real, but building interiors, exact positions, and **which specific guards group are not literally this precise**; the layout is illustrative staging. 

But immediately inside the figure it labels:

> **“Group: Guard Patrol (3, live)”**

and its accessibility description says the three guards “already compose into a live group.” 

That's stronger than the prose's “plausibly already are one.”

So the inset currently mixes three truth levels:

* **verified:** five buildings;
* **verified:** thirteen entities / role counts;
* **illustrative:** spatial layout and which exact guards are grouped.

Yet the figure visually promotes the third item into “live.”

That's the one place where a reader really could mistake illustration for verified state.

**Verdict:** the overall labeling strategy works; fix the Guard Patrol assertion or downgrade it to illustrative/plausible.

---

## 4. Group correction and Clan lifecycle reasoning — **The conclusion survives, but less strongly than the card suggests; plus one correction didn't propagate**

The important correction is valid. Group formation really does contain an independent accept decision: recruitment is appraised against trust/history before an active recruitment contract plus proximity can materialize the Group. 

That absolutely destroys the old rationale:

> Group has no handshake; Clan needs one.

Idea 40 correctly acknowledges that. Its current rationale is instead:

> Group's acceptance concerns a transactional, expiring recruitment contract; Clan membership is a standing identity relationship. Therefore Marriage remains the closer precedent for the *durable relationship semantics*. 

That reasoning is defensible, but the correction does weaken the exclusivity of the original conclusion.

The most accurate conceptual reading now is:

* **Group recruitment** is already a strong precedent for the *joining decision*: offer → target independently appraises → accept/refuse.
* **Marriage** is a stronger precedent for what happens *after acceptance*: a durable identity-level relationship with no natural expiry.

So “Marriage is still the better precedent” is reasonable if “precedent” means the whole relationship. “Use Marriage rather than Group” would now be too categorical.

There is also a separate internal inconsistency that the revisions missed.

The Group Layer card says:

> **“Succession reuses the sociability-election rule.”** 

But Idea 40's correction explicitly says that this is **not succession**: if the Group leader dies or goes inactive, the Group immediately dissolves; the sociability rule only replaces a still-living leader who is being outclassed. 

That means the Group card's “complete lifecycle” audit still contains an old interpretation that Idea 40 has already disproved.

This doesn't make Group unhealthy—the real lifecycle can simply be:

> leader death → dissolution

—but the word **Succession** in the Group audit is wrong.

**Verdict:** corrected Clan reasoning mostly survives, but it should now be understood as combining two precedents, and the Group card itself still needs its leader-death correction propagated into it.

---

## 5. Country lifecycle — **The audit is good; the health judgment is slightly too generous**

The investigation itself is strong.

It distinguishes three things clearly:

1. no running path creates a genuinely new Country;
2. no path removes one;
3. plenty of meaningful state changes happen between those endpoints.

A Country can change diplomacy, tension, military strength, and territorial holdings, while a territory-less, strength-less Country remains forever as an inert record. 

I agree with the refined principle:

> a healthy layer does not necessarily need literal biological-style birth and death.

For something like a City or Region, that is especially sensible.

For a **political actor**, however, founding and dissolution are more fundamental than the phrase “two missing edges” makes them sound. Without them, the set of political actors is effectively **closed at world construction**. War can radically alter their state, but can never produce:

* a new polity;
* a merger that removes one;
* a destroyed state that actually ceases to exist.

So I agree with the **Partial** badge, but I would not say Country “clears the bar comfortably.” It clears the **middle-of-lifecycle** test comfortably while failing both identity-boundary transitions.

The decision to **leave it open** is right, though. The atlas's method throughout has been to distinguish:

> “here is a verified gap”

from

> “here is a design we have evidence/precedent for.”

There is no reusable creation/destruction precedent for a top-level polity. Inventing a Country-founding mechanic merely because the audit found an empty space would undermine that discipline. Revision 42 explicitly documents that reasoning rather than hiding the absence. 

**Verdict:** investigation excellent; “partial” is right; “comfortably healthy” is somewhat too forgiving. Leaving the missing edges as an open finding is the correct choice.

---

## 6. Reusing `SocialAppraisalSystem.appraise_contract()` three times — **Good shared primitive; slightly overfit when described as the whole shape**

There really is a common subproblem across all three cases:

> One character initiates a socially meaningful interaction; the target should not automatically comply; trust/history affects acceptance.

For that exact subproblem, `appraise_contract()` is a very good grounded precedent. The Group audit confirms it already handles bond sentiment or reputation/history and refuses on severe distrust/betrayal. 

So the cross-reference itself is not opportunistic reuse.

But the three domains diverge immediately after that shared gate.

**Clan joining:** acceptance creates long-lived organizational identity.

**Affiliation switching:** acceptance changes political allegiance. More importantly, “trust in the proposer” is not necessarily the same as trust in the **Country**. If a friendly ambassador from a hated polity asks me to swear fealty, personal trust and political legitimacy are different variables. Idea 39 currently says the target's trust in the proposer decides entry; that is plausible as a first gate, but calling allegiance switching “the same shape” as recruitment overstates the equivalence. 

**Conversation:** the shared gate is weaker still. A contract-like hard refusal rule is a reasonable precedent for whether someone agrees to a sensitive information exchange, but conversation also has topic, trigger, intelligence, specialist/peer routing and information-flow semantics. The card currently says Conversation should **“mirror this exact shape.”**  That phrase is stronger than necessary.

The clean interpretation is:

> `appraise_contract()` is a shared precedent for **social acceptance appraisal**, not a universal template for Clan membership, political allegiance, and conversation.

Under that interpretation, the cross-wiring is strong. If “same mechanism” starts implying same thresholds, same counterpart semantics, or same lifecycle, it becomes overfit.

**Verdict:** sound reuse at the gate level; mildly overstated at the whole-interaction level.

---

## 7. Did this actually close the original discussion's four questions? — **A lot was answered, but not all four are closed**

### Lifecycle / boundary / domain

This has advanced substantially.

Group now has a genuine full audit. Country has an explicit partial audit. Clan's lifecycle has been explored through founding, joining/leaving, leader loss and dissolution. City/Region boundaries are much clearer than before. 

But it is **not complete across all layers**.

The newly separated City has not yet received the same explicit lifecycle audit as Entity/Group/Country. Race also still mostly has a scope definition plus proposed population/relations semantics rather than the same formal lifecycle test.

So this original question is **partially answered, not closed**.

### Relationship-type taxonomy

It improved, but the City split exposes something new.

The earlier discussion added **affiliation** alongside containment, membership and distribution. The current diagram now distinguishes affiliation explicitly. 

But after the City/Region split, the graph itself now distinguishes:

> City **geographically inside** Region

from

> City **owned by** Country.

Those are not the same relationship.

So the old four-type taxonomy—containment, membership, population distribution, affiliation—is no longer quite complete unless “containment” is intentionally broad enough to cover both geographical nesting and political sovereignty, which would undo one of the main gains of Revision 37.

In other words, Revision 37 didn't just clarify an existing link. It surfaced **ownership/sovereignty as distinct from geographic containment**.

And `Region ≍ Country ≍ Clan` is not another relationship type at all; it only communicates comparable reach.

So this question is **still open at the taxonomy level**, even though the diagram itself is clearer.

### Reproduction / marriage implications

A lot was addressed after the original discussion:

* marriage does not structurally belong to a City/Country;
* child birthplace does;
* the broken population-pressure feedback loop was explicitly identified and Idea 38 attempts to close it by feeding births back into the aggregate cohort. 

But Revision 37 creates a new terminology consequence that has **not** been reconciled into Idea 32.

The reproduction entry still says a child permanently records its:

> **“birth/home region”** 

After the City split, if the intended biographical concept is “which settlement was I born/raised in?”, that is now City, not biome Region.

Likewise, the reproduction pressure still talks about **regional scarcity/capacity**. That might deliberately remain Region-scale, or it might actually be settlement health. The new City/Region distinction means this needs an explicit semantic interpretation; the old wording can no longer be taken for granted.

So the reproduction question was addressed before Revision 37, but Revision 37 **reopens part of it**.

### “What doesn't fit the link types?”

This remains the least fully resolved question.

The earlier discussion identified something important: the model isn't only topology; it also has **pressures/flows** running through that topology. Race hostility, Country diplomacy, Clan obligations, personal attachment and now information propagation can simultaneously influence the same Entity without one containing another.

The recent work reinforces that rather than resolving it into one more hierarchy edge.

I think that is actually the right outcome: “pressure/influence/information flow” is not necessarily another structural membership link. It is a **dynamic relation over the topology**.

But the atlas has not yet formalized that distinction into the layer model itself. The diagrams show structural links; ideas such as race relations, affiliation acceptance and information hubs describe causal flows separately.

**Verdict:** this original question is still productively open.

---

# Overall judgment

**Revisions 37–43 leave the layer model substantially stronger than the version reviewed in the original discussion.** The City/Region correction is not merely cosmetic; it produces a much more useful separation between geography, sovereignty, affiliation and membership. The Group and Country audits also improve the epistemic quality of the atlas: both found evidence that contradicted prior assumptions, and those corrections were mostly incorporated rather than defended away.

I would not send this batch back for another broad rethink. I would classify it as **sound with four localized issues**:

1. `Region ≍ Country ≍ Clan` and `→ Race → World` are weaker shorthand than the actual graph and risk making a non-hierarchical model look hierarchical again.
2. The composite's claim that a tuple **proves non-contiguous territory support** is stronger than the evidence shown, especially now that future ownership is City-based while the existing tuple contains Region IDs.
3. The “real” City inset correctly says exact grouping is illustrative, but the figure simultaneously labels the three Guards as a **live Group**, which contradicts that caveat.
4. The Group lifecycle card still calls SOC-228 **succession**, even though Idea 40 correctly establishes that leader death actually dissolves the Group; and the new City split has not yet propagated into reproduction's lingering **birth/home region** wording.

The cross-wiring around trust appraisal is otherwise a net positive as long as it is understood as a **shared acceptance primitive**, not proof that Conversation, Clan membership, and political allegiance are the same kind of relationship.

So: **stronger and more coherent overall, with some overstatement and stale cross-references—not a conceptual regression.**
