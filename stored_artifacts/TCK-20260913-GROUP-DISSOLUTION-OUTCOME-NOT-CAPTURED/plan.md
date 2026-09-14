# Plan — TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED

Peer approved Option 1 (retain-with-terminal-marker, mirroring Clan/Camp), with two conditions:
audit each of the 11 `state.groups` consumers individually and report per-file which needed a
filter (not just assume the marker alone is sufficient), and keep outcome-semantics (what
`dissolution_tick`/a future `dissolution_reason` should actually mean) as a separate question for
later, not decided inside this ticket.

## Step 1 — `GroupSystem.update_groups()` itself
Both dissolution branches (leader dead/missing, membership drops below 2) now append
`dataclasses.replace(group, dissolution_tick=state.tick)` to `groups_add_or_update` instead of
`g_id` to `groups_remove` — the same `StateUpdate.groups_add_or_update` mechanism the rest of this
function already uses for live-group updates, no new schema. Added a top-of-loop guard
(`if group.dissolution_tick is not None: continue`) to protect against
`get_relevant_group_ids()`'s own `force_full_scan`/no-dirty-set fallback, which returns ALL of
`state.groups.keys()` — without the guard, a full-scan tick would re-run dissolution/cohesion
logic against every already-dissolved group, forever, once they stop being deleted.
`find_group_for_contract()`'s own docstring updated to reflect that it now finds dissolved groups
too (callers check `.dissolution_tick`).

## Step 2 — Per-consumer audit (the real work, per peer's own framing)

| Consumer | Needed a filter? | Why |
|---|---|---|
| `src/engine/pipeline_phases/groups.py::GroupPhase.resolve()` | **YES** — 2 sites | Both the leadership-election and defection passes build `all_relevant_group_ids` directly from `set(state.groups.keys())` (NOT the dirty-tracked path), so a retained dissolved group would run through both every tick forever without a filter. Most severe of the 3 real hazards found — bypasses even the dirty-tracking optimization Step 1 relies on. |
| `src/domains/cooperation/phase.py::CooperationPhase.execute()` | **YES** | `for g_id, g_rec in state.groups.items():` evaluates party cohesion for every group with no liveness filter; an unfiltered dissolved group would be scored `LEADER_LOST`/`MEMBER_ABANDONING` and its former (still-alive, now ungrouped) members would keep receiving the "abandoned" trust/grudge penalty every tick, forever. |
| `src/domains/cooperation/services.py::PartyCohesionService.evaluate()` | No direct change | Only ever called from the site above; safe once that caller filters. |
| `src/systems/social_systems/party.py::PartyCoordinationSystem.validate_shared_target()` | No | Only called from within `update_groups()`'s own per-group loop, which now `continue`s before reaching a dissolved group. |
| `src/engine/tactical.py` (2 sites, `state.groups.get(entity.identity.group_id)`) | No | Safe by construction: `entity.identity.group_id` is reset to `-1` in the SAME `StateUpdate` a group dissolves in (`group_id_set=-1`), so a live entity's own group_id field never points at an already-dissolved group by the time any later tick reads it. |
| `src/engine/apply_plan.py` (the `groups_add_or_update`/`groups_remove` apply logic itself) | No | Already handles `groups_add_or_update` (whole-record replace-in-place) correctly — this is the exact mechanism Option 1 reuses, mirroring how `ClanUpdate`/`CampUpdate` already work. |
| `src/engine/executor.py::get_frozen(state.groups, ...)` | No | Liveness-agnostic read-only freeze/cache utility. |
| `src/engine/checkpoint.py` (canonical-dict serialization of all groups) | No — and improved | Already serializes whatever is in `state.groups`; now correctly preserves a dissolved group's historical record in a checkpoint instead of losing it. |
| `src/replay/fingerprint.py` (hashes all groups) | No — and improved | Same reasoning as checkpoint: fingerprint now reflects full group history, still fully deterministic (just different hash values going forward than before this change, which is expected and correct, not a determinism regression). |
| `src/core/dirty.py` (`DirtySetBuilder`) | No | Marks a group dirty via `groups_add_or_update` (line iterating `base.group_ids`/adding `g.id` for each add-or-update) — this already fires correctly for the tick a group dissolves in, and naturally stops re-firing in later ticks once nothing further writes to that group id, with no change needed. |
| `src/systems/world_systems/groups.py` itself | **YES** — see Step 1 | The function being changed; covered above. |

## Step 3 — Tests
See test_plan.md.

## Step 4 — Regression + finalize
Full group/cooperation/faction-related regression, then a full fast-tier sweep. Update the ticket
to DONE with the real files-changed list, close, and bring the outcome-semantics question to peer
separately once this lands (not decided here, per peer's own explicit condition).
