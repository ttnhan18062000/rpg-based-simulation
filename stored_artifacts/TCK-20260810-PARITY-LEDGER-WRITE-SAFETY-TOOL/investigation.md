---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL
artifact_type: investigation
tags: [ai, agent-monitoring, process-improvement]
---

# Investigation — TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL

## Current Behavior

**`tools/parity_index.py`** (module docstring, lines 1-44) is a read-only importer. Lines 10-12
state explicitly, twice: "It never writes into `docs/parity_ledger/` and implements no mutation
CLI (`\"build\"` is the only subcommand that writes anything, and only to the derived database)."
Confirmed directly, not assumed — `main()` (line 711) only registers five subparsers: `build`,
`entry`, `impact`, `health`, `check-staleness` (lines 717-750), none of which touch
`docs/parity_ledger/*.yaml`. This is further defended by two architecture-guard tests in
`tests/tools/test_parity_index.py`:
- `test_no_mutation_cli_or_write_path_to_docs_parity_ledger` (line 535) — asserts no
  `open(..., "w")`/`.write_text(...)` call in the source targets `docs/parity_ledger`.
- `test_health_subcommand_never_writes_to_docs_parity_ledger` (line 548) — behavioral proof via a
  real build+health run, hashing shard bytes before/after.

Adding a mutation CLI directly inside `parity_index.py` would both contradict its own documented
contract and break `test_no_mutation_cli_or_write_path_to_docs_parity_ledger`'s literal
static-source assertion.

**`tools/parity_ledger_scan.py`** — `find_p0_intersection` (line 36) globs the 8
`CANONICAL_LEDGER_FILES` (line 24, `faction.yaml` excluded) and does `yaml.safe_load(path.read_text())`
at line 49 with **no `try`/`except`** around the parse. `docs/ai/parity_readpath_gate_a_decision.md`
§6.3 confirms this raises an uncaught `yaml.YAMLError` on a malformed shard — a real, disclosed,
previously-unfixed fragility.

**`tools/gate_checks/parity_updater_static.py`** — `derive_mapping` (line 39) is the read-side
deterministic mapping consumer; it wraps its own `yaml.safe_load` in a bare `except: continue`
(line 55-56), silently skipping malformed shards — a **different** behavior from both
`find_p0_intersection`'s crash and `parity_index.py`'s labeled `ShardParseError` abort. Three
distinct behaviors for the same input shape, exactly as §6.3 documents. Nothing in this module
writes to `docs/parity_ledger/`.

**`.claude/agents/parity-updater.md`** "What to Do" (lines 58-67) is entirely raw `Read`/`Edit`:
"2. Read the relevant YAML file. 3. Find the entry... 4. Update the entry... " — no schema
validation step anywhere. Its own "Entry Schema" section (lines 40-56) states P0 requires a
non-null `test_path`, and that `verified`/`divergent` require `v2_evidence`+`test_path`, and
`divergent` requires `divergence_note` — but nothing enforces this at write time.

**`docs/parity_ledger/schema.json`** — **structurally broken as-parsed**, confirmed by direct
`json.load()` test (not assumed): the `items` object (lines 44-56) declares **two top-level `"if"`
keys** in the same JSON object:
```
"if": {"properties": {"status": {"enum": ["verified", "divergent"]}}},
"then": {"required": ["v2_evidence", "test_path"]},
"if": {"properties": {"status": {"const": "divergent"}}},
"then": {"required": ["divergence_note"]}
```
JSON object keys must be unique; every standard parser (confirmed with Python's `json.load`, and
`jsonschema` 4.10.3 which is importable in this venv though absent from any `requirements*.txt`)
silently keeps only the **second** `if`/`then` pair. Live-verified: `items.get("if")` returns only
`{"properties": {"status": {"const": "divergent"}}}` — the first rule (verified/divergent requires
`v2_evidence`+`test_path`) is **completely unenforced** by any naive `jsonschema.validate()` call
against this raw file. This is not a new discovery — `tools/parity_index_baseline.py`'s
`_schema_coverage_as_parsed()` (lines 62-90) already documents this exact defect verbatim
("the source file contains two top-level `\"if\"` keys... duplicate JSON object keys mean only the
second survives standard parsing"), built for `TCK-20260731-PARITY-INDEX-BASELINE` as
observed-fact evidence capture, explicitly **not fixed** there (read-only baseline tool, by design).
Additionally, **the schema has no P0→non-null-`test_path` conditional at all** — that rule exists
only as CLAUDE.md/`parity-updater.md` prose ("P0 entries require a non-null `test_path` pointing to
a passing test"), never machine-expressed in `schema.json`.

**`tools/agent-monitoring/generate_retro.py`** (lines 251-276) — the exact functions whose output
this ticket's Request Summary cites as the "0% co-occurrence" evidence:
- `_is_parity_ledger_yaml_write(tool_row)` (line 251): `True` only for a `tool_row` whose
  `tool` is `"Edit"`/`"Write"` **and** whose `input_summary` contains both `"docs/parity_ledger/"`
  and `".yaml"`.
- `_is_parity_index_build_call(tool_row)` (line 258): `True` only for `tool == "Bash"` **and**
  `input_summary` containing both `"parity_index.py"` and `"build"`.
- `compute_tool_safety_metrics` (line ~818) computes `run_ids_with_build_calls` from the second
  function, then flags a yaml-write row as safe only if its `run_id` is in that set.

Critically, `input_summary` for a `Bash` tool call is populated by
`tools/agent-monitoring/post_tool_hook.py::_input_summary` (line 15-16) as
**`tool_input.get("command")[:80]`** — the literal, agent-issued shell command text, truncated to
80 characters. It has **no visibility into what a Bash-invoked script does internally**
(subprocess calls, Python function calls inside that script are invisible to this hook). This is
directly load-bearing for Decision 2 below — see Risks and Open Questions.

## Mechanics / Engine Constraints

This ticket is agent-infrastructure tooling (`layer: ai`), not simulation/gameplay logic — no
`docs/mechanics/` chapter or `docs/engine/` contract governs `docs/parity_ledger/*.yaml`'s own
write-time validation. The relevant authority is CLAUDE.md's own "Authoritative Mechanics Rule"
(parity ledger sync requirement) and "Parity Ledger — Entry Schema" prose, both of which this
ticket's writer must encode as enforced, not descriptive, rules.

## Docs Requiring Update

- `docs/parity_ledger/schema.json`: fix the duplicate top-level `"if"` key defect (combine both
  conditionals into an `allOf` array so both survive standard JSON parsing) and add the currently
  prose-only P0→non-null-`test_path` conditional — explicitly permitted by this ticket's own Out
  of Scope clause ("Broadening `schema.json` itself beyond what's needed to express the existing
  entry schema documented in CLAUDE.md's 'Entry Schema' section" is out of scope; fixing it to
  actually express that already-documented schema is not a broadening).

## Parity Ledger Overlap

- `INFRA-315` (`docs/parity_ledger/infrastructure.yaml`, status `verified`, priority P2) — its
  `text`/`v2_evidence` describe `compute_tool_safety_metrics`'s **original, unscoped** "zero-tolerance
  count of Edit/Write calls" design. `TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE` (DONE)
  changed that logic to the co-occurrence-gated version described above and did **not** update
  `INFRA-315` (confirmed: no ledger entry anywhere cites that ticket ID or
  `_is_parity_index_build_call`). `INFRA-315` is therefore already stale, pre-existing this ticket.
  Fixing it is explicitly out of scope here (this ticket's Out of Scope forbids any
  `docs/parity_ledger/*.yaml` content change) — flagged for a follow-up, not silently ignored.
- No P0 entry anywhere cites `tools/parity_index.py`, `tools/parity_ledger_scan.py`,
  `tools/gate_checks/parity_updater_static.py`, or `docs/parity_ledger/schema.json` (confirmed by
  grep across all 9 shards) — the P0-test_path-required gate in
  `docs/parity_ledger/schema.json` is not itself parity-tracked. This ticket does not add a new
  ledger entry for its own new writer tooling, consistent with the precedent set by the sibling
  `TCK-20260731-PARITY-INDEX-*` epic (which built `parity_index.py` itself and also added no
  ledger entry for it) and with this ticket's own Out of Scope clause.

## Prior Work

- `TCK-20260731-PARITY-INDEX-IMPORTER`/`-BASELINE`/`-IMPACT-PROOF`/`-READPATH-GATE` (all DONE)
  built the read-only importer/read-path this ticket's write path must sit beside without
  reopening. `parity_index_baseline.py`'s `_schema_coverage_as_parsed()` already captured the
  schema.json defect as observed fact — reused directly above, not rediscovered independently.
- `TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY` (DONE) built `check_staleness()` (factored
  `_shard_manifest_hash()` out of `_build_into()` specifically so a cheap check can never drift
  from what a real `build()` computes) and the `make parity-index`/`make parity-index-check`
  targets. **Reused directly, not reimplemented**: this ticket's writer should call
  `parity_index.build()` (or `check_staleness()`) as an imported Python function, not re-derive
  the hash logic.
- `TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE` (DONE) defined the exact
  `parity_write_safety` co-occurrence semantics (same `run_id`, a `Bash` row matching
  `_is_parity_index_build_call`) this ticket's own Request Summary evidence relies on — its
  Implementation Notes explicitly note the initial broad-substring design was corrected after a
  real-corpus false-positive check; the current logic is narrow and literal-substring-based, not
  semantic. This literalness is exactly what makes Decision 2's "does an internal call actually
  register" question non-trivial (see below).

## Risks and Open Questions

**1. (Blocks Plan) Writer location — CONFIRMED, not left open.** `parity_index.py`'s own
docstring and its architecture-guard test both hard-block adding a mutation path inside that
module. **Decision: a new sibling module** (e.g. `tools/parity_ledger_writer.py`, matching the
existing `parity_index.py`/`parity_ledger_scan.py`/`parity_index_baseline.py`
single-responsibility layering) that imports `parity_index.build`/`check_staleness` as black-box
functions after a successful validated write, and imports/validates against the (fixed)
`docs/parity_ledger/schema.json`.

**2. (Blocks Plan) Index-rebuild-on-write vs. staleness-flag — recommend rebuild-on-write, with a
load-bearing caveat.** AC #2 ("rebuilds the derived index in the same run... verified by a test
asserting the chosen behavior actually happens") is a **pytest-testable claim about the writer's
own function-level behavior** — calling `parity_index.build()` in-process immediately after a
successful validated write, then asserting `check_staleness()` reports `FRESH`, is the narrowest,
most directly-testable option and is recommended.

**However**: this does **not** mechanically move the `parity_write_safety` retro metric the
Request Summary cites as motivation, and Plan must not assume it does. `_is_parity_index_build_call`
pattern-matches the literal text of a **separate, agent-issued `Bash` tool call**
(`command[:80]`, per `post_tool_hook.py::_input_summary`) — it has zero visibility into a Python
function call made *inside* a script the agent invoked via one Bash call. Two further
consequences, both real and neither optional to acknowledge:
  - If the new writer's own CLI is invoked as `python3 tools/parity_ledger_writer.py write ...`,
    that command text alone will not satisfy `_is_parity_index_build_call` (no `"parity_index.py"`
    substring) even though the writer's internal call to `parity_index.build()` genuinely rebuilds
    the index. For the co-occurrence signal to actually appear in a future retro run,
    `.claude/agents/parity-updater.md`'s new "What to Do" should have the agent issue the writer
    call and a follow-up **separate, visible** `python3 tools/parity_index.py build` Bash call —
    this is achievable without touching `generate_retro.py` at all (out of scope here; that
    module belongs to this ticket's sibling epic child, `TCK-20260810-CONTEXT-TOOLING-
    EFFECTIVENESS-TRACKING`).
  - Once the writer stops using raw `Edit`/`Write` tool calls on the YAML file (replaced by one
    `Bash` call to the new writer CLI), `_is_parity_ledger_yaml_write` (which only matches
    `Edit`/`Write` tool rows) will **structurally stop detecting real future parity-ledger
    writes at all** — the metric's numerator collapses toward zero going forward, which looks like
    "0 violations" but actually means "0 observed writes," a different and worse signal than
    today's. This is a genuine, non-obvious side effect of legitimately fixing the underlying
    tool, not scope creep to fix here, but Plan must record it as a known, disclosed follow-up
    (do not let it surface as a surprise later) rather than silently let the metric go dark.

**3. (Blocks Plan) Gate A §6.2/§6.3 — recommend §6.2 DEFER, §6.3 FIX.**
  - **§6.2** (`_PATH_REF_RE` not recognizing `.claude/`-prefixed paths) is a **read-path** issue
    (`_populate_ref_tables`'s `code_refs`/`constraint_refs`/`ticket_refs` extraction inside
    `parity_index.py`'s `build()`). This ticket's own Out of Scope and the parent epic's Out of
    Scope both explicitly forbid touching the read-path-wiring decision Gate A deferred to a
    future Phase-3 ticket. **Recommend: defer**, rationale: fixing it here would require touching
    `_PATH_REF_RE` inside `parity_index.py`, which is squarely the read-path surface both this
    ticket and its parent epic explicitly wall off ("must not be used to backdoor that larger
    decision").
  - **§6.3** (`find_p0_intersection` raises uncaught `yaml.YAMLError`, `tools/parity_ledger_scan.py`
    line 49) is a **different, narrow, cheap fix directly adjacent to work this ticket is already
    doing**: the new writer must itself read the target shard before mutating it, and must not
    crash uncaught on a malformed shard (same risk class). **Recommend: fix in this ticket** —
    wrap `find_p0_intersection`'s `yaml.safe_load` in `try`/`except yaml.YAMLError`, raising a
    labeled error (mirroring `parity_index.py`'s `ShardParseError` pattern) instead of an uncaught
    crash, plus one regression test. Building a hardened writer next to an unfixed, disclosed,
    known-crashing sibling function in the same subsystem — when the fix costs a few lines — would
    be an inconsistent half-measure. Final call belongs to Plan, but leaving it unfixed requires
    active justification, not default deferral.

**4. `jsonschema` is not declared in any `requirements*.txt`** despite being importable in this
venv (confirmed 4.10.3, likely a transitive dependency of something else). Plan must confirm
whether to add it as an explicit dependency or hand-roll the four validation rules in plain Python
(no `jsonschema.validate()` call) — either resolves AC #1, but the dependency question needs an
explicit decision, not an assumption that it's "already available."

**5. `tools/parity_index_baseline.py`'s `_schema_coverage_as_parsed()` (lines 62-90) will become
stale once `schema.json` is fixed** — its docstring and `known_defect`/`discarded_rule` fields
describe the *current*, broken parse result. If Plan fixes `schema.json` via `allOf` restructuring,
`items.get("if")` will return `None` post-fix (no top-level `if` key at all), changing this
function's output shape. `tools/parity_index_baseline.py` is **not** listed in this ticket's own
"Related Code Areas" — a real gap in the ticket's own scoping that Plan must account for (either
update this function/its docstring in the same PR, or explicitly document why leaving it
stale-but-accurate-to-history is acceptable).

## Anti-Drift Hazards

- Do not let the new writer duplicate `parity_index.py`'s shard-loading/hash logic — reuse
  `_load_shards`/`_shard_manifest_hash`/`build`/`check_staleness` as imports, per the explicit
  precedent `TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY` set for exactly this kind of reuse.
- Do not let `schema.json`'s fix silently also change enforcement for entries that are not
  `verified`/`divergent`/P0 (`missing`/`unsupported`/`legacy_verified` status entries have no
  `v2_evidence`/`test_path` requirement today — the `allOf` restructuring must preserve that,
  not accidentally tighten it).
- Do not let this ticket's writer become the vehicle for editing existing ledger *content*
  (`docs/parity_ledger/*.yaml` entries) — Out of Scope is explicit; the writer is infrastructure,
  this ticket ships no ledger-content diff.
- Do not conflate "the writer rebuilds the index" (AC #2, a function-level pytest claim) with "the
  retro metric moves" (a separate, `generate_retro.py`-owned observability claim, out of scope) —
  keep these two claims distinct in Plan and in the eventual Completion Summary; overclaiming the
  second from evidence for the first would be a real accuracy problem in the closed ticket record.
- Do not fix §6.2 "for free" while touching `_PATH_REF_RE`-adjacent code for another reason —
  the boundary is deliberate and documented in two places (this ticket's Out of Scope, the parent
  epic's Out of Scope); a tempting drive-by fix here would violate both.
