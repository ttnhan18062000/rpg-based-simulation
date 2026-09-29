---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated review/instruction record for the systemic-world roadmap, copied from the local working file `external-ai-instruction-execute-first-systemic-world-batch.md` on 2026-09-27. An input to the planning work, not current status.

# External AI instruction — execute and self-review the first systemic-world batch

This is a **complete external AI instruction** for the next batch. The owner wants a reviewable result without a chain of small document revisions. Work through the bounded tasks below, perform an independent consistency and evidence review before reporting back, and return one consolidated review package. Follow the repository's ticket, testing, PR, and approval conventions. The owner has asked to proceed with this batch; do not treat the proposed document status as a reason to stop ordinary authorized investigation, planning, or reversible implementation work. Do not silently mark the roadmap owner-approved, merge a PR, deploy, or claim a product proof without its stated evidence.

## Intended result

Advance the persistent, gameplay-neutral simulation world on two independent fronts:

- **World correctness:** natural aging must lead to authoritative death/succession, and a bounded two-hop lineage sequence must work through ordinary ticks without staged “already past maximum age” state.
- **Situated understanding:** identify what a particular observer can legitimately encounter after a single inheritance, separate raw state from evidence and provenance, and assess whether a person given only those clues can form a reasonable hypothesis. A reasonable but mistaken inference is valid.
- **Cross-domain foundation:** resolve the three already named authority-boundary unknowns separately when their representative scenarios are executable.

The first-wave outcome does not require that every internal mechanism be visible. Hidden foundations and private events are valid. Do not reveal world truth through a UI or mock packet to make a demonstration easier. The engine's world-side correctness must not depend on an observer exercise succeeding.

The source documents are the current `docs/plans/systemic_world_roadmap.md` and `docs/plans/systemic_world_first_wave_plan.md`. The copies last reviewed externally still needed a small final consistency pass; read the current repository versions, not the attachment copies, and apply the changes below where they are still needed. The frozen World Rule Catalog remains the semantic authority. The Semantic Control Plane (SCP), mechanism registry, production code, runtime scenarios, and observer exercise carry different evidence levels; preserve those distinctions.

## Phase 0 — one consolidated documentation correction and task setup

Before implementation, correct the remaining plan inconsistencies in a single targeted pass:

1. In roadmap §4, remove the stale claim that the lineage path is “already working today, zero new capability work.” It has a real natural-aging composition defect and an unresolved observer/evidence path. Preserve the valid point that lineage does not depend on recognition propagation.
2. Remove the already-resolved “which trajectory to investigate first” item from the **Owner Decision List**. Record lineage as the working default in the delivery section, not as an owner-level semantic question.
3. Treat M4b as an optional, separately scoped **future follow-on**, rather than a first-wave milestone with no finite exit evidence. If the repository's planning convention requires keeping it in the plan, give it a finite design deliverable and finite exit evidence, and make clear it is not required for first-wave completion.
4. An observer-facing follow-on needs a **legitimate, encounterable evidence path sufficient for its claim**. A dedicated inheritance-provenance record is one possible solution, not a mandated design if another domain-appropriate path works. Do not create a globally readable history feed.
5. Clarify M2's two outcome levels: its scriptable state/encounter/non-leakage checks may finish while player-side intelligibility remains `PENDING` if no blinded human exercise happens. If no clue can be encountered, inference using that clue is `BLOCKED`, not silently assumed runnable. A negative human result does not block M1 or M4a.
6. Remove any other stale claim that lineage is already a delivered product proof, that an audit has not yet run, or that two distinct authority failures necessarily share one identical root cause. Keep the roadmap's decision-bearing body concise; leave review history in an appendix or PR notes.
7. Check internal references, headings, tables, milestone names, decision statuses, and dependency statements in **both** documents in one pass. Do not append another large “response to review round” section to the roadmap.

Use this pass to produce an implementation-ready first-wave scope, but do not let document cleanup become another broad investigation. Establish repository tickets or equivalent work items as the project requires. If local approval rules require a separate approval before a particular irreversible action, prepare that action for review; do not reinterpret ordinary reversible work as blocked.

## Phase 1 — M1: fix the natural-aging succession defect at the correct authority boundary

The previous investigation reported a reproducible 5-tick run in which ordinary aging causes `ApplyPath` to commit `entity.lifecycle.active=False` before `LifecycleSystem.resolve_lifecycle` dispatches `OLD_AGE`, leaving `death_reason=None` and preventing succession. Reproduce this on the current branch before changing code. Keep the raw seed, initial state, per-tick relevant state, and the exact test or reproduction command with the work item.

Design a domain-correct resolution of the authority and ordering problem. The obligation is a canonical authority for the persistent fact and a declared resolution rule for any world effect based on possibly stale state; it does not mandate one universal `revalidate()` API or one physical writer for every kind of effect. Check the semantics of non-aging death paths before choosing a fix, including combat and hazard paths if they touch `active`, so a narrow OLD_AGE correction does not corrupt them. Do not turn M1 into an unbounded rewrite of `ApplyPath`.

Implement the smallest correct change and a meaningful regression scenario that uses ordinary per-tick aging. Exit evidence must show the OLD_AGE cause and successor effects fire when the entity naturally reaches the relevant threshold, without mid-run artificial staging, while existing death/inheritance tests and any directly affected non-aging scenarios remain valid. Report the precise scope covered and any death path left unverified. If investigation overturns the reported root cause, revise the diagnosis and implement against the observed cause rather than preserving a mistaken story.

## Phase 2 — M4a: verify a composed world-side sequence after M1

After M1's regression evidence passes, run a bounded two-hop sequence through ordinary ticks: predecessor → heir → next heir. Verify identity, chronological order, authoritative death reasons, relevant inheritance or history transfer, and later state or behavior actually caused by the first transition. Keep seed and state/event trace. Define exactly what this scenario proves; do not infer natural frequency, population-wide emergence, player legibility, or a changed opportunity and later decision from one composed run.

This phase is gated **only** by M1's world-side correctness evidence. It proceeds even if M2 is pending, weak, or negative. If a new simulation blocker appears, record a reproducible failure and its narrowest known cause; do not silently expand the implementation scope. Fix a small directly related defect if the repository's task and risk rules permit it; otherwise create a follow-up item and leave M4a `BLOCKED_WITH_REASON`.

## Phase 3 — M2: separate state, encounterable evidence, provenance, and human inference

M2 may proceed in parallel with M1 and M4a using the already verified single transition. Use a minimal **provisional** observer position, not a permanent gameplay lens. Keep four checks distinct:

1. **World state:** inventory or another chosen state changed in a real single-hop run. Cite the run. This alone is not observer evidence.
2. **Encounter:** verify via a deterministic scenario whether the specified observer could actually receive a signal about the changed state at the relevant time and place. Identify the real carrier or viewpoint-scoped query. Check non-leakage of private cognition/strategic fields and avoid using developer-only logs as an in-world surface. If no encounter path exists, report the missing edge rather than inventing an omniscient projection.
3. **Provenance:** determine whether a clue identifies *inheritance* specifically, or only an ambiguous observation such as “this person now carries an item.” Record the confirmed absence or presence of an inheritance-origin signal separately from the raw inventory state. Do not require a dedicated provenance record by default; choose any future evidence-production design by domain meaning, authority, and viewpoint scope.
4. **Inference:** if legitimate clues can be presented, run a small blinded human observation exercise when a suitable participant is available. Give them only what the provisional observer could encounter. Ask what they think happened, which clues support that view, what remains unknown, and how a later clue might revise the view. Do not demand the true hidden answer. A script can verify data access, timing, and leakage; it cannot establish that a human can reason from the clues. If no human exercise can be run, report `PENDING`. If no clue is encounterable, report `BLOCKED` for this exercise.

M2's scripted checks may complete while the **player-facing outcome remains unproven**. State both statuses explicitly. If the current evidence is too weak for the product's intended inference, identify the minimum missing evidence-production capability and its domain owner as a proposed follow-up, without implementing a universal event/reputation feed.

## Phase 4 — M3a/M3b/M3c: independently schedulable authority checks

These are three separate, bounded checks. They can proceed in parallel with M1/M2 and need not all finish together to unblock M4a:

- **M3a, entity death:** `alive_set` across combat and world dynamics. Attempt a representative same-tick collision scenario.
- **M3b, faction diplomacy:** `diplomatic_relations_set` across autonomous transition and auto-alliance paths. Attempt a same-pair, same-tick scenario.
- **M3c, public reputation:** `reputation_set` from the two known producer paths. Attempt a same-entity, same-tick scenario. This checks mechanical authority/order only and does not decide what `public_reputation` should mean in the world.

Each finishes with `CONFIRMED_FINE_WITHIN_SCOPE`, `DEFECT_CONFIRMED`, or `BLOCKED_WITH_REASON`, supported by the scenario, code path, and bounded scope. Do not turn a harness limitation into a “fine” result. If a new defect is found, document and route it as a separate fix; do not automatically merge all three checks into M1.

The known region-ownership/FAC-010 issue remains independently tracked. Do not reclassify or silently close it as a side effect of the lineage fix.

## Registry and evidence workflow throughout

Use the current SCP validator and report-only drift detector, the mechanism registry, and existing causal-edge queries to ground Rule and mechanism claims. Update touched evidence through the project's normal process. The fact that lineage Rules are not formally SCP-mapped is `UNKNOWN` from the formal mapping perspective, not proof that a mechanism is missing. Full-Catalog mapping remains non-blocking.

For every significant claim in a PR or report, show which level supports it: frozen Rule, formal mapping, registry declaration, reachable production path, scenario runtime, longitudinal/composed run, or actual human observation. A passing test cannot be promoted to `PLAYER-EXPERIENCED`. A registry absence alone cannot establish universal absence across production code. A drift result of zero applies only to the mapped evidence the detector checks.

The earlier roadmap suggested a small `mechanism_id → citing rule_id` reverse query. It is optional to implement if it materially saves work in this batch and fits the existing registry API; otherwise leave it as a precisely scoped tooling follow-up. Do not build a second registry or a general Context Compiler here.

## Self-review and one consolidated handoff

Before asking for external review, conduct a deliberate second pass against the actual diff, not just your own completion summary:

- Verify every diagram edge against the milestone dependency table and detailed gate text. World-side work must never wait on M2.
- Search the active roadmap and plan for stale phrases such as “zero new capability work,” “gate not yet run,” “one incident,” “cheapest proof,” “player-facing proof delivered,” and outdated milestone names. Historical appendix text must be clearly historical.
- Verify that M1 and M4a have finite world-side exit evidence, M2 has separate technical and human statuses, and each M3 item has its own bounded result.
- Ensure every named “milestone” in the first wave has a finite deliverable and exit condition. Move optional future work without one out of the first-wave milestone list.
- Reconcile the roadmap's §4/§5/§7/§8, Owner Decision List, first-wave plan, registry notes, and tickets. Remove duplicative or contradicted current claims.
- Rerun only the tests and validation relevant to changed paths and required repository gates. Record commands, results, seed, and limitations. Do not keep adding speculative tests after the finite acceptance questions are answered.
- Review the player packet for hidden-world-truth leakage and for any clue that exists only because the developer already knows the answer.
- Label every remaining uncertainty `UNKNOWN`, `BLOCKED_WITH_REASON`, or `PENDING` at the appropriate evidence layer. Do not convert these to “pass” to make a tidy report.

Return **one consolidated review package**: links to the docs and PR(s)/tickets, a compact change summary, a milestone status table, the M1 regression and M4a run evidence, M2's four separate results, M3a/b/c results or legitimate scheduling status, SCP/registry validation results, remaining material risks, and only decisions that genuinely require the owner. The decision summary should fit on one page; the underlying evidence can be longer. Do not send a series of partial roadmap edits for external review while this bounded batch is still in progress.

If an external approval or project gate genuinely stops a dependent action, complete all independent work and present the exact reviewable action and reason. Keep the roadmap and plan `PROPOSED / FOR REVIEW` until the owner approves their direction; do not merge, deploy, or claim a player-facing proof without the evidence and authorization appropriate to those actions.
