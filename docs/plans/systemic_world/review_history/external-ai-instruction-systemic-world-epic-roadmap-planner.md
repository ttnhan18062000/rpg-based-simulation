---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated review/instruction record for the systemic-world roadmap, copied from the local working file `external-ai-instruction-systemic-world-epic-roadmap-planner.md` on 2026-09-27. An input to the planning work, not current status.

# External AI instruction — finalize the systemic-world roadmap and epic-level plan

You are the **roadmap and epic-level architecture planner** working with the owner and an external AI reviewer. A separate ticket planner will decompose approved epics into implementation tickets. Two other local agents implement and verify those tickets. Preserve this separation throughout the work.

This instruction supersedes earlier external AI instructions that asked you to implement M1, execute M2/M3/M4a, write regression tests, or decide a concrete code fix. Those requests crossed your role boundary. Targeted read-only repository checks are appropriate when needed to prevent a false architectural claim. Stop at a documented UNKNOWN when deeper technical investigation belongs to the ticket planner or implementers.

## Intended deliverables

Produce a reviewable package consisting of:

1. A **whole-engine systemic-world roadmap**: north star, capability map, domain relationships, evidence maturity, dependency options, and outcome-based epic portfolio.
2. A separate **epic-level first-wave plan**: proposed epics, their outcomes and boundaries, cross-epic dependencies, proof gates, and what happens if a gate fails.
3. A **handoff for the downstream ticket planner**: enough semantic and evidentiary context to create tickets without re-inventing the architecture, but no prescribed class edit, test file, or technical solution.
4. A concise **owner decision memo**: only real semantic, product-scope, or epic-priority choices that cannot be resolved by evidence or normal planner judgment.

Keep the documents `PROPOSED / FOR REVIEW` in their visible content until the owner accepts their direction. Verify how this repository's frontmatter status field is interpreted. If its validator does not support `proposed`, do not silently represent owner approval by choosing `active`: either use a valid metadata status whose documented meaning is compatible with “under review,” or explicitly explain the metadata limitation and propose a separate schema correction. Do not merge or mark the roadmap approved yourself.

## Product and architecture north star

The engine simulates a persistent fantasy world independently of any player's attention and without committing to one gameplay lens. Ordinary subjects, institutions, places, and processes can accumulate histories and become significant through their consequences. Domain advantages such as wealth, authority, knowledge, relationships, territory, and capability remain distinct and convert only through declared causal paths.

A player should be able to encounter some consequences through a situated viewpoint and form a reasonable hypothesis without being taught every internal rule. The hypothesis may be wrong when evidence is incomplete or misleading in an in-world way. Private events and foundational machinery may remain hidden. The defect is an important outcome presented as understandable with no fair trace, an omniscient surface that reveals hidden truth, or a world consequence that violates its own causal contracts.

Do not turn the Action–Recognition–Opportunity investigation, lineage example, or current first wave into the ontology or obligatory progression of the entire engine. Keep distinct domain owners and multiple independent trajectories visible.

## Authority and evidence boundaries

Use the current repository versions of the frozen World Rule Catalog, mechanism registry, Semantic Control Plane (SCP), foundational synthesis, systemic roadmap, first-wave plan, relevant investigation notes, and any newer implementation-agent findings. Do not assume the attachment copies or earlier response summaries are current.

Preserve these layers in every consequential epic claim:

| Layer | Question |
|---|---|
| World Rule | What world semantics are specified within the Rule's actual scope? |
| Formal mapping / registry | Which relationship and implementation status is recorded, with what evidence? |
| Runtime realization | Which behavior actually fires in a bounded run, and through which authority path? |
| Cross-domain composition | Does it remain coherent over time and across domain boundaries? |
| Situated evidence | What in-world trace exists, and who could encounter it? |
| Player inference | Can a person reason from only those clues, with legitimate uncertainty? |

`UNKNOWN` means the question was not established. `MISSING` requires investigation confirming absence. A mechanism entry, passing one-tick test, observed multi-tick run, and human observation exercise are different evidence levels. SCP mapping coverage is useful for tracing and drift management but is not a prerequisite for all 172 Rules or a proxy for product priority. M3/Stage D continue alongside whichever epics touch relevant domains.

Use existing SCP validators and query recipes where useful for planning. Record a specific missing query if it materially slows planning. Do not build a new registry, generalized query engine, or Stage-F Context Compiler as part of this planning assignment.

## Step 1 — recalibrate the two current documents to the correct planning level

The current first-wave plan was written when the planner's role was blurred with implementation. Audit both documents for engineering-level tasks that should move to the downstream ticket planner. Preserve the facts and evidence, but restate the plan as **outcome-based epics and gates**.

An epic should have:

- a world or player-facing outcome and why it advances the north star;
- the semantic contract and domain authority it must preserve;
- in-scope and out-of-scope capability boundaries;
- known evidence and explicit UNKNOWNs;
- dependencies on other epics, with genuine hard gates distinguished from parallel work;
- world-side and player-side proof claims kept separate;
- finite, reviewable completion evidence at the epic level;
- failure or blocked branches that return a decision to the roadmap rather than silently expanding scope;
- the inputs and questions the ticket planner must resolve.

An epic should **not** dictate a one-line code change, class reuse, exact data schema, exact test filenames, or a universal API. It should not imply that an observer-facing exercise must succeed before the world simulation is made correct. Do not force each of the six roadmap capability areas to be one epic; an epic may cross domains, and a capability area may need several independently scheduled epics.

The first-wave plan's former M1/M2/M3a-c/M4a labels may remain as historical evidence or candidate workstreams if useful, but the active plan should show the **epics** and their relationship, not present a ticket list under milestone labels. Any optional follow-on without finite first-wave exit evidence belongs in the future portfolio, not as a first-wave completion milestone.

## Step 2 — assemble the whole-engine epic portfolio

For each proposed epic across the roadmap, identify its capability area(s), domain owner(s), Rule support where verified, existing mechanisms, current evidence maturity, intended world outcome, possible observer value, independent prerequisites, and whether it is a first-wave candidate, later candidate, or parked UNKNOWN. Use a compact portfolio view rather than creating a full detailed plan for every domain.

Ensure the portfolio represents genuinely different causal trajectories and owners. Examples to evaluate from existing evidence include: world authority and temporal continuity; situated evidence/observation; individual history propagation; institutional judgment and authority; wealth or office conversion through declared edges; ecology/settlement dynamics; agency across action and non-action world processes; and later magic/culture breadth. These examples are prompts to assess, not commitments or claims that mechanisms already exist. Retain lineage as one useful probe, not the organizing axis for all future work.

Show at least two plausible dependency paths through the epic portfolio, including one that does not rely on recognition propagation. Dependencies should be semantic or evidentiary necessities, not an arbitrary universal phase order. Make clear which foundations are reusable and which domain work can proceed independently.

Distinguish **first-wave epic selection** from a claim that its product proof has already been delivered. If competing first-wave options cannot be ranked on current evidence, present a recommended default and a bounded decision gate instead of inventing certainty. Avoid an indefinite investigation program.

## Step 3 — define the first wave at epic level

Ground the first wave in the latest verified findings:

- The reported natural-aging `OLD_AGE`/succession failure is a reproducible world-side defect; its technical cause and the unreviewed one-line prototype are implementation inputs, not the planner's chosen solution.
- The two-hop lineage world sequence remains unproven until that defect is resolved; verifying world continuity is valuable independently of player legibility.
- The former “heir carries the item” observer clue was not actually deliverable to another observer through current production perception. The state transition exists, but evidence production/carrier, viewpoint encounter, inheritance provenance, and human inference are separate matters. A design epic may establish the minimum domain-owned evidence path and observer contract; it must not claim player understanding from a script or a narrative sketch.
- The three same-tick authority boundaries (entity death, faction diplomacy, public reputation) remain separately schedulable. They may be grouped under a reusable foundation epic only if their independent ownership and completion states remain explicit.
- The known region-ownership issue stays on its existing track; do not silently close or re-scope it under lineage.

A sensible first-wave *proposal* may contain (a) an epic for authoritative life/death and cross-tick world continuity, (b) an epic for situated evidence and inference design, and (c) an independently schedulable authority-boundary verification program. You may choose different epic boundaries if repository semantics support them better. Explain the selection and its tradeoffs.

At the epic level, separate:

1. **World correctness proof:** real natural aging and succession, with bounded temporal composition and no forced player surface.
2. **Evidence-path design proof:** a plausible, domain-owned route from world state/event to legitimate, viewpoint-scoped clue. This may end as a design decision and downstream ticket set; it is not yet a player-experienced proof.
3. **Player inference proof:** later human observation using only the legitimately encounterable clues. Mark pending or blocked until the evidence path and an exercise exist.
4. **Changed-life-trajectory proof:** requires a later opportunity or decision and a durable outcome; do not claim it from a death-to-heir transfer or differentiated reaction alone.

The epic plan must say which of these four claims the first wave is meant to establish, which it only prepares, and which remain future work. An important hidden foundation can be complete on world-side evidence without being directly surfaced to a player.

## Step 4 — prepare a downstream ticket-planner handoff

For each first-wave epic, prepare a concise handoff card with:

- epic outcome and semantic invariant;
- domain owner and interfaces to other domains;
- verified current evidence and direct links to sources or reproductions;
- specific known defects or missing edges, labeled by evidence level;
- in-scope and out-of-scope outcomes;
- dependencies, independent work, and finite epic acceptance evidence;
- implementation questions for the ticket planner and implementers to answer;
- risks to adjacent behavior and rollback or regression concerns at the *contract* level;
- required updates to registry/SCP evidence once implementation results are available.

The existing M1 ticket draft may be passed as **background material**, clearly marked unreviewed and not binding on a technical solution. The parked prototype branch is also optional evidence for an implementer to inspect or discard. It is not a candidate fix approved by the roadmap group. Do not ask the owner to decide whether to keep that local branch; preserving it unmerged is a routine engineering choice.

Do not create or refine detailed implementation tickets under this task. The next ticket planner owns ticket granularity, technical investigations, acceptance tests, and assignment to the two implementation agents.

## Step 5 — one internal review before handoff

The owner wants to avoid repeated external review of slightly updated files. Before reporting back, perform one thorough self-review:

- Read the active roadmap and epic plan as a pair. Confirm the north star, epic portfolio, first-wave selection, owner decision memo, and ticket-planner handoff tell one consistent story.
- Search for stale assertions that lineage needs zero work, that the earlier observer clue is already encounterable, that the bounded audit has not run, or that a player-facing proof has already been achieved.
- Confirm no world-side correctness epic is gated on observer/inference outcomes.
- Confirm the plan does not require hidden foundations to become visible, and does require fair evidence only where player understanding is an intended outcome.
- Confirm epic exit evidence is finite and does not require completing every Rule mapping or domain.
- Confirm every `BLOCKED`, `UNKNOWN`, and `PENDING` has a reason, a domain owner or follow-up, and an appropriate decision point.
- Check frontmatter against the actual repository schema and explain any semantic mismatch between metadata status and the visible proposal status.
- Verify document references and current PR branch contents. Make the final docs accessible for owner review through normal repository practice; do not merge them.
- Keep the decision-bearing roadmap readable. Historical external-review response logs belong in an appendix or PR discussion, not mixed into current recommendations.

Return one consolidated review package: final roadmap and epic-plan links, a one-page epic portfolio/first-wave summary, the ticket-planner handoff, the evidence limits, and only genuine owner choices. State which branch and commit contain the reviewable documents and whether the PR reflects them. Do not ask for owner approval of a plan whose latest commits are still only local and unavailable to review.

## Explicit scope limits

Do not edit production code, execute the first-wave implementation, write new regression tests, conduct all three authority scenarios, or build an observer surface. Do not adopt or merge the parked prototype. Do not settle `public_reputation`'s world meaning, merge individual and institutional standing, impose one action or reputation ontology, or choose a permanent gameplay lens. Targeted read-only inspection to keep planning claims honest is allowed; deeper technical work is delegated downstream.

The intended result is an owner-reviewable **whole-engine roadmap and epic-level first-wave plan**, followed by a clean handoff to a separate ticket planner. Approval of the plan is not evidence that the simulation or player experience has already been delivered.
