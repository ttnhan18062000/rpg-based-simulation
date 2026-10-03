---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260915-MECHANISM-REGISTRY-FOUNDATION
phase: done
date: 2026-09-15
tags: [architecture, documentation, schema]
---

# TCK-20260915-MECHANISM-REGISTRY-FOUNDATION

## Title
The mechanism registry file, its schema, its validator, and the initial seed

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Create the single hand-authored source for what simulation mechanisms exist, which layer each belongs
to, and what each depends on. Everything else in
`TCK-20260915-EPIC-MECHANISM-REGISTRY` builds on this file.

Two blocks — layers carry frequency, mechanisms carry dependency:

```yaml
layers:
  entity:  { cadence: per_tick, rank: 1 }
  faction: { cadence: daily,    rank: 3 }

mechanisms:
  - id: combat
    layer: entity
    depends_on: [movement, perception]
    state: done
```

`state` uses the atlas's existing six classes (`done`, `partial`, `gap`, `orphan`, `gated`,
`skeleton`) — not a new vocabulary. Those six already encode the built-but-never-runs distinction;
inventing a seventh is explicitly out of scope.

## Scope
1. **The registry file** — location alongside the existing generated index
   (`docs/brainstorm/`), YAML for hand-authorability.
2. **Seed it with real mechanisms**, ~30–50 expected. Derive from the wiring map's existing flowchart
   nodes and the atlas's layer sections rather than inventing a taxonomy; both already name the real
   systems.
3. **Validator** enforcing four invariants, wired into CI:
   - every `depends_on` id resolves to a declared mechanism,
   - the dependency graph is acyclic,
   - every `layer` is declared in the `layers` block,
   - every `state` is one of the six classes.
4. **`make` target**, registered alongside `brainstorm-idea-index`.
5. **Graphify cross-check (report-only)** — flag any declared `depends_on` edge with no supporting
   call/import path as suspicious. Report, never fail: graphify's 35k-node graph is advisory here.

## Out of Scope
- The `verified` block (child 2).
- Priority derivation and chart generation (child 3).
- Changing any artifact to read from this file (child 4).
- Auto-generating `depends_on` from code. Hand-authored; 30–50 nodes is human-scale.

## Acceptance Criteria
1. The registry file exists, is valid, and is seeded with the real mechanism set.
2. `depends_on` is the only hand-authored edge data — no stored dependent-count anywhere.
3. Frequency appears only on layers, never on a mechanism.
4. The validator fails on each of the four invariants, each proven by a test using a deliberately
   invalid fixture — **not** by a clean pass on valid input. A validator only ever run against good
   data is indistinguishable from one that does nothing.
5. The `make` target regenerates or validates without manual steps.

## Related Tickets
- `TCK-20260915-EPIC-MECHANISM-REGISTRY` — parent
- `TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX` — the generated-index precedent

## Related Docs
- `docs/plans/mechanism_registry_initiative.md` §3 — shape and invariants

## Related Stored Artifacts
- `stored_artifacts/TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX/plan.md`

## Related Code Areas
- `tools/generate_brainstorm_idea_index.py`
- `docs/brainstorm/idea_index.json`
- `Makefile`

## Assumptions / Open Questions
1. Real mechanism count once seeded — 30–50 is an estimate.
2. Whether mechanism ids should align to atlas card ids, wiring-map node ids, or stand alone. Leaning
   stand-alone with mappings added by child 4, so seeding is not blocked on reconciling 139 cards.
3. Whether the file belongs in `docs/brainstorm/` beside `idea_index.json` or in `registries/`.
   `registries/` is append-only allowlists and a mechanism registry must support edits, so
   `docs/brainstorm/` is the better fit — confirm against repo convention before committing.

## Implementation Notes
The strongest reason to enforce the validator from day one: a `depends_on` pointing at a renamed
mechanism fails silently, which is the exact defect family this arc spent weeks cataloguing. Build
the failure loud.

**Two stale source documents fixed before seeding** (seeding known-wrong data would propagate the
error into every future consumer at once): Breakthrough Bonuses was badged `gap`/stub in the atlas
and wiring map, but `BreakthroughService.apply_bonuses()` is real and called on every stat
recalculation from the production path (`progression/breakthroughs.py:36-58`, called from
`rpg_depth.py:367`) — fixed in `rpg_feature_atlas.html`, `rpg_simulation_wiring_map.html`, and
mirrored into `simulation_capabilities.html` per the standing atlas-sync rule. Race-Keyed
Evolution Chains cited a duplicate implementation already deleted by
`TCK-20260824-WIRE-ORPHANED-MECHANISMS`; collapsed to a single `done` mechanism.

**Real mechanism count is 75, not the 30–50 estimate** (Assumptions #1) — 71 atlas JSON cards
(`entity-action` through `beyond-city`, all 14 sections excluding `design-ideas`) + 2 net splits
(`aging_death`/`succession`, `xp_leveling`/`breakthrough_bonuses`) + 2 wiring-map-only additions
(`nest`/`lair`, which have no atlas JSON card at all — sourced from the wiring map's own separate
"Beyond the City" table). Seeded all 75, no curation, per peer review — every id carries a real
citation, and a mechanism missing from the registry is invisible, the exact failure this epic
exists to prevent. This investigation itself carried three separate inherited-but-unverified
numbers across roughly a day (73→75 mechanism count, a stale ~25/75 `depends_on`-density claim
corrected to the real 42/75, and the two stale atlas badges above) — each caught only by checking
the real source directly. Documented in investigation.md's own "This Document's Own Drift" section
as structural evidence for the registry's founding rationale, not a self-criticism.

**Assumption #2 (mechanism ids stand-alone, not aligned to atlas card ids) confirmed correct as
scoped** — ids are derived names (`combat_resolution`, `tactical_decision`, etc.), not literal
atlas card indices; card-index citations live only in investigation.md's provenance trail, not in
the registry file itself.

**Assumption #3 (file location) resolved: `docs/brainstorm/mechanisms.yaml`.** `registries/*.jsonl`
is documented as strictly append-only (managed via a `tools/*_registry.py add` CLI, never
hand-edited) — incompatible with a file that needs real hand-edits as mechanism state changes.
`docs/brainstorm/` is git-tracked, editable, and already houses `idea_index.json` (a related but
distinct generated-index precedent, not hand-authored the way this file is).

**`depends_on` density**: 42 of 75 mechanisms declare an outgoing dependency, but only 26 distinct
mechanisms are ever named as someone else's dependency (49 have zero dependents) — a small set of
real hub prerequisites (`action_pacing_readiness`, `regional_trauma_hazards_sovereignty`,
`combat_resolution`, `belief_cycle`, `betrayal_siege_war`, others) surrounded by leaves. This is
the expected shape of a real dependency graph, not a defect — flagged for T3 (priority derivation)
since `rank × dependents` will have layer rank doing most of the ordering work for the 49 leaves,
which is correct (small real blast radius), not a degradation.

**Two known placeholders, not blocking**: `race_collective_force` and `settlement_capacity_axis`
are seeded under `layer: faction` as the nearest organizational tier a real implementation would
likely live in — a guess, not a citation-backed placement, flagged inline via YAML comment for a
future layer-design ticket.

**Graphify cross-check real output**: 47 `depends_on` edges checked against `graphify-out/graph.json`
(38,139 nodes / 107,182 links), 9 supported, 8 suspicious, 30 no_match — many `no_match` results
are the token-subset matching heuristic correctly admitting it can't find a code symbol for a
given id phrasing (e.g. `action_pacing_readiness`) rather than falsely claiming support. Report-only,
never fails the build; wired as informational output appended after the hard-invariant `validate()`
call in `make mechanism-registry-validate`.

**UPDATE 2026-09-16: `test_make_target_validates_real_registry` (this ticket's own test) found a
real, pre-existing, broader CI defect on its first real CI run.** `Makefile`'s `PYTHON3 :=` (line
35) resolved bare `python3` via `[ -x "$$py" ]`, which tests a relative path in the current
directory, not `$PATH` resolution — verified directly (`[ -x "python3" ]` is false with no
`./python3` file present; the full fallback loop resolves to an empty string when none of the
hardcoded dev-machine paths exist, exactly CI's own situation: no `.venv/`, no
`/home/u24desktop/...`/`/home/vboxuser/...`). `make mechanism-registry-validate` therefore ran with
no interpreter on CI, while every local run "worked" only because a hardcoded absolute dev-machine
path happened to exist. `PYTHON` (a separate, correctly-written variable at line 428) already used
`command -v "$$py"`, the right form — `PYTHON3` did not. This bug is not new and not specific to
this ticket: every `$(PYTHON3)`-based `make` target (`brainstorm-idea-index` included) has been
silently broken on CI the whole time; nothing before this ticket's own test ever exercised a `make`
target from inside a CI job. Fixed in the same commit that introduced the test that found it
(`PYTHON3`'s definition changed from `[ -x "$$py" ]` to `command -v "$$py" >/dev/null 2>&1`,
mirroring `PYTHON`'s already-correct form) — fixing the substance the gate correctly flagged, not
weakening the test. Verified directly before pushing: the broken form resolves to an empty string
in a simulated CI-like shell (no dev-machine paths on `$PATH`, no `.venv`), the fixed form resolves
correctly to `python3`; both the relative-path (`.venv/bin/python3`) and absolute-path precedence
cases were independently re-verified to still work correctly under the fixed form, not just the
bare-name case. Diagnosed collaboratively: this session pushed a five-step diagnostic (rerun the
exact same job on the exact same commit to rule out flakiness; check whether `main` had ever failed
this job; reproduce the job's scope in two separate local venvs, including one built fresh the same
way CI installs — all passed cleanly, both raw-log-fetch endpoints network-blocked in this
sandbox); peer read the Makefile directly and found the actual defect from that record, without
needing log access at all.

**UPDATE 2026-09-16 (second): the Makefile fix alone did not resolve CI — a second real defect
was under it, in this ticket's own new code, not the Makefile.** After the Makefile fix, CI still
failed the same job; per-step probing (temporarily splitting the job's combined `pytest` step into
one step per directory, `if: always()` on each, read via `gh api .../jobs/{id} --jq '.steps[]'`
without needing log access at all) first localized it to `tests/unit/tools` (every other directory
in that job passed, including `tests/unit/docs` — ruling out a hypothesis that the new
`mechanisms.yaml` file tripped a corpus-wide docs inventory test), then a second, file-level split
localized it further to `test_mechanism_registry.py` AND `test_mechanism_registry_graphify_check.py`
both failing. Root-caused to one shared cause: `graphify-out/` is gitignored (0 tracked files,
confirmed via `git ls-files graphify-out/`), so a fresh CI checkout has no `graphify-out/graph.json`
at all. `tools/mechanism_registry_graphify_check.py`'s `_load_graph()` raised an uncaught
`FileNotFoundError` on that — directly reproduced locally by moving `graphify-out/` aside
temporarily (restored immediately after each check) — which crashed both the graphify-check's own
tests AND, indirectly, `test_mechanism_registry.py`'s `test_make_target_validates_real_registry`,
since `make mechanism-registry-validate`'s second command (Step 5's own wiring) is that same
script; `make`'s default sequential-recipe behavior means the second command's crash failed the
whole target, and therefore the test invoking it, even though that test has nothing to do with
graphify directly. Fixed in `tools/mechanism_registry_graphify_check.py`: `check()` now catches
`FileNotFoundError` from a missing graph and returns `{"supported": [], "suspicious": [],
"no_match": [], "graph_unavailable": True}` instead of raising; `main()` reports a clear "SKIPPED"
message and still returns 0. This is the substance fix, not a workaround — Scope item 5's own
contract already says "Report, never fail: graphify's 35k-node graph is advisory here," and a hard
crash on a missing (locally-optional, CI-absent) graph directly contradicted that contract before
this fix. Verified directly (not just trusted): moved `graphify-out/` aside again after the fix,
confirmed `tools/mechanism_registry_graphify_check.py`, `make mechanism-registry-validate`, and the
full 44-test suite in `tests/unit/tools/` + the capability-registry regression check all pass
cleanly with the directory genuinely absent, then restored it. New test
`test_missing_graph_reports_and_never_fails` added (`monkeypatch`-based, never touches the real
`graphify-out/` directory) to guard this regression going forward. Diagnosed via the same
step-splitting technique peer proposed (a temporary diagnostic addition to
`.github/workflows/test.yml`, two rounds, removed again once the cause was found — the workflow
file is byte-identical to its pre-diagnostic state, confirmed via `git diff`). Peer's own first
guess at this second root cause (before the second round's step data confirmed it) was
appropriately labelled a prediction, not a diagnosis, and was directionally correct.

## Test Summary
`tests/unit/tools/test_mechanism_registry.py` (24 tests) + `test_mechanism_registry_graphify_check.py`
(7 tests, including the new `test_missing_graph_reports_and_never_fails`) + regression check
`tests/unit/engine/test_capability_registry.py` (9 tests, the imitated pattern, unmodified) —
40/40 passing. Per Acceptance Criteria #4, all four validator invariants proven failing on
deliberately broken fixtures (unresolved `depends_on`, direct 2-node cycle, a longer 3-node cycle
so a pairwise-only check can't accidentally pass, undeclared layer, invalid state), each fixture
isolated to exactly one invariant, plus a parametrized test proving all six valid states are
individually accepted (the enum boundary is exact on both sides), plus a valid-fixture canary using
real seeded ids so the invalid-fixture tests are proven to be testing a validator that *can* pass.
`make mechanism-registry-validate` tested both against the real committed file and against a
`tmp_path` copy with an injected defect (never mutating the real file in place). Regenerated
`docs/brainstorm/idea_index.json` after the two atlas badge fixes; verified the idea count stayed
at 68 with no generator assertion failure.

Whole suite re-verified with `graphify-out/` genuinely absent (moved aside, restored immediately
after) to match the real CI condition exactly — all 44 tests in `tests/unit/tools/` +
`tests/unit/engine/test_capability_registry.py` pass under that condition, confirming the
graph-unavailable fix without relying on trust in a CI-only reproduction.

Scoped pytest command used throughout:
```
.venv313/bin/python3 -m pytest tests/unit/tools/test_mechanism_registry.py tests/unit/tools/test_mechanism_registry_graphify_check.py tests/unit/engine/test_capability_registry.py -v
```

## Files Changed
- `docs/brainstorm/mechanisms.yaml` (new) — the registry, 75 mechanisms
- `tools/mechanism_registry.py` (new) — reader + validator
- `tools/mechanism_registry_graphify_check.py` (new) — report-only cross-check
- `tests/unit/tools/test_mechanism_registry.py` (new) — 24 tests
- `tests/unit/tools/test_mechanism_registry_graphify_check.py` (new) — 6 tests
- `Makefile` — `mechanism-registry-validate` target, plus fixing a real pre-existing
  `PYTHON3 :=` resolution bug this ticket's own CI run found (see UPDATE 2026-09-16 above)
- `docs/brainstorm/rpg_feature_atlas.html` — two stale badges corrected (Breakthrough Bonuses,
  Race-Keyed Evolution Chains)
- `docs/brainstorm/rpg_simulation_wiring_map.html` — same two corrections mirrored (BRK node +
  Buildup table row)
- `docs/brainstorm/simulation_capabilities.html` — Breakthrough Bonuses tier corrected
  (`built`→`live`), plain-language desc updated, per the standing atlas-sync rule
- `docs/brainstorm/idea_index.json` — regenerated (badge-text edits changed two
  `wiring_map_mentions` counts; both verified as expected, not regressions)
- `staging_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/` — investigation.md, plan.md,
  test_plan.md

## Completion Summary
DONE. Registry built and seeded with the real, citation-backed mechanism set (75, not the
estimated 30–50 — reported and decided with peer review before seeding). Validator enforces all
four invariants, each proven against a deliberately broken fixture, not just a clean pass. Two
stale source-document badges fixed before they could seed wrong data. Report-only graphify
cross-check shipped as a real, conservative first version rather than deferred. All out-of-scope
items (verified block, priority/chart derivation, artifact convergence, auto-derived depends_on)
correctly deferred to child tickets 2–4. `tests/unit/tools/` is already wired into the
"Unit · infra / observability" CI fast lane (verified directly against `.github/workflows/test.yml`
before considering this ticket closeable — no new CI-wiring gap, unlike an earlier ticket this same
session that added a brand-new top-level test directory).

**This ticket's own CI run surfaced two real, undeclared local-state dependencies — the same
pattern this registry exists to make visible, just one layer down in the tooling that builds it,
not in the simulation itself:** (1) `Makefile`'s `PYTHON3 :=` resolved a bare `python3` fallback
via `[ -x "$$py" ]`, which only works because a hardcoded absolute dev-machine path happens to
exist on every machine this was run from locally — broken on CI, where none of the hardcoded paths
exist and the bare-name fallback needed `$PATH` resolution (`command -v`) instead. (2)
`tools/mechanism_registry_graphify_check.py` read `graphify-out/graph.json` unconditionally, which
only works because that gitignored, uncommitted directory happens to exist locally wherever
`graphify update` has been run — absent on a fresh CI checkout, where the script crashed instead
of honoring its own documented "report, never fail" contract. Both were real, silent, and
non-obvious until something ran in an environment without the ambient local state — exactly the
"depends on something nobody declared" shape. Neither was hypothetical: both were reproduced
directly (a simulated no-dev-paths shell for the first, physically moving `graphify-out/` aside
and back for the second) before being called findings, not just suspected.

**One root cause, two failure sites, worth stating explicitly so a future reader doesn't go looking
for two separate causes:** `test_mechanism_registry.py`'s `test_make_target_validates_real_registry`
has nothing to do with graphify and still failed alongside
`test_mechanism_registry_graphify_check.py`'s own tests, because `make mechanism-registry-validate`
(Step 5's own wiring) runs the graphify-check script as its second command — that script's crash
failed the whole `make` target, and therefore every test that invokes it, regardless of what that
test itself is about.
