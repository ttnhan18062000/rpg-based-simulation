---
status: idea
layer: observability
authority: P2
audience: developer
maturity: idea
date: 2026-07-28
tags: [idea, agent-monitoring, observability, data-quality, reporting]
---

# Idea: Distinguish Active Work Time from Idle/Session-Pause Gaps in Agent Monitoring Duration

## Problem

`runs.jsonl`'s `duration_s` (and the `RETRO-*.md` "Slow Runs"/"Duration outliers" sections computed
from it) is naive wall-clock: `end_ts - start_ts`, with no awareness of gaps where the orchestrating
session was paused (overnight break, quota exhaustion, human away) rather than actually working.
This makes duration-based signals actively misleading, not just noisy.

**Confirmed on real data**, not speculative — `agent-monitoring/events.jsonl` timestamps for the
28-day retro's top "Slow Runs" outliers:

| run_id | reported total duration | single largest inter-event gap | gap as % of total |
|---|---|---|---|
| `TCK-20260710-SIMQ-DEPTH-SOCIAL` | 828 min | 590.6 min | 71% |
| `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` | 585 min | 576.8 min | 99% |
| `TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS` | 576 min | 539.6 min | 94% |
| `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` | 541 min | 485.8 min | 90% |

All four of the retro's top duration outliers are dominated by one multi-hundred-minute gap between
two consecutive phase events — almost certainly a session pause, not agent work or simulation
runtime. A prior read of this report (same session, corrected in-thread) initially attributed these
to "long simulation runs inside the ticket" — wrong, and exactly the kind of misread this document
exists to prevent from recurring silently in future retros.

**Scope of the contamination**: `cost_proxy_score` (tool-call-based: weighted `bash_ms` +
`agent_count` + `edit_count`) is *not* affected — it's computed from tool-call volume, not
wall-clock time, so the phase/agent cost rankings discussed elsewhere are sound. Only fields
derived from `start_ts`/`end_ts`/inter-event gaps are contaminated: `runs.jsonl`'s `duration_s`,
the retro's "Slow Runs" table, and its "Duration outliers (by tier)" section.

## Idea

Add gap-awareness by computing, from each run's ordered `events.jsonl` timestamps, an
**active-duration view** alongside the existing raw `duration_s` — e.g. `active_duration_s` (sum of
inter-event gaps under some pause threshold) and/or `idle_gap_s` (sum of gaps at or above it), plus
enough detail to show *where* the gap fell (which phase boundary) so a human reviewing a slow run
isn't left guessing.

### Where to compute it: retro/dashboard read-time, not Finalize write-time

Two candidate points were considered:

1. **Correct after ticket completion (Finalize-time, stored in `runs.jsonl`)** — the workflow
   already has the full event sequence in-session when it writes the run record; could compute and
   store `active_duration_s` then, once.
2. **Correct at report-generation time (`generate_retro.py` / dashboard ingest, derived from
   `events.jsonl`)** — read-only, recomputed on demand from data already on disk.

**Recommendation: option 2.** Reasons:

- The raw ingredient (`events.jsonl` timestamps) already exists for every run, past and future —
  a read-time fix applies retroactively to all 28+ days of existing history with zero backfill.
  A Finalize-time field only helps runs going forward.
- The pause threshold (15 min? 30 min? phase-dependent?) is a judgment call likely to need tuning
  once someone actually looks at real gap distributions. A constant in a report generator is cheap
  to iterate on; a value baked into historical stored records under a since-changed definition is
  not.
- The production monitoring **write path** (`post_tool_hook.py` / `record_run.py` /
  `record_events.py` / `writer.py`) was just consolidated and hardened by
  `TCK-20260721-MONITORING-WRITER-UNIFICATION`, specifically because duplicate ad hoc writer logic
  was a fragility source, and `CLAUDE.md`'s hard rule that "monitoring write failure must never
  fail the workflow" underscores how sensitive that path is treated. This is a purely a *reporting*
  interpretation problem — the raw `start_ts`/`end_ts`/event timestamps are correct as recorded —
  so there's no reason to add new computation to a write path that just got stabilized for an
  unrelated concern.

### Hard constraint: single shared utility, not N reimplementations

This project has already paid once for exactly this mistake in an adjacent area — the
tag→skill-suggestion mapping table was hand-duplicated across 4-5 files with no single source of
truth, now being consolidated by `TCK-20260720-SKILL-MAPPING-DEDUP`. Gap-detection logic must not
repeat that pattern: implement it once (e.g. `tools/agent-monitoring/duration_utils.py`, a function
taking a run's ordered event timestamps + a threshold and returning active/idle breakdown), and have
both `generate_retro.py`'s Slow Runs/outliers sections and the dashboard's duration-facing views
(if any expose raw `duration_s` today) import it — not reimplement it.

## Natural Integration Points

| Existing component | How this idea attaches |
|---|---|
| `tools/agent-monitoring/generate_retro.py` — "Slow Runs" / "Duration outliers" sections | Primary consumer; report active/idle breakdown alongside raw duration instead of raw duration alone |
| Agent-ops dashboard (`src/api/agent_ops_dashboard/`) | Secondary consumer if/where it surfaces run duration directly from `runs.jsonl` |
| `docs/agent-monitoring/schema.md` | Should document `duration_s`'s known limitation (naive wall-clock, no gap-awareness) once this ships, mirroring how the doc already discloses "Token counts are not recorded" |
| `agent-monitoring/retro/RETRO-*.md` historical reports | Not retroactively rewritten — but future reports should carry a visible note distinguishing active vs. idle time so a reader doesn't re-derive the SIMQ-DEPTH-SOCIAL-style misread by hand |
| [`idea_agent_monitoring_pause_resume_seq_collision.md`](idea_agent_monitoring_pause_resume_seq_collision.md) | Sibling finding from the same investigation session — that idea covers `tool_call_count`/`cost_proxy_score` corruption from pause/resume `seq` collisions; this one covers wall-clock duration contamination from the same underlying pause/resume behavior. Independent bugs, independent fixes, but both touch resume handling. |

## Open Questions

- What pause threshold actually separates "normal phase-to-phase thinking/tool latency" from "the
  session was away"? Needs a look at the real gap-length distribution across events.jsonl before
  picking a number — don't guess one into the implementation.
- Should the retro report just *flag* runs with a large idle component (a boolean/note), or fully
  restructure "Slow Runs" to rank by `active_duration_s` instead of raw `duration_s`? The latter is
  more correct but changes what "slow" has meant in every past report.
- Does the dashboard need this at all today, or only the retro report — i.e. is there a live UI
  surface currently showing raw per-run duration that would mislead a viewer the same way the retro
  did?

---

*Raised: 2026-07-28, from a session's own workflow-cost-overhead investigation — the retro's
"Slow Runs" table was initially misread as evidence of long simulation runtime inside specific
tickets, until inter-event gap inspection showed the true cause was session pauses.*
