---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-RETRO-INDEX-REPORTS-ZERO
phase: done
date: 2026-09-15
tags: [agent-monitoring, data-quality, reporting]
---

# TCK-20260915-RETRO-INDEX-REPORTS-ZERO

## Title
`agent-monitoring/retro/index.md` shows 0 runs for every period report — including ones containing 69, 249 and 300 runs — because rows are keyed by ISO week and never read the reports they link to

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
The retro index is the first file a reader opens, and it contradicts the documents it links to:

| Row | Index claims | The linked report says |
|---|---|---|
| `LAST7D` | 0 runs, 0 DONE | **69 runs** |
| `LAST14D` | 0 runs, 0 DONE | **249 runs, 233 DONE** |
| `LAST28D` | 0 runs, 0 DONE | **300 runs** |
| `ALL` | 1609 runs, 1383 DONE | **1149 runs, 962 DONE (83%)** |

Cause is `tools/agent-monitoring/generate_retro.py::_update_index` (:1885-1925). Every row is
computed from the live corpus at generation time and never parses the report it links to:

```python
week_runs = all_runs if name == "ALL" else runs_by_week.get(name, [])
```

- `runs_by_week` is keyed by **ISO week string**. `"LAST7D"`/`"LAST14D"`/`"LAST28D"` are not ISO
  weeks, so the lookup misses and the row renders as zeros. There is an explicit special case for
  `"ALL"` and none for any other non-week scope, so **every `--days N` report indexes as 0**.
- The `ALL` row uses the unfiltered `all_runs` (1609) while `RETRO-ALL.md`'s own body reports 1149
  after `main()`'s filtering — same label, two populations.

`RETRO-LAST7D.md` and `RETRO-LAST28D.md` have been **tracked in git since 2026-09-06**, so the index
has been reporting "nothing here" over reports containing real work for nine days. Because it never
parses the reports, it cannot notice the disagreement.

## Scope
- Make each index row reflect the report it links to. Either parse the report's own Run Summary, or
  have `main()` hand `_update_index` the per-report figures it already computed.
- Fix the `ALL` row's population mismatch so it matches `RETRO-ALL.md`'s body.

## Out of Scope
- Redesigning the index's columns or the retro report format.
- The weekly (`RETRO-2026-Wnn`) rows, which appear correct — verify before changing them.

## Acceptance Criteria
- [x] Every index row matches the Run Summary of the report it links to, verified for at least one
      week report and all four non-week reports — with one honest, documented exception (see
      Assumptions / Open Questions below): `RETRO-2026-W38.md` (21/19/2), `RETRO-ALL.md`
      (1532/1385/99), `RETRO-LAST7D.md` (107/98/9), and `RETRO-LAST28D.md` (455/427/24) were all
      regenerated live and diffed against the freshly-rebuilt index — exact match on every field for
      all four. `RETRO-LAST14D.md` could **not** be safely regenerated to close this loop the same
      way (see below) — its index row is now correctly non-zero and uses the identical
      population-resolution logic proven correct on the other three `LAST{N}D`-shaped reports, but
      it necessarily reads a few runs newer than what that specific file's frozen content shows.
- [x] A test pins this — `tests/tools/test_generate_retro.py` adds 4 new tests against
      `_update_index`/`_resolve_report_run_population` directly, comparing synthetic input against
      the index's own rendered output rather than checking the index in isolation.
- [x] Regenerating the index does not change numbers in unrelated rows — verified: weekly rows
      (`2026-W27` through `2026-W36`) are unchanged by this fix (their ISO-week lookup was already
      correct); only the `LAST7D`/`LAST14D`/`LAST28D`/`ALL` rows changed, and only in the direction
      of correcting a 0.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)

## Related Docs
- `agent-monitoring/retro/index.md`
- `agent-monitoring/retro/RETRO-LAST14D.md` (its addendum documents this finding)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py` (`_update_index`, :1885-1925; called at :1882)

## Assumptions / Open Questions
- Whether non-week reports were ever intended to appear in the index at all is worth confirming —
  "exclude them" is a legitimate alternative fix to "compute them correctly", though it loses
  visibility for exactly the reports a fortnightly review uses. Resolved in favor of computing them
  correctly: they are exactly the reports a fortnightly review reads first, per this ticket's own
  framing.
- **`RETRO-LAST14D.md` cannot currently be safely regenerated to prove a bit-for-bit match**, and
  this is accepted and documented rather than forced. That file carries 223 lines of hand-authored
  content in its `## Notes` section (a peer's "Deep review" analysis plus this epic's own
  `TCK-20260915-DUPLICATE-RUN-RECORDS` addendum) — running the CLI (`generate_retro.py --days 14`)
  on it would call `out_path.write_text(report)` unconditionally and destroy that content, exactly
  the hazard `TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES` (ticket 9 of this epic, not yet
  implemented) exists to fix. Per this repo's Gate Integrity rule, the correct response to "the
  verification I want would require an unsafe action" is to not take the unsafe action and document
  the gap honestly, not to force it. The other three `LAST{N}D`-shaped reports (`LAST7D`, `LAST28D`,
  and a synthetic multi-window test) prove the population-resolution logic itself is correct;
  `LAST14D`'s index row uses the identical code path, so the fix is not in doubt — only a live,
  exact-to-the-file verification of that one specific row is deferred until ticket 9 makes
  regenerating it safe. Confirmed via `git diff --stat -- agent-monitoring/retro/RETRO-LAST14D.md`
  showing no changes at any point during this ticket's work.

## Implementation Notes
Root cause exactly as scoped: `_update_index`'s `week_runs = all_runs if name == "ALL" else
runs_by_week.get(name, [])` only recognized `"ALL"` as a non-ISO-week special case; `runs_by_week`
is keyed by ISO week string, so `"LAST7D"`/`"LAST14D"`/`"LAST28D"` always missed and rendered as
zeros. The `"ALL"` branch also used the raw, non-deduplicated `all_runs` while `RETRO-ALL.md`'s own
body (since `TCK-20260915-DUPLICATE-RUN-RECORDS`) reports the deduplicated count — same label, two
populations.

Fix: added `_resolve_report_run_population(name, all_runs, runs_by_week)`, mirroring `main()`'s own
three branches exactly — `"ALL"` uses the full corpus, a name matching `^LAST(\d+)D$` recomputes the
same `datetime.now(timezone.utc) - timedelta(days=N)` cutoff `main()` uses via the same
`_record_since_cutoff()`, and anything else is treated as an ISO week label via the existing
`runs_by_week` lookup (unrecognized names correctly fall through to an empty population, not a
crash or a false match-everything). `dedupe_to_latest_per_execution()` — the same function `main()`
already calls unconditionally — is applied uniformly to all three branches' output, fixing the
`"ALL"` row's population mismatch and (harmlessly, since duplicates are rare) making the weekly rows
exactly correct too, not just "appear correct" as the ticket's own Out of Scope note put it.

Verified by regenerating `RETRO-ALL.md`, `RETRO-LAST7D.md`, `RETRO-LAST28D.md`, and the current-week
`RETRO-2026-W38.md` via the real CLI (each file's own `## Notes` section holds only unfilled
boilerplate, confirmed before regenerating, so no hand-authored content was at risk), then
rebuilding the index and diffing each row's `Runs`/`DONE`/`Gate failures` numbers against that same
report's own persisted `## Run Summary` table — exact match on all four. `RETRO-LAST14D.md` was
deliberately left untouched (see Assumptions above); its row is now correctly non-zero via the same
proven-correct code path, with a documented, known small drift versus that specific file's frozen
content until ticket 9 makes safe regeneration possible.

Search Calls / Read Calls / Skill Invocations columns (not literally part of the "Run Summary"
table the ticket's acceptance criteria name, but computed from the same `week_runs`/`week_run_ids`
variable) are fixed by the same change, since they were equally broken (always 0) for the same
non-ISO-week names before this fix.

## Test Summary
- New: 4 tests in `tests/tools/test_generate_retro.py` — `_update_index` correctly resolves
  `LAST7D`/`LAST14D`/`LAST28D` names to time-windowed populations (not 0), independently correct
  across multiple window sizes in one corpus, the `ALL` row uses the deduplicated execution count
  (not the raw row count) matching `RETRO-ALL.md`'s own body, and an unrecognized report name
  resolves to an empty population rather than raising or matching everything.
- Full `tests/tools/test_generate_retro.py` suite re-run: 160 passed (no regressions).
- Real-corpus regeneration + diff (see Implementation Notes): `RETRO-ALL.md` (1532/1385/99),
  `RETRO-LAST7D.md` (107/98/9), `RETRO-LAST28D.md` (455/427/24), `RETRO-2026-W38.md` (21/19/2) —
  every index row matched its linked report's own `## Run Summary` table exactly. Confirmed no
  unrelated weekly row (`2026-W27` through `2026-W36`) changed.

## Files Changed
- `tools/agent-monitoring/generate_retro.py` — added `_resolve_report_run_population()`; rewired
  `_update_index` to use it in place of the old `"ALL"`-only special case.
- `tests/tools/test_generate_retro.py` — 4 new tests (synthetic-fixture based, not dependent on
  real corpus state or wall-clock precision beyond day-level margins).
- `agent-monitoring/retro/RETRO-ALL.md`, `RETRO-LAST7D.md`, `RETRO-LAST28D.md`, `RETRO-2026-W38.md`,
  `index.md` — regenerated with corrected, current data (each safe to regenerate: only boilerplate
  `## Notes` content, confirmed before running). `RETRO-LAST14D.md` intentionally NOT touched.

## Completion Summary
Fixed `_update_index`'s population lookup so every index row (`ALL`, `LAST7D`/`LAST14D`/`LAST28D`,
and ISO-week reports) reflects the actual population its linked report was built from, replacing a
lookup that only special-cased `"ALL"` and otherwise silently missed for any non-ISO-week name.
Also fixed the `ALL` row's population to match `RETRO-ALL.md`'s own deduplicated body count.
Verified by live regeneration and exact-match diffing for `ALL`/`LAST7D`/`LAST28D`/current-week;
`LAST14D` is verified via the same proven-correct code path but not via a live regenerate-and-diff,
since doing so today would require the still-unimplemented `TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES`
fix to do safely — recorded explicitly rather than forced or silently skipped.
