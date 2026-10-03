---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG
artifact_type: investigation
tags: [observability, simulation-quality, progression]
---

# investigation.md — TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG

## Current Behavior

`event_extractor.py`'s "Quest progress lifecycle events" block iterated
`entity.strategic.projects.items()` (ALL strategic projects, any kind) with no
`isinstance(qstate, QuestState)` filter, and compared `.status` (the generic `ProjectStatus`
field inherited from `ProjectState`) rather than `.quest_status` (the `QuestStatus` field
`QuestService`/`QuestResolutionSystem` actually mutate) — both confirmed by the parent ticket
(`TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE`, Finding 2).

## A second, deeper bug found during Implement: the payload-carryover gap

Read `QuestEvent`'s class definition (`src/observability/events.py:134-151`) directly:
`status`/`quest_id` are top-level Pydantic fields on `QuestEvent`, never copied into
`.payload` by its `__init__` override (which only builds `message`). Read
`ObservabilityEventEnvelope.from_simulation_event()` (`events.py:28-41`) directly: it only
carries `event.payload` through to the envelope — `status` (a `QuestEvent`-specific attribute,
not a generic `SimulationEvent` field) is silently dropped in the conversion.

`quality_hub.py`'s `_translate_quest_event()` reads `(env.payload or {}).get("status",
"started")` — since `payload` was always `{}` for every `QuestEvent`, this **always** returned
the default `"started"`, regardless of the real status, even before this ticket's own fix. This
is a genuinely separate defect from the `.status`-vs-`.quest_status` field mismatch: even a
perfectly correct status *value* would never have reached the scoring translation layer, because
the conversion path that carries events to it structurally drops `QuestEvent`'s own typed fields.

Found and fixed inline (not filed as a separate follow-up) because it directly and completely
undermines this ticket's own stated fix — without it, the isinstance filter + `.quest_status`
read would be logically correct but functionally inert for the ticket's own stated purpose
(accurate quest completion/failure tracking reaching SimQ scoring). Same precedent as this
session's own `run_shadow_shapers()` default-lockstep fix (`TCK-20260806-PUSH-CUTOVER-PHASE2`) —
a bug discovered mid-implementation that would otherwise make the ticket's own change pointless.

**Not** fixed at the class level (`QuestEvent.__init__`/`ObservabilityEventEnvelope.
from_simulation_event()`) — confirmed via `src/observability/behavior/normalizer.py:244`
(`status = getattr(event, "status", None) or payload.get("status") or ""`) that a separate
consumer already correctly prefers the direct Pydantic attribute over payload, so a class-level
change risked altering behavior for that consumer too. Fixed narrowly at the two
`event_extractor.py` construction call sites instead: `payload={"status": <same string>}` passed
explicitly alongside the existing `status=` kwarg.

## `QuestStatus` has no `FAILED` value — a third, related finding

`QuestStatus` (`src/core/models/quests.py`) is `ACTIVE`/`COMPLETED`/`REWARDED`/`REWARD_PENDING`
only — no `FAILED` state exists in the real quest system at all, matching
`docs/simulation/quest_contract.md`'s own documented lifecycle
(`[generated] → ACTIVE → COMPLETED → REWARD_PENDING → REWARDED`, no failure branch). The
pre-existing test `test_quest_failed_confirmed_via_quest_event` (N-14) asserted behavior the real
type system cannot produce — the exact same class of bug (assuming quest-like status values that
don't actually exist on `QuestState`) this ticket fixes elsewhere. Corrected by replacing it with
a real terminal-state transition (`REWARD_PENDING` → `REWARDED`) rather than deleting coverage.

## `commitment_abandoned` — confirmed generic, kept independent of the QuestState gate

Traced `commitment_abandoned`'s own condition (`getattr(qstate, "status", ...) == ProjectStatus.
ABANDONED`) — reads the generic `ProjectStatus` field, applies to any project kind (quests,
`GoalKind`-typed AI goals, anything with a `.status`), and is translated via `quality_hub.py`'s
`_TRANSLATE_CONDITIONAL` into `project_abandoned` (AGENCY-scored), not quest-specific. Kept this
check structurally independent of the new `isinstance(qstate, QuestState)` gate — it now runs for
every project transitioning to `ABANDONED` regardless of kind, exactly matching its pre-fix
behavior for non-quest projects (previously it happened to be nested inside the same `elif` as
the buggy `QuestEvent` construction, but its own condition never depended on that nesting).

## Docs Requiring Update

None. No doc describes `quest_event`'s exact filtering/field semantics that would go stale — the
event type's existence and general purpose (already documented in `event_type_coverage.md`,
`docs/simulation/quest_contract.md`) remain accurate; this is a bug fix making the code match the
documented quest-lifecycle model, not a new documented capability.

## Parity Ledger Overlap

`quest_event` (translated to `quest_started`/`quest_completed`/`quest_failed`) is scored by
`NarrativeScorer`, not `ProgressionScorer`/`FactionScorer` — confirmed via
`src/simulation_quality/scorers/narrative.py`. New entry `SOC-241` added to
`docs/parity_ledger/social_narrative.yaml` (not `progression.yaml`, despite this ticket's own
tags — the parity file is chosen by the event's real consumer, not the ticket's own tag set).

## Prior Work

- `TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE` (Finding 2, DONE — source of this ticket)
- `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` (sibling, still open — the real quest system
  remains unreachable from live gameplay, confirmed again here via a real-kernel check showing
  `quest_event` count dropped to 0 post-fix, not to some nonzero "real quest" count)

## Risks and Open Questions

None left open.

## Anti-Drift Hazards

- Any future `SimulationEvent` subclass that declares its own top-level typed fields (like
  `QuestEvent.status`/`quest_id`) must either pass them into `payload` explicitly at construction
  time, or verify its consumers read the typed attribute directly (like `normalizer.py` already
  does) — `ObservabilityEventEnvelope.from_simulation_event()` only ever carries `.payload`
  through, silently dropping anything else. This exact gap will recur for any new subclass that
  doesn't account for it.
- Once `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` lands and real `QuestState` quests exist,
  `_translate_quest_event()`'s own vocabulary (only recognizing `"completed"`/`"failed"` as
  special, defaulting everything else including `"rewarded"`/`"reward_pending"` to
  `"quest_started"`) may need its own follow-up — not fixed here, since no real quest currently
  reaches those states to matter yet.
