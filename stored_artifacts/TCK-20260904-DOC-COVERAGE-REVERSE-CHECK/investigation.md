---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-DOC-COVERAGE-REVERSE-CHECK
artifact_type: investigation
tags: [testing, ai, documentation, process-improvement]
---

# Investigation — TCK-20260904-DOC-COVERAGE-REVERSE-CHECK

## Current Behavior

**`check_docs_to_update_coverage`** (`tools/gate_checks/done_checker_static.py:482-558`) is
strictly one-directional today: it reads `investigation.md`'s `## Docs Requiring Update` bullets
(`_parse_docs_to_update`, line 429) and confirms every flagged path was actually touched
(`_git_touched_paths`/`_path_touched`, lines 383-426), comparing against real `git status`. It never
checks the reverse — whether a `docs/` path git shows as touched is *reflected back* into the
ticket's own `## Files Changed`/`## Related Docs` body-section prose. `tier == "hotfix"` returns
`NA` unconditionally (line 515-516) because no `investigation.md` exists to check against.

**`check_tag_drift`** (lines 769-810) is the explicit precedent this ticket is told to mirror for
path-resolution and section-reading, and it already does something structurally similar to what
the reverse check needs: it resolves the ticket path itself (`tickets/done/{id}.md`, falling back
to `tickets/inprogress/{id}.md`, lines 780-784 — no `tier` parameter at all), reads two body
sections via `_extract_section_text` (`Files Changed`... actually `Files Changed`/`Related Code
Areas` for tag drift), and diffs derived candidates against what the ticket declares. Two load-bearing
differences from what the new check needs, not just mechanics to copy verbatim:
1. **Status vocabulary**: `check_tag_drift` deliberately returns `CLEAN`/`FLAGGED` — "never
   PASS/FAIL/NA" (own docstring, lines 774-778) — specifically so no blocking-status consumer can
   misread it as a DoD condition, and it is explicitly *not* added to `run_finalize_selfcheck`'s
   checks tuple. This ticket's AC requires the opposite: a check that "actually blocks Verify, not
   just advises." The new check must return `PASS`/`FAIL` (matching
   `check_docs_to_update_coverage`'s own vocabulary), not adopt `CLEAN`/`FLAGGED`.
2. **Tier handling**: `check_tag_drift` has no `tier` parameter and applies uniformly regardless of
   tier (it just resolves whichever ticket file exists). `check_monitoring_write_recorded`
   (line 737) is the second, even more explicit precedent for this: its own docstring states it
   "Deliberately has no `tier` parameter and no NA branch — CLAUDE.md's Hard Rule requires the
   monitoring write 'including hotfix'" and `test_check_monitoring_write_recorded_applies_under_
   hotfix_tier` (`tests/tools/test_done_checker_static.py:999-1013`) locks this in as deliberate,
   not an oversight.

**`run_static_precheck`** (line 588-606) aggregates exactly 8 named checks in a fixed tuple,
7 of which are blocking (`docs_to_update_coverage` is the 7th) and 1 report-only
(`temporal_week_consistency`, always `PASS`). Its own docstring says "Aggregate all 8 Part A
checks" — note the *module*-level docstring at the top of the file (lines 8-9) is already stale
independent of this ticket ("the 5 pre-Finalize conditions"), a pre-existing staleness this ticket
did not introduce (see Anti-Drift Hazards).

**The JS/awk early-warning check** (`.claude/workflows/implement-ticket.js:903-918`,
`TCK-20260831-HOTFIX-FILES-CHANGED-DOC-OMISSION-EARLY-WARNING`) runs inside the **Document-Update
phase itself**, immediately after `doc-updater` returns and before the doc-staleness gate. It
`awk`-extracts only the ticket's `## Files Changed` section text (line 911; `## Related Docs` is
never checked), compares it against `docUpdate.docs_updated`'s own self-reported paths only (not
full `git status`), and on a mismatch **only logs a `⚠` warning** (line 917) — it never blocks, never
writes to the ticket, never fails a gate. It is scoped to the exact same problem class this ticket
targets, just earlier and softer.

**`.claude/agents/doc-updater.md`** (current base prompt) has no explicit self-check instruction
at all today — Step 0 tells the agent what to update and Output tells it what to report, but
nothing tells it to cross-reference its own touched paths against what will land in the ticket's
`Files Changed`/`Related Docs` text before returning.

**`docs/architecture/doc_updater_agent.md`**'s "Error handling" section (lines 142-148) states
today: "The Verify-time gate (`check_docs_to_update_coverage`) stays **fully decoupled** from
doc-updater's own output — it continues re-deriving ground truth from `investigation.md` + real
`git status` only" and "No new coupling is added." This is accurate for the *forward* direction
(unchanged by this ticket) but needs precise rewording once a reverse check exists, per this
ticket's own Scope instruction.

## The 3 named historical incidents — concrete evidence

All three are `standard`-tier, `DONE`, closed 2026-08-31, all surfaced by `RETRO-2026-W36.md`'s
"What to change?" note (`agent-monitoring/retro/RETRO-2026-W36.md:343`) as one recurring class:
"a Document-Update-added doc file not reflected back into the ticket's own `## Files
Changed`/`## Related Docs`." Reading the actual DONE tickets shows the class is not perfectly
uniform:

1. **`TCK-20260831-RACE-RELATIONS-MATRIX`**: `docs/mechanics/02_combat_laws.md` — "added by
   Document-Update after confirming this doc covers the exact `is_hostile_compat` function this
   ticket extends but was **not updated by the original Implement pass**" (Files Changed, line
   209-211). A genuine `docs/` path.
2. **`TCK-20260831-READINESS-SPEED-FORMULA`**: `docs/simulation_quality/corpus_tier_taxonomy.md` —
   "(Document-Update, after Implement)... recorded durably here... so future
   corpus-validation-dependent tickets discover it independently" (Files Changed, line 162-167). A
   genuine `docs/` path.
3. **`TCK-20260831-ITEM-INSTANCE-HISTORY`**: the actual gap named in Implementation Notes is
   **`src/core/state.py`**'s `to_readonly()` missing `item_instances=ReadOnlyDict(...)` — "Flagged
   by Document-Update's independent doc-vs-code cross-check, fixed directly" (line 85-94). This is
   a **`src/` code path, not a `docs/` path** — `doc-updater` apparently noticed a code bug while
   doing its doc-vs-code cross-check and fixed it outside its own documented scope (see Anti-Drift
   Hazards), and *that* fix is what wasn't originally reflected in Files Changed.

**This is directly load-bearing for Open Question 2 (scope):** a reverse check restricted to
`docs/` paths (matching the forward check's own scope, and this ticket's own Scope-text wording
— "does git status show a **docs/ path**...") would catch incidents #1 and #2 but **could not
structurally catch incident #3**, since `src/core/state.py` is never a `docs/` path regardless of
which body section is checked. The ticket's AC #3 only requires reproducing "at least one" of the
three as a fixture — incidents #1/#2 alone satisfy that bar with a `docs/`-only implementation — but
Plan should decide this with the #3 gap explicitly disclosed, not silently.

## Mechanics / Engine Constraints

None. This ticket is pure tooling/process (a `done-checker` static gate check and an agent-prompt
instruction) — it does not touch simulation state, the authoritative mutation pipeline, or any
Mechanics Bible / Engine Contract law. No chapter or contract constrains the implementation.

## Docs Requiring Update

- `docs/architecture/doc_updater_agent.md`: ticket's own Scope explicitly requires rewording the
  "Error handling" section's "fully decoupled ... No new coupling is added" language (lines
  142-148) to reflect that a reverse check now exists, while preserving the "never trust
  doc-updater's self-report" principle for the *forward* direction, which is genuinely unchanged.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md`: this
  epic's own "Acceptance signal" (lines 147-151) defines M2 as satisfied by exactly this ticket's
  work ("`check_docs_to_update_coverage` (or its replacement)... verified against at least one of
  the three real historical tickets"). This doc already carries a precedent for exactly this kind
  of update — its own "M1 is superseded — do not implement, already done" section (lines 23-41)
  documents a prior milestone being marked shipped in place once its owning ticket closed. M2
  should receive the equivalent note once this ticket lands.
- `docs/parity_ledger/infrastructure.yaml`: this file is the established parity-ledger home for
  `check_docs_to_update_coverage`'s own evolution — `INFRA-322` (line 8121, tolerant-matching
  extension by `TCK-20260802-DOC-COVERAGE-CHECK`'s tolerant-format follow-up) and `INFRA-396`
  (line 11688, resolved-conditional-bullet marker by
  `TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED`) both recorded a change to this
  exact function as its own new entry, even when the change was a pure logic extension rather than
  a new blocking condition. This ticket's reverse-direction extension fits the same precedent
  regardless of whether it lands as an extension of the existing function or a new tuple entry in
  `run_static_precheck` (see Risks — this is Parity phase's job via `parity-updater`, not
  Document-Update's, but the path itself belongs in this section since `check_docs_to_update_
  coverage` treats any `docs/` path, including `parity_ledger/`, uniformly).
- `docs/ai/ticket-lifecycle.md`: lines 358-362 state today that hotfix tier "has no equivalent
  backstop (`check_docs_to_update_coverage` returns `NA` unconditionally for hotfix) — an accepted,
  pre-existing gap, not something this phase introduces." Whether this text needs to change depends
  on Open Question 3 (does the reverse check inherit the hotfix NA exemption): if the reverse check
  is made tier-agnostic (this investigation's recommendation, see Risks), this passage becomes
  stale and must be corrected to describe the new hotfix-tier backstop; if the reverse check
  instead inherits the exemption, this passage remains accurate as-is for the reverse direction too
  and needs no edit. **Resolved during implementation, condition not met** should be added to this
  bullet's own text if Plan/Implement determine the exemption is inherited unchanged and no edit is
  needed here, per the resolved-conditional-bullet convention (`TCK-20260829-DOC-COVERAGE-
  CONDITIONAL-BULLET-BLIND-DOD-BLOCKED`).

The following were considered and are excluded:

`docs/ai/workflows.md` and `docs/ai/system_overview.md` (paths: `docs/ai/workflows.md`,
`docs/ai/system_overview.md`) are not required to change for this ticket: both are updated only
when a new pipeline *phase* or *agent* is added (see `tests/tools/test_document_update_phase_
wiring.py`'s existing coverage of exactly these two files for the Document-Update phase's own
introduction). This ticket extends an existing static check function and an existing agent's
prompt — it introduces no new phase and no new agent — so neither file's tables need a new row.

`docs/mechanics/*.md` and `docs/engine/*.md` are not required to change for this ticket: no
simulation law, formula, or pipeline behavior is touched (see Mechanics/Engine Constraints above).

If Plan ultimately confirms no doc genuinely needs a change beyond the four listed above, this
section stands as written — do not add a fifth "None" framing on top of a non-empty bullet list.

## Parity Ledger Overlap

- `INFRA-322` (`docs/parity_ledger/infrastructure.yaml:8121`, `status: verified`, `priority: P2`) —
  prior extension of `check_docs_to_update_coverage`'s tolerant bullet-matching. Not directly
  touched by this ticket's own behavior change, but is the precedent this ticket's own parity entry
  (added by `parity-updater` in the Parity phase, out of Investigate/Document-Update's own scope)
  should follow in shape.
- `INFRA-396` (`docs/parity_ledger/infrastructure.yaml:11688`, `status: verified`, `priority: P2`,
  `test_path: tests/tools/test_done_checker_static.py::test_docs_coverage_resolved_conditional_
  bullet_untouched_passes`) — same function, most recent prior extension. Same note as above.
- Neither `INFRA-322` nor `INFRA-396` is `P0` — no P0 parity entries are implicated by this
  ticket's scope. No `combat_movement`/`town_resource`/`strategic_cognition`/etc. subsystem ledger
  is touched; this is purely `infrastructure.yaml` territory (gate-check tooling, matching that
  file's own established `support_boundary` convention of "no simulation behavior is involved").

## Prior Work

- `TCK-20260802-DOC-COVERAGE-CHECK` (done) — built `check_docs_to_update_coverage` as the 7th Part
  A condition; established the bullet-format contract this ticket's reverse check must not disturb
  (Out of Scope, explicitly).
- `TCK-20260823-HOTFIX-INVESTIGATOR-EXCLUDED-DOC-BULLET-TEMPLATE-GAP` and
  `TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED` (done) — both prior hardenings
  of the same forward-direction check's bullet parsing; establish the Format 1/Format 2 and
  resolved-conditional-marker conventions this investigation reuses above.
- `TCK-20260831-HOTFIX-FILES-CHANGED-DOC-OMISSION-EARLY-WARNING` (done) — built the JS/awk
  early-warning check now proven (by this ticket's own retro evidence) insufficient alone; see
  Risks for the supersede-vs-coexist recommendation.
- `TCK-20260803-DOC-UPDATER-EPIC`/`-CORE-WIRING` (done) — introduced `doc-updater` and the
  Document-Update phase; `docs/architecture/doc_updater_agent.md` is that design's own ADR.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md`
  (active, not yet a tracked ticket at time of its own writing) — the epic plan this ticket
  implements M2 of; already names this ticket's exact scope and cites the same 3 historical
  incidents and the same 2 retro reports (`RETRO-2026-W33`, `RETRO-2026-W36`) this investigation
  independently confirmed by reading the real tickets and retro.

## Risks and Open Questions

**Decision 1 — supersede vs. coexist with the JS/awk early-warning check.**
Recommendation: **coexist**, do not remove. Evidence: the JS/awk check
(`implement-ticket.js:903-918`) runs inside Document-Update, before the doc-staleness gate, and is
non-blocking by design (a `⚠` log only) — it exists to give the agent a chance to self-correct in
the very same phase, cheaply, before the ticket ever reaches Verify. The new Python check is
necessarily later (Verify-time) and blocking. These are not two competing implementations of the
same fix — they are the same "generation-time defense-in-depth vs. deterministic enforcement"
split the ticket's own Request Summary already describes for parts (1)/(2) of this ticket, just
applied to a *prior* ticket's parts (1)/(2) instead. The JS/awk check already existed when all
three named incidents recurred (`TCK-20260831-HOTFIX-FILES-CHANGED-DOC-OMISSION-EARLY-WARNING` is
listed as a "prior" related ticket, and its own ticket text is dated before the three
`TCK-20260831-*` incidents in the working log) — proving the early warning alone did not prevent
the recurrence, but that is an argument for *adding* the blocking backstop, not for removing the
early warning (which still reduces how often the backstop needs to fire, mirroring the epic
doc's own explicit language: "The prompt self-check exists and reduces how often the primary
control needs to act, but is not itself the acceptance bar").

**Decision 2 — `docs/` paths only, or all touched paths.**
Recommendation: **`docs/` paths only**, matching the ticket's own Scope-text wording ("a **docs/
path** touched"), the forward check's existing scope, and the function name
(`check_docs_to_update_coverage`, not a generic files-changed-coverage check). Concrete
consequence to disclose explicitly rather than silently absorb: this scope **cannot** structurally
catch incident #3 (`ITEM-INSTANCE-HISTORY`'s `src/core/state.py` fix) — only #1 and #2. AC #3's "at
least one" wording is satisfiable either way, so this is not a blocking gap for AC compliance, but
Plan should record this as an accepted, disclosed limitation (mirroring the exact "accepted,
pre-existing gap" language style `docs/ai/ticket-lifecycle.md` already uses for the hotfix-tier
gap) rather than let the Completion Summary imply broader coverage than what was actually built.
Widening to all touched paths would close this gap but meaningfully changes the check's blast
radius (test files, `staging_artifacts/` itself, `tickets/working_log.csv`, etc. would all need
tolerance/exclusion rules not designed here) — out of this ticket's stated Scope if chosen, and
would need its own separately-scoped follow-up.

**Decision 3 — hotfix-tier NA exemption inheritance.**
Recommendation: **do not inherit it** — make the reverse check tier-agnostic, following
`check_monitoring_write_recorded`'s explicit precedent (no `tier` parameter, docstring reasoning:
"CLAUDE.md's Hard Rule requires the monitoring write 'including hotfix'") and `check_tag_drift`'s
own signature (no `tier` parameter at all). The forward check's `NA` for hotfix exists because its
required input, `investigation.md`, genuinely does not exist for hotfix tickets — that is a real
structural absence, not a policy choice. The reverse check's required inputs — real `git status`
and the ticket's own `## Files Changed`/`## Related Docs` body-section text — exist for **every**
tier, hotfix included (per Ticket Format, hotfix tickets carry the identical body-section set).
There is no structural reason to NA on hotfix here, and doing so anyway would leave exactly the
same recurring gap unguarded on the one tier where "self-evident intent" already means less
scrutiny elsewhere in the pipeline. If Plan disagrees and inherits the exemption instead, the
`docs/ai/ticket-lifecycle.md` bullet above should get the "Resolved during implementation,
condition not met" marker rather than being edited.

**Fourth latent decision (not one of the ticket's named 3, but blocking on the Docs list above):**
whether the reverse check lands as (a) an in-place extension of `check_docs_to_update_coverage`'s
own return value/evidence, or (b) a wholly separate function wired in as its own new tuple entry in
`run_static_precheck` (the ticket's Scope text literally offers both: "check_docs_to_update_
coverage" the docstring/module-count language ("Aggregate all 8 Part A checks") and the
`docs/ai/ticket-lifecycle.md` condition-6 backing prose would need updating in case (b) but not
necessarily in case (a). Recommend Plan decide this explicitly too, since it changes which of the
Docs Requiring Update bullets above are truly unconditional.

## Anti-Drift Hazards

- **Do not silently widen `check_tag_drift`'s advisory, non-blocking status vocabulary
  (`CLEAN`/`FLAGGED`) into this check.** The two functions solve structurally similar problems
  (ticket-body-section vs. derived-truth mismatch) but this ticket's own AC requires blocking
  behavior — reusing `check_tag_drift`'s *mechanics* (path resolution, `_extract_section_text`) is
  explicitly asked for; reusing its *status contract* would silently produce a non-blocking check
  that fails this ticket's own AC #2 ("actually blocks Verify, not just advises").
- **Do not touch `_parse_docs_to_update`'s forward-direction bullet-format contract.** Explicitly
  Out of Scope; several prior tickets (`TCK-20260823-...`, `TCK-20260829-...`) hardened this format
  against real false positives — any incidental edit here risks reopening one of those.
- **`doc-updater` fixing a code bug outside its own documented scope (the `to_readonly()` incident)
  is itself a real, disclosed drift** from `doc-updater.md`'s stated mandate ("updates the relevant
  `docs/` files... After a behavior change is implemented"), not a `docs/`-only action. This
  ticket's AC #4 (a self-check instruction) is about doc-updater's own *reporting* discipline, not
  about narrowing what it's allowed to fix — do not conflate the two while editing
  `doc-updater.md`'s prompt.
- **`docs/parity_ledger/infrastructure.yaml`'s own edit is Parity phase's (`parity-updater`'s) job,
  not Document-Update's** — despite being listed above as a required doc, `doc-updater.md`'s own
  scope explicitly excludes `docs/parity_ledger/*.yaml` (Per-Family Rules, "out of scope — that is
  `parity-updater`'s exclusive territory"). Do not route this bullet's satisfaction through
  `doc-updater`.
- **The module-level docstring's stale "5 pre-Finalize conditions" (line 8-9) predates this
  ticket and is not something this ticket is required to fix** — flagging it here only so it is not
  mistaken for new staleness this ticket introduced.
