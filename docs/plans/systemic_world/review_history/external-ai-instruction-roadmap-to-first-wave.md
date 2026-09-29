---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated review/instruction record for the systemic-world roadmap, copied from the local working file `external-ai-instruction-roadmap-to-first-wave.md` on 2026-09-27. An input to the planning work, not current status.

# External AI review — instruction for bridging the roadmaps to the first delivery wave

The following is an **external AI review and direction** based on documents transferred into another conversation. Verify every status claim against the current repository and its evidence before editing any document.

## Context and authority boundaries

Read the latest `docs/plans/systemic_world_roadmap.md`, `docs/world_rules/roadmap.md`, `docs/plans/simulation_semantic_control_plane/roadmap.md` and its `rollout_plan.md`, the current mechanism registry and mapping data, and the relevant foundational synthesis. The copy of the Semantic Control Plane roadmap supplied to the external reviewer marks M2 shipped, M3 as a continuing ingestion stream, and M4 done on 2026-09-24, while its opening status still says no milestone has started. Check the repository's current state and correct stale status text if you touch that document. Do not assume that the whole Catalog has been mapped: M0–M4 demonstrate the mapping approach, whereas M3/Stage D continue as tickets touch relevant domains.

Keep the three authorities distinct. The World Rule Catalog specifies world semantics. The Semantic Control Plane records Rule-to-Mechanism relationships, classifications, and evidence. The systemic world roadmap identifies capabilities still needed for the engine to realize, integrate, and deliver a coherent world experience. Mapping informs decisions and verification; completion of all 172 Rules is not a gate, and mapping coverage does not dictate product priority.

## Requested work

### 1. Make the two remaining small corrections to the proposed systemic roadmap

- In §3.1, state the semantic obligation already supported within the investigated scope: every persistent fact has a canonical authority, and a world effect must not commit from stale assumptions without a declared resolution rule. What remains open is how to verify and enforce that obligation across consequential domain boundaries, not whether the obligation exists. Do not impose one universal `revalidate()` API or a universal single-writer implementation shape.
- In the Owner Decision List, running the feasibility gate on lineage first should be a **recommended default for the local investigation**, rather than an owner decision unless a genuine tradeoff needs owner judgment. Final proof selection remains OPEN until the gate produces evidence. Preserve genuinely open semantic questions, especially the intended meaning, provenance, and scope of `public_reputation`.

### 2. Produce a short decision bridge instead of restating both roadmaps

Create a `PROPOSED / FOR REVIEW` document in an appropriate location under `docs/plans/`, or add a compact section to the systemic roadmap if that avoids duplication. Answer: **Given the existing Rules, registry, and runtime evidence, which first wave best advances both causal world integrity and a player-observable consequence?**

For each of the systemic roadmap's six capability areas, provide a compact table entry with related Rules/domains (Rule IDs only when supported by sources), current mechanisms and mapping evidence, consequential causal or integration gaps, missing evidence, and potential for a player-facing proof. Keep at least three levels separate: `semantic target` (what the Rules specify), `realization/integration` (what the engine does), and `player observation` (which legitimate traces a player may encounter). Use Control Plane classifications where appropriate. Do not turn `UNKNOWN` into `MISSING` or infer runtime correctness from mapping coverage. Where mapping is incomplete, record `UNKNOWN` and inspect only the Rules and mechanisms needed for the candidates under consideration; do not initiate a full-Catalog sweep.

### 3. Run the candidate-trajectory feasibility gate

Lineage leads on mechanism-level evidence, but **has not been chosen as the first product proof**. Check it with a real seeded run, or identify a concrete blocker if the environment cannot run one. Answer each of the five questions in §5 separately:

1. Can a consequential sequence actually emerge from authoritative state and history, without inventing events or causes for the demonstration?
2. What traces could a player plausibly encounter through an explicitly assumed minimal gameplay lens, and what could legitimately remain unknown?
3. Can an initial presentation preserve identity, chronology, and causal continuity for the same family or subject over the relevant period?
4. Would the proof require only projection and integration, or does the run reveal a missing simulation or evidence-production edge?
5. How does its feasibility and experiential clarity compare with at least one other candidate trajectory?

Choose a comparison candidate with a genuinely different domain or causal path, grounded in current evidence. Do not treat economy/wealth as ready if its conversion edges remain `MISSING`; it may still serve as a comparison that exposes the additional simulation work required. Apply the same standard to the other candidate: identify its causal sequence, encounterable traces, dependencies, and evidence limits. If execution is impossible, report a specific `BLOCKED` or `UNKNOWN` result and the condition that would resolve it; do not promote an unrun scenario to a proven product proof.

### 4. Recommend the first wave at the architecture and product level

Present one or two ordered options. For each, identify the capability and cross-domain boundary to strengthen, the trajectory proof, supporting Rule and registry evidence, prerequisites, work that can proceed in parallel, finite exit evidence, and material costs or risks still `UNKNOWN`. A wave may include both causal/authority hardening at consequential mutation boundaries and a player-facing proof. Do not force them into a single module or a fixed sequence unless a dependency is evidenced.

An experiential proof must follow world truth → legitimate evidence → situated encounter → player inference. Evaluate the world-side causal trace separately from the player's ability to form an intelligible hypothesis. A mistaken hypothesis reasonably supported by available clues is acceptable. A scenario that stops at differentiated reaction is a reaction proof only. A claim of changed life trajectory requires a later opportunity or decision and a durable outcome. Do not expose hidden world truth through the UI merely to make a proof easy to narrate.

## Deliverables and review discipline

Return (a) the document diff or PR, (b) the decision-bridge table, (c) the feasibility-gate results and candidate comparison, (d) the recommended wave with finite acceptance evidence, and (e) any decisions that genuinely require the owner. Label conclusions as verified current, inherited evidence requiring recheck, proposal, or `UNKNOWN`. Cite Rule IDs, mechanisms, and tickets only after checking their sources. Bound the authority review to named consequential mutation paths; do not claim that the entire engine has no recurrence of a class of defect.

This is **investigation and high-level design**. Do not implement gameplay tickets, edit the World Rule Catalog, freeze a gameplay lens or renderer, design a universal reputation/power/action ontology, or make full registry coverage a prerequisite for progress. If repository evidence contradicts this external AI review, prefer the repository evidence, explain the discrepancy, and revise the recommendation.
