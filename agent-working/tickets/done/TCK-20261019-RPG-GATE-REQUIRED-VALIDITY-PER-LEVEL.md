---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-RPG-GATE-REQUIRED-VALIDITY-PER-LEVEL
phase: done
date: 2026-10-19
tags: [testing, regression, simulation-quality]
---

# TCK-20261019-RPG-GATE-REQUIRED-VALIDITY-PER-LEVEL

## Title
The rpg gate's required-validity check asks for each V row only at the level it is judged at (per-seed `run` or `pooled`), not in every document.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
rpg-planner's v1 gate dispatch (run 39212800104 on 864f7b281) came out red, with 36 `no-data (contract_error)` rows reading "required validity row <id> missing". The 36 come from 3 worlds × (5 seeds × V7 + pooled × V1-V6, V8) = 15 + 21.

The metric module emits per-seed documents with V1-V6 and V8 (scope `run`) and a pooled document with V7 only (scope `pooled`). That is the right shape.

The fault is testing's. `rpg_gate_baseline_format.md` ("Required validity rows") says that every required id must be in "every seed document and the pooled one". Both `rpg_gate_report.missing_required` and `rpg_gate_candidate._missing_required` apply `config.required_validity` to every document, with no notion of level. So the v1 baseline cannot be recorded, though nothing is actually missing.

testing-planner ruling, 2026-10-19: each required id is required at the level(s) the config declares. Nothing else changes: a row that is truly missing is still `no-data`/`contract_error`, still refuses the candidate, and still shows in the banner.

## Scope
1. **Config shape** (`load_config` in `tools/test_architecture/rpg_gate_baseline.py`): `required_validity` becomes a mapping from level to ids, for example `{run: [V1, V2, V3, V4, V5, V6, V8], pooled: [V7]}`. The keys are `run` and `pooled` only. An id can appear under both. The plain-list form is refused with a message that names the new shape, because the list form is the ambiguity that caused this. The existing checks still apply: refuse a duplicate within a level, a bad id or a non-list value.
2. **Report** (`rpg_gate_report.py`, `missing_required`): a seed document is checked against `run` ids and the pooled document against `pooled` ids.
3. **Candidate** (`rpg_gate_candidate.py`, `_missing_required`): same split. The `omitted_validity` label uses the real level, `<id>:run:<world>:*` or `<id>:pooled:<world>:*`, instead of always `run`.
4. **Config values** (`tests/simulation_quality/rpg_gate/config.yaml`, rpg's file): rewrite L16 to `{run: [V1, V2, V3, V4, V5, V6, V8], pooled: [V7]}`, which is exactly what rpg's module emits on 864f7b281. **rpg-planner must say yes to these values on the PR before merge.** The values are rpg's; the shape is testing's.
5. **Format doc** (`docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`):
   - Rewrite "Required validity rows" to the per-level rule.
   - V8 section: scope is `run`. A pooled V8 row is optional; if a module emits one, its `violations` must equal the sum of the seeds' rows.
   - While there, remove the stale "Not yet emitted" sentence about V8 examples, if #660 has not landed it first. Whichever merges second rebases.
6. **Stub metrics** (`tests/helpers/rpg_gate_stub_metrics.py`): only if the stub's documents don't already follow the per-level shape.
7. **Re-run the report offline** on rpg's run-39212800104 documents (`/mnt/data/scratch-rpg-planner/gate_v1/`, read-only; copy into the scratchpad first). Show the 36 contract_error rows are gone and nothing else changed. The 4 real validity fails, V2 crowded/43, V3 frontier/42 and V4 frontier/44 and /45, must still show.

8. **Mixed-version check is per world** (added 2026-10-19, after rpg's count check). The report's header says `contract_error: 69`. Required-missing explains 36; the other 33 are `mixed metric module versions` on `O2.population` / `meat+plant+prepared`, 11 ticks × 3 worlds. `_threshold_problems` keys `seen` on `(id, group)` across the whole run set, so it compares floors across worlds: crowded 3.8, urban 3.0, frontier 3.1–3.3. Floors may differ by world (the row key includes `world`), so key the comparison on `(world, id, group)`, plus `tick` if the row carries one. Apply the same change in the candidate if it has the same check. The format doc's "mismatch across documents" becomes "across the documents of one world".
   - **What stays a real contract_error:** within `frontier_living_world` the floor differs by SEED (s42 3.3, s43 and s45 3.1, s44 and s46 3.2). A row has one threshold across seeds, or pooling is meaningless, so that stays `contract_error` after the fix. It is rpg's to resolve (a fixed floor, or a ruling that the floor is relative); testing-planner has asked rpg-planner.
   - **RESOLVED 2026-10-19 (testing-planner ruling, option 2):** O2.population's floor is relative by design: `max(3.0, 0.10 * first_tick_population)` (rpg_gate_metrics.py:146-148). rpg's module (Lane B, rpg-pre-v1-fixes) will compute it from the world's pooled tick-0 mean, so it is identical across seeds. The contract does not change: one k/floor/oracle per (world, id, group) across a world's documents. Do NOT add relative-floor handling to the report. On the old run-39212800104 documents the 11 rows correctly stay `contract_error` (AC4). On rpg's fixed-branch documents the total must be 0.
## Out of Scope
- rpg's metric module and any V row's values or thresholds.
- The 4 real validity fails (rpg's, going to the designer).
- The V1 free-meal entry in `rpg_gate_known.yaml` that matches nothing (rpg is checking it).
- Re-running the simulation. The fix is checked by re-reading the existing documents.

## Acceptance Criteria
- [x] AC1: `load_config` accepts the per-level mapping and refuses the plain list, an unknown level, a duplicate within a level and a bad id. Each case has a unit test.
- [x] AC2: in the report and candidate tests, a seed document with no V7 and a pooled document with only V7 give no `required_missing` rows when the config says `{run: [.., V8], pooled: [V7]}`.
- [x] AC3: a regression test fixes the mutation: drop V3 from one seed document, and the report gives exactly one `contract_error` row for that (world, seed). The candidate refuses, unless an owned `state: fail` entry exists, in which case the label is `V3:run:<world>:*`. The same goes for dropping V7 from a pooled document (label `V7:pooled:<world>:*`).
- [x] AC4: the offline re-run on run 39212800104's documents shows 0 "required validity row" rows (was 36). It shows **total contract_error = 11** (was 69): only frontier_living_world's per-seed O2.population floor, 11 ticks. The 4 real validity fails are unchanged. Quote before and after counts by detail in the Test Summary. Any other contract_error left over is a stop-and-report, not a fix-up.
- [x] AC4b: a test where two worlds have different floors for one (id, group) gives no mixed-version row, and two seeds of one world with different floors still do.
- [x] AC5: the format doc states the per-level rule and V8's level. No doc or code line still says "every seed document and the pooled one".
- [ ] AC6 (open until rpg-planner's comment link is on the PR): rpg-planner's yes on the config.yaml values is on the PR (comment link).
- [x] AC7: `tests/simulation_quality/rpg_gate/` and the rpg_gate tool tests pass.

## Related Tickets
- TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK (done; added V8 to required_validity)
- TCK-20261019-V8-SELF-TEST-ASSERTS-THE-EXAMPLE-NAMES-THE-ENTITY (PR #660; touches the same doc)
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC

## Related Docs
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK/

## Related Code Areas
- tools/test_architecture/rpg_gate_baseline.py (`load_config`, `GateConfig.required_validity`)
- tools/test_architecture/rpg_gate_report.py (`missing_required`)
- tools/test_architecture/rpg_gate_candidate.py (`_missing_required`)
- tests/simulation_quality/rpg_gate/config.yaml (rpg's values)
- tests/helpers/rpg_gate_stub_metrics.py

## Assumptions / Open Questions
- **rpg-planner said YES, 2026-10-19,** to the scope including the config.yaml L16 values `{run: [V1, V2, V3, V4, V5, V6, V8], pooled: [V7]}`. They'll confirm on the PR (AC6 still needs that comment).
- **Ordering constraint (rpg):** config.yaml is hashed into the gate harness, so this PR moves the harness hash. That is fine because no v1 baseline exists yet, but it **must merge before rpg's 5x3 v1 rerun on main**, so v1 is recorded on the new harness. Tell testing-planner the PR number as soon as it is up.
- V8 is `run` only. rpg won't emit a pooled V8 for now, and the optional-pooled rule stays in the doc.
- Only the v1 baseline record is blocked, so this goes ahead of the re-anchor's commit step but not ahead of its runs.
- If rpg prefers to emit every row at both levels instead, this ticket stops. That is rpg's call on values, but the shape ruling above stands as the default.

## Implementation Notes
- `GateConfig.required_validity` is now `{level: (ids)}` with `required_at(level)`; `_load_required_validity` refuses a plain list (message names the new shape), a non-mapping, an unknown level, a non-list, a duplicate within a level and a bad id.
- Report: `missing_required` asks a seed document for the `run` ids and the pooled document for the `pooled` ids. `_threshold_problems` keys on `(world, id, group)`.
- Candidate: `_missing_required` splits by level and returns `(world, level, id, owner)`; labels are `<id>:run:<world>:*` and `<id>:pooled:<world>:*`. An owned missing row is left out of every document of that world and level, so one dropped seed row with an owner does not trip the "absent from seed" refusal. `_thresholds` keys on `(world, id, group)`.
- Config L16 and the format doc rewritten to the per-level rule; V8 stays `run`, a pooled V8 is optional. The stale "Not yet emitted" V8 sentence is left to #660 (it removes it), to avoid a conflict. The stub metrics already follow the shape and are unchanged.
- O2.population floors: no relative-floor handling added (ruling option 2).

## Test Summary
- `tests/unit/tools/test_rpg_gate_{baseline,report,candidate,workflow_support,harness}.py` and `tests/simulation_quality/rpg_gate`: 161 passed (`-k "rpg_gate or v8"` over tests/unit/tools plus the rpg_gate directory).
- AC4 offline re-run on run 39212800104's documents (copied read-only from /mnt/data/scratch-rpg-planner/gate_v1/, 18 documents, harness hash taken from the documents, no rerun, no baselines), before = origin/main code and config, after = this branch:
  - contract_error total: 69 -> 11
  - by detail: "required validity row ... missing" 36 -> 0; "mixed metric module versions" 33 -> 11
  - the 11 left are frontier_living_world O2.population meat+plant+prepared (floor differs by seed), as ruled
  - fails unchanged (4): V2 crowded_frontier/43, V3 frontier_living_world/42, V4 frontier_living_world/44 and /45
  - no-data rows 173 -> 137, pass 104 -> 104.

## Files Changed
tools/test_architecture/rpg_gate_baseline.py, rpg_gate_report.py, rpg_gate_candidate.py; tests/simulation_quality/rpg_gate/config.yaml (L16, rpg-planner said yes); docs/plans/test_architecture/reference/rpg_gate_baseline_format.md; tests/unit/tools/test_rpg_gate_{baseline,report,candidate}.py.

## Completion Summary
Required validity is per level (run / pooled); the mixed-version check is per world. AC6 (rpg-planner's yes on the PR) is the one open item.
