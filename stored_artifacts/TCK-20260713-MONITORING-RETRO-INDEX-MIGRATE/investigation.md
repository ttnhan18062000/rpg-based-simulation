---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE
artifact_type: investigation
tags: [agent-monitoring, data-quality, schema]
---

# Investigation — TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE

## Current Behavior

**`tools/agent-monitoring/generate_retro.py` (816 lines).** The ticket's stated line numbers for
the three helpers are stale (predate later insertions in this file); corrected:

- `_resolve_status(r)` — **line 88**, not 71. `return r.get("final_status") or r.get("status")`.
  Deliberately non-normalizing (docstring: legacy spelling variants like `"success"`/`"done"`
  stay distinct from `"DONE"`).
- `_is_legacy_event(e)` — **line 99**, not 82. `return e.get("agent") is None`.
- `_is_gate_fail(r)` — **line 107**, not 90. `return _resolve_status(r) not in ("DONE",
  "EPIC_SCOPED", "IN_PROGRESS")`.

**Call-site count is wrong in the ticket — verified by grep, not assumed.** The ticket claims "6
call sites inside `generate()`". Actual count, by function:

| Helper | Call sites | Location |
|---|---|---|
| `_resolve_status` | 288, 299, 335, 356, 367, 369 (6) | inside `compute_retro_metrics()` |
| `_resolve_status` | 807, 808 (2) | inside `_update_index()` — a **separate function**, not `generate()` or `compute_retro_metrics()` |
| `_is_gate_fail` | 289, 336 (2) | inside `compute_retro_metrics()` |
| `_is_legacy_event` | 420, 421 (2) | inside `compute_retro_metrics()` |

**Total: 12 call sites across 3 helpers, spread over 2 functions — not 6, and not inside
`generate()`.** `generate()` (521-741) itself never calls any of the three helpers directly; it
only renders the dict `compute_retro_metrics()` returns. The call sites live in
`compute_retro_metrics()` (extracted from `generate()` by `TCK-20260718-RETRO-STATS-REFACTOR`,
which is presumably why the ticket's "inside `generate()`" framing is now inaccurate) and in
`_update_index()` (789-811, called from `main()` after `generate()` returns, rebuilds
`agent-monitoring/retro/index.md` by calling `load_jsonl(RUNS_FILE)` directly and re-deriving
DONE/gate-fail counts per ISO week). **`_update_index()` is not named anywhere in the ticket's
Scope, yet it duplicates 2 of the 12 call sites and its own direct `load_jsonl(RUNS_FILE)` read**
— migrating "together, not partially" per the ticket's own Scope wording requires resolving
whether `_update_index()` is in scope (see Risks #3).

**Critical finding — `build_index.py` imports `_resolve_status` directly from
`generate_retro.py` (build_index.py:39, `from generate_retro import _resolve_status`), and calls
it at line 111 to populate the `runs.resolved_status` SQL column.** This means:
1. `resolved_status` in the index is **guaranteed identical to `_resolve_status()`'s output by
   construction (import), not reimplementation** — confirmed directly by
   `tests/tools/test_build_index.py::TestNormalizationParity::test_resolved_status_matches_generate_retro_resolve_status`
   (line 184), which builds an index and asserts `row[0] == _resolve_status(record)` for every
   fixture row. **AC2's "byte-identical... proving the new index's normalization preserves
   `_resolve_status`'s documented non-normalizing behavior" is therefore already proven true by
   this existing test, by construction** — there is no risk of the index's `resolved_status`
   silently normalizing legacy strings that `_resolve_status()` would leave distinct, because it
   is the exact same function.
2. **The function `_resolve_status()` cannot be literally deleted from `generate_retro.py`
   without breaking `build_index.py`'s import** — `build_index.py` is explicitly Out of Scope for
   this ticket ("that is sibling ticket TCK-20260713-MONITORING-SQLITE-INDEX's responsibility").
   AC1's literal wording ("removed... from generate_retro.py") is not achievable without either
   (a) an out-of-scope edit to `build_index.py`, or (b) moving the function to a third shared
   module both files import from (a materially larger, unrequested architectural change — not
   named anywhere in this ticket's Scope). See Risks #1 for the recommended resolution.
3. `_is_legacy_event`/`_is_gate_fail` have **no external importers** (confirmed by repo-wide
   grep) — only `_resolve_status` is load-bearing for `build_index.py`. Those two are free to be
   literally removed/inlined if the plan chooses.

**`compute_retro_metrics()`/`generate()` are pure functions tested by direct dict injection, not
through the index.** `tests/tools/test_generate_retro.py` (709 lines, confirmed by direct read —
more like 35 tests, not "30+" loosely) calls `compute_retro_metrics(runs, events)` and
`generate(runs, events, label, ...)` directly with hand-built plain dicts (e.g. `_BASE_RUN =
{"run_id": ..., "final_status": "DOD_BLOCKED", ...}`) that never pass through
`build_index.py`/SQLite at all. **If the migrated call sites inside `compute_retro_metrics()` are
changed to read a pre-injected key (e.g. `r["_resolved_status"]`, mirroring `query.py`'s
`load_runs_from_index()` convention) instead of calling `_resolve_status(r)`, every one of these
~15+ direct-dict tests that rely on `final_status`/`status` resolution (DONE counts, gate-fail
counts, tag breakdowns, tier distribution) would silently break**, because their fixture dicts
carry no such injected key and were never designed to. This directly conflicts with AC4's "tests
… continue to pass unmodified." See Risks #1 — this is the second half of the same architectural
tension `_resolve_status`'s cross-import creates.

**`tools/agent-monitoring/build_index.py`** (211 lines) — confirmed: `runs` table has
`resolved_status TEXT`, `is_complete INTEGER` columns; `events` table has `run_id`, `seq`,
`workflow`, `phase`, `agent` (raw, **not** case-normalized via `_normalize_phase`/`_normalize_agent`)
columns, plus `raw_json` on both. No column exists for "is legacy" on `events` — but this is moot,
since `_is_legacy_event()`'s discriminator (`agent is None`) is already directly readable off the
raw `agent` column/field with zero index involvement; migrating this predicate needs no schema
support at all. `_ingest_runs()`/`_ingest_events()` apply **no filtering** (unlike `_ingest_tools()`,
which skips malformed rows) — every `runs.jsonl`/`events.jsonl` line becomes exactly one row, so
there is no `build_index.py`-side row-dropping risk analogous to the tools-table divergence found
by the VALIDATE-INDEX-MIGRATE ticket (see Prior Work).

**`tools/agent-monitoring/query.py`** (166 lines) — the precedent for the read-loading shape:
`open_index(db_path)` hard-requires the db (`sys.exit(1)` if missing, query.py:29-36).
`load_runs_from_index(conn)` (39-46) parses `raw_json` back to a plain dict and injects
`record["_resolved_status"] = resolved_status` from the SQL column — this is the exact pattern a
migrated `generate_retro.py` would need to either adopt (breaking AC4, per above) or avoid.

**`tools/agent-monitoring/validate.py`** (326 lines) — sibling migration precedent
(`TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE`, already shipped). Its `open_index()` is
byte-identical to `query.py`'s (hard `sys.exit(1)` on missing index) — **this ticket's own Scope
explicitly rejects that pattern** ("must never become a hard gating dependency... build-on-demand,
or a clear error"). `validate.py`'s `main()` still has its own `load_jsonl()` function retained
(imported by `legacy_reader.py`/`ingest.py`), separate from `RUNS_FILE`/`EVENTS_FILE`/`TOOLS_FILE`
constants which were deleted.

## Mechanics / Engine Constraints

Not simulation-mechanics work. `docs/agent-monitoring/README.md` scopes `agent-monitoring/` to
"Claude Code agents only... not the RPG simulation engine's Grafana/Loki/Prometheus stack." No
`docs/mechanics/` chapter or `docs/engine/` contract governs this file. The one binding constraint
is CLAUDE.md's Hard Rule: *"Monitoring write failure must never fail the workflow."* This ticket
is entirely read-side (no write-path file is touched), so this rule constrains the *fallback
design* only in spirit — a weekly retro report failing hard because the index wasn't built is
exactly the kind of avoidable gating failure this rule's intent argues against, which is
consistent with (and likely the motivation for) this ticket's explicit divergence from
`query.py`/`validate.py`'s hard-`exit(1)` precedent.

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml`:

- **INFRA-289** (`query.py` migration, `status: verified`) — its own text explicitly names this
  ticket as a separate, not-yet-done sibling: "Does not migrate... `generate_retro.py`'s
  legacy-shape helpers (TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE) -- separate sibling tickets."
- **INFRA-290** (`validate.py` migration, `status: verified`) — same disclaimer, and documents a
  **real, narrow, non-gating output divergence** it found on the live corpus (a `tools.jsonl` row
  with valid `run_id`+`seq` but no `tool` field: counted by `validate.py`'s hand-rolled loop, but
  excluded by `build_index.py`'s stricter `_ingest_tools()`, shifting a "Mismatches" count from
  487→488). **This specific divergence class does not transfer to this ticket** —
  `generate_retro.py` never reads `tools.jsonl`, and `_ingest_runs()`/`_ingest_events()` (the two
  tables this ticket's data would come from) apply no analogous filtering (confirmed above). No
  equivalent divergence is expected, but the *pattern* (measure against live data before assuming
  parity, not just curated fixtures) is directly relevant precedent for this ticket's own AC2
  verification.
- **INFRA-283** (phase/agent case-fold normalization) — explicitly states its own vocabulary
  handling is "a different vocabulary with its own separate, already-documented no-normalize-
  legacy-strings design in `_resolve_status`'s own docstring, not reopened here." Confirms
  `_normalize_phase`/`_normalize_agent` are a deliberately separate concern from the three helpers
  this ticket targets — not in scope here, no index column supports them anyway (see Current
  Behavior).
- No P0 entries touch this subsystem in `infrastructure.yaml` — nothing here requires a passing
  `test_path` as a hard gate beyond this ticket's own new tests.
- This ticket's own eventual migration (once shipped) should add a new `INFRA-29x` entry
  (next-free-ID pattern established by INFRA-289/290's own Plan-phase "re-verify max ID
  immediately before assignment" convention) — not resolved here, a Parity-phase action.

## Prior Work

- **`stored_artifacts/TCK-20260713-MONITORING-SQLITE-INDEX/`** (plan.md, investigation.md) — built
  `build_index.py`. Its own investigation.md explicitly flags (Anti-Drift Hazards #5, Prior Work
  reference): "the sibling `TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE` ticket will need
  `build_index.py`'s schema to expose normalized phase/agent values, not just `resolved_status`,
  to be a real upgrade" — but confirms this schema gap is real (raw `phase`/`agent` columns only)
  and out of this ticket's own reach (`build_index.py` is out of scope here too).
- **`stored_artifacts/TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE/plan.md`** — **direct
  precedent for the exact architectural conflict this ticket faces.** Its own ticket's AC3 asked
  to "reduce `LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES` to a single reference,"
  but those constants are imported directly by `build_index.py` and `legacy_reader.py` — literally
  identical shape to this ticket's `_resolve_status`/`build_index.py` conflict. The plan explicitly
  overrode the ticket's literal wording: *"AC3 is resolved as inapplicable/satisfied-by-inaction
  for the two named functions... `validate.py` is already the canonical upstream definer... Do not
  attempt to 'fix' this later by inverting the import direction."* This is the strongest available
  precedent for how Planning should resolve this ticket's AC1 (see Risks #1).
- **`stored_artifacts/TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE/plan.md`** — establishes the
  `open_index()`/`load_*_from_index()` helper shape and the hard-`exit(1)` missing-index pattern
  this ticket must explicitly diverge from (per its own Scope). Also documents the "Python-side
  filtering, load `raw_json` back to identical dicts" approach as the lowest-risk way to make
  before/after output parity provable — directly reusable here.
- **`docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md`** — the originating
  idea doc. Confirms `generate_retro.py`'s helpers were the explicit "third migration target" from
  the start, and its own Open Questions leave "should the index ever build automatically" and
  "should normalization be a build-time SQL column vs. a Python helper" both unresolved — this
  ticket's fallback design directly re-opens the first of those two.

## Risks and Open Questions

1. **[BLOCKING — requires Plan-phase decision, not resolvable in Investigation] AC1's literal
   "removed... from generate_retro.py" is not achievable as written**, for two independent
   reasons found above: (a) `build_index.py` imports `_resolve_status` directly and is out of
   scope to edit, so the function definition cannot be deleted; (b) `compute_retro_metrics()`'s
   own call sites are exercised by ~15+ existing tests that inject plain dicts with no pre-resolved
   status key, so changing those call sites to read an index-injected key (rather than calling
   `_resolve_status(r)`) would break AC4's "tests continue to pass unmodified" — the two ACs
   directly conflict as stated. **Recommended resolution, following the VALIDATE-INDEX-MIGRATE
   precedent exactly:** keep `_resolve_status()`'s *definition* in `generate_retro.py` (it remains
   the canonical function `build_index.py` imports and the index's `resolved_status` column is
   built from), keep `compute_retro_metrics()`'s internal call sites calling it exactly as today
   (zero behavior change, AC4 trivially satisfied), and migrate only the **data-loading layer** in
   `main()`/`_update_index()` — from `load_jsonl(RUNS_FILE)`/`load_jsonl(EVENTS_FILE)` (which
   re-scans and re-parses the raw files) to `open_index()`/`load_runs_from_index()`/
   `load_events_from_index()` returning **field-identical dicts from `raw_json`** (no injected
   key, mirroring `validate.py`'s `load_runs_from_index` — explicitly *not* `query.py`'s
   `_resolved_status`-injecting variant). This achieves the idea doc's real DRY payoff (one
   physical read of the corpus at index-build time instead of a second linear JSONL scan per
   retro-report invocation) without requiring the two blocked literal changes. `_is_legacy_event`/
   `_is_gate_fail`, which have no external importers, can still be literally removed/inlined if
   desired — only `_resolve_status` is architecturally pinned. This should be stated explicitly in
   plan.md's Summary the same way VALIDATE-INDEX-MIGRATE's plan.md stated it, not silently applied.
2. **[Needs Plan-phase decision] Build-on-demand fallback design.** Concretely: `build_index.py`
   exposes an importable `build(args)` function taking either an `argparse.Namespace` or a
   `types.SimpleNamespace` with `runs_file`/`events_file`/`tools_file`/`db_path` attributes
   (confirmed by `tests/tools/test_build_index.py::_args()`, which constructs exactly this shape).
   `generate_retro.py` can import `build_index` and, when `DEFAULT_DB_PATH` doesn't exist, call
   `build_index.build(types.SimpleNamespace(runs_file=str(RUNS_FILE), events_file=str(EVENTS_FILE),
   tools_file=str(DEFAULT_TOOLS_FILE), db_path=str(DEFAULT_DB_PATH)))` before proceeding — this is
   the same "import, not reimplement" convention `build_index.py` itself already uses for
   `_resolve_status`/`_record_is_complete`. This *does* create a second cross-import edge
   (`generate_retro.py → build_index.py`, in addition to the existing `build_index.py →
   generate_retro.py`) — not a circular-at-call-time problem (Python allows this as long as
   neither top-level module body executes the other's import before the needed name is defined,
   and `_resolve_status` is defined well before any `generate_retro.py` top-level `import
   build_index` would need to resolve it), but worth an explicit test asserting the import
   succeeds without `ImportError`, since this repo's other three modules deliberately avoid
   cross-importing each other by convention (validate.py's plan.md: "no cross-import between the
   two modules' index-loading helpers"). Alternative: catch the failure and print a clear
   human-actionable error (`"run `make agent-monitoring-index` first"`, matching `query.py`'s
   message) without auto-building — simpler, no new import edge, but a scheduled/automated weekly
   retro run would then need an out-of-band `make agent-monitoring-index` step first, which is
   plausibly what the ticket's "must never become a hard gating dependency" is trying to avoid in
   the first place. This is a real design fork the investigation cannot resolve unilaterally.
3. **`_update_index()` (789-811) is not named in the ticket's Scope but duplicates 2 of the 12
   `_resolve_status` call sites and has its own direct `load_jsonl(RUNS_FILE)` read** (line 796).
   If left unmigrated, the migration is partial by construction, in tension with the ticket's own
   "migrated together (not partially)" wording for the 3 helpers/6-claimed-call-sites. Flag for
   Plan-phase scope clarification — either explicitly include `_update_index()`'s 2 call sites and
   its `load_jsonl(RUNS_FILE)` read in scope, or explicitly document why it's excluded.
4. **`generate_retro.py`'s own `load_jsonl()` (44-47) has no malformed-line tolerance** — unlike
   `validate.py`'s `load_jsonl()` (which catches `json.JSONDecodeError` per line and warns), a
   malformed JSONL line currently crashes `generate_retro.py` outright. If `main()` migrates to
   reading through the index (built by `build_index.py`, which reuses `validate.py`'s
   `load_jsonl()`), a line that previously crashed `generate_retro.py` would now be silently
   skipped-with-a-warning at build time instead. Low risk (no known malformed lines in the live
   corpus), but a real behavior change if it ever occurs — worth a one-line note in the plan, not
   a blocker.
5. **No existing test isolates the 3 helpers in direct predicate-level unit tests today** —
   confirmed by full read of `tests/tools/test_generate_retro.py`: every test drives them
   indirectly through `compute_retro_metrics()`/`generate()`. The ticket's Assumptions claim is
   accurate. This is genuinely valuable, low-risk, achievable-regardless-of-Risk-#1's-resolution
   work.

## Anti-Drift Hazards

- **Do not delete `_resolve_status()`'s definition** without first confirming `build_index.py`'s
  `from generate_retro import _resolve_status` (build_index.py:39) has been independently
  re-pointed — which is out of this ticket's scope to do. Deleting it will break
  `tests/tools/test_build_index.py` (imports it directly at line 44 too) and the live
  `make agent-monitoring-index` target.
- **Do not touch `build_index.py`, `query.py`, or `validate.py`** — all three are explicitly Out
  of Scope, per the ticket and confirmed by each sibling ticket's own "does not migrate
  generate_retro.py" disclaimer in the parity ledger.
- **Do not normalize legacy status-string spellings** (`"success"`→`"DONE"` etc.) anywhere in this
  migration — `_resolve_status()`'s docstring and `INFRA-283`'s entry both explicitly document
  this as deliberate, verified-untouched behavior. The index's `resolved_status` column is built
  from the exact same non-normalizing function, so this is automatically preserved as long as
  Risk #1's recommended resolution (keep the function, migrate only the loader) is followed.
- **Do not introduce a hard `sys.exit(1)`-on-missing-index pattern** copied wholesale from
  `query.py`/`validate.py` — this ticket's Scope explicitly requires the opposite (build-on-demand
  or a non-fatal clear error), a deliberate, stated divergence from sibling precedent, not an
  oversight to "fix" toward consistency.
- **Do not touch `_normalize_phase`/`_normalize_agent`/`_flag_outliers`/`_canonicalize`** — a
  different, already-shipped normalization concern (INFRA-283/284) with no index column support
  and not named anywhere in this ticket's Scope.
- **Do not modify `agent-monitoring/runs.jsonl`/`events.jsonl`/`tools.jsonl`** — read-only source
  of truth throughout; this ticket is 100% read-side, same as its two shipped siblings.
- **Do not silently drop the 2 `_update_index()` call sites from the migration without an explicit
  scope note** — see Risks #3; an implementer who greps only for "6 call sites inside generate()"
  (the ticket's literal, stale wording) will miss them entirely.
