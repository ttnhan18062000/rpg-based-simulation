---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261009-EPIC-SESSION-LEAD-PLANNER
phase: open
date: 2026-10-09
tags: [ai, process-improvement, governance]
---

# TCK-20261009-EPIC-SESSION-LEAD-PLANNER

## Title
Epic E — Session lead-planner: one cross-domain seat (project manager + technical lead) that tracks every session on every host, owns the cross-domain dependency and priority board, governs the tech stack, and advises the planners

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary

Several long-lived sessions now work on this repo, across two hosts. Domains: rpg, agent-working,
testing, codebase, asset, perf. Today the only thing above the domain planners is the owner, and
the owner rebuilds the cross-domain picture by hand: who is doing what, what is blocked on whom,
what should wait. The session layer (Epics A to D) gave each seat an identity, routing and a
per-host status view (`tools/sessions/status.py`). It has no view across hosts and no seat that
owns cross-domain sequencing.

On 2026-10-09 the owner asked for a **lead-planner** seat and decided two things:

- **Authority: advisory plus sequencing.** The lead tracks status, owns the cross-domain
  dependency and priority board, and sends `finding` / `question` / `fyi` messages and
  recommendations. **Work assignment still goes from the owner to a domain planner.** The lead is
  not added to any role's `accepts_dispatch_from`. Push, merge, grants and governing files stay
  owner-only. This is the smallest change to plan §9.0 ("information may bypass the hub; work
  assignment may not"): the lead is an information hub, not a dispatch hub.
- **Cross-host visibility: a committed heartbeat.** Each role session writes a small status
  record at start and stop. The record travels over the existing committed-transit mechanism
  (`tools/handover_transit.py`), so the lead sees the other host without a live network link.
  This lifts plan §12.5's deferral of "cross-machine sessions" **for status only**. Cross-host
  dispatch and wake stay deferred.

A third decision, on 2026-10-09: the lead is also the **technical lead** (project manager plus
tech lead). It owns the tech stack: architecture direction, frameworks, tooling and libraries.
Today nobody does. `tools/sessions/route.py` reports `unowned` for every file that defines the
stack: `pyproject.toml`, `uv.lock`, `Makefile`, `compose.yaml`, `docker/**`,
`dashboard-frontend/**`, `website/**`, `.mcp.json`, `.github/workflows/deploy-docs.yml` and
`docs/architecture/**`. Stack decisions are spread across ticket comments in `pyproject.toml` and
one-off ADRs. There is no inventory, version policy or adoption rule. This is the same pattern as
the advisory-plus-sequencing decision: the lead **owns the decision record** for the stack, and the
domain implementers still make the edits.

Evidence that the gap is real (lead-planner's first survey, 2026-10-09):
- Every seat in `status.py` shows `instance unknown`. There is no role-state directory, and every
  `manual_actions.jsonl` row on 2026-10-09 has `session_role: unresolved`. The live sessions run
  under names the roster does not know (asset-\*, perf-\*); PR #476 is the open fix.
- The u24desktop transit bundle, exported 2026-10-04 (148 files), had not been imported on any
  host five days later. Cross-host state is invisible unless someone goes and looks.
- Four worktrees on the import-linter and code-craft track had been idle 1 to 4 days, holding up
  to 21 unmerged commits, with nobody flagged as owning them.

## Scope

- **E1 — Lead seat. DELIVERED 2026-10-10 by PR #476 (`TCK-20261009-REGISTER-OTHER-HOST-SEATS`):** domain `lead`, one `planner` seat, in no `accepts_dispatch_from`, card `docs/guidelines/session_roles/domains/lead.md`, validator 17 roles / 0 findings. It also delivered E6's ownership half: `pyproject.toml`, `uv.lock` and `docs/architecture/**` route to `lead-planner` (the asset and perf ADRs are split out to their own domains). Not applied: `agent-working/lead/**`, which joins `owns` once its first file is on main (E4's board); `.github/workflows/pr-body-lint.yml` stays with delivery, but `route.py` still reports it `unowned` (follow-up for agent-working). Original scope: Register `lead-planner` in `registries/session_roles.yaml` as a cross-domain
  role (a `lead` function or a `lead` domain, decided in E1). It reads everything and may write
  only under `agent-working/lead/**` and `.claude/handover/**`. It is in no role's
  `accepts_dispatch_from`. Includes a generated card (within the 400-token budget) and a handover
  file. The `session_authority.yaml` diff, if any, is a governing-file edit and the owner confirms
  the literal text.
- **E2 — Fleet view.** `tools/sessions/fleet.py`, read-only, exit 0. Combines `status.py` (worktrees
  and seats) with open PRs per role/branch, in-progress and stale tickets and epics, how fresh each
  seat's handover is, the last monitoring activity per `session_role`, and pending transit bundles.
  Emits markdown and JSON. Answers: what is in flight, what is idle or orphaned, what is waiting on
  whom.
- **E3 — Cross-host heartbeat.** At SessionStart and Stop, a role session writes one small record
  (host, role, session id, branch, ticket, state, timestamp; no transcript content). The
  committed-transit path carries it to the other host, and `fleet.py` merges it in. A failed write
  never blocks the session (same rule as monitoring). Records older than a threshold show as
  `stale`, never as `live`.
- **E4 — Lead protocol and board.** Two message types: `status-request` (lead → any role,
  information only, no obligation to act) and `status-report`. Plus a durable cross-domain board,
  `agent-working/lead/board.md`, with one row per active epic or batch: owner role, state,
  depends-on, blocked-by, the lead's recommended next step, and whether the owner needs to decide.
  The board is advice; a planner's queue is still set by the owner.
- **E5 — Measurement hook-in.** Lead actions (status requests, recommendations, escalations to the
  owner) are recorded with `session_role: lead-planner`. The Epic D M7 review evaluates whether the
  lead lowers the headline metric (manual orchestration actions per completed batch).

- **E6 — Tech-stack governance.**
  - **Ownership:** `registries/session_roles.yaml` gives the lead seat the stack-root paths listed
    above, so `route.py` answers `lead-planner` for them. `frontend/**` stays with rpg and
    `visual_assets/**` with asset. A lockfile or `package.json` change in those domains needs a
    stack-registry entry, not lead ownership of the path.
  - **Inventory:** a tech-stack registry (`registries/tech_stack.yaml`, schema-validated). One entry
    per component (runtime library, framework, dev/lint tool, Node toolchain, container image, CI
    runner, MCP server), each with: owner domain, purpose, version policy (exact pin / floor /
    image tag), status on a tech radar (`adopt` / `trial` / `hold` / `retire`) and the ADR or ticket
    that introduced it.
  - **Decision rule:** adding a component, removing one, a major version bump, or a change of
    framework needs a short ADR under `docs/architecture/` that the lead reviews and the owner
    accepts. Patch and minor bumps inside the stated version policy need no ADR.
  - **Drift check:** report-only, exit 0. Compares `pyproject.toml`, `uv.lock`, the three
    `package.json` files, `compose.yaml` images and `.mcp.json` against the registry. Reports
    undeclared components, version-policy violations (for example an unpinned tool that a baseline
    depends on), the same framework at diverging versions across frontends, and floating container
    tags. Runs at retro, like the roster check.
  - **Seed review:** the first registry is filled from the current stack. It also records the
    findings the lead made on 2026-10-09 as stack-health items, each routed to its owning domain:
    - `mypy` is unpinned in the `dev` group, while `mypy-baseline` and the lint tools are pinned
      exactly. The mypy baseline can shift on a release with no code change.
    - `torch` is installed outside the lock (manual CPU-wheel step for the `knowledge` extra), so
      that environment is not reproducible from `uv.lock`.
    - `mcp` is declared twice (the `search-mcp` extra and `dev`).
    - Two React 19 + Vite 7 + Tailwind 4 + Radix apps (`frontend/`, `dashboard-frontend/`) have
      separate lockfiles and no shared workspace. `website/` (Docusaurus 3) is a third Node
      project. The versions match today but nothing keeps them aligned.
    - The `redis:7-alpine` image tag floats, while the observability images (Prometheus, Grafana,
      Loki, Promtail) are pinned.
    - Untracked clutter at the repo root (`uvicorn.log`, `replay_v2.json`, `scratch/`, `tmp/`, and
      `agent-monitoring/`, `reviews/`, `stored_artifacts/` outside `agent-working/` after the M-1
      root move).

## Out of Scope

- Any dispatch or queue-reordering authority for the lead (owner decision 2026-10-09).
- Cross-host dispatch, auto-wake, or a message inbox (still deferred; Epic D M7 decides on evidence).
- A batch registry separate from PR bodies (plan §12.5 stands).
- Changes to `Workflow` scripts or the delegated subagent roles.
- Applying the stack-health fixes from the E6 seed review. Each one is a ticket for its owning domain.
- Any automatic dependency-update bot, or a blocking gate on the stack registry (report-only until measured).
- Fixing the individual stalls the lead finds. Each goes to the owning planner as a `finding`.

## Acceptance Criteria

1. A session launched as `lead-planner` resolves its role, gets its card and handover, and
   `tools/sessions/validate.py` reports 0 findings with the new role.
2. `fleet.py` prints in one command, for both hosts: every seat with its instance state
   (live / orphaned / stale-heartbeat / none), its branch, open PR and current ticket; stale epics
   and tickets; and pending transit bundles. It exits 0 when `gh` or transit data is missing,
   showing `unknown` instead.
3. A seeded heartbeat from a second host appears in `fleet.py` after the transit import, and is
   shown `stale` once it is past the threshold.
4. A failing heartbeat write does not fail SessionStart or Stop (seeded failure test).
5. `agent-working/lead/board.md` exists with the agreed columns. A `status-request` /
   `status-report` exchange is documented in the message-class convention (plan §9.0 table updated).
6. Monitoring rows written by the lead carry `session_role: lead-planner`, and the `agent`
   vocabulary is unchanged (the `vocabulary_drift` ratchet does not move).
7. `registries/tech_stack.yaml` exists, validates, and covers every component that `pyproject.toml`,
   the three `package.json` files, `compose.yaml` and `.mcp.json` declare. The drift check is
   report-only, exits 0, and reports a seeded undeclared dependency and a seeded unpinned tool.
   `route.py` names `lead-planner` for `pyproject.toml`, `uv.lock` and `docs/architecture/**`.
   `docs/guidelines/` gains a short "adding or changing a stack component" rule, which links the
   ADR template.
8. Plan `session_layer_working_process.md` is amended: §9.0 adds the lead as an information hub,
   §12.5 records that cross-host status (not dispatch) has been lifted, and §12.3 records the
   owner decisions of 2026-10-09.

## Related Tickets

- `TCK-20261009-REGISTER-OTHER-HOST-SEATS` (PR #476, merged 2026-10-10) delivered E1 and the full roster.
- Sibling of the session-layer epics A to D (`agent-working/tickets/todos/session-layer/INDEX.md`).
  Feeds Epic D (`TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW`) via E5.
- Prior art: `TCK-20261004-SESSION-LAYER-M4A-STATUS-DISK-AND-RETIREMENT-REPORT` (status.py),
  `TCK-20261004-SESSION-LAYER-M3B-MESSAGE-CLASS-CONVENTION`,
  `TCK-20261004-SESSION-LAYER-M2A-ROLE-STATE-DIRECTORY-AND-LIVENESS`.

## Related Docs

- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding; §9.0, §11, §12.3, §12.5)
- `docs/guidelines/session_roles/`
- `docs/guides/agent_session_reset_boundaries.md`

## Related Stored Artifacts
None.

## Related Code Areas
`tools/sessions/` (roster, status, state, launch, card generation), `tools/handover_transit.py`,
`registries/session_roles.yaml`, `tools/agent-monitoring/` (session_role attribution); for E6:
`pyproject.toml`, `uv.lock`, `*/package.json`, `compose.yaml`, `docker/`, `.mcp.json`, `Makefile`,
`docs/architecture/`.

## Assumptions / Open Questions

- E1: whether "lead" is a new **function** (one cross-domain seat) or a new **domain** with one seat.
  The validator's one-domain-per-role and ownership-overlap rules decide this; the default is a
  function, because a lead owns no paths outside `agent-working/lead/**`.
- E3: the transit channel is a committed path today. If a heartbeat commit per SessionStart is too
  noisy, the heartbeat goes in the existing export bundle and refreshes on export. The lag is then
  one export, which the owner accepts (decision 2026-10-09).
- Domain routing: `agent-working/**` and `tools/sessions/**` belong to the agent-working domain, so
  the children are planned by the agent-working planner (interim holder: agent-working-designer).
  The lead-planner session drafted this epic at the owner's request.

## Implementation Notes

E1 is done (#476). Suggested order for the rest, non-binding: E2 (useful alone, on one host) → E6 (independent of E3/E4; the
seed review is useful immediately) → E3 → E4 → E5. E2 can start
before #476 merges, against the current roster. Child tickets are created by the agent-working
planner, or through `/create-tickets` if the owner asks.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
(Open.)
