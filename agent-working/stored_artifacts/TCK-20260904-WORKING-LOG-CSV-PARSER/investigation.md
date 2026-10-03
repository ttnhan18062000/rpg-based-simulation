---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-WORKING-LOG-CSV-PARSER
artifact_type: investigation
tags: [ai, data-quality]
---

# Investigation — TCK-20260904-WORKING-LOG-CSV-PARSER

## Current Behavior

**`tickets/working_log.csv` shape (confirmed by direct scan, 2026-09-06):** 3377 physical lines,
header `timestamp,ticket_id,title,status,summary,artifacts_path` (line 1), 3376 data rows read by
`csv.reader` (quote-aware). The file **does** use RFC-4180 double-quoting for some rows (1702 lines
contain a `"` character; e.g. line 6, line 8) — it was not "never written with CSV quoting." Quoting
is applied inconsistently: some free-text fields with embedded commas are correctly wrapped in
`"..."`, others are not, because every append is a manual/LLM-authored text edit (`CLAUDE.md`'s
Workflow Rule: "Append to the bottom of `tickets/working_log.csv`") — there is no programmatic
writer anywhere in the codebase. Confirmed by `grep -rn "working_log.csv" tools/ src/` +
inspecting every hit: all touches are read-only (`tools/validate_working_log.py`,
`tools/knowledge_search.py`, `tools/ticket_stats_report.py`, `tools/agent-monitoring/{validate,
epic_staleness_check}.py`, `tools/agent_codex_pilot_entrypoint/preparation.py`,
`tools/codebase_health_baseline.py`, `tools/gate_checks/done_checker_static.py`); none opens the
file in append/write mode. So the corruption source really is "no enforced writer, free-text
committed by hand" — confirming the ticket's framing that the manual-append convention itself is
the open corruption source.

### Finding 1 — 11 field-count-mismatch rows (ticket's claim CONFIRMED exactly, with real content)

A full-file `csv.reader` scan (quote-aware, matching the file's actual header of 6 fields) finds
**exactly 11** rows where the parsed field count != 6. Real line numbers and content (verified
directly, not estimated):

| Line | Fields | Ticket ID | Root cause |
|---|---|---|---|
| 1511 | 9 | TCK-20260817-RUNTIMEMODE-BENCH-SCOPING | Unescaped commas in `summary`, **plus** a literal unescaped `"` mid-field (`result[mode_sequence"]`) that desyncs `csv.reader`'s quote-tracking state for the rest of the row — worse than a plain comma split. |
| 3104 | 9 | TCK-20260817-RUNTIMEMODE-BENCH-SCOPING | Exact duplicate of line 1511 (see Finding 2). |
| 1581 | 7 | TCK-20260820-EPIC-WORLD-RENDERING-CORE | Unescaped comma inside `artifacts_path` (`none (epic, scope-only)`). |
| 3174 | 7 | TCK-20260820-EPIC-WORLD-RENDERING-CORE | Exact duplicate of line 1581 (see Finding 2). |
| 3245 | 7 | TCK-20260831-HOTFIX-TEST-SCOPER-BARE-DIRECTORY-RULE | Unescaped comma inside `title` (`"Always the Bare Directory, Never Cherry-Picked Files"`); embedded `"` characters are literal English quotation marks, not CSV escaping — harmless on their own since mid-field quotes are literal to `csv.reader`, the comma is the actual splitter. |
| 3253 | 7 | TCK-20260831-HOTFIX-TEST-SCOPER-BARE-DIRECTORY-RULE | Exact duplicate of line 3245 (independent duplicate, **not** part of Finding 2's mega-block — see below). |
| 3284 | 7 | TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH | Unescaped comma inside `title`. |
| 3287 | 9 | TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE | Multiple unescaped commas across `title`/`summary`. |
| 3289 | 9 | TCK-20260902-EPIC-RPG-M3-REPRODUCTION | Multiple unescaped commas inside `summary`. |
| 3294 | 8 | TCK-20260902-HOTFIX-TEST-SCOPE-COVERAGE-AI-SYSTEMS-ALLOWLIST-GAP | Unescaped commas inside `summary`. |
| 3307 | 8 | TCK-20260903-CLAN-LIFECYCLE-SUCCESSION | Unescaped comma inside `title` (`joining, leaving, and succession-on-death`). |

All 11 are dated 2026-08-17 through 2026-09-03 — recent and live, confirming the ticket's "as
recently as 2026-09-03" claim. Given the known 6-column schema, a heuristic recovery is plausible
for most (`title`/`summary` are the only free-text fields; `timestamp`/`ticket_id`/`status` are
fixed-shape and `artifacts_path` is the trailing field, so "first 3 fields fixed, last field is the
tail, everything between the fixed-shape edges collapses into `title`+`summary`" is workable for
rows 1581/3174/3245/3253/3284/3307/3294/3289 — 9 of 11). **Rows 1511/3104 are the one case where
this heuristic is NOT safely recoverable**: the stray unescaped `"` breaks quote-tracking mid-row,
so a `csv.reader`-based re-join cannot distinguish where the corrupted quote state should have
closed vs. where a genuine field boundary is — these two must be flagged as genuinely ambiguous,
not heuristically repaired, confirming the ticket's premise that full recovery is not always
possible.

### Finding 2 — NEW, previously-undiscovered: a ~1586-row whole-block duplication, dwarfing the "2-3 duplicate rows" the ticket named

**This is the single most important finding of this investigation and materially changes the
problem's shape.** The ticket's own prose cites "2-3 exact-duplicate-content rows (e.g.
RUNTIMEMODE-BENCH-SCOPING at 1511/3104)" as a small, separate, out-of-scope nuisance. Direct
verification shows this dramatically undercounts the real defect:

- Physical lines 2–1587 (1586 data rows) are **byte-for-byte identical**, in the same relative
  order, to physical lines 1595–3180 (confirmed via positional diff: 1586/1592 lines match exactly
  at matching offsets, first divergence at absolute line 1588 vs. 3181).
- Physical line 1594 is a **second, embedded copy of the header row itself**
  (`timestamp,ticket_id,title,status,summary,artifacts_path`), sitting in the middle of the file as
  if it were a data row (confirmed: `grep -n "^timestamp,ticket_id,..."` returns exactly lines 1 and
  1594).
- This means the file's real distinct-entry count is not 3376 but **~1790** (3376 − 1586), which
  reconciles cleanly with the prior `TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS`
  ticket's confirmed 1486-data-row count as of 2026-08-19 (~304 genuinely new rows added since,
  ~19/day — plausible; the naive reading of "1890 new rows in 2.5 weeks" that the raw 3376 count
  implies is not).
- **Root cause identified with high confidence via `git log --numstat -- tickets/working_log.csv`**:
  commit `5993cac3` (PR #90, "M1 Quick Wins & Housekeeping...", merged 2026-08-31) shows **+1640/−0**
  for this file — a pure, large insertion with zero deletions, immediately before the point where
  the duplicate block ends. `.gitattributes` already declares
  `tickets/working_log.csv merge=union` (added by the done `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS`
  ticket on 2026-08-26, five days *before* this incident, with its own claimed "git-level regression
  test proving the shipped merge=union .gitattributes behavior actually resolves concurrent-branch
  appends"). A long-lived branch merged back after the union-merge protection landed still produced
  a whole-history duplication — meaning **the existing merge=union guard did not prevent this
  specific incident**, a real gap in that prior ticket's own verified guarantee.
- A separate, small, *genuinely independent* duplicate pair also exists outside this mega-block:
  lines 3245/3253 (`TCK-20260831-HOTFIX-TEST-SCOPER-BARE-DIRECTORY-RULE`), which is NOT part of the
  1586-row contiguous block (both lines are past line 3180) — this one likely really is an isolated
  manual double-paste, matching the ticket's "2-3 duplicate rows" framing far better than the
  RUNTIMEMODE/EPIC-WORLD-RENDERING-CORE pairs, which are simply two of the ~1586 rows caught up in
  the merge incident.
- **Direct production impact, already live:** `tools/knowledge_search.py::_extract_working_log_rows`
  (line 95) has no ticket_id-uniqueness or field-count check — it would index the bogus embedded
  header row (line 1594) as a real corpus document with `id="ticket_id"`, `title="title"` (both
  fields are truthy so the `if not ticket_id and not title: continue` guard at line 118 does not
  skip it), and it silently indexes ~1586 duplicate documents for tickets that already have a
  correctly-indexed row. This is a stronger, more concrete manifestation of "corrupts automated
  rework-rate/reopened-ticket signals" than the 11 comma-corrupted rows — a naive "row count per
  ticket_id > 1 ⇒ reopened" signal would report ~1586 false positives today.

**This finding does not have to be fixed by this ticket** (Scope explicitly excludes rewriting
historical rows and the sibling duplicate-row concern is Out of Scope), but Plan must decide
explicitly whether the *new* parser's "ambiguous/unparseable" classification (AC1/AC2) should also
surface duplicate-content detection as a first-class signal, given how much larger the real
duplicate population is than the ticket's own framing assumed. Recommend filing a **separate
follow-up ticket** for the `merge=union` gap itself (git-merge mechanics, not a parser concern) —
consistent with this project's "file tickets for workflow gaps, don't silently patch around them"
convention.

### Finding 3 — NEW, previously-undiscovered: 34 lines (17 distinct corrupted rows) with a quote-desync that coincidentally still totals 6 raw fields, invisible to any field-count check

An architecture-review pass over the Plan built on this investigation flagged 34 additional line
numbers as suspected corrupted rows following a different mechanism than Finding 1's 11 rows —
verified directly against the real file, line by line, not trusted at face value.

**Verification method (independent of the reviewer's list):** rather than trust the 34 given line
numbers, this investigation re-derived them from scratch using two independently-constructed
signals run against the *entire* file, both converging on the exact same 34 lines with zero
overlap and zero extra hits:

1. **Parenthesis-balance check on the parsed `artifacts_path` field** (last of 6 fields) for every
   row where `csv.reader` already reports exactly 6 fields: `count("(") != count(")")`. Run against
   all 3365 six-field rows in the file, this flags **exactly 34** rows, every one with
   `artifacts_path == ' no staging artifacts)'` (0 opens, 1 close) — a value that occurs **34
   times** file-wide and **never** as anything else (confirmed via a full distinct-value survey of
   all 1378 distinct `artifacts_path` values across the 3365 six-field rows: no other value has
   unbalanced parens).
2. **A regex on the parsed `summary` field's ending**, independent of `artifacts_path` entirely:
   `,\s*(N/A|none|stored_artifacts)[^,()]*\([^)]*$` (an unclosed `(` clause trailing the field,
   introduced by a fixed vocabulary word). This also flags **exactly 34** rows, and they are the
   **identical 34 line numbers** as signal 1.

Both signals independently confirm the reviewer's count of 34 with no drift — this is the true,
fully-swept total for this pattern, not merely "at least 34."

**Mechanism (confirmed on all 34, not assumed from one example):** every one of the 34 lines has
this exact shape: `summary` is opened with a proper leading `"`, is never given its own closing
`"` at the correct position (immediately before the comma that should start `artifacts_path`), and
instead keeps absorbing characters — including the literal comma that should have been the
field-4/field-5 delimiter — until it hits a **stray `"` that happens to be immediately followed by
`, `** somewhere later in the line. Because a quote-char immediately followed by the delimiter is
syntactically valid CSV for ending a quoted field, `csv.reader` (non-strict) treats that stray
quote as field 4's closing quote and treats the immediately-following comma as the real field
4/5 boundary. Everything after that comma becomes field 5. This absorbs one real comma that should
have stayed inside an intended (but never actually quoted) `artifacts_path` value, so the row still
totals exactly 6 fields — it never trips `len(raw_fields) != 6`.

Concretely, for every one of the 34 lines, the stray `"` lands right after one of three fixed
vocabulary fragments — `N/A (hotfix`, `none (hotfix`, or `none (scope-only epic` — and the parsed
`artifacts_path` is **always** the identical truncated fragment `' no staging artifacts)'` (leading
space, no opening paren). Example (line 1100, confirmed by direct execution): raw tail
`...0 regressions.,N/A (hotfix", no staging artifacts)\n` parses to
`summary` ending `...0 regressions.,N/A (hotfix` and `artifacts_path` = `' no staging artifacts)'`.

**These 34 lines are 17 distinct corrupted append events, not 17+34 separate incidents — they are
caught up in Finding 2's mega-duplication.** Mapping each flagged line to its physical position
shows every one of the 17 lines in the range 1100–1462 has an exact duplicate at `line + 1593` in
the range 2693–3055 — precisely Finding 2's documented `+1593` duplicate-block offset (physical
lines 2–1587 duplicated at 1595–3180). Confirmed pairing (all 17, ticket_id read directly from the
parsed row, not inferred):

| Original | Duplicate | Ticket ID | Reconstructed vocabulary |
|---|---|---|---|
| 1100 | 2693 | TCK-20260720-MONITORING-PIPELINE-BUGFIXES | `N/A (hotfix` |
| 1101 | 2694 | TCK-20260720-CLAUDE-MD-CONSISTENCY-FIXES | `N/A (hotfix` |
| 1102 | 2695 | TCK-20260720-DOCS-AI-SCHEMA-ACCURACY | `N/A (hotfix` |
| 1103 | 2696 | TCK-20260720-GATE-CHECK-WIRING-DECISIONS | `N/A (hotfix` |
| 1318 | 2911 | TCK-20260809-TEST-ISOLATION-RESOURCE-REGISTRY-RESET | `none (hotfix` |
| 1320 | 2913 | TCK-20260809-TEST-ISOLATION-ITEM-REGISTRY-STONE | `none (hotfix` |
| 1329 | 2922 | TCK-20260809-MONITORING-ZERO-DURATION-COMBAT-RUNS-HOTFIX | `none (hotfix` |
| 1332 | 2925 | TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK | `none (hotfix` |
| 1337 | 2930 | TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG | `none (hotfix` |
| 1400 | 2993 | TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC | `none (scope-only epic` |
| 1401 | 2994 | TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION | `none (hotfix` |
| 1415 | 3008 | TCK-20260816-HOTFIX-KGMCP-LOCAL-DATA-BOOTSTRAP-DOCS | `none (hotfix` |
| 1453 | 3046 | TCK-20260817-HOTFIX-TRACEABILITY-PATH-SPAWN-COLLISION-FIXTURE-STALE | `none (hotfix` |
| 1457 | 3050 | TCK-20260818-HOTFIX-URBAN-POLITICAL-1000T-SOCIAL-ANCHOR-STALE | `none (hotfix` |
| 1459 | 3052 | TCK-20260818-HOTFIX-PERF-BUDGET-GUARD-TEST-STALE-RAISE-EXPECTATION | `none (hotfix` |
| 1460 | 3053 | TCK-20260818-HOTFIX-LEGACY-REGRESSION-LANE-MISSING-RESOURCE-BUDGET | `none (hotfix` |
| 1462 | 3055 | TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP | `none (hotfix` |

None of these 17 are the isolated 3245/3253 duplicate pair from Finding 1/2 — all 17 sit inside the
1586-row mega-block, so they inherit Finding 2's "flag, do not deduplicate" treatment as well as
their own field-boundary-corruption flag.

**Detection signal `strict=True` does NOT catch this class — a real, evidence-based negative
result, not assumed.** Direct test: `csv.reader([raw_line], strict=True)` was run against all 34
lines; **all 34 parse successfully under `strict=True`** (no `csv.Error` raised), because a quote
immediately followed by the delimiter is legal CSV even when misplaced. By contrast, the same
`strict=True` test against Finding 1's irreducible rows 1511/3104 **does** raise
(`',' expected after '"'`) — confirming those two are a genuinely different, more severely
malformed shape (stray quote *not* immediately followed by the delimiter) than this 34-line class.
**This means Finding 1's own recommended detection path (`strict=True` re-parse to catch quote-
desync) is not sufficient on its own for this new class** — a parser relying on `strict=True`
alone to catch "quote problems beyond field-count" would silently miss all 34 of these.

**Recommended detection signal: parenthesis-balance check on the last field of an already-6-field
row**, i.e. `artifacts_path.count("(") != artifacts_path.count(")")`. Evidence this does not
false-positive: run against every one of the file's 3365 six-field rows, it flags precisely these
34 and nothing else — every other artifacts_path value in the file (`none`, `none (hotfix)`,
`N/A`, `none (hotfix, no staging artifacts)`, `N/A (hotfix, no staging artifacts)`,
`stored_artifacts/...`, empty, `None`, free-text descriptions like `isolated custom metric
registry`, etc. — 1378 distinct values surveyed) has balanced parens. The sibling regex signal
(`,\s*(N/A|none|stored_artifacts)[^,()]*\([^)]*$` on the `summary` field) independently confirms
the identical 34-line set, so either is usable; the parenthesis-balance check on `artifacts_path`
is recommended as primary since it needs no fixed-vocabulary word list and is a general shape
check, not a literal-string match.

**Recovery: safely possible for all 17 (stronger confidence than Finding 1's 9/11), not merely
plausible.** Unlike Finding 1's rejoin heuristic (which infers a likely boundary), this class's
reconstruction is confirmed against real, independent, correctly-quoted rows using the **identical
fixed vocabulary elsewhere in the same file** — not inferred, matched:
- `N/A (hotfix, no staging artifacts)` appears correctly quoted 10 times elsewhere (e.g. line
  1097, line 1090).
- `none (hotfix, no staging artifacts)` appears correctly quoted 48 times elsewhere (e.g. line
  908).
- `none (scope-only epic, no staging artifacts)` appears correctly quoted 10 times elsewhere,
  including two other real closed epics with the exact same phrase (lines 1381, 1388, 1394).

Reconstruction rule (mechanical, single unambiguous candidate for every one of the 17): strip the
trailing `,{fragment}` from the parsed `summary` (where `{fragment}` is one of the three fixed
vocabulary strings above, always found at the literal end of the parsed `summary` value), and
rebuild `artifacts_path` as `{fragment} + "," + {parsed artifacts_path}` (e.g.
`"N/A (hotfix" + "," + " no staging artifacts)"` → `"N/A (hotfix, no staging artifacts)"`,
byte-identical to the clean convention used elsewhere). **This is categorically different from
1511/3104**, where no independent byte-identical clean instance of the intended content exists
anywhere else in the file to confirm against — these 17 do have that independent confirmation, so
they should be classified as "reconstructable" rather than "irreducibly ambiguous" if Plan decides
to support a reconstruction tier at all (Scope still forbids rewriting historical rows in place —
this is about classification confidence, not license to edit `tickets/working_log.csv`).

**Full-file sweep confirms 34 is the true total, not a partial list.** No occurrences of this
pattern exist outside the given 34 lines — both independent signals above were run against the
*entire* file (all 3365 six-field rows), not just the 34 candidate lines, and neither found
anything beyond the reviewer's original 34.

### Existing parsers

**`tools/validate_working_log.py`** (full file, 81 lines) uses bare `csv.DictReader` (line 34),
no field-count check at all. For a malformed row, `DictReader` maps only the first 6
comma-split values positionally into the 6 known keys and silently discards any extra fields into
`row[None]` (the `restkey`, never read by this script) — so the malformed rows' `title`/`summary`/
`artifacts_path` values are **silently truncated/mis-assigned**, not flagged, exactly as the ticket
describes ("silently mis-mapping columns via bare DictReader"). Confirmed empty-field check
(lines 62-67) does not catch mis-mapped fields either since DictReader always produces non-empty
strings for malformed rows here (they just contain wrong/partial content). This script has **no
dedicated test file** today (`tests/tools/` has none matching `working_log`/`validate_working_log`)
— confirms the ticket's Scope item "Add new tests... no dedicated test file exists today."

**`tools/knowledge_search.py::_extract_working_log_rows`** (lines 95-130) also uses bare
`csv.DictReader` with `encoding="utf-8-sig"`, tolerant of multiple historical column-name variants
(`ticket_id`/`id`/`ID`, etc.) but with zero field-count or plausibility validation — see Finding 2's
concrete embedded-header-row bug. Wrapped in a broad `try/except Exception` (line 128) that only
catches file-level errors (e.g. missing file), never per-row shape issues, since `DictReader` itself
never raises for ragged rows.

**`tools/ticket_stats_report.py::compute_velocity`** (lines 109-141) is the model to mirror per AC3.
It does **not** use `csv`/`DictReader` at all for this specific check — it reads raw lines and does
a manual `line.split(",", 1)[0]` to grab just the `timestamp` column (deliberately avoiding full-row
parsing, since it only needs one field), then validates the timestamp shape via
`generate_retro.py::iso_week()`. Malformed/unparseable rows increment a plain `int` counter
(`unparseable_rows`) that is always present in the returned dict (`{"by_day": ..., "by_week": ...,
"unparseable_rows": N}`), covered by a real test
(`tests/tools/test_ticket_stats_report.py::test_compute_velocity_counts_unparseable_rows_without_crashing`,
lines 79-92) that asserts the exact count and that no exception is raised. **The "mirrored
convention" AC3 references is: a plain integer count, always present in the returned structure,
incremented (never causing a crash or silent drop) for any row whose relevant field(s) fail a shape
check** — not a list of line numbers or a structured record. If the new parser's ambiguous-row
signal needs per-row detail (line number, raw content) for surfacing/debugging, that would be an
*extension* of the mirrored convention, not the convention itself — Plan should decide whether the
minimal int-count contract is sufficient for AC1/AC3 or whether more detail is warranted given this
ticket's stronger requirement ("Explicitly surface each of the 11... as flagged/ambiguous").

## Mechanics / Engine Constraints

Not applicable. `tickets/working_log.csv` is agent-tooling/process bookkeeping, not a simulation
subsystem — no `docs/mechanics/` chapter or `docs/engine/` contract governs its format or parsing.
This mirrors the identical conclusion already reached by
`stored_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/investigation.md`'s own "Mechanics/Engine
Constraints" section.

## Docs Requiring Update

- `docs/ai/ticket-lifecycle.md`: **conditional** — its Finalize-phase section (lines 567-570) shows
  a literal `Append tickets/working_log.csv:` example with no CSV quoting demonstrated. This MUST be
  updated to show the correct quoted-field form only if Plan adopts the "migrate to a stricter
  quoted-field format going forward" branch of the deferred decision; if Plan instead picks the
  tolerant-parser-only branch (no write-time format change), this doc requires no edit. Resolved
  during implementation if the condition (stricter-format adoption) is never met, per the
  established conditional-bullet convention (`TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED`).

The `docs/guides/ticket_reporting.md` (path: `docs/guides/ticket_reporting.md`, under `docs/`)
Pillar 2 section documents `tools/ticket_stats_report.py`'s own `unparseable_rows` convention
specifically, not `validate_working_log.py`'s or `knowledge_search.py`'s. AC3 only requires the
latter two to *match* that convention's shape, not to edit this doc; whether the implementer wants
to cross-reference the new signal here is a nice-to-have, not a requirement of this ticket's scope,
so it is not listed as a required doc.

`docs/parity_ledger/*.yaml` (any subsystem file) is not required to change: two independent prior
investigations (`TCK-20260705-WORKING-LOG-BACKFILL` and this one) both confirm `working_log.csv`
tooling is outside the parity ledger's simulation-subsystem scope.

`docs/guidelines/intentional_divergences.md` is not required to change: this ticket is a tooling/
data-quality fix, not an intentional simulation-behavior divergence from the Mechanics Bible.

## Parity Ledger Overlap

None. Confirmed by direct grep of `docs/parity_ledger/` for `working_log`/CSV-parsing terms
(no hits) and by both this and the prior `WORKING-LOG-BACKFILL` investigation's identical
conclusion.

## Prior Work

Three distinct malformed-row classes now confirmed across this file's history, in chronological
discovery order:

1. **Column-order shape** (found by `TCK-20260705-WORKING-LOG-BACKFILL`, not itself fixed there —
   deferred): `ticket_id` sitting in column 1 instead of column 2 for a historical block (~71 rows,
   2026-06-10 through 2026-06-29 era). Flagged, not fixed, by that investigation (its own explicit
   recommendation was "fix the checker in a follow-up ticket," never executed as far as this
   investigation can tell — `validate_working_log.py` today is still the same bare `DictReader`
   with no column-order detection).
2. **Legacy multi-schema blocks + unescaped-comma splits within the pre-2026-08-19 file**, fixed by
   `TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS`: a two-signal sweep (column-count mismatch,
   then field-plausibility via timestamp/ticket_id shape regexes) found and fixed 156 rows,
   including — critically — a documented case of unescaped commas splitting a well-formed 6-column
   current-schema row into 7-10 raw fields, repaired by "locate the literal `DONE` token as the
   status anchor and rejoin the surrounding fragments." **This is the exact same failure mode as
   this ticket's 11 live rows** — meaning the fix technique from that hotfix (status-token anchor +
   rejoin) is a proven, directly-reusable heuristic for most of the 11, not a novel approach that
   needs re-inventing. That hotfix also explicitly warned that field-count alone misses
   "coincidentally still exactly N columns but wrong content" rows (its own 36-row second-pass
   finding) — directly relevant precedent for this investigation's own Finding 2 (the embedded
   header-row at line 1594 is structurally 6 fields, semantically garbage, and would slip past a
   naive field-count-only classifier exactly the way that hotfix's 36 rows did).
3. **Current live unescaped-comma corruption** (this ticket): the 11 rows in Finding 1, all recent
   (2026-08-17 through 2026-09-03), confirming the manual-append convention keeps reintroducing this
   exact class even after it was fully swept clean as of 2026-08-19 (`TCK-20260819` explicitly
   verified "0 bad rows file-wide" for both its sweeps at close). This is the strongest evidence
   that a parser fix alone, without also closing the write-time gap, will keep needing re-runs.

Additionally, **Finding 2's whole-block duplication is a fourth, structurally distinct defect
class** (row-population duplication via git merge, not malformed-field content) that neither prior
ticket encountered or discussed — it postdates both (occurred 2026-08-31, after
`TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS` closed on 2026-08-19).

**Finding 3 (this investigation's own architecture-review follow-up) is a fifth, structurally
distinct defect class**: a quote-desync that coincidentally still totals exactly 6 raw fields, so
it is invisible to field-count-based detection entirely — unlike class 3 above (this ticket's own
Finding 1, which is field-count-visible) and unlike class 4 (row duplication, not field-boundary
corruption). It shares Finding 1's root failure mode (unescaped-comma-bearing free text plus a
stray literal `"`) but is distinguished by producing a syntactically-valid-yet-wrong 6-field
parse rather than a detectably-wrong field count, and by being independently confirmed
reconstructable via byte-identical clean siblings elsewhere in the file (see Finding 3 for detail).

## Risks and Open Questions

1. **Tolerant-parser-vs-stricter-format lean (this investigation's recommendation, not a decision):**
   Recommend Plan adopt **both**, not an either/or: (a) a tolerant parser for the 11 existing rows
   (and any future legacy rows), reusing the proven status-token-anchor rejoin heuristic from
   `TCK-20260819`, since 9/11 rows are heuristically recoverable and the remaining 2 (1511/3104) can
   be flagged ambiguous without blocking the other 3374 rows; **and** (b) closing the write-time gap
   by having the Finalize-phase instructions (`docs/ai/ticket-lifecycle.md`) explicitly require
   quoting any field containing a comma going forward — since no code path writes this file
   programmatically, "migrate to a stricter format" cannot be enforced by changing a writer function
   (none exists); it can only be enforced by (i) doc instruction change and/or (ii) a new CI/gate
   check that rejects a newly-appended row failing quote-consistency, mirroring how
   `done_checker_static.py` already checks for "exactly one working_log.csv row" at Finalize. Pure
   tolerant-parsing alone (option a only) leaves the corruption source open, as directly evidenced
   by the fact this is the *second* time in under a month the same failure mode reappeared after a
   full sweep.
2. **Rows 1511/3104 cannot be safely auto-repaired** (see Finding 1) — any parser must classify these
   two as irreducibly ambiguous, not attempt the same rejoin heuristic used for the other 9, or it
   risks silently reinterpreting corrupted quote-state as if it were clean data (a violation of the
   ticket's hard "never rewrite/reinterpret historical rows" constraint).
3. **Finding 2 (the ~1586-row duplication) is out of this ticket's literal Scope/AC** but is large
   enough that Plan should explicitly decide whether the new parser's "ambiguous/unparseable"
   classification also flags duplicate-content rows as a visible signal (distinct from, but
   presented alongside, field-count-mismatch rows), given how much it currently corrupts any
   naive rework-rate signal. This is a genuine open question, not assumed here either way.
4. **Field-count matching alone (the AC1 literal test) will not catch semantically-bogus-but-
   structurally-6-field rows** — the embedded duplicate-header row (line 1594) is proof this
   already happened once for real, and Finding 3's 34 lines (17 distinct corrupted rows) are a
   second, independently-confirmed proof of the exact same class. Recommend Plan consider whether
   AC1's "clean" classification needs the same plausibility layer (timestamp/ticket_id shape regex,
   **plus** the parenthesis-balance check on `artifacts_path` that Finding 3 confirms catches all
   34 with zero false positives against the file's 1378 distinct `artifacts_path` values)
   `TCK-20260819` proved necessary, or whether that is explicitly left as a known residual gap for
   this ticket (as it was for `TCK-20260819`'s own 17 blank-`artifacts_path` residual rows).
5. **`strict=True` re-parsing is not a sufficient general detection signal on its own** — Finding 3
   directly demonstrates this: `strict=True` correctly raises for Finding 1's 1511/3104 (severe
   quote-desync, stray quote not immediately followed by the delimiter) but does **not** raise for
   any of Finding 3's 34 lines (quote-desync where the stray quote happens to be immediately
   followed by the delimiter — legal CSV, wrong content). If Plan's tolerant-parser design uses
   `strict=True` as its sole "beyond field-count" signal, it will silently misclassify all 34 of
   Finding 3's rows as clean. The parenthesis-balance check on the last field (or the equivalent
   summary-ending regex) must be added as a second, independent signal alongside both the
   field-count check and any `strict=True` check.
6. **Finding 3's 17 distinct corrupted rows are, this investigation assesses, safely reconstructable
   with higher confidence than Finding 1's 9/11 rejoin-heuristic rows** (each has an independently-
   confirmed byte-identical clean sibling elsewhere in the file using the same fixed vocabulary —
   see Finding 3's Recovery section) — but Scope's "never rewrite historical rows in place" still
   applies regardless of reconstruction confidence; this only affects classification tier
   (reconstructable-but-flagged vs. irreducibly-ambiguous-and-flagged), not whether the file itself
   may be edited.

## Anti-Drift Hazards

- **Do not touch/reformat any of the 11 existing malformed rows or the ~1586 duplicate rows in
  place** — Scope and this investigation both require flag-only for historical content; any
  in-place rewrite (even a "safe-looking" rejoin) violates the ticket's hard constraint and this
  project's append-only precedent for this file (see both prior tickets' identical anti-drift
  notes).
- **Do not silently drop the 2 irreducibly-ambiguous rows (1511/3104)** from parser output — they
  must appear in the ambiguous/unparseable set, not be excluded as "unparseable, so omit."
- **Do not conflate Finding 2's duplicate-block discovery with this ticket's Scope** — flag it in
  Plan/Implementation Notes as a genuine, real, larger-than-described related issue, but do not
  silently fold a dedup/cleanup pass into this ticket without an explicit Plan decision (this
  mirrors the ticket's own Out-of-Scope treatment of the smaller "2-3 duplicate rows" it already
  named).
- **Do not touch `tools/validate_working_log.py`'s duplicate-ticket-ID or missing-log-entry checks**
  — those are unrelated to the field-count-mismatch parsing problem this ticket scopes; conflating
  them repeats the exact scope-creep risk `TCK-20260819` explicitly declined ("any change to
  validate_working_log.py itself... out of scope" was that ticket's own boundary, though this
  ticket's Scope *does* explicitly permit updating validate_working_log.py's row-extraction/
  reporting — keep that permission narrowly to the ambiguous-row-count signal, not the unrelated
  duplicate-ID/missing-entry checks already in the file).
- **Do not assume `csv.DictReader`'s `restkey`/`restval` behavior is "safe" tolerance** — it is
  silent data loss (extra fields vanish into an unread `None` key; missing fields become `None`
  with no signal), which is exactly the "silently mis-mapping columns" failure this ticket exists to
  close. A correct tolerant parser must detect the field-count mismatch itself, not rely on
  `DictReader`'s default leniency.
- **Do not rely on field-count == 6 as sufficient evidence a row is clean** — Finding 3's 34 lines
  (17 distinct rows) are structurally 6-field and would pass a naive field-count check while
  containing wrong content; a plausibility layer (parenthesis-balance on `artifacts_path`, or
  equivalent) is required alongside the field-count check, not as an optional enhancement.
- **Do not touch/reformat any of Finding 3's 17 corrupted rows (34 lines, including duplicates) in
  place**, and do not silently "fix" them even though a high-confidence single-candidate
  reconstruction exists (see Finding 3) — the same append-only, flag-don't-rewrite constraint that
  applies to Finding 1's 11 rows applies here regardless of reconstruction confidence.
- **Do not assume `strict=True` re-parsing is a complete "beyond field-count" signal** — Finding 3
  shows it misses an entire real 34-line corruption class that a parenthesis-balance/plausibility
  check does catch; a parser that only adds `strict=True` on top of field-count and calls the
  quote-desync problem solved has a confirmed, real blind spot.
