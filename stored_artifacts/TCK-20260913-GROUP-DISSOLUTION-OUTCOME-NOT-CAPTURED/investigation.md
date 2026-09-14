# Investigation — TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED

**Per this ticket's own explicit acceptance criteria, this document originally brought a design
question with real options and a recommendation, not a decision, with nothing in `src/` or
`tests/` changed. Peer/user has since reviewed it and approved Option 1 (see the Resolution
section at the end) — the options and reasoning below are preserved as the record of that
decision, not retroactively edited to look like the plan all along.**

## Where Group dissolution happens today

`GroupSystem.update_groups()` (`src/systems/world_systems/groups.py`) has exactly 2 branches that
dissolve a group, both ending in `groups_remove.append(g_id)` — full deletion from `state.groups`,
no trace retained:
1. **Leader dead/missing/inactive** (line ~93-98).
2. **Membership drops below 2 after filtering** (line ~157-158) — itself the union of several
   distinguishable underlying causes: a member died/deactivated, a member fell outside
   `cohesion_radius`, or the group's bound contract became invalid/expired.

`GroupRecord.dissolution_tick` (`src/core/state.py`) is declared but has no write site anywhere —
confirmed by grep, dead at the data-model level, matching the ticket's own claim.

## Precedent survey: how does this codebase handle "record left the active set, but its outcome
still matters" elsewhere?

Checked every durable-state sibling with a comparable terminal-state shape, per this ticket's own
instruction to survey precedent before proposing anything.

**1. `ClanState.dissolved_tick` — real, live, in-place terminal field on a retained record.**
`ClanLifecycleService.process_dissolution()` (`src/systems/social_systems/clan_lifecycle.py`)
returns `ClanUpdate(clan_id=clan.clan_id, dissolved_tick_set=tick)` — the `ClanState` is **never
removed** from `state.clans`; it stays there permanently with `dissolved_tick` populated. Every
consumer that needs "is this clan still active" checks `clan.dissolved_tick is not None`
(confirmed live at `src/engine/domain/core_actions.py:489`). Clan has exactly one dissolution cause
(zero members AND zero assets), so it needs no separate "reason" field — the tick alone is a
complete outcome record for its own purposes.

**2. `CampState.active` — real, live, in-place terminal boolean on a retained record.**
`CampService.resolve_camp_clearing()` (`src/world/camp.py`) returns `CampUpdate(id=camp_id,
active_set=False)` — again, the `CampState` is **never removed** from `state.camps`; it stays with
`active=False`. A second real, independent confirmation of the same pattern.

**3. `WorldEventCategory.CAMP_CLEARED` / `PARTY_ABANDONED` — declared, but dead. Corrected after
initially assuming otherwise.** `docs/world/raid_boss_camp_contract.md` states "CAMP_CLEARED event
broadcast" on camp clearing, and `WorldEventCategory.PARTY_ABANDONED` already exists in the schema
with an entry in `CampaignOrchestrator`'s own category-weight table (`"entity_death", 0.4"`),
which looked at first like a ready-made mechanism for exactly this ticket's need. **Verified
directly rather than trusted, per this session's own standing discipline of checking a claim
against the real producer, not just its schema entry or doc text — and the claim doesn't hold.**
Grepped for every real construction site of `WorldEvent(category=WorldEventCategory.CAMP_CLEARED`
or `PARTY_ABANDONED` and confirmed `resolve_camp_clearing()` (read in full, above) does **not**
emit one — only sets `active_set=False` and applies a trauma delta. Both categories exist only as
declared enum values and orchestrator weight-table entries; neither has a live producer anywhere in
`src/`. **This is not a usable precedent to build on** — reusing either category would mean wiring
a genuinely new producer for previously-dead schema, not extending an established live mechanism.
Recorded here so a future reader doesn't repeat the same initial (wrong) assumption.

**4. `NarrativeLedgerEntry` / Chronicle — real, live, but campaign-mode-only and fed by
`recent_world_events`, which (per #3) neither Camp nor a hypothetical Group event currently
reaches.** `CampaignOrchestrator._advance_state()` converts `AuthoritativeState.recent_world_events`
into permanent, cross-episode `NarrativeLedgerEntry` records — genuinely durable, but only under
Campaign mode, and only for events that actually get emitted into `world_events_add` in the first
place (which, per #3, nothing currently does for either camp-clearing or party-ending). A
plain-Kernel run never reaches this layer at all; `recent_world_events` itself is a short, bounded,
one-tick-lagged sliding window, not a permanent log on its own.

## Conclusion from the precedent survey

The two *real, live* precedents (Clan, Camp) both use the same shape: **stop deleting the record on
its terminal transition; instead set an in-place terminal field and keep it in the durable
collection forever.** The event-based shape (`WorldEventCategory` → `NarrativeLedgerEntry`) that
looked like an existing mechanism for this turned out to be declared-but-unproduced for both
analogous cases checked — not a foundation to build on without also being the first real producer
for it, and even then it would only be durable under Campaign mode.

## Fit against this ticket's own actual need

The origin ticket's own `GroupSystem.find_group_for_contract()` (`src/systems/world_systems/
groups.py:337`) already has a docstring naming this exact ticket: *"Only finds groups while they're
alive -- dissolved groups are removed from state.groups outright... so this cannot answer the
question after dissolution (TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED)."* If Group
records stopped being deleted on dissolution (mirroring Clan/Camp), **this exact function keeps
working with no changes of its own** — it would simply start returning a dissolved-but-still-present
`GroupRecord` instead of `None`, and a caller checks `.dissolution_tick` for the outcome timing.
This is about as clean a fit as precedent-matching gets: the very function this gap blocks already
assumes, in its own comment, that the fix looks like "stop removing it."

`StateUpdate.groups_add_or_update: List[GroupRecord]` (`src/core/updates.py`) already supports
whole-record replace-in-place — the same field `update_groups()` already uses to write updated
`GroupRecord`s for still-alive groups. Marking dissolution would use the identical mechanism
(`dataclasses.replace(group, dissolution_tick=tick)` appended to `groups_add_or_update` instead of
`group_id` appended to `groups_remove`) — no new `StateUpdate` field needed.

## Real cost: consumers currently assume "present in `state.groups` == alive"

Retaining dissolved groups is not free. 11 files read `state.groups` today
(`src/domains/cooperation/services.py`, `src/domains/cooperation/phase.py`,
`src/engine/apply_plan.py`, `src/engine/executor.py`, `src/engine/tactical.py`,
`src/engine/checkpoint.py`, `src/engine/pipeline_phases/groups.py`,
`src/systems/social_systems/party.py`, `src/systems/world_systems/groups.py` itself,
`src/replay/fingerprint.py`, `src/core/dirty.py`). Each would need auditing for whether it assumes
"in the dict = currently active" — the same audit `ClanState`/`CampState`'s own consumers already
had to pass when *those* types adopted this pattern, so it's a known, bounded, but real cost, not a
free win. Not counted or estimated further here (out of this investigation's own scope, which is
the design question, not the implementation plan).

## Options

1. **Retain-with-terminal-marker (mirrors Clan/Camp, the only two real, live precedents found).**
   Stop deleting `GroupRecord`s on dissolution; populate the already-declared `dissolution_tick` in
   place via the already-existing `groups_add_or_update` mechanism. Directly unblocks
   `find_group_for_contract()`'s own documented gap with no changes to that function. Real,
   bounded cost: audit ~11 consumer sites for the "presence implies alive" assumption. Captures
   *when* a group ended, not *why* — matching this ticket's own explicit scope (reason
   differentiation is out of scope here, filed as future work).
2. **Wire up the event-based path (`PARTY_ABANDONED` → `world_events_add` → eventually
   `NarrativeLedgerEntry`).** Would require becoming the first real producer of a currently-dead
   category, and its durability guarantee is Campaign-mode-only (a plain-Kernel run's own
   `recent_world_events` window is short and lossy) — weaker fit for "answerable after the fact" in
   the general case, and doesn't reuse an established *working* mechanism the way Option 1 does,
   despite superficially looking like the more "correct" observability-shaped answer.
3. **Both**: Option 1 for the durable, queryable-by-contract-id record (the origin ticket's own
   actual need), plus a `WorldEvent` emission at the same dissolution sites for tick-scoped
   observability/simulation-quality visibility (becoming the first real producer for
   `PARTY_ABANDONED`, finally giving it one). More total work than Option 1 alone, but closes two
   real gaps (this ticket's, and the pre-existing dead-schema gap for `PARTY_ABANDONED`) instead of
   one, if that's judged worth doing together rather than separately.

## Recommendation: Option 1, with Option 3's event half as an optional, separable follow-up

Option 1 is the one directly evidenced by two real, live, working precedents in this exact codebase
(not just a plausible design), it requires no new `StateUpdate` schema (the field and the
add-or-update mechanism both already exist), and it is the *specific* fix the origin function's own
docstring already names as the missing half. Its real cost (the consumer audit) is disclosed above,
not hidden, and is the same shape of cost Clan and Camp's own adoptions already paid — a known
quantity, not a novel risk.

Reason-differentiation (leaving `dissolution_tick` as the only new signal, not a
`dissolution_reason`) is deliberately left for the actual contract-outcome-differentiation ticket
this one exists to unblock — building it now would be scope creep past what this ticket asks for,
and per its own Out of Scope, that follow-on work isn't this ticket's to do.

Wiring `PARTY_ABANDONED` (Option 3's event half) is a real, separable improvement — it's the
correct place for a currently-dead schema entry to finally get a producer — but it's not required
to close this ticket's own gap, and bundling it in isn't necessary if peer/user prefers to keep
this ticket narrowly scoped to Option 1 alone.

## Resolution (2026-09-14) — Option 1 approved and built

Peer approved Option 1 with two conditions: audit each of the 11 `state.groups` consumers
individually (not just assume retention is safe) and report which needed a filter; keep
outcome-semantics (what `dissolution_tick`/a future reason field should mean) as a separate
question for later, not decided inside this ticket.

The per-consumer audit found 2 real, previously-undiscussed hazards beyond the mechanism itself:
`GroupPhase.resolve()` (`src/engine/pipeline_phases/groups.py`) builds its own relevant-group-id
set directly from `state.groups.keys()`, bypassing dirty-tracking entirely — without a filter it
would re-run leadership elections and defection checks against every already-dissolved group,
forever. `CooperationPhase.execute()` (`src/domains/cooperation/phase.py`) iterates all of
`state.groups.items()` with no liveness check — without a filter, a dissolved group's former
(still-alive) members would keep receiving the "abandoned" trust/grudge social penalty every tick,
forever. Both fixed with the same `dissolution_tick is not None: continue` guard `GroupSystem.
update_groups()` itself needed for the `force_full_scan` fallback case. Full per-file audit table
in plan.md. See the ticket's own Implementation Notes/Test Summary/Files Changed for the complete
build record.
