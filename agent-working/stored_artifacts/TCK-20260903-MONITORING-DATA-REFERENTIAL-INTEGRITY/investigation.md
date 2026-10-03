---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY
artifact_type: investigation
tags: [agent-monitoring, observability, data-quality, schema]
---

# Investigation — TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY

## Current Behavior

### The FK contract (confirmed by direct read, `docs/agent-monitoring/schema.md`)

- Line 141: `events.jsonl` — "One record per agent call within a workflow run. FK: `run_id →
  runs.run_id`."
- Line 172: `events.jsonl`'s `run_id` field table entry — "FK to runs.jsonl."
- Line 370: `tools.jsonl` — "Joined to events by `run_id` + `seq`."
- Line 407: `tools.jsonl`'s `run_id` field table entry — "FK → runs.jsonl. `null` when the tool call
  occurred outside an active workflow run."
- Line 408: `tools.jsonl`'s `seq` field table entry — "FK → events.seq. Identifies which agent event
  this tool call belongs to... `null` if the sidecar was not yet written at hook time."
- Lines 470-502: a "Join Example" section that already demonstrates the correct glob-based,
  all-weeks read pattern (see below) — but as pure illustrative documentation, not an executable
  check. No script anywhere in `tools/agent-monitoring/` currently runs this join and reports
  violations. **Confirmed: exactly 2 FK relationships are documented, matching the ticket's own
  framing** — `events.run_id → runs.run_id` and `tools.(run_id, seq) → events.(run_id, seq)`. No
  third relationship exists anywhere in the schema doc (`runs.jsonl` itself has no outbound FK).

### The 3 documented exceptions (confirmed by direct read)

- `RETRIEVAL-EVENT-<slug>` prefix (schema.md lines 353-364): a `run_id` prefix `infer_workflow()`
  deliberately returns `None` for; these events have no matching `runs.jsonl` row by design, and the
  doc states outright "Because these `run_id`s have no matching `runs.jsonl` row, they are naturally
  excluded from every existing run-scoped retro/dashboard view." **Confirmed 0 occurrences in the
  live corpus today** (see Real Corpus Characteristics below) — the exception must still be
  implemented (schema-sanctioned, could appear any time `tools/hybrid_retrieval.py` or
  `tools/retrieval_cache.py` run standalone), just not currently exercised.
- `tools.jsonl` `run_id: null` (schema.md line 407): "tool call occurred outside an active workflow
  run (interactive session use)." **48,357 of 184,396 real `tools.jsonl` rows (26.2%) have `run_id:
  null`** — a large, expected, non-violating population that must be excluded from the
  `tools.(run_id, seq) → events` check entirely (not just skipped as "no match found").
- Negative/zero `seq` shadow rows (schema.md lines 145, 310, 338-340): `context-packet-wrapper` rows
  emit `seq = -(1 + prior_shadow_count)`, deliberately disjoint from the monotonic `seq >= 1` range.
  **Confirmed 0 occurrences of `seq <= 0` anywhere in the live `tools.jsonl` corpus today** — same
  situation as the retrieval-event exception: schema-sanctioned, must be implemented, not currently
  exercised (this shadow mechanism is gated behind `SHADOW_CONTEXT_PACKET_ENABLED=1`, off by default
  per schema.md line 331).

### Existing tooling that already touches this join — `tools/agent-monitoring/validate.py`

Read in full (`/home/u24desktop/Working/rpg-based-simulation/.claude/worktrees/doc-tag-enforcement/tools/agent-monitoring/validate.py`).

- `compute_tool_count_drift_report()` (lines 151-194) is the closest existing precedent for this
  ticket's second FK check — it groups `tools` rows by `(run_id, seq)` and compares the count
  against `events[i]['tool_call_count']`. **This is a count-drift check, not an existence/FK check**:
  it only validates events that already carry a non-null `tool_call_count` (line 177: `if run_id is
  None or seq is None or recorded is None: continue`), and it never asks "does an event exist at all
  for this `(run_id, seq)`?" — a `tools` row whose `(run_id, seq)` has **no** matching event row is
  invisible to this function; it would only ever surface as `actual_counts.get((run_id, seq), 0)`
  feeding into some *other* event's mismatch, never as its own orphan finding. **This ticket's
  `tools.(run_id, seq) → events.(run_id, seq)` check is a genuinely new capability, not a
  duplicate of this function** — it must be additive, reusing `validate.py`'s report-string
  conventions but not replacing/modifying this function.
- `compute_multi_invocation_collision_report()` (lines 197-220) detects the pause/resume seq-restart
  *signature* (>1 `phase="Scope", seq=1` event per run_id) — a different, narrower detector than a
  full FK check, and it only looks at `events`, never joins against `tools`.
- **`validate.py`'s own read path is stale relative to the new weekly-folder layout and this ticket
  must not depend on it.** `main()` (lines 258-262) calls `open_index()`/`load_runs_from_index()`
  etc. against `agent-monitoring-index/monitoring.db`, built by `build_index.py`. `build_index.py`'s
  own default paths (`DEFAULT_RUNS_FILE = Path("agent-monitoring/runs.jsonl")`,
  `DEFAULT_EVENTS_FILE = Path("agent-monitoring/events.jsonl")`, `DEFAULT_TOOLS_FILE =
  Path("agent-monitoring/tools")`) still point at the 3 physical paths `TCK-20260903-MONITORING-
  DATA-MIGRATION` (child 2, this ticket's hard prerequisite) already retired via `git rm` — those
  paths **no longer exist** in the working tree. `TCK-20260903-MONITORING-DATA-MIGRATION`'s own Out
  of Scope explicitly defers updating `build_index.py` to children 3/4
  (`-CONSUMERS-CORE`/`-CONSUMERS-GATES-DASHBOARD`), which are sibling, in-flight tickets right now,
  not yet landed. Building this ticket's script against the SQLite index would therefore either (a)
  crash if the index is stale/absent, or (b) silently read a stale index built before this ticket's
  own real-corpus run, defeating AC #2 ("runs successfully against the real post-migration corpus").
  **The new script must read `agent-monitoring/data/*/{runs,events,tools}.jsonl` directly**, via the
  glob pattern already established by 3 independent call sites in already-landed code (below) — not
  a 4th independent loader, and not the stale SQLite index.
- `load_jsonl()` (lines 223-240) is the existing single-file/single-directory (`tools-*.jsonl` shard
  glob, old shape) loader `validate.py`/`build_index.py` share — still useful as a per-file JSONL
  reader (line-by-line, tolerant of malformed JSON with a stderr warning), but its directory-glob
  branch targets the **retired** `agent-monitoring/tools/tools-*.jsonl` shape, not the new
  `agent-monitoring/data/<week>/{runs,events,tools}.jsonl` layout. Reusable for the per-file read
  primitive; not reusable as-is for the new multi-week-folder glob.

### The established glob-over-all-weeks read pattern (child 1, already landed — reuse this, not a 4th loader)

`tools/agent-monitoring/record_events.py::compute_tool_stats()` (lines 34-74, landed by
`TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY`) already implements exactly the pattern this
ticket needs for reading across all week folders:

```python
for tools_path in sorted(Path(".").glob("agent-monitoring/data/*/tools.jsonl")):
    for line in tools_path.read_text().splitlines():
        if not line:
            continue
        row = json.loads(line)
        ...
```

The same pattern (glob `agent-monitoring/data/*/<source>.jsonl`, sorted, concatenated) appears
independently in `docs/agent-monitoring/schema.md`'s own "Join Example" (lines 472-502) and in
`tools/agent-monitoring/migrate_monitoring_data.py`'s verification/relocation code. This ticket's
new script should build its own thin loader following this exact pattern (one function per source:
`load_all_weeks(data_dir, source) -> list[dict]`, tolerant of `json.JSONDecodeError` per line with a
stderr warning, matching `validate.py::load_jsonl()`'s error-tolerance convention), parameterized by
an overridable `data_dir` (default `Path("agent-monitoring/data")`) so tests can point it at a
`tmp_path` fixture directory instead of the real corpus — this is the "dual-mode" design point noted
in the ticket's Scope: a real-path default for production use, an injectable path for hermetic
tests, not two different loading *strategies*.

### `unknown-week` is a real, legitimate week folder — must not be special-cased out

`TCK-20260903-MONITORING-DATA-MIGRATION` routes any record whose timestamp field is missing/
unparseable to `agent-monitoring/data/unknown-week/`. It exists today
(`agent-monitoring/data/unknown-week/`, confirmed via `ls`) and is included by the same glob pattern
above (`Path("agent-monitoring/data").glob("*/tools.jsonl")` matches
`agent-monitoring/data/unknown-week/tools.jsonl` exactly like any ISO-week folder). The new script
must not filter it out or treat it specially — it is just another folder under the glob, and the
real corpus already has legitimate cross-week-boundary events landing partly in `unknown-week` (see
below).

## Mechanics / Engine Constraints

Not applicable. `agent-monitoring/` is observability tooling, not simulation mechanics — no
`docs/mechanics/` chapter or `docs/engine/` contract governs it (same conclusion independently
reached by `stored_artifacts/TCK-20260705-MONITORING-RUNID-JOIN/investigation.md`'s own "Mechanics
Constraints" section for the same subsystem).

## Real Corpus Characteristics (direct measurement against the live post-migration data)

Measured directly against the real `agent-monitoring/data/*/` tree (16 week folders,
`2026-W23`–`2026-W36` plus `unknown-week`; 1,229 unique `run_id`s in `runs.jsonl`, 9,018 events,
184,396 tool-call rows) via a one-off scratchpad script (glob + `json.loads`, same pattern as the
new tool will use). Not committed to the repo — reproducible from the loading pattern above.

**Cross-week spans are real and non-trivial, confirming the ticket's core correctness requirement:**

- **8 `run_id`s** have their `runs.jsonl` entry appear in **2 different week folders** (e.g.
  `TCK-20260820-EPIC-WORLD-RENDERING-CORE`: `2026-W34` and `2026-W35`) — a duplicate/legacy-shape
  run record landing in an adjacent week, not just events/tools spanning.
- **17 `run_id`s** have `events.jsonl` rows spanning **2 distinct week folders** (including several
  where one side is the `unknown-week` fallback bucket, e.g. `TCK-20260619-E53Ab-DECISION-PHASE`:
  `2026-W26` + `unknown-week`).
- **11 `run_id`s** have `tools.jsonl` rows spanning **2 distinct week folders** (e.g.
  `TCK-20260614-RESOURCE-BUDGET-GATE`: `2026-W24` + `2026-W25`).
- **8 distinct `(run_id, seq)` tool-call groups** have their own rows split across 2 week folders —
  the exact shape `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION` and
  `record_events.py::compute_tool_stats()`'s docstring describe as the reason the union-of-all-weeks
  read is required at all (e.g. `('TCK-20260830-STALE-37-PHASE-REFERENCES-SWEEP', 6)`: `2026-W35` +
  `2026-W36`).
- **18 `run_id`s** have events landing in a week folder that is **not** a subset of their own
  `runs.jsonl` week(s) — i.e. the run record's own week differs from (or is a strict subset of) the
  weeks its events actually landed in. This is the single clearest confirmation that a same-week-
  scoped join would false-positive on real, legitimate data.

**These are exactly the fixture shapes the required test (b) ("a `run_id` whose `events`/`tools` rows
legitimately span 2+ week folders — must NOT be flagged") should be modeled on** — real, not
hypothetical.

**Retrieval-event and negative-seq exceptions: 0 occurrences in the live corpus** (see Current
Behavior above) — synthetic fixtures are required for scenario (e) since the real corpus currently
has no live examples to draw from.

## `(run_id, seq)` Global Uniqueness — Partially Re-Confirmed, One Caveat Found

Child 1's `compute_tool_stats()` docstring claims "(run_id, seq) is globally unique across weeks,"
citing `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`'s `seq_offset.py` fix as the mechanism
that makes this true **going forward**. Direct spot-check against the real corpus:

- **`tools.jsonl`**: no uniqueness claim applies here by design — many tool-call rows legitimately
  share one `(run_id, seq)` (every tool call an agent makes during one phase). Not a violation
  signal.
- **`events.jsonl`**: **145 distinct `(run_id, seq)` keys have more than one event row** in the real
  corpus (e.g. `('TCK-20260606-DOCSITE-SCHEMA', 1)`, `('TCK-20260614-ARTIFACT-BUDGET-REG', 5)`) —
  these are **not** cross-week duplicates (both copies are in the same week folder in every sampled
  case), consistent with the already-documented legacy-schema-duplicate pattern
  `TCK-20260705-MONITORING-RUNID-JOIN` found in `runs.jsonl` (Class A: an older-schema-generation
  record plus a current-schema record for the same identity). **This does not break the FK check
  this ticket builds** (an existence check — "does at least one event exist at this key" — is
  unaffected by a key having 2+ matches instead of exactly 1), but it does mean the new script must
  not assume `(run_id, seq)` uniquely identifies one `events` row when building its lookup structure
  — build a `set`/`multidict` keyed by `(run_id, seq)`, not a `dict` that silently drops all but the
  last write for a colliding key. Worth a one-line note in the script's docstring; not itself a
  finding requiring new code, since `dict.setdefault(key, []).append(...)` (or a plain lookup `set`
  for the existence-only check) already handles it correctly.

## Real Referential-Integrity Findings Against the Live Corpus (informational — implementer must
triage, this investigation does not resolve them)

Running the 2 target checks by hand against the real corpus produced substantial real violations
that the eventual tool will surface. These are reported here, per the ticket's own Scope
("if it finds real violations, they must be reported and explicitly triaged... never silently
suppressed"), for the implementer/Test-phase to triage explicitly, not to pre-judge:

**Check 1 — `events.run_id → runs.run_id`, excluding `RETRIEVAL-EVENT-*`:**
**18 distinct `run_id`s** (out of 1,241 unique event `run_id`s) have no matching `runs.jsonl` row
anywhere in the corpus. Examples: `TCK-20260701-HAZARD-KIND-RESOLVER-GAP`,
`TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS`,
`TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT`, `run-E43B-1782052032`,
`FOLDER-tickets/todos/simq-integration-14716b96`, several `TCK-20260821-*NOISE-FILL*`/`-COMPILER-*`
run_ids. `run-E43B-1782052032` matches `TCK-20260705-MONITORING-RUNID-JOIN`'s already-documented
"Pattern 1" (`run-{code}-{unix_ts}` legacy debris, pre-refactor, not reproducible by current code) —
its sibling run record exists under a *different* run_id (`run-E43B-1782052024`), a known,
previously-triaged, accepted historical mismatch. Most of the others dated 2026-08-11 through
2026-08-21 are newer than that investigation's cutoff and have not been individually traced by this
investigation — plausible candidates given precedent are `implement-epic.js`'s already-documented
"Pattern 3" batch-write split (events land, run record write step fails/skips) or a `create-tickets`-
workflow `Investigate`-phase event whose concern was later judged a non-actionable duplicate and
never promoted to a real ticket run (`create-tickets.js`'s own `Investigate` phase writes one event
per *concern*, not per resulting ticket — a concern that never became a ticket would have an event
but legitimately no run record). **This is a hypothesis, not a confirmed root cause — flagged as an
open question below**, since resolving it is templated as implementation-time triage in the
ticket's own Scope, not pre-decided here.

**Check 2 — `tools.(run_id, seq) → events.(run_id, seq)`, excluding `run_id: null` and `seq <= 0`:**
**17,274 of 135,804 checked tool-call rows (~12.7%)** have no matching event at their exact
`(run_id, seq)`. This is a large volume and spans **every week folder from `2026-W24` through the
current `2026-W36`** — i.e. **not purely legacy debris that stopped after a known fix landed**.
Two identifiably distinct sub-patterns found by spot-checking specific `(run_id, seq)` groups:

1. **Historical, pre-`TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`/`TCK-20260824-SIDECAR-
   CROSS-SESSION-SCOPE` corruption** — both of those already-closed tickets document, with concrete
   traced examples, that `tools.jsonl` rows were historically mis-attributed to the wrong
   `(run_id, seq)` (stale `.claude/current_run` sidecar bleeding across a crashed run or a
   concurrent session sharing one un-scoped sidecar file) — a mis-attributed row would, by
   definition, point at a `(run_id, seq)` combination that has no real matching event. Both fixes
   are explicitly documented as **not backfilled** (append-only precedent) — pre-fix rows remain
   permanently wrong. This plausibly explains a large share of the `2026-W24`–`2026-W34`-era volume
   (pre-2026-08-24).
2. **A newly-observed, *not* pre-existing-debris case, found directly in this investigation**:
   `TCK-20260902-MONITORING-SHARD-MIGRATION` — confirmed `DONE` in `tickets/done/`, a real,
   substantial, completed piece of work (229 real tool-call rows across 6 `seq` groups spanning
   ~1.5 real hours on 2026-09-02) — has **zero** `events.jsonl` rows and **zero** `runs.jsonl` rows
   anywhere in the corpus. Every one of its 229 tool rows is therefore an orphan under Check 2 (no
   matching event can exist since no event exists at all), and its complete absence from `runs.jsonl`
   means it would also be invisible to a hypothetical "does this run_id have a runs.jsonl row"
   check — this ticket's Check 1 wouldn't even see it, since Check 1 only walks `events.jsonl`, which
   also has zero rows for this `run_id`. This is dated well after both documented sidecar fixes
   (2026-08-24) and inside this very epic's own week (`2026-W36` write-time for some of its rows,
   though the tool-call `ts` values are 2026-09-02). **This is the single most notable finding of
   this investigation**: it demonstrates the referential-integrity gap is not purely historical
   noise from already-fixed mechanisms — a fully completed ticket's entire `events`/`runs` write
   can still go missing under current code, while its `tools.jsonl` rows (written independently, by
   the always-on `PostToolUse` hook) land correctly. Flagged prominently for implementation-time
   triage — **not resolved here**, since root-causing *why* `writeMonitoring`'s events/run writes for
   this specific ticket never landed is beyond this ticket's own scope (Out of Scope: "Repairing any
   orphan this check finds"). A likely candidate area to look at first, given proximity: this
   ticket's own epic (`TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`) was actively changing
   `record_events.py`/`record_run.py`'s write paths (child 1) at almost exactly this time — a
   transient failure during the epic's own dogfooding of its own in-flight change is plausible but
   unverified.

**A separate, clearly benign class also present in the current week's orphan set**: this
investigation's own in-flight tool-call rows (this session, `run_id =
TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY`, `seq=1`) appear as orphans in `2026-W36`
*because the Investigate-phase event for this very ticket has not been written yet* (events are
written in a batch at end-of-phase; `tools.jsonl` rows land live via the hook). **This is expected,
transient, and self-resolving** — any currently-in-progress run's most recent phase will show as an
"orphan" until its phase-completion event write lands. The tool's own report/docstring should call
this out explicitly so a reader doesn't mistake "the tool I'm running it from is currently flagged"
for a bug.

## Prior Work

- `TCK-20260705-MONITORING-RUNID-JOIN` (`stored_artifacts/TCK-20260705-MONITORING-RUNID-JOIN/`) —
  established the `end_ts`-completion dedup-by-run_id methodology `validate.py` still uses
  (`LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES`), and 3 named patterns of historical
  run_id/event mismatch (Pattern 1: `run-{code}-{ts}` legacy debris; Pattern 2: ad hoc `-REDESIGN`
  run_id suffix; Pattern 3: `implement-epic.js` batch-write split between events and run record) —
  directly relevant precedent for interpreting this ticket's Check 1 orphan list.
- `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`
  (`stored_artifacts/TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION/`) — the closest prior art
  to this ticket's Check 2: an empirical `(run_id, seq)`-grouped cross-check of `tools.jsonl` against
  `events.jsonl`'s `tool_call_count`, tracing ~35% historical mismatch to 2 now-fixed mechanisms
  (Scope-phase sidecar gap; `writeMonitoring`'s own bookkeeping calls polluting the last open phase
  before its sidecar-clear ran). Directly explains a large share of this ticket's own Check 2 orphan
  volume as pre-existing, non-backfilled, already-understood historical corruption — but does not
  explain the `TCK-20260902-MONITORING-SHARD-MIGRATION` zero-events case found above.
- `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` (referenced in schema.md, not separately re-read in
  full here) — fixed cross-session sidecar contamination via per-session-scoped `.claude/
  current_run.<SESSION_ID>` files; also explicitly not backfilled.
- `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION` — confirms the cross-week `(run_id, seq)`
  collision mechanism and its `seq_offset.py` fix; this ticket's core correctness requirement (never
  false-flag a legitimate cross-week reference) is the direct, explicit continuation of the same
  concern this ticket's own architecture-reviewer independently re-derived.
- `TCK-20260729-SHADOW-PACKET-CALL-SITE` — established the negative-`seq` shadow-row convention this
  ticket's exclusion list must implement (not independently re-read in full; schema.md's own
  description, lines 326-347, is authoritative and was read directly).
- `TCK-20260902-MONITORING-SHARD-MIGRATION` (`tickets/done/`) — the prior epic's tools-only migration
  whose own monitoring records are, ironically, the clearest live example this investigation found
  of a genuinely missing `events`/`runs` pair (see Real Referential-Integrity Findings above).

## Docs Requiring Update

- `docs/agent-monitoring/schema.md`: this ticket's own real-corpus run (captured above) surfaces at
  least one referential-integrity finding (`TCK-20260902-MONITORING-SHARD-MIGRATION`'s complete
  absence from `events`/`runs.jsonl` despite real, completed, dated tool-call activity) that is not
  yet documented anywhere, and the doc's own "Known Limitations" section is the established location
  for this exact class of finding (it already documents 3 related classes: legacy schema generations
  without `end_ts`, the manual/ad hoc `run_id` convention, and a pointer to
  `TCK-20260705-MONITORING-RUNID-JOIN`'s full evidence). Once this ticket's tool produces its final
  real-corpus report (captured in this ticket's own Test Summary per AC #2), add a short
  "Referential Integrity" entry to Known Limitations summarizing the check's existence, its 3
  documented exceptions, and a pointer to whatever volume/triage conclusion the real run lands on —
  mirroring the existing "Full evidence" pointer pattern to `TCK-20260705-MONITORING-RUNID-JOIN`'s
  own investigation. **Deferred to implementation time**: the exact wording depends on how the
  implementer's own real-corpus run (re-run against the finished tool, not this investigation's
  scratchpad script) characterizes the volume/triage — write the entry then, not now.

`docs/parity_ledger/*.yaml` was considered and excluded: `agent-monitoring/` is observability
tooling, not a simulation subsystem, and no `docs/parity_ledger/` file (`substrate.yaml`,
`combat_movement.yaml`, `strategic_cognition.yaml`, `town_resource.yaml`, `progression.yaml`,
`social_narrative.yaml`, `world_dynamics.yaml`, `infrastructure.yaml`) tracks monitoring-tool
internals — `infrastructure.yaml` (the closest by name) covers "Replay, telemetry, observability,
workers" in the sense of simulation-replay/telemetry infrastructure, not this repo's own CI/agent
tooling meta-observability; confirmed by `TCK-20260705-MONITORING-RUNID-JOIN`'s own investigation
reaching the identical conclusion for the same subsystem ("None. `agent-monitoring/` is
infrastructure, not a simulation subsystem tracked in `docs/parity_ledger/`").

The Mechanics Bible (`docs/mechanics/*.md`) and Engine Contracts (`docs/engine/*.md`) were
considered and excluded for the same reason — no chapter or contract governs agent-monitoring
tooling.

## Parity Ledger Overlap

None (see Docs Requiring Update above for the explicit reasoning).

## Risks and Open Questions

1. **Open question, not resolved here (implementer/Test-phase decision)**: what should the tool's
   exit code / severity contract be given the real corpus already has ~17K Check-2 orphans and 18
   Check-1 orphans? `validate.py`'s own convention is errors → exit 1, warnings → exit 0 regardless.
   Given the volume found is dominated by already-documented, non-backfilled historical corruption
   (not a currently-reproducible bug for most of it), a hard-fail exit code on the real corpus today
   would likely be the wrong default (it would immediately "fail" every future invocation against
   accumulated legacy noise, training operators to ignore it) — but the ticket's own Out of Scope
   explicitly defers "wiring this into `done_checker_static.py`/CI" as a deliberate decision, not a
   default. Recommend: report both counts unconditionally (never suppress), but do not hard-fail
   the process on volume alone unless/until a gate-wiring decision is separately made — mirroring
   `compute_drift_report()`/`compute_tool_count_drift_report()`'s existing "never gates anything,
   purely additive reporting" precedent in the same file. This is a plan-time decision, flagged here
   as the most consequential design fork this investigation surfaced.
2. **Open question**: root cause of `TCK-20260902-MONITORING-SHARD-MIGRATION`'s complete
   `events`/`runs.jsonl` absence (see Real Referential-Integrity Findings) is unconfirmed — it should
   be reported and triaged per the ticket's AC #3, not silently folded into "known legacy noise,"
   since (unlike the sidecar-collision-era rows) it postdates every currently-known fix and involves
   a *complete* absence of both FK targets, not a mis-attributed row.
3. **Open question**: the 17 non-`run-{code}`, non-`FOLDER-*` orphan `run_id`s in Check 1 dated
   2026-08-11 through 2026-08-21 (`TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS`,
   `TCK-20260813-*`, `TCK-20260821-*NOISE-FILL*`/`-COMPILER-*`, etc.) were not individually traced by
   this investigation past the pattern-matching against `TCK-20260705-MONITORING-RUNID-JOIN`'s
   already-documented patterns — several `NOISE-FILL`/`COMPILER-NOISE-FILL` names look like synthetic
   corpus-diversity test fixtures (matching the `simq-corpus-diversity` tooling's naming convention
   elsewhere in this repo) rather than real tickets, which would make their "orphan" status entirely
   expected (a synthetic test fixture's events with no corresponding real ticket run) rather than a
   genuine gap — but this is a hypothesis, not verified by reading `simq_corpus_diversity`-adjacent
   code in this investigation pass.
4. Whether the volume found (~12.7% of checked tool rows) should itself trigger a separate,
   dedicated follow-up ticket to backfill/repair (explicitly Out of Scope for *this* ticket, which
   only verifies+reports) is a call for whoever reads the final real-corpus report at Implementation
   Notes / Test Summary time.

## Anti-Drift Hazards

- **Do not scope the join to a single week folder anywhere in the implementation** — not even as an
  optimization/fast-path with a "fallback to full scan" — the real corpus already has runs whose
  `runs.jsonl` week differs from their `events`/`tools` week(s) (8 + 17 + 11 + 18 real examples
  above). Any code path that resolves a `run_id`'s week before searching (e.g. "look up which week
  folder `runs.jsonl` says this run_id is in, then only scan that folder's `events`/`tools`") is a
  latent bug even if it happens to pass a same-week-only test.
- **Do not build a 4th independent JSONL-across-weeks loader.** Reuse the
  `sorted(Path(...).glob("agent-monitoring/data/*/<source>.jsonl"))` pattern already established by
  `record_events.py::compute_tool_stats()`, `migrate_monitoring_data.py`, and schema.md's own Join
  Example — 3 independent precedents already converge on this exact shape.
- **Do not depend on `agent-monitoring-index/monitoring.db` / `build_index.py`.** It is confirmed
  stale against the new layout as of this investigation (still points at the 3 retired physical
  paths) and updating it is explicitly out of scope for sibling tickets 3/4, which have not landed
  yet. A script that requires the index to exist/be current would either crash or silently read
  stale data.
- **Do not filter out `unknown-week`** — it is a real, currently-populated folder under the same glob
  pattern as every ISO-week folder, and events legitimately span into it in the real corpus today.
- **Do not treat the retrieval-event / negative-seq exceptions as dead code because the real corpus
  has 0 current examples.** Both are schema-sanctioned, gated-off-by-default mechanisms that could
  produce real rows at any time (`SHADOW_CONTEXT_PACKET_ENABLED=1`, or any standalone
  `hybrid_retrieval.py`/`retrieval_cache.py` invocation) — the exclusion logic must be implemented
  and exercised via synthetic fixtures (scenario e), not skipped because "the real corpus doesn't
  need it today."
- **Do not silently drop the 145 duplicate-`(run_id, seq)`-event-key rows** from whatever data
  structure indexes events for the lookup — use a `set` of valid keys (or a `dict` mapping to a
  list) built by iterating and adding every row, never a `dict(events_by_key)`-style comprehension
  that overwrites on collision, or a rare real duplicate-key event could silently vanish from the
  lookup depending on file/glob ordering.
- **Do not conflate this ticket's own scope's tool-row orphans (Check 2) with the currently-running
  investigation/implementation session's own in-flight rows.** A run still mid-pipeline will show its
  latest phase's tool calls as orphans until that phase's event-batch write lands — this is expected,
  not a bug, and the tool's own documentation must say so explicitly (see Real Referential-Integrity
  Findings) so a future reader running the tool against a live corpus mid-run doesn't misread their
  own current activity as a violation.
- **Do not attempt to fix or backfill any orphan found** — Out of Scope is explicit on this, and 2
  prior tickets in this exact area (`TCK-20260711-...`, `TCK-20260824-...`) already established the
  "document, never backfill, append-only precedent" convention for this class of finding.
