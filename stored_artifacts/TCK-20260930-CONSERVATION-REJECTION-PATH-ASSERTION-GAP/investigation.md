---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP
artifact_type: investigation
tags: [testing, economy, resource]
---

# Investigation — TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP

Framing guard (AC-7): this is a **test-coverage gap, not a live defect**. Every rejection path in
`resolve()` already returns `accepted=False` with the right reason. Nothing here claims otherwise.

Resume note (second resume): re-produced with all five owner decisions of 2026-10-01 folded in. Load-bearing line references (all `accepted=False` lines, reservation guards `:107/:124/:239/:276`, `economy.py:89/103/142/289/324/346/350`, `apply.py:307-308/487`, target sha prefix `bb5484ebbed8`, baseline counts 177/60/117) were re-verified against the working tree in this run; `git diff --stat origin/main -- src/` is empty.

## Current Behavior

`src/core/conservation.py` (334 lines, sha256 prefix `bb5484ebbed8` — identical to the baseline's
`target.sha256` prefix, so the baseline is not stale on content; `stale_after` = 30 days from
2026-09-29 or target sha change).

`ResourceTransactionResolver.resolve()` (`:45-334`) is a pure `@staticmethod`; every rejection is
`TransactionResult(accepted=False, reason=...)` (frozen dataclass, `:16-34`). Rejection paths (all
line numbers re-verified by grep `accepted=False`):

| Line | Source kind | ReasonCode |
|---|---|---|
| 59 | any (idempotency vs `state.processed_transaction_ids`) | IDEMPOTENCY_VIOLATION |
| 74/77/89 | NODE | INVENTORY_FULL / TARGET_INVALID / SOURCE_DEPLETED |
| 101/104/108 | GROUND_ITEM | INVENTORY_FULL / SOURCE_MISSING / **TARGET_LOCKED** |
| 118/121/125 | CORPSE | INVENTORY_FULL / SOURCE_MISSING / **TARGET_LOCKED** |
| 136/139/144 | CRAFTING | INVENTORY_FULL / INSUFFICIENT_GOLD / INSUFFICIENT_RESOURCES |
| 158/162/169/174 | SHOP_BUY | INVENTORY_FULL / TARGET_INVALID / OUT_OF_STOCK / INSUFFICIENT_GOLD |
| 198/201/206 | SHOP_SELL | TARGET_INVALID / LIQUIDITY_EXHAUSTED / INSUFFICIENT_RESOURCES |
| 228 | COMBAT | INVENTORY_FULL |
| 240/244 | QUEST | **TARGET_LOCKED** / INVENTORY_FULL |
| 257 | TOWN_SERVICE/TAX/REPAIR_FEE/SERVICE_FEE/INFORMATION_PURCHASE | ACTION_EXHAUSTION |
| 277/280 | RECRUIT, CHEST | **TARGET_LOCKED** / ACTION_EXHAUSTION |
| 309/314/320 | HOME_STORAGE | ACTION_EXHAUSTION / INSUFFICIENT_CAPACITY / ACTION_EXHAUSTION |
| 334 | unknown kind | UNKNOWN_SOURCE_KIND |

29 rejection returns in total. Production `building` source kind: there is no `BUILDING`-specific
reservation branch in `resolve()` (see Risks 2).

Apply path: `ResourceTransactionSystem` in `src/engine/economy.py` (re-verified): `processed_ids`
from the incoming update `:39`; `reservations = {}` `:47`; `in_tick_processed_ids = set()` `:50`;
independent-intent in-tick idempotency check `:89` (rejects before the resolver); `if result.accepted:`
`:103`; `in_tick_processed_ids.add(...)` `:142` inside the accepted block (grouped path adds at `:229`);
output `processed_transaction_ids=list(processed_ids.union(in_tick_processed_ids))` `:289`. Failure
branch emits `TRANSACTION FAIL`, `IntentResult(accepted=False)`, interaction reset and a `RejectionEvent`.
Grouped intents resolve all, commit only if all accepted, else roll back. `src/engine/apply.py:307-308`
(`new_processed = list(prior_state...)`; `.extend(update.processed_transaction_ids)`) -> `:487`
(`processed_transaction_ids=new_processed`) into `AuthoritativeState`. The ticket's trace is confirmed.

`_apply_world_effects` (`economy.py:315`) populates `reservations` only for `("NODE", id)` `:324`,
`("GROUND_ITEM", id)` `:346` and `("CORPSE", id)` `:350`.

Existing tests: CORRECTION to the earlier finding — `TARGET_LOCKED` IS asserted end to end by `tests/unit/resource/test_resource_conflicts.py:76` and `tests/integration/kernel/test_race_conditions_v2.py:89,113` (two actors, same GROUND_ITEM/CORPSE, apply path). Both lie outside the baseline's 8 selected files, which is why the mutants survived the baseline; they do not assert the burn or zero-change properties this ticket adds. `tests/unit/resource/test_resource_conservation_regression.py` has full-inventory style cases. `tests/unit/economy/test_gold_sink.py:271` asserts `accepted is False` + `ACTION_EXHAUSTION` for REPAIR_FEE (precedent). `tests/unit/quest/test_quest_rewards.py` covers idempotency of an *accepted* repeat, not the rejection-burn case.

Side finding (not in the ticket): the baseline also has surviving mutants on the reservation
*conditions* themselves (e.g. `("XXGROUND_ITEMXX", ...)`, `.get(..., 1)`, `> 1`, `or`) at lines 104-125. The
TARGET_LOCKED tests with positive and negative controls will likely kill most of these as a bonus; the
ticket does not require it and the record should report it only as an observation.

## Mechanics / Engine Constraints

- `docs/mechanics/03_economic_laws.md` section 1 (Atomic Conservation Law) and sub-contract
  `docs/mechanics/resource_conservation_contract.md` (gate sequence, failure codes ~`:147`, "Concurrent
  Actor Protection" `:224-228`): a rejected transfer leaves world state unchanged — oracle for AC-3.
- `docs/engine/authoritative_mutation_pipeline_contract.md` and `docs/core/state.md`: durable change only via
  apply path; `processed_transaction_ids` is durable authoritative state (Durable State Rule).
- CLAUDE.md Testing Rule: architecture tests must verify read-only logic did not mutate live state.
- Ticket Out of Scope: `src/` must not change (AC-5). A test that needs a production change means stop and report.
- `docs/mechanics/resource_conservation_contract.md:226` states the resolver checks reservations for
  "NODE, GROUND_ITEM, CORPSE, QUEST, CHEST, or RECRUIT". The resolver does (for GROUND_ITEM, CORPSE, QUEST,
  RECRUIT/CHEST; NODE's lock is charge accounting at `:82-91`); the apply path only populates NODE, GROUND_ITEM
  and CORPSE. The sentence is therefore incomplete as a statement of runtime behavior (owner decision 3 authorizes
  correcting it).

## Docs Requiring Update

- `docs/mechanics/resource_conservation_contract.md`: owner decision 3 authorizes a prose-only fix — (a) the `:226` reservation sentence must say the resolver honours QUEST/CHEST/RECRUIT reservations but the apply path populates only NODE/GROUND_ITEM/CORPSE, and that no building reservation guard exists; (b) the Regression Tests table (`:282-289`) cites `tests_v2/...` paths that do not exist in the repo and must cite the real new test paths.

Considered and excluded (prose only, no machine-parsed bullet): `docs/mechanics/03_economic_laws.md`
(path: `docs/mechanics/03_economic_laws.md`) — the ticket's "consider whether this chapter should say the law lives in
`src/core/conservation.py`" is optional and outside the owner's authorization; not required. The docs
`docs/core/state.md` and `docs/engine/authoritative_mutation_pipeline_contract.md` need no change because no behavior changes.
`docs/guidelines/intentional_divergences.md` needs no entry (owner decision 3: doc-only fix of existing behavior).

## Parity Ledger Overlap

All in `docs/parity_ledger/town_resource.yaml` (re-verified present):
- TOWN-011 (`:122`, P0, verified) and TOWN-012 (`:134`, P0, verified) — resolver capacity gates; no change forced.
- TOWN-014 (`:160`, P0, verified; test_path = the three conservation_regression tests) — authoritative side effects;
  candidate to append new test node ids.
- TOWN-103 (`:1088`, P0, verified; `test_path: null`) — "All active resource acquisition paths share one conservation law."
  Pre-existing P0 with null test_path; new tests are natural evidence; filling it is a parity-updater decision, not forced scope.
- TOWN-121 (`:1272`), TOWN-123 (`:1296`), TOWN-124 (`:1307`), TOWN-125 (`:1317`) — concurrent loot/corpse protection, all verified with
  `test_path: null`. The GROUND_ITEM/CORPSE two-actor apply-path tests are direct evidence for TOWN-121/123; TOWN-122 already has a test_path.
- Gold-sink entry (~`:1966`) references `conservation.py L255-272`; unchanged since `src/` is unchanged.
Owner decision 3 says "update the matching parity-ledger entry if one exists": the doc `resource_conservation_contract.md` is
cited by these entries. No status change is expected; the only candidate edits are `test_path`/`v2_evidence` enrichments on
TOWN-014/103/121/123 by parity-updater. Because these edits are conditional and no mandate exists, they are not listed as
machine-parsed required docs.

## Prior Work

- `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY` / PR #259 produced `tests/mutation/baselines/src_core_conservation.json`
  (present in this worktree; the ticket's "unpushed on b1ab0c2d5" note is outdated).
- PR #265 `tests/unit/resource/test_node_charge_accounting.py` killed the `:82-91` mutants (excluded from this ticket's delta, AC-6).
- Related open: `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS` (excluded).
- `TCK-20260427-RESOURCE-CONSERVATION-HARDENING`, `TCK-20260427-PHASE3-RESOURCE-CONSERVATION`, `TCK-20260501-E5-HARDENING`
  (race-condition safeguards, exactly-once idempotency), `TCK-20260415-PIPELINE-IDEMPOTENCY` — earlier hardening of the same resolver/idempotency.

## Risks and Open Questions

**Genuinely open questions: none.** All five owner decisions of 2026-10-01 are settled and folded in; none is re-opened here.

Settled (decisions, not questions):
1. All 22 flag-flip survivors are the AC-6 target (ids 22, 32, 54, 57, 63, 67, 76, 80, 82, 86, 91, 96, 100, 111, 113, 117, 132, 153, 155, 169, 171, 175; lines 59, 77, 101, 104, 108, 118, 125, 136, 139, 144, 158, 162, 169, 198, 201, 206, 240, 277, 280, 309, 314, 320). The record names which are killed.
2. AC-4 is resolver-level for QUEST/RECRUIT/CHEST (hand-built reservations dict); "building" is recorded as "no such guard exists", not tested; no `src/` guard.
3. The doc fix to `docs/mechanics/resource_conservation_contract.md` is authorized (prose only, no divergence entry).
4. If mutmut 2.5.1 cannot run: AC-6 stop-and-report, no substitute measurement (no hand mutation, no AST flipper, no 3.x; 3.x rejects `src.` import paths).
5. Mutation re-run scope: (a) first run the baseline-selection-only pass (the unchanged 8 files) as positive control; it must reproduce 177 / 60 / 117 with mutmut 2.5.1, else stop-and-report (tool, version or environment changed; the delta is not attributable to the new tests) before any delta is reported. (b) The delta pass runs the baseline's 8 files plus the 2 new files. `tests/unit/resource/test_resource_conflicts.py:76` and `tests/integration/kernel/test_race_conditions_v2.py:89,113` are NOT added, but the record must name them as existing TARGET_LOCKED end-to-end coverage outside the selection (they assert `ReasonCode.TARGET_LOCKED` via the apply path with two actors; this corrects the earlier "no test references TARGET_LOCKED" finding), so no artifact reads "survived" as "untested". (c) Record at `tests/mutation/reruns/src_core_conservation_rerun.json`, outside the `tests/mutation/baselines/*.json` glob. It must state that the core-RPG report's mutation layer reads only `baselines/*.json` so the re-run is invisible to the report, and that the baseline is not refreshed and still goes stale on 2026-10-30. It carries: exact mutmut 2.5.1 command, version, full test file list and count, source and target shas, runtime, a statement that before and after test sets differ, before counts (177/60/117), and each of the 22 ids killed or alive, excluding the `:82-91` kills (PR #265).

Facts the implementer must respect (not questions):
- QUEST, RECRUIT and CHEST TARGET_LOCKED (`conservation.py:240`, `:277`) are reachable only by a direct `resolve()` call; the apply path populates reservations only for NODE, GROUND_ITEM, CORPSE (`economy.py:324, 346, 350`). The end-to-end "two entities claim one source" story holds for GROUND_ITEM and CORPSE only.
- Line `:59` (resolver idempotency) is pre-empted on the apply path by `economy.py:89`; killable only by a direct resolver call.
- Baseline survivor ids 45-49 (line 91) predate PR #265; compute the delta excluding `:82-91`.
- `equivalent: not-classified`: no kill-rate claim.
- Sibling-record trap: `tests/unit/tools/test_mutation_baseline_records.py` and `tests/unit/tools/test_core_rpg_report.py` are the only readers of `tests/mutation/`; the `reruns/` directory is outside the baseline glob, so neither is affected and the baseline JSON must not be rewritten. Nothing in `tools/` reads `tests/mutation/`.
- Baseline staleness: sha prefix `bb5484ebbed8` matches at investigation time; the positive-control pass must re-confirm the target sha before running.
- Mutmut run cost is about 341 s per pass; two passes in a scratch copy at a real path (not `/tmp`, not in the repo).

## Anti-Drift Hazards

- No edit under `src/` (AC-5); verify with `git diff --stat origin/main -- src/` (never local `main`).
- Do not assert only `not accepted`; assert `is False` and exact `ReasonCode` (a wrong code is its own defect class).
- A parametrised test must enumerate source kinds from an explicit table and have a guard that fails when `resolve()` gains a source kind not in the table.
- Do not add a `building` reservation test or a `src/` building guard; record "no such guard exists".
- Do not put ticket IDs/phase labels in test identifiers (project convention).
- Do not touch `src/core/inventory.py`, do not add mutmut as a project dependency, do not claim a live conservation defect in any artifact, docstring or record.
- Do not rewrite the baseline's historical record; the re-run record is a separate file under `tests/mutation/reruns/` and does not refresh the baseline.
- Do not add the existing TARGET_LOCKED end-to-end files to the mutmut selection; name them in the record instead.
- Do not report any delta before the baseline-selection-only pass reproduces 177/60/117.
- Do not edit `plan.md` from this role (the planner owns it).
