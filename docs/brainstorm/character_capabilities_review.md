I reviewed the page strictly on the terms in your brief: as a **standalone, non-technical capability statement**, without trying to validate anything against implementation. The page clearly establishes the four-section structure and the three intended status meanings. 

The underlying content is quite strong, especially in how often it admits limitations. But I would **not hand it to a stakeholder as-is yet**. There are a few real internal contradictions, several cards whose status becomes muddy, and some wording that sounds more like an engineering audit than a stakeholder capability overview. All card-specific observations below refer to the capability data embedded in the page. 

## Highest-priority issues

| Card                                                                        | What's wrong                                                                                                                                                                                                                                        | Suggested fix                                                                                                                                                      |
| --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Keeping Promises & Recognizing Betrayal** + **Sense of Time & Deadlines** | **Direct internal contradiction.** The first says deadline pressure is live and ramps sharply near a commitment deadline. The second says the urgency/deadline system “isn't currently active.” A stakeholder cannot tell which statement is true.  | Either merge them, or explicitly distinguish two systems: e.g. **“Commitment deadline pressure is live; the broader sense-of-time system is built but inactive.”** |
| **In-the-Moment Fight Decisions** + **Emotions**                            | The fight card says a character can be “swept up by fear” and retreat. The Emotions card says characters currently **do not feel fear, panic, confidence, etc.** because the emotion system never runs.                                             | Call the live behavior something like **danger/retreat response** rather than fear, then state that it does not use the richer emotion model.                      |
| **Combat & Tactics** + **Occupation & Social Role**                         | Combat says Heroes can be reborn up to four times **before death becomes permanent**. Occupation says Heroes **cannot be permanently killed outright in combat**. These may technically be compatible, but “cannot” reads much stronger.            | Say: **“Heroes cannot be permanently killed on their first combat death; they can return up to four times before combat death can become permanent.”**             |
| **Aging, Death & Inheritance**                                              | This is really three capabilities with different statuses: aging/death = live; inheritance = built but never triggered; aging stat penalties = built/inactive. The single Live card hides too much status complexity despite the explanatory badge. | Split into **Aging & Old-Age Death — Live**, **Inheritance — Built, not active**, and possibly **Age-Based Stat Changes — Built, not active**.                     |
| **Experience, Leveling & Mastery**                                          | Same problem. Leveling is live; broader mastery is unfinished/inactive; combat practice mastery is live; skill training is live but never chosen. That's too many independent states for one card.                                                  | Split into at least **Experience & Leveling**, **Practice-Based Combat Experience**, and **Deeper Mastery / Breakthroughs**.                                       |
| **Memory, Trust Percentages & Limited Capacity**                            | One card describes **three separate memory systems**, only one live. This is conceptually interesting to an engineer, but confusing to a stakeholder and doesn't fit one status tag.                                                                | Make the live memory behavior the card. Put the two inactive approaches into separate Built cards, or omit them from this audience-facing document.                |
| **Temporary Conditions**                                                    | Tagged as Built, yet its first sentence says several conditions **exist and genuinely affect characters now**. Conversely, the unified system does not exist. The card is simultaneously describing Live and Not Yet Built.                         | Split into **Existing Temporary Effects — Live** and **Unified Temporary-Condition System — Not yet built**.                                                       |
| **What Drives a Character**                                                 | CSS/status tier is Built, but the visible badge says **“Partially live”**, and the description says the doctrine/motivation layer actually affects choices today.                                                                                   | Split the live doctrine behavior from the inactive value-driven layer, or make the card Live and describe the inactive value layer explicitly as an extension.     |
| **Planning Several Steps Ahead**                                            | Tagged Built, but labelled **“Half-built.”** That directly conflicts with your definition of Built: underlying mechanism real and complete.                                                                                                         | If the actual capability is multi-step planning, mark it **Not yet built**. You can explain that storage for a plan exists, but plan creation does not.            |
| **A Second, Larger Mental Model**                                           | Marked Not yet built, but says an entire version is “laid out” and “almost none” is populated, implying that at least some structure exists. That conflicts with “doesn't exist in any form yet.”                                                   | Clarify whether this is **design only** or partially implemented. If design only: “A design exists, but the capability itself has not been built.”                 |

These are the ones I'd fix before anything else.

---

## Important clarity and precision issues

### **Moving Around the World**

> “the more it genuinely costs them to move each step”

**Costs what?** Stamina? time? readiness? movement distance?

For a non-developer this is incomplete. Say exactly what gets consumed or reduced.

Also, “resolved correctly rather than colliding” is slightly circular. Better to explain the result: one moves first, one waits, they exchange positions safely, etc.

---

### **In-the-Moment Fight Decisions**

“**Bracket a target**” is specialist/military terminology. A general stakeholder may not know it.

Use something like:

> “front-line fighters can coordinate with allies to attack a target from opposing sides”

Also, “roughly ten fruitless exchanges” needs a clearer definition of **exchange**. Ten failed attacks? Ten attempted actions? Ten rounds?

---

### **How Stats Become Real Numbers**

Two problems.

First, **“pipeline”** is engineering terminology:

> “combat-number pipeline”
> “mental-bandwidth pipeline”

Just say **calculation** or **system**.

Second:

> “with enough of a buffer built in that the role doesn't flicker…”

The document is otherwise unusually numerical, so “enough of a buffer” sticks out. If a threshold exists, give it.

---

### **Race & Starting Template**

> “a handful of starting-skill lists reference skills that don't actually exist”

“Handful” is precisely the type of vague qualifier the rest of the page tries to avoid.

Give the number if known:

> “3 starting-skill lists…”
> “5 references across X templates…”

If no stable number exists, just say **“some starting templates…”** and avoid presenting it as quantified-but-not-quite.

---

### **Personality**

The bravery description is concrete enough. Sociability isn't:

> “more sociable characters behave differently under pressure than withdrawn ones.”

**How?** This tells the stakeholder almost nothing.

Give one observable behavioral difference, ideally with direction:

> “more sociable characters are more/less likely to X…”

Otherwise remove that sentence.

---

### **Growing Into a Stronger Form**

> “some transform”

Who qualifies?

And are levels **10, 25 and 50** three successive transformation opportunities, or alternative thresholds used by different character types?

The card currently sounds precise while leaving the important rule unspecified.

---

### **Aging, Death & Inheritance**

This card gives detailed ±30% and −50% adjustments, yet two more fundamental numbers are missing:

* What is the **fixed lifespan**?
* At what age does a character count as **elderly**?

Those would be more useful to a stakeholder than several of the percentages currently included.

---

### **Gathering, Looting & Opening Chests**

“**Cooldown**” is common game terminology, but the brief says a non-developer should need no background knowledge.

Use:

> “an opened chest cannot be used again until a waiting period has passed.”

And since the interruption threshold is precisely stated as ~5%, the obvious next question is: **how long is the waiting period?**

If it is fixed, give the number.

---

### **Wounds & Scars**

This card is missing the most important mechanics.

We learn:

* > 25% max-health hit → Wound
* healed Wound may become a Scar
* Scar retains ~30% of original penalty

But:

1. **What is the Wound penalty?**
2. **What is the probability of a Scar?**
3. What causes a Wound to heal?

“There's a chance” is unusually vague compared with the rest of the page.

This card needs at least the first two answered if those numbers are stable.

---

### **Relationships & Affection**

> “an offer is refused outright once trust drops below roughly 0.2…”

What kind of **offer**?

Trade? Group invitation? information request? cooperation in general?

This matters because elsewhere the page explicitly says direct team-up invitations do not exist.

Name the interaction precisely.

Similarly:

> “gets formally promoted to a recognized rival”

“Promoted” sounds odd here. **“is classified as a recognized rival”** is clearer.

---

### **What Drives a Character**

The page now has several identity concepts:

* race
* archetype
* class
* occupation
* combat role
* doctrine/play-style

A developer will separate these automatically. A stakeholder may not.

This is becoming a terminology problem across the document rather than just this card.

I would add a tiny plain-language distinction somewhere near **Who Each Character Is**, for example:

> **Race/archetype** defines the starting template; **class** governs progression; **occupation** determines the character's social/job role; **combat role** describes battlefield behavior.

Then explain doctrine if it is another genuinely distinct dimension.

---

## Numbers / claims that need tightening

A major issue is the use of **“moment.”**

The document contains things such as:

* roughly **10,000 in-game moments**
* last **20 moments**
* checks running “every moment”

But nowhere does the page tell a non-developer what a **moment** represents.

If one moment is effectively a simulation tick, that term is intentionally being avoided—but replacing “tick” with “moment” doesn't solve the comprehension problem.

Define it once, e.g.:

> “A simulation moment is one decision/update cycle; it is not equivalent to a fixed number of real-world seconds.”

Or use another stakeholder-meaningful time unit if one exists.

### **Choosing What to Do Next**

> “15 distinct kinds in total”

Most other counts are self-contained:

* nine stats → all nine listed
* seven emotions → all seven listed
* six obstacle types → all six listed
* four personality traits → all four listed

But the 15 activities are not listed.

For a document designed to be checkable from itself, either:

**list all 15**, perhaps compactly, or say:

> “Characters can choose from a broad set of activities…”

I'd prefer listing them if the names are understandable.

### **Experience, Leveling & Mastery**

> “four base classes to choose from”

The four are not named.

Again, because the exact count is given, list them.

This is especially important because a later card mentions only **warrior, ranger and mage doctrines**, which could easily lead a stakeholder to wonder whether the page has accidentally changed from four classes to three.

### **Remembering Why Something Went Wrong**

> “logged at a fixed, moderate confidence level”

If it is genuinely **fixed**, give the number.

“Fixed, moderate” combines the worst parts of precision and vagueness.

### **Memory, Trust Percentages & Limited Capacity**

> “capped to a limited number of active leads”

How many?

This is one of the few places where the title explicitly promises **limited capacity** and then doesn't state the capacity.

---

## Two additional internal consistency problems

### **Different Paths to Power** vs **Experience, Leveling & Mastery**

One says:

> characters of the same class/race follow an **identical numeric path**

But the leveling card says each level gives:

> **+5 stat points to spend**

and two stats can actually receive those points.

If characters are genuinely choosing how to spend those points, then two characters can potentially follow different numeric paths.

You need to clarify one of these:

* allocation is fixed/automatic → they really are identical, or
* there is limited allocation choice → progression is **mostly fixed**, not identical.

### **Paying for Information** vs **Asking Specific People for Information**

The first effectively says neither prerequisite is ever produced **anywhere**, so a transaction can never happen.

The later card says the request-triggering piece isn't connected in **most worlds**.

“Most worlds” implies it may be connected somewhere, while “never anywhere” says the opposite.

Use one consistent statement.

Also, this sentence is awkward given the status:

> “The system exists and runs its check every moment…”

A Built/not-active capability that runs every moment isn't exactly inactive. More precise:

> “The transaction logic exists, but the states required to start a transaction are never produced in current simulations, so no transaction occurs.”

That explains the limitation without status ambiguity.

---

## Tone problems

The document is mostly matter-of-fact, but it regularly slips into evaluative language:

* “one of the **most fully developed** parts”
* “**smart enough** to leave allies out”
* “**genuinely well-designed** emotional system”
* “Live and **rich**”
* “one of the **richest systems found**”
* “the **clearest example**”
* “Live, **well-built**”
* “the **single largest**, most central… **by a wide margin**”

Those aren't necessarily marketing claims, but they sound like a reviewer praising the implementation rather than a document describing capabilities.

I would remove nearly all of them.

For example:

> “Area attacks exclude allied characters from their affected targets.”

is stronger than:

> “Area attacks are smart enough to leave allies out of the blast.”

And:

> “This decision system turns goals, group needs, and current beliefs into concrete actions.”

is much more useful than:

> “The single largest, most central piece… by a wide margin.”

---

## **Big-Picture Decision Making** is the weakest card

This deserves separate attention.

The entire substantive claim is basically:

> this is the largest decision-making logic and converts goals, group needs and beliefs into decisions.

That does not tell a stakeholder what the capability **does differently**.

It's also one of the least self-verifiable claims on the page: a stakeholder cannot assess “single largest” or “by a wide margin” from anything presented here.

I'd rewrite the card around behavior:

> Characters combine their current goals, immediate needs, group obligations, known information, and current situation to decide which objective to pursue next. This is the main decision layer connecting what a character knows and wants to what they actually do.

Then add 1–2 concrete decision examples if available.

That would make it a real capability card instead of an implementation-size observation.

---

## Section balance

The current balance is approximately:

| Section                         |  Cards |
| ------------------------------- | -----: |
| What Characters Do              |      9 |
| Who Each Character Is           |     11 |
| Wounds, Scars & Lasting Change  |  **2** |
| How Characters Think & Remember | **17** |

This is noticeably lopsided.

The biggest problem isn't simply that Section 3 is short. It's that its current description says:

> “How injury and temporary conditions leave their mark…”

Yet one of its only two cards is explicitly about **temporary conditions**, which by definition aren't “lasting change.”

Meanwhile genuine lasting-change material is sitting in Section 2:

* Aging
* Leveling
* Transformation
* possibly mastery/progression

So the information architecture overlaps.

### I would choose one of two fixes.

**Option A — best in my view:** rename Section 3 to:

**Injury & Physical Conditions**

Keep Wounds/Scars and Temporary Conditions there. Two cards is acceptable because the section now makes no promise of covering every form of lasting character change.

**Option B:** make it genuinely about:

**How Characters Change Over Time**

Then move some material from Identity:

* Wounds & Scars
* Aging & Old-Age Death
* Leveling
* Transformation
* possibly Mastery

That would also reduce the overloaded Identity section.

I prefer **Option B** if the four-part document architecture matters.

---

## One scope leak I'd clean up

**Occupation & Social Role** finishes by saying occupation:

> “factors directly into how armed conflicts between factions play out.”

Your scope explicitly stops at the character layer.

It's fine to explain that faction events influence characters, but this sentence starts describing a wider-system outcome.

I'd keep it character-centric:

> “Occupation also changes how a character responds when their faction becomes involved in a larger conflict.”

Likewise, references to region-level population changes in **Genetic Variation** are useful as limitations, but keep them framed only as an explanation for why reproduction does not happen at individual-character level.

---

# What is already working well

There is quite a lot worth preserving.

The document is unusually good at plainly saying **“this exists but does nothing today”** rather than quietly counting it as a delivered capability. Cards such as Genetic Variation, Sizing Up a Fight, Emotions, information seeking, and failure-learning generally make that distinction clear.

The use of concrete thresholds is also mostly effective: 5% interruption damage, 25% wound threshold, 90/95 hunger/sleep thresholds, relationship ranges, three rival-causing incidents, 40/70 mental exhaustion thresholds, transformation levels, etc. That gives the page much more credibility than vague statements such as “characters respond dynamically.”

And the card titles are generally strong. A stakeholder can skim the page and understand the intended coverage without knowing system architecture.

## Final judgment

**Not quite ready to hand to a non-developer stakeholder as-is.**

I wouldn't call this a content rewrite problem. It's primarily a **classification and precision pass**.

The blockers I'd require before publishing are:

1. resolve **deadline urgency** contradiction;
2. resolve **fear vs inactive emotions**;
3. clarify **Hero permanent death**;
4. split the worst mixed-status cards;
5. fix **Built / Half-built / Partially-live / Not-yet-built** status ambiguity;
6. clarify the two information-seeking cards;
7. fix **identical progression vs spendable stat points**;
8. define **“moment”**;
9. give the missing critical numbers or remove claims of precision;
10. replace the evaluative “rich / largest / well-designed / smart enough” language.

After those, I think the document becomes a **strong stakeholder-facing capability inventory**. The underlying pattern—*what works, what limitation remains, and what genuinely doesn't exist*—is exactly the right one; it just needs to be applied more consistently.
