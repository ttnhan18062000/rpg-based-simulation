---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated review/instruction record for the systemic-world roadmap, copied from the local working file `external-ai-instruction-finalize-systemic-roadmap-and-first-wave-plan.md` on 2026-09-27. An input to the planning work, not current status.

# External AI instruction: finalize the systemic world roadmap and prepare the first delivery-wave plan

This instruction is an **external AI design review and work request**. I do not have the live repository or your current PR diff. Treat the repository, frozen World Rule Catalog, current registry and mapping files, runtime behavior, and existing project conventions as authoritative evidence. If any statement below conflicts with current evidence, record the discrepancy and correct the recommendation rather than conforming the evidence to this instruction.

The owner wants a roadmap for the **whole simulation engine**, followed by a concrete first-wave milestone plan. The engine simulates a persistent world independently of the player's attention or a chosen gameplay lens. Ordinary subjects can acquire significance through causal history. The player should be able to discover the world's logic through situated evidence and ordinary inference, including plausible mistaken interpretations. The product should not have to explain every mechanism or expose omniscient truth.

Your role is to perform the repository-aware investigation and draft reviewable documents. My role as external reviewer is to preserve the cross-domain architecture, evidence discipline, and product direction. This request is for **feasibility investigation, architecture/roadmap finalization, and planning**, not production feature implementation.

## 0. Recover the current state before making conclusions

Read the latest version of:

- `docs/plans/systemic_world_roadmap.md`, including the changes made after the third external review;
- `docs/world_rules/roadmap.md` and the frozen Rules relevant to the candidate trajectories and audited boundaries;
- `docs/plans/simulation_semantic_control_plane/roadmap.md`, `rollout_plan.md`, the actual Rule↔Mechanism mappings, mechanism registry, classifications, validators, and drift reporting;
- the foundational synthesis and the investigation Parts A/B/C that the systemic roadmap cites;
- repository instructions, ticket conventions, and existing scenario/corpus evaluation practices.

Verify whether the roadmap now accurately distinguishes the two passing death-to-heir tests from an actual five-question feasibility result. Resolve any remaining stale cross-references or conflicting status claims with a small editorial diff. Do not re-open a broad wording-review cycle once the document is internally consistent.

Use this authority separation throughout:

1. **World Rule Catalog**: target world semantics. The Catalog is frozen; reopen only on genuine semantic evidence, under its own governance.
2. **Semantic Control Plane**: formal mappings and evidence about Rule realization; M3/Stage D are ongoing, not a full-Catalog prerequisite.
3. **Mechanism registry and production code**: declared and actual implementation paths. A registry entry alone is not proof that a causal path fires in a real run.
4. **Runtime and scenario evidence**: actual reachability, state changes, and causal continuity, within the tested scenario's limits.
5. **Player observation**: legitimate clues exposed from a specified viewpoint and the inferences a player can reasonably make. This is not implied by any of the earlier layers.

Do not flatten those five into a single `implemented` status. Explicitly distinguish `UNKNOWN` (not established) from `MISSING` (investigated and confirmed absent), and distinguish observed single-scenario reachability from distributional or longitudinal behavior.

## 1. Make the evidence workflow efficient, using existing registry infrastructure

The owner wants the registry and Semantic Control Plane to reduce manual checking, hallucinated links, and management overhead. Use existing tools before proposing new infrastructure. Record the actual commands or query steps that answer the following practical questions for the candidate paths and audit boundaries:

- Given a Rule or domain capability, which formal mapping, mechanism, classification, and evidence currently exist?
- Given a mechanism or changed production path, which mapped Rules, downstream causal relationships, and scenario checks may need revalidation?
- What is formally mapped, what is supported only by Catalog prose or investigation notes, and what has no evidence yet?
- Which paths or evidence references have drifted since their last verification?

If present tooling cannot answer a question, identify the *specific* missing query or validation affordance and show a concrete example. Propose the smallest incremental improvement in the existing Control Plane, not a second registry, a universal ontology, or an early Stage-F Context Compiler. A useful output can be a reproducible query recipe or report format without implementing any new tool in this task. Do not infer `SUPPORTED` from symbol names, tests that never reach production, or an AI-generated narrative. New mapping claims require the established validation and evidence process.

Keep this work targeted to the chosen candidate trajectories and the finite authority audit. Do not sweep all 172 Rules or turn mapping completeness into a delivery gate.

## 2. Finish the lineage feasibility investigation as an investigation, not a pre-selected proof

The two re-run tests establish specific death-to-heir transitions. They do not establish a coherent long sequence, a legitimate evidence surface, or player understanding. Carry out the five-question gate in §5/§7 with an explicit evidence table: `PASS`, `PARTIAL`, `UNKNOWN`, or `BLOCKED`, with the scope and source of every answer. Avoid a single overall “gate passed” label unless all required questions have been answered at the scope being claimed.

### World-side causal investigation

Select a bounded, reproducible seeded run that can test more than one isolated transition if the existing runtime makes this feasible. The sequence need not span multiple generations just for spectacle. It must be long enough for an earlier event to alter a later world state, behavior, relationship, opportunity, or decision that is meaningful for the particular proof being claimed. State the minimum length and why it is causally sufficient. Record the seed, starting state, relevant ticks/events, stable subject identities, authoritative state changes, and provenance for each causal link. Do not write fabricated event history into the scenario to make the demonstration read well.

If existing tests cannot compose into that run, investigate whether the blocker is scenario setup, event selection, missing runtime integration, state/history recording, evidence production, or an actual simulation edge. Report the narrowest confirmed blocker. A single transition can remain a valid *vignette or mechanism check*; do not rename it a changed-life-trajectory proof.

Check that the state transitions honor their domain's authority and causality. Do not equate a passing unit or single-tick test with frequency, emergence, or temporal continuity in ordinary world runs.

### Situated observation and inference investigation

Choose a **minimal provisional observer position** for the exercise, not a permanent gameplay-lens decision. For example, specify where the observer is, when they could encounter a person, object, record, or account, and which clues are legitimately available from that position. For each proposed clue, identify its originating world event/state, evidence-production path, possible carrier, scope, chronology, and whether the observer can actually encounter it. Separate an in-world trace from a developer-only event log or omniscient state dump.

Prepare one or more small evidence packets or low-fidelity projections derived only from the real run. Show what the observer can see at an earlier and a later moment, what may legitimately remain hidden, and at least one reasonable hypothesis available from the clues. A reasonable hypothesis may be wrong. If a later clue can revise that hypothesis, record how. Include a negative check for a supposedly meaningful outcome with no discoverable trace and for a projection that leaks hidden truth.

This design check can answer technical and product feasibility questions. Do **not** mark `PLAYER-EXPERIENCED` as proven merely because an agent wrote a plausible narrative or mock projection. An actual player-observation exercise or equivalent user evidence remains a separate acceptance step; if none is run, label it pending. No renderer or full UI implementation is required for this investigation.

For gate question 4, report separately whether the *tested world transition* needs another simulation edge, whether its *evidence production* exists, and whether a *situated projection* can be built from it. “The mechanism is observed” alone cannot answer the latter two.

## 3. Compare candidate trajectories without an artificial winner

Keep economy/wealth in the comparison as a useful counterexample if its declared conversion edge remains absent. It tells us what simulation work that trajectory needs; it does not establish that lineage has the best player experience.

Look for one other **plausibly viable** candidate with a different causal shape if repository evidence supports one. Search beyond mechanism names alone, including relevant production paths, existing scenarios, and registry causal edges, but keep the search bounded. Potential areas from earlier design stress tests include a displaced family/feud, settlement facing an environmental threat, or institutional/office consequences. These are search prompts, **not** claims that the mechanisms exist or are ready. Avoid choosing a second lineage variant and calling it independent contrast. If none qualifies after a finite search, record the exact scope searched and leave comparative experiential clarity `UNKNOWN`.

Compare candidates on: real causal sequence, authority and history continuity, legitimate observer traces, later consequences, missing simulation work, integration work, and proof cost. Do not select by registry coverage, the number of passing tests, or the most dramatic story alone.

## 4. Run the bounded foundation audit in parallel

Define a finite set of consequential cross-domain mutation boundaries before checking them. Select boundaries by expected systemic impact, authoritative state ownership, and evidence of multi-path writes or stale assumptions. The regional-sovereignty defect is one precedent, not evidence that the same defect recurs everywhere. Do not limit the inquiry to literal duplicate field writers if a domain can commit a world effect from stale assumptions through another path.

For each named boundary, identify the persistent fact and canonical authority, relevant producers/consumers, attempted effect and resolution rule, existing tests or scenario evidence, and any conflicting path. Check a representative integration scenario where practical. Classify each boundary as `CONFIRMED_FINE_WITHIN_SCOPE`, `DEFECT_CONFIRMED`, or `UNKNOWN_WITH_REASON`; a repaired defect additionally needs a retest result. The audit has a finite exit condition: the named set has explicit outcomes and remaining unknowns, not “no such defect exists in the engine.”

Separate findings that warrant an immediate correction from findings that belong in a later capability wave. Record relevant Rule and mechanism links via the Control Plane's normal evidence process, without making M3 a blocking migration project. Do not modify production code under this planning instruction unless a separate existing authorization and task already covers a fix; if a severe defect appears, document and escalate it through repository practice.

## 5. Make a first-wave decision from the evidence

After the feasibility and audit work, prepare a short decision memo with one recommended option and a credible alternative. Explain whether lineage is ready to become the first *delivery candidate*, remains a feasibility exercise, or should yield to another trajectory. Say which unknowns are prerequisites and which can be investigated in parallel. Avoid saying that all future world development depends on this one proof.

The wave should serve the systemic roadmap, not only lineage. It may combine a small amount of reusable causal/authority work with a player-observation candidate. Keep domain ownership distinct: economy, lineage, institutions, environment, and recognition need not share a data shape or deployment sequence. Direct participation, uninvolved witnessing, and secondhand hearsay remain separate semantic cases. Individual relations and institutional judgments must not be silently merged; `public_reputation` must not become an omniscient shortcut.

Define the evidence ladder explicitly for the selected candidate:

- correct domain state transition;
- real cross-domain causal composition over the claimed span;
- legitimate evidence produced and encounterable from a specified viewpoint;
- reasonable player inference, including the possibility of error and later revision;
- a later decision/opportunity and durable outcome **only if** claiming a changed-life-trajectory proof.

A differentiated reaction by itself is a reaction proof. A designed projection is not automatically a player-experienced proof. Preserve both distinctions in the decision memo and milestones.

## 6. Finalize the roadmap, then draft a separate first-wave milestone plan

Update the proposed systemic roadmap to reflect verified results without turning it into a transcript of every investigation. Keep its six areas as a **capability and dependency map**, not a mandated six-module implementation order. Preserve the north star, domain diversity, cross-domain causal contracts, epistemic delivery principle, and separate levels of design/realization/verification/integration/player experience. Keep the Catalog roadmap and Semantic Control Plane roadmap independent and accurately referenced. Correct stale status text, links, tables, and owner decisions in the same pass. Leave uninvestigated domains and Rule families honestly `UNKNOWN`.

Draft a separate `PROPOSED / FOR REVIEW` first-wave plan in an appropriate `docs/plans/` location. It should contain:

1. Outcome and scope, including the explicit proof claim it aims to establish and claims it does not yet establish.
2. A small set of milestones with dependency order, owner by **domain responsibility**, and parallel paths where supported.
3. For each milestone: entry evidence, deliverable, finite exit evidence, relevant Rules/mechanisms/scenarios, and failure/blocked branch.
4. World-side and player-side acceptance criteria kept separate.
5. A bounded evidence and regression strategy using existing tests, scenario/corpus infrastructure, and targeted registry updates; no “full Catalog complete” gate.
6. Integration with the presentation programs at an **interface/contract** level only, without selecting a renderer, final gameplay lens, or full art pipeline.
7. Open decisions and when they truly become blocking. The meaning and provenance of `public_reputation` and individual-versus-institutional standing should remain visible, but they need not block a lineage wave that does not use them.
8. How verified observations from this wave will update the systemic roadmap and the ongoing Semantic Control Plane, without creating a competing source of truth.

If feasibility remains unresolved, draft a **conditional plan** with a short decision gate and explicit branches rather than inventing certainty or assigning all implementation milestones prematurely. The final roadmap should remain `PROPOSED / FOR REVIEW` until the owner explicitly approves it. Do not merge or mark it approved on the basis of this instruction.

## 7. Return a review package, not just a completion summary

Provide:

- document links and a concise diff summary;
- the five-question gate table with raw run/scenario references and remaining unknowns;
- observer/evidence provenance examples and the current limit of any player inference claim;
- the named authority boundaries and individual audit results;
- candidate comparison and first-wave decision rationale;
- the milestone plan or its conditional branches;
- a short, reproducible description of how existing registry/Control Plane tools were used, plus any specific missing query that materially slowed the work;
- only genuinely owner-level semantic or product decisions, with a recommended default, consequence of each choice, and the date/phase at which a decision is needed.

For every significant conclusion, distinguish **verified in the current repository**, **inherited evidence not rechecked**, **inference**, **proposal**, and **UNKNOWN**. Do not claim that test execution proves a player experience, that registry absence proves universal runtime absence, or that one incident establishes systemic recurrence.

The intended outcome is a reviewable whole-engine roadmap and an evidence-grounded first-wave plan. It is not a complete implementation backlog for every domain, nor a new automated governance system.
