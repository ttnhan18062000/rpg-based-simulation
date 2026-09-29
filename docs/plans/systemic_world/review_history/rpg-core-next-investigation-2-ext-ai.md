---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated review/instruction record for the systemic-world roadmap, copied from the local working file `rpg-core-next-investigation-2-ext-ai.md` on 2026-09-27. An input to the planning work, not current status.

# Instruction for local repo-aware agent — Entity Action, Recognition, and roadmap integration

## Context and purpose

The World Rule Catalog is a frozen target-semantics baseline. Pass 1 found a compositional decision pipeline and history-conditioned choices. Pass 2 found meaningful lived history but a weak general path from an individual's history to other subjects' reactions and changed opportunities. The Recognition/Standing synthesis then verified three additional facts:

- `ReputationUpdateService.process_witnessed_event()` is called without an observer or perception gate and updates subject-owned reputation; its name does not establish witnessed propagation.
- `PublicReputationProfile` has no observer dimension; consumers read a shared value.
- `InformationProvider → KnowledgeModelService` is a live, per-entity, opacity-respecting knowledge path, but the synthesis found no entity-history/reputation content flowing through it.

The synthesis proposes a directed `(observer, subject) → standing` record as the shared primitive behind several gaps. **Treat this as an important hypothesis, not an approved architectural decision.** In particular, the existence of a generic information pipeline does not prove that a particular event creates observable evidence, reaches another subject, changes its belief, or should create durable standing. Wealth-to-protection and other power-conversion edges may not depend on standing at all.

The project's next broad roadmap decision needs an evidence-backed view of the whole loop:

```text
world state → perceived opportunity/trigger → decision → attempted action
→ validation/resolution → authoritative consequence → observable evidence
→ information/belief/standing where appropriate → reaction
→ changed opportunity → later decision and life trajectory
```

Your task is an **investigation and roadmap proposal**, not an implementation request. Use current repository truth for code claims and frozen Rules for target semantics. Do not make existing code the ceiling of the final world design.

## Working rules

1. Read the relevant current World Rules, architecture documents, contracts, scenario records, and production code. Identify the current commit/revision and exact paths. Explicitly mark active, archived, stale, and unknown sources. Mechanism Registry absence alone does not prove implementation absence.
2. Separate every conclusion into `TARGET SEMANTIC NEED`, `PROVEN CURRENT`, and `EXPANSION SPACE`. Also label recommendations `PROPOSED`; do not silently promote them into `DECIDED`.
3. Match evidence to claim strength: a symbol proves existence; call tracing proves reachability; runtime evidence proves firing; a later-consumer scenario proves behavioral consequence; Rule comparison tests semantic conformance. Record `UNKNOWN` where evidence stops.
4. Trace the **first failed or unproven causal edge** for each scenario. Distinguish absent behavior from an unaudited path, a feature flag that is off, or a path that fires without meaningful downstream consumption.
5. Do not edit the World Rule Catalog or implementation in this task. If you discover a possible Rule omission, state the exact existing Rules examined, the minimal counterexample, and whether it is ambiguity or a genuinely new semantic need. Route it through the established post-freeze review policy.
6. Do not decide on a universal Action system, closed action enum, universal reputation score, or universal power-conversion framework before examining the traces. Preserve domain ownership of world facts.

## Part A — Action and Affordance investigation

### A1. Inventory the live concepts

Find active definitions and producers/consumers for concepts named or functioning as `Opportunity`, `Affordance`, `Goal`, `Decision Candidate`, `Intent`, `Command`, `Action`, `Request`, `Proposal`, `Effect`, `Result`, `Event`, and `History`. Classify each as world semantic, AI decision state, engine interface, domain mechanism, gameplay/UI concept, or archived design. Similar names do not establish identical semantics.

Pay particular attention to the join between the opportunity pipeline (`ResourceOpportunityProvider`, `ServiceOpportunityProvider`, `PerceptionGate`, `MotivationPressureResolver`, `RequirementsFilter`), goal scoring/selection, domain execution, `WorkerPool` proposals if live, and authoritative apply. Draw the actual production call/data path with file symbols and evidence levels. If there are multiple independent paths, show them rather than forcing one pipeline.

### A2. Trace contrasting action families

Trace **three live, contrasting families** at minimum:

- Combat, as a contested action with target, risk, injury/death, and history.
- Harvest/Gather, as a resource transformation with reach, depletion, inventory, and cost.
- One genuine social/economic action with a confirmed production path, preferably trade, contract, or quest reward.

Add Move/Travel or Loot/Take only if a clear active path exists and it materially tests a different boundary. A Rule or design document about loot does not by itself prove a live loot action. If the selected social/economic path is too incomplete, name the limitation and use another live path.

For each family, follow an actual event from trigger/candidate to later consequence where possible. Compare:

| Dimension | Questions to resolve |
| --- | --- |
| Origin and actor | Who initiates it: NPC decision, player command, organization, script, or world process? Does origin alter the world's rules? |
| Opportunity and decision | Who presents possibilities? What is perceived, filtered, scored, and selected? |
| Intent and target | Is a choice represented separately from an attempted action? What can be targeted? |
| Validation | Where are reach, access, authority, capability, resources, and current target state checked? Are stale candidates revalidated at execution? |
| Time and cost | When are time, resources, and risks charged? What happens on rejection, failure, partial success, interruption, and retry? |
| Resolution | What can fail after a valid attempt? How are simultaneous/conflicting actions resolved? |
| State authority | Which owner commits each changed fact? How are cross-domain effects coordinated? |
| Consequence | What persistent state changes, and what later system consumes it? |
| Observation | What event/evidence remains, who can perceive or learn it, and how does it become history or belief? |

Distinguish `invalid request rejected before an in-world attempt` from `valid attempt that fails in-world` where relevant. Do not impose a single transaction or outcome schema if the domains demonstrably need different semantics. Report whether the existing Rule families already cover the world meaning while execution contracts remain inconsistent.

### A3. Architectural assessment

After tracing, compare these possible outcomes without presupposing a winner:

1. Existing Rules and domain mechanisms are sufficient; only local wiring/contract repairs are needed.
2. A **small engine-level attempt/resolution contract** would remove proven duplication while domain actions retain their semantics.
3. A separate affordance/action semantic layer is justified by a real cross-domain invariant.
4. One or more existing World Rules are ambiguous or a genuine post-freeze semantic gap is demonstrated.
5. No shared abstraction should be added yet.

For any shared contract you propose, state its **minimum invariant**, what it deliberately leaves to domain owners, the concrete duplicated behavior it fixes, and at least one case where it must not be applied. Consider whether deliberate entity actions generalize to reflexes, coercion, organizational decisions, and environmental processes; mark that boundary open if the traces do not settle it.

## Part B — Test the Recognition/Standing synthesis

Use a scenario that distinguishes **knowledge, interpretation, standing, and reaction**, rather than merely proving that reputation can affect a price. Suggested shape:

> An ordinary hunter completes a deed. Shopkeeper A witnesses or reliably learns it; shopkeeper B does not, or hears a conflicting account. Later both evaluate the hunter for trade or a contract. A guild may hold a separate institutional view. Their treatment should be explained by what each knows and by its own interests or rules.

Adapt the details to actual production paths and existing Rule scenarios. An existing `shop.py` discount is a useful consumer, but a direct read of global `public_reputation` is **not** proof that A learned the deed. If no end-to-end scenario can currently run, give a code-traced path and mark each unproven link. Do not fabricate a runtime result.

Trace these separate edges:

1. Objective event/history: what occurred and whose authoritative state records it?
2. Recordable evidence: what could another subject encounter, including witnesses or records?
3. Propagation: through which actual producer/provider does information travel, with what reach and opacity?
4. Observer/institution knowledge or belief: what does A know, what does B know, and could either be mistaken?
5. Interpretation and standing: is a durable observer-relative record **causally required** for this scenario, or can the decision consume belief and local policy directly? When would an institution need its own durable view, and who can update it?
6. Reaction: which decision point consumes which observer-owned information? What changes for A and B?
7. Future opportunity and trajectory: does the subject encounter a different offer/access condition, and does that alter a later choice?

Evaluate the proposed `(observer, subject) → standing` representation against at least two contrasting cases: a one-off witness reaction and a durable institutional judgment. Specify the semantic owner and provenance/update authority only if evidence and Rules support them. Consider forgetting/decay, conflicting reports, and private versus public knowledge at the level needed to expose correctness; do not turn this into a giant schema design.

Recheck the synthesis's claim that all five Pass-2 gaps are downstream of standing. Classify each as `REQUIRES STANDING`, `MAY CONSUME STANDING`, `INDEPENDENT CAUSAL EDGE`, or `UNKNOWN`, with a short reason. In particular, test notability/naming, gossip, institutional treatment, opportunity generation, and wealth/reputation/office conversion separately. A global aggregate over private standing must not automatically become public knowledge. A conversion may itself create persistent obligations, contracts, office, or access rather than only a derived view.

End Part B with a calibrated verdict: what the repo proves about `public_reputation` and `KnowledgeModelService`; whether directed standing is necessary, useful, or still unproven for particular scenarios; the first failed/unproven edge in each trace; and whether any Catalog clarification is genuinely needed.

## Part C — Propose a broader roadmap revision

Locate the **current canonical RPG-core roadmap** and its owner/status; do not confuse it with the separate Live Map/render-art roadmap or an archived brainstorm. If the roadmap location/authority is ambiguous, report candidates and produce a standalone proposal rather than modifying one arbitrarily.

Produce a **roadmap proposal**, not a list of five new reputation systems or a mandatory universal Action framework. Organize around causal capabilities that close the entity-world loop:

1. Entities discover or receive meaningful, situated opportunities.
2. Decisions turn into valid attempts and domain-owned world changes.
3. Consequences persist as state/history and can leave evidence.
4. Information reaches specific observers or institutions without omniscient injection.
5. Their knowledge, interpretation, and rules change treatment where appropriate.
6. Treatment changes future opportunities and later trajectories.

For each proposed milestone/slice, provide:

- The player-independent **world capability** it proves and why it matters.
- A concrete seeded scenario with at least two different possible causal outcomes; avoid merely measuring event count or activity.
- The earliest current failed/unproven edge and the evidence supporting that classification.
- Existing Rules that define target behavior; mark any proposed clarification separately.
- Mechanism candidates using existing change vocabulary (`INTRODUCE`, `EXTEND`, `WIRE`, `TUNE`, `SPLIT`, `MERGE`, `RETIRE`, `INTERPOSE`) without prematurely fixing their design.
- Dependencies, sequencing, and what can proceed independently. Keep Semantic Control Plane M3 as ongoing/non-blocking ingestion.
- Verification level needed to claim success: source trace, scenario runtime, later behavior, Rule conformance, or distribution/corpus evidence.
- Exit criteria, unresolved choices, and explicitly deferred scope.

Choose one **thin end-to-end proof of changed life trajectory** that an ordinary first-class entity can undergo through real history, world reaction, changed opportunity, and later action. Also show a countercase where an observer lacks or misinterprets the information and responds differently. The slice should test causal coherence, not guarantee heroic success or world equilibrium.

Distinguish milestones needed for the first demonstrable loop from future expansion across action families, professions, institutions, politics, magic, and power conversion. Do not turn narrative archetypes, epithets, or biography output into authoritative simulation state. A life chronicle may be a read-only validation projection over actual causal events.

## Required outputs

1. **Investigation report:** exact repo revision, source/Rule references, concept inventory, 3+ action traces, recognition contrast trace, evidence level for each causal edge, first failed/unproven edges, and correction of any earlier Pass-1/Pass-2/synthesis claims that evidence no longer supports.
2. **Architecture decision table:** options for Action and Recognition, supporting evidence, counterexamples, what remains `UNKNOWN`, and recommendation with confidence level. Do not silently mark a recommendation as approved.
3. **Standalone roadmap revision proposal:** proposed slices, dependency order, scenarios, acceptance/verification criteria, and how findings enter the Semantic Control Plane. Identify the existing roadmap section(s) that would change and supply suggested replacement/addition text or a reviewable diff, but **do not overwrite canonical roadmap files in this investigation**.
4. **Decision requests for the owner:** only choices that evidence cannot settle; give options and consequences. Do not ask the owner to decide implementation details that can be resolved locally.

Stop when the evidence supports a reviewable proposal. Do not implement systems, modify frozen Rules, or claim runtime behavior from source inspection alone. Report `UNKNOWN` explicitly where a full trace is unavailable.
