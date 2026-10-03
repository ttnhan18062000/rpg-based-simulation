---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-AGENT-COST-OBSERVABILITY
artifact_type: investigation
tags: [agent-monitoring, observability, data-quality]
---

# Investigation — TCK-20260708-AGENT-COST-OBSERVABILITY

## Current Behavior

### `writeMonitoring` — `.claude/workflows/implement-ticket.js:189-239`

- `pushEvent(phaseLabel, agentName, status, summary, ts, toolCallCount, reasonCode)` (line 156-167)
  builds each in-memory event with exactly these keys: `seq`, `phase`, `agent`, `status`, `summary`
  (sliced to 200 chars), `ts`, `tool_call_count` (`null` until backfilled), `reason_code`. No cost
  field exists anywhere in this object today.
- `writeMonitoring` (line 189) is invoked once at Finalize with the accumulated `events` array. It
  delegates the actual write to a fresh sub-agent (`{label: 'monitoring-write'}`), which:
  1. Gets `END_TS` via `date -u`.
  2. Computes `tool_call_count` per `seq` via an inline Python one-liner (line 204-217) that reads
     `agent-monitoring/tools.jsonl`, filters rows where `run_id == tid` and `seq is not None`, and
     `Counter`s them by `seq`. **This is the only place `tools.jsonl` is read today** — it counts
     rows, it does not touch `duration_ms` or `tool` at all.
  3. Merges `run_id` and the computed `tool_call_count` into each event, then shells out to
     `python3 tools/agent-monitoring/record_events.py --data '<json>'`.
  4. Writes the run record via `record_run.py`.
  5. Clears `.claude/current_run`.
- **Gap confirmed**: no code path anywhere in `implement-ticket.js` reads `tool` or `duration_ms`
  from `tools.jsonl`. Computing `cost_proxy_score` requires extending Step 2's Python one-liner (or
  adding a new one) to also group by `tool` and sum `duration_ms`/count occurrences per `seq`, then
  folding that into each event dict in Step 3 before calling `record_events.py`.

### `record_events.py` — `tools/agent-monitoring/record_events.py:11-28`

- `REQUIRED = {"run_id", "seq", "ts", "phase", "agent", "summary", "status"}` — `cost_proxy_score`
  is **not** in this set today and must not be added to it (Tier 1 is a proxy, not guaranteed
  computable for every historical record; making it required would break nothing at write time
  since it's always computed by `writeMonitoring`, but the schema doc explicitly frames tiers as
  additive, and `tool_call_count`/`reason_code` — the two most recent precedent fields — are both
  optional/nullable, not required). `validate_record` only checks presence/non-null of `REQUIRED`
  and a `VALID_STATUS` enum on `status`; an extra key not in `REQUIRED` passes through untouched
  and is written verbatim by the `json.dumps(record, ...)` loop at the bottom (line 94-95). No
  schema whitelist rejects unknown keys — **an additive field is safe to add with zero code changes
  to `record_events.py` itself**, only to the caller (`writeMonitoring`) that builds the dict.
- `warn_vocabulary_drift` (line 31-43) only inspects `phase`/`agent` against `vocabulary.py` — adding
  a new field cannot trigger or interact with this check.

### `generate_retro.py` — `tools/agent-monitoring/generate_retro.py` (current actual state, post
`TCK-20260708-RETRO-TAG-BREAKDOWN`, commit `7b0d64fd`)

Confirmed section order inside `generate()` (line 168-404), in emission order:

1. `## Run Summary` (unconditional, line 256)
2. `## Gate Failure Breakdown` (unconditional, line 269)
3. `## Reason Codes` (conditional on `reason_counter`, line 282-289)
4. `## Tag Breakdown — Subsystem/Topic` (conditional on `subsystem_tag_runs`, line 298-309)
5. `## Tag Breakdown — Process/Skill-signal` (conditional on `skill_tag_runs`, line 316-340)
6. `## Tier Distribution` (unconditional, line 343-353)
7. `## Agent Status Distribution` (unconditional, line 356-370)
8. `## Summary Quality` (unconditional, line 372-383)
9. `## Slow Runs (> 30 min)` (unconditional, line 386-396)
10. `## Notes` (unconditional, line 399-402)

Helper functions confirmed present exactly as landed: `_collect_inprogress_tagged_tickets(root)`
(line 98-137), `_collect_tagged_tickets(root)` (line 140-151), `_is_gate_fail(r)` (line 90-95,
factored out of the old inline `gate_fails` tuple check and now reused by both the Run Summary
gate-fail count and the Subsystem/Topic table's per-tag gate-failure column), and `generate(runs,
events, label, week_str=None, tickets_root=None)` (line 168) — the `tickets_root=None` param exists
and defaults via `tickets_root if tickets_root is not None else _DEFAULT_TICKETS_ROOT` (line 169).
This matches the ticket's own note exactly; no drift from what the prompt described.

### `tests/tools/test_generate_retro.py` — current test surface

11 `def test_*` functions (confirmed via `grep -c` and a live `pytest` run with the project venv:
`.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py -q` → **11 passed**). Combined with
`test_tag_report.py` in one invocation: **24 passed** (matches
`TCK-20260708-RETRO-TAG-BREAKDOWN`'s own Test Summary). Note: the system Python (`/usr/bin/python3`)
lacks `pydantic` and cannot even collect `tests/conftest.py` — **all test commands in this
investigation and the test plan must use `.venv/bin/python3 -m pytest`**, not bare `pytest` or
`python3 -m pytest`.

### `agent-monitoring/tools.jsonl` — actual real-data shape (not assumed)

Sample record (interactive session, no active workflow run):
```json
{"session_id":"...","run_id":null,"seq":null,"ts":"...","tool":"Bash","input_summary":"...","status":"ok","duration_ms":82}
```
Sample record (inside a real `implement-ticket` run, `run_id`+`seq` populated):
```json
{"run_id":"TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING","seq":9,"phase":"Parity", ...}
```
(that one is from `events.jsonl` — the join key confirmed live: `tools.jsonl` rows carry `run_id` +
`seq` set by the PostToolUse hook reading `.claude/current_run`; join to `events.jsonl` is `run_id`
+ `seq` exactly as `docs/agent-monitoring/schema.md` documents.)

Aggregate stats computed directly against the live 41,295-line `agent-monitoring/tools.jsonl`
(21,911 rows have `run_id` set — i.e. attributed to a workflow run):

| Tool | n (attributed) | sum(duration_ms) | avg(duration_ms) |
|---|---|---|---|
| Bash | 11,171 | 398,274,760 | 35,652.6 |
| Write | 1,132 | 8,682,179 | 7,669.8 |
| Agent | 418 | 6,842,680 | 16,370.0 |
| Edit | 2,968 | 1,122,981 | 378.4 |
| Read | 5,480 | 608,751 | 111.1 |

Grouped **per (run_id, seq)** — i.e. per single agent-event's tool footprint, the actual unit
`cost_proxy_score` will be computed over (543 real event-groups sampled):

| Component | median | p90 | p99 | max |
|---|---|---|---|---|
| `Σ duration_ms` where `tool=Bash` | 1,921 | 379,803 | 20,609,043 | 109,137,872 |
| `count(tool=Agent)` | 0 | ~2-3 | — | 30 |
| `count(tool in {Read,Edit,Write,MultiEdit})` | 4 | 24 | 321 | 1,385 |

**Key finding on `Agent` tool `duration_ms`**: it does **not** represent the nested subagent's real
wall-clock work. A single ticket's own tool-call sample showed `Agent` averaging 97ms — clearly just
the SDK call-dispatch overhead, not the spawned agent's actual runtime (which is tracked
independently under its own `seq`, if it makes any tool calls itself; a background-run agent's cost
is invisible to the parent's own tool-call duration entirely). This directly confirms *why* the idea
doc's formula treats `count(tool=Agent)` as a multiplier rather than summing `Agent` `duration_ms` —
duration-summing agent spawns would silently undercount the actual cost of the fan-out.

## Mechanics / Engine Constraints

None apply. This ticket touches only `.claude/workflows/implement-ticket.js` and
`tools/agent-monitoring/*` — agent-tooling/observability infrastructure, not simulation state,
combat, economy, or world logic. No chapter of `docs/mechanics/` or contract in `docs/engine/`
governs agent-monitoring schema or reporting. Confirmed by reading the ticket's own `layer: ai` and
cross-checking that neither `docs/mechanics/` nor `docs/engine/` is listed in Related Docs.

## Parity Ledger Overlap

**None.** Confirmed by direct inspection of all 8 `docs/parity_ledger/*.yaml` files
(`substrate.yaml`, `combat_movement.yaml`, `strategic_cognition.yaml`, `town_resource.yaml`,
`progression.yaml`, `social_narrative.yaml`, `world_dynamics.yaml`, `infrastructure.yaml`,
`faction.yaml`) for any mention of `cost_proxy`, `agent-monitoring`, `writeMonitoring`, or related
terms — zero hits. This is pure agent-tooling/observability work with no simulation-mechanics
surface, matching the pattern of its two sibling tickets
(`TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT`, `TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING`),
both of which independently confirmed and recorded "no parity ledger entries touched." No new
parity ledger entry should be added for this ticket, and the Parity phase of `implement-ticket.js`
should skip its full parity-updater call (no `src/` path change, `behavior_changed: false`).

## Prior Work

- **`TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT`** (done, `stored_artifacts/` +
  `tickets/done/`): landed the exact "clean phase/agent vocabulary" precondition this ticket's
  scope note calls out as a dependency — `vocabulary.py`'s canonical `WORKFLOW_PHASES`/
  `WORKFLOW_AGENTS` sets are now the single source of truth, warned-not-rejected at write time. This
  matters for a future spend-by-phase/spend-by-agent breakdown: phase/agent labels used as grouping
  keys are now enforced-canonical going forward (though historical drifted records — 98
  `workflow: null`, etc. — are explicitly not backfilled, so a spend-by-phase breakdown over
  historical data will still show some drift for pre-2026-07-08 records; this is an accepted,
  already-documented limitation, not a new gap this ticket introduces).
- **`TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING`** (done): confirms the precedent of adding new
  status/behavior to `implement-ticket.js` while explicitly re-verifying "no parity ledger entry
  touched" as part of Test/Parity — same pattern this ticket should follow. Also demonstrates the
  established pattern for JS-side changes with no JS test harness: verify via structural/manual
  review plus the Python-side regression suite, not by inventing a JS test framework.
- **`TCK-20260708-RETRO-TAG-BREAKDOWN`** (done, commit `7b0d64fd`, landed *after* this ticket's own
  Related Tickets note was written): added the two Tag Breakdown sections described above. This
  ticket's new spend-by-phase/spend-by-agent section must be inserted **after** `## Tag Breakdown —
  Process/Skill-signal` (line 340) and **before** `## Tier Distribution` (line 343) to sit alongside
  the other per-run/per-event breakdown sections in one coherent block, or equally validly
  immediately after `## Agent Status Distribution` (line 370) since it's conceptually a sibling of
  that table (both key off `events`, not `runs`+tags). Recommend: **immediately after `## Agent
  Status Distribution`** (line 370, before `## Summary Quality`) — it is the closest existing section
  in shape (per-agent breakdown table keyed by `events`), and this placement makes zero contact with
  either of the two newly-landed Tag Breakdown blocks' code or conditional-render logic, eliminating
  any risk of a collision with `TCK-20260708-RETRO-TAG-BREAKDOWN`'s diff (already landed, so this is
  now actually about clean insertion into the current file, not diff-rebasing).
- **`TCK-20260705-GATE-DET-DONE-CHECKER`** (done): established the `verified_by` field precedent —
  a genuinely new, additive, optional field bolted onto an existing schema (`DONE_SCHEMA` in
  `implement-ticket.js`) without breaking existing callers, self-reported by the producing agent
  rather than computed by a static script. Directly analogous precedent for how a Tier 2
  `self_reported_scope` field (if attempted) should be designed: optional, additive, same trust
  ceiling as the existing free-text `summary` field — exactly what this ticket's Scope section
  already specifies.

## Risks and Open Questions

1. **Is a unitless proxy score actionable?** (Idea doc's own Open Question — investigated, not
   assumed.) The concrete retro use case named in the idea doc is: *"`architecture-reviewer` costs
   3x `ticket-scoper` — is that proportional to the value it catches, or is its prompt bloated?"*
   This is a **within-report relative comparison** (agent A vs. agent B, same report, same time
   window), not an absolute dollar judgment — relative/ranked comparisons are exactly what a
   monotonic, comparable-but-unitless score supports well, and exactly what `tool_call_count`
   already does today for a coarser "complexity" signal (this ticket is a direct refinement of that
   existing pattern, not a new kind of claim). **Recommendation: proceed with Tier 1 as an explicit,
   labeled proxy — do not block on a per-model `$/call` constant.** The schema doc must state
   plainly (per Scope) that this is a monotonic ranking aid, not a real-cost figure, so no reader
   mistakes a `cost_proxy_score` delta for a dollar delta. This resolves the ticket's Assumption /
   Open Question #1 in favor of proceeding.
2. **Starting weight values** (Assumption/Open Question #2) — sized below from the actual data
   distribution (see Current Behavior's aggregate stats table), not guessed:
   - **`w_bash = 0.001`** (i.e., score units per millisecond of Bash `duration_ms` — equivalently,
     1 unit per second of Bash wall time). At the median event (1,921ms Bash), this contributes
     ~1.9 units; at p90 (379,803ms), ~380 units. Chosen because Bash is generally the most
     execution-time-heavy tool category (tests, builds, greps) and its raw `duration_ms` is a
     genuine wall-clock signal (unlike `Agent`'s, see Risk 3 below).
   - **`w_agent = 50`** (units per nested `Agent` tool spawn). Median event has 0 spawns; p90 has
     ~2-3. A single nested spawn should weigh noticeably more than a single Read/Edit call (spawns
     imply an entire additional agent's worth of hidden work, invisible to the parent's own
     `duration_ms`), but should not so dominate the score that a phase with zero Bash and 1 spawn
     always outranks a phase with heavy Bash and zero spawns — 50 keeps a single spawn roughly
     comparable to ~50 seconds of Bash, i.e. a real but not overwhelming weight.
   - **`w_edit = 1`** (units per Read/Edit/Write/MultiEdit call). Median event has 4 (contributing
     4 units), p90 has 24. Kept at the lowest weight since these are typically the cheapest,
     highest-frequency tool calls and the idea doc's own formula groups them together as the "low
     cost per call, but tracks breadth of file touch" component.
   - All three values are explicitly calibratable, not load-bearing precision (per the ticket's own
     Assumption #2 framing) — they should be named module-level constants in `implement-ticket.js`
     (or wherever the computation lives) with a comment pointing at this investigation's basis, so a
     future retro can tune them with evidence rather than guesswork.
3. **Outlier sensitivity** — the per-event Bash-duration-sum distribution has extreme high-end
   outliers (max observed: 109,137,872ms ≈ 30 hours on a single event-group; max Read/Edit/Write
   count: 1,385 in one event-group). A linear, unclamped `w_bash · Σduration_ms` term means a single
   pathological event (e.g., a hung background process, a very long-running test suite invocation)
   could dominate a spend-by-phase/spend-by-agent breakdown, making the report describe one outlier
   run rather than typical behavior. **This is a real risk to flag for Plan**, but per the ticket's
   own framing (comparable/monotonic ranking, not precision) it does not have to be solved before
   landing Tier 1 — Plan should explicitly decide whether to (a) ship the raw linear formula as
   specified and let outliers be visible signal (arguably correct — a 30-hour Bash call *should*
   show up as expensive), or (b) note it as a known limitation for a later follow-up (e.g. capping
   or median-based aggregation for the retro table specifically, not the per-event score). Recommend
   (a): ship as specified, document the outlier-sensitivity as a known characteristic in
   `schema.md`, defer any capping decision until real retro data shows it's actually distorting
   conclusions.
4. **`Agent` tool `duration_ms` does not measure the spawned agent's real cost** (see Current
   Behavior finding above) — this is why the formula must keep using `count(tool=Agent)`, never
   `Σ duration_ms where tool=Agent`. If a future revision were tempted to "improve accuracy" by
   summing Agent durations instead of counting, it would actually make the proxy *less* accurate for
   background-run (async) agent spawns. Document this explicitly so it isn't "fixed" by a future
   session that hasn't seen this data.
5. **Where exactly the computation should live** — `writeMonitoring`'s Step 2 Python one-liner
   (line 204-217) already reads `tools.jsonl` filtered to the run and grouped by `seq`; the natural,
   minimal-diff extension is to widen that same one-liner's `Counter` logic into a small dict
   keyed by `seq` with `{bash_ms, agent_count, edit_count}` (or the final `cost_proxy_score` computed
   directly there), then fold it into the event dict in Step 3 alongside the existing
   `tool_call_count` merge — not a second, separate pass over `tools.jsonl`. This is an implementation
   detail for Plan, not a blocking question, but worth stating so Plan doesn't invent a redundant
   second read of the file.
6. **Historical events lack `cost_proxy_score`** (ticket's own Out of Scope — no backfill). A
   spend-by-phase/spend-by-agent retro table computed with `--all` or `--days N` will mix records
   that have the field with ones that don't (`null`/absent). `generate_retro.py`'s new breakdown
   section must treat a missing/`None` `cost_proxy_score` as excluded from the average/sum (not
   coerced to 0, which would silently understate older phases relative to newer ones) — mirror the
   existing `durations = [r["duration_s"] for r in runs if r.get("duration_s")]` filter-then-average
   pattern already used for `avg_dur` (line 181-183), not a `.get(..., 0)` default-sum pattern.

## Anti-Drift Hazards

**(a) Section insertion point in `generate_retro.py`** — the two Tag Breakdown sections
(`## Tag Breakdown — Subsystem/Topic`, lines 298-309; `## Tag Breakdown — Process/Skill-signal`,
lines 316-340) are already landed and must not be touched, reordered, or have their conditional-
render logic (`if subsystem_tag_runs:` / `if skill_tag_runs:`) altered. The new spend-by-phase/
spend-by-agent section should be inserted as its own new block **after line 370** (`## Agent Status
Distribution`'s closing `lines.append("")`) and **before line 372** (`## Summary Quality`'s comment
line) — i.e., a sibling of Agent Status Distribution, not interleaved with either Tag Breakdown
block or the Tier Distribution block. Do not touch `_collect_inprogress_tagged_tickets`,
`_collect_tagged_tickets`, `_is_gate_fail`, or `generate()`'s `tickets_root` parameter — none of
those are relevant to a spend computation, which only needs `events` (already available in
`generate()`'s signature).

**(b) `events.jsonl` schema must gain `cost_proxy_score` additively, not by touching `REQUIRED`**.
`record_events.py`'s `REQUIRED` set (line 11: `{"run_id", "seq", "ts", "phase", "agent", "summary",
"status"}`) must NOT be edited to include `cost_proxy_score` — doing so would reject every event
from any code path that doesn't compute it (there is none today besides `writeMonitoring`, but
making it required is an unjustified tightening beyond this ticket's scope and inconsistent with
how `tool_call_count`/`reason_code` were both added as optional/nullable). The only code that needs
to change is `implement-ticket.js`'s event-building step (inside `writeMonitoring`, Step 2-3) —
`record_events.py` itself needs zero changes since it already passes unknown keys through
untouched (confirmed: no schema whitelist rejects extra keys).

**(c) Unitless-proxy actionability** — resolved above (Risk #1): proceed with Tier 1, framed
explicitly as a proxy in `schema.md`/`README.md`, not gated on a dollar constant. Do not let Plan
reopen this as a blocking design question — the investigation found a concrete, named retro use
case (relative agent/phase comparison) that a monotonic proxy directly serves.

**(d) Starting weights** — use `w_bash = 0.001`, `w_agent = 50`, `w_edit = 1` as documented,
concrete starting values (not placeholders) per Risk #2 above, defined as named constants with a
comment citing this investigation, not re-derived from scratch or left symbolic in the plan.

**(e) `Agent` tool `duration_ms` is not a real-cost signal** — do not let Implement "simplify" the
formula into `Σ duration_ms` across all tool types uniformly; the `Agent` term must stay a `count`,
never a duration-sum, per Risk #4.

**(f) Missing-field handling in the new retro section** — must use a filter-then-aggregate pattern
(exclude records lacking the field), not a coerce-to-zero default, per Risk #6 — otherwise every
historical (pre-this-ticket) event silently reads as a real "0 cost" event and skews phase averages
downward for `Scope`/`Investigate`/etc. captured before this ticket landed.

**(g) Test environment** — the system `/usr/bin/python3` cannot even collect `tests/conftest.py`
(missing `pydantic`); every test command for this ticket (Implement, Test phase) must use
`.venv/bin/python3 -m pytest ...`, confirmed working in this investigation.

**(h) Scope discipline** — this ticket's Out of Scope explicitly excludes Tier 3 (real token/cost,
platform-blocked — do not attempt any workaround), model-routing policy (this ticket only produces
evidence, not a routing decision), and backfilling historical events. Do not let Implement "helpfully"
compute `cost_proxy_score` for existing `events.jsonl` rows in a one-off migration script — that is
explicitly out of scope and would violate the append-only precedent already established for this
file (see `docs/agent-monitoring/schema.md`'s Known Limitations section on the append-only
`runs.jsonl` convention, same principle applies to `events.jsonl`).
