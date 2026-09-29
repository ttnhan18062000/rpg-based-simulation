---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated review/instruction record for the systemic-world roadmap, copied from the local working file `rpg-core-next-investigation-3-ext-ai.md` on 2026-09-27. An input to the planning work, not current status.

# Follow-up instruction — Foundational Entity–World Architecture and RPG Core Roadmap

## Role and objective

You are the **local repository-aware investigator**. Use your access to the repository, World Rule Catalog, existing roadmaps, and the completed investigation reports to establish implementation facts and correct any stale claims. The external reviewer will concentrate on world semantics, architectural boundaries, and roadmap direction. Please keep those responsibilities distinct.

Read the completed Part A (Action/Affordance), Part B (Recognition/Standing), and Part C (roadmap proposal), alongside Pass 1, Pass 2, and the prior Recognition synthesis. Part C is a useful draft, **not an approved roadmap**. In particular, do not assume that its proposed slices, dependencies, action representation, witness/rumor wiring, standing record, or opportunity filter extension have been chosen.

Your assignment is to produce a **high-level foundational synthesis and revised roadmap proposal** for a persistent systemic fantasy RPG world. The aim is a core simulation in which ordinary first-class subjects can accumulate history, act, change, be recognized where information reaches others, encounter different future possibilities, and develop distinct lives. The core remains neutral to the current observer-style gameplay lens.

Do not implement features, write low-level tickets, or modify canonical World Rules in this assignment. Do not spend the main report on line-by-line code paths or one shopkeeper/quest/harvest example. Keep detailed traces in an evidence appendix or references to Parts A and B. The primary report should answer **what the world must mean, which architectural responsibilities exist, how they compose, and what the roadmap must prove**.

## A. Reassess the complete causal loop as a foundation

Use this as a question to test, rather than a mandatory engine pipeline:

```text
world state and ongoing processes
→ what a subject can perceive, know, believe, or be offered
→ available possibilities and motivations
→ decision or other initiating cause
→ attempt or world process
→ resolution and authoritative world change
→ persistent consequence and potential evidence
→ information held by other subjects/institutions
→ their interpretation and reaction
→ changed future possibilities
→ further world history
```

Identify the **minimal semantic distinctions** that must hold across domains. In particular, examine:

- world truth versus observation, information, belief, memory, and socially recognized interpretation;
- affordance or opportunity versus desire/goal, selected intent, valid attempt, resolution, and consequence;
- an action by an agent versus a world process, involuntary effect, institutional decision, or environmental event;
- objective capability/access versus an actor's belief that an action is possible;
- physical possession versus legitimate ownership and legal/social interpretation;
- private attitude, durable relationship, institutional standing, public claim, and aggregate narrative notability;
- actual causal power/resources versus concrete paths by which one advantage can be converted into another.

For each distinction, state its semantic home, authoritative state owner **if already established**, participating domains, and whether it is causal state, a derived view, or a narrative/analytical projection. Do not assign a new universal owner merely because the concept crosses several domains. Mark unresolved ownership honestly.

Ask whether the current World Rules already compose to supply these semantics. Separate a genuine missing world law from an implementation contract gap, a missing mechanism, absent wiring, weak evidence, or an unneeded abstraction. Preserve the Catalog freeze and the evidence-first post-freeze policy.

## B. Assess architecture boundaries without presupposing a framework

We need a coherent explanation of how autonomous subjects and other processes can change a persistent world while respecting domain-owned truth. Consider these boundaries at a conceptual level:

1. **Agency and opportunity:** how possibilities become available to a particular subject, and how incomplete or mistaken knowledge affects its decisions.
2. **Attempt and resolution:** what invariants should hold between intention, validation, execution, cost, failure, and committed effects; which parts can be shared and which must remain domain-specific.
3. **State authority and causal history:** who may mutate what, how cross-domain consequences remain coherent, and which outcomes need durable provenance.
4. **Observation and interpretation:** how an event becomes knowable to particular people or institutions, and when their beliefs, relationships, or policies affect treatment.
5. **Feedback into future opportunity:** how changed body, capability, resources, relationships, roles, location, reputation, or institutional position alter later possibilities through concrete causal edges.

Determine whether a small common engine contract is justified for attempts and effects, or whether existing domain contracts suffice. State the **minimum shared invariant** and the cases it must leave open; do not define a giant `Action` ontology or require every world process to masquerade as an agent action. Likewise assess directed standing as a possible representation for some observer-relative judgments, not as a universal prerequisite for every kind of recognition or power conversion.

Make the design robust to more than a hunter and shopkeeper. Stress it conceptually with a few genuinely different trajectories: an ordinary craftsperson becoming economically influential, a displaced family developing a feud, a guild changing its treatment of a member, a settlement reacting to danger, or a political office exercising authority. Choose examples that reveal different causal owners. These are **design tests**, not instructions to implement every feature now.

## C. Correct the Part C roadmap at the right level

Part C organizes work around recognition but does not yet convincingly represent the full Action-to-Consequence foundation. Its Slice 1 describes different treatment, while the full changed-life-trajectory proof also requires changed opportunities and later decisions. Revisit the roadmap structure accordingly.

Propose a small number of **capability areas or phases**, not a premature list of implementation tickets. A possible shape to evaluate is:

- **Foundational causal/authority contract:** world facts have owners; attempts and processes produce coherent domain effects and traceable consequences.
- **Situated agency and action:** subjects encounter partial opportunities, decide, attempt, and experience success, failure, cost, and persistence across contrasting domains.
- **Information and world reaction:** specific observers/institutions can learn, mislearn, remember, interpret, and respond without omniscient knowledge.
- **Development and opportunity feedback:** accumulated personal and collective histories alter access, risk, resources, relationships, and future trajectories.
- **Systemic breadth and validation:** the same foundations compose across non-combat professions, institutions, places, politics, economy, lineage, magic, and other domain families as justified by causal value.

This is a candidate grouping, **not a required five-phase architecture**. Improve or replace it if Part A/B evidence and existing canonical plans imply a stronger structure.

For each proposed capability area, define:

- the world-level outcome it enables;
- the invariant or design boundary it establishes;
- what is already semantically designed, currently realized, and still unknown;
- the minimum meaningful cross-domain demonstration and evidence needed to claim the capability works;
- dependencies that are truly causal, as opposed to convenient implementation order;
- what can be explored independently and what remains open for later design;
- how its findings should enter the Semantic Control Plane, with M3 remaining an ongoing, non-blocking ingestion stream.

Show how these areas connect to the frozen World Rule Catalog and the existing roadmap landscape. Explain where a new roadmap or revision should live and how it relates to the closed `rpg_design_roadmap`, the Semantic Control Plane roadmap, and engine-infrastructure planning. Avoid stuffing a new capability program into an old completed milestone series solely to reuse its numbering.

Propose **one eventual end-to-end validation trajectory** for an ordinary entity that links real action, persistent consequence, differentiated world reaction, altered opportunity, and later action. State what smaller proofs can precede it. Make clear that one scenario validates a causal chain; it does not define the final ontology or imply universal completion across all domains.

## D. Calibrate conclusions and decisions

Review Parts A/B/C for claims that go beyond their evidence. In particular, reconsider these candidate claims without assuming they are false or true:

- the first general break is always a standing record rather than event evidence, propagation, belief, or consumption;
- an existing generic rumor function is sufficient for direct witnessing and secondhand information;
- individual relationship history and institution-specific standing should share one record shape;
- a fifth `RequirementsFilter` category is the correct architectural place for reputation-sensitive opportunity;
- a global reputation view can safely be derived by aggregating private observer attitudes;
- wealth, office, and reputation conversion share one prerequisite;
- a source-level or unit-level check proves a world-level causal behavior;
- the first recognition slice alone proves a changed life trajectory.

Return corrected statuses as `DECIDED`, `PROVEN CURRENT`, `PROPOSED`, `OPEN/UNKNOWN`, or `SUPERSEDED`. For claims about runtime behavior, give the actual verification level. If a claim cannot be resolved without more work, keep it open and explain its impact on roadmap sequencing.

Owner decisions should be limited to real choices about **target world semantics, architectural commitment, or program scope**. Questions such as which existing class to extend, whether to retire an unused type, and exact field layout usually belong to local engineering investigation after the semantic boundary is set. Present a recommendation and tradeoffs for any genuine owner-level choice; do not make the owner choose among uninvestigated code options.

## Deliverables

1. **Foundational architecture synthesis:** a concise model of the entity–world causal loop; semantic boundaries; ownership and participation map; current strengths, first unproven edges, and alternatives. Keep detailed code evidence in a compact appendix with source locations and links to Parts A/B.
2. **Revised high-level roadmap proposal:** capability areas, true dependencies, proof levels, a staged end-to-end trajectory, relationship to existing plans, and proposed permanent document home. Mark every recommendation as proposed until accepted.
3. **Delta from Part C:** what should be retained, corrected, moved to later ticket design, or removed; explicitly address the mismatches above.
4. **Owner decision memo:** only the few semantic/program choices evidence cannot settle, with a recommended default and consequences. `UNKNOWN` is a legitimate outcome.

Produce reviewable standalone documents or a clearly separated report. **Do not edit the frozen Catalog, existing canonical roadmaps, registry states, or production code in this pass.** The next step after review is to accept or revise the broad design, then have local agents derive detailed milestone plans and implementation tickets from it.
