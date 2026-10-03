---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER
artifact_type: plan
tags: [ai, workflows, determinism, architecture-reviewer]
---

# Implementation Plan — TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER

## Summary

Build `tools/gate_checks/architecture_reviewer_static.py` with 3 documented, deliberately-imperfect
check functions (durable-state mutation, raw-domain-object API exposure, reason/metadata
smuggling) plus an aggregator, each carrying an explicit precision/recall caveat per
investigation.md's findings. Because architecture-reviewer's *original* call site runs pre-Implement
against `plan.md` prose (no code exists yet to parse — investigation.md's Risk 1), wire the static
checks into a **new, second, unconditional post-Implement call site**: a new `Architecture-Verify`
phase in `.claude/workflows/implement-ticket.js`, inserted between Implement and Test, calling
`agentType: 'architecture-reviewer'` again with a prompt narrowly scoped to judging the static
checks' flagged items against the real diff (`implementation.files_changed`) — not re-reviewing the
whole plan. Reuses the existing `APPROVED`/`NEEDS_CHANGES`/`BLOCKED` vocabulary (no new status string,
per SEQUENCE.md decision 2) — a failure `return`s and ends the run for a fresh re-invocation, same as
every other gate in this file (there is no loop-back mechanism anywhere in `implement-ticket.js`;
corrected per architecture review round 1, see Step 5). The new phase's
own schema (`ARCH_VERIFY_SCHEMA`, necessarily a distinct JS identifier from the existing
`REVIEW_SCHEMA`) gains `verified_by`, satisfying the AC's intent even though the literal constant
name differs from the ticket text (documented below, not an open question). No new parity ledger
entry (this is agent-workflow tooling, matching the 3 DONE siblings' precedent). Every check function
is built to tolerate legacy/unparseable input gracefully (never crash the gate it backstops) and is
honest in its own docstring about what it cannot see, per the ticket's explicit preference for a
narrow, disclosed-limitations design over an ambitious, unreliable one.

## Steps

### Step 1 — Durable-state-mutation check function

**Files:** `tools/gate_checks/architecture_reviewer_static.py` (new)

**Change:** Add `check_durable_state_mutation(file_path: str, source: str) -> tuple[str, str]`
(`(status, evidence)`, status one of `PASS`/`FAIL`/`SKIP`). Parse `source` with `ast.parse`; wrap the
whole function body in `try/except SyntaxError` → return `("SKIP", "unparseable: <error>")` on
failure (never raise — mirrors `parity_updater_static.derive_mapping`'s `except Exception: continue`
convention, applied per-file here since this check is file-scoped, not corpus-scoped).

Walk the AST for three independent violation shapes, and FAIL (with a `file:line` citation in
evidence) if any is found; PASS otherwise:

1. **`object.__setattr__` bypass outside the field-name allowlist.** Match `ast.Call` nodes where
   `func` is `Attribute(value=Name(id='object'), attr='__setattr__')` with 3 positional args; extract
   the literal field-name string (2nd arg, if it's an `ast.Constant` str — skip/ignore non-literal
   field names, do not guess). FAIL unless the field name matches `_ALLOWLISTED_SETATTR_FIELDS`:
   - a name ending in `_cache` (the confirmed `src/engine/apply.py` `replace()` convention), OR
   - a literal in the named-exception set mined from investigation.md's grep:
     `{"_index_hits", "_index_misses", "world_indexes", "transient_claims", "occupancy_snapshot",
     "_opt_profile", "_force_full_scan"}`.
   This is **field-name-based only, never path-based** — confirmed no `src/engine/authoritative_pipeline*`
   path exists (investigation.md), and two legitimate call sites
   (`src/world/environment.py:87`, `src/systems/strategic_systems/intelligence.py:240`) are outside
   `src/engine/` entirely, so a directory-prefix test would misfire on them.
   Before finalizing this list, re-grep `object\.__setattr__` across `src/` (excluding tests) and
   confirm each of the ~13 known call sites' actual field name resolves via one of the two buckets
   above; if `src/simulation_quality/weights.py`'s `ScoringWeights` call site uses a field name that
   matches neither bucket, add that literal name to the named-exception set (this file's exact field
   name was not captured in investigation.md and must be confirmed at implementation time).

2. **Nested mutable-container mutation by field-name heuristic.** Match two shapes:
   - `ast.Assign`/`ast.AugAssign` where the target is `ast.Subscript` whose `.value` is an
     `ast.Attribute` with `.attr` in `_KNOWN_MUTABLE_CONTAINER_FIELDS`.
   - `ast.Call` where `func` is `ast.Attribute` with `.attr` in a mutating-method set
     (`{"append", "extend", "insert", "remove", "pop", "popitem", "update", "clear", "sort", "add",
     "discard"}`) and `func.value` is itself `ast.Attribute` with `.attr` in
     `_KNOWN_MUTABLE_CONTAINER_FIELDS`.
   `_KNOWN_MUTABLE_CONTAINER_FIELDS = {"items", "global_resources", "trust_history"}` — a short,
   explicitly-incomplete list mined from `src/core/models/inventory.py:42`
   (`InventoryComponent.items`) and `src/core/state.py:1124` (`AuthoritativeState.global_resources`);
   the module docstring must state this list requires manual extension as new mutable state fields
   are added, and that name-only matching cannot distinguish `entity.inventory.items` from an
   unrelated object's `.items` attribute (false positives are expected and accepted, per
   investigation.md's "highest-value, hardest-to-catch" framing).

3. **Direct nested attribute assignment** (`entity.combat.hp = 5` — no `object.__setattr__`,
   would already raise `FrozenInstanceError` at runtime on a real frozen dataclass). Match
   `ast.Assign`/`ast.AugAssign` where the target is `ast.Attribute` and `target.value` is itself
   `ast.Attribute` (i.e., an attribute-of-attribute chain, depth ≥ 2) — FAIL unconditionally (no
   allowlist; this pattern has no sanctioned legitimate use in the codebase's own convention). The
   module docstring must disclose this catches the pattern *before* a test run, not a bug that would
   otherwise ship — the runtime already guards it on every actual frozen dataclass.

**Do NOT touch:** No directory-prefix / `src/engine/` path test anywhere in this function — confirmed
nonexistent target path. Do not attempt type inference to resolve `.items` to
`InventoryComponent.items` specifically — out of scope per investigation.md (no such thing in plain
`ast`).

**Verify:** `test_flags_setattr_bypass_outside_allowlist_on_non_cache_field`,
`test_does_not_flag_cache_suffix_setattr`, `test_does_not_flag_allowlisted_call_site_outside_src_engine`,
`test_flags_mutable_container_mutation_by_known_field_name`,
`test_does_not_crash_on_unrelated_attribute_with_same_name`,
`test_direct_attribute_assignment_on_frozen_field_is_flagged`,
`test_tolerates_unparseable_python_fixture` (all in `tests/tools/test_architecture_reviewer_static.py`).

---

### Step 2 — Raw-domain-object API-boundary check function

**Files:** `tools/gate_checks/architecture_reviewer_static.py`

**Change:** Add `_collect_domain_class_names(base_dir: Path = Path(".")) -> set[str]`: `ast.parse`
each of `src/core/state.py`, `src/core/strategic.py`, `src/core/self_model.py`, and every
`src/core/models/*.py` file, collecting every module-level `ast.ClassDef.name`. Skip a file silently
(no raise) if it doesn't exist or fails to parse — same legacy-data tolerance as Step 1. This is
**dynamically derived, not a hand-maintained list** — mirrors `parity_updater_static.derive_mapping`'s
own "read the real source of truth at call time" convention, avoiding a second hardcoded list that
drifts from the actual domain model as classes are added/renamed.

Add `check_api_boundary_exposure(file_path: str, source: str, domain_class_names: set[str]) ->
tuple[str, str]`. Only applies when `file_path` is under `src/api/` (caller's responsibility to filter
— see Step 3's aggregator). `ast.parse(source)` (same try/except-SKIP tolerance). Walk top-level
`FunctionDef`/`AsyncFunctionDef` nodes (module scope only — do not descend into nested/inner
functions):
- Skip (do not include in scan at all) any function whose `name` starts with `_` — confirmed real
  example `src/api/routes/decisions.py:_get_index` must never be flagged (private helper, never a
  registered route handler).
- If `returns` is `None` (no return annotation): `("SKIP", "no return annotation — cannot statically
  verify")` for that function — never a silent `PASS`, per the ticket's own AC wording that a flagged
  item must be addressed *or explained*, and per test_plan.md's requirement that unannotated handlers
  are visibly unchecked, not indistinguishable from clean.
- If the annotation (unwrap `ast.Subscript`/`ast.Attribute` to get the base name, e.g. `Dict[str,
  Any]` → `Dict`) is `Dict` or a bare `Name`/`Attribute` ending in `Response` → `PASS`.
- If the annotation's base name is in `domain_class_names` → `FAIL`, citing `file:line:function_name`.
- Otherwise (an annotation that's neither a known raw domain class nor a recognized shaped-response
  shape — e.g. `str`, `bool`, some other type) → `PASS` (this check's job is to catch raw domain
  model exposure specifically, not to enforce every handler use `Dict`/`*Response`; do not
  over-reach the ticket's stated scope).

Aggregate per-file result: `FAIL` if any function-level check is `FAIL`; else `PASS` if at least one
function was checkable; else `SKIP` if every function was unannotated.

**Do NOT touch:** Do not flag `src/api/presenters/*.py`'s own `present_*` methods for taking a raw
domain object as an *input* parameter — the check only inspects return annotations, never parameter
annotations (the presenter convention explicitly uses raw types as input, confirmed clean in
investigation.md).

**Verify:** `test_flags_route_returning_raw_domain_model_directly`,
`test_does_not_flag_presenter_or_response_return_types`,
`test_does_not_flag_private_helper_returning_raw_model`,
`test_does_not_flag_or_crash_on_unannotated_handler`.

---

### Step 3 — Reason/metadata-smuggling regex check function

**Files:** `tools/gate_checks/architecture_reviewer_static.py`

**Change:** Add `check_reason_metadata_smuggling(file_path: str, source: str) -> tuple[str, str]`.
Text/regex-based (not AST — matches the ticket Scope's own "regex check" framing), operating directly
on `source`:

1. Find candidate "packed" assignments: a regex matching an f-string or `.join(...)` call assigned to
   a name/key containing `reason` or `metadata` (case-insensitive), where the string literal/f-string
   contains **2 or more** `{...}` placeholders (or, for `.join`, 2+ comma-separated join-items)
   separated by a **non-alphanumeric delimiter character** (e.g. `f"{a}|{b}|{c}"`,
   `"|".join([a, b, c])`).
2. Find a candidate "unpacking" call elsewhere in the same file: `.split(<same delimiter char>)` (or
   `.split()` with no args, if the packed side used whitespace).
3. FAIL only if both (1) and (2) are found in the same file (the delimiter-pack-then-later-split
   round-trip is the actual signature this check targets, per test_plan.md's
   `test_flags_delimiter_joined_reason_field`); otherwise PASS.

The module or function docstring **must** state explicitly, in plain language: *this check's patterns
are derived from CLAUDE.md's Durable State Rule prose, not from any confirmed historical incident —
investigation.md searched `git log`, `tickets/done/`, `docs/archive/`, and all 31 recorded
`NEEDS_CHANGES`/`BLOCKED` architecture-review verdicts in `agent-monitoring/events.jsonl` and found
zero real instances of this exact pattern.* This is the weakest-evidenced of the three checks and
must carry the strongest disclosed caveat (per investigation.md Risk 4).

**Do NOT touch:** Do not flag the real, confirmed-clean `src/lab/workflows.py:1176` pattern
(`return {"status": "BLOCKED", "reason": f"Malformed or unparseable run manifest: {e}"}`) — a single
interpolated diagnostic value is not a multi-value pack; the ≥2-placeholder-with-delimiter condition
must exclude it.

**Verify:** `test_flags_delimiter_joined_reason_field`,
`test_does_not_flag_plain_human_readable_reason_string`, `test_docstring_discloses_no_incident_corpus`.

---

### Step 4 — Aggregator function

**Files:** `tools/gate_checks/architecture_reviewer_static.py`

**Change:** Add `run_architecture_checks(files_changed: list[str], base_dir: Path = Path(".")) ->
list[dict]`. For each path in `files_changed` ending in `.py` and starting with `src/` (skip
everything else silently — docs/tests/config changes are not this check's concern):
- Read the file's current on-disk content via `base_dir / path` (try/except `OSError` → one `SKIP`
  entry with evidence noting the file could not be read, e.g. deleted in a later commit within the
  same diff — never raise).
- Always run `check_durable_state_mutation` → one dict `{"condition": f"durable_state_mutation:{path}",
  "status": ..., "evidence": ...}`.
- Always run `check_reason_metadata_smuggling` → one dict
  `{"condition": f"reason_metadata_smuggling:{path}", "status": ..., "evidence": ...}`.
- If `path.startswith("src/api/")`, additionally call `_collect_domain_class_names(base_dir)` once
  (cache the result across the loop — do not re-parse the domain-source files per API file) and run
  `check_api_boundary_exposure` → one dict `{"condition": f"api_boundary_exposure:{path}", ...}`.

Return the flat `list[dict]` (matches the `condition`/`status`/`evidence` shape of
`done_checker_static.run_static_precheck` — the closest structural sibling, since this is a
per-condition checklist rather than a per-file cross-reference like `parity_updater_static`).

**Do NOT touch:** Do not add a CLI/`argparse` entry point — consumed exclusively via `python3 -c
"..."` from `implement-ticket.js`'s new `bash()` call, per SEQUENCE.md decision 1.

**Verify:** `test_run_all_returns_list_of_condition_status_evidence_dicts`.

---

### Step 5 — Wire the new `Architecture-Verify` phase into `implement-ticket.js`

**Files:** `.claude/workflows/implement-ticket.js`

**Change:** Insert a new phase between the end of the Implement phase (after the existing
`pushEvent('Implement', ...)` call, currently the line immediately before `// ─── Phase 6: Test`)
and `phase('Test')`. Gate the whole new phase on `tier !== 'hotfix'` — hotfix's own Tier Routing
pipeline (`Scope → Implement → Test → Parity → Verify → Finalize`) already omits the entire
architecture-review concern by design (the existing pre-Implement Review phase is likewise skipped
for hotfix at line ~421-426); Architecture-Verify is the same concern, post-Implement, so the same
tier exclusion applies for consistency. Push a `skipped` event in the `else` branch, matching the
existing hotfix-skip pattern for Review/Investigate/Plan.

Structure (mirrors the Parity phase's pre-agent `bash()` + post-agent JSON-marker-prefix parsing
pattern at lines ~561-570 and ~632-649):

1. Build `filesChangedArgs` from `implementation.files_changed` (individually shell-quoted argv
   elements — never JSON-embedded in the `-c` string, per the Parity phase's own documented
   shell-quoting hazard).
2. `await bash(...)` running `python3 -c "..."` that imports
   `tools.gate_checks.architecture_reviewer_static.run_architecture_checks`, calls it with
   `sys.argv[1:]`, and prints `'ARCH_CHECK_JSON:' + json.dumps(result)`.
3. Parse the output via the `ARCH_CHECK_JSON:` marker-prefix + `try/catch` → `null` on parse failure
   (mirrors Parity's `PARITY_CHECK_JSON:` handling — no established contract that raw `bash()` output
   is safe for a bare `JSON.parse()`).
4. Define `ARCH_VERIFY_SCHEMA` (new identifier, distinct from the existing `REVIEW_SCHEMA` at line
   ~361 — both must coexist in the same script scope): `required: ['verdict', 'violations',
   'summary']`, properties `verdict` (enum `APPROVED`/`NEEDS_CHANGES`/`BLOCKED` — same vocabulary as
   `REVIEW_SCHEMA`, no new status string), `violations` (array of strings), `summary`, `ts`, and
   `verified_by` (array of strings, e.g. `["static:architecture_reviewer_static", "llm"]`) — this is
   where the AC's "`REVIEW_SCHEMA` gains a `verified_by` field" is actually realized (see Anti-Drift
   Notes below for why the literal constant name differs from the AC text).
5. `await agent(...)` with `agentType: 'architecture-reviewer'` (same agent identity as the original
   Review call — "one agent owns the concern end-to-end"). Prompt must:
   - Include the standard `Step 0`/`Step 0b` timestamp + run-registration boilerplate (copy verbatim
     from the adjacent Parity/Security-Review prompts).
   - Inject the parsed static-check results verbatim (or `'UNPARSEABLE — treat as inconclusive, do
     not silently pass'` if parsing failed).
   - Inject `implementation.files_changed`.
   - Explicitly state this is a **narrow verification, not a full re-review**: judge only the flagged
     item(s) (if any) by reading the actual file/line, decide real-violation vs. false-positive (with
     stated reason), and do **not** re-litigate strategic/tactical/abstraction-premature soundness —
     that was already judged `APPROVED` in the pre-Implement Review phase.
   - Request the same return shape as `ARCH_VERIFY_SCHEMA`.
6. **On `archVerify.verdict !== 'APPROVED'`** (revised per architecture review round 1, CONFIRMED
   finding): log verdict + violations, `pushEvent('Architecture-Verify', 'architecture-reviewer',
   'failed', ...)`, `await writeMonitoring(archVerify.verdict)`, and `return` a failure-shape object —
   but **do not describe this as "reusing the existing loop-back-to-Implement behavior."** Confirmed
   by grepping the whole file for `while|for (|recursi|loop|goto`: there is no loop-back mechanism
   anywhere in `implement-ticket.js`, for any phase. Every gate's `NEEDS_CHANGES`/`BLOCKED` `return`
   **ends the entire run** — the human must re-invoke with `ticket_id` to resume (confirmed by
   `docs/ai/agents.md:104`, "the workflow **halts**... re-run," and `docs/ai/ticket-lifecycle.md`'s own
   diagram). The original Review phase's `return` (lines 404-417) uses the message
   `'Fix violations in staging_artifacts/' + tid + '/plan.md then re-run...'` — this is **wrong for
   Architecture-Verify**, since by the time this new phase runs, `plan.md` has already been executed;
   the actual violation is in the written code. **Mirror `Security-Review`'s remediation phrasing
   instead** (the correct sibling template — also a post-Implement re-invocation of a reviewer-type
   agent, per `docs/ai/ticket-lifecycle.md` line 72: "human fixes **code**, re-run with ticket_id"):
   `message: 'Fix the flagged code in the files changed for ' + tid + ', then re-run with ticket_id="' + tid + '".'`
7. On `APPROVED`: `pushEvent('Architecture-Verify', 'architecture-reviewer', 'ok', ...)`, log, fall
   through to `phase('Test')` as today.
8. **Update the in-file `meta` block** (lines 1-16, at the top of `implement-ticket.js` — revised per
   architecture review round 1, CONFIRMED finding: this was never scheduled for update, but
   `Security-Review` — an existing conditional phase — **is** listed there at line 12, establishing
   that conditional phases belong in this array too). Add one entry to `meta.phases` for
   `Architecture-Verify`, mirroring `Security-Review`'s conditional-phrasing style: `{ title:
   'Architecture-Verify', detail: 'Post-Implement deterministic backstop for architecture-reviewer's
   durable-state/API-boundary/reason-metadata rules — re-invokes architecture-reviewer against the
   actual diff (skipped for hotfix)' }`, inserted between the existing `Implement` and `Test` entries
   (matching the phase's actual execution order — confirm exact array position at implement time).
   Also update the top-level `description` string (line 3) to include
   this phase in the pipeline summary.

**Do NOT touch:** Do not modify the existing pre-Implement `phase('Review')` block (lines ~359-426)
at all — it keeps reviewing `plan.md` exactly as today, with its own unmodified `REVIEW_SCHEMA`. Do
not fold this into the Security-Review phase (lines ~668-716) — confirmed conditional on
`tags.includes('security')`, a different, narrower concern (injection/secrets/path-traversal), and
folding would mean these checks almost never run.

**Self-reference note (architecture review round 1, disclosed, not a defect):** This ticket's own
Implement phase edits `implement-ticket.js` to add the new phase, but the workflow script executing
*this ticket's own* run was already loaded/parsed before Implement's edits land — so this ticket's own
implementation run will NOT exercise the new Architecture-Verify phase against itself; it proceeds
straight from Implement to Test as today, same as every prior sibling ticket. The first ticket to
actually trigger a second `architecture-reviewer` call per run will be some future ticket, not this
one. Note this in Step 6/7's doc updates so a future reader isn't confused by this ticket's own run
history showing no second call.

**Verify:** No automated JS test exists in this repo (confirmed absent by all 3 DONE siblings and by
test_plan.md) — verification is manual/structural review of the diff, consistent with established
precedent. Confirm via direct inspection: (a) the phase fires for `tier !== 'hotfix'` only, (b) the
`bash()` call happens before the `agent()` call, (c) the schema/status vocabulary matches
`REVIEW_SCHEMA`'s enum exactly, (d) hotfix path still pushes a `skipped` event.

---

### Step 6 — Update `.claude/agents/architecture-reviewer.md`

**Files:** `.claude/agents/architecture-reviewer.md`

**Change:** Add a new section, `## Post-Implementation Verification (Architecture-Verify phase)`,
after the existing `## Output` section, describing: this agent is invoked a second time per ticket,
post-Implement, with the static-check JSON output from
`tools/gate_checks/architecture_reviewer_static.py` already injected into the prompt; in this mode,
judge only the flagged item(s) against the real changed files (not the whole plan again); return the
same `APPROVED`/`NEEDS_CHANGES`/`BLOCKED` vocabulary plus a `verified_by` field self-reporting which
findings came from the static script vs. independent judgment. State plainly, in this new section,
each of the three checks' disclosed limitations (field-name-heuristic container-mutation check,
annotation-blind API-boundary check, zero-incident-corpus reason/metadata check) so the agent does
not over-trust a `PASS` from the script.

Also add one disclosure sentence noting the self-reference bootstrapping case (architecture review
round 1): "This ticket's own implementation run does not exercise this new phase against itself — the
workflow script executing this ticket's own run was already loaded before its own edits landed; the
first ticket to trigger a real second `architecture-reviewer` call will be a future ticket."

**Do NOT touch:** The existing `## What to Review` / `## Output` sections (pre-Implement mode)
— unchanged.

**Verify:** Manual review — confirm the new section exists and cites the correct module path.

---

### Step 7 — Update the 4 shared docs

**Files:** `docs/ai/agents.md`, `docs/ai/workflows.md`, `docs/ai/system_overview.md`,
`docs/ai/ticket-lifecycle.md`

**Change:**
- `docs/ai/agents.md`: in the existing `### \`architecture-reviewer\`` section (lines 87-105), add a
  `**Step 0 — static pre-check (post-Implement only):**` paragraph mirroring the `done-checker`/
  `parity-updater` sections' phrasing exactly (see lines 108-136, 188-199 for the established
  template): names the module (`tools/gate_checks/architecture_reviewer_static.py`), the entry point
  (`run_architecture_checks(files_changed)`), when it runs (a second, post-Implement call — not the
  original pre-Implement call, since no code exists yet at that point), and that the agent
  self-reports provenance via `verified_by`.
- `docs/ai/workflows.md`: in the `implement-ticket` phase table (lines 78-89), add a new row
  `| Architecture-Verify | \`architecture-reviewer\` | Second, post-Implement call; runs
  \`tools/gate_checks/architecture_reviewer_static.py::run_architecture_checks\` before the agent call
  and injects its JSON output; narrowly scoped to judging flagged items, not re-reviewing the plan;
  stops if NEEDS_CHANGES or BLOCKED (same vocabulary as Review) |` immediately after the `Implement`
  row and before `Test`.
- `docs/ai/system_overview.md`: update the phase-chain prose (lines 77-97) to insert
  `→ Architecture-Verify (\`architecture-reviewer\`, 2nd call, gate: NEEDS_CHANGES/BLOCKED)` between
  `Implement` and `Test`; update the hotfix Tier Routing row's pipeline text only if it currently
  lists phases explicitly enough to need it (confirm at implementation time — the hotfix row already
  omits Review, so it should continue to omit Architecture-Verify too, no text change needed there).
- `docs/ai/ticket-lifecycle.md`: add an `[Architecture-Verify]` block to the phase-by-phase ASCII
  diagram (mirroring the existing `[Review]`/`[Implement]`/`[Parity]` blocks around lines 52-70) plus
  a new `### Architecture Verify` prose subsection (mirroring `### Parity`/`### Security-Review`'s
  structure around lines 265-290) describing inputs/outputs/gate behavior.

**Do NOT touch:** `mechanics-auditor`'s section/rows in any of these 4 docs — untouched by this
ticket (sibling, already DONE).

**Verify:** Manual review — no automated doc test exists in this repo; consistency confirmed by
re-reading all 4 files after editing and checking cross-references match.

---

### Step 8 — Coverage-honesty test suite

**Files:** `tests/tools/test_architecture_reviewer_static.py` (new)

**Change:** Implement every test named in test_plan.md (17 tests across 4 groups), importing directly
from `tools.gate_checks.architecture_reviewer_static` (mirror
`tests/tools/test_parity_updater_static.py`'s `sys.path` bootstrap and `_write_ledger`-style inline
fixture-writing convention — here, `tmp_path.write_text(...)` per test, no checked-in static fixture
files). No pytest marker (must not be discovered by `pytest tests/ -m "architecture"` /
`make lane-architecture`, per SEQUENCE.md decision 1 and test_plan.md's explicit negative-control
requirement).

**Do NOT touch:** `tests/tools/test_done_checker_static.py`, `test_parity_updater_static.py`,
`test_mechanics_auditor_static.py`, or `tools/gate_checks/__init__.py` (currently empty — no change
needed; the new module is a sibling addition, not a package-init change).

**Verify:**
```
pytest tests/tools/test_architecture_reviewer_static.py -v
pytest tests/tools/ -v
pytest tests/ -m "architecture" -v   # confirm zero collected tests from the new file
```

---

## Scope Guards

- Do not touch the other 3 gates' static verifiers (`done_checker_static.py`, `parity_updater_static.py`,
  `mechanics_auditor_static.py`) or their tests — sibling tickets, already DONE.
- Do not re-decide `status: verified`/`divergent` semantics, Mechanics Bible compliance judgment, or
  strategic/tactical boundary soundness — all remain LLM-judged, unchanged, per ticket Out of Scope.
- Do not attempt to achieve high precision/recall on any of the 3 checks — an honest, narrow, first
  version is the explicit target; do not add type inference, multi-file cross-reference, or an
  incident-corpus mining pass beyond what investigation.md already gathered.
- Do not add token/cost telemetry (SEQUENCE.md decision 5, out of scope for all 4 tickets).
- Do not fold the new checks into the Security-Review phase, and do not modify Security-Review's
  schema or prompt at all.
- Do not modify the original pre-Implement `REVIEW_SCHEMA`/Review-phase prompt at lines ~359-426 of
  `implement-ticket.js` — it is untouched; only a new, second phase is added.
- Do not add a new parity ledger entry — this is agent-workflow tooling, not simulation-behavior
  verification (matches all 3 DONE siblings' precedent; `INFRA-204` stays untouched).
- Do not add a CLI/`argparse` interface to the new module.
- Do not assume `src/engine/authoritative_pipeline*` exists as a path anywhere in the new module or
  its docstrings — confirmed nonexistent.

## Dependency Map

- Steps 1-4 (the module's 3 check functions + aggregator) are independent of Step 5 (JS wiring) and
  can be implemented/tested in isolation first.
- Step 5 (JS wiring) depends on Step 4 (aggregator's exact function signature/output shape) existing
  first, so the `bash()` call's import path and JSON shape are correct.
- Step 6 (agent role-prompt doc) and Step 7 (shared docs) depend on Step 5's actual phase name/schema
  field names being final, so the doc text describes the real wiring, not a guess.
- Step 8 (tests) depends on Steps 1-4 (the functions must exist to test against) but is independent of
  Steps 5-7.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `tools/gate_checks/architecture_reviewer_static.py` exists with 3 documented check functions, each with an explicit, disclosed precision/recall caveat | Steps 1, 2, 3 | `test_*` in `tests/tools/test_architecture_reviewer_static.py` (all groups) |
| The Review phase's prompt instructs architecture-reviewer to run these checks first and address any flagged item, or explain why a flagged item is a false positive | Step 5 (realized as the new Architecture-Verify phase's prompt, not the original pre-Implement Review prompt — see Anti-Drift Notes) | Manual review of `implement-ticket.js` diff |
| `REVIEW_SCHEMA` gains a `verified_by` field | Step 5 (`ARCH_VERIFY_SCHEMA`, the new phase's schema — see Anti-Drift Notes for the naming reconciliation) | Manual review of `implement-ticket.js` diff |
| At least one coverage-honesty test per check function, including a clean-fixture negative control | Step 8 | All tests in `tests/tools/test_architecture_reviewer_static.py` |
| `docs/ai/agents.md`'s `architecture-reviewer` section and the other 3 shared docs updated | Steps 6, 7 | Manual review |

## Anti-Drift Notes

- **AC-wording reconciliation (decided here, not a design ambiguity):** the ticket's AC text says
  "`REVIEW_SCHEMA` gains a `verified_by` field," written before this Plan resolved *where* the check
  runs. Since the check now runs in a **new, second** phase (per the orchestrating session's
  resolution #1), it needs its own schema constant — `ARCH_VERIFY_SCHEMA` — because JS cannot have two
  `const` declarations named `REVIEW_SCHEMA` in the same script scope, and the *original*
  pre-Implement `REVIEW_SCHEMA` has nothing to verify against (no code exists yet at that point, so a
  `verified_by` field there would always read `["llm"]` and add no signal). `ARCH_VERIFY_SCHEMA`
  gaining `verified_by` is the correct, intent-preserving realization of this AC line. Do not
  "fix" this by adding a no-op `verified_by` to the original `REVIEW_SCHEMA` — that would satisfy the
  AC's literal text while adding zero real signal, which is the failure mode the whole gate-determinism
  initiative exists to close.
- **Field-name allowlist, not path allowlist:** every part of Step 1's `object.__setattr__` check must
  stay field-name-based. The single most important regression guard in this ticket
  (test_plan.md's own framing) is that `test_does_not_flag_cache_suffix_setattr` and
  `test_does_not_flag_allowlisted_call_site_outside_src_engine` both stay green — if a future edit
  reintroduces a directory-prefix test, both will start failing (or worse, silently stop verifying
  what they claim to).
- **The container-mutation heuristic is intentionally incomplete** — do not expand
  `_KNOWN_MUTABLE_CONTAINER_FIELDS` speculatively beyond what's mined from real `src/core/state.py`/
  `src/core/models/inventory.py` fields; do not attempt type resolution to close the
  same-attribute-name-different-object false-positive gap (`test_does_not_crash_on_unrelated_attribute_with_same_name`
  documents this gap is expected to remain, not to be fixed).
- **The API-boundary check is blind to unannotated handlers** — `test_does_not_flag_or_crash_on_unannotated_handler`
  must assert `SKIP`/unchecked, never a silent `PASS` masquerading as "verified clean." Do not use
  runtime introspection or a live import to infer an actual return type for unannotated functions —
  explicitly out of scope (a static-only `ast` pass per the ticket's Scope text).
- **The reason/metadata check has zero incident-corpus grounding** — its docstring's disclosure
  language must not be softened in a later edit without also updating
  `test_docstring_discloses_no_incident_corpus`; this is the weakest-evidenced of the three checks and
  must stay visibly labeled as such.
- **Legacy-data tolerance throughout:** every function that parses a file (`ast.parse` in Steps 1-2)
  must catch `SyntaxError`/`Exception` and return a non-crashing `SKIP` status, never propagate an
  exception up through `run_architecture_checks` — this check runs against the full set of changed
  `src/` files on every ticket, including any that might be malformed, and must never crash the gate
  it backstops.
- **Hotfix tier skip:** Architecture-Verify must be skipped for `tier === 'hotfix'`, consistent with
  the existing Review-phase skip and the Tier Routing table's hotfix pipeline (`Scope → Implement →
  Test → Parity → Verify → Finalize` — no review phase at all). This was inferred from existing
  pattern per the Clarification Rule ("Otherwise, follow existing patterns"), not one of the two
  pre-resolved open questions — flagging it here for visibility, not as unresolved.

## Deviations (recorded during Implement)

1. **Step 1's named-exception set gained 2 entries beyond the 6 explicitly listed above.** As this
   Plan itself instructed ("Before finalizing this list, re-grep `object\.__setattr__` across `src/`
   ... if `src/simulation_quality/weights.py`'s `ScoringWeights` call site uses a field name that
   matches neither bucket, add that literal name"), the implementer re-grepped and confirmed
   `weights.py` uses `_flat_rules` and `_pillar_weights` (neither `_cache`-suffixed) — both added to
   `_ALLOWLISTED_SETATTR_FIELDS`. This is confirmation of an already-anticipated gap, not a new
   deviation in spirit, but is recorded here since it changes the literal set contents from what was
   drafted above.

2. **A real false positive was found and fixed that this Plan did not anticipate.** Step 1 point 3
   ("direct nested attribute assignment... FAIL unconditionally (no allowlist; this pattern has no
   sanctioned legitimate use in the codebase's own convention)") is contradicted by real production
   code: `src/lab/workflows.py`'s `_validate_scenario`/`_validate_experiment` methods configure
   `MagicMock` instances via `mock_world_repo.list_worlds.return_value = [...]`, an AST shape
   identical to `entity.combat.hp = 5`. The implementer added a narrow, evidence-driven exception —
   `_MOCK_CONFIGURATION_ATTRS = {"return_value", "side_effect"}` — rather than following the
   unconditional rule as literally drafted, since doing so would have produced a demonstrable,
   avoidable false positive on real, current, correct code the very first time this check is run
   against that file. Disclosed in the function's docstring and covered by a new regression test
   (`test_does_not_flag_mock_return_value_configuration`).

3. **The docstring's disclosed-limitation language for the `object.__setattr__`/nested-assignment
   false-positive gap was broadened beyond the two files named above** (`src/engine/apply.py`,
   `src/core/state.py`) after the implementer additionally confirmed the same false-positive shape
   recurs in `src/engine/kernel.py` (direct nested attribute assignment on its own
   `_status.current_tick_violations`-style internal fields) and
   `src/engine/pipeline_phases/actions.py` (`object.__setattr__(sliding_state, "entities", ...)`
   sliding-window rebuild). No allowlist expansion was made for either file — per this Plan's own
   "do not attempt high precision/recall" instruction and Anti-Drift Notes — only the docstring text
   was widened so the disclosed limitation matches what was actually observed against the real
   repository, not just the two files this Plan happened to name.

None of the above required re-litigating the check design, the JS wiring, the schema field names, or
any Acceptance Criterion — all fall within "Investigate must scope realistic precision/recall before
committing to a specific AST pattern set" and "a first version that catches only the clearest
violations... is preferable to an over-ambitious one that's unreliable," both already agreed in this
Plan and the ticket's own Scope text.

