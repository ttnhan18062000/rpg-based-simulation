---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT
artifact_type: investigation
tags: [ai, workflows, determinism, agent-monitoring]
---

# Investigation — TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT

## Current Behavior

**`.claude/agents/mechanics-auditor.md`** (lines 38–56, "Checking Parity" section): the agent's own
prompt instructs it, before writing a final `Status`/`Finding` for any `verified`-status ledger entry,
to run `tools/gate_checks/mechanics_auditor_static.py`'s `verify_entry_test_path(entry_id)` via
`python3 -c "..."` and cite the PASS/FAIL + evidence verbatim. It self-reports a `verified_by` field
per row (e.g. `["static:mechanics_auditor_static", "llm"]` or `["llm"]`, lines 77–79). The prompt
explicitly discloses (lines 53–56): *"Unlike done-checker/parity-updater's Step 0 (which the
orchestrator runs and independently verifies), this Step 0 has no orchestrator-side enforcement —
mechanics-auditor has no pipeline call site — so compliance depends entirely on this agent actually
running the script and citing it honestly."* The same sentence (near-verbatim) is duplicated in
`docs/ai/agents.md:290-293`.

**`tools/gate_checks/mechanics_auditor_static.py`** (176 lines) already provides the deterministic
building block this ticket needs: `verify_entry_test_path(entry_id, ledger_dir, base_dir) -> dict`
(lines 154–175) looks up one parity-ledger entry by ID via `find_entry` (lines 131–151), parses its
`test_path` citation(s) via `parse_test_path_citations` (lines 43–74, handles 4 legacy citation
shapes), and runs each cited test scoped (`check_test_path`, lines 77–128, `pytest <citation> -x -q`,
never the full suite). Returns `{"entry_id", "ledger_file", "status": "PASS"|"FAIL", "evidence",
"verified_by": ["static:mechanics_auditor_static"]}`. `verify_entries(entry_ids, ...)` (lines
178–183) is a thin batch wrapper. `candidate_ledger_files_for_module` (lines 186–195) reuses
`parity_updater_static.expected_subsystems_for_files` for module-level discovery. **Nothing in this
module currently reads or cross-checks an agent's *self-reported* `verified_by` claim against its own
recomputed result** — it only answers "does this entry's cited test pass right now?", one entry at a
time, on request.

**`.claude/workflows/implement-ticket.js`** (1172 lines, read fresh for this ticket): confirmed via
`grep -n "mechanics-auditor\|mechanics_auditor"` — **zero matches**. No `Agent(subagent_type:
"mechanics-auditor")` call, no `mechanics_auditor_static` import, anywhere in the file. By contrast,
the three sibling static-check modules each have a live call site with the identical
bash()-before-agent()/pushEvent-after shape:
- `architecture_reviewer_static.run_architecture_checks` — computed at lines 577–591
  (`archCheckOutput`), injected into the `archVerify` agent prompt at lines 607–624
  (Architecture-Verify phase, post-Implement).
- `done_checker_static.run_static_precheck` / `run_finalize_selfcheck` — called from the Verify and
  Finalize phases (not re-read in full this session, but referenced identically per
  `docs/ai/ticket-lifecycle.md:358-363`).
- `parity_updater_static.expected_subsystems_for_files` / `cross_reference_touched` — computed
  before/after the Parity-phase agent call at lines 774–830 (`p0ScanOutput`, `archCheckResults`-style
  marker-prefixed JSON parse).

All three of these call sites follow the same precedent: `bash()` runs the Python check via
`python3 -c "..."` with a `MARKER_JSON:`-prefixed stdout convention (documented at
`implement-ticket.js:170-172` — never embed raw JSON directly in the `-c` string, always
individually-quoted argv elements, to avoid quote-corruption), the JSON is parsed with a
try/catch-to-`null` fallback, and the result is injected as literal context into the paired
`agent()` prompt. `mechanics-auditor` has none of this — its only "Step 0" is a self-contained
instruction inside the agent's own prompt file (`.claude/agents/mechanics-auditor.md`), never
constructed or verified by any JS orchestrator.

**Sidecar/`captureTs()` precedent (siblings' work, confirmed already landed):** `writeSidecar()`
(lines 174–181) and `captureTs()` (lines 189–192) are now defined once in `implement-ticket.js` and
called immediately before every `agent()` call site (11 sites, per `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH`'s
Implementation Notes). These are **not directly relevant to this ticket's core design decision** —
mechanics-auditor has no call site in this file at all, so there is no adjacent `writeSidecar()`/
`captureTs()` call to add one next to. They are cited here only because the ticket brief asked me to
confirm this, and because if a future ticket *did* add a mechanics-auditor call site, it would need to
follow this same two-call precedent (per the file's own established convention) — noted as a design
constraint for that hypothetical, not something this ticket must itself satisfy.

## Mechanics / Engine Constraints

None. This ticket is agent-infrastructure/tooling work (`layer: ai`) — it does not touch any
`src/` gameplay code, `docs/mechanics/` formula, or `docs/engine/` contract. `mechanics-auditor` is
the tool that *enforces* the Authoritative Mechanics Rule (parity between `docs/mechanics/` and
source) for other tickets; this ticket only hardens the provenance-honesty of that enforcement tool
itself. No mechanics chapter or engine contract directly constrains the implementation choice here.

## Parity Ledger Overlap

None, confirmed. `grep -rn "mechanics-auditor\|mechanics_auditor" docs/parity_ledger/` returned zero
matches across all 9 files (`combat_movement.yaml`, `faction.yaml`, `infrastructure.yaml`,
`progression.yaml`, `social_narrative.yaml`, `strategic_cognition.yaml`, `substrate.yaml`,
`town_resource.yaml`, `world_dynamics.yaml`). This ticket does not add, remove, or change the status
of any parity-ledger entry — it changes only agent-infrastructure tooling around how those entries'
existing `test_path` citations get cross-checked. No `parity_updater` phase action is expected at
Finalize.

## Prior Work

**`TCK-20260705-GATE-DET-MECHANICS-AUDITOR`** (done, `tickets/done/TCK-20260705-GATE-DET-MECHANICS-AUDITOR.md`)
built `mechanics_auditor_static.py` and wired its `Step 0` instruction into the agent's own prompt
file only. Its plan.md (Summary, lines 25–29) states the resolved decision explicitly:

> "Wiring happens entirely inside `.claude/agents/mechanics-auditor.md`'s own prompt (its existing
> 'Checking Parity' section) — per the orchestrating session's resolved decision, this ticket does
> **not** add a new `Agent(subagent_type: "mechanics-auditor")` call site to `implement-ticket.js`,
> since the agent has zero pipeline call sites today and adding one would be new pipeline
> architecture beyond this ticket's scope."

And its Implementation Notes (Step 3, lines 114-120) confirm what actually shipped:

> "No `Agent(subagent_type: "mechanics-auditor")` call site was added to
> `.claude/workflows/implement-ticket.js` (confirmed zero pre-existing call sites; adding one is
> explicitly out of scope per the plan and ticket)."

Its Scope Guards (line 331) reiterate: "Do not add any new call site to
`.claude/workflows/implement-ticket.js`." **This was a deliberate scope-boundary decision made
by the orchestrating session at plan time, not a rejected proposal or an architecture-reviewer
finding against the idea** — nothing in that ticket's investigation.md/plan.md frames a call site as
architecturally unsound; it is framed purely as "new pipeline architecture beyond this [gate-parity]
ticket's scope." This distinction matters for this ticket's own resolution (see Risks/Anti-Drift
below): overturning a scope decision is a materially different, lower-bar action than overturning an
architecture-reviewer rejection.

**`TCK-20260705-GATE-DET-DONE-CHECKER` / `-ARCHITECTURE-REVIEWER` / `-PARITY-UPDATER`** (siblings,
all done): each of these three gates *does* have a natural, fixed-cadence pipeline hook — Verify/
Finalize (done-checker), post-Implement diff review (architecture-reviewer), post-Implement ledger
update (parity-updater) — because each one's job is defined as "run exactly once, at a specific
point, for every standard/epic ticket." `mechanics-auditor`'s job (compare a mechanics chapter or a
named ledger entry against source, on demand) has no equivalent fixed cadence: it is not something
every ticket needs run against it, and its natural unit of work (a chapter, or an explicit small set
of entry IDs) does not map onto "the diff this ticket produced" the way `architecture_reviewer_static`
does. This structural difference — not merely "it happens to have zero call sites today" — is the
main evidence against directly porting the Architecture-Verify pattern.

**`TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH`** and **`TCK-20260710-CURRENT-RUN-SIDECAR-BASH`**
(siblings in this same epic, both done): both ticket files' own Out-of-Scope sections explicitly
name this ticket ("C3 (verified_by provenance enforcement) — separate ticket
TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT, different mechanism") and confirm no file overlap:
both siblings' `Related Code Areas` are `.claude/workflows/*.js` + `tools/agent-monitoring/*`; this
ticket's are `.claude/agents/mechanics-auditor.md` + `tools/gate_checks/mechanics_auditor_static.py`
+ (potentially) `implement-ticket.js` if a call site is chosen. No coordination-file-overlap risk was
found, confirming the ticket brief's own claim.

**Epic ticket** (`tickets/todos/agent-bookkeeping-determinism/TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC.md`,
scope item 3, lines 71–81) frames the open question identically to this ticket's own Assumptions
section: "must confirm whether mechanics-auditor has any pipeline call site to enforce against, or
whether enforcement means something else (e.g. a standalone post-hoc audit) given it's invoked ad
hoc."

## Risks and Open Questions

1. **Core design decision (blocking, must be resolved at Plan time, not assumed here).** Two
   candidate designs, with materially different scope and risk:
   - **(a) New pipeline call site.** Add `Agent(subagent_type: "mechanics-auditor")` to
     `implement-ticket.js`, mirroring Architecture-Verify's `bash()`-then-`agent()` shape. This
     directly overturns `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s explicit scope ruling and
     requires Architecture-Review sign-off per this ticket's own Scope/Assumptions. It also requires
     answering questions that ticket never had to: *when* does it run (every standard/epic ticket,
     unconditionally? only tickets whose `implementation.files_changed`/`parity_subsystems` overlap a
     mechanics chapter's source, mirroring Parity's `p0ScanOutput` conditional-trigger pattern?) and
     *which entries* does it audit (the ticket has no natural "this diff touches these N ledger
     entries" list the way Architecture-Verify has `files_changed`). None of this is scoped or
     answered by the current ticket text — building it without answering these first would be
     under-specified pipeline architecture, the exact failure mode the prior ticket declined to take
     on.
   - **(b) Standalone post-hoc audit function, no `implement-ticket.js` edit.** Extend
     `tools/gate_checks/mechanics_auditor_static.py` with a new function (naming TBD at Plan time,
     e.g. `audit_verified_by_claims(rows, ledger_dir, base_dir)`) that takes a `mechanics-auditor`
     agent's own output rows (`entry_id`, `status`, `verified_by`) and, for each row whose underlying
     ledger `status == "verified"`, independently *recomputes* `verify_entry_test_path` and compares:
     did the agent's `verified_by` claim `"static:mechanics_auditor_static"` when a fresh recompute
     shows the check was never actually runnable/passing consistently with that claim (a "falsely
     cited" case), or did the row omit the static-check tag entirely for a `verified`-status entry
     the agent's own prompt says it *must* check (a "Step 0 skipped" case)? This does not require an
     `implement-ticket.js` call site (mechanics-auditor remains ad hoc), does not overturn the prior
     ruling (no new `Agent()` call site is added), and directly satisfies this ticket's AC #2/#3
     wording ("static check result computed... injected as context" / "cross-checked post-hoc
     against the orchestrator-computed static result") if the wrapper computing the pre-check and the
     module doing the post-hoc cross-check are the same reusable code path.

   **My recommendation, for the Plan phase to confirm or override:** (b). Reasoning: `mechanics-auditor`'s
   invocation cardinality (zero, one, or many entries, on demand, not tied to a specific ticket's
   diff) structurally does not fit the "exactly once per standard/epic ticket, against this ticket's
   own diff" shape that makes the Architecture-Verify/Parity/done-checker call sites work. Design (a)
   would require inventing new trigger semantics not asked for anywhere in this ticket's Scope, while
   design (b) satisfies the literal AC wording without engineering a new pipeline phase. This
   recommendation should still be explicitly confirmed (not silently adopted) during Plan/Review,
   since the ticket's own Scope frames it as a genuinely open resolution, not a foregone conclusion.

2. **Where does the post-hoc audit actually get invoked, if not from a pipeline?** Design (b) closes
   the *detection* gap (a deterministic function now exists that can catch a false/omitted
   `verified_by` claim) but does not, by itself, close the *invocation* gap — nothing forces anyone to
   run it after a `mechanics-auditor` session, the same class of "depends on someone remembering"
   problem the idea doc's Problem section describes for `duration_s`/sidecar registration. Options to
   resolve at Plan time: (i) accept this as a partial, documented improvement (a callable/testable
   audit tool is strictly better than none, even if not auto-triggered) and disclose the residual gap
   explicitly, mirroring `architecture_reviewer_static.py`'s own "disclosed limitations" convention;
   (ii) invoke it from `mechanics-auditor.md`'s own prompt as a second, later Step (the agent
   self-audits its own just-produced table before returning) — but this reintroduces the same
   "compliance depends on the agent honestly running it" problem the ticket is trying to remove,
   just moved one step later; (iii) find a genuinely orchestrator-side trigger point elsewhere (e.g.
   done-checker's Verify phase, if a ticket's `parity_subsystems` list is non-empty) — but this
   reopens design (a)'s scope-creep problem in a different location. This must be resolved explicitly
   in plan.md, not left implicit.

3. **What does "falsely cited" mean precisely for a `["llm"]`-only row?** The agent's prompt
   currently never *requires* citing the static check for a non-`verified`-status entry (`missing`/
   `divergent` branches don't mention Step 0 at all, per `.claude/agents/mechanics-auditor.md:64-65`).
   The new audit function must not flag a `["llm"]`-only `verified_by` for a `missing`/`divergent`
   entry as a violation — only for a `verified`-status entry, where Step 0 is mandatory per the
   agent's own prompt. This distinction must be preserved by whatever check function ships.

## Anti-Drift Hazards

- **Do not silently add an `Agent(subagent_type: "mechanics-auditor")` call site to
  `implement-ticket.js`** without an explicit, written Architecture-Review sign-off overturning
  `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s scope ruling — this ticket's own Scope requires that
  overturn to be justified in writing, not simply implemented as if the prior ruling didn't exist.
- **Do not let the post-hoc audit's result override `mechanics-auditor`'s own `Status` classification**
  (`PARITY`/`DIVERGENT`/`MISSING`/`UNDOCUMENTED`) — this repeats the exact non-override principle
  `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s Step 0 already established and its Anti-Drift Notes
  explicitly corrected during architecture review round 1 (a static FAIL must never force
  `PARITY`→`DIVERGENT`/`MISSING`). The new post-hoc audit answers a narrower, different question
  ("was the `verified_by` claim honest?"), not "is the code right?" — conflating the two would repeat
  a mistake this codebase has already caught and fixed once.
- **Do not run the new audit as a ledger-wide sweep.** `mechanics_auditor_static.py`'s existing design
  discipline (scoped strictly to explicit entry IDs, never a bulk run — see its module docstring,
  lines 10–13, and 82% of `verified` entries having no `test_path` at all) must carry over to any new
  function added here. A bulk audit would produce a wall of unrelated FAILs unrelated to any actual
  dishonesty.
- **Do not touch `tools/gate_checks/parity_updater_static.py` or `tools/gate_checks/done_checker_static.py`**
  beyond importing from them — same restriction the prior ticket already established and this one
  inherits (`Related Code Areas` lists them read-only-adjacent, not as edit targets).
- **Do not fold this ticket's file changes into the two sibling tickets' diffs.** Confirmed no file
  overlap exists (siblings touch only `.claude/workflows/*.js` + `tools/agent-monitoring/*`; this
  ticket touches `.claude/agents/mechanics-auditor.md` + `tools/gate_checks/mechanics_auditor_static.py`
  + docs, and only `implement-ticket.js` *if and only if* design (a) is chosen with sign-off).
- **Do not introduce a new tag not already in `docs/guidelines/tag_registry.jsonl`** — no
  `mechanics`/`auditor`/`enforcement`/`gate` tag currently exists in the registry (confirmed via
  `python3 tools/tag_registry.py list`); use existing registered tags (`ai`, `workflows`,
  `determinism`, `agent-monitoring`) for this ticket's own frontmatter and artifacts, or register a
  new one explicitly before use if none of these fit at Plan/Implement time.
