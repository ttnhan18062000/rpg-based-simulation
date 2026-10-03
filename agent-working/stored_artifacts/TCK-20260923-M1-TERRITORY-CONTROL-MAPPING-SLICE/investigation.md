---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE
artifact_type: investigation
tags: [architecture, schema, registry, world]
---

# Investigation — TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE

## Current Behavior

### The four real TERR Rules (`docs/world_rules/places-culture/territory-control.md`)

- **TERR-01** (`:27`) — claim/de-facto-control/jurisdiction/ownership/occupation/cultural-
  association/residence are seven distinct relation types; none silently implies another where a
  domain models more than one. Doc's own "Repository evidence" (`:56-89`) already gives a verdict:
  **CONFLICTING** for control/sovereignty and the contested-claim case; **MISSING** for cultural
  association and residence specifically.
- **TERR-02** (`:100`) — control requires a real, declared causal basis (presence, administrative
  reach, military capability, institutional enforcement, resource access, connectivity, local
  compliance); a bare `faction.owner_id = region` assignment is never itself control. Doc's own
  verdict (`:116-123`): **PARTIAL** — "the *assignment itself* was not confirmed to trace to any of
  this Rule's own named causal bases... not exhaustively traced this batch." That exhaustive trace
  is what this investigation adds (see below).
- **TERR-03** (`:130`) — claim ≠ control; contested/divergent facts must remain representable, not
  collapsed to one winner. Doc's own verdict (`:146-162`): **CONFLICTING**, same root cause as
  TERR-01 (the single `owner_faction_id` slot forecloses ever representing a second, diverging
  relation).
- **TERR-05** (`:170`) — a Place may lie inside/span/remain culturally associated with a territory
  other than its current controller; territory ≠ settlement ≠ Region geometry. Doc's own verdict
  (`:186-190`): **PARTIAL** — `RegionState.places` confirms the containment half; no mechanism
  confirmed for the cultural/historical-association-survives-control-change half.
- **TERR-04** does not exist as a heading. Confirmed directly: `territory-control.md` has no
  `## TERR-04` line; `grep -c '^## TERR-04'` returns 0. The inline citation at `:30` ("jurisdiction
  ... see TERR-04") is stale — jurisdiction was admitted as an Inherited entry (`:217-239`, no local
  ID by the Catalog's own admission discipline), not a new Domain Rule. `tools/semantic_control_
  plane/rule_catalog.py::scan_rule_ids()`'s own heading regex
  (`^## ([A-Z]{2,8}-[0-9]{2})\b`, `rule_catalog.py:27`) will correctly never resolve `TERR-04` —
  this is the validator behaving correctly, not a coverage gap. Not fixed here (frozen doc; tracked
  separately as `TCK-20260923-TERR01-STALE-JURISDICTION-CITATION`, per the ticket's own Out of
  Scope).

### `RegionState.owner_faction_id` — the overloaded slot (`src/core/state.py:282`)

`owner_faction_id: Optional[int] = None  # Faction that currently controls the region`. Sibling
field `PlaceState.owner_faction_id` (`src/core/state.py:360`) carries the comment `# Sovereignty
override; defaults to the parent Region's`. Both are confirmed live-read as more than one concept
by direct grep of every read/write site (`grep -rn "owner_faction_id" src/`, 30+ hits across
`src/world/`, `src/engine/`, `src/systems/`, `src/api/`):

- **De facto control / taxation authority**: `src/engine/town_resolution.py:65,128-170` reads
  `region.owner_faction_id` to gate tax collection and combat-penalty (`suppression_active`)
  checks against faction affiliation.
- **Sovereignty**: `PlaceState.owner_faction_id`'s own field comment (`src/core/state.py:360`)
  names it exactly this, third concept, same field shape.
- **Metrics/replay aggregation**: `src/engine/metrics.py:42-43`,
  `src/replay/fingerprint.py:89` both fold `owner_faction_id` into faction-power and determinism
  fingerprints as if it were the single source of truth for "who owns this."

This directly confirms `territory-control.md`'s own CONFLICTING verdict for TERR-01/TERR-03 —
independently reproduced by direct code read, not merely trusted from the doc's citation.

### `FactionInfluenceService` — the real sovereignty-mutation binding (`src/world/influence.py`)

`registries/mechanisms.yaml:1971-1998` (`regional_sovereignty`, `state: done`,
`verified.instrument: code_trace`, `verdict: observed`) binds correctly to
`src/world/influence.py::FactionInfluenceService`, **not** the plausible-but-dead
`RegionalSovereigntyService` (`src/world/regional_sovereignty.py`, confirmed zero real callers
anywhere in `src/` by the registry's own prior correction — re-confirmed here by grep, no hit
outside its own file and tests). Do not re-introduce that binding.

`FactionInfluenceService.process_influence_shift()` (`src/world/influence.py:32-74`):
accumulates a per-region `influence_deltas` dict from real entity deaths (`+5.0`/`-5.0` per death
depending on protector/invader faction affiliation, `DEATH_INFLUENCE_SHIFT = 5.0`), then, only once
the accumulated `region.influence` crosses `CONQUEST_THRESHOLD = -50.0` or
`LIBERATION_THRESHOLD = 50.0` (`influence.py:28-30,65-70`), writes
`owner_faction_id_set`. This is gated by accumulated combat-death evidence, not a bare assignment.

**Second, independent writer of the same field with a different threshold**:
`src/engine/world_dynamics.py::WorldDynamicsSystem.resolve_dynamics()` (`:60-90`) re-implements a
structurally similar but numerically different ownership-transition check on the same
`region.influence` value — thresholds `>= 100.0` / `<= -100.0` (`world_dynamics.py:78-87`), not
`FactionInfluenceService`'s own `±50.0`. Both write `owner_faction_id_set` on the same field from
the same underlying `influence` quantity, under different threshold laws. Not chased further here
(out of scope — no code fix in this ticket), but recorded as a real finding: the "declared causal
basis" for TERR-02 is not even a single internally-consistent implementation.

### `RegionalConsequenceService` — `regional_trauma` (`src/world/consequences.py`)

`process_recovery()` (`:12-51`) implements passive trauma decay (`new_trauma = max(0.0,
region.trauma_score - 0.0005)`) and stability recovery, confirmed real caller at
`src/engine/apply_plan.py:101` per the registry's own binding note
(`registries/mechanisms.yaml:1948-1970`). `state: done`, `verified.instrument: corpus_run`,
`verdict: contradicted`, date `2026-09-17` — the Lair region specifically never accumulates
trauma in a real corpus run. **Applying the STARVED/REACH-LIMITED/genuinely-broken convention
(`docs/plans/status_axis_model.md` §4) to this note**: the note text itself (`registries/
mechanisms.yaml:1959-1967`, "correct, wired code, defeated by real-world data (no combat occurs in
that region) never meeting the accumulation precondition") already describes **STARVED**, not
REACH-LIMITED or genuinely-broken — the mechanism is correct and would fire under real combat
conditions, but the Lair region's actual gameplay never supplies the precondition. Confirmed, not
assumed.

### `city` mechanism (`registries/mechanisms.yaml:2327-2350`)

`state: partial`, bound to `src/core/state.py::RegionState` (the class itself, not a service) — "a
City is not its own class... City-state IS `RegionState`." Depends on `regional_sovereignty`
(edge CONFIRMED KEEP). `RegionState.places` (`src/core/state.py:294-297`, Idea 66) is the same
class's own structural field confirming TERR-05's containment half.

### `settlement_capacity_axis` (`registries/mechanisms.yaml:2428-2437`)

`state: gap`, zero implementing code anywhere in `src/` (confirmed by the registry's own prior
edge-resolution pass, and re-confirmed here — no `settlement_capacity` symbol found in `src/`).
No TERR-Rule evidence connects to it during this investigation. Per the ticket's own instruction
and `architecture.md` §7, this should map to no edge at all (`UNKNOWN`), not a forced one.

### The FAC-010 lead — CONFIRMED as real, second, independent evidence

`src/engine/military_conflict.py::MilitaryConflictPhase.execute()` (docstring `:155-165`):
> "Note on owner_faction_id: `RegionState.owner_faction_id` is `Optional[int]` while
> `FactionState.faction_id` is `str`. Authoritative ownership is `FactionState.territory` (updated
> via `FactionUpdate.territory_add`/`remove`). `RegionState.owner_faction_id` is **NOT** set during
> transfer (documented in FAC-010)."

`docs/parity_ledger/faction.yaml:227-242`, entry `FAC-010`, `status: verified`, `priority: P1`,
confirms this in full: on siege completion (`siege_progress >= 1.0`),
`MilitaryConflictPhase.execute()` emits `FactionUpdate(territory_add/territory_remove)` and a
`TERRITORY_TRANSFERRED` WorldEvent — but never touches `RegionState.owner_faction_id`. The two
ownership representations (`RegionState.owner_faction_id: Optional[int]` vs.
`FactionState.territory: Set[str]`) diverge on every real siege-driven conquest.

This is a genuinely **second, structurally distinct** piece of CONFLICTING evidence, independent
of the already-documented "one field serves three concepts" finding: here it is two *different*
fields/representations of the same "who controls this region" fact that go out of sync through a
real, live code path (siege/territory-transfer, `betrayal_siege_war` mechanism,
`registries/mechanisms.yaml:1804-1826`, `state: partial`, siege-war half confirmed real/live).
This strengthens, and does not merely repeat, TERR-01/TERR-03's CONFLICTING classification, and
should be cited as its own evidence line in the `rule_mechanism_edges.yaml` rows for TERR-01/
TERR-03 (mechanism_id: `betrayal_siege_war`), separate from the `regional_sovereignty` edge.

### TERR-02's genuinely-open axis — SUPPORTED, with caveats (evidence-backed determination)

The ticket's own framing: does `FactionInfluenceService` supply a genuine causal requirement, or
merely write the ownership field? Confirmed by direct code read (`influence.py:32-74`, see above):
**a real causal-basis mechanism exists** — ownership only changes once accumulated in-region
combat-death evidence crosses a threshold, which is a real (if narrow) proxy for TERR-02's own
"military capability" causal basis, not a bare `faction.owner_id = region` assignment with zero
grounding. TERR-02 explicitly permits partial/single-basis coverage ("No domain is required to
check every one of these for every case").

**Caveats that keep this a narrow SUPPORTED, not a clean one:**
1. **World-generation-time initial assignment bypasses the causal basis entirely.**
   `src/worldbuilding/compiler.py:415,446` sets `RegionState.owner_faction_id` directly from the
   world spec's own declared `owner_faction_id` (`src/worldbuilding/schema.py:54`,
   `src/worldbuilding/recipe.py:33`) — a bare, declarative assignment, exactly the "assignment
   alone never constitutes control" shape TERR-02 forbids, for every region's *starting* state.
   Only post-generation transitions (conquest/liberation) go through the causal accumulation.
2. **Two live, mutually-inconsistent threshold implementations** (`FactionInfluenceService` ±50.0
   vs. `WorldDynamicsSystem` ±100.0, see above) both claim to gate the same causal-basis check.
3. TERR-02's own doc text (`:116-123`) still reads PARTIAL because the batch that wrote it did not
   exhaustively trace the assignment path — this investigation's own trace is new evidence beyond
   what the doc currently states, and should be recorded as such in the edge's `evidence` field
   rather than silently overriding the doc.

**Recommendation for the M1 mapper**: `TERR-02` → `PARTIALLY_REALIZES` `regional_sovereignty`
(the causal-basis mechanism is real for conquest/liberation, but does not cover initial
world-generation assignment, and has two inconsistent thresholds) is the evidence-backed edge; the
Rule-level classification in `rule_classifications.yaml` is the mapper's own judgment call, not
mechanically derived here (per `architecture.md` §3/§4's "declared, not derived" discipline) —
this investigation supplies the evidence, not the verdict.

### TERR-05 — has a real partial mechanism, not zero

The containment half (`RegionState.places` / `PlaceState.region_id`, Idea 66) is real, live,
structural data — genuinely realized, mappable as `city` → `PARTIALLY_REALIZES` TERR-05. The
cultural/historical-association-survives-control-change half has **zero implementing code**:
`PlaceState` (`src/core/state.py:344-383`) carries no field for it — `prior_kind`/
`transformed_tick` (`:365-367`) is a Place-*kind* transformation trail (City→Ruin), not an
association-with-a-polity fact, and nothing else in `src/` reads or writes such a concept.
**MISSING is the correct, evidenced call for this half** — not UNKNOWN (this was actually
investigated and confirmed absent) and not invented into an edge.

## Mechanics / Engine Constraints

- `docs/plans/simulation_semantic_control_plane/architecture.md` §3: Rule↔Mechanism mapping is
  many-to-many, typed (`REALIZES`/`PARTIALLY_REALIZES`/`CONSTRAINED_BY`), never a Cartesian
  product — record only real, investigated relationships; everything else stays `UNKNOWN`.
- §4: Rule realization classification (`SUPPORTED|PARTIAL|CONFLICTING|MISSING|INERT-OFF|UNKNOWN`)
  is a separate, declared human judgment, never mechanically derived from the edge list —
  `tools/semantic_control_plane/registry.py`'s own `validate_rule_classifications()` docstring and
  `test_no_function_derives_classification_from_edges` (`tests/unit/tools/
  test_semantic_control_plane_schema.py:387-400`) enforce this by construction.
- §7: `UNKNOWN` is permanent and expected, never coerced to `MISSING`. `settlement_capacity_axis`
  (gap, zero code) is the textbook case this investigation confirms should stay unedged rather
  than forced.
- §8: the six management-view axes (DESIGN, REALIZATION, IMPLEMENTATION, VERIFICATION,
  INTEGRATION, OBSERVED OUTCOME, `architecture.md:212-220`) must render independently, never
  averaged into one score, and must show `mapped`/`unmapped` + `verified`/`unverified` counts
  (§7, reused directly for AC 6).
- `docs/plans/status_axis_model.md` §1 (Axis D, Rule-semantic realization) and §4 (the STARVED/
  REACH-LIMITED/genuinely-broken prose convention, applied above to `regional_trauma`).

## Docs Requiring Update

None.

Two doc paths were genuinely considered and excluded, not silently skipped:

`docs/world_rules/places-culture/territory-control.md` was considered because this investigation's
own code trace produces evidence (the TERR-02 causal-basis trace, the FAC-010 second-desync
finding) beyond what the doc's existing "Repository evidence" prose currently states. It is not
required to change for this ticket: the ticket's own Scope is explicit that "the frozen Catalog's
own §'Implementation Candidates — Non-Binding' prose... is M3 ingestion input," and the doc itself
is frozen/Batch-11A-authoritative — updating it is a separate, later (M3) concern, not this
mapping-slice ticket's job. The new evidence belongs in `registries/rule_mechanism_edges.yaml`'s
own `evidence` fields, not a doc edit here.

`docs/parity_ledger/faction.yaml` (path: `docs/parity_ledger/faction.yaml`, under `docs/`) was
considered because FAC-010 is now directly cited as evidence in this ticket's own mapping output.
It is not required to change: FAC-010 already reads `status: verified` and already documents
exactly the fact this ticket cites — this ticket makes no `src/` change and finds no new behavior
to record against it, only reuses its existing, already-correct entry as a citation. Confirmed per
the ticket's own Out of Scope ("Any CI wiring" / no code fix) and the general parity-ledger rule
(update only when a behavior changes) — no behavior changed here.

## Parity Ledger Overlap

- **`FAC-010`** (`docs/parity_ledger/faction.yaml:227-242`), `status: verified`, `priority: P1`.
  Directly cited as evidence for TERR-01/TERR-03's CONFLICTING classification (the
  `RegionState.owner_faction_id` vs. `FactionState.territory` desync). No status change needed —
  this ticket reuses, does not alter, this entry. Its own `test_path` was not independently
  re-run here (out of scope — this ticket makes no `src/` change); flagged for the mapper to keep
  in mind if a future ticket touches `military_conflict.py`.
- No other `docs/parity_ledger/*.yaml` entries were found to overlap TERR-01/02/03/05 specifically
  by a targeted grep of `town_resource.yaml`/`world_dynamics.yaml` for `owner_faction_id`/
  `sovereignty`/`territory` beyond FAC-010 itself; a full cross-ledger sweep was not performed
  (out of this investigation's scope — the ticket's Related Docs list only names FAC-010's family
  via the Scope-phase lead, not a general parity audit).

## Prior Work

- `stored_artifacts/TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION/{investigation,plan,test_plan}.md`
  — built the three empty schemas and `tools/semantic_control_plane/registry.py` this ticket
  populates. Confirmed all three registries (`rule_mechanism_edges.yaml`,
  `rule_classifications.yaml`, `mechanism_causal_edges.yaml`) are still genuinely empty
  (`edges: []` / `classifications: []`) going into this ticket.
- `stored_artifacts/TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC/{plan,investigation,test_plan}.md` —
  parent epic.
- `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` — source of the mapped/unmapped +
  verified/unverified counts requirement now AC 6.
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (DONE) — precedent for recording a
  measured-but-deliberately-unfixed behavior (`tactical_decision`'s own STARVED-shaped note),
  directly analogous to `regional_trauma`'s own STARVED note applied here.
- The generated-view precedent (`docs/brainstorm/mechanism_system_rollup_view.md` +
  `tools/mechanism_registry/generate_mechanism_system_rollup_view.py`, wired via a `Makefile`
  target — `mechanism-system-rollup-view`, `Makefile:358` — and a `--check`/`--output` CLI shape)
  is the pattern reused for the Territory-only view.

  **Chosen path/format (M1's own open decision, resolved here):**
  `docs/brainstorm/territory_control_management_view.md`, generated by a new
  `tools/semantic_control_plane/generate_territory_control_view.py`, following the exact same
  three conventions the precedent already establishes: (1) a "Generated from ... — regenerate
  with `make territory-control-view`. Do not hand-edit." banner: (2) counts only, never a single
  collapsed badge, per `architecture.md` §8's own "never averaged into one score"; (3) an
  `--output PATH` flag for test isolation and a `--check` flag for staleness detection, matching
  `generate_mechanism_system_rollup_view.py`'s own CLI shape exactly. Placed in
  `docs/brainstorm/` (not `docs/plans/simulation_semantic_control_plane/`) because every existing
  generated-registry view in this repo already lives there alongside its hand-maintained peers
  (`mechanism_system_rollup_view.md`, `mechanism_verification_view.md`) — `docs/plans/` is reserved
  for hand-authored design/rollout docs, not generated output, and mixing the two there would
  break the same "which files are safe to hand-edit" signal `docs/brainstorm/`'s own placement
  already protects. A new `Makefile` target (`territory-control-view`) should be added alongside
  `mechanism-system-rollup-view`/`mechanism-verification-view` (`Makefile:349-365`), not folded
  into an existing target, since it renders a structurally different (per-Rule, six-axis, not
  per-system) rollup, reusing `tools/semantic_control_plane/registry.py` + `rule_catalog.py` as
  its own data source rather than `tools/mechanism_registry/registry.py`.

## Risks and Open Questions

- **TERR-02's classification (SUPPORTED vs. PARTIAL vs. MISSING) is evidence-backed here but not
  decided here.** This investigation confirms a real causal-basis mechanism exists (narrowing the
  question from "does one exist at all" to "how complete is it"), but the final
  `rule_classifications.yaml` value is the mapper's own human judgment per `architecture.md` §3/§4
  — do not read this investigation's "SUPPORTED, with caveats" language as pre-deciding the
  classification field; it is evidence for that decision, which AC 3 requires stay a visible
  judgment, not a mechanical roll-up.
- **The `FactionInfluenceService` (±50) vs. `WorldDynamicsSystem` (±100) dual-threshold
  inconsistency is a real, live bug-shaped finding**, out of this ticket's own scope to fix
  (Out of Scope: "Resolving the TERR-01/TERR-03 vs. `owner_faction_id` conflict in code"). Record
  it as evidence, not as something to patch here — flagging for whoever next touches
  `regional_sovereignty`/`betrayal_siege_war`.
- **Where the FAC-010 evidence should be attached**: recommend citing it on TERR-01/TERR-03 edges
  against `mechanism_id: betrayal_siege_war` (distinct from the existing `regional_sovereignty`
  edge), since it is a structurally separate desync mechanism, not a restatement of the same one.
  This is a mapping-detail recommendation, not a settled fact — the mapper should confirm this
  reads correctly against `architecture.md` §3's edge-typing guidance before committing it.
- **No blocking M0 schema friction was found in this investigation pass.** Every real fact traced
  above (TERR-01/02/03/05's evidence, the FAC-010 second-desync finding, the STARVED note
  convention) fits the existing three-schema shape without a field addition. One soft
  representational gap is worth flagging, not fixing: `mechanism_causal_edges.yaml`'s
  `producer_mechanism_id`/`consumer_mechanism_id` shape models "A produces input for B," which
  does not cleanly describe "`regional_sovereignty` and `betrayal_siege_war` independently,
  inconsistently write the same durable field" (a conflict/duplication relation, not a producer→
  consumer one). Recommend the mapper record this in an edge's free-text `evidence` field rather
  than force it into a causal-edge row, and treat this as AC 7's "explicitly deferred with a
  reason" case if the mapper agrees no schema change is warranted for one soft-fit case.

## Anti-Drift Hazards

- **Do not re-introduce the `RegionalSovereigntyService` binding.** It has zero real callers
  anywhere in `src/`, confirmed independently here by grep, matching the registry's own prior
  correction (`registries/mechanisms.yaml:1991-1998`). Any edge citing `regional_sovereignty`
  must point at `FactionInfluenceService` evidence, never `RegionalSovereigntyService`.
- **Do not fix the `owner_faction_id` overload, the FAC-010 desync, or the ±50/±100 threshold
  mismatch as part of this ticket.** All three are real findings to *record*, per the ticket's own
  Out of Scope — a mapping slice that quietly patches the underlying conflict while mapping it
  would violate the ticket's own explicit scope boundary.
- **Do not classify Rules while writing edges in the same pass** — the ticket's own Implementation
  Notes sequencing hint (classify only after all edges are laid down) exists specifically to
  prevent the classification silently becoming a mechanical roll-up of the edge list, the exact
  failure `test_no_function_derives_classification_from_edges` guards against in code.
- **Do not force an edge for `settlement_capacity_axis`** — zero implementing code, confirmed
  here; any TERR mapping row citing it needs real, not inferred, evidence.
- **Do not invent a cultural-association/residence mechanism for TERR-01 or TERR-05's own MISSING
  halves** — both are confirmed, evidenced absences (`PlaceState` has no such field), not merely
  unlooked-at gaps; forcing an edge here would misuse `UNKNOWN`'s "not yet looked at" semantics for
  something that was, in fact, looked at and found absent.
