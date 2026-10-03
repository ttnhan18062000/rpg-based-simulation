---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-GATE-DET-MECHANICS-AUDITOR
artifact_type: investigation
tags: [ai, workflows, determinism, mechanics-auditor, parity]
---

# Investigation — TCK-20260705-GATE-DET-MECHANICS-AUDITOR

## Current Behavior

### `mechanics-auditor` is invoked purely ad hoc — never from `implement-ticket.js`

Confirmed by direct evidence, not inference:

- `grep -n -i "mechanics-auditor\|mechanics_auditor\|PARITY verdict" .claude/workflows/implement-ticket.js`
  returns **zero matches**. There is no phase, no `agent()` call, no string reference to this agent
  anywhere in the workflow file.
- By contrast, the two sibling tickets' agents ARE wired into `implement-ticket.js`:
  - `parity-updater`: `implement-ticket.js:597` (`expected_subsystems_for_files` before the agent call)
    and `:637` (`cross_reference_touched` after it returns) — Parity phase.
  - `done-checker`: `implement-ticket.js:769` (`run_static_precheck` before the agent call) — Verify
    phase; `:856` (`run_finalize_selfcheck`) — Finalize phase.
  - Both are also documented in `docs/ai/workflows.md:86,88`, `docs/ai/system_overview.md:81,113`, and
    `docs/ai/ticket-lifecycle.md:270,307,344` as part of the 9-phase pipeline table.
- `docs/ai/skills.md:177` ("Choosing the Right Tool" table) lists the only invocation path found
  anywhere in the repo: `| Check mechanics parity after a change | Agent(subagent_type: "mechanics-auditor") |`.
- `docs/ai/agents.md:224-246` (mechanics-auditor's own section) states "**When to invoke directly:**
  Before modifying a simulation subsystem, or after a `parity-updater` run to verify the ledger is
  consistent with the actual implementation." — this is explicitly framed as a direct/manual
  invocation, unlike `done-checker`'s and `parity-updater`'s sections which describe a `Step 0 —
  static pre-check` wired into a named pipeline phase.
- `docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md` all currently
  have **zero** mentions of `mechanics-auditor` (confirmed by grep) — there is no phase table row to
  extend, because it isn't part of the phase table.

**Conclusion (resolves the ticket's own flagged Assumption):** this ticket's wiring point is the
agent's own prompt file, `.claude/agents/mechanics-auditor.md`, not a `.claude/workflows/implement-ticket.js`
edit. There is no workflow call site to hook `run_static_precheck`-style plumbing into, because the
agent has none today. The instruction to run the new static check before rendering any `PARITY`
verdict must be added as a step inside `mechanics-auditor.md`'s own "Checking Parity" section
(currently lines 32-38), the same way the agent already self-directs to read
`docs/parity_ledger/` and check `status` there. The 3 shared docs (`workflows.md`,
`system_overview.md`, `ticket-lifecycle.md`) will need a *new* mention (not an edit to an existing
phase-table row) — likely framed as "ad hoc agents with their own static pre-checks" rather than
inserted into the 9-phase table, since mechanics-auditor genuinely isn't a phase. This framing
decision should go to the Planner explicitly rather than being assumed.

### `mechanics-auditor.md`'s current "Checking Parity" logic (lines 32-38)

```
For each rule:
- Find the relevant parity ledger entry in `docs/parity_ledger/` (the subsystem YAML that covers this rule).
- Check its `status`: `verified` / `divergent` / `missing` / `unsupported` / `legacy_verified`.
- If `verified`: confirm the `v2_evidence` still points to the correct source location and the `test_path` exists and passes.
- If `missing`: flag as gap...
- If `divergent`: read `divergence_note` and confirm the divergence is documented...
```

Then (lines 44-49) the agent's own output classification is a 4-value enum: `PARITY` / `DIVERGENT` /
`MISSING` / `UNDOCUMENTED`. **`PARITY` is the auditor's own output-table label, not a ledger `status`
value** — see "Parity Ledger Overlap" below for the exact mapping. Today "confirm ... `test_path`
exists and passes" is pure prose instruction — nothing enforces it; the agent could render `PARITY`
without ever running anything.

### `GATE-DET-PARITY-UPDATER`'s mapping module (`tools/gate_checks/parity_updater_static.py`) — what's actually reusable here

Read in full. Three functions:
- `derive_mapping(ledger_dir)` — scans every `v2_evidence` citation across `CANONICAL_LEDGER_FILES`
  (8 files; deliberately excludes `faction.yaml` — confirmed via `tools/parity_ledger_scan.py:24-33,41`)
  via regex `src/[\w\-./]+\.py`, building `{src_path: {ledger_filenames}}`.
- `expected_subsystems_for_files(files_changed, ledger_dir)` — filters to `src/` paths, returns
  `{src_path: sorted(candidates) | None}`.
- `cross_reference_touched(files_changed, touched_ledger_files, ledger_dir)` — diffs expected vs.
  actually-touched ledger files, returns PASS/FAIL/NA per file.

**What this ticket can and cannot reuse:** This module solves a different problem —
"which `src/` files should have caused a ledger touch." It has **zero test-execution logic** and
never reads `test_path` for the purpose of running it (only for building the `src_path` mapping via
citations found *in* `v2_evidence`, not `test_path`). The genuinely reusable piece for this ticket is
narrow: if `mechanics-auditor` is asked to audit an entire chapter/module (not a single named entry
ID), `expected_subsystems_for_files`/`derive_mapping` can help it discover *which ledger YAML file(s)*
correspond to the `src/` files it's about to compare against the Mechanics Bible — i.e., an optional
"which subsystem file to load entries from" helper. The actual new logic this ticket needs — (a)
does a given entry's `test_path` field exist and point to a real, invocable test, (b) run that one
test and report exit code — does not exist anywhere in `parity_updater_static.py` and must be written
fresh in `tools/gate_checks/mechanics_auditor_static.py`. Import `CANONICAL_LEDGER_FILES` from
`tools/parity_ledger_scan.py` (already the shared constant both `parity_updater_static.py` and
`done_checker_static.py`'s siblings reuse) rather than re-deriving the ledger file list.

### `docs/parity_ledger/schema.json` — what "PARITY verdict" actually means

`status` enum (schema.json:16-19): `["verified", "divergent", "missing", "unsupported", "legacy_verified"]`.
There is **no literal "PARITY" value anywhere in the schema.** The ticket's own title/scope wording
("For any PARITY verdict...") is the *auditor's own output classification*, and per
`mechanics-auditor.md`'s explicit mapping (lines 35-36: "If `verified`: confirm ... `test_path` exists
and passes"), a `PARITY` row in the auditor's output table is produced precisely when the underlying
ledger entry's `status` is `verified` **and** the auditor is affirming that status holds. So: the
new static check fires whenever `mechanics-auditor` is about to write `status: verified` → `PARITY`
in its output table for an entry — i.e., gate on ledger `status == "verified"`, not on any field
literally named "PARITY." (Schema also requires `test_path` for `status: divergent`, but the auditor's
prose only calls for a `test_path` check on the `verified` branch — flagging this as a minor internal
inconsistency in the agent prompt for the Planner to note, not something to silently "fix" by
guessing which is right.)

Schema also encodes (lines 44-49): `if status in [verified, divergent] then required: [v2_evidence, test_path]`.
This is a **structural requirement already in the schema** — but see Parity Ledger Overlap below for
how badly it's violated in practice today.

### `test_path` field format in the real ledger — this is the load-bearing finding for AC #4

Scanned all 9 files under `docs/parity_ledger/*.yaml` (1884 entries total across the 8 canonical
files; `faction.yaml` has 13 more, separately, all `status: verified`, all already in clean
`path.py::test_name` node-id format).

Aggregate counts (script run against all files, see the exact command used in this investigation):

| Metric | Count |
|---|---|
| Total entries (8 canonical files) | 1,884 |
| `test_path` is null/missing | 1,588 (84%) |
| — of which `status: verified` with **no** `test_path` | **1,352 / 1,644 verified entries (82%)** |
| `test_path` present, uses `::` node-id | 163 |
| `test_path` present, wrapped in literal backticks (part of the string value itself, not just Markdown rendering) | 49 |
| `test_path` present, comma- or `+`-joined multiple files in one string | 13 |
| `test_path` present, with a trailing parenthetical human annotation, e.g. `` `tests_v2/test_deterministic_baseline.py` (indirectly via `WorkerResult` and `EntityUpdate` flow) `` | 11 |

Critical, non-obvious sub-finding: **the `tests_v2/` directory referenced by most of the
backtick-wrapped legacy citations does not exist anywhere in the repo** (`ls tests_v2` →
`No such file or directory`). Those citations are stale by construction, independent of any string-parsing
work — the check must recognize this class and FAIL them cleanly, not attempt to "fix" the path.

A random sample of 10 clean-looking (`::`-containing, non-`tests_v2`) `test_path` values was checked for
on-disk existence of the file part: 9/10 existed; the 1 failure was a `+`-joined dual-file citation
(`"tests/unit/worldbuilding/test_quest_definition.py + tests/unit/worldbuilding/test_world_compiler.py"`)
where naive `split("::")` on the whole string produces a bogus concatenated path.

**Conclusion:** the new check cannot assume `test_path` is a directly-invocable pytest node-id. It
must, in order: (1) treat `None`/empty as a hard FAIL (per AC "non-null"); (2) strip enclosing
backticks and surrounding whitespace; (3) split on `,`/`;`/`+` if multiple citations are joined,
treating each as a separate sub-check (or explicitly picking a documented policy, e.g. "first
citation only" — this is a Planner decision, flagged as open below); (4) if what remains still
contains un-strippable trailing prose (parenthetical annotation not matching a `path[::name]` shape),
treat as unparseable and FAIL with an evidence message naming the raw string, never crash; (5) if the
resulting file path starts with `tests_v2/`, FAIL immediately with an explicit "legacy path, directory
does not exist" evidence message (cheap, no subprocess needed); (6) otherwise, run
`python3 -m pytest <parsed_path> -x -q` (a real file path or `file.py::test_name` node-id both work
unscoped-full-suite-free) and report exit code.

## Mechanics / Engine Constraints

This ticket touches process/tooling (`docs/ai/*`, `.claude/agents/mechanics-auditor.md`,
`tools/gate_checks/`), not simulation law — no `docs/mechanics/` chapter or `docs/engine/` contract
directly constrains the *logic* being added. The relevant constraint is procedural, from
`docs/parity_ledger/schema.json` itself (structure of `test_path`/`status`, described above), and from
this repo's own `CLAUDE.md` Hard Rules: "Do not break determinism" and "Do not leave changes untested
or untraceable" — both of which this ticket exists to serve (making an LLM verdict deterministically
checkable), not ones the implementation risks violating.

## Parity Ledger Overlap

No parity-ledger entry's `text` field describes agent/workflow tooling itself (the ledger only
tracks `src/` simulation-law parity, not meta-tooling about the ledger) — there is nothing to update
in `docs/parity_ledger/*.yaml` as a *result* of this ticket's own implementation. This ticket instead
**reads** the ledger's `status`/`test_path` fields as its target data.

Flag for the Planner (not a P0 gate on this ticket, but material to scope): **82% of currently
`status: verified` entries have no `test_path` at all**, which already violates
`docs/parity_ledger/schema.json`'s own `required: [v2_evidence, test_path]` constraint for that
status. This is squarely the established "legacy-data-scope" convention from
`GATE-DET-DONE-CHECKER` (do not investigate why; make the new check tolerate it gracefully, never
crash). The material design implication: if `mechanics-auditor` were ever run as a blanket audit over
the *entire* ledger, the vast majority of existing "PARITY" (verified) entries would immediately FAIL
the new check purely because they've always lacked a `test_path` — not because of any newly
introduced regression. The ticket's own scope wording ("given a parity-ledger entry ID **or a set of
entries mechanics-auditor is about to render a PARITY verdict for**") already implies a scoped
per-invocation check (only the entries actually under audit in the current session), not a
ledger-wide validator — this reading should be made explicit in `plan.md` so nobody mistakes a
narrow per-entry check for a full-ledger gate that would fail almost everything on day one.

## Prior Work

- `stored_artifacts/TCK-20260705-GATE-DET-DONE-CHECKER/` (DONE) — established the
  `tools/gate_checks/` module shape (plain functions, no CLI/argparse, `python3 -c "..."` invocation),
  the legacy-data-tolerance convention, and the `Step 0 — static pre-check` documentation pattern in
  `docs/ai/agents.md`.
- `stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/` (DONE) — shipped
  `tools/gate_checks/parity_updater_static.py`; confirmed general-purpose per its own module
  docstring ("so the sibling `GATE-DET-MECHANICS-AUDITOR` ticket can import it directly"), but as
  detailed above, only a narrow discovery helper is reusable, not the core test_path-verification logic.
- `tests/tools/test_parity_updater_static.py` and `tests/tools/test_done_checker_static.py` — model
  the coverage-honesty test structure (one fixture per check function proving it catches a real
  violation, using `tmp_path`-based fake ledger files, never touching the real `docs/parity_ledger/`).
- Both siblings' modules live in `tests/tools/` (not `tests/architecture/` — confirmed by directory
  listing) despite `SEQUENCE.md` mentioning `lane-architecture` only as a *rejected* home. New tests
  for this ticket should go in `tests/tools/test_mechanics_auditor_static.py` to match.

## Risks and Open Questions

1. **Multi-citation `test_path` policy is undecided.** ~13 entries cite more than one test file in a
   single string (comma or `+` joined). Does "the cited test_path" mean ALL joined citations must
   pass, or is checking the first one sufficient? Flag for Planner — do not guess; the ticket's AC
   doesn't address this explicitly, and choosing wrong either over- or under-verifies.
2. **Doc-update framing for the 3 shared docs is unresolved.** Because mechanics-auditor has no
   phase-table row in `workflows.md`/`system_overview.md`/`ticket-lifecycle.md` today (confirmed zero
   mentions), the AC's "3 shared docs updated" cannot literally mirror ticket 1/2's pattern (editing
   an existing phase-table cell) — it requires deciding *where* an ad hoc, non-pipeline agent's static
   pre-check gets documented in docs that are currently structured entirely around the 9-phase
   pipeline. Flag for Planner.
3. **Whether `mechanics-auditor.md`'s prompt-file edit is sufcient "wiring," or whether the workflow
   needs an actual `Agent(subagent_type: "mechanics-auditor")` call site added somewhere** (e.g., as
   an optional post-Parity-phase step) is a scope question the ticket's Assumptions section left open
   and this investigation only partially resolves: it confirms today's *ad hoc-only* invocation
   pattern, but does not decide whether this ticket should also *add* a new call site to
   `implement-ticket.js` (which would be new pipeline behavior, arguably beyond "wire a static
   pre-check into an existing agent") or leave invocation ad hoc and only harden the prompt file. This
   is exactly the kind of "conflict with existing system" the Clarification Rule calls out — the
   Planner/user should decide, not this investigation.
4. **The schema's own `if/then` for `divergent` status also requires `test_path`**, but
   `mechanics-auditor.md`'s prose only mentions checking `test_path` on the `verified` branch (line
   35-36), not explicitly on `divergent`. Minor prompt-file inconsistency; note but do not silently
   resolve.

## Anti-Drift Hazards

- **Do not build a ledger-wide validator.** Given the 82%-missing-test_path finding above, it would
  be easy to over-scope this into "audit every verified entry in the ledger," which would produce a
  wall of new FAILs unrelated to this ticket's actual goal (backstopping a *specific* PARITY verdict
  currently being rendered). Keep the check's entry point scoped to explicit entry ID(s) passed in.
- **Do not attempt to "fix" or "modernize" malformed `test_path` strings.** Stripping backticks and
  recognizing a `tests_v2/`-is-dead shortcut is in scope; rewriting/guessing corrected paths for the
  49 backtick or 11 parenthetical-annotation entries is not — report FAIL with the raw evidence
  string and move on, per the legacy-data-scope convention.
- **Do not fold this into `make lane-architecture`.** SEQUENCE.md decision 1 already settled this —
  `lane-architecture` is a `src/`-code architecture-guard lane (`Makefile:185`,
  `pytest tests/ -m "architecture"`), a different domain from agent-workflow-hygiene checks. Confirmed
  again here: no `gate_checks` reference exists anywhere in the `Makefile`.
- **Do not re-derive `CANONICAL_LEDGER_FILES`.** Import from `tools/parity_ledger_scan.py` (already
  the single source of truth `parity_updater_static.py` and `done_checker_static.py`'s siblings use).
- **`verified_by` field name and shape must match the established convention** (a flat list of
  strings, e.g. `["static:mechanics_auditor_static", "llm"]`) — do not invent a differently-shaped
  provenance field; both sibling agents already use this exact shape.
