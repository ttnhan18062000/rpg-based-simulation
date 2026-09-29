---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated review/instruction record for the systemic-world roadmap, copied from the local working file `external-ai-review-systemic-world-roadmap-instruction.md` on 2026-09-27. An input to the planning work, not current status.

# External AI review — `systemic_world_roadmap.md`

**To the local repository-aware agent**

This is an **external AI architecture/product review** of the supplied `docs/plans/systemic_world_roadmap.md`. I read the document supplied by the owner, but did **not** independently inspect the live repository, the revised foundational synthesis, Parts A/B, or PR #249. Treat repository and PR statements below as review of the document's reported evidence, not independent source verification. Please check the live files and PR before editing.

The roadmap is a strong proposed direction. The requested changes are a **bounded calibration and revision**, not a new foundation investigation or a rejection of its structure. Keep it `PROPOSED / FOR REVIEW`; do not promote or merge it as an owner-approved plan through this request.

## What this external review accepts as the current direction

Preserve these elements unless live repository evidence directly contradicts them:

1. **Whole-engine scope.** The Action–Recognition–Opportunity loop is one important cross-domain proof, not the organizing definition of the entire simulation engine. The persistent world also includes non-agent processes, life, environment, economy, lineage, institutions, culture, magic, and other causally valuable domains.
2. **Gameplay-neutral core.** The engine simulates a world independently of player attention. A gameplay lens defines how the player observes or acts in it; today's observer mode does not set the final engine ontology.
3. **Capability map and conditional dependencies.** The six perspectives provide useful coverage without implying six runtime modules or one mandatory development sequence. The three sample paths correctly show that lineage and some wealth/office conversions need not wait for social recognition.
4. **Epistemic product direction.** Players should learn world logic through situated observation and reasonable inference. A plausible but mistaken interpretation can be part of the intended experience. Player-facing material must not silently reveal hidden world truth simply because the engine knows it.
5. **Separate evidence axes.** `DESIGNED`, `REALIZED`, `VERIFIED`, `INTEGRATED`, and `PLAYER-EXPERIENCED` should remain distinct. M3 remains an ongoing, non-blocking evidence-ingestion stream.
6. **Delivery proofs at different strengths.** A player noticing a reaction differs from a later opportunity changing and a subsequent decision producing a durable consequence. Preserve the distinction between an initial experiential proof and a later closed-loop proof. Use multiple domain trajectories rather than claiming universal success from a hunter/shopkeeper demo.
7. **Governance.** A standalone proposed roadmap with an explicit relationship to existing plans is a sensible home. Preserve the frozen World Rule Catalog and its evidence-first change process.

## Changes required before I would recommend owner adoption

### 1. Reclassify the lineage first-product proof as a candidate with a feasibility gate

Section 5 calls lineage the cheapest proof, says its only missing piece is a player-facing projection, and recommends it as the first proof shipped. The reported code trace supports that several history-to-behavior mechanisms exist; it does **not yet prove** that the product can expose enough coherent, situated evidence across time for a player to observe a family's changing circumstances and infer a plausible explanation. A projection may require event selection, temporal continuity, viewpoint/scope, provenance, pacing, and sufficient durable evidence. Those are product-design and integration questions, even if no new world mechanism is needed.

Please retain lineage as a **strong first candidate to test**, not a committed first shipped proof. Add a lightweight decision gate before choosing it over other candidate trajectories:

- Can a real seeded run produce a consequential sequence from existing authoritative state/history, without inventing events or causes?
- What traces could a player plausibly encounter through a proposed gameplay lens, and what might legitimately remain unknown?
- Can an initial presentation preserve identity, chronology, and causal continuity across the relevant period?
- Is the player-facing proof feasible with projection/integration work alone, or does the run reveal a missing simulation or evidence-production edge?
- Compare feasibility and experiential clarity with at least one other existing trajectory, without requiring a large new UI design or a completed player-role decision at roadmap stage.

Use the result to recommend a first proof. Do not treat “few new simulation mechanisms” as equivalent to “cheap to deliver.” If this feasibility cannot be checked now, label the initial proof selection `OPEN`, with lineage the leading candidate.

### 2. Calibrate the player-understanding acceptance criterion

The evidence table says a player should state a plausible causal account **matching the real underlying state**. This risks turning the test into “guess the correct hidden answer,” contradicting the accepted goal that people may infer wrongly but reasonably.

Separate two checks:

1. **World-side truth check:** the underlying outcome has a coherent, Rule-conforming causal trace and player-facing clues originate from legitimate world evidence or an explicitly scoped projection.
2. **Player-side inference check:** given only the available clues, a player can form one or more intelligible hypotheses, distinguish observation from speculation, and revise an earlier interpretation when later evidence arrives. The hypothesis need not be true if the clues reasonably support it.

Also test the failure cases: no meaningful clue to an outcome the product expects the player to understand; a supposedly in-world view leaking hidden truth; and behavior that changes without a coherent world cause. Avoid requiring every private event to leave a publicly discoverable trace. Salience and promised player comprehension matter.

### 3. Narrow broad status and completeness claims

The Catalog being frozen establishes an accepted **baseline of target semantics**, not that every possible future world case is fully designed. In the capability table, replace unqualified `DESIGNED: Fully` and similarly broad “no Rule needed” wording with claims scoped to the current Catalog and investigated cases. Keep deferred areas, such as involuntary/coerced action, explicitly `OPEN` where the Catalog itself defers them.

Likewise, `PLAYER-EXPERIENCED: N/A` for world substrate, agency, or evaluation is too strong. Those capabilities can be experienced **indirectly** through coherent consequences, even though their internals are not exposed as a player-facing surface. Use “not directly surfaced,” “not evaluated,” or a similarly precise status. Do not fill this column by inference from internal test success.

Where §3.4 says witnessed/secondhand propagation into “that same already-correct state” is missing, avoid implying that `bonds/trust_history` is already the decided destination for witnessed or hearsay evidence. The earlier synthesis left those representations open. Preserve the distinction between direct participation, uninvolved witnessing, and secondhand report.

### 4. Make foundation verification finite and evidence-calibrated

Section 3.1 proposes a systematic pass whose proof is the **absence of recurrence** of the regional-sovereignty dual-authority pattern. A finite audit cannot prove that no other case exists anywhere. State a bounded verification target instead: identify the most consequential cross-domain mutation paths, review ownership/authority at their boundaries, and exercise representative integration scenarios. Report the scope covered and the remaining `UNKNOWN`s.

Preserve the stronger semantic obligation: every persistent fact has a canonical authority, and a world effect must not commit from stale assumptions without a declared resolution rule. This does not imply one physical code writer per fact or one universal `revalidate()` API for all domain actions and world processes.

### 5. Refine what belongs in the owner-decision list

The present #1 (“one record shape or two”) is mostly an implementation/modeling decision. The owner-level semantic question, if one genuinely remains, is whether **individual subjective relations and institutional judgments are distinct world concepts with different authority, evidence, and update rules**. Recommend a semantic default from the frozen Rules; leave the exact record types to local design.

For #2, propose institutions as the semantic home if that is what `IP-S17` and the Catalog support. Escalate to the owner only if there is a real, unresolved cross-domain authority conflict; the possibility of one is not yet a decision request.

For #3, first state the intended world meaning of `public_reputation` as an open semantic issue. A global scalar used as a fallback by strangers is not automatically a publicly knowable fact. Do not decide to retain or retire the field until the information provenance and scope of any “public” signal are defined.

#4, roadmap promotion, is a governance step after review rather than an unresolved world-semantic choice. Mention it as the next review action, not as a fourth conceptual decision the owner must settle now. The owner's meaningful near-term product choice is **which candidate trajectory to use for the first player-facing feasibility proof**, informed by the gate in item 1.

## Additional precision to retain in the revised roadmap

- The claim that a world process and an agent action need different execution paths is valid as an architectural boundary; do not infer that all current bypass paths are therefore semantically correct without domain evidence.
- An event can be unknown to the player without being a product defect. The defect is an outcome presented as learnable or important without a fair, situated way to reason about it, or a violation of the world's own causal rules.
- `PLAYER-EXPERIENCED` is an evidence level, not a property automatically produced by a projection existing in code. A small player-observation exercise or equivalent usability evidence is needed before claiming that outcome.
- Supportive lineage evidence is valuable, but do not label it a full cross-domain generalization or a verified product proof merely because it contains several causal components.
- Keep all implementation-specific findings as references or appendix material. Do not broaden this revision into new mechanism design, milestone tickets, UI specifications, or a redesign of World Rules.

## Requested work product

Update the proposed roadmap in the existing PR, and adjust the revised foundational synthesis only where the correction must also appear there. Return:

1. A concise change summary mapped to the five requested correction areas above.
2. The revised first-proof recommendation or an explicit `OPEN` with a bounded feasibility gate.
3. Updated evidence/status wording and bounded foundation verification criteria.
4. A shortened owner-decision list containing only actual semantic/product decisions, with local engineering decisions assigned locally.
5. A note of any external-review concern you rejected because direct repository evidence disproves it, with that evidence.

Keep the result `PROPOSED / FOR REVIEW`. This external AI review does not independently verify PR #249 or authorize merging, implementation, or Catalog edits. Once the revised roadmap is reviewable, the owner can accept the direction and local agents can then draft detailed milestone plans.
