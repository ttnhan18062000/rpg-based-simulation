---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP
artifact_type: plan
tags: [simulation-quality, world, adventure, bug]
---

# Plan: TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP

Phase timestamp: 2026-07-06T15:27:41Z

## 0. Decisions carried in from orchestrator (not re-litigated here)

1. Fix **both** `wood_node` and `herb_patch` (additive `source_region_tags`), not just one.
2. File two new standalone follow-up tickets now (this session, as part of Plan/scoping output):
   - `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP` (bug, P2) — see §6a.
   - `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT` (chore, P2) — see §6b.
3. Scope guards: no `ResourceNodeState` region field, no `urban_political` calibration-profile/flag
   change, no direct corpus-wide fix — all three deferred to the follow-ups above or explicitly out
   of scope.

## 1. Exact catalog edit — `data/content/world/resources.yaml`

Both edits are **additive only** (append `"hometown"` to the existing tuple/list; never replace),
using the `metadata.source_region_tags` override mechanism already established by `stone_outcrop`
(`TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`). This is the only lever that changes gating — the
sibling `preferred_biomes` field is a different, un-consulted schema field for these two kinds today
(confirmed live in investigation.md §1a: `res.metadata` is `{}` for both entries pre-fix, so gating
currently falls through to the hardcoded legacy-heuristic branch, not `preferred_biomes`).

**`wood_node`** (current, lines 1-8):
```yaml
# STATE: EXISTING-LOGIC
- id: "wood_node"
  material: "wood"
  display_name: "Wood Node"
  resource_type: "wood"
  required_ticks: 10
  default_charges: 10
  preferred_biomes: ["frontier_village", "near_forest"]
```
New:
```yaml
# STATE: EXISTING-LOGIC
- id: "wood_node"
  material: "wood"
  display_name: "Wood Node"
  resource_type: "wood"
  required_ticks: 10
  default_charges: 10
  preferred_biomes: ["frontier_village", "near_forest"]
  metadata:
    source_region_tags: ["near_forest", "hometown"]
```
(Live-projected pre-fix tags were `("near_forest",)` only — confirmed in investigation.md §1;
`"frontier_village"` from `preferred_biomes` was never actually live despite being a sibling key,
because branch 2 of the adapter's precedence never fires without an explicit `metadata:` nest. The
new `metadata.source_region_tags` is additive over the *live* pre-fix set, not over
`preferred_biomes`.)

**`herb_patch`** (current, lines 31-38):
```yaml
# STATE: LEGACY-EXPORT
- id: "herb_patch"
  material: "herb"
  display_name: "Herb Patch"
  resource_type: "herb"
  required_ticks: 8
  default_charges: 8
  preferred_biomes: ["near_forest", "sunken_swamp"]
```
New:
```yaml
# STATE: LEGACY-EXPORT
- id: "herb_patch"
  material: "herb"
  display_name: "Herb Patch"
  resource_type: "herb"
  required_ticks: 8
  default_charges: 8
  preferred_biomes: ["near_forest", "sunken_swamp"]
  metadata:
    source_region_tags: ["near_forest", "moon_cave", "hometown"]
```
(Live pre-fix tags were `("near_forest", "moon_cave")` — confirmed in investigation.md §1.)

Keep each entry's original `# STATE: ...` provenance comment unchanged (`EXISTING-LOGIC` /
`LEGACY-EXPORT`) — those track original-authoring lineage, not this edit; git blame + the
`intentional_divergences.md` entry (§5 below) carry the fix's own provenance. Do **not** touch
`preferred_biomes` on either entry (it remains dead for gating purposes, consistent with every other
non-`stone_outcrop` entry in the file; changing that fallback-precedence behavior generally is out of
this ticket's scope).

## 2. Recompile / pick-up confirmation

`data/content/world/resources.yaml` is global catalog content, not per-world. `tools/calibrate_simq.py`
loads each world's pre-resolved `data/worlds/{name}/resolved/world.resolved.yaml` and calls
`WorldCompiler.compile(spec, seed)` **fresh in-process on every invocation** (confirmed:
`tools/calibrate_simq.py:109-138`) — which re-bootstraps `CatalogRepository("data/content").load_all()`
→ `CatalogToResourceRegistryAdapter.adapt()` each run. There is therefore no separate "recompile the
world" step distinct from re-running calibration — no `.pyc`/registry singleton survives across
process invocations that would need busting.

Steps:
1. Live read-only check (no calibration run needed) — reuse investigation's method: run
   `CatalogRepository("data/content").load_all()` → `CatalogToResourceRegistryAdapter.adapt()`
   in-process and assert `resources["wood_node"].source_region_tags` and
   `resources["herb_patch"].source_region_tags` both include `"hometown"` and retain their prior
   entries. This is Test Plan step 1 (§7 below), run first as a fast correctness gate before any
   full calibration.
2. Compile `simq_routing_test`'s resolved spec via `WorldCompiler.compile()` for each of seed
   42/123/456 (read-only inspection, no calibration harness yet) and confirm: still exactly 5
   resource node instances (no count regression — `res_0`/`res_1`/the 3 `old_mine` nodes), and a
   synthetic hero entity placed at `navigation.region_id="hometown"` now receives a non-empty
   `ResourceOpportunityProvider.get_opportunities()` result naming `wood_node` and/or `herb_patch`.
3. Confirm `urban_political`'s resolved spec picks up the same catalog change automatically (read-only
   check only): compile `urban_political`'s resolved spec, confirm its `hometown`-placed
   `wood_node`/`herb_patch` nodes (per `docs/parity_ledger/town_resource.yaml` TOWN-183) also now
   gate correctly. **Do not** enable `ENABLE_ADVENTURE_ROUTING` for `urban_political`, edit its
   calibration profile, or run a new calibration for it as part of this ticket — the dormant-gap
   confirmation is read-only evidence for this ticket's Completion Summary and for
   `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP` (§6a), nothing more.

## 3. Calibration re-run — all 3 seeds, live-verified (not assumed)

Per the ticket's own Acceptance Criteria and the STONE-GAP/AGENCY-STASIS-COLLAPSE precedent of
always live-verifying "should be inert" claims, do **not** assume seed42/123 are unaffected — run
and check all three.

Clear stale calibration output first (documented append-mode footgun from the
AGENCY-STASIS-COLLAPSE investigation), then re-run:
```
rm -rf data/calibration/simq_routing_test_seed42_500t data/calibration/simq_routing_test_seed123_500t data/calibration/simq_routing_test_seed456_500t

ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 42  --name simq_routing_test
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 123 --name simq_routing_test
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 456 --name simq_routing_test
```

For each seed, inspect the run's `decision_trace.jsonl` / `quality_scores.jsonl` output and confirm:

- **seed42 / seed123**: entity 23 continues to route via `FORM_PARTY` (sociability 0.534 / 0.407,
  both clear the 0.2 gate) — confirm live that its trace does **not** newly show
  `gather_resource` displacing `FORM_PARTY` in a way that changes event counts/timing enough to move
  the AGENCY grade. Expected result: AGENCY stays `A`/`A` and all other 9 pillars are unchanged from
  the current `grade_anchors.json` values (`simq_routing_test_seed42_500t` /
  `simq_routing_test_seed123_500t`). If any pillar drifts, treat it as a real regression signal to
  investigate before closing this ticket — do not silently re-anchor without explanation.
- **seed456**: entity 23 now has `gather_resource` (via `wood_node` and/or `herb_patch` in
  `hometown`) as a legal candidate route at every tick starting tick 1 (both nodes exist from world
  start, not seeded later by ecology). Confirm whether its 491-event `defer_with_reason` streak
  (starting tick 176, per the existing D-grade documented exception) is interrupted or shortened.
  Record the resulting AGENCY grade — **do not assume** it improves; both outcomes are handled:
  - If AGENCY improves (expected, most likely outcome: entity 23 now has a non-`FORM_PARTY` fallback
    for its whole life) → proceed to §4/§5 to re-anchor and update the AC6 documented-exception text
    to reflect closure.
  - If AGENCY does **not** improve (e.g. `gather_resource` is offered but entity 23's decision logic
    still selects `defer_with_reason` for an independent, legitimate reason — e.g. an active
    higher-priority need, or node charge exhaustion before entity 23 ever reaches it) → the anchor
    stays as-is, and §5's doc update records *why* the fix didn't move this seed's grade (which is
    itself a real, useful finding — not a failure of this ticket, since the AC only requires the
    grade be **re-verified**, not necessarily raised).

## 4. `grade_anchors.json` update (conditional on §3's live result)

File: `tests/simulation_quality/fixtures/grade_anchors.json`, key `simq_routing_test_seed456_500t`,
field `"AGENCY"` (currently `"D"`, line ~121).

- If seed456's re-verified AGENCY grade differs from `D`: update this single field to the new grade
  (must be a `GRADE_ORDER` member — `D`/`C`/`B`/`A`/`S`; per `test_grade_regression.py:34`, there is
  still no `F` slot, so if the grade somehow computes as a worse-than-`D` condition, that itself
  would be the surprising result investigation.md's test plan already flags — not silently absorbed).
- If it re-verifies unchanged at `D`: no anchor edit — but the Completion Summary must state the
  live-verification was performed and explain why the new route availability didn't move the grade
  (per §3's second bullet).
- `simq_routing_test_seed42_500t` / `simq_routing_test_seed123_500t` anchors: no edit expected: only
  touch them if §3's live run shows an actual drift (in which case treat as a regression to root-cause
  before editing, per repo's "no silent grade drift" convention established by the STONE-GAP ticket).

## 5. Docs — `docs/simulation_quality/eval_matrix_results.md` AC6 section

This is the third ticket to touch this section's seed456 story (STONE-GAP → established F/D anchor
floor; AGENCY-STASIS-COLLAPSE → scoring-formula fix, F→D, "DOCUMENTED EXCEPTION"; this ticket → the
content fix that exception's own text already anticipated). Do not overwrite prior history — append a
new dated status paragraph, consistent with how the two prior tickets each added their own dated
paragraph rather than editing previous ones.

**Exact new content** (append after the existing "Status as of 2026-07-04
(TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE): DOCUMENTED EXCEPTION." paragraph, i.e. after line 397,
before the `---` / "## AGENCY — Cross-World Design Note" heading):

- If seed456's grade improved to `<NEW_GRADE>`:
  ```
  **Status as of 2026-07-06 (TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP): EXCEPTION CLOSED
  (grade improved).** `wood_node` and `herb_patch`'s `source_region_tags` in
  `data/content/world/resources.yaml` now additively include `"hometown"` (both kinds were already
  physically placed there by `frontier_village_core.yaml`; only the catalog-level gating tag was
  missing — see investigation.md §1a for the root mechanism). Entity 23 in seed456 now has a legal
  `gather_resource` route in `hometown` for its entire life, [interrupting / shortening] its
  491-event `defer_with_reason` streak. Re-verified AGENCY grade: `<NEW_GRADE>` (up from `D`).
  `grade_anchors.json`'s `simq_routing_test_seed456_500t.AGENCY` anchor updated to `<NEW_GRADE>`.
  seed42/seed123 re-verified live (not assumed inert): AGENCY held at `A`/`A`, no regression on any
  of the other 9 pillars. This closes the per-seed legitimate-stasis exception documented above as a
  historical record only — the record itself is retained for traceability (it correctly described the
  state of the world *before* this fix), not deleted or rewritten.
  ```
- If seed456's grade did **not** improve (fallback text, only used if §3 resolves this way):
  ```
  **Status as of 2026-07-06 (TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP): CONTENT GAP
  CLOSED, EXCEPTION RETAINED.** `wood_node` and `herb_patch`'s `source_region_tags` now additively
  include `"hometown"` (see investigation.md §1a). Entity 23 in seed456 now has a legal
  `gather_resource` route available in `hometown`, but its re-verified AGENCY grade remains `D`
  because <live-observed reason — e.g. decision logic still selects defer for an independent reason
  / node charges exhausted before entity 23 reaches them>. The per-seed legitimate-stasis exception
  above therefore remains ACTIVE, now for a narrower, re-confirmed reason. No `grade_anchors.json`
  edit required. seed42/seed123 re-verified live: AGENCY held at `A`/`A`, no regression.
  ```

Also add one bracketed cross-reference at the end of the existing "**Second exception class**"
paragraph under "AGENCY — Cross-World Design Note" (after line 441) pointing to whichever of the two
outcomes above actually occurred, so a reader landing on that note isn't left with only the
now-superseded "even if that lands..." forward-reference.

## 6. Follow-up tickets (filed now, per DECIDED §0.2)

### 6a. `tickets/todos/TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP.md`
Standalone (not in a folder). standard tier, bug type, P2 priority — dormant gap, no observed
failure today (identical root cause to this ticket, but `urban_political`'s shipped calibration
profile does not force `ENABLE_ADVENTURE_ROUTING=ON`, so `AdventureDecisionPhase` never runs there —
per `eval_matrix_results.md`'s "AGENCY — Cross-World Design Note"). Body cites investigation.md §4(i)
verbatim as its evidence trail. Scope: decide + implement whichever of (a) enabling routing for
`urban_political` in a future profile, or (b) explicitly documenting the dormant risk as accepted, is
warranted — this ticket's own fix (§1-§5 above) already closes the *content* half of the gap as a
side effect, so this follow-up is really about the *profile/flag* half plus a live confirmation once
routing is (if ever) turned on for that world.

### 6b. `tickets/todos/TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT.md`
Standalone (not in a folder). standard tier, chore type, P2 priority. Body cites investigation.md §4
(ii) verbatim (the full uncovered-region table across all 10 worlds) as its evidence trail. Scoped
explicitly to "audit + fix-or-decide", not "must fix everything" — including evaluating investigation
§3's rejected option (c) (region-aware `ResourceNodeState` gating) as one candidate long-term
direction, without committing this ticket to that architecture change.

(Both ticket bodies written in full below in §8; this plan's job is to describe them, the actual
files are created alongside this plan during the Plan phase per the orchestrator's explicit
instruction to file them now.)

## 7. Test coverage

Re-run (all currently pass per investigation.md §6's individual-assertion analysis; confirm live,
not just trust the investigation's read-only reasoning):
```
pytest tests/unit/strategic/test_opportunities.py -v
pytest tests/unit/core/test_registry_bridge.py tests/unit/core/test_registry_parity.py -v
pytest tests/unit/content/test_adapter_heuristic_reporting.py -v
pytest tests/integration/content/test_registry_projection_parity.py -v
pytest tests/integration/worldassembly/test_e2e_smoke.py -v
pytest tests/simulation_quality/test_grade_regression.py -v
```

New tests to add, per test_plan.md's Normal Flow steps 1-2:
1. A live catalog-projection assertion (extend `tests/unit/core/test_registry_bridge.py`'s existing
   `wood_node`/`herb_patch` region-tag checks, ~line 355-368 — add `assert "hometown" in
   res_wood.source_region_tags` and `assert "hometown" in res_herb.source_region_tags` alongside the
   existing `"near_forest"`/`"old_mine"` `in` assertions there, rather than a new file, since this is
   exactly the same real-catalog assertion style already established) — additive assertions, not
   replacing the existing ones (preserves the pre-existing near_forest/moon_cave subset checks).
2. A new opportunity-provider test in `tests/unit/strategic/test_opportunities.py`, mirroring
   `test_resource_opportunities_basic`'s pattern: entity in `navigation.region_id="hometown"`,
   `ResourceNodeState(kind="wood_node", ...)`, assert `get_opportunities()` returns a non-empty
   `gather_resource` opportunity list. Add a second parametrized/duplicate case for `herb_patch`.

Both new tests are additive; no existing test's assertions are modified except the additive `in`
checks in item 1.

## 8. Parity ledger check — `docs/parity_ledger/town_resource.yaml`

`TOWN-183` (urban_political resource-node-count entry) remains accurate and is **not** edited — it is
scoped to node *count* being >= 3, not opportunity-gating coverage, and this fix changes neither node
count. However, per the repo's Authoritative Mechanics Rule ("when a behavior changes... if no entry
exists, add one"), this fix **does** change observable behavior (a `hometown`-standing hero now
receives `gather_resource` opportunities where none existed before) and has no existing ledger entry
describing that specific gating fact. Add a **new** entry, `TOWN-188` (next unused ID after
`TOWN-187`), to `docs/parity_ledger/town_resource.yaml`:

```yaml
- id: TOWN-188
  text: >
    wood_node and herb_patch resource nodes placed in the hometown region (by
    frontier_village_core.yaml, used by both simq_routing_test and urban_political) now correctly
    yield gather_resource opportunities for entities standing in hometown.
    ResourceOpportunityProvider.get_opportunities() gates on a global, catalog-wide,
    per-resource-kind source_region_tags allowlist (not the node's own placement region);
    wood_node/herb_patch's catalog entries previously omitted "hometown" from that allowlist despite
    both kinds already being physically placed there, so the gate silently never fired for
    hometown-standing entities of any role.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    data/content/world/resources.yaml — wood_node/herb_patch metadata.source_region_tags now
    additively include "hometown"; src/core/registries.py CatalogToResourceRegistryAdapter.adapt()
    precedence (metadata override > preferred_biomes > legacy_id heuristic); src/world/providers/
    resources.py:69 ResourceOpportunityProvider.get_opportunities() gating check.
  proof_type: parity
  test_path: >
    tests/unit/core/test_registry_bridge.py; tests/unit/strategic/test_opportunities.py
  divergence_note: >
    Content-authoring gap, not a decision-logic or scoring bug: frontier_village_core.yaml's
    resource_recipes already placed both node kinds in hometown (TCK-20260627-P0B-URBAN-RESOURCE-NODES),
    but that placement was never reflected in the global catalog's per-kind gating tags until this fix
    (TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP).
  support_boundary: null
```

Also add a matching `intentional_divergences.md` entry (new `### 2.27` heading, immediately after
`### 2.26 Resource Ecology Kind-Emission Catalog Alignment`) with **Rationale: Bug Fix** — same class
as §2.26's precedent, since this is authoring staleness (a fix landed for placement but never for the
gating tag), not a deliberate design decision:
```
### 2.27 Hometown Resource-Opportunity Gating Fix (TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP)
- **Subsystem**: World / Resource Opportunities
- **Old Behavior**: wood_node/herb_patch's catalog source_region_tags (data/content/world/
  resources.yaml) did not include "hometown", even though frontier_village_core.yaml already placed
  both kinds' nodes there (TCK-20260627-P0B-URBAN-RESOURCE-NODES). ResourceOpportunityProvider gates
  purely on the kind-level catalog allowlist, never on a node's own placement region (ResourceNodeState
  has no region field), so hometown-standing entities never received gather_resource opportunities
  regardless of role or seed.
- **New Behavior**: wood_node's source_region_tags additively gains "hometown" (now
  ["near_forest", "hometown"]); herb_patch's additively gains "hometown" (now ["near_forest",
  "moon_cave", "hometown"]), via the same metadata.source_region_tags override mechanism used for
  stone_outcrop. Purely additive — no other world/region's existing tag coverage changes.
- **Rationale**: **Bug Fix**. The original P0B ticket's evident intent (placing nodes in hometown) was
  never fully realized for opportunity-matching purposes; this closes that gap.
- **Verification**: tests/unit/core/test_registry_bridge.py, tests/unit/strategic/test_opportunities.py
- **Status**: ACTIVE
```

## 9. Corpus regression gate

```
make evaluate --dry-run
```
Confirm 0 regressions across the rest of the corpus (all worlds other than `simq_routing_test`, which
place `wood_node`/`herb_patch` in `near_forest`/`moon_cave`, are unaffected since the edit is purely
additive — investigation.md §3 already enumerates the six other worlds using these kinds:
`frontier_extended`, `frontier_living_world`, `generated_frontier_3_42`, `sandbox_world`,
`swamp_border_world`, `wilderness_survival`). Any non-zero regression must be root-caused before
closing this ticket, not silently re-anchored.

## Unresolved questions

None block this ticket. Both open questions the investigation flagged (OQ-1: `urban_political`'s
side-effect fix; OQ-2: the corpus-wide pattern) are resolved by filing the two follow-up tickets in
§6/§8 above, per the orchestrator's explicit decision — no further human judgment call is needed to
proceed with implementation.

One genuinely open item that does require live evidence (not a decision, a to-be-observed fact): §3's
seed456 outcome (does the grade actually improve, and if so to what letter) cannot be determined
without running the calibration — the plan handles both branches explicitly in §3-§5 rather than
assuming the "improves" branch.

## Deviations (recorded during implementation)

1. **Seed456 outcome matched the "improves" branch, cleanly.** Live re-run: AGENCY `D` → `A`
   (norm +0.6415). `decision_trace.jsonl` for entity 23 shows `gather_resource` selected at every
   one of the 50 logged decision ticks (0, 10, ..., 490) across the 500-tick run — zero
   `defer_with_reason` selections anywhere in the trace. The 491-event streak is fully interrupted,
   not merely shortened. This matches §3's "most likely outcome" bullet exactly; no third outcome
   occurred. §4/§5's "improves" branch text was used verbatim (with `<NEW_GRADE>` = `A`,
   "[interrupting]" chosen over "[shortening]").
2. **Two additional seed456 pillars moved by one grade step each, unanticipated by §3-§5's text**
   (which only discussed AGENCY for seed456 and only discussed "no regression" for seed42/123):
   COGNITION `S`→`A` and NARRATIVE `A`→`S`. Root cause: entity 23's freed decision stream (no longer
   purely deferring) changes the overall event mix that COGNITION's and NARRATIVE's scorers also
   consume. Both moves are within `test_grade_regression.py`'s ±1-letter anchor-band tolerance (only
   AGENCY's 3-step D→A move exceeded the band), so per §4's "single field" instruction only the
   AGENCY anchor was updated — COGNITION/NARRATIVE were left as-is, and the eval_matrix_results.md
   status paragraph added in §5 documents this explicitly so it isn't mistaken for an unexplained,
   silently-absorbed drift later.
3. **§7's premise about `test_registry_bridge.py` (~line 355-368) was factually incorrect.** That
   assertion block runs inside `test_registry_bridge_seeding_catalog(mock_catalog_repo)`, which
   builds a fully synthetic `tempfile.TemporaryDirectory()` catalog (only `wood_node`/`iron_vein`
   entries, no `herb_patch`, no `hometown` anywhere in the fixture) — it does not read
   `data/content` at all, contrary to investigation.md §6's claim. Extending that specific assertion
   block with a `"hometown"` check would only exercise the generic adapter mechanism on synthetic
   data, not verify this ticket's actual real-catalog fix. Resolution: added a new, separate,
   additive test function, `test_production_catalog_wood_and_herb_cover_hometown`, to the same file
   (`test_registry_bridge.py`, honoring the plan's file target) that uses
   `CatalogRepository("data/content")` directly (matching the pattern already used by
   `test_registry_parity.py::test_production_catalog_parity`) and asserts `"hometown"` is present in
   both kinds' real, projected `source_region_tags`. No existing test's assertions were modified.
4. **Two pre-existing test failures, confirmed unrelated via `git stash` A/B comparison** (both
   reproduce identically on unmodified code, so not caused or fixed by this ticket):
   `test_resource_opportunity_provider.py::test_stone_outcrop_node_surfaces_as_opportunity_in_
   frontier_village` (fails only under a specific multi-file pytest run order — test-order
   pollution, not `wood_node`/`herb_patch`-related) and 5 tests in
   `tests/integration/worldassembly/test_e2e_smoke.py` (`[CAT-REL-099] Resource 'stone_outcrop'
   references non-existent material 'stone'` — a `stone_outcrop`/material-catalog issue unrelated
   to this ticket's `wood_node`/`herb_patch` edits). Neither was investigated further or fixed here,
   consistent with this ticket's scope boundaries.
