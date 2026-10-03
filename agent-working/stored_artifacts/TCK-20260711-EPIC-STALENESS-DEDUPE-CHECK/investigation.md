---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK
artifact_type: investigation
tags: [ai, agent-monitoring, process-improvement]
---

# Investigation — TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK

## Current Behavior

**`tools/agent-monitoring/epic_staleness_check.py::discover_candidate_epics()`** — current live
file, lines 119-188 (the ticket's scope text cites "lines 119-163"; that range is stale/approximate
— the function has grown to 188 lines since TCK-20260710-EPIC-STALENESS-CHECK landed, unrelated to
this ticket, just line drift from normal file evolution). Confirmed via direct read, not the ticket
text.

- Line 120: `candidates = []` — a single flat list, shared across both discovery modes.
- Lines 122-139 (**epic_id mode**): iterates `sorted(inprogress_dir.glob("*.md"))`, keeps only files
  whose `## Tier` section body is `epic` (line 128), reads `ticket_id` from frontmatter (line 130),
  and appends an `EpicCandidate(mode="epic_id", ...)`.
- Lines 141-186 (**folder mode**): iterates `sorted(p for p in todos_dir.iterdir() if p.is_dir())`,
  looks for `SEQUENCE.md` and/or an epic-tier `TCK-*.md` file directly inside the subdir (one level,
  not recursive — `subdir.glob("TCK-*.md")`, not `rglob`), derives `epic_id` from the epic ticket's
  frontmatter if one exists, else synthesizes `FOLDER-tickets-todos-{subdir.name}`, and appends an
  `EpicCandidate(mode="folder", ...)`.
- Line 188: `return candidates` — **no dedupe pass across the two loops.** `_dedupe_preserve_order()`
  (line 59) exists and is used in two places: inside `_child_ids_from_text()` (line 112, dedupes
  child-ID substring matches *within one ticket's text*) and inline in the folder-mode
  sibling-files fallback (line 176, dedupes sibling `TCK-*.md` stems within one folder). **It is
  never applied to the top-level `candidates` list itself.** If the same `epic_id` is discoverable
  both as a file directly in `tickets/inprogress/` (epic_id mode) and as an epic-tier file inside a
  `tickets/todos/{folder}/` subdir (folder mode), `discover_candidate_epics()` returns **two**
  `EpicCandidate` objects for that one epic — same `epic_id`, different `mode`/`source_path`.

**Downstream consumption — confirmed this actually surfaces as visible duplication, not just an
internal artifact:**
- `_classify_candidates()` (lines 290-303) calls `discover_candidate_epics()` once and loops
  `for candidate in candidates:` with no dedupe-by-`epic_id` step. Each of the two duplicate
  candidates is independently run through `resolve_child_activity()` / `is_epic_stale()` /
  `is_epic_never_started()`.
- `find_stale_epics()` (lines 306-322) returns `[candidate for candidate, _ in stale]` — a flat
  list that **can contain two `EpicCandidate` entries with the same `epic_id`** if both duplicate
  candidates independently classify as stale (they will, since they share identical `child_ids`
  resolution behavior modulo `mode`).
- `compute_stale_epics_report()` (lines 329-365) and the `--hook` branch (lines 379-415) both
  render every entry in `stale`/`never_started` via `_format_epic_line()` (line 325:
  `f"{candidate.epic_id} ({candidate.source_path})"`) — so a duplicated epic renders as **two
  separate lines** in the report (distinguishable only by differing `source_path`, e.g.
  `tickets/inprogress/TCK-...md` vs `tickets/todos/some-folder`) and inflates `len(stale)` in the
  hook's nudge message (`"{len(stale)} open epic(s) have gone idle..."`). This is real, observable
  double-discovery/double-nudging, not a theoretical concern.

**Return type**: `discover_candidate_epics()` returns `list[EpicCandidate]` (line 119 type hint says
plain `list`, but in practice always `EpicCandidate` instances) — a flat, unordered-by-key list, no
dict/set keying by `epic_id` anywhere in the discovery path.

## Mechanics / Engine Constraints

None apply. This is pure Claude-agent-orchestration tooling (`layer: ai`), not a gameplay mechanic —
consistent with TCK-20260710-EPIC-STALENESS-CHECK's own finding ("No parity ledger entries apply
... pure agent-tooling, not a tracked simulation subsystem"). No `docs/mechanics/` or `docs/engine/`
chapter constrains this work.

## Parity Ledger Overlap

None. Searched `docs/parity_ledger/*.yaml` for any entry referencing `epic_staleness_check`,
`EPIC-STALENESS`, or `EPIC-SCOPE-ORPHAN`; the only hit is **INFRA-265** in
`docs/parity_ledger/infrastructure.yaml` (lines 3765-3801+), which covers the *sibling* ticket
(TCK-20260711-EPIC-SCOPE-ORPHAN-FIX)'s `resolveScopeTicketLocation()` / `scope_ticket_relocate.py` /
`epic_scope_orphan_check.py` orchestrator-determinism change — a distinct file/mechanism from this
ticket's target (`discover_candidate_epics()`'s internal dedupe). No parity ledger entry exists for
`epic_staleness_check.py` itself, matching the precedent set when that file was first built
(TCK-20260710-EPIC-STALENESS-CHECK's Completion Summary explicitly states no parity entry applies).
This ticket should follow that same precedent: **no new parity ledger entry expected**, since it is
an internal-logic hardening of an already-parity-exempt pure-tooling module, not an
orchestrator-determinism change in the INFRA-183/INFRA-263/INFRA-265 lineage. Flag this as a
confirmation point for the Parity phase rather than assuming it silently — if the Parity phase
disagrees (e.g. because it touches the same file family as INFRA-265), an entry should be added
there, not skipped.

## Prior Work

- **TCK-20260710-EPIC-STALENESS-CHECK** (`tickets/done/`, `stored_artifacts/TCK-20260710-EPIC-STALENESS-CHECK/`)
  — built `epic_staleness_check.py` and its 11-test suite (originally 9 ACs-worth + 2 defensive
  additions). Established the `_write_ticket(path, ticket_id, tier, date_str, related_tickets="")`
  fixture helper (test file line 42) that every synthetic test in the suite reuses. New dual-presence
  test(s) for this ticket should reuse this exact helper for both the `tickets/inprogress/` epic-tier
  file and the `tickets/todos/{folder}/` epic-tier file (same `ticket_id` in both calls).
- **TCK-20260711-EPIC-SCOPE-ORPHAN-FIX** (`tickets/done/`, no stored_artifacts subfolder listed in
  its own Related Stored Artifacts — check the ticket file directly) — the sibling/root-cause fix,
  closed in this same session. Confirmed via its own ticket file (Scope section) that it explicitly
  carved this ticket's exact scope **out** of its own Out of Scope: "Adding dedupe logic to
  `tools/agent-monitoring/epic_staleness_check.py`'s `discover_candidate_epics()` double-discovery
  across its epic_id-mode and folder-mode scan loops -- tracked separately in
  TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK." This is a clean, intentional split, not overlapping
  scope.
- Introduced two new sibling modules in the same session, both reusable references:
  - `tools/agent-monitoring/scope_ticket_relocate.py::resolve_and_relocate_ticket()` — the
    prevention fix (move-not-copy for epic tier at Scope time).
  - `tools/agent-monitoring/epic_scope_orphan_check.py::scan_epic_scope_orphans()` /
    `check_single_epic_orphan()` — a **standalone, unwired** sweep that already detects the exact
    dual-presence signature (epic-tier ticket in both `tickets/inprogress/` and
    `tickets/todos/**`), but only as a pass/fail static check over `tickets/inprogress/*.md`, one
    entry per file — it does not touch or call `discover_candidate_epics()` at all, and has its own
    separate test file (`tests/tools/test_epic_scope_orphan_check.py`, 6 tests, `_write_ticket`
    helper reused there too with a simpler 3-arg signature: `(path, ticket_id, tier)`). This module
    is a good design-pattern reference (dedupe-by-existence-check against `todos_dir.rglob(...)`)
    but is not itself the fix target — this ticket's fix belongs inside
    `discover_candidate_epics()`, per the ticket's explicit AC wording ("epic_staleness_check.py's
    `discover_candidate_epics()`, given a fixture epic present in both ... is confirmed via a new
    test to dedupe").

## Risks and Open Questions

1. **Is this ticket still worth doing, now that the root cause is fixed? Yes — the gap is real,
   narrower than originally framed, but not dead code.** `resolve_and_relocate_ticket()`'s
   move-for-epic-tier path (lines 80-87 of `scope_ticket_relocate.py`) performs
   `shutil.copyfile(todos_path, inprogress_path)` (creates the inprogress copy) as a **separate
   statement** from `todos_path.unlink()` (deletes the todos original) a few lines later, guarded by
   `if tier == "epic":`. If the orchestrator process is interrupted (crash, kill, `implement-ticket.js`
   error) in the window between those two statements, both files exist simultaneously — a genuine,
   if narrow, transient window that the prevention fix does not close, because it is not atomic.
   This is a more concrete, more probable justification than the ticket's own listed hypotheticals
   (manual copies, post-hoc Tier-field edits) and should be called out to whoever reviews this
   ticket's continued value.
2. **Manual/human ticket copies remain fully unguarded.** Nothing in the repo prevents a person (or
   an agent under different instructions) from `cp`-ing a ticket file into both locations directly,
   bypassing `resolve_and_relocate_ticket()` entirely. `epic_staleness_check.py` is the
   *discovery*-side check and has no way to know how the dual-presence state arose — hardening it is
   the only lever available at this layer.
3. **`epic_scope_orphan_check.py` already exists and detects this exact signature — should this
   ticket instead call *that* rather than re-implement dedupe inside `discover_candidate_epics()`?**
   Open design question for the Plan phase, not decided here: the ticket's AC explicitly asks for
   dedupe *inside* `discover_candidate_epics()` (so `find_stale_epics()`/`compute_stale_epics_report()`
   never see the duplicate at all), whereas `epic_scope_orphan_check.py` is a separate advisory
   report about orphans specifically, unwired into any workflow phase, with a different output shape
   (`list[{"ticket_id","status","evidence"}]`, not `list[EpicCandidate]`). Reusing it as a filter
   inside `discover_candidate_epics()` is plausible (it already knows how to detect this exact
   shape) but would create a new cross-module dependency where none exists today, and its detection
   is by-file-existence-check (recomputes `todos_dir.rglob` per ticket_id) rather than an
   in-memory-dedupe over already-collected candidates — a possible plan option, but this is a design
   choice for the Plan phase, not something to assume here.
4. **Tie-break / which entry wins is undecided.** If dedupe is added as an in-memory pass over the
   already-built `candidates` list (the more natural fix, matching `_dedupe_preserve_order()`'s
   existing style), a decision is needed on which of the two duplicate `EpicCandidate` objects
   survives: since `epic_id`-mode (`tickets/inprogress/`) runs first (lines 122-139, before the
   folder-mode loop at 141-186), a straightforward "first occurrence wins" dedupe keyed by
   `epic_id` would naturally prefer the `tickets/inprogress/` entry — which also happens to be the
   documented single authoritative resting place for epic-tier tickets per
   `docs/ai/ticket-lytecycle.md:440` (per the sibling ticket's own Out of Scope note: "Redesigning
   `tickets/inprogress/` as a resting place for `epic_id`-mode epics -- that placement is correct").
   This is a reasonable default but is a Plan-phase decision, not assumed here — flagging so it is
   made explicitly rather than accidentally by insertion order.
5. **Line-range drift in the ticket text.** The ticket's Scope section cites
   "lines 119-163" for `discover_candidate_epics()`; the live function is actually lines 119-188.
   Not a blocker (the function identity and behavior are unambiguous), but the Plan phase should not
   anchor edits to the stale line numbers without re-reading the current file first.

## Anti-Drift Hazards

- **Do not touch `resolve_and_relocate_ticket()` or `.claude/workflows/implement-ticket.js`.** Those
  are TCK-20260711-EPIC-SCOPE-ORPHAN-FIX's territory (already closed); this ticket's Out of Scope
  explicitly excludes "Fixing the root-cause orphan-creation bug in implement-ticket.js's Scope
  phase" and "Any change to done_checker_static.py or a new orphan-detection static check." Do not
  extend or wire `epic_scope_orphan_check.py` into a workflow phase as a side effect of this work —
  that module is deliberately standalone/unwired per its own docstring and the sibling ticket's
  scope; wiring it in is a distinct, undecided future ticket.
- **Do not change the never-started/stale classification semantics** (`is_epic_stale()`,
  `is_epic_never_started()`, Decision 5's "no `epic_date` fallback" rule) while touching this file —
  those are settled, tested behavior from TCK-20260710-EPIC-STALENESS-CHECK and are out of scope
  here. The fix belongs entirely inside `discover_candidate_epics()` (or a helper it calls), not in
  the classification/reporting layers.
- **Do not silently change `EpicCandidate`'s field shape or `discover_candidate_epics()`'s return
  type** (still `list[EpicCandidate]`) — all 11 existing tests and both sibling test files
  (`test_scope_orphan_fix.py`, `test_epic_scope_orphan_check.py`) depend on this module's current
  public surface (`_section_body`, `EpicCandidate`, etc. are imported directly by
  `epic_scope_orphan_check.py` and `scope_ticket_relocate.py`). Any signature change to
  `discover_candidate_epics()` itself (e.g. adding new required params) would ripple beyond this
  ticket's stated scope.
- **Do not reduce the existing 11 tests' fixture isolation.** All existing synthetic tests use
  `tmp_path`-scoped `inprogress_dir`/`todos_dir` fixtures; the new dual-presence test must do the
  same (never touch the real `tickets/inprogress/`/`tickets/todos/` trees), consistent with
  `test_advisory_only_no_file_mutation`'s hash-before/hash-after guard elsewhere in the same file.
- **Do not conflate this fix with the live-repo one-time sweep.** TCK-20260711-EPIC-SCOPE-ORPHAN-FIX
  already confirmed the real repo has zero current orphans (`scan_epic_scope_orphans()` returns zero
  findings today). This ticket's new test must be a synthetic fixture, not a live-repo assertion —
  there is no real dual-presence case to point it at today.
