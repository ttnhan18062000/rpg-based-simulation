---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: unknown
---

Good. Milestone 6 is where the system stops being “maybe strategic internally” and becomes **provable**.

Up to Milestone 5, you can build a serious life-direction engine. But unless you can export a canonical, deterministic representation of an entity’s persisted cognition, you are still mostly trusting yourself. That is not engineering. That is optimism. Milestone 6 is the point where the stored strategic/subjective state becomes an explicit artifact you can inspect, diff, and regression-test. That matches both the design direction and your own goal of exporting the stored graph of an entity and using it to test the whole thinking feature.

# Milestone 6 — Entity cognition graph export

## What this milestone actually delivers

At the end of Milestone 6, you should be able to:

- take an entity’s persisted state
- derive a canonical cognition graph from it
- export that graph deterministically
- inspect it directly
- compare it across runs
- use it as a regression artifact for “thinking”

That is the first time the engine has a stable answer to this question:

**What does this entity currently believe it is doing, why, what is blocking it, what social bindings matter, and what history is shaping it?**

Without this milestone, the answer remains scattered across models and presenter logic. With it, the answer becomes an artifact. That is a huge difference.

What Milestone 6 does **not** need:

- fancy visualization UI
- a graph database
- editable graph authoring
- deep analytics dashboards

This is an export and verification milestone, not a product polish milestone.

---

## The real problem you are solving

The trap here is obvious: you already have replay, inspection views, presenters, and structured state, so it is tempting to say “we can already observe the system.”

Not enough.

Why? Because right now the truth is still fragmented:

- strategy lives in `mind.strategic`
- beliefs live elsewhere
- turning points live elsewhere
- social state lives elsewhere
- tactical continuity lives elsewhere
- replay likely compresses too much
- presenter output is optimized for display, not canonical structural verification

That means you can inspect parts of the system, but you do not yet have one deterministic artifact that says: **this is the entity’s stored cognition state as a graph.** Without that artifact, your “whole thinking” tests remain weaker than they should be.

---

## What must exist by the end of this milestone

You need five things.

### 1. A canonical export schema

You need one stable output schema for the cognition graph.

At minimum it should contain:

- graph metadata
- root entity info
- nodes
- edges
- optional annotations/reasons
- deterministic ordering

Do not leave this as ad hoc JSON assembled differently by different callers. That would be sloppy and would destroy regression value.

### 2. Stable node and edge kinds

The graph must be based on persisted domain concepts, not presentation fluff.

Likely node kinds:

- entity
- directive
- project
- objective
- concern
- blocker
- lead
- obligation
- contract
- candidate_zone / hypothesis
- turning_point
- belief_target
- memory_anchor if strongly justified

Likely edge kinds:

- `has_directive`
- `owns_project`
- `has_objective`
- `current_project`
- `current_objective`
- `blocked_by`
- `informed_by`
- `generated_from`
- `bound_by`
- `contracts_with`
- `believes_about`
- `remembers`
- `interrupted_by`
- `attached_to_place`

Do not invent edge types for aesthetics. Every node and edge should map back to persisted state.

### 3. Deterministic export rules

This is non-negotiable.

The same entity state must export the same graph every time.
That means:

- stable node IDs
- stable edge IDs or stable derivation
- deterministic ordering
- no incidental dict iteration behavior
- no time-dependent decorations unless explicitly stored

If the export is not deterministic, it is useless for regression.

### 4. Read-only derivation from persisted state

The export must be derived from stored state, not become a second state store.

That means:

- no mutation during export
- no hidden “graph-only” truth
- no repair or inference that changes entity data
- no export-time side effects

If export mutates state or invents extra truth, you have created another lie layer.

### 5. Access path for tests and inspection

The graph needs a consistent retrieval path.

Good options:

- dedicated export service callable from code
- optional API endpoint
- optional CLI export file output
- optional inspector hook for summary

The service is the primary thing. API and CLI are just delivery surfaces.

---

## The correct implementation order

### Step 1 — Write tests for determinism and structural completeness

Start with the anti-sloppiness tests.

Write failing tests that prove:

- empty strategic state exports a valid graph
- populated state exports required node/edge types
- same input state exports identical output
- export does not mutate the entity
- current project/objective appear consistently
- blockers, leads, obligations, and contracts appear only when present
- missing optional domains do not crash export

If you do not start here, you will drift into “whatever JSON is convenient.”

### Step 2 — Define the graph schema

Create a dedicated schema module, something like:

- `src/core/models/cognition_graph.py`
  or
- `src/api/schemas/cognition_graph.py`

You need:

- `CognitionGraph`
- `GraphNode`
- `GraphEdge`

Minimal useful fields:

`GraphNode`

- `node_id`
- `kind`
- `label`
- `ref_id` or domain ID
- `attributes`

`GraphEdge`

- `edge_id`
- `kind`
- `source_id`
- `target_id`
- `attributes`

`CognitionGraph`

- `entity_id`
- `tick`
- `nodes`
- `edges`
- maybe `summary`

Keep it minimal and deterministic. Do not bury important semantics in unbounded `attributes` blobs if they deserve first-class typed fields.

### Step 3 — Build the exporter service

Create something like:

- `src/core/logic/cognition_graph_exporter.py`
- `EntityCognitionGraphExporter`

Its job:

- accept entity + maybe world/snapshot context
- read persisted state
- emit a deterministic graph structure
- never mutate source state

This service should be the semantic heart of the milestone.

### Step 4 — Start with strategic core only

Do not try to export the entire mind on day one.

First useful slice:

- entity root
- directives
- projects
- objectives
- concerns
- blockers
- leads
- obligations
- contracts
- current project/objective edges

That already gives you a graph worth testing.

Then expand carefully to:

- candidate zones / hypotheses
- turning points
- selected beliefs
- selected place attachments
- maybe social relation anchors when clearly relevant

You do not need total exhaustiveness for Phase 6. You need canonical coverage of the most important stored cognition structures.

### Step 5 — Add deterministic mapping rules

You need hard mapping rules like:

- one node per persisted record ID
- root entity node always first
- node sort order by kind, then stable ID
- edge sort order by kind, then source, then target
- edge kinds fixed by domain relationship
- labels derived deterministically from typed fields

Do not leave any of this implicit.

### Step 6 — Add delivery surfaces

Once the service works, expose it through one or more surfaces:

- code-level export function for tests
- optional API endpoint
- optional CLI output file
- optional debug/inspector summary

The service comes first. Delivery comes second.

### Step 7 — Add regression hooks

Now wire the export into testing:

- seed-based export snapshot tests
- structural invariant tests
- comparison with replay summary where overlap exists
- end-to-end tests in later milestone

This is where Milestone 6 becomes more than introspection. It becomes a proof surface.

---

## What the implementation should probably look like

## A. Dedicated graph schema module

Create typed graph output models. Do not use loose dicts.

This matters because the whole point of Milestone 6 is to create a **canonical** artifact. Loose dict assembly invites drift and undocumented inconsistencies.

## B. Dedicated exporter service

Keep export logic out of presenter code.

Presenters are for consumption formatting.
Exporters are for canonical structural derivation.

If you mix them, you will end up optimizing the export around UI convenience instead of truth.

## C. Small domain mappers

Do not write one massive `export_entity()` monster.

Create small mapping helpers, for example:

- `_map_directives(...)`
- `_map_projects(...)`
- `_map_concerns(...)`
- `_map_leads(...)`
- `_map_contracts(...)`
- `_map_turning_points(...)`

That will make later extension survivable.

## D. Optional caching only after determinism is proven

You mentioned “store if not stored yet.”

Be careful. The right default is:

- derive from persisted entity state
- optionally cache by `(entity_id, tick)` at the delivery layer

Do **not** add a second permanent domain store for the graph unless you have a very strong reason. The graph is a view, not the truth.

---

## TDD sequence for Milestone 6

Use this order.

### Test batch A — empty and minimal exports

Write failing tests that prove:

- empty strategy exports valid root-only or minimal graph
- minimal populated strategy exports directives/projects correctly
- export is deterministic

Then implement graph schema and exporter skeleton.

### Test batch B — strategic core coverage

Write failing tests that prove:

- projects and objectives become nodes
- current project and current objective become explicit edges
- concerns, blockers, leads, obligations, and contracts appear when present
- absent structures do not create fake nodes

Then implement strategic core mapping.

### Test batch C — non-mutation guarantees

Write failing tests that prove:

- export does not mutate source entity
- export does not reorder source lists
- export does not fill missing fields back into entity state

Then lock export to read-only semantics.

### Test batch D — extended context mapping

Write failing tests that prove:

- turning points or major memories can appear as graph nodes if included
- relevant belief targets can appear without exploding graph size
- place attachments or contract-linked members can appear when relevant

Then add carefully bounded expansion.

### Test batch E — delivery surfaces

Write failing tests that prove:

- API or file export returns canonical graph format
- CLI or debug access path returns the same structure as direct service call
- same source state through different surfaces gives identical export

Then add API/CLI integration.

That is the right sequence because it locks truth shape first, then coverage, then safety, then delivery.

---

## Suggested file targets

Likely new or changed files:

- `src/core/models/cognition_graph.py`
- `src/core/logic/cognition_graph_exporter.py`
- `src/api/schemas/...` if API-specific wrappers are needed
- `src/api/routes/...` if you add an endpoint
- `src/ui/cli/...` if you add file export or command output
- `src/utils/replay.py` only if you add references or parity checks
- presenter/inspector modules only for visibility hooks

Suggested tests:

- `tests/core/test_cognition_graph_schema.py`
- `tests/core/test_cognition_graph_exporter.py`
- `tests/core/test_cognition_graph_non_mutation.py`
- `tests/api/test_cognition_graph_endpoint.py`
- `tests/cli/test_cognition_graph_export_cli.py`

---

## Definition of done for Milestone 6

Milestone 6 is done only when all of this is true:

- there is a canonical typed cognition graph schema
- an exporter can derive that graph from persisted entity state
- export is deterministic
- export is read-only
- core strategic structures are represented as nodes and edges
- current continuity state is explicitly visible
- tests can consume the graph directly
- delivery surfaces return the same canonical structure

If the export is just presenter JSON, you failed.
If the export mutates state, you failed.
If the export shape depends on caller or ordering accidents, you failed.
If the export does not make project continuity and blockers visible, you failed.

---

## Milestone 6 checklist

- [x] Add failing tests for valid export of empty or minimal entity cognition state

- [x] Add failing tests for deterministic export from identical source state

- [x] Add failing tests proving export does not mutate entity state

- [x] Add failing tests proving current project and current objective appear explicitly

- [x] Add failing tests for exporting concerns, blockers, leads, obligations, and contracts when present

- [x] Add failing tests proving absent optional structures do not create fake graph artifacts

- [x] Add failing tests for identical graph output across direct service/API/CLI access paths where implemented

- [x] Create a canonical cognition graph schema module

- [x] Add `CognitionGraph` model

- [x] Add `GraphNode` model

- [x] Add `GraphEdge` model

- [x] Define stable node fields

- [x] Define stable edge fields

- [x] Define graph metadata fields such as `entity_id` and `tick`

- [x] Keep schema typed and deterministic

- [x] Create a dedicated cognition graph exporter service/module

- [x] Make exporter derive graph from persisted entity state only

- [x] Keep exporter read-only

- [x] Prevent exporter from becoming a second source of truth

- [x] Add deterministic node ID rules

- [x] Add deterministic edge ID or edge ordering rules

- [x] Add deterministic overall sort/order rules

- [x] Map root entity into graph

- [x] Map directives into graph nodes and ownership edges

- [x] Map projects into graph nodes and ownership edges

- [x] Map objectives into graph nodes and project linkage edges

- [x] Map current project and current objective into explicit continuity edges

- [x] Map concerns into graph nodes and generation/context edges

- [x] Map blockers into graph nodes and blocked-by edges

- [x] Map leads into graph nodes and informed-by or candidate edges

- [x] Map obligations into graph nodes and binding edges

- [x] Map contracts into graph nodes and social linkage edges

- [x] Add bounded support for candidate zones and/or hypotheses

- [x] Add bounded support for turning points or major interpreted events where useful

- [x] Add bounded support for selected belief targets where useful

- [x] Avoid exploding graph size with every possible low-value node

- [x] Implement deterministic labels and attribute shaping for nodes

- [x] Implement deterministic labels and attribute shaping for edges

- [x] Keep export format compact enough for regression use

- [x] Keep semantics rich enough for reasoning and debugging

- [x] Add code-level export access path for tests

- [x] Add API endpoint or response path if needed

- [x] Add CLI/file export path if needed

- [x] Ensure all delivery surfaces return the same canonical structure

- [x] Add optional cache keyed by entity and tick only if necessary

- [x] Keep caching outside the domain truth layer

- [x] Extend inspector/debug tooling to reference or summarize exported cognition graph if useful

- [x] Keep visibility structural rather than decorative

- [x] Ensure graph export can be diffed easily in tests or debug workflows

- [x] Add deterministic unit tests for graph schema validation

- [x] Add deterministic unit tests for exporter core mapping

- [x] Add deterministic unit tests for non-mutation guarantees

- [x] Add deterministic integration tests for export coverage of strategic continuity

- [x] Add deterministic tests for parity across delivery surfaces

- [x] Confirm milestone definition of done with passing automated tests

Priority Plan

What you must change in mindset or assumptions:
Stop treating observability as a side concern. At this stage, observability is the proof that the strategic system is real.

What actions you must take immediately:
Write determinism and non-mutation tests first, then define the graph schema, then implement the exporter service, then expose it through one or more delivery surfaces.

What you must stop or eliminate:
Stop relying on scattered presenter output as your source of truth. Stop allowing ad hoc export shapes. Stop building visibility layers that silently invent or repair data.

The consequences and opportunity cost if you fail to change:
You will have a complex internal system that still cannot prove its own state coherently. That means weak regression testing, weaker debugging, and a much higher chance that “thinking” is only convincing until the moment you need to verify it.
