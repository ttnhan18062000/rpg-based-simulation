# Session Layer — Epic Index

**Status: epics A–D scoped 2026-10-02; all open.** This folder holds **four epic-tier tickets only**. Child
tickets are created later by the agent-working planner, not here. This file is deliberately **not** named
`SEQUENCE.md`, because `implement-epic` reads that name as a child-ticket order.

Binding plan: `docs/plans/agent_infrastructure/session_layer_working_process.md`. The model: three functions
(designer, planner/reviewer, implementer), a full set of three seats per domain (`rpg`, `agent-working`,
`testing` now; UI, assets and others later), the **role id as the permanent identity**, and sessions as
disposable instances that hold a seat.

| Order | Epic | Starts when | Notes |
|---|---|---|---|
| 1 | `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (A) | now; **its M0 spike first** | identity, registry, launcher, recovery; the value core |
| 2 | `TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY` (B) | after A's M0 (hook and delivery results), M1 and M2 | routing, message classes, authority guardrails |
| 3 | `TCK-20261002-EPIC-SESSION-LAYER-OPERATIONS` (C) | after A's M1; parallel with B | status and hygiene tooling; justified by the 2026-10-02 disk incident; never blocks A or B |
| 4 | `TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW` (D) | M6a after A and B land; **M7 four weeks later** | time-gated; not a candidate for `implement-epic` until the data window elapses |

A is the critical path. B and C can run in parallel once A's registry (M1) exists. D is last by design.

**Why four epics.** The repo's epic rule is all-or-nothing, so one epic ending in a four-week soak could never
close. Splitting lets the core (A) ship and close, keeps hygiene (C) from gating the control-plane proof, and
isolates the time-gated review (D).

## Owner decisions (recorded 2026-10-02)

- One launcher command, `cc <role>`.
- The launcher may start role sessions with `crossSessionInbound = accept` (delivery only; it authorizes nothing).
- Agent-working drafts and implements the manifest and authority files; the owner confirms every authority diff.
- Standing grants have no default expiry and are revoked by deletion.
- Recovery default for an orphaned instance: offer resume, replace and inspect with evidence; suggest *resume*
  when the transcript is newer than the handover note, else *replace*; the owner chooses.
- Three functions and a full set of three seats per domain; `world-rules` is part of `rpg`.

## Owner decisions still open (none blocks M0)

1. Staffing `agent-working-planner` and `testing-designer`; until then `agent-working-design` holds the first and
   the second stays empty.
2. Confirm the practice changes (detail tickets move to the planner; `test-architecture-implementer` stops
   writing them; the implementer keeps committing the drafts the planner hands over).
3. Whether a new domain (UI, assets) may start with an unstaffed seat.

**Hold rule:** child tickets may be described by the detail planner, but **no M1 or M2 child may be activated
before M0 has recorded its go / adjust decision**, and no `settings.json` or hook change lands without the
owner's confirmation of the literal diff.
