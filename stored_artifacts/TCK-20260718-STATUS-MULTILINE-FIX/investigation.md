---
artifact_type: investigation
ticket_id: TCK-20260718-STATUS-MULTILINE-FIX
date: 2026-07-18
---

# Investigation — TCK-20260718-STATUS-MULTILINE-FIX

## Current Behavior

The Agent Ops Dashboard's Tickets-view Status filter (`src/api/agent_ops_dashboard/ingest.py`'s
`workflow_status` field) is populated via `tools/generate_registry.py::parse_body_section(body,
"Status")`, which captures the entire text of a ticket's `## Status` section up to the next `## `
heading or end-of-file — not just the first line.

Two predecessor tickets today (TCK-20260718-STATUS-DRIFT-REPAIR, TCK-20260718-STATUS-SUFFIX-TRIM)
used a simpler first-token-only regex (`^## Status\s*\n+\s*(\S+)`) to find and fix drift. That
regex under-detects relative to the real parser: it only ever looks at the first whitespace-
delimited token after the heading, so any file where real dashboard-visible garbage exists *past*
that first token was invisible to it.

Using the real `parse_body_section` function directly (matching exactly what `ingest.py` sees),
three further classes of live dashboard fragmentation were found:

## Class A — stray leftover INPROGRESS line (3 files)

`tickets/done/TCK-20260504-CORE-TEST-STABILIZATION.md`,
`tickets/done/TCK-20260506-TOWN-TEST-STABILIZATION.md`,
`tickets/done/TCK-20260507-TEST-BASE-REWORK.md` all read:

```
## Status
DONE
INPROGRESS

## Tier
```

All three have the full standard 12-section format. The first-token regex saw only `DONE` (correct
by luck) and missed the trailing `INPROGRESS` line entirely; the real dashboard parser returns
`"DONE\nINPROGRESS"` as one garbled value — a distinct, wrong filter-dropdown entry.

**Fix**: delete the stray `INPROGRESS` line. Mechanical, no other content touched. Verified no
other text was on that line before deleting (read each file directly).

## Class B — DONE bleeding into trailing bold-metadata block (11 files)

`TCK-20260325-FINAL_E2E_SMOKE`, `TCK-20260327-WINDBIGMOD-CLEANUP`,
`TCK-20260330-AOA-COMPOSITION-COMPLETED`, `TCK-20260330-CORE-STABILIZATION`,
`TCK-20260331-RUNTIME-INTEGRITY`, `TCK-20260404-STABILIZATION`, `TCK-20260405-CONVERGENCE`,
`TCK-20260405-DOCS`, `TCK-20260405-LOGFIX`, `TCK-20260405-PROD-STACK-STABILIZE`,
`TCK-20260406-RPG-CORE-STABILIZE` — all 11 are a genuinely older ticket format (section order:
Description → Scope → Acceptance Criteria → Related Tickets → Status → Summary of Changes → Status
again(!) with metadata) — actually confirmed order is: `## Description`, `## Scope`,
`## Acceptance Criteria`, `## Summary of Changes`, `## Status`, with `## Status` as the LAST
heading in the file. No separate `## Tier`/`## Type`/`## Priority` headings exist; that metadata
is written as inline bold text directly under `## Status`:

```
## Status
DONE

**Tier:** standard
**Type:** chore
**Priority:** P1
```

All 11 files have byte-identical trailing text (verified via direct read of every file before
transforming — same `standard`/`chore`/`P1` values, apparently batch-created from one template).
Because there is no next `## ` heading, `parse_body_section` captures `DONE` plus the entire
trailing bold block as one value.

**Decision — approach (a), minimal-invasive conversion, chosen over leaving as legacy**:
converted each file's `**Tier:** standard` / `**Type:** chore` / `**Priority:** P1` lines into real
`## Tier` / `## Type` / `## Priority` headings. Rejected leaving these as untouched legacy (option
b) because: (1) this directly fixes the actual parsing bug — a missing heading boundary — rather
than working around a symptom; (2) the transform is low-risk and mechanical since all 11 files
share byte-identical trailing text, verified before transforming; (3) unlike the `resource_v2_*.md`
precedent (pre-TCK-naming files, a genuinely different naming scheme this project has established
as categorically out of scope), these are TCK-named files using the current standard section
vocabulary (`## Tier`, `## Type`, `## Priority` are the SAME field names the modern format uses,
just expressed as bold text instead of headings) — converting them is a narrow syntactic fix, not
a structural reformat. Every other section (`## Description`, `## Scope`, `## Acceptance Criteria`,
`## Summary of Changes`) was left completely untouched — no attempt was made to remap `Description`
to `Request Summary` or add missing sections like `## Title`/`## Completion Summary`, since that
broader modernization was explicitly out of scope.

**Side effect discovered and fixed**: `tools/generate_registry.py::collect_tickets()` (used to
build `docs/REGISTRY.yaml`) also reads `Tier`/`Type` via `parse_body_section` — before this fix,
all 11 files' `tier`/`ticket_type` registry fields were unparseable (empty), since there was no
real `## Tier`/`## Type` heading. Confirmed via `tests/tools/test_generate_registry.py`'s drift
test failing after the ticket-body fix (correctly detecting the registry was now out of sync) —
regenerated `docs/REGISTRY.yaml` via `python3 tools/generate_registry.py --output
docs/REGISTRY.yaml`; all 11 files now correctly show `tier: standard`, `ticket_type: chore` in the
registry.

## Class C — inconsistent epic-terminal-state wording, escalated to a real status bug (1 file)

`tickets/done/TCK-20260628-E-RESOURCE-ECOLOGY.md` read `## Status\nSCOPED (epic — awaiting child
tickets)` while 6 sibling epic tickets all read the bare `EPIC_SCOPED` token for the same concept.
The original framing assumed this was purely a wording inconsistency requiring normalization to
`EPIC_SCOPED` to match the other 6.

**Deviation from the literal request, with justification**: reading the full file revealed this is
NOT the same case as the other 6. Its own `## Completion Summary` section explicitly states "Epic
DONE 2026-06-28" and lists all 3 child tickets (E21C/E21D/E21E) as complete, with parity ledger
entries (TOWN-186, TOWN-187, WORLD-104) cited. The other 6 `EPIC_SCOPED` tickets have no completed
children — they are genuinely still at the scoped-only stage. This ticket's frontmatter also showed
`phase: scoped` while `status: historical` — every other `status: historical` ticket sampled in the
corpus pairs with `phase: done`, confirming `phase: scoped` was itself stale.

**Fix applied**: normalized `## Status` to bare `DONE` (not `EPIC_SCOPED` as originally
instructed) and corrected frontmatter `phase: scoped` → `phase: done`, since the ticket's own body
proves it is fully complete, not merely scoped. The stale `**Status: BLOCKED pending 5,000-tick D06
validation run.**` sentence embedded in the `## Request Summary` prose (not a structured heading
the dashboard parses) was left untouched — out of scope for this ticket, which is specifically
about the `## Status` heading value the dashboard actually reads, not general prose staleness
elsewhere in ticket bodies. Noted here for visibility only.

## Checker Extension Decision

`tools/gate_checks/status_drift_check.py` (from TCK-20260718-STATUS-DRIFT-REPAIR) used a
first-token-only regex that would NOT have caught any of Class A, B, or C:
- Class A: regex captures only `DONE` (first token), silently missing the trailing `INPROGRESS`.
- Class B: regex captures only `DONE`, silently missing the trailing bold-text block.
- Class C: regex captures only `SCOPED` (stops at the space before `(epic`), which IS in the
  checker's own `EPIC_TIER_VALUES` exemption set — so the checker actively, silently treated this
  as a legitimate non-drift value.

Given this is the **second consecutive ticket** to discover real dashboard-visible drift the
checker's regex-based approach missed, the decision this time (unlike STATUS-SUFFIX-TRIM's
deferral) is to **fix the checker's extraction to call `parse_body_section` directly** rather than
maintaining a parallel, simpler, and now twice-proven-insufficient regex. This eliminates the
"checker says clean, dashboard shows garbage" gap by construction — any future drift shape that the
real dashboard parser would show as fragmented will now also be caught by the checker, without
needing a fifth bespoke regex pattern for a fifth discovered shape.

This is judged a well-scoped, low-risk fix: `parse_body_section` is a small (~10-line), already
widely-used, already-tested function; the checker's own exemption logic (`EPIC_TIER_VALUES`
value-set check, `TCK-` filename-prefix check, empty-string skip for colon-format tickets) is
otherwise unchanged and still correct — verified the colon-format skip behavior is identical
between the old regex and the real `parse_body_section` (both require a newline directly after the
heading, so same-line `## Status: X` still resolves to `""` under both).

## Constraints

No Mechanics Bible or Engine Contract chapter applies — pure ticket-corpus data hygiene plus one
dashboard-tooling regression-check module, outside the simulation domain entirely.

## Prior Work

- TCK-20260718-STATUS-DRIFT-REPAIR (tickets/done/) — first drift-repair pass, 71 tickets + 7
  runs.jsonl records, introduced `status_drift_check.py`.
- TCK-20260718-STATUS-SUFFIX-TRIM (tickets/done/) — second pass, 10 files with `DONE (...)`
  parenthetical suffixes on the first line.

## Risks and Open Questions

- The 78 tickets found (during a prior, separate investigation this session) to resolve to an
  empty `workflow_status` via `parse_body_section` were NOT re-audited here — that is a distinct,
  broader question (some are genuinely colon-format per the known limitation, others may have no
  `## Status` heading at all for other reasons) explicitly out of scope for this ticket. Flagged as
  a candidate for a future, separately-scoped investigation.
- The same-line colon-suffixed `## Status: X` exclusion (12 files, 6 non-`DONE`) remains
  unaddressed, per TCK-20260718-STATUS-DRIFT-REPAIR's original scope decision — not revisited here.

## Anti-Drift Hazards

- The Class B bold-text-to-heading transform must never be applied to a file where the trailing
  block isn't byte-identical to the verified template — a blanket regex across files with differing
  trailing content could silently corrupt unrelated text. Verified via an `assert text.endswith(...)`
  guard per file before transforming (all 11 passed).
- `docs/REGISTRY.yaml` must be regenerated after any ticket-body change that alters a
  `parse_body_section`-derived field (Status, Tier, Type, Priority, Title) — confirmed via the
  existing drift test in `test_generate_registry.py`, which is exactly the safeguard that caught
  this ticket's Class B side effect before it could go unnoticed.
