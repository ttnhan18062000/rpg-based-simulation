---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated review/instruction record for the systemic-world roadmap, copied from the local working file `rpg-core-next-investigation-4-ext-ai.md` on 2026-09-27. An input to the planning work, not current status.

# Instruction for local agent — Finalize the simulation-engine direction and high-level roadmap

## Starting point

Read `rpg-core-foundational-synthesis-and-roadmap-revision.md`, its supporting Parts A/B/C, the frozen World Rule Catalog, the established RPG design direction, and the current roadmap landscape. The synthesis is a strong draft, but it is still `PROPOSED`. This instruction records the owner's newly clarified **product direction** and asks you to turn the architectural synthesis into a reviewable, high-level roadmap for the **whole persistent systemic fantasy RPG simulation engine**.

The Action–Recognition–Opportunity loop is a valuable cross-domain proof. **It is not the full scope of the engine.** The target world includes people, creatures, families, organizations, institutions, settlements, places, resources, environment, economy, politics, culture, magic, and other first-class subjects and processes where causally meaningful. The core simulates the world; a gameplay lens defines a player's relationship to it. Current observer-style gameplay must not become a core ontology constraint.

The owner also clarified the intended player experience:

> Players should be able to understand much of the world through ordinary observation, logic, and self-directed discovery, without being taught every rule. They may form interpretations that are wrong but reasonable given the information available to them.

Treat this as **accepted product direction**. Do not translate it into an omniscient explanation UI or a requirement that every hidden cause be revealed. The engine must sustain coherent causality; the delivered experience must expose natural, situated evidence from which people can infer, compare accounts, revise beliefs, and learn how the world works. An understandable world may still contain secrets, false reports, uncertainty, and genuinely surprising outcomes. Player error should come from plausible limited or misleading evidence, not arbitrary or inconsistent world behavior.

## Your role and scope

Use your repo access to establish source truth and identify the authoritative documents. Focus the main output on **target semantics, architecture boundaries, capability dependencies, product experience, and evidence-based delivery stages**. Keep code-level details in references or a compact evidence appendix. Do not spend the main roadmap on individual classes, fields, enum shapes, ticket IDs, or a single hunter/shopkeeper scenario.

This request authorizes documentation work: revise the standalone foundational synthesis as needed and create a proposed high-level roadmap in the repo at a sensible new home. It does **not** authorize implementation changes or silent edits to the frozen World Rule Catalog. Mark the new roadmap `PROPOSED / FOR REVIEW`; do not declare it owner-approved or supersede existing canonical plans without showing the relationship and receiving the owner's decision. Preserve existing roadmap identities and unrelated content.

## 1. Correct the foundational synthesis before using it as roadmap authority

Make these four corrections explicitly and propagate them into the new roadmap:

1. **Capability map, not a compulsory five-step pipeline.** The five areas in the current synthesis are useful, but many world trajectories do not require all of them in that order. Lineage has a working history-to-behavior loop; wealth or office can create concrete leverage without individual recognition. Present real causal dependencies **per outcome or trajectory**, and distinguish them from convenient implementation order. Some capabilities can develop concurrently.

2. **Separate state authority from attempt correctness.** A world fact has a canonical authoritative owner, but this does not imply only one code site may ever write it under that owner's control. For agent attempts, state changes must not be committed using stale assumptions without a declared resolution rule. Do not require every domain to run an identical `revalidate()` step: reservations, multistage actions, ongoing processes, conflict resolution, and environmental effects may have different legitimate contracts. Specify the shared semantic obligation and leave domain execution shape open.

3. **Narrow the claim about individual standing.** `SocialComponent.bonds/trust_history` proves a directed, causally used history of direct interpersonal interaction. It does not prove that an uninvolved witness or a recipient of hearsay can form the right kind of subject-specific belief, evaluation, and later reaction. Institutional standing remains a separate confirmed realization gap. Keep direct participation, direct witnessing, and secondhand reports distinguishable. Do not assume one storage primitive must represent all three.

4. **Bound the World Rule conclusion.** Say that the investigated cases have **not demonstrated a need for a new World Rule family**. Do not claim that no semantic gap can exist anywhere in the final engine. The Catalog remains frozen; future substantial counterexamples use the evidence-first reopening process. Deferred subjects, such as coercion and involuntary action, remain open rather than being silently covered.

Also check for second-order overreach already noticed in Part C: rumor API generality is not proof of correct witness/recipient semantics; an extra `RequirementsFilter` category is not automatically the right home for new offers; an aggregate of private attitudes is not automatically public knowledge; a differentiated reaction alone does not prove a changed life trajectory.

## 2. State the complete engine and product north star

Write a concise section that an architect, designer, and future local agent can all use. It should explain:

- The world exists and changes through agents **and** non-agent processes, even without a player watching.
- Ordinary first-class subjects can accumulate consequential history and, through circumstances, become important; significance is not a privileged starting class.
- World processes are causally coherent across domains. Magic participates in that coherence. Growth, decline, conflict, positive feedback, and instability are valid outcomes.
- Capability, wealth, status, relationships, knowledge, territory, authority, and other advantages remain distinct; conversion happens through specific causal paths.
- A gameplay lens may permit observation, indirect influence, or direct action according to future product choices. Do not freeze that choice into engine semantics now.
- Simulation value is delivered when a player can **encounter** consequential differences, recognize patterns, and form their own hypotheses about why events occurred.

Do not turn this into a promise of exhaustive detail, complete historical logging, universal player access to truth, or a guarantee that every event will be interesting. Depth means meaningful causal connectivity, not maximum variable count.

## 3. Add an epistemic and experiential delivery principle

The roadmap must distinguish these layers:

```text
world truth and causal history
→ potential evidence in the world
→ what particular characters/institutions can perceive or learn
→ their possibly mistaken beliefs and reactions
→ what the player can actually encounter through a gameplay lens
→ the player's own interpretation
```

The player is not automatically the world's omniscient debugger. A biography, event log, map, HUD, dialogue, rumor, behavior change, or institutional record is a **projection or source of evidence**, with a viewpoint and scope. Some projections may be explicitly analytical/debug surfaces, but ordinary player-facing surfaces should not silently leak hidden world truth.

Define the experiential quality bar in practical, non-UI-specific terms:

- Similar causes tend to have intelligible relationships to similar effects, subject to context, chance, and incomplete information.
- Important consequences may leave discoverable traces through behavior, material changes, witnesses, records, offers, and relationships where the world's rules support them.
- Different observers can possess different accounts; the player can reasonably infer a false explanation from a partial or unreliable account.
- New evidence can make an earlier interpretation revisable. The engine does not retroactively change causal truth to match a plot twist.
- The player can learn recurring world logic by observing multiple situations, without a mandatory tutorial for every mechanic.
- The product gives enough temporal and contextual continuity to relate an outcome to earlier events, without printing internal scores or explaining every causal edge.

Use one or two short examples involving **different domains** to show how this feels to a player. Distinguish deliberate ambiguity from opaque or arbitrary behavior. Do not prescribe a specific UI, camera, journal format, or player control scheme.

## 4. Build a roadmap for the whole simulation engine

Create a **standalone proposed roadmap**, not an M11 appended solely to reuse a closed numbering scheme. First map it to the existing RPG design roadmap, World Rule Catalog roadmap, Semantic Control Plane roadmap, engine-infrastructure roadmap, and adjacent rendering/HUD/art work. State which are authoritative for what and which remain independent. Do not overwrite their scope.

Organize the new roadmap as a **capability map with delivery waves or programs**, rather than assuming one mandatory linear five-phase sequence. Cover at least these perspectives at the appropriate level:

1. **World substrate and causal governance:** persistent identity, time, space, authoritative state, provenance, costs, resources, transformation, reach, and cross-domain consequences.
2. **Autonomous world dynamics:** life/body/ecology, environment, material/economic processes, social/lineage, institutions/politics/law, culture/belief, magic, and interaction among them. Do not imply all domains have equal implementation depth or must be finished together.
3. **Situated agency and action:** perception, knowledge, need/goal, opportunity, choice, attempt, resolution, failure, and persistence where relevant; include non-agent processes without forcing them into an Action type.
4. **History and feedback:** development, injury/loss, relationships, institutional change, information propagation, recognition, changing opportunities, and concrete conversion of advantages.
5. **Observation and player delivery:** ways for a gameplay lens to expose coherent world consequences and imperfect information so players can infer rather than be instructed; distinguish gameplay surfaces from authoritative simulation state.
6. **Evaluation and expansion:** hard correctness, causal correctness, observed reach, persistent consequence, emergent capacity, performance/scale, and distributional behavior. Keep M3 as a non-blocking ingestion stream. Evaluate across varied domain trajectories instead of relying on one benchmark scenario.

These six perspectives are a coverage checklist, **not a mandated six-module architecture**. Improve the grouping if a clearer structure follows from the existing design. Show a few meaningful dependency paths, including at least one that does **not** require social recognition. Clearly identify reusable foundation work, independent domain work, integration proofs, and later breadth work. Do not gate all future development on full completion of every Rule mapping or every domain.

For each major capability or wave, specify the player/world outcome it eventually enables, the semantic foundation it relies on, current evidence at a high level, a meaningful cross-domain proof, and what remains open. Separate `DESIGNED`, `REALIZED`, `VERIFIED`, `INTEGRATED`, and `PLAYER-EXPERIENCED` where useful. Do not collapse these into a single completion percentage.

## 5. Give a credible delivery path

The roadmap should make the path from foundation to a user-visible product concrete without pretending a single demo proves the entire engine:

- Propose one **initial product proof** in which a player can observe an ordinary subject's consequential history, encounter situated evidence, make a reasonable inference, and later see a world reaction or opportunity that follows from real state. The player's inference may be right or plausibly wrong.
- Propose a later **closed-loop proof** where changed opportunity affects a subsequent decision/action and durable outcome. Distinguish it from a reaction-only proof.
- Propose at least one **contrasting domain proof** (e.g. lineage, economy, institution, settlement/environment) so the architecture is not validated only through personal reputation.
- State which pieces are currently evidenced, which require engineering, and what runtime/scenario or player-observation evidence would justify a delivery claim.

The player-facing proof must be evaluated on what the player could reasonably understand from the available evidence, not merely on internal state transitions or a debug trace. Conversely, player misunderstanding alone is not a bug if their interpretation was plausible under the available clues and the world remains causally coherent.

## 6. Decision discipline and output

Keep engineering decisions with the local engineering team unless they change target world semantics or product scope. In particular, exact record types, class reuse, and unused symbol retirement do not need to be sent to the owner now. The institutional-standing semantic home may be recommended based on existing domain ownership, with any genuinely unresolved cross-domain authority question called out. `public_reputation` remains open until its intended meaning (publicly knowable fact, scoped claim, derived projection, or technical fallback) is established. Do not demand a premature final choice.

Deliver:

1. A revised **foundational synthesis** with the four corrections and the player-experience north star.
2. A new **proposed simulation-engine roadmap** with capability map, conditional dependencies, delivery waves/proofs, relationship to existing plans, and explicit evidence/status labels.
3. A short **change summary** explaining what changed from the prior five-phase draft and why.
4. A **small owner-decision list** containing only genuinely unresolved world-semantic or product-scope questions. Recommend defaults when reasonable; `OPEN/UNKNOWN` is acceptable.

Keep the main documents high level and readable. Cite Parts A/B and relevant World Rules for factual support; place narrow code traces in an appendix. Do not alter production code, frozen Rules, or existing canonical roadmaps in this pass. Do not call the new roadmap final or approved until the owner reviews it.
