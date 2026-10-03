---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-AGENT-COST-OBSERVABILITY
artifact_type: plan
tags: [agent-monitoring, observability, data-quality]
---

# Implementation Plan — TCK-20260708-AGENT-COST-OBSERVABILITY

## Summary

Ship Tier 1 `cost_proxy_score` as a small, independently-testable module
(`tools/agent-monitoring/cost_proxy.py`) that computes a weighted, unitless proxy score from
`tools.jsonl` rows using the concrete starting weights sized by investigation
(`w_bash=0.001`, `w_agent=50`, `w_edit=1`). Wire it into `writeMonitoring`'s existing Step 2
Python one-liner (widen the current `Counter`-per-`seq` pass — do not add a second read of
`tools.jsonl`), fold the computed score into every new event alongside the existing
`tool_call_count`, document it explicitly as a proxy (not real cost) in `schema.md`, and add a
spend-by-phase/spend-by-agent breakdown table to `generate_retro.py`'s report, inserted as a new
sibling section immediately after `## Agent Status Distribution` so it makes zero contact with the
two already-landed Tag Breakdown sections. Both open questions from the investigation are resolved
in this plan (module extraction: yes; outlier capping: no, ship raw linear formula). Tier 2
(`self_reported_scope`) is sequenced as a final, explicitly optional step — not required for this
ticket's Definition of Done, per the ticket's own "Stretch, only if Tier 1 lands cleanly" framing.

## Steps

### Step 1 — Create the `cost_proxy.py` formula module

**Files:** `tools/agent-monitoring/cost_proxy.py` (new file)

**Change:** Create a small, pure-function module with no side effects and no file I/O:

```python
"""Tier 1 agent-cost proxy formula (TCK-20260708-AGENT-COST-OBSERVABILITY).

Computes a monotonic, unitless "cost_proxy_score" from a group of tools.jsonl rows belonging to
one (run_id, seq) — i.e. one agent event's tool-call footprint. This is a comparable RANKING aid
(e.g. "agent A costs 3x agent B this week"), not a dollar-denominated cost figure. Real token/cost
telemetry is platform-blocked (see docs/agent-monitoring/README.md's "What It Does NOT Capture").

Weights are calibratable, not load-bearing precision — sized from the real aggregate distribution
of agent-monitoring/tools.jsonl (543 sampled event-groups) in this ticket's investigation
(staging_artifacts/TCK-20260708-AGENT-COST-OBSERVABILITY/investigation.md), not guessed:
  - W_BASH:  score units per Bash duration_ms (0.001 == 1 unit per second of Bash wall time).
  - W_AGENT: score units per nested `Agent`-tool spawn (count, NEVER duration-sum — see note below).
  - W_EDIT:  score units per Read/Edit/Write/MultiEdit call.

IMPORTANT — do not "improve" this by summing Agent tool duration_ms instead of counting spawns.
Investigation confirmed the Agent tool's own duration_ms is SDK call-dispatch overhead, not the
spawned subagent's real wall-clock work (a single sampled ticket showed ~97ms avg for Agent calls
regardless of the spawned agent's actual runtime, especially for background/async spawns whose
cost is invisible to the parent's own duration entirely). Summing would silently undercount
fan-out cost. Count spawns, don't sum their durations.
"""

W_BASH = 0.001
W_AGENT = 50
W_EDIT = 1
_EDIT_TOOLS = {"Read", "Edit", "Write", "MultiEdit"}


def compute_cost_proxy_score(tool_rows: list[dict]) -> float:
    """tool_rows: tools.jsonl row dicts already filtered to one (run_id, seq) group.

    Returns W_BASH * sum(duration_ms where tool == "Bash", treating null/missing as 0)
          + W_AGENT * count(tool == "Agent")
          + W_EDIT  * count(tool in {"Read", "Edit", "Write", "MultiEdit"})
    """
    bash_ms = sum(
        (r.get("duration_ms") or 0) for r in tool_rows if r.get("tool") == "Bash"
    )
    agent_count = sum(1 for r in tool_rows if r.get("tool") == "Agent")
    edit_count = sum(1 for r in tool_rows if r.get("tool") in _EDIT_TOOLS)
    return (W_BASH * bash_ms) + (W_AGENT * agent_count) + (W_EDIT * edit_count)
```

This resolves investigation Open Question 1 (module extraction) in favor of extraction: the
formula becomes directly importable both by `writeMonitoring`'s Python one-liner (via
`sys.path.insert(0, 'tools/agent-monitoring')`) and by unit tests, without shelling out to an
embedded one-liner string to verify the math. This also resolves Open Question 2 (outlier
capping) by omission — ship the raw linear formula exactly as specified, with no clamping/cap
logic anywhere in this function. Do not add a cap, a `min()`, a percentile clip, or any smoothing.

**Do NOT touch:** `tools/agent-monitoring/record_events.py`, `record_run.py`, `vocabulary.py`, or
any existing module in `tools/agent-monitoring/`. This is a new, standalone file with zero imports
from and zero edits to any existing agent-monitoring script.

**Verify:** `.venv/bin/python3 -m pytest tests/tools/test_cost_proxy.py -v` — new file, covers
`test_cost_proxy_score_computation_matches_formula` (Bash-only, Agent-only, edit-only, and mixed
groups, asserting exact formula output using `W_BASH=0.001`/`W_AGENT=50`/`W_EDIT=1`) and
`test_cost_proxy_score_excludes_null_duration_bash_rows` (a Bash row with `duration_ms: null`
contributes 0, not a `TypeError`).

---

### Step 2 — Wire `cost_proxy_score` into `writeMonitoring`

**Files:** `.claude/workflows/implement-ticket.js` (lines 202-227, inside `writeMonitoring`'s
agent-prompt template string)

**Change:** Widen Step 2's existing Python one-liner (currently lines 204-217: builds `TOOL_COUNTS`
via a `Counter` grouped by `seq`) so it *also* groups the full row dicts by `seq` and computes
`cost_proxy_score` per group via the Step 1 module, in the same single pass over
`agent-monitoring/tools.jsonl` — do not add a second read of the file. New one-liner shape:

```python
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
sys.path.insert(0, 'tools/agent-monitoring')
from cost_proxy import compute_cost_proxy_score
f = Path('agent-monitoring/tools.jsonl')
counts = Counter()
rows_by_seq = defaultdict(list)
if f.exists():
    for line in f.read_text().splitlines():
        if not line: continue
        r = json.loads(line)
        if r.get('run_id') == '${tid}' and r.get('seq') is not None:
            counts[r['seq']] += 1
            rows_by_seq[r['seq']].append(r)
scores = {seq: compute_cost_proxy_score(rows) for seq, rows in rows_by_seq.items()}
print(json.dumps({"counts": dict(counts), "scores": scores}))
```

Save the result as `TOOL_STATS` (a dict with `"counts"` and `"scores"` keys — both keyed by `seq`,
serialized as string keys per normal `json.dumps` behavior, matching the existing `TOOL_COUNTS`
precedent). Update the prompt's Step 3 instructions: for each event, set `tool_call_count` from
`TOOL_STATS["counts"][str(event.seq)]` (or `0` if absent — unchanged from today), and set
`cost_proxy_score` from `TOOL_STATS["scores"][str(event.seq)]` (or `0.0` if absent — a genuine
zero for an event with no matching tool rows, not a missing-data marker). Every new event gets a
numeric `cost_proxy_score`, satisfying AC1 ("writes `cost_proxy_score` for every new event").

Also update the surrounding prompt comments (the "Step 2 — compute tool_call_count..." heading
text) to reflect that this step now computes both `tool_call_count` and `cost_proxy_score` in one
pass.

**Do NOT touch:** `pushEvent` (lines 156-167) — do not add a `cost_proxy_score` parameter there;
the field is computed entirely inside `writeMonitoring`'s Step 2/3, exactly mirroring how
`tool_call_count` already works today (it is `null` in the in-memory event and only populated at
write time). Do NOT touch Step 1 (END_TS), Step 4 (`record_run.py` call), or Step 5 (sidecar
clear) of the prompt template. Do NOT touch `record_events.py` — it already passes unknown keys
through untouched (confirmed in investigation), so zero changes are needed there; adding
`cost_proxy_score` to `REQUIRED` (line 11) is explicitly forbidden (see Scope Guards).

**Verify:** No JS test harness exists for `implement-ticket.js` (established precedent from
`TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING`) — verify via structural/manual review of the
diff plus the Step 3 integration test below, which exercises the same downstream contract
(`record_events.py` accepting a `cost_proxy_score` key) without needing to run the full JS
workflow. Also run `node --check .claude/workflows/implement-ticket.js` (or equivalent syntax
check) to confirm the edited template literal is not malformed.

---

### Step 3 — Prove the field persists through `record_events.py` untouched

**Files:** `tests/tools/test_record_events.py` (extend — add one new test function; do not modify
existing tests)

**Change:** Add `test_cost_proxy_score_field_written_to_events_jsonl`: build an event dict
containing all of `REQUIRED`'s fields plus `cost_proxy_score: <float>`, call
`record_events.py --data '<json>'` (or call `validate_record`/the write path directly, matching
however the existing file's tests invoke `record_events.py` — follow the existing test file's own
pattern rather than inventing a new invocation style), and assert: (a) `validate_record` returns no
errors, (b) the persisted JSONL row contains `cost_proxy_score` with the expected value. This
proves the additive-field claim end-to-end without touching `record_events.py`'s source.

**Do NOT touch:** `tools/agent-monitoring/record_events.py` itself (no code change — this step is
pure test-writing, confirming existing pass-through behavior). Do NOT modify any of the 11 existing
test functions in this file, and do NOT touch `REQUIRED` (line 11) — this step's test must fail
loudly if a future edit adds `cost_proxy_score` to `REQUIRED`.

**Verify:** `.venv/bin/python3 -m pytest tests/tools/test_record_events.py -v` — all existing tests
plus the one new test pass.

---

### Step 4 — Document the field in `schema.md` and `README.md`

**Files:** `docs/agent-monitoring/schema.md`, `docs/agent-monitoring/README.md`

**Change:**

In `schema.md`:
1. Add a `cost_proxy_score` row to the `events.jsonl` Fields table (currently lines 89-99), after
   the existing `reason_code` row (line 99): `| \`cost_proxy_score\` | float | Yes | ... |`.
2. Insert a new subsection immediately after the `reason_code` values section (after line 137,
   before the "Canonical phase/agent values..." paragraph at line 139), titled something like
   `### \`cost_proxy_score\` — proxy formula and interpretation`. It must state explicitly and
   unambiguously:
   - This is a **monotonic, unitless proxy for relative comparison** (e.g. "agent A costs 3x agent
     B this week"), **not a dollar-denominated cost figure** — no reader should subtract or
     interpret deltas as real currency.
   - The exact formula and current weights: `cost_proxy_score = w_bash * Σ(Bash duration_ms) +
     w_agent * count(Agent spawns) + w_edit * count(Read/Edit/Write/MultiEdit calls)`, with
     `w_bash=0.001, w_agent=50, w_edit=1` as the current starting values, explicitly labeled
     calibratable (not precision-load-bearing), with a pointer to
     `tools/agent-monitoring/cost_proxy.py` as the single source of truth for the live weight
     values (mirroring how this doc already defers to `vocabulary.py` for phase/agent vocabulary).
   - Why `count(Agent)` and never `Σ duration_ms where tool=Agent` — the Agent tool's own
     `duration_ms` is SDK dispatch overhead, not the spawned subagent's real cost (same explanation
     as the module's own docstring, restated here for a doc reader who won't read the .py file).
   - Known limitation: the raw linear formula is unclamped and outlier-sensitive (a single
     very-long Bash call can dominate a spend breakdown) — documented as an accepted characteristic
     of Tier 1, not a bug; a future ticket may revisit capping if real retro data shows distortion.
   - Known limitation: `null`/absent for every event recorded before this ticket landed (no
     backfill, per this ticket's Out of Scope) — a retro breakdown over a period spanning the
     cutover will show partial coverage, by design.

In `README.md`:
- Add one bullet to "What It Captures" (after the existing `tool_call_count` bullet, line 20):
  something like "A monotonic cost-proxy score per agent event, derived from `tools.jsonl` (Bash
  duration + Agent spawn count + edit-tool call count), stored as `cost_proxy_score` — an explicit
  proxy, not real token/dollar cost (see schema.md)."

**Do NOT touch:** the "What It Does NOT Capture" section (lines 23-27) — the ticket's own Scope
explicitly requires token counts remain listed there as still-not-captured; do not remove or soften
that bullet, and do not imply `cost_proxy_score` is a substitute for real token telemetry anywhere
in either doc. Do NOT touch any other section of either file (Navigation, Quick Start, Known
Limitations' legacy-schema content, etc.).

**Verify:** No automated test for doc content; verify by direct read-through confirming both
required statements (proxy framing + Agent-count-not-duration rationale) are present, and that no
existing doc content was altered or removed.

---

### Step 5 — Add spend-by-phase / spend-by-agent breakdown to `generate_retro.py`

**Files:** `tools/agent-monitoring/generate_retro.py` (inside `generate()`, lines 168-404)

**Change:** Insert a new block immediately after the existing `## Agent Status Distribution`
section's closing `lines.append("")` (line 370) and before the `## Summary Quality` section's
opening comment (line 372) — a sibling of Agent Status Distribution, not interleaved with either
already-landed Tag Breakdown block or the Tier Distribution block. Compute using a
filter-then-aggregate pattern (mirrors the existing `avg_dur` pattern at lines 181-183: `durations
= [r["duration_s"] for r in runs if r.get("duration_s")]`) — events lacking `cost_proxy_score`
(`None`/absent, i.e. every pre-this-ticket historical event) must be **excluded from the
denominator**, never coerced to `0`:

```python
# Spend proxy — by phase and by agent. Filter-then-aggregate: events lacking cost_proxy_score
# (pre-TCK-20260708-AGENT-COST-OBSERVABILITY historical records, no backfill) are excluded from
# both sum and count, never coerced to 0 (would silently deflate older phases' averages).
scored_events = [e for e in events if e.get("cost_proxy_score") is not None]
phase_scores = defaultdict(list)
agent_scores = defaultdict(list)
for e in scored_events:
    phase_scores[e.get("phase", "?")].append(e["cost_proxy_score"])
    agent_scores[e.get("agent", "?")].append(e["cost_proxy_score"])
```

Render two tables (or one section with two subtables) titled `## Spend Proxy — By Phase` and
`## Spend Proxy — By Agent` (or a single `## Spend Proxy (cost_proxy_score)` section containing
both tables back to back) — either heading structure is acceptable as long as both axes named in
the ticket's Scope ("spend-by-phase / spend-by-agent breakdown table") are present. Each table:
`| {Phase|Agent} | Events scored | Total | Avg |` with `Total = sum(scores)`, `Avg = round(sum /
len, 1)`. If `scored_events` is empty, omit the section entirely (mirrors the existing conditional-
render pattern used by Reason Codes / both Tag Breakdown sections) rather than rendering an
empty/zero table.

**Do NOT touch:** `_collect_inprogress_tagged_tickets`, `_collect_tagged_tickets`, `_is_gate_fail`,
the `tickets_root` parameter, or any code inside the two already-landed Tag Breakdown blocks (lines
298-340) — no reordering, no touching their `if subsystem_tag_runs:` / `if skill_tag_runs:`
conditionals. Do NOT touch the Tier Distribution block (343-353) or Agent Status Distribution block
itself (356-370) beyond appending the new block immediately after its closing `lines.append("")`.
Do NOT change any existing test's assertions in `test_generate_retro.py` — if implementing this
step requires editing an existing test, that is a signal the insertion landed in the wrong place;
stop and re-check against this step's placement instructions first.

**Verify:**
`.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py -v` covering the four new tests:
`test_retro_spend_by_phase_breakdown_renders_with_fixture_events`,
`test_retro_spend_by_agent_breakdown_renders_with_fixture_events`,
`test_retro_spend_breakdown_omitted_or_zero_safe_when_no_events_have_cost_proxy_score`,
`test_retro_spend_breakdown_placement_does_not_disturb_tag_breakdown_sections` — plus confirmation
that all 11 pre-existing tests in this file still pass unmodified.

---

### Step 6 (optional stretch — only if Steps 1-5 are green) — Tier 2 `self_reported_scope`

**Files:** `.claude/workflows/implement-ticket.js` (`pushEvent`, lines 156-167), possibly
`tools/agent-monitoring/record_events.py` (no change expected — additive field, same
pass-through as `cost_proxy_score`), `docs/agent-monitoring/schema.md`

**Change (only attempt after Steps 1-5 pass all their Verify commands):** Add an optional
`self_reported_scope` field to the in-memory event object, populated only if the calling agent's
structured return includes it (same trust ceiling as the existing free-text `summary` field — not
independently verified, self-reported). Follow the `verified_by` precedent from
`TCK-20260705-GATE-DET-DONE-CHECKER`'s `DONE_SCHEMA` addition exactly: optional, additive, `null`
default, does not break any existing caller that omits it. Document in `schema.md` with the same
"self-reported, same trust ceiling as `summary`" framing.

**Do NOT touch:** anything from Steps 1-5 while implementing this step — if this step reveals a
need to change the Step 1-5 design, that is a signal to stop and not attempt Tier 2 in this pass
(per the ticket's own "only if Tier 1 lands cleanly" framing — a rocky Tier 2 attempt must not
block or destabilize the required Tier 1 scope).

**Verify:** `test_self_reported_scope_optional_field_does_not_break_existing_callers` in
`tests/tools/test_record_events.py`, plus a full re-run of Steps 1-5's Verify commands to confirm
nothing regressed.

**This step is explicitly NOT required for this ticket's Definition of Done.** If skipped, say so
plainly in the ticket's Completion Summary — do not silently omit it without a note.

## Scope Guards

- Do NOT add `cost_proxy_score` to `record_events.py`'s `REQUIRED` set (line 11). It is optional
  and additive, exactly like `tool_call_count` and `reason_code` before it.
- Do NOT touch `record_run.py` at all — this ticket is entirely event-level (`events.jsonl`), not
  run-level (`runs.jsonl`).
- Do NOT touch `vocabulary.py`, `warn_vocabulary_drift`, or any phase/agent canonical-vocabulary
  logic — a new numeric field cannot interact with vocabulary checks.
- Do NOT touch either of the two already-landed Tag Breakdown sections in `generate_retro.py`
  (lines 298-340) — their code, their conditional-render triggers, or their section order relative
  to each other. The new spend section is a new, independent sibling block inserted only after
  `## Agent Status Distribution`.
- Do NOT touch `_collect_inprogress_tagged_tickets`, `_collect_tagged_tickets`, `_is_gate_fail`, or
  `generate()`'s `tickets_root` parameter — none are relevant to spend computation.
- Do NOT modify any of the 11 pre-existing tests in `test_generate_retro.py` or any pre-existing
  test in `test_record_events.py` — only add new test functions.
- Do NOT attempt Tier 3 (real token/cost telemetry) in any form — confirmed platform-blocked; no
  workaround exists and none should be attempted.
- Do NOT make any model-routing policy decision or change — this ticket only produces an evidence
  base.
- Do NOT backfill `cost_proxy_score` onto any existing `events.jsonl` row — append-only precedent,
  new writes only.
- Do NOT touch the "What It Does NOT Capture" section of `docs/agent-monitoring/README.md` — token
  counts must remain listed there.
- Do NOT touch any `docs/parity_ledger/*.yaml` file — confirmed zero parity-ledger surface for this
  ticket; no entry should be added or edited.
- Do NOT touch any `src/` file — this ticket is pure agent-tooling/observability infrastructure.
- Do NOT sum `Agent` tool `duration_ms` anywhere in the formula — count spawns only, per
  investigation's confirmed finding that `Agent` duration is dispatch overhead, not real cost.
- Do NOT add any capping/clamping/percentile-clip logic to the score formula in this pass — ship
  the raw linear formula as specified; defer any capping decision to a later ticket if real retro
  data shows distortion.
- Do NOT run the full `pytest tests/` suite — scope stays inside `tests/tools/` per the test plan's
  own instruction; always use `.venv/bin/python3 -m pytest ...` (system Python lacks `pydantic`).

## Dependency Map

- Step 1 (module) has no dependencies — pure new file, can be implemented and verified first.
- Step 2 (wire into `writeMonitoring`) depends on Step 1 (imports `compute_cost_proxy_score`).
- Step 3 (record_events.py integration test) has no code dependency on Steps 1-2 (it constructs the
  event dict directly) but is logically the proof that Step 2's output contract is safe — implement
  after Step 2 for narrative order, though it could technically run standalone.
- Step 4 (docs) depends on Step 1 (needs the final formula/weights to document accurately) but not
  on Steps 2-3 or 5.
- Step 5 (retro breakdown) is independent of Steps 1-3 — it only reads `cost_proxy_score` off
  `events` dicts in test fixtures, and does not import `cost_proxy.py` or call `writeMonitoring`.
  It can be implemented in parallel with Steps 1-4 if desired, but is listed after them for a
  clean, incremental PR narrative.
- Step 6 (Tier 2, optional) depends on Steps 1-5 all being green — explicitly gated, not parallel.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `writeMonitoring` computes and writes `cost_proxy_score` for every new event | Steps 1, 2 | `tests/tools/test_cost_proxy.py` (formula correctness) + Step 2's structural review + Step 3's `test_cost_proxy_score_field_written_to_events_jsonl` (persistence) |
| `docs/agent-monitoring/schema.md` documents the field's formula and explicitly labels it a proxy | Step 4 | Manual read-through verification (no automated doc test exists in this repo's pattern) |
| `make agent-monitoring-retro`'s report includes a spend-by-phase and spend-by-agent breakdown table | Step 5 | `test_retro_spend_by_phase_breakdown_renders_with_fixture_events`, `test_retro_spend_by_agent_breakdown_renders_with_fixture_events` |
| If Tier 2 is attempted: `self_reported_scope` is optional, does not break existing callers that omit it | Step 6 (optional) | `test_self_reported_scope_optional_field_does_not_break_existing_callers` (only if Step 6 attempted) |
| Tests cover proxy score computation against a fixture `tools.jsonl` and retro report breakdown generation against fixture events | Steps 1, 5 | `tests/tools/test_cost_proxy.py` (both new tests) + `test_generate_retro.py`'s four new tests |

## Anti-Drift Notes

- **Module extraction decision (resolved):** `tools/agent-monitoring/cost_proxy.py` is a new,
  standalone, dependency-free module. It is imported by `writeMonitoring`'s Python one-liner via
  `sys.path.insert(0, 'tools/agent-monitoring')` and directly by `tests/tools/test_cost_proxy.py`.
  `generate_retro.py` does **not** need to import it — the retro breakdown only aggregates
  `cost_proxy_score` values already present on `events` dicts; it does not recompute anything from
  raw `tools.jsonl` rows. Do not add an unnecessary import from `generate_retro.py` to
  `cost_proxy.py`; there is no computation there that needs the formula.
- **Outlier-capping decision (resolved):** ship the raw, unclamped linear formula exactly as
  specified in investigation. A 30-hour Bash call showing up as a genuinely large score is correct,
  visible signal — not a bug to suppress. Document the sensitivity in `schema.md` (Step 4) as a
  known characteristic; do not implement any capping logic in this ticket.
- **`Agent` tool duration is not a real-cost signal** — the formula must count `Agent` tool call
  occurrences, never sum their `duration_ms`. This is deliberate and must not be "fixed" by a future
  session that hasn't seen the investigation's data (SDK dispatch overhead, ~97ms regardless of the
  spawned agent's real runtime, and invisible entirely for background/async spawns).
- **Missing-field handling in the retro breakdown must never coerce to 0.** Every pre-this-ticket
  historical event lacks `cost_proxy_score` entirely; a coerce-to-zero default would silently
  understate historical phases relative to newer ones. Filter-then-aggregate, matching the existing
  `avg_dur` pattern already in `generate_retro.py`.
- **Section insertion point in `generate_retro.py` is exact:** after line 370's `lines.append("")`
  (closing `## Agent Status Distribution`), before line 372's `## Summary Quality` comment. This
  placement makes zero contact with either Tag Breakdown block already landed by the concurrent
  `TCK-20260708-RETRO-TAG-BREAKDOWN` ticket (already merged at commit `7b0d64fd`).
- **Test environment:** every test command must use `.venv/bin/python3 -m pytest ...` — the system
  `/usr/bin/python3` lacks `pydantic` and cannot even collect `tests/conftest.py`.
- **Scope discipline:** Tier 3 (real token/cost) is platform-blocked and explicitly out of scope —
  do not attempt any workaround. Model-routing policy is a separate, later decision — this ticket
  only produces evidence. No backfill of historical `events.jsonl` rows under any circumstance.

## Deviations

- **Step 3 test placement**: `test_cost_proxy_score_field_written_to_events_jsonl` was added as a
  standalone module-level function at the end of `tests/tools/test_record_events.py`, not nested
  inside `TestVocabularyWarning` (the last class in the file before this edit). The plan only
  specified "extend — add one new test function" without a placement class; nesting it inside
  `TestVocabularyWarning` would have been semantically wrong (that class is scoped to
  phase/agent-vocabulary warning behavior, not field pass-through), so it was placed as its own
  top-level test with a new section comment header, matching the file's existing mix of top-level
  functions and purpose-scoped classes.
- **Step 6 (Tier 2 `self_reported_scope`) was deferred**, exactly as the plan allows ("optional
  stretch — only if Steps 1-5 are green"). Steps 1-5 passed all Verify commands, but Tier 2 was
  judged to need its own separately-reviewable diff (wiring an optional field through every
  `pushEvent` call site across all workflow phases) rather than being folded into this already-
  complete Tier 1 change. See the ticket's Implementation Notes for the full rationale.
