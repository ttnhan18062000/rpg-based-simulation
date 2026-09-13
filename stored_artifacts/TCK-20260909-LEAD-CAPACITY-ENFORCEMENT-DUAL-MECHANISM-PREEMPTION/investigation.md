# Investigation — TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION

## Starting premise (from the ticket)

Two live mechanisms enforce `max_leads`:
- `DetourSuggestionSystem.enforce_bandwidth()` (`src/systems/strategic_systems/detour.py:146-179`),
  called early in the tick (from `fused_strategic_pass()` in
  `src/systems/strategic_systems/intelligence.py`, at three real call sites: lines 578, 878, 1729).
  Reads `entity.strategic.leads` as of the start of the tick only.
- `CapacityEnforcementPhase.enforce()` (`src/engine/pipeline_phases/capacity_enforcement.py:44-57`),
  the dedicated phase, running later in the pipeline. Reads `entity.strategic.leads` **plus**
  `strat_upd.leads_add_or_update` accumulated so far this tick — more correct, pending-update-aware.

The ticket's own cited evidence that preemption is real: a unit test
(`tests/unit/strategic/test_belief_staleness_decay_pipeline.py::
test_capacity_enforcement_prunes_newly_decayed_lead_over_fresh_ones`) had to call
`CapacityEnforcementPhase.enforce()` directly, bypassing `fused_strategic_pass()`, because
running the full pipeline against a **synthetically constructed 9-pre-existing-lead entity**
caused `enforce_bandwidth()` to prune it down to `max_leads` before the dedicated phase ever ran.

This confirms the mechanism *can* preempt when the precondition (an entity already carrying more
leads than `max_leads` at the start of a tick) is met. It does not by itself establish how often
that precondition is met in real play — that test constructs the precondition directly.

## Real call-site analysis: three sites, not one

`enforce_bandwidth()` is called from three places in `intelligence.py`, not the single site the
ticket's Request Summary describes:

- **Line 578** — unconditional, every tick, inside a block explicitly commented "Capacity
  Enforcement (unconditional, every tick)... Logic ID: STRAT-012". Result merged into `strat_up`
  if non-noop.
- **Line 878** — inside concern-list construction (Law 194), filters `new_concerns` by
  `bandwidth_upd.concerns_remove`. Concerns-specific; touches `leads_remove` only incidentally
  via the same call.
- **Line 1729** — inside route-switching logic (Law 194-197), merges `leads_remove` from both
  `memory_upd.leads_remove` and `bandwidth_upd.leads_remove` via set union.

All three ultimately call the same static method on the same pre-tick `entity.strategic.leads`
snapshot — the three call sites are different *trigger contexts* for invoking one
compute-then-merge operation, not three independent enforcement passes with different data. This
doesn't change the core finding below.

## Real-run instrumentation (the evidence the ticket's own AC asks for)

Per standing review instruction: "instrument a real run and count how often the dedicated phase
actually changes anything after the earlier pass has run." Wrote a monkeypatch harness
(`scratchpad/instrument_lead_capacity.py`, same pattern as this arc's prior trust/party-formation/
knowledge-fact instrumentation) patching both `DetourSuggestionSystem.enforce_bandwidth()` and
`CapacityEnforcementPhase.enforce()` directly, run against a real `frontier_living_world` episode,
`hero_guild_perspective`, seed 7, 500 ticks — the same scenario/seed used throughout this audit
arc for consistency.

**Result:**

```
capacity_phase_total_calls: 500          (once per tick — the phase itself is live, not dead)
capacity_phase_entity_updates_seen_total: 11703
enforce_bandwidth_total_calls: 10570     (called thousands of times — also live, not dead)
enforce_bandwidth_entities_leads_len_total: 0   (sum, across every one of 10570 calls, of len(entity.strategic.leads))

max_leads_len_seen (any entity, any tick, whole run): 0
max_leads_headroom_seen (leads_len - profile.max_leads): -8   (never even close; max_leads=8 for the one entity sampled)

pending_strat_upd_had_leads_add_or_update: (never incremented — zero occurrences)
capacity_phase_added_new_lead_removals_calls: (never incremented — zero occurrences)
capacity_phase_saw_existing_removal_added_nothing_new: (never incremented — zero occurrences)

Final-state direct check (independent third angle): 0 / 49 entities had any lead
at the last-observed tick.
```

Three independent measurement angles (running len() at every `enforce_bandwidth()` call; snapshotting
`entity_updates[*].strategic.leads_add_or_update` on entry to `CapacityEnforcementPhase.enforce()`;
direct inspection of live `state.entities` at the last-observed tick) all agree: **`entity.strategic.leads`
was empty for every entity, at every tick, for the entire 500-tick run.**

## What this means for the ticket's own question

Both mechanisms are real, live, and frequently invoked — not the "unreachable" pattern from
`TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`, confirming the ticket's own framing on that
point. But their shared trigger condition (`len(leads) > profile.max_leads`, with or without
pending adds) never evaluates true in a real run, because `len(leads)` is always 0. Neither
mechanism ever removes a lead under real conditions. There is no live preemption to resolve today:
`enforce_bandwidth()` cannot preempt `CapacityEnforcementPhase.enforce()` on a collection that is
always empty when either one looks at it.

This does not contradict the ticket's own cited unit-test evidence — that test built a 9-lead
entity by hand specifically to exercise the interaction. It shows the codepath is reachable and
the interaction is real *given that precondition*; it does not show the precondition itself is
ever reached organically.

None of the three original candidate dispositions (supersedes, genuinely complementary, ordering
bug) fits, because all three presuppose the preemption is actually happening in real play. The
honest finding is a fourth one: **the question is currently moot** — there is nothing to unify,
sequence-fix, or justify as complementary, because neither mechanism's own logic is ever exercised
against a non-empty `leads` collection under real gameplay.

## Why leads are never populated (traced one level further, to confirm this isn't an
instrumentation artifact — not to solve a new ticket)

Grepped every real `LeadState(...)` construction site in `src/` (excluding tests/certification/perf
fixtures) and checked reachability of each:

- `src/systems/social_systems/guilds.py:46` (`GuildIntelSystem.update()`, rumor-on-guild-visit
  path) — **zero callers anywhere in `src/`** outside its own definition and a passthrough
  re-export (`src/systems/guild_system.py`). Not gated — genuinely never invoked by the pipeline.
- `src/town/guild.py:31` (`GuildAction.visit()`, the guild-visit lead-grant action) — wired via
  `src/engine/pipeline_phases/guild_visit.py`, called from `pipeline.py:364`, but gated behind
  `ENABLE_GUILD_QUEST_GENERATION`, default `OFF` (`src/domains/optimization/feature_flags.py:91`).
  `frontier_living_world`'s own `world.yaml` does not override it.
- `src/systems/strategic_systems/intelligence.py:416` (`BeliefCycleSystem.process_observation()`
  call inside the belief-confirmation loop) — only iterates `entity.strategic.leads.values()`
  (already-existing leads) to confirm/deny them; the "new" `LeadState` it builds is immediately
  overwritten with the original lead's own `id` (`replace(l, id=lead.id, ...)`), so this updates an
  existing lead in place — it can never seed the collection from empty.
- `src/engine/pipeline_phases/paid_information.py:158` (`PaidInformationTransactionSystem.enforce()`)
  — wired unconditionally in `pipeline.py:370` (no feature-flag guard), but requires a registered
  `InformationProvider` for the transaction to proceed. Grepped every `InformationProvider(...)`
  construction site in `src/` — **zero real construction sites anywhere**, in any world. Not
  flag-gated; the precondition is structurally unreachable everywhere.
- `src/strategy/leads.py` (two more `LeadState(...)` sites) — **zero callers anywhere in `src/`**.
  Dead.
- `src/domains/information/normalizer.py`, `src/world/providers/information.py` — feed into the
  already-known `InformationBeliefPhase` / `ASK_INFORMATION` paths documented as inert end-to-end
  by `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` (pending-response
  threading gap; `ENABLE_INFORMATION_INTENT_EXECUTION` default off).

Every real lead-creation path is either dead code with zero callers, gated off by an existing
documented flag not enabled by this world, structurally unreachable (a class never constructed
anywhere), or an update-only path that requires a lead to already exist. This is consistent with —
and explains — the empty-collection finding above; it is not an artifact of the instrumentation.

**This lead-creation-reachability gap is new scope, not something this ticket asked to resolve.**
It is flagged to peer review as a candidate for its own investigation ticket (same "inert end to
end" shape as the knowledge-fact ticket), not decided or filed here.

## Evidence this is not an instrumentation bug

- Both patched functions are confirmed hit thousands of times (not a silent no-op patch — a
  broken patch would show 0 total calls, not 0 non-empty results).
- The field read (`entity.strategic.leads`) is identical in the instrumentation, in
  `enforce_bandwidth()` itself, and in `CapacityEnforcementPhase.enforce()` — no mismatched
  attribute path.
- Three independently-implemented measurements (running tally, pending-update snapshot, final-state
  direct read) agree with each other.
