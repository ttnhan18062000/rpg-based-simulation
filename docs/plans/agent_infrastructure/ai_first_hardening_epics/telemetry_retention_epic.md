---
status: active
layer: observability
authority: P1
audience: agent
date: 2026-09-04
tags: [ai, agent-monitoring, data-quality]
---

# Epic Plan — Telemetry & Retention

**Tracking ticket**: not yet created (planning stage — detail plan and milestones only).
**Source**: `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Rev.3, Bucket A / Horizon 1 item
"agent-monitoring/tools.jsonl rotation — coherent hot→archive→index lifecycle", grouped with the
broader artifact-retention and subsystem-ownership work the same epic covers.
**Roadmap**: `roadmap.md` — Horizon 1, no hard dependency on the Horizon-0 gate.
**Priority**: P1 for the still-open scope (M2/M3 below). M1 is **superseded — already shipped**,
found and confirmed during planning discussion (see below).

## M1 is superseded — do not implement, already done

While designing M1 in this session (write-time sharding + reconciliation-before-deletion, to fix
the rotation race and the "ingestion exit code ≠ verified" gap), a search of this repo's other
active worktrees turned up **`TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC`** and its immediate
successor **`TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`** — both `DONE`, merged to `main` via
PR #112 (confirmed `MERGED` via `gh pr view 112`, and confirmed present on `main` after this
session pulled). This is not a partial or superficial overlap — it solves the same problem more
thoroughly than this session's own M1 design did:

- **Final shipped layout**: `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` — one
  folder per UTC ISO week, covering all three monitoring sources (this session's M1 only covered
  `tools.jsonl`/`events.jsonl`; the shipped work also unified `runs.jsonl`).
- **Real reconciliation, already exact**: the migration verified `179243 + 190 live = 179433`
  before retiring the monolithic file — a literal, exact accounting, stronger than the
  `raw == ingested + rejected` invariant this session had only proposed.
- **Referential-integrity verification already built and shipped**
  (`tools/agent-monitoring/verify_referential_integrity.py`, child ticket 6 of the unified epic):
  joins `events.run_id → runs.run_id` and `tools.(run_id, seq) → events.(run_id, seq)`,
  cross-week-boundary aware, report-only (never gating), confirmed against real corpus violations
  (~12.7%/18 real orphans already present, not hidden).
- **Every real consumer migrated** — 9 core scripts, gate checks, the Agent Ops Dashboard backend,
  and the Codex-runtime-activation subsystem's shared shard-resolution helper. This closes the
  exact "sharding breaks every hardcoded reader" gap this session separately found (originally
  raised as a concern in this planning discussion, before the pre-existing epic was found) —
  already solved for all ~10+ real consumers, not just named as a risk.
- **4 real, live, silently-broken production bugs fixed** during the shipped work (e.g.
  `record_events.py` had been silently computing `tool_call_count=0`/wrong `cost_proxy_score` on
  every event since 2026-09-02, because it still read the now-empty legacy `tools.jsonl` path) —
  bugs this session's own M1 design would not have caught, since it was designed without knowledge
  of the existing consumer inventory.
- **257+ tests passing**, independently re-verified by both `architecture-reviewer` and
  `done-checker`, not just the implementer's self-report.

**Action for this epic**: none. The work is done and live on `main`. This session's earlier M1
draft (write-time sharding, the reconciliation-invariant table, per-shard metadata) is retracted
in favor of the shipped design — recorded here as a note that the concern was real and independently
re-derived, not as a competing proposal to still build.

## Problem (remaining scope only)

The shipped epics above cover `runs.jsonl`/`events.jsonl`/`tools.jsonl` exclusively. They do **not**
touch the rest of this repo's artifact classes — `stored_artifacts/`, `tickets/done/`,
`working_log.csv`, `graphify-out/`, `knowledge-index/` all still have real, uncoordinated
lifecycles that have never been classified together. That gap is this epic's remaining scope.

## Scope

### M2 — Artifact retention classification, repo-wide (gated on nothing)

Classify every artifact class the repo produces, using the four categories the freeze pass
established (Ephemeral / Run-scoped / Ticket-scoped / Long-lived / Institutional):

| Artifact class | Classification | Recommended treatment |
|---|---|---|
| `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` | Operational telemetry | **Already resolved** — see M1 note above; referenced here only for completeness of this table |
| `stored_artifacts/{id}/` | Ticket-scoped → institutional knowledge | Keep permanent |
| `tickets/done/*.md` | Institutional knowledge | Keep permanent |
| `agent-monitoring/retro/RETRO-*.md` | Aggregated retrospective / institutional knowledge | Keep permanent |
| `working_log.csv` | Aggregated retrospective (currently data-quality-broken) | Keep permanent once its parser is fixed — see `standalone_items.md` |
| `graphify-out/` | Derived operational index (rebuildable) | **Open question** — insufficient evidence on CI/dev workflow needs to recommend build-output vs. tracked treatment; this milestone's output should resolve it with real evidence, not carry the "open question" forward a second time |
| `knowledge-index/` | Derived operational index (rebuildable) | Same open question as `graphify-out/` |
| `.claude/current_run` sidecar(s) | Ephemeral / run-scoped | Already correctly ephemeral — no change needed |

This milestone's deliverable is a committed doc recording this table as reviewed fact, with the
two open questions either resolved or explicitly still-open with a named follow-up owner.

### M3 — Ownership & lifecycle documentation for new/changed subsystems (gated on nothing)

For every *remaining* subsystem this epic and its siblings touch, record an accountable role (not
a person — see the roadmap's shared role vocabulary), an update trigger, a staleness signal, and a
removal condition:

| Subsystem | Accountable role | Update trigger | Staleness signal |
|---|---|---|---|
| Capability-envelope baseline (from `governance_capability_policy_epic.md`) | Agent Configuration Maintainer | Any new legitimate permission need | Baseline diverges from a working local file |
| Ticket-claim detection log (from `workflow_reliability_epic.md`) | Workflow Runtime Maintainer | Continuous | Zero incidents after 30 days |

The `agent-monitoring/data/` weekly-shard layout's own ownership is a matter for whoever maintains
the already-shipped `TCK-20260902/903-MONITORING-*` epics' code — not re-assigned here.

This milestone documents ownership for this epic's own remaining subsystems and cross-references
the sibling epics' rows rather than duplicating their content — one ownership table, referenced
from every epic doc, not restated in each.

## Out of scope

- Re-implementing anything in the M1 note above — it is done, on `main`, verified.
- Rewriting `.git` history to shrink what the already-shipped migration retired — not this epic's
  concern, and the shipped work's own design already chose recoverable-via-`git log --follow`
  over history rewriting, consistent with this repo's general practice.
- Resolving the `graphify-out/`/`knowledge-index/` git-tracking question by assertion — M2 either
  resolves it with real evidence or leaves it open with a named owner, never guesses.

## Acceptance signal for this epic

- M1: none required — already shipped and verified upstream.
- M2: a committed retention-classification table covers every remaining artifact class in the
  table above, with the two open questions either resolved or explicitly assigned a follow-up
  owner.
- M3: an ownership table exists for the remaining subsystems and is cross-referenced from this
  epic's sibling docs rather than duplicated.

## References

- `roadmap.md` — Horizon-1 placement.
- `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` — §"Telemetry & artifact lifecycle" (the source
  of M2's table; its M1-equivalent content is now superseded by the shipped work above).
- `tickets/done/agent-monitoring-weekly-sharding/TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC.md`,
  `tickets/done/agent-monitoring-unified-weekly-data/TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC.md`
  — the shipped epics that supersede this doc's original M1 (present on `main` as of this
  session's pull; PR #112).
- `tools/agent-monitoring/verify_referential_integrity.py` — the already-shipped
  referential-integrity tool.
- `docs/agent-monitoring/schema.md` — schema documentation, already updated by the shipped epics
  to describe the current `agent-monitoring/data/YYYY-Www/` layout.
