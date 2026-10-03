# Investigation — TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION

## Headline: a genuine refinement of the parent audit's own conclusion

`TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`'s dominant pattern — "this codebase repeatedly
accumulates superseded implementations left alongside their live replacements" — held cleanly for
`BiologicalSystem`, `spawn_calamity()`, `effective_certainty()`: a live replacement fully covers the
dead module's job, delete with confidence.

**It does not hold cleanly here. Every one of these 8 modules is partially superseded, with
orphaned unique capability.** A live mechanism took over the *core* job in every case — but in 7 of
8, something the dead module alone did went with it when the live replacement was built, and no
one carried it forward. "Superseded" in this package is not automatically "safe to delete" —
supersession here has been partial, not total. That distinction matters past this one ticket:
the next person reading `docs/audits/unreachable_code_inventory.md` and seeing "superseded" next to
a module name should not read that as "delete the file" without checking whether the supersession
was total or partial. This package is direct evidence it can go either way.

**The risk this creates, and the one to guard against explicitly in every disposition below:** the
unique capability lives inside the same file, often the same class, as the superseded part. A
disposition phrased as "delete `degradation.py`" reads completely differently from "delete
`GracefulDegradationManager`'s pressure-level computation; `should_skip_phase()`'s whole-phase-skip
and `resolve_content_source()`'s catalog-preference-under-pressure have no live equivalent and need
their own decision." Every disposition below is written at the second resolution, not the first,
specifically so a future reader doesn't do the coarse thing.

## Method

Manual, module-by-module pass, per standing instruction — not another automated sweep. The
audit tool's own generic-name blind spot (`cache_strategy.py`'s `CacheKey`/`CacheStrategy` never
appeared in its output at all) means grep-first, narrow-keyword checks are insufficient on their
own; each module below was checked against the *real* live mechanism doing its job today, verified
by reading that mechanism directly, not assumed from a keyword match.

**A parallel version of the same blind spot showed up mid-investigation, in manual form, worth
recording explicitly for whoever does this kind of pass next**: the first check on
`trace_governor.py` used a narrow keyword grep (`max_trace_events`, `trace_volume`,
`TraceVolumeGovernor`) and would have concluded "genuinely missing" — wrong. Checking the broader
live event-volume-management system directly (`EventRecorder`, which shares no vocabulary with
`trace_governor.py` at all) found a real, live, functionally-overlapping mechanism instead (see
#8). The lesson generalizes: a keyword search — automated or manual — can only find what already
uses the same words. The reliable check is "what live mechanism does this job," read directly, not
"does this live mechanism's name/vocabulary match."

Peer review's own `degradation.py`/`governor.py` finding was treated as a lead, not a conclusion,
and re-verified independently below (see #1) — it held for the core job, but not fully: acting on
"superseded, delete" as originally framed would have deleted `should_skip_phase()`'s and
`resolve_content_source()`'s real, undocumented-elsewhere capability. This is the second time this
arc a lead would have caused real loss if inherited rather than verified.

## 1. `degradation.py` (`GracefulDegradationManager`) vs. `governor.py` (`ResourceGovernor`)

**Core pressure-level computation: confirmed superseded.** Both react to compute pressure by
escalating through discrete levels computed from a tick-time ratio
(`GracefulDegradationManager.update_pressure()`: `ratio = tick_time_ms / limit_ms`, four levels;
`ResourceGovernor._get_indicated_mode()`: `signals.tick_compute_ms` vs.
`profile.max_tick_budget_ms` at multiple thresholds, four `RuntimeMode` levels). Different specific
thresholds and a richer live model (also considers `work_debt_total`, `memory_estimate_mb`,
`worker_utilization`, `queue_utilization`, with hysteresis via dwell time + confidence window +
recovery watermark — `ResourceGovernor._can_recover()`). Confirmed `ResourceGovernor` is live: its
own `evaluate()` return value (`GovernorPolicy`, including `phase_budgets`) is consumed by the real
kernel tick loop (`src/engine/kernel.py`), and `RuntimeMode` transitions are directly observable —
watched a real `[ALERT] type=WatchdogTrip` fire during this ticket's own instrumentation runs
earlier in this arc.

**But two specific consumer-facing methods have no live equivalent — this is the qualification
that changes the disposition from clean "delete":**
- `should_skip_phase(phase_name)` — skips entire named optional phases
  (`ENABLE_WORLD_EMERGENCE`, `ENABLE_LIFE_ARC_CAMPAIGNS`, `ENABLE_COOPERATION`) outright under
  DEGRADED/CRITICAL. Checked the live pressure-response mechanism
  (`PhaseBudgetGovernor.evaluate()`, `src/engine/phase_governor.py:44-143`): it only throttles
  *budgets* (`candidate_budget`, `movement_budget`, `scan_policy`, `strategic_budget`) — it never
  disables a whole named phase by feature flag. `GovernorPolicy`/`RuntimeMode.SURVIVAL` scale
  numbers down; nothing skips a phase outright. No live equivalent.
- `resolve_content_source()` — under degraded/critical pressure, prefers catalog-driven content
  over hardcoded static defaults, cheapest-first. Grepped for any comparable "prefer catalog under
  pressure" logic anywhere in `src/`; found none. No live equivalent.

**Disposition: the pressure-level computation itself is superseded (delete that part with
confidence) — but `should_skip_phase()`'s whole-phase-skip capability and
`resolve_content_source()`'s catalog-preference-under-pressure are genuinely distinct capabilities
that don't exist live anywhere.** Neither is currently exercised (nothing calls
`GracefulDegradationManager` at all), so nothing observable breaks today either way — but deleting
the whole module would foreclose ever recovering these two specific ideas without reinventing them.

## 2. `budget_manager.py` (`PhaseBudgetManager`) vs. live `GovernorPolicy`/`PhaseBudgets`

**Not the same mechanism, despite solving an adjacent problem — a genuinely different
architecture, not "same implementation, different numbers."** Live `PhaseBudgets`
(`src/engine/policy.py`, computed by `PhaseBudgetGovernor.evaluate()`) is a set of *pre-computed,
declarative* per-tick limits (`candidate_budget`, `movement_budget`, `strategic_budget`,
`scan_policy`) that individual phases are expected to respect by convention — decided once per
tick, before any phase runs. `PhaseBudgetManager.check_and_consume()` is a *stateful, imperative*
running-total tracker: call it every time you're about to spend, it increments and rejects once
over (`"Time budget exhausted"`, `"Entity limit exhausted"`, etc.), a reusable enforcement
primitive rather than a set of numbers other code must remember to respect on its own.

`max_provider_calls_per_tick`/`current_provider_calls` and `max_trace_events_per_tick`/
`current_trace_events`: checked for live enforcement (not just counting) of either — found none
under the narrow keywords, see #7 and #8 below for the broader check that changed one of those
answers.

**Disposition: genuinely missing, not superseded.** The live system provides declarative
per-tick budget *numbers*; nothing provides `PhaseBudgetManager`'s own imperative "consume and get
rejected mid-tick" enforcement primitive. Whether that primitive is actually needed (do any real
phases need mid-tick rejection rather than a pre-tick cap?) is a real design question, not decided
here.

## 3. `cache_strategy.py` (`CacheStrategy`/`CacheKey`) vs. `WorldIndexService` and `admission_control.py`

**`admission_control.py`'s own comments are misdirecting in a specific, narrow way — corrected
below in Files Changed once picked up for implementation.** Its comments (`admission_control.py:
59-60,96-97`) cite `cache_strategy.py` by name and line number as if `CacheStrategy` is the live
implementation being extended or reused. It is not. `admission_control.py` implements its own,
separate, per-*API-client* token-bucket rate-limiter (`_ClientAdmissionState`: tokens, mode,
dwell_count — itself a reuse of the `ResourceGovernor` hysteresis pattern, a different borrow than
the cache one) and only borrowed `CacheStrategy.put()`'s *LRU-eviction shape* (`_keys_order`
recency list, evict-oldest-on-overflow) as an implementation pattern reference — it does not
import, construct, or depend on `CacheStrategy` at all. Confirmed via read: `admission_control.py`
never imports from `src.domains.optimization`.

**`CacheStrategy`'s own real target domain — caching region-scoped world-query results
(`resource_nodes`, `shop_stock`, `services`, `pressure`), invalidated by event type — partially
overlaps a real live mechanism, `WorldIndexService`/`WorldIndexes`
(`src/engine/world_index.py`).** That service caches `active_resource_nodes` (plus buildings/
entities/ground_items/corpses) as a spatial index, invalidated via `CacheInvalidationPolicy.
should_invalidate(domain, dirty)` against the real `DirtySet` — a different mechanism
(DirtySet-driven wholesale-rebuild-per-tick vs. `CacheStrategy`'s own per-key LRU with bespoke
`event_type`-string invalidation) doing an overlapping job for the `resource_nodes` category
specifically. `shop_stock`/`services`/`pressure` query caching has no live equivalent found
anywhere.

**Disposition: mixed, narrower than it first looks.** `resource_nodes` caching: superseded by
`WorldIndexService` (different mechanism, same data). `shop_stock`/`services`/`pressure` caching:
genuinely missing, no live equivalent. `admission_control.py`'s comments should be corrected
regardless of `cache_strategy.py`'s own eventual disposition — they currently read as though
`CacheStrategy` is a live dependency, which it isn't.

## 4. `dirty_scheduler.py` (`DirtyWorkScheduler`) vs. `src/core/dirty.py` (`DirtySetBuilder`/`DirtySet`)

**The "mark X dirty" surface overlaps the live `DirtySetBuilder.mark_entity()` closely** (both take
an id and a reason/tag). But `DirtyWorkScheduler.next_entities(phase_name, count)`/
`next_regions(phase_name, count)` provide a genuinely distinct capability: bounded, incremental,
cross-tick batch draining of a persistent dirty backlog (`clear_processed_entities()` only removes
what was actually processed, leaving the rest for the next call). Confirmed via read: `DirtySet`/
`DirtySetBuilder` (`src/core/dirty.py:58-`, `212-`) have no `next_*`/batch-scheduling methods at
all — the live mechanism computes the full dirty set fresh every tick with no persistent backlog
concept.

**Disposition: the "mark dirty" primitive is superseded; the persistent, bounded, cross-tick batch-
scheduling capability is genuinely missing**, with no live equivalent anywhere in the engine
(everything else this whole audit arc has found processes its full dirty set in one pass, every
tick — see `CapacityEnforcementPhase`, `ReadModelCache`'s own recent fix, etc.).

## 5. `memory_limits.py` (`MemoryCapacityLimits`) — the most fragmented of the 8

Four independent bounded-eviction categories (`facts`, `opponents`, `rewards`, `coop_memories`),
each needing its own check — confirmed they do NOT share one disposition:

- **`add_fact()`**: superseded. `InformationAssimilationService.assimilate()`
  (`src/domains/information/assimilation.py:48-53`) already enforces `max_facts=10` inline, with a
  different eviction algorithm (oldest-first, per the code comment in `action_intent.py:158`) vs.
  `MemoryCapacityLimits`'s own salience+timestamp sort — same job, different implementation, live
  (though currently unexercised for unrelated reasons — `assimilate()` fires zero times in a real
  run, per `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` — that's a
  separate, already-filed finding, not this ticket's to re-litigate).
- **`add_opponent()`/`add_reward()`/`add_coop_memory()`**: NOT "missing capacity enforcement" —
  something more fundamental. Grepped `src/core/strategic.py` and the rest of `src/core/` for any
  "opponent salience"/"reward salience"/"cooperation memory" tracked state at all; found none. The
  underlying state concepts these three methods would bound don't appear to exist anywhere in the
  current cognition model (`entity.strategic.leads/concerns/hypotheses/projects`, the real bounded
  categories, are a structurally different design — confirmed via the lead-capacity ticket earlier
  this arc). This reads as an orphaned design direction (early RL-flavored opponent/reward modeling,
  never adopted in any form) rather than a capability gap in the current one.

**Disposition: `add_fact()` superseded; `add_opponent()`/`add_reward()`/`add_coop_memory()` refer
to state that was never built, in either form — not a wiring gap, an abandoned design.**

## 6. `diagnostics.py` (`DeveloperDiagnostics`) vs. the live alerts/observability system

**Confirmed superseded, cleanest case of the 8.** `DeveloperDiagnostics` is a simple
record-issue/generate-report aggregator. A much richer, confirmed-live, load-bearing observability
system already exists and does the same job: `AlertsManager`/`AlertRouter`/`AlertSink`
(`src/observability/alerts/`), with real routing, deduplication (`AlertDeduplicator`), and multiple
sinks (`LogAlertSink`, `WebhookAlertSink`) — directly observed firing (`[ALERT] type=WatchdogTrip`)
during this ticket's own instrumentation runs. No unique behavior in `DeveloperDiagnostics` that
isn't already better-served live; its own docstring ("Aggregates optimization, budget skip, and
cognition failure diagnostics") depends entirely on inputs from the other 7 dead modules, which
themselves rarely/never fire, so even wired it would have had little to report.

## 7. `provider_enforcement.py` (`ProviderBudgetEnforcement`) — genuinely missing

Wraps a generic `provider_func: Callable[[], List[Any]]` call with a call-count budget and rejects
"global scan" attempts (missing `entity_id`/`region_id` scope) without a debug flag. Checked
`src/world/providers/` and `src/domains/information/` — the real consumer paths for provider-shaped
calls investigated extensively in `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-
INVESTIGATION` — for any live call-budget or scope-rejection logic; found none. The only live
`provider_call_count` references (`src/observability/performance/{models,profiler}.py`) are passive
metrics counters, not enforcement — they record how many calls happened, they don't cap or reject
any. Also checked `admission_control.py`'s own token-bucket rate limiter, since it's the other real
rate-limiting mechanism in the codebase: it operates per-API-client (`_ClientAdmissionState`,
keyed by `client_id`), a different scope entirely from per-tick, per-simulation-domain provider
calls. No live equivalent at any scope.

**Disposition: genuinely missing, no live equivalent found anywhere, at any scope.**

## 8. `trace_governor.py` (`TraceVolumeGovernor`) — correction made mid-investigation

**Initial narrow grep (`max_trace_events`, `trace_volume`, `TraceVolumeGovernor`) found nothing and
would have wrongly concluded "genuinely missing."** Caught this before finalizing, per the standing
"verify, don't assume" discipline and peer review's own explicit warning about the audit tool's
generic-name blind spot — the same risk applies to a narrow manual grep, not just the automated
tool. Checked the real, broader live event-volume-management system instead:
`EventRecorder` (`src/observability/event_recorder.py`) has its own confirmed-live `max_events` cap
(`BoundedObservabilityQueue`), mode-based severity dropping (DEGRADED mode drops INFO/DEBUG,
keeps WARNING+), and its own drop-count tracking (`dropped_event_count`,
`_events_dropped_by_mode`) — directly analogous to `TraceVolumeGovernor.process_events()`'s own
keep-hard-laws-and-high-severity / cap-and-drop-the-rest logic, via a different specific mechanism
(bounded queue + severity tier vs. category allow-list + per-tick numeric cap).

One capability check remains open: `TraceVolumeGovernor`'s "repeated message summarization"
(collapse N identical messages into one representative event annotated with a count). The closest
live analogue, `AlertDeduplicator.should_suppress()` (`src/observability/alerts/deduplicator.py`),
does time-window-based full suppression (boolean skip), not summarize-with-count, and only applies
to the separate alerts pipeline, not general trace events. No live summarize-with-count behavior
found for general trace events.

**Disposition: core volume-bounding job is superseded by `EventRecorder`'s own mechanism (confirmed
live and load-bearing). The specific "summarize N repeats into one counted entry" behavior (as
opposed to suppress/drop) has no live equivalent** — a narrower, more specific gap than the whole
module first appeared to represent.

## Summary table

| Module | Core job | Genuinely unique behavior (no live equivalent) |
|---|---|---|
| `degradation.py` | Superseded (`ResourceGovernor`) | `should_skip_phase()` (whole-phase skip), `resolve_content_source()` (catalog-under-pressure) |
| `budget_manager.py` | Genuinely missing (different enforcement model than live `PhaseBudgets`) | The whole imperative consume-and-reject primitive itself |
| `cache_strategy.py` | Mixed — `resource_nodes` superseded (`WorldIndexService`) | `shop_stock`/`services`/`pressure` query caching |
| `dirty_scheduler.py` | "Mark dirty" superseded (`DirtySetBuilder`) | `next_entities()`/`next_regions()` bounded cross-tick batch draining |
| `memory_limits.py` | `add_fact()` superseded (`assimilate()`'s own cap) | `add_opponent()`/`add_reward()`/`add_coop_memory()` — state that was never built, not a gap |
| `diagnostics.py` | Superseded (`AlertsManager`/`AlertRouter`) | None found |
| `provider_enforcement.py` | Genuinely missing | Entire module — no live equivalent at any scope |
| `trace_governor.py` | Superseded (`EventRecorder`'s own volume bounding) | "Summarize N repeats into one counted entry" specifically |

No module is a clean "confirmed superseded, delete outright" case except `diagnostics.py`. No
module is a clean "confirmed genuinely missing, wire in as-is" case either —
`provider_enforcement.py` comes closest, but "as-is" isn't established (its specific numbers/API
shape were never validated against real usage, since nothing has ever called it).

## Disposition and follow-up tickets

Grouped by decision type, per peer review's explicit direction — 8 modules would fragment one
question into eight if filed per-module. Every disposition below is written at method/behavior
granularity, not file granularity, per the risk named in the Headline section above.

**A — Clean deletion (mechanical, no design question).**
`diagnostics.py` (`DeveloperDiagnostics`, `DiagnosticIssue`) — the whole file. Confirmed superseded
by `AlertsManager`/`AlertRouter`, nothing unique found. Filed as its own hotfix ticket.

**B — `memory_limits.py` (its own disposition, not grouped with A or C — the reasoning differs from
both).** `add_fact()`/`MemoryFact`/`get_facts()`: superseded by `InformationAssimilationService.
assimilate()`'s own inline cap — delete. `add_opponent()`/`add_reward()`/`add_coop_memory()`: NOT
orphaned capability in the sense C below means it (a real behavior nothing else does) — the state
these methods would bound (opponent salience, reward salience, cooperation-memory salience) doesn't
exist anywhere in the current cognition model. Document as an abandoned design direction, not a
capability gap; nothing is lost by deleting these methods too, since there's nothing for them to
track. Whole file deletable, but with distinct rationale per half — filed as its own hotfix ticket,
not folded into A, so the "abandoned design, not a gap" reasoning isn't diluted by A's simpler
"superseded, nothing unique" framing.

**C — Orphaned-capability determination (one decision session, one ticket, five capabilities).**
Whether each of these 5 is actually wanted is a single question worth deciding together, since
they're the same shape of question (a real capability the codebase never carried forward when its
containing module's core job was superseded elsewhere):
- `degradation.py`'s `should_skip_phase()` (whole-phase skip under pressure, by feature flag name)
  and `resolve_content_source()` (catalog-preferred-under-pressure content resolution) —
  `get_provider_cap()` bundled here too, since it's the same "scale a number down under pressure"
  pattern `GovernorPolicy` already applies to other budget categories, just never extended to this
  one; if any of the three is kept, it should be rescoped to read pressure level from
  `ResourceGovernor`'s own `RuntimeMode` rather than reviving `DegradationLevel` as a second,
  parallel pressure signal — do not let `update_pressure()`/`get_level()`/`DegradationLevel` survive
  as a shim just to feed these three; that recreates the exact dual-mechanism-preemption shape this
  arc has already found real elsewhere (`TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-
  PREEMPTION`).
- `cache_strategy.py`'s `shop_stock`/`services`/`pressure` region-scoped query caching (the
  `resource_nodes` use case is redundant with `WorldIndexService` regardless of this decision).
- `dirty_scheduler.py`'s `next_entities()`/`next_regions()` bounded, cross-tick batch draining of a
  persistent dirty backlog (the `mark_entity_dirty()`/`is_entity_dirty()` surface is redundant with
  `DirtySetBuilder`/`DirtySet` regardless).
- `trace_governor.py`'s "summarize N repeated messages into one counted entry" behavior specifically
  (the cap-and-keep-important-events job is redundant with `EventRecorder`'s own volume bounding
  regardless).

For each of the 5: if not wanted, delete the whole containing module/class (including its
superseded core — nothing is served by it surviving standalone once its unique reason for existing
is declined). If wanted, the real implementation shape is a separate question from this
determination — likely rescoped to plug into whichever live mechanism (`ResourceGovernor`,
`WorldIndexService`, `DirtySet`, `EventRecorder`) already owns the adjacent, superseded half, not a
revival of the dead module's own parallel state. Filed as one standard-tier ticket.

**D/E — Genuinely missing (separate tickets, separate questions).**
`budget_manager.py`'s imperative, stateful "consume and reject mid-tick" budget-enforcement
primitive and `provider_enforcement.py`'s provider-call rate limiting + global-scan rejection are
each their own "should we build this" design question, not a cleanup — filed as two separate
standard-tier tickets, per peer review's explicit instruction. Worth checking during either
ticket's own Investigate phase whether the two overlap specifically on provider-call budgeting
(`budget_manager.py`'s own `max_provider_calls_per_tick` vs. `provider_enforcement.py`'s own
`max_calls`) — flagged as a real possibility, not resolved here.
