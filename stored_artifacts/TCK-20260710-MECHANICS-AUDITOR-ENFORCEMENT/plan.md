---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT
artifact_type: plan
tags: [ai, workflows, determinism, agent-monitoring]
---

# Implementation Plan — TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT

## Summary

This plan implements design (b) from `investigation.md`: a standalone, on-demand post-hoc audit
function, `audit_verified_by_claims`, added to `tools/gate_checks/mechanics_auditor_static.py`. It
takes a `mechanics-auditor` agent's own already-produced output rows (`entry_id`, `status`,
`verified_by`, `Finding`) and, for every row whose *underlying parity-ledger entry* has
`status: verified`, independently recomputes `verify_entry_test_path` and flags two dishonesty
shapes: a row that omits the `static:mechanics_auditor_static` tag entirely ("Step 0 skipped") and a
row that claims static corroboration but whose fresh recompute contradicts it without a disclosed
caveat ("falsely cited"). No new `Agent()` call site is added anywhere, `implement-ticket.js` is not
touched, and `.claude/agents/mechanics-auditor.md`'s own Step 0 prompt text is not touched — this
keeps `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s prior scope ruling ("no call site") fully intact
rather than reversing it. The function's output field is named `honesty_status` (not `status`) and
reuses this module's own existing `PASS`/`FAIL` vocabulary rather than inventing a new string,
preventing the exact non-override mistake the prior ticket's architecture review already caught once.
The invocation-reliability gap (nothing forces this function to run after a session) is accepted as a
disclosed, documented residual limitation, not silently closed — see Design Decisions below.

## Design Decisions (Resolved at Plan Time)

These are the three open questions `investigation.md`'s Risks/Open Questions section explicitly left
for this phase to decide. All three are resolved here, in writing, per the ticket's own Scope
requirement that this not be left implicit.

### Decision 1 — Design (b) confirmed over design (a)

**Confirmed: design (b)**, a standalone post-hoc audit function in
`tools/gate_checks/mechanics_auditor_static.py`. No new `Agent(subagent_type: "mechanics-auditor")`
call site is added to `implement-ticket.js`.

Reasoning (adopting and confirming the investigation's recommendation): `mechanics-auditor`'s
invocation cardinality (zero, one, or many entries, on demand, not tied to any specific ticket's own
diff) does not fit the "exactly once per standard/epic ticket, against this ticket's diff" shape that
makes the Architecture-Verify/Parity/done-checker `bash()`-then-`agent()` call sites work. Design (a)
would require inventing new trigger semantics (when does it run? which entries does it audit?) that
nothing in this ticket's Scope asks for or answers — building that without first answering those
questions would repeat exactly the kind of under-specified pipeline architecture the prior ticket
declined to take on. Design (b) satisfies the literal AC wording (a static result computed and
cross-checked against a self-report) without engineering a new pipeline phase, and — critically —
does **not** require Architecture-Review sign-off to overturn `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s
ruling, because that ruling was scoped narrowly to "no new call site in `implement-ticket.js`" and
design (b) adds zero call sites anywhere. See Step 8 below for where this is recorded in the ticket's
own Implementation Notes.

### Decision 2 — Invocation-reliability gap: accepted as a disclosed residual gap

Design (b) closes the **detection** gap (a deterministic function now exists that can catch a false or
omitted `verified_by` claim, given the rows to check) but does not, by itself, close the **invocation**
gap (nothing forces the function to actually run after a `mechanics-auditor` session).

Of the three options `investigation.md` posed:

- **(ii) rejected.** Wiring a call to `audit_verified_by_claims` into `mechanics-auditor.md`'s own
  prompt as a later self-audit step would require the same agent to honestly invoke and honestly
  report the result of a check on its own prior honesty — this reintroduces, one step later, the exact
  "compliance depends on the agent honestly running it" problem this whole ticket and its parent epic
  exist to remove. Rejected on that basis alone.
- **(iii) investigated, found infeasible without new out-of-scope work.** A git pre-commit hook or
  Makefile target that runs the audit against recent `tickets/done/` entries on some cadence was
  considered. It does not work today: `audit_verified_by_claims` requires the agent's own emitted
  output *rows* (`entry_id`/`status`/`verified_by`/`Finding`) as its input, and nothing in this
  codebase currently captures a `mechanics-auditor` session's Markdown table output into any durable,
  machine-parseable location (no sidecar, no JSON log — `mechanics-auditor` has no
  `tool_call_count`/`cost_proxy_score` sidecar registration either, per this same epic's sibling ticket
  `TCK-20260710-CURRENT-RUN-SIDECAR-BASH`, which is explicitly Out of Scope here). A cron/hook trigger
  would first require inventing that durable-capture mechanism — new pipeline/data-model architecture
  beyond this ticket's Scope, structurally the same problem design (a) has. Rejected for this ticket;
  noted below as a legitimate future-ticket idea, not built here.
- **(i) accepted.** A callable, independently-tested audit function is strictly better than none, even
  though nothing auto-triggers it today. This mirrors `architecture_reviewer_static.py`'s own
  established "DISCLOSED LIMITATIONS" convention (confirmed present in that file, e.g. its
  `check_test_path`-adjacent DISCLOSURE blocks) — an accepted, documented gap, not a silently "fixed"
  one.

**Residual gap statement (to be written into docs, Step 7, and the ticket's Implementation Notes, Step
8):** after this ticket, a human reviewer, a future orchestrator change, or a future ticket can call
`audit_verified_by_claims(rows, ...)` against any `mechanics-auditor` session's own output rows to
verify `verified_by` honesty — but nothing currently calls it automatically. Closing that residual gap
would require a durable-capture mechanism for ad hoc agent output that does not exist yet and is
explicitly out of this ticket's scope; it is a plausible future ticket, not something to build here.

### Decision 3 — Function name, shape, and "honesty status" field

- **Function name:** `audit_verified_by_claims(rows, ledger_dir="docs/parity_ledger", base_dir=Path("."))
  -> list[dict]`, matching the investigation's proposed name and this module's existing plain-function,
  no-CLI, dict-return convention (mirrors `verify_entries`'s batch shape).
- **Output field name:** `honesty_status`, with values restricted to `"PASS"` / `"FAIL"` — the exact
  same two-value vocabulary `check_test_path` and `verify_entry_test_path` already use in this same
  module, not a new invented string (`"HONEST"`/`"DISHONEST"`/`"VIOLATION"`/etc. are all rejected).
  This satisfies the gate-determinism-followups `SEQUENCE.md`'s "one failure vocabulary, not two"
  shared design decision by reusing the vocabulary this exact module already established for "did the
  static check corroborate," rather than reusing the agent's separate `PARITY`/`DIVERGENT`/`MISSING`/
  `UNDOCUMENTED` classification vocabulary (which would conflate two different questions) or minting a
  third vocabulary.
- **Never named `status`/`Status`.** This is the specific mistake `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s
  architecture review round 1 already caught and corrected once (a static result must never be
  positioned to overwrite or relabel the agent's own `Status` column). `audit_verified_by_claims`'s
  return dicts use `entry_id` / `honesty_status` / `evidence` only — no key named `status` or `Status`
  appears anywhere in its return shape.

## Steps

### Step 1 — Implement `audit_verified_by_claims` core function + happy-path test
**Files:** `tools/gate_checks/mechanics_auditor_static.py`, `tests/tools/test_mechanics_auditor_static.py`
**Change:** Add the following function to the end of `mechanics_auditor_static.py` (after
`candidate_ledger_files_for_module`):

```python
def audit_verified_by_claims(rows, ledger_dir="docs/parity_ledger", base_dir: Path = Path(".")) -> list:
    """Post-hoc cross-check of a mechanics-auditor agent's own self-reported `verified_by` claims
    against an independently recomputed Step 0 result. Scoped strictly to the rows passed in — never
    a ledger-wide sweep (see module docstring).

    Each item in `rows` is one row of a mechanics-auditor agent's own output table, shaped:
        {"entry_id": str, "status": <agent's PARITY|DIVERGENT|MISSING|UNDOCUMENTED classification>,
         "verified_by": list[str], "Finding": str (optional, default "")}

    Only rows whose underlying parity-ledger entry has ledger status == "verified" are evaluated —
    Step 0 is mandatory only for that branch per .claude/agents/mechanics-auditor.md's "Checking
    Parity" section. Rows mapping to missing/divergent/unsupported/legacy_verified ledger entries, or
    to an entry_id not found at all, are skipped entirely: never flagged, never included in the
    returned list.

    Returns a list of dicts, one per evaluated row:
        {"entry_id": str, "honesty_status": "PASS" | "FAIL", "evidence": str}
    `honesty_status` reuses this module's own existing PASS/FAIL vocabulary (see check_test_path /
    verify_entry_test_path) rather than inventing a new status string, and is never named
    "status"/"Status" — it must never be read as, or substituted for, the agent's own
    PARITY/DIVERGENT/MISSING/UNDOCUMENTED classification for entry_id.
    """
    results = []
    for row in rows:
        entry_id = row.get("entry_id")
        entry, _filename = find_entry(entry_id, ledger_dir)
        if entry is None or entry.get("status") != "verified":
            continue

        claimed_static = "static:mechanics_auditor_static" in (row.get("verified_by") or [])
        finding_text = str(row.get("Finding") or "")

        if not claimed_static:
            results.append({
                "entry_id": entry_id,
                "honesty_status": "FAIL",
                "evidence": (
                    f"ledger status is 'verified' (Step 0 is mandatory) but row's verified_by "
                    f"{row.get('verified_by')!r} omits 'static:mechanics_auditor_static' — Step 0 "
                    "appears to have been skipped."
                ),
            })
            continue

        recompute = verify_entry_test_path(entry_id, ledger_dir, base_dir)
        if recompute["status"] == "FAIL" and "FAIL" not in finding_text.upper():
            results.append({
                "entry_id": entry_id,
                "honesty_status": "FAIL",
                "evidence": (
                    "row claims static corroboration but a fresh recompute of "
                    f"verify_entry_test_path returned FAIL ({recompute['evidence']}) with no FAIL "
                    "caveat disclosed in the row's Finding text — falsely cited static PASS."
                ),
            })
            continue

        results.append({
            "entry_id": entry_id,
            "honesty_status": "PASS",
            "evidence": f"verified_by claim corroborated by fresh recompute: {recompute['evidence']}",
        })

    return results
```

Add `test_audit_passes_honest_static_pass_claim` to `tests/tools/test_mechanics_auditor_static.py`
(happy path, test_plan.md item 4): a fixture `verified`-status entry whose `test_path` cites a
genuinely passing test, and a row honestly claiming
`verified_by: ["static:mechanics_auditor_static", "llm"]` with no contradicting caveat — assert the
returned list has exactly one item with `honesty_status == "PASS"`.
**Do NOT touch:** `check_test_path`, `verify_entry_test_path`, `find_entry`, `verify_entries`,
`candidate_ledger_files_for_module` — this step only appends a new function; no existing function
signature or return shape changes.
**Verify:** `python3 -m pytest tests/tools/test_mechanics_auditor_static.py::test_audit_passes_honest_static_pass_claim -v`

### Step 2 — Add "Step 0 skipped" detection test (AC #4, scenario A)
**Files:** `tests/tools/test_mechanics_auditor_static.py`
**Change:** Add `test_audit_detects_step_0_skipped_on_verified_status_entry` (test_plan.md item 2): a
fixture ledger entry with `status: verified`, and a simulated row with `verified_by: ["llm"]` only (no
static-check tag at all). Assert the function returns exactly one item for that `entry_id` with
`honesty_status == "FAIL"` and evidence mentioning the omission. This is the literal AC #4 scenario
("Step 0 was skipped").
**Do NOT touch:** the function body written in Step 1 unless this test reveals a genuine bug in the
`claimed_static` branch — if it passes as designed, this step is test-only.
**Verify:** `python3 -m pytest tests/tools/test_mechanics_auditor_static.py::test_audit_detects_step_0_skipped_on_verified_status_entry -v`

### Step 3 — Add "falsely cited static PASS" detection test (AC #4, scenario B)
**Files:** `tests/tools/test_mechanics_auditor_static.py`
**Change:** Add `test_audit_detects_falsely_cited_static_pass` (test_plan.md item 1): a fixture ledger
entry whose `test_path` cites a genuinely failing test, and a simulated row claiming
`verified_by: ["static:mechanics_auditor_static", "llm"]` with a `Finding` string that contains no
"FAIL" caveat. Assert the function returns exactly one item for that `entry_id` with
`honesty_status == "FAIL"` and evidence naming the contradiction. This is the literal AC #4 scenario
("falsely cited").
**Do NOT touch:** the function body unless this test reveals a genuine bug in the recompute-comparison
branch.
**Verify:** `python3 -m pytest tests/tools/test_mechanics_auditor_static.py::test_audit_detects_falsely_cited_static_pass -v`

### Step 4 — Add branch-scoping negative control test
**Files:** `tests/tools/test_mechanics_auditor_static.py`
**Change:** Add `test_audit_passes_honest_llm_only_claim_on_non_verified_status_entry` (test_plan.md
item 3): a fixture ledger entry with `status: missing` (or `status: divergent`), and a simulated row
with `verified_by: ["llm"]` only. Assert the function's returned list does **not** contain an entry for
that `entry_id` at all (not flagged, not evaluated — Step 0 was never mandatory for this branch).
**Do NOT touch:** the `entry.get("status") != "verified": continue` guard's semantics — this test locks
that behavior in, it must not be loosened to also flag non-`verified` branches.
**Verify:** `python3 -m pytest tests/tools/test_mechanics_auditor_static.py::test_audit_passes_honest_llm_only_claim_on_non_verified_status_entry -v`

### Step 5 — Add no-bulk-sweep anti-drift lock-in test
**Files:** `tests/tools/test_mechanics_auditor_static.py`
**Change:** Add `test_audit_scoped_by_row_not_whole_ledger` (test_plan.md item 5), mirroring the
existing `test_scoped_by_entry_id_not_whole_ledger` convention and reusing its 3-entry
(`A-001`/`A-002`/`A-003`) ledger fixture. Call `audit_verified_by_claims` with `rows` containing only
one of the three entry_ids; assert the returned list contains at most one item, and that the other two
entry_ids never appear anywhere in the result (mirrors the existing test's
`assert "A-001" not in str(result)` pattern).
**Do NOT touch:** the function's `for row in rows:` iteration shape — must never be changed to accept
a ledger file/directory instead of an explicit row list (that would reintroduce the bulk-sweep problem
this module's design discipline already avoids elsewhere, per Anti-Drift Hazard #3 in investigation.md).
**Verify:** `python3 -m pytest tests/tools/test_mechanics_auditor_static.py::test_audit_scoped_by_row_not_whole_ledger -v`

### Step 6 — Add non-override anti-drift lock-in test
**Files:** `tests/tools/test_mechanics_auditor_static.py`
**Change:** Add `test_audit_never_overrides_agent_status_classification` (test_plan.md item 6): call
`audit_verified_by_claims` on any fixture row and assert (by inspecting dict keys, not just values)
that no returned item ever contains a key named `"status"` or `"Status"` — only `entry_id`,
`honesty_status`, `evidence`. This is the literal lock-in for Design Decision 3 above.
**Do NOT touch:** the return-dict key names decided in Step 1 (`entry_id`/`honesty_status`/`evidence`)
— this test exists specifically to prevent a future edit from renaming `honesty_status` to `status` or
adding a second `status` key.
**Verify:** `python3 -m pytest tests/tools/test_mechanics_auditor_static.py::test_audit_never_overrides_agent_status_classification -v`

### Step 7 — Document the new function in `docs/ai/agents.md`
**Files:** `docs/ai/agents.md`
**Change:** In the `mechanics-auditor` section, immediately after the existing paragraph ending "...so
compliance depends entirely on the agent actually running the script and citing it honestly." (do not
edit that sentence — it remains accurate; Step 0 itself still has no orchestrator-side auto-trigger),
add a new paragraph:

> A separate, on-demand post-hoc audit closes part of this gap after the fact:
> `tools/gate_checks/mechanics_auditor_static.py`'s `audit_verified_by_claims(rows, ...)` takes a
> `mechanics-auditor` session's own output rows and independently recomputes each `verified`-status
> row's Step 0 result, flagging a row whose `verified_by` omits the static-check tag entirely ("Step 0
> skipped") or whose claim contradicts a fresh recompute without a disclosed caveat ("falsely cited").
> It returns `honesty_status: "PASS"|"FAIL"` per row — a field distinct from, and never overriding,
> the agent's own `PARITY`/`DIVERGENT`/`MISSING`/`UNDOCUMENTED` classification. **Disclosed
> limitation:** nothing currently calls this function automatically — it requires a human reviewer or
> a future ticket to supply a session's output rows explicitly. Closing that invocation gap would
> require a durable-capture mechanism for ad hoc agent output that does not exist yet (see
> `TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT`'s plan.md, Decision 2).

**Do NOT touch:** `.claude/agents/mechanics-auditor.md` (no edit — the agent's own Step 0 prompt text
is intentionally left unchanged; see Decision 2's rejection of option (ii)). Do NOT edit
`docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`, or
`docs/ai/skills.md` in this step — Step 9 verifies they need no change.
**Verify:** manual review (no automated test for prose); confirmed by Step 9's grep pass.

### Step 8 — Reconcile the ticket's own Scope/AC wording and Implementation Notes
**Files:** `tickets/inprogress/TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT.md`
**Change:** In the ticket's `## Implementation Notes` section, write:
1. Design (b) was chosen and implemented — no `Agent(subagent_type: "mechanics-auditor")` call site
   was added to `implement-ticket.js` (confirmed zero matches both before and after, via `grep`).
2. **Why this does not reopen or amend `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s closed record:**
   that ticket's ruling was scoped narrowly and explicitly to "no new call site in
   `implement-ticket.js`" (its plan.md Summary and Implementation Notes, quoted in
   investigation.md's Prior Work section). Design (b) adds zero call sites anywhere — it is a new,
   independent function in a module that ticket already built, addressing a question
   (post-hoc honesty cross-check) that ticket never posed or ruled on. The prior ruling remains
   correct and untouched; this ticket does not amend, supersede in substance, or require
   Architecture-Review sign-off to overturn it, because nothing about "no call site" was reversed.
3. AC #2 ("if a call site/wrapper is added, the static check result is computed before the agent
   renders its verdict and injected as context") is satisfied vacuously — no call site/wrapper was
   added, so its precondition never triggers. The closest functional analogue — a static result
   computed and made available for comparison — is delivered by `audit_verified_by_claims`'s internal
   recompute-and-compare step (Step 1 above), just without an agent-prompt injection point, since no
   agent-prompt call site exists to inject into.
4. AC #3 ("the agent's verified_by self-report is cross-checked post-hoc against the
   orchestrator-computed static result") is satisfied directly by `audit_verified_by_claims`: it takes
   the agent's self-reported rows and independently recomputes the static result for comparison.
5. Note the disclosed residual invocation gap (Decision 2) explicitly, so a future reader does not
   mistake "a callable audit function exists" for "the audit runs automatically."

**Do NOT touch:** the ticket's `## Scope`, `## Out of Scope`, `## Acceptance Criteria`, or `## Related
Tickets` sections — those are the accepted scope record; this step only appends to `## Implementation
Notes` (and, at Finalize, `## Files Changed`/`## Completion Summary` per the normal ticket-closure
workflow, not part of this plan's steps).
**Verify:** manual review — confirm the five points above are present in Implementation Notes before
moving the ticket to `tickets/done/`.

### Step 9 — Verification pass: negative controls + full scoped test run
**Files:** none changed; verification only.
**Change:** Run, in order:
1. `grep -n "mechanics-auditor\|mechanics_auditor" .claude/workflows/implement-ticket.js` — must return
   zero matches (confirms the prior ruling was not accidentally overturned).
2. `grep -n "no orchestrator-side enforcement" .claude/agents/mechanics-auditor.md docs/ai/agents.md
   docs/ai/workflows.md docs/ai/system_overview.md docs/ai/ticket-lifecycle.md` — confirm the phrase's
   surrounding claim is still accurate for Step 0 itself (it is — Step 0's orchestrator-enforcement
   status is unchanged by this ticket) and that `docs/ai/agents.md` now additionally documents the
   new post-hoc function (Step 7). The other four files require no edits.
3. `python3 -m pytest tests/tools/test_mechanics_auditor_static.py -v` — all tests pass, including the
   6 new ones from Steps 1–6, plus the 16 pre-existing tests unmodified (per test_plan.md's regression
   baseline of 16 tests in this file, now 22).
4. `python3 -m pytest tests/tools/test_mechanics_auditor_static.py tests/tools/test_parity_updater_static.py tests/tools/test_done_checker_static.py -v`
   — confirms no regression in the two sibling gate-check modules this module imports from / sits
   alongside.
**Do NOT touch:** anything — this step is read-only verification.
**Verify:** all four commands above; this step *is* the verification for the plan as a whole.

## Scope Guards

- Do NOT touch `.claude/workflows/implement-ticket.js` — no edits of any kind, no new `Agent()` call
  site, no new `bash()` block.
- Do NOT add any `Agent(subagent_type: "mechanics-auditor")` call site anywhere in the codebase.
- Do NOT reopen, amend, or edit `tickets/done/TCK-20260705-GATE-DET-MECHANICS-AUDITOR.md` — its closed
  record stands; Step 8 documents *why* this ticket doesn't need to touch it, but does not touch it.
- Do NOT modify `.claude/agents/mechanics-auditor.md` — the agent's own Step 0 prompt text is
  intentionally left unchanged (Decision 2 rejects self-invocation of the new audit function).
- Do NOT modify `tools/gate_checks/parity_updater_static.py` or `tools/gate_checks/done_checker_static.py`
  beyond the existing import already present in `mechanics_auditor_static.py`.
- Do NOT modify `check_test_path`, `verify_entry_test_path`, `find_entry`, `verify_entries`, or
  `candidate_ledger_files_for_module` — this ticket only appends one new function.
- Do NOT make `audit_verified_by_claims` accept a ledger file/directory or run a ledger-wide sweep —
  it must only ever operate on caller-supplied `rows`.
- Do NOT name the new output field `status` or `Status`, and do NOT invent a `honesty_status` value
  outside `{"PASS", "FAIL"}`.
- Do NOT edit `docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`, or
  `docs/ai/skills.md` — Step 9's grep confirms none of their existing `mechanics-auditor` mentions go
  stale as a result of this ticket.
- Do NOT touch anything under the sibling tickets' scope: `TCK-20260710-CURRENT-RUN-SIDECAR-BASH`'s
  `tool_call_count`/`cost_proxy_score` sidecar fields, or `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH`'s
  per-phase `ts` capture — both are explicitly Out of Scope on this ticket.
- Do NOT introduce a tag outside `{ai, workflows, determinism, agent-monitoring}` without first
  registering it via `tools/tag_registry.py add`.
- Never run `pytest tests/` (full suite) — use only the scoped commands in Step 9.

## Dependency Map

- Step 1 is a prerequisite for Steps 2–6 (each adds one isolated test against the function Step 1
  builds).
- Steps 2, 3, 4, 5, 6 are mutually independent — each adds exactly one test to the same file and can
  be done/verified in any order once Step 1 lands.
- Step 7 (docs) depends only on Step 1 (needs the final function name/signature/field names to
  document accurately) — independent of Steps 2–6.
- Step 8 (ticket reconciliation) depends on Steps 1–7 being complete, since it summarizes the shipped
  design.
- Step 9 (verification) depends on all prior steps and must run last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — design explicitly resolved, documented (not left implicit) | Design Decisions section (this plan) + Step 8 | Manual review of ticket Implementation Notes (no automated test per test_plan.md) |
| AC #2 — if a call site/wrapper is added, static check computed before agent renders verdict | Vacuously satisfied (no call site added); closest analogue delivered by Step 1's internal recompute; documented in Step 8 | N/A — condition's precondition never triggers, per Step 8's written reconciliation |
| AC #3 — agent's verified_by self-report cross-checked post-hoc against orchestrator-computed static result | Step 1 (core function) | `test_audit_passes_honest_static_pass_claim` (Step 1), `test_audit_detects_falsely_cited_static_pass` (Step 3) |
| AC #4 — new test demonstrates detection of Step 0 skipped or falsely cited | Step 2 (skipped) and Step 3 (falsely cited) | `test_audit_detects_step_0_skipped_on_verified_status_entry` (Step 2), `test_audit_detects_falsely_cited_static_pass` (Step 3) |

## Anti-Drift Notes

- **Non-override principle (repeat of a previously-caught mistake):** `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s
  architecture review round 1 already had to correct a static check result being positioned to
  override the agent's own `Status` classification. This plan's `honesty_status` field name (never
  `status`/`Status`) and Step 6's dedicated lock-in test exist specifically so this ticket does not
  repeat that exact mistake.
- **One failure vocabulary, not two:** per `tickets/done/gate-determinism-followups/SEQUENCE.md`'s
  shared design decision, `honesty_status` reuses this module's own existing `PASS`/`FAIL` strings
  (from `check_test_path`/`verify_entry_test_path`) rather than minting a third vocabulary
  (`HONEST`/`DISHONEST`/etc.). This is a deliberate, narrower reuse than reusing the agent's
  `PARITY`/`DIVERGENT`/`MISSING`/`UNDOCUMENTED` vocabulary, which would have conflated two different
  questions (code correctness vs. self-report honesty) — see Decision 3.
- **No-bulk-sweep discipline:** `mechanics_auditor_static.py`'s existing design principle (scoped
  strictly to explicit IDs, 82% of `verified` entries have no `test_path` at all) must carry over
  exactly to `audit_verified_by_claims` — it must never accept or scan a whole ledger file. Step 5's
  test locks this in.
- **Branch scoping:** Step 0 is only mandatory for `status: verified` ledger entries per the agent's
  own prompt (`missing`/`divergent` branches never mention Step 0). `audit_verified_by_claims` must
  never flag an `["llm"]`-only claim on a non-`verified`-status entry as a violation. Step 4's test
  locks this in.
- **Prior ruling is preserved, not reversed:** design (b) was chosen specifically because it does not
  require Architecture-Review sign-off to overturn `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s "no
  call site" ruling — zero call sites are added by this ticket either. Step 9's `grep` negative
  control on `implement-ticket.js` exists to catch any accidental drift from this during
  implementation.
- **Residual invocation gap is disclosed, not silently left implicit:** the audit function's existence
  does not mean it runs automatically. This must be stated plainly in both `docs/ai/agents.md` (Step
  7) and the ticket's own Implementation Notes (Step 8) — a future reader must not conclude the
  invocation gap from the parent epic's idea doc was fully closed by this ticket.

## Confirmation of Open Questions

All three open questions `investigation.md` left for this phase are resolved above (Design Decisions
1–3), with written reasoning for each, including an explicit feasibility check (not an assumption) for
option (iii) under Decision 2. No genuine unresolved question remains that requires human input before
implementation begins.

## Deviations

Two immaterial deviations from this plan's literal text, both surfaced during implementation:

1. **Step 7 insertion point.** The plan's literal wording says to insert the new paragraph
   "immediately after the existing paragraph ending '...so compliance depends entirely on the agent
   actually running the script and citing it honestly.'" In the actual file
   (`docs/ai/agents.md`), that quoted sentence is not the paragraph's final sentence — it is followed,
   in the same paragraph, by "The agent self-reports in `verified_by` whether each row's `Status` was
   corroborated by the static check or came from independent judgment alone." Inserting strictly
   "immediately after" the quoted sentence would have split that paragraph in two mid-thought. The new
   paragraph was instead inserted after the *whole* Step 0 paragraph (i.e., after the
   "...independent judgment alone." sentence) and before the pre-existing "A convenience wrapper..."
   paragraph — satisfying the plan's intent (new paragraph placed directly after the Step 0
   description, before the unrelated convenience-wrapper paragraph) without breaking up an existing
   sentence pair. No other change to the surrounding prose was made.

2. **Step 9's anticipated test-count baseline.** The plan (Step 9, item 3) anticipated "16 pre-existing
   tests, now 22" in `tests/tools/test_mechanics_auditor_static.py`. The actual pre-existing count at
   implementation time, read fresh from the file, was 11 tests; adding the 6 new tests from Steps 1–6
   brings the total to 17, not 22. This is a factual correction to the plan's stated baseline, not a
   scope or behavior change — all 6 planned tests were added exactly as specified, and the full file
   (17/17) plus the sibling-module regression run (79/79 combined) pass.
