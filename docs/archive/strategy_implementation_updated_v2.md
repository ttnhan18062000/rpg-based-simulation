This document is a corrective implementation plan derived from verification of the current source and test suite.

It is **not** a restatement of the original corrective draft.
It contains only:

- remaining missing tasks,
- wrongly framed tasks that need correction,
- stale tasks that should be removed from the plan,
- and cross-cutting corrective work still required to make the implementation match the milestone intent.

The most important finding is this:

The source is still ahead of the proof, but the original corrective plan is now also partly behind the source.
Some original corrective tasks were valid when written and are now stale. The remaining risk is no longer “missing architecture.” It is stale verification paths, truth-surface drift, and over-broad milestone claims.

---

## Cross-Cutting Remediation Track — Runtime Isolation, Artifact Truth, and Stale-Proof Repair

[Track Description]

Before continuing any further strategy expansion, repair the verification surfaces that are now actively misleading.

The current system no longer has the same problems the original corrective draft described. Some infrastructure import guards are already in place, deterministic regression has already been moved to `HeadlessRunner`, and several Milestone 1 proof tasks are already covered by tests. The remaining problems are narrower and more dangerous:

1. disabled-mode infrastructure proof is still incomplete,
2. replay-vs-graph assertions are partially stale against current replay shape,
3. graph/API/inspector/replay surfaces still expose overlapping but not fully aligned strategic truth.

[Track technical implementation]

Address these exact classes of problems:

1. **Disabled-mode infrastructure proof gap**
   - `api/rabbitmq_client.py` already uses guarded import semantics for `pika`.
   - The corrective task should no longer pretend RabbitMQ guarding is missing.
   - The real missing work is proving collection and execution in disabled mode across the optional integration surface.

2. **Stale artifact-consistency assertions**
   - `assert_strategic_consistency` still reads replay using `ticks[-1]["state"]["entities"]`.
   - current replay-facing tests and cognition assertions read `ticks[-1]["entities"]`.
   - that mismatch makes the current strategic consistency helper partially stale as a verification source.

3. **Split truth surfaces**
   - `StrategicStateSchema` exposes obligations, contracts, offers, zones, hypotheses, current project/objective, and cognition metadata.
   - the graph exporter and its assertions still verify a much narrower overlap.
   - the plan must now focus on explicit ownership and overlap contracts instead of generic “more tests.”

[Track important notes]

Remove these stale tasks from the corrective plan entirely:

- the direct `scripts.test_harness` migration task,
- the broad “missing `StrategicUpdate` transport tests” task,
- the broad “missing strategic snapshot proof” task.

Those are no longer open work in the form originally written. Regression tests already use `HeadlessRunner`, transport semantics already have dedicated tests, and strategic snapshot isolation/serialization coverage already exists in the suite. Keeping them open is misdirection.

[Track acceptance criteria]

The corrective track is complete only when:

- disabled infrastructure mode is explicitly proven in tests,
- replay-vs-graph assertions read the real artifact shape,
- and every visibility surface has documented ownership and intentionally limited overlap.

## Task

[x] (checkbox) - [Track Task 1] - Prove optional-infrastructure disabled-mode collection and execution

[Task Description]

The original wording was wrong. RabbitMQ import guarding is already implemented. The missing work is not “add the guard.” The missing work is proving disabled-mode collection and execution without optional broker packages present.

[Task technical implementation]

Add tests that prove:

- plain unit and integration test collection succeeds with RabbitMQ/Kafka disabled,
- optional infrastructure modules do not crash import when packages are unavailable,
- and regression paths remain runnable without broker dependencies when disabled.

[Task possible affected files]

- `src/api/rabbitmq_client.py`
- Kafka client modules under `src/api/`
- test fixtures configuring `DISABLE_RABBITMQ`, `DISABLE_KAFKA`, and related env flags
- CI/test bootstrap modules

[Task check list]

- [x] Add brokerless-import smoke test for RabbitMQ-disabled mode
- [x] Add brokerless-import smoke test for Kafka-disabled mode
- [x] Add disabled-mode regression runner smoke test
- [x] Document the required env flags for hermetic test execution

[Task acceptance criteria]

The suite proves disabled-mode isolation instead of assuming it.

---

[x] (checkbox) - [Track Task 2] - Repair stale replay-vs-graph assertion paths before deepening semantics

[Task Description]

Current strategic consistency assertions are reading an older replay shape. That invalidates part of the proof surface before any semantic deepening even begins.

[Task technical implementation]

First, align `assert_strategic_consistency` with the actual replay artifact shape.
Then define a strict overlap contract for what replay and graph are intentionally compared on.

Do not add more semantic assertions until the helper is reading the right artifact.

[Task possible affected files]

- `src/testing/assertions.py`
- `tests/e2e/strategy/test_strategic_regression.py`
- `src/utils/replay.py`

[Task check list]

- [x] Replace stale `ticks[-1]["state"]["entities"]` read path
- [x] Define the exact replay fields eligible for graph comparison
- [x] Add a regression test that fails on replay-shape drift
- [x] Document strategic consistency overlap rules

[Task acceptance criteria]

Artifact-consistency assertions read the actual artifact and only compare intentional overlap.

---

[x] (checkbox) - [Track Task 3] - Define and enforce truth-surface ownership with real overlap tests

[Task Description]

The API presenter, replay, inspector, and graph exporter now expose overlapping strategic data, but they do not share one explicit ownership contract. This is now the central integrity problem.

[Task technical implementation]

Document and enforce these boundaries:

- replay = compact longitudinal summary,
- presenter/API = structured human-facing inspection surface,
- inspector = debug rendering,
- graph export = machine-verifiable relational artifact,
- assertions = consumers of artifacts, not hidden truth reconstructors.

Then add focused tests for overlapping semantics.

[Task possible affected files]

- `src/utils/replay.py`
- `src/api/presenters/ai_presenter.py`
- `src/ui/cli/inspector.py`
- `src/core/logic/cognition_graph_exporter.py`
- `src/testing/assertions.py`

[Task check list]

- [x] Add ownership docstrings/comments to each truth surface
- [x] Add populated-state parity tests for overlap fields
- [x] Assert that replay stays summary-level
- [x] Assert that graph export derives from persisted state only
- [x] Assert that inspector does not invent hidden state

[Task acceptance criteria]

Each surface has one job and no surface silently repairs another.

---

## Milestone 1 — Strategic state foundation (Revised Corrective Scope)

[Milestone Description]

Most of the originally claimed “missing Milestone 1 proof” is now stale.
Strategic transport tests exist. Snapshot isolation exists. JSON round-trip exists. The remaining Milestone 1 work is narrower: strategic visibility smoke coverage and artifact-shape consistency for populated state.

[Milestone technical implementation]

Do not reopen transport or snapshot work broadly.
Focus only on the remaining shallow surfaces:

- dedicated strategic inspector smoke coverage for uncertainty and contracts,
- and populated-state replay/API consistency checks for strategic summaries.

[Milestone important notes]

Remove the original open task for `StrategicUpdate` transport semantics from this plan.
It is already covered enough to stop treating it as missing corrective work.

[Milestone acceptance criteria]

Milestone 1 is complete when strategic visibility surfaces are smoke-tested for real populated state and no stale “missing proof” task remains in the document.

## Task

[x] (checkbox) - [Task 1] - Add dedicated strategic inspector smoke coverage for uncertainty and contract surfaces

[Task Description]

The inspector already renders uncertainty and social-contract sections, but the corrective plan should stop claiming the whole strategic inspector surface is missing. The real gap is dedicated smoke coverage for those rendered sections.

[Task technical implementation]

Add tests that verify the inspector can render:

- empty strategic state safely,
- uncertainty structures,
- contracts/offers/obligations,
- and partially populated mixed strategic state without crash.

[Task possible affected files]

- `tests/ui/test_inspector_strategy_output.py`
- `src/ui/cli/inspector.py`

[Task check list]

- [x] Add empty-state strategic inspector smoke test
- [x] Add uncertainty-section smoke test
- [x] Add contracts/offers/obligations smoke test
- [x] Add mixed partial-state no-crash smoke test

[Task acceptance criteria]

Strategic inspector coverage matches the sections the inspector actually renders.

---

[x] (checkbox) - [Task 2] - Add populated-state strategic summary parity tests across replay and API

[Task Description]

There is proof for isolated surfaces, but the populated-state summary contract across replay and API is still too loose.

[Task technical implementation]

Add tests that inject one populated strategic state and verify:

- API presenter exposes the expected summary fields,
- replay recorder emits the intended compact summary,
- and differences are intentional and documented.

[Task possible affected files]

- `tests/integration/api/test_strategy_observability.py`
- `src/utils/replay.py`
- `src/api/presenters/ai_presenter.py`

[Task check list]

- [x] Add populated-state replay summary assertion
- [x] Add populated-state API summary assertion
- [x] Document intentional replay/API field differences

[Task acceptance criteria]

Replay and API strategic summaries are intentionally different, not accidentally divergent.

---

## Milestone 2 — Strategic appraisal and project continuity (Revised Corrective Scope)

[Milestone Description]

The continuity layer is not absent, but the remaining proof gap is now specific:
resume-path objective continuity and structured explainability remain thinner than the milestone intent. The broad “continuity missing” wording should be narrowed.

## Task

[x] (checkbox) - [Task 1] - Add resume-restores-objective and objective-to-tactical alignment tests

[Task Description]

Current continuity tests prove retention and selection behavior, but the corrective plan should now target the missing edges: resume restoring a valid objective and tactical behavior staying aligned with current objective.

[Task technical implementation]

Add tests that verify:

- interrupted project resumption restores a valid `current_objective_id`,
- resumed objective survives one tactical decision cycle,
- and tactical choice remains aligned with the active strategic objective.

[Task possible affected files]

- `tests/integration/strategy/test_strategic_persistence.py`
- `src/ai/brain.py`

[Task check list]

- [x] Add resume-restores-objective test
- [x] Add resumed-objective persistence test
- [x] Add objective-to-tactical alignment assertion

[Task acceptance criteria]

Continuity proof covers the resume path instead of only initial selection and retention.

---

[x] (checkbox) - [Task 2] - Add structured strategic explainability assertions

[Task Description]

This task remains valid.
Explainability still needs structural tests rather than behavioral inference alone.

[Task technical implementation]

Add tests asserting surfaced reasons for:

- keep current project,
- switch project,
- suspend project,
- resume project,
- and tactical choice alignment.

[Task possible affected files]

- `tests/ai/test_strategic_explainability.py`
- `src/api/presenters/ai_presenter.py`

[Task check list]

- [x] Add keep-project reason assertion
- [x] Add switch-project reason assertion
- [x] Add suspend/resume reason assertion
- [x] Add objective-to-tactical explanation assertion

[Task acceptance criteria]

Continuity outcomes are structurally explainable.

---

## Milestone 3 — Leads, uncertainty, blockers, and detours (Revised Corrective Scope)

[Milestone Description]

The blocker and detour architecture is real.
The remaining gap is anti-cheating proof and end-to-end learning-state application, not basic feature existence.

## Task

[x] (checkbox) - [Task 1] - Add anti-cheating candidate-zone and hypothesis tests

[Task Description]

This remains valid.
The system still needs proof that vague information stays vague instead of silently collapsing to exact truth.

[Task technical implementation]

Add tests that verify:

- vague lead ingestion creates candidate zones or hypotheses where appropriate,
- no exact coordinate is emitted without sufficient direct evidence,
- contradictory evidence degrades uncertainty structures rather than silently replacing them.

[Task possible affected files]

- `tests/ai/test_strategic_leads_and_uncertainty.py`
- strategic knowledge ingestion services

[Task check list]

- [x] Add vague-rumor candidate-zone test
- [x] Add no-silent-coordinate-collapse test
- [x] Add contradiction-updates-uncertainty test

[Task acceptance criteria]

Uncertain strategic knowledge stays uncertain until justified.

---

[x] (checkbox) - [Task 2] - Add authoritative application tests for lead-learning and source-trust updates

[Task Description]

`StrategicLearningService` now emits `source_trust_updates`, but the proof surface should stop relying on comments and assumptions. It needs end-to-end application tests.

[Task technical implementation]

Add tests that verify:

- success and failure outcomes update source trust in authoritative strategic state,
- updated source trust affects later source weighting or learning behavior,
- and lead exhaustion/reactivation behavior is preserved after state application.

[Task possible affected files]

- `tests/ai/test_lead_learning.py`
- `tests/ai/test_tested_lead_memory.py`
- `src/systems/gameplay/action_system.py`

[Task check list]

- [x] Add source-trust authoritative application test
- [x] Add future-weighting effect test
- [x] Add reactivation-on-new-info integration test

[Task acceptance criteria]

Lead learning is proven as stateful behavior, not just service-local output.

---

## Milestone 5 — Event-driven strategic reprioritization (Revised Corrective Scope)

[Milestone Description]

The event pipeline exists, but the remaining missing proof is thresholding and durable downstream effects. That part of the original corrective plan remains valid.

## Task

[x] (checkbox) - [Task 1] - Add thresholded repeated-event mutation tests

[Task Description]

Keep this task.
It is still aimed at a real proof gap.

[Task technical implementation]

Add tests for repeated-event thresholds in directive mutation and reprioritization, not just one-off event reactions.

[Task possible affected files]

- `tests/ai/test_directive_mutation_from_events.py`

[Task check list]

- [x] Add repeated-near-death threshold test
- [x] Add repeated-defense-success threshold test
- [x] Add repeated-betrayal threshold test
- [x] Assert no one-off overreaction

[Task acceptance criteria]

Repeated-event effects are thresholded and history-sensitive.

---

[x] (checkbox) - [Task 2] - Add downstream feedback-loop tests

[Task Description]

Keep this task, but narrow it to the feedback loops that still lack durable proof.

[Task technical implementation]

Add tests that verify:

- betrayal affects later recruitment,
- repeated false leads affect later source weighting,
- severe failure affects later reattempt behavior.

[Task possible affected files]

- `tests/ai/test_reprioritization_feedback_loops.py`

[Task check list]

- [x] Add betrayal-to-future-recruitment test
- [x] Add false-lead-to-source-weighting test
- [x] Add severe-failure-to-reattempt test

[Task acceptance criteria]

Event consequences feed forward into later strategic behavior.

---

## Milestone 6 — Entity cognition graph export (Revised Corrective Scope)

[Milestone Description]

The original corrective wording is now partially wrong.
The exporter is no longer “only strategic core.” It already includes turning points, place attachments, and a `cognition_profile` node. The real problem is not pure under-implementation anymore. The real problem is mixed scope and incomplete parity with persisted/API-visible strategic structures.

[Milestone technical implementation]

Do not rewrite this as “rename to strategic-core graph.”
That would now be behind the source.

Instead:

- align graph export with the persisted strategic structures already exposed elsewhere,
- then explicitly document which broader cognition domains are in scope and which are intentionally excluded.

[Milestone important notes]

Remove the stale checklist items that still say turning points and place attachments are missing.
They are already exported.

## Task

[x] (checkbox) - [Task 1] - Expand graph export coverage to persisted strategic structures already exposed in API/schema

[Task Description]

This task remains valid and becomes more important now that `StrategicStateSchema` already exposes zones, hypotheses, obligations, contracts, and offers.

[Task technical implementation]

Add graph support for:

- obligations,
- contracts,
- recruitment offers,
- candidate zones,
- hypotheses,
- and deterministic continuity edges where relevant.

[Task possible affected files]

- `src/core/logic/cognition_graph_exporter.py`
- `src/core/models/cognition_graph.py`
- `tests/core/test_cognition_graph_exporter.py`

[Task check list]

- [x] Add obligation nodes/edges
- [x] Add contract nodes/edges
- [x] Add recruitment-offer nodes/edges
- [x] Add candidate-zone nodes/edges
- [x] Add hypothesis nodes/edges
- [x] Add deterministic ordering tests

[Task acceptance criteria]

Graph export covers the persisted strategic structures already visible in API/schema.

---

[x] (checkbox) - [Task 2] - Define remaining broader cognition scope explicitly

[Task Description]

Turning points and place attachments are already in graph scope. The remaining ambiguity is selected belief targets, memory anchors, and any other broader cognition domains not yet clearly in or out of scope.

[Task technical implementation]

Choose one of two paths explicitly:

**Option A — expand further**
Add selected belief-target and memory-anchor support relevant to active strategic context.

**Option B — document exclusion**
Keep current graph scope, but document that these broader cognition domains are intentionally excluded from this artifact.

[Task possible affected files]

- `src/core/logic/cognition_graph_exporter.py`
- `src/core/models/cognition_graph.py`
- graph docs and test docs

[Task check list]

- [x] Decide whether belief targets are in scope
- [x] Decide whether memory anchors are in scope
- [x] Document included vs excluded cognition domains
- [x] Update tests/docs to match that scope exactly

[Task acceptance criteria]

The exporter’s scope is explicit and truthful.

---

## Milestone 7 — Final-system CLI regression path (Revised Corrective Scope)

[Milestone Description]

The canonical runner migration is already done.
What remains is semantic depth and stale assertion repair, not harness replacement.

## Task

[x] (checkbox) - [Task 1] - Deepen replay-vs-graph consistency assertions after helper repair

[Task Description]

Keep this task, but only after fixing the stale replay read path first.

[Task technical implementation]

After helper repair, extend overlap checks only for fields intentionally present on both sides.

[Task possible affected files]

- `src/testing/assertions.py`
- `tests/e2e/strategy/test_strategic_regression.py`

[Task check list]

- [x] Add current-objective consistency assertion if replay exposes it
- [x] Add concern/blocker overlap assertions where intentional
- [x] Add contract/obligation assertions only if replay intentionally summarizes them
- [x] Document excluded comparisons explicitly

[Task acceptance criteria]

Consistency checks are deeper and still honest.

---

[x] (checkbox) - [Task 2] - Strengthen deterministic scenario semantics in final-system tests

[Task Description]

This task remains valid.
The runner proves artifact production, but some scenario semantics are still thinner than the milestone intent.

[Task technical implementation]

Strengthen deterministic end-to-end scenarios for:

- blocker plus detour emergence,
- contract-backed continuation,
- event-driven pivot or suspension.

Each must assert semantic artifact outcomes, not just file existence.

[Task possible affected files]

- `tests/e2e/strategy/test_strategic_regression.py`
- dedicated scenario tests under `tests/e2e/strategy/`

[Task check list]

- [x] Add blocker/detour artifact assertions
- [x] Add contract-backed continuation assertions
- [x] Add pivot/suspension assertions
- [x] Keep scenarios small and deterministic

[Task acceptance criteria]

Final-system scenarios prove strategic behavior, not just runnable output.
