---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT
artifact_type: investigation
tags: [process-improvement]
---

# Investigation — TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT

Verified against `origin/main` on 2026-09-11 by parsing every `tickets/done/**/*.md` frontmatter block.
`search_docs` has no index in this worktree; duplicate-work detection used the `docs/REGISTRY.yaml` fallback.

## 1. The count, and a second class the ticket missed

| | Count |
|---|---|
| Done tickets parsed | 1917 |
| Canonical `status: historical` / `phase: done` | 1522 |
| **Non-canonical** | **395** |

The ticket's 227 counted only `active`/`open`. That class has grown to 235, and it is one of several:

| status / phase | Count | Class |
|---|---|---|
| `active` / `open` | 235 | valid, location-inconsistent |
| `done` / `done` | 83 | **schema-invalid** |
| `done` / `open` | 27 | **schema-invalid** |
| `active` / `done` | 17 | valid, location-inconsistent |
| `open` / `open` | 13 | **schema-invalid** |
| `done` / `epic_scoped` | 9 | **schema-invalid** — see §5 |
| `active` / `inprogress` | 4 | valid, location-inconsistent |

`tools/validate_frontmatter.py:44` defines `STATUS_VALUES = {authoritative, active, historical, archive}`.
`done` and `open` are not in it. `PHASE_VALUES` (line 56) lacks `epic_scoped`. So roughly 138 files carry
values the existing validator would reject outright.

**This changes the ticket's framing.** It describes the gap as a missing cross-field rule, with each field
individually valid. That is true of about 256 files. The other ~138 violate the existing single-field enum —
which can only happen if the validator is not run on them.

## 2. The validator does not run on this directory

`validate_frontmatter.py` is not invoked by any CI workflow, the Makefile, or pre-commit. Its only
enforcement call site is `tools/gate_checks/done_checker_static.py::check_frontmatter_valid()` (line 683),
which validates **the single ticket being closed**, and only when `done_checker` runs.

## 3. Onset

| Month | Canonical | Non-canonical | % |
|---|---|---|---|
| 2026-03 | 19 | 0 | 0.0 |
| 2026-04 | 246 | 0 | 0.0 |
| 2026-05 | 245 | 0 | 0.0 |
| 2026-06 | 254 | 163 | **39.1** |
| 2026-07 | 241 | 42 | 14.8 |
| 2026-08 | 337 | 168 | 33.3 |
| 2026-09 | 144 | 21 | 12.7 |

Zero drift across 756 tickets before June, then sustained drift since. `TCK-20260606-DOCSITE-FM-TICKETS`
introduced ticket frontmatter on 2026-06-06, using an older schema (`status: DONE`, numeric `phase`).
Hypothesis, consistent with the data but not proven: pre-June tickets were normalized by a later bulk pass,
while every ticket since has been *born* `active`/`open` from the CLAUDE.md template and depends on its close
step to flip it. The `status: done` values plausibly originate in that older `DONE` schema.

## 4. Closure path is the strongest signal

Post-June done tickets, classified from `agent-monitoring` events: *pipeline* = has an event from a real
pipeline agent (`investigator`, `implementer`, `done-checker`, ...); *hand* = events from `claude` only;
*no record* = no monitoring events at all.

| Path | Canonical | valid-but-inconsistent | schema-invalid | Drift % |
|---|---|---|---|---|
| Pipeline | 668 | 116 | **13** | 16.2 |
| Hand-orchestrated | 196 | 95 | 41 | 41.0 |
| No record | 112 | 45 | 84 | **53.5** |

This separates three causes:

1. **No cross-field rule.** The pipeline catches almost every *invalid* value (13 slipped), because
   `done_checker` runs the enum check. It misses 116 *valid-but-inconsistent* values, because nothing
   relates a ticket's location to its status/phase. Affects every path.
2. **The check is not reached.** 125 of the 138 schema-invalid files come from hand-orchestrated or
   unrecorded closes, which never run `done_checker`.
3. **Nothing instructs the canonical value.** The string `historical` appears nowhere in
   `.claude/workflows/implement-ticket.js`. The pipeline gets it right 84% of the time by imitating existing
   tickets, not because any step says to.

**The ticket's proposed fix — a new condition in `done_checker` — is necessary but insufficient.** It fixes
cause 1 for pipeline closes and does nothing for cause 2, where the drift is worst.

## 5. Intentional-mismatch sample

The ticket asks that files be sampled for deliberate mismatches before any bulk fix. One real case exists:
**all 9 `phase: epic_scoped` tickets are epic-tier**, from one 2026-06-19 batch (E13, E21, E31, E32, E33, E41,
E42, E43, E53A). Two have body `## Status: EPIC_SCOPED`, seven `DONE`. CLAUDE.md lists `EPIC_SCOPED` as a
valid body status for epics. The frontmatter phase was used deliberately, not randomly. These need a
recorded decision rather than a silent rewrite. Their `status: done` is invalid either way.

## 6. Self-check

This session closed `TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP` by hand-orchestration. It
sits in `tickets/done/` at `active`/`open` — a live instance of cause 2 and 3, produced while this
investigation's author was working in this exact area.

## 7. Prior art

`TCK-20260804-BACKLOG-PHASE-VALIDATOR-FIX` added `backlog` to `PHASE_VALUES` after a legitimate value was
found missing — the precedent for deciding whether `epic_scoped` belongs in the enum.
