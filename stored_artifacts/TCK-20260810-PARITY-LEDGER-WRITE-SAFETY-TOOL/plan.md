---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL
artifact_type: plan
tags: [ai, agent-monitoring, process-improvement]
---

# Implementation Plan — TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL

## Summary

Build a schema-validating writer for `docs/parity_ledger/*.yaml` in a new sibling module,
`tools/parity_ledger_writer.py`, that hand-rolls the four required rejection rules directly in
Python (mirroring, not importing, `docs/parity_ledger/schema.json`'s corrected `allOf` structure)
and rebuilds `parity_index.py`'s derived SQLite index in-process after every successful validated
write. Before the writer is built, fix the two real, disclosed defects it would otherwise inherit:
`schema.json`'s duplicate top-level `"if"` key (which today silently drops the
verified/divergent→`v2_evidence`+`test_path` rule) and the missing P0→non-null-`test_path`
conditional (today prose-only). Alongside, fix Gate A §6.3 (`find_p0_intersection`'s uncaught
`yaml.YAMLError` on a malformed shard) as a narrow, adjacent robustness fix, and reconcile the one
existing test file (`tests/tools/test_gate_a_readpath_review.py`) whose helper depends on the old
crash behavior. Gate A §6.2 (read-path `_PATH_REF_RE` gap) is explicitly deferred — fixing it would
require touching `parity_index.py`'s read-path internals, which both this ticket's and its parent
epic's Out of Scope sections wall off. Finally, `.claude/agents/parity-updater.md`'s "What to Do"
section is updated to call the new writer instead of raw `Read`/`Edit`, and to still issue a
separate, visible `python3 tools/parity_index.py build` Bash call so the `parity_write_safety` retro
metric (which only pattern-matches literal Bash command text, not in-process Python calls) keeps
registering a signal going forward.

## Design Decisions

**Writer location (resolved, not open):** new sibling module `tools/parity_ledger_writer.py`, not
inside `tools/parity_index.py`. Confirmed via direct read: `tools/parity_index.py`'s own docstring
(lines 10-12) states twice that it "never writes into `docs/parity_ledger/` and implements no
mutation CLI," and `tests/tools/test_parity_index.py::TestArchitectureGuards::
test_no_mutation_cli_or_write_path_to_docs_parity_ledger` (line 535) statically asserts no
`open(...,"w")`/`.write_text(...)` call in that file's source targets `docs/parity_ledger`. Adding a
mutation path there would break that test and contradict the module's own stated contract.

**Index freshness (resolved, not open):** rebuild-on-write. After a successful validated write, the
writer calls `parity_index.build()` (imported from `tools/parity_index.py`, confirmed present at
`tools/parity_index.py:530`) in-process, in the same run. This is the narrowest AC #2-testable
option — a caller can assert `parity_index.check_staleness(...)` (confirmed present at
`tools/parity_index.py:406`) returns `FRESH` immediately after a successful `write_entry()` call.
**Caveat, not to be overclaimed in Completion Summary:** this makes the writer's own function-level
behavior correct and testable, but does **not** by itself move the `parity_write_safety` retro
metric (`tools/agent-monitoring/generate_retro.py:258`'s `_is_parity_index_build_call` only matches
a *separate* `Bash` tool call whose `command[:80]` text literally contains both `"parity_index.py"`
and `"build"` — an in-process Python call inside a script invoked via one Bash call is invisible to
it). Step 7 below compensates by also having the agent issue a visible, literal
`python3 tools/parity_index.py build` Bash call after the writer call.

**`jsonschema` dependency (resolved, not open — this ticket's own open question, decided here):
do not add it.** Confirmed `jsonschema` 4.26.0 is importable in this repo's venv
(`.venv/lib/python3.12/site-packages/jsonschema/__init__.py`) but is not declared in
`requirements.txt` or `requirements-knowledge.txt` (grep of both files found no `jsonschema` line)
and is not imported anywhere in the current codebase (`grep -rn jsonschema --include=*.py` across
the repo returned zero hits outside the venv itself) — it is an incidental transitive dependency of
some other declared package, not a deliberate, tracked choice. Per the investigation's own
guidance ("prefer the option with less new dependency surface unless jsonschema is already a safe,
already-present choice"), an undeclared transitive import is not a safe, already-present choice —
a future dependency bump could silently remove it. The writer instead hand-rolls the four validation
rules as plain Python functions in `tools/parity_ledger_writer.py`, structured to mirror
`schema.json`'s corrected `allOf` block field-for-field (each Python `if` block cites the exact
`schema.json` line range it mirrors in a code comment). This is a real, disclosed drift risk (the
two representations must be kept in sync by hand on any future schema change) — recorded under
Anti-Drift Notes below, not silently accepted.

**Writer interface style: importable Python function, no argparse CLI.** Matches the stated,
existing convention for this exact family of modules — `tools/gate_checks/parity_updater_static.py`
docstring (lines 20-21) states its sibling modules are "consumed exclusively via `python3 -c`," no
argparse/CLI. `tools/parity_ledger_writer.py` follows the same shape: plain functions
(`validate_entry`, `write_entry`), invoked by an agent via
`python3 -c "import sys; sys.path.insert(0,'tools'); from parity_ledger_writer import write_entry; ..."`.
This does not change the metric-visibility caveat above either way — see Step 7.

## Steps

### Step 1 — Fix `docs/parity_ledger/schema.json`'s duplicate-`if` defect and add the P0 conditional

**Files:** `docs/parity_ledger/schema.json`, `tests/tools/test_parity_ledger_schema.py` (new)

**Change:** Confirmed by direct read (`docs/parity_ledger/schema.json:44-56`) that the `items`
object currently declares two top-level `"if"` keys in the same JSON object — standard JSON parsing
silently keeps only the second, so the verified/divergent→`v2_evidence`+`test_path` rule is
currently unenforced by any naive `jsonschema.validate()` call (independently reproduced: `json.load`
on the raw file shows `items["if"]` resolves only to the `status == "divergent"` branch). Restructure
both conditionals into an `items.allOf` array so both survive standard parsing, and add a third
`allOf` entry expressing the currently prose-only P0→non-null-`test_path` rule (documented today only
in `.claude/agents/parity-updater.md:53`, "P0 entries require a non-null `test_path`"). For the
"non-null" requirement specifically (not just "present"), give the P0 branch's `then` an explicit
`"properties": {"test_path": {"type": "string"}}` override alongside `"required": ["test_path"]` —
plain JSON Schema `required` only checks key presence, and `test_path`'s base type is
`["string", "null"]` (`docs/parity_ledger/schema.json:34-36`), so a bare `required` would still allow
an explicit `null`. Apply the same `{"type": "string"}` override to the `v2_evidence`/`test_path`
pair in the verified/divergent branch and to `divergence_note` in the divergent branch, for the same
reason (test_plan.md's rejection tests explicitly construct `v2_evidence: null` / `test_path: null` /
`divergence_note: null`, not merely omitted keys).

Final `items` shape:
```json
"allOf": [
  {
    "if": {"properties": {"status": {"enum": ["verified", "divergent"]}}},
    "then": {
      "properties": {"v2_evidence": {"type": "string"}, "test_path": {"type": "string"}},
      "required": ["v2_evidence", "test_path"]
    }
  },
  {
    "if": {"properties": {"status": {"const": "divergent"}}},
    "then": {
      "properties": {"divergence_note": {"type": "string"}},
      "required": ["divergence_note"]
    }
  },
  {
    "if": {"properties": {"priority": {"const": "P0"}}},
    "then": {
      "properties": {"test_path": {"type": "string"}},
      "required": ["test_path"]
    }
  }
]
```

**Do NOT touch:** the `properties` block's field list/types/enums (id pattern, status enum, priority
enum, etc. — unchanged, per this ticket's Out of Scope "broadening `schema.json`... beyond what's
needed to express the existing entry schema"); do not add any conditional gated on `missing` /
`unsupported` / `legacy_verified` status — those three statuses must remain fully unconstrained on
`v2_evidence`/`test_path`/`divergence_note`, matching current documented behavior.

**Verify:** No dedicated pytest exists today for this file's raw JSON structure (confirmed: no test
in `tests/tools/test_parity_index_baseline.py` references `SCHEMA_PATH` or
`_schema_coverage_as_parsed`, and `tests/tools/test_parity_index.py`/`test_gate_a_readpath_review.py`
never load `schema.json` directly) — this step adds one. New test file
`tests/tools/test_parity_ledger_schema.py`, with a function
`test_schema_json_parses_and_has_fixed_allof_structure` that: (1) opens and `json.load`s
`docs/parity_ledger/schema.json` and asserts it succeeds without raising; (2) asserts
`len(schema["items"]["allOf"]) == 3`; (3) asserts `"if" not in schema["items"]` and
`"then" not in schema["items"]` (no top-level conditional survives directly under `items` — both
former top-level keys must now live only inside the three `allOf` entries). This is a direct,
runtime, regression-blocking proof of the fix itself — per architecture-reviewer NEEDS_CHANGES
feedback on the prior draft of this plan, Step 5/6's writer tests exercise `validate_entry()`, a
separate hand-rolled Python reimplementation that never loads or parses `schema.json` at runtime, so
they cannot catch a future regression to the raw JSON structure (e.g. someone re-introducing a
duplicate top-level `"if"` key) — only a test that actually parses this file closes that gap. Retain
the one-off `python3 -c "import json; d=json.load(open('docs/parity_ledger/schema.json'));
assert len(d['items']['allOf'])==3; assert 'if' not in d['items']"` check as a quick manual sanity
check during implementation, but the new pytest is the authoritative, CI-enforced proof that this
step is complete — it is added to Step 8's scoped verification run below.

### Step 2 — Update `tools/parity_index_baseline.py`'s `_schema_coverage_as_parsed()` to stop describing a now-fixed defect as current

**Files:** `tools/parity_index_baseline.py` (function at lines 62-90)

**Change:** Confirmed by direct read (`tools/parity_index_baseline.py:62-90`) that this function's
docstring and `known_defect`/`discarded_rule` return fields describe the *pre-fix* parse result
(`items.get("if")` returning only the second surviving pair). After Step 1's `allOf` restructuring,
`items.get("if")` and `items.get("then")` will both resolve to `None` (no top-level `if`/`then` key
remains under `items`), silently changing this function's output shape without updating its
narrative. Confirmed no test depends on this function's output (`grep -rn "_schema_coverage_as_parsed\|SCHEMA_PATH" tests/`
returns nothing under `tests/`) and it is only consumed by `build_manifest()`
(`tools/parity_index_baseline.py:168`), which writes a JSON manifest artifact via `main()`
(`tools/parity_index_baseline.py:183`) — a CLI report generator, not a gated check. Update the
function to detect the fixed structure and report accurately: if `items.get("allOf")` is present,
report `known_defect: None` and a `note` field stating the defect was fixed by
`TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL`; keep the pre-fix branch (checking bare `items.get("if")`)
as a defensive fallback in case this function is ever run against an older git revision of the file,
so it degrades to the old, accurate-for-that-revision report rather than crashing.

**Do NOT touch:** `_sha256_hex`, `_scan_shard`, `_missing_evidence_health`, `build_manifest`,
`serialize_manifest`, `main` — only the one function's body/docstring.

**Verify:** No pytest gate. Manually confirm via
`python3 -c "import sys; sys.path.insert(0,'tools'); from parity_index_baseline import _schema_coverage_as_parsed; print(_schema_coverage_as_parsed())"`
that it runs without error and no longer claims the fixed defect is present.

### Step 3 — Fix Gate A §6.3: `find_p0_intersection`'s uncaught `yaml.YAMLError`

**Files:** `tools/parity_ledger_scan.py`

**Change:** Confirmed by direct read (`tools/parity_ledger_scan.py:49`) that
`entries = yaml.safe_load(path.read_text()) or []` inside `find_p0_intersection`
(`tools/parity_ledger_scan.py:36`) has no `try`/`except` around it — a malformed canonical shard
raises an uncaught `yaml.YAMLError`, confirmed as real and disclosed by
`docs/ai/parity_readpath_gate_a_decision.md` §6.3 and reproduced live in
`tests/tools/test_gate_a_readpath_review.py`'s `_safe_find_p0_intersection` wrapper (lines 133-141),
which exists solely to catch this exact crash. Add a local exception class mirroring
`tools/parity_index.py`'s `ShardParseError` shape (`tools/parity_index.py:126-131`,
`__init__(self, filename, message)`, message `f"failed to parse shard {filename!r}: {message}"`) —
defined locally in `tools/parity_ledger_scan.py` (not imported from `parity_index.py`, to keep the
two modules' import direction independent, consistent with `parity_ledger_scan.py`'s existing
single-file, no-cross-import shape). Wrap the `yaml.safe_load` call in
`try/except yaml.YAMLError as exc: raise ShardParseError(filename, str(exc)) from exc`.

**Other writers/readers of this exact code path (per fact-verification rule #2):**
`find_p0_intersection` is called from two places today: (a) `.claude/workflows/implement-ticket.js`'s
Parity-phase skip check (per this module's own docstring, lines 1-9) — a malformed shard there would
now raise a labeled `ShardParseError` instead of a bare `yaml.YAMLError`; both are uncaught by the
orchestrator today either way, so this does not change orchestrator-level behavior, only the
exception's label/message. (b) `tests/tools/test_gate_a_readpath_review.py`'s
`_safe_find_p0_intersection` (lines 133-141), which explicitly catches `yaml.YAMLError` by name —
this is addressed in Step 4 below, in the same change-set, so the two steps must land together.
No other module imports `find_p0_intersection` (confirmed:
`grep -rn "find_p0_intersection" --include=*.py` shows only `tools/parity_ledger_scan.py` itself,
`tests/tools/test_parity_ledger_scan.py`, and `tests/tools/test_gate_a_readpath_review.py`).

**Do NOT touch:** `CANONICAL_LEDGER_FILES`, the P0-only filter logic, the substring-match loop, or
any other function in this file (`derive_mapping`-equivalent logic lives in a different file,
`tools/gate_checks/parity_updater_static.py`, and is not part of this fix).

**Verify:** new test `test_find_p0_intersection_malformed_shard_raises_labeled_error_not_crash` in
`tests/tools/test_parity_ledger_scan.py` — write a malformed-YAML fixture shard (e.g. unbalanced
flow-mapping syntax) into a `tmp_path` canonical filename, call `find_p0_intersection`, assert it
raises the new labeled exception (not a bare `yaml.YAMLError` propagating un-relabeled) with the
shard filename captured on the exception.

### Step 4 — Reconcile `tests/tools/test_gate_a_readpath_review.py`'s crash-catching helper with the Step 3 fix

**Files:** `tests/tools/test_gate_a_readpath_review.py`

**Change:** Confirmed by direct read (`tests/tools/test_gate_a_readpath_review.py:133-141`) that
`_safe_find_p0_intersection` wraps `find_p0_intersection` in
`try: ... except yaml.YAMLError as exc: return {"ok": False, "error_class": type(exc).__name__}` —
this exists specifically to convert the pre-fix uncaught crash into a recorded result for the Gate A
adjudication harness. Once Step 3 makes `find_p0_intersection` raise the new
`ShardParseError` (defined locally in `tools/parity_ledger_scan.py`, not a `yaml.YAMLError`
subclass) instead of letting the raw `yaml.YAMLError` propagate, this `except yaml.YAMLError`
clause will no longer catch it, and the malformed-shard corpus case
(`gate_a_full_run` fixture, line ~238) will crash the whole module's collection instead of recording
a result. Add an import of the new exception class
(`from parity_ledger_scan import ShardParseError` alongside the existing
`from parity_ledger_scan import find_p0_intersection`, line 39) and change the `except` clause to
`except (yaml.YAMLError, ShardParseError) as exc:` — catching both keeps this harness correct
regardless of exception type, and is the minimal edit. Confirmed no test asserts the literal
`error_class` string value (`grep -n "error_class" tests/tools/test_gate_a_readpath_review.py` shows
only the one assignment site, lines 141/239/241/244 read the dict's `ok`/`hits` keys, never the
`error_class` string) — so returning `"ShardParseError"` instead of `"YAMLError"` does not break any
assertion.

**Other writers/readers of this file's protected-file guard (per fact-verification rule #2):**
`TestNoMutation::test_gate_a_review_leaves_protected_files_byte_identical`
(`tests/tools/test_gate_a_readpath_review.py:155-165`) hashes `tools/parity_ledger_scan.py` (among
other protected files) — but confirmed by direct read that `_PRE_RUN_HASHES` is computed once at
**module import time** (line 152, top-level statement, evaluated fresh every time pytest collects
this module) and compared against a hash computed **within the same test run** (line 158) — both
hashes are computed against whatever `tools/parity_ledger_scan.py` bytes exist on disk when pytest
runs, not against a historical/pinned baseline. This means Step 3's edit to
`tools/parity_ledger_scan.py` does **not** break this guard: as long as nothing mutates the file
*during* the test session itself, pre- and post-run hashes will still match, regardless of the file's
absolute content. No change to `_protected_files()` or the hashing mechanism is needed.

**Do NOT touch:** the `_Adjudications.MALFORMED_SHARD_THREE_WAY` narrative text
(`tests/tools/test_gate_a_readpath_review.py`, describes the pre-fix three-way behavior as an
*observed-at-review-time* historical finding — still true of what Gate A observed; not a live-behavior
assertion, so it does not need updating), `gate_a_corpus.json`, `gate_a_results.json`, or any other
adjudication logic in this file — this step touches only the one `except` clause and its import line.

**Verify:** `pytest tests/tools/test_gate_a_readpath_review.py -v` passes unchanged (all existing
tests, including `TestNoMutation` and the malformed-shard adjudication cases in `TestAdjudication`).

### Step 5 — Build `tools/parity_ledger_writer.py`: `validate_entry()` + `write_entry()` (no rebuild yet)

**Files:** `tools/parity_ledger_writer.py` (new), `tests/tools/test_parity_ledger_writer.py` (new)

**Change:** New module, importing `yaml`, `re`, `pathlib.Path`, and from `tools/parity_index.py`:
`DEFAULT_LEDGER_DIR` (confirmed present, `tools/parity_index.py` module-level constant, used as
`write_entry`'s default `ledger_dir`) — no `build`/`check_staleness` import yet in this step (added
in Step 6). Define:

- `class EntryValidationError(Exception)` — `__init__(self, field, reason)`, message
  `f"invalid parity ledger entry field {field!r}: {reason}"` — a specific, labeled error per
  test_plan.md's requirement ("not a generic `ValueError`/`AssertionError`").
- `_ID_PATTERN = re.compile(r"^[A-Z]+-[0-9]{3}$")` — mirrors `docs/parity_ledger/schema.json:11`'s
  `id` pattern exactly.
- `validate_entry(entry: dict) -> None` — four independent checks, each citing in a code comment the
  exact Step-1-fixed `schema.json` `allOf` branch it mirrors:
  1. `id` must match `_ID_PATTERN` (mirrors `schema.json:9-11`).
  2. if `status in {"verified", "divergent"}`: `v2_evidence` and `test_path` must both be non-null,
     non-empty strings (mirrors Step 1's first `allOf` branch).
  3. if `status == "divergent"`: `divergence_note` must be a non-null, non-empty string (mirrors
     Step 1's second `allOf` branch).
  4. if `priority == "P0"`: `test_path` must be a non-null, non-empty string (mirrors Step 1's third
     `allOf` branch).
  Each violated rule raises `EntryValidationError` immediately, naming the specific field.
- `write_entry(shard_filename: str, entry: dict, ledger_dir=None) -> dict` — calls
  `validate_entry(entry)` **first, unconditionally, before any file I/O**; on success, reads the
  target shard (`Path(ledger_dir or DEFAULT_LEDGER_DIR) / shard_filename`) via `yaml.safe_load`
  (empty list if the file doesn't exist yet), upserts by `id` (replaces the existing list entry with
  matching `id` in place, else appends), and writes the shard back with
  `yaml.safe_dump(entries, sort_keys=False)`. This is the **only** code path in the module that
  reaches `docs/parity_ledger/*.yaml` write bytes — required for the architecture-guard test below.
  Returns `{"status": "ok", "shard": shard_filename, "entry_id": entry["id"]}`.

Explicitly out of scope for `validate_entry`: duplicate-`id` detection across shards. The ticket's
own Scope enumerates exactly four rejection conditions (bad `id` pattern; missing
`v2_evidence`/`test_path` for verified/divergent; missing `divergence_note` for divergent; non-null
`test_path` for P0) — duplicate-id collision is a different concern already caught later by
`parity_index.build()`'s `DuplicateEntryIdError` (`tools/parity_index.py:133-137`) on rebuild (Step
6), not something this step adds to `validate_entry`.

**Do NOT touch:** `tools/parity_index.py`, `tools/parity_ledger_scan.py` (beyond Step 3),
`tools/gate_checks/parity_updater_static.py` — this step only adds a new file plus its new test file.

**Verify:**
- `test_writer_rejects_bad_id_pattern`
- `test_writer_rejects_verified_missing_v2_evidence`
- `test_writer_rejects_verified_missing_test_path`
- `test_writer_rejects_divergent_missing_v2_evidence`
- `test_writer_rejects_divergent_missing_test_path`
- `test_writer_rejects_divergent_missing_divergence_note`
- `test_writer_rejects_p0_missing_test_path`
- `test_writer_accepts_valid_verified_entry_and_writes_shard`
- `test_writer_never_bypasses_validation_via_direct_yaml_dump` (static-source guard, mirroring
  `tests/tools/test_parity_index.py:535`'s pattern: assert `validate_entry(` appears in
  `write_entry`'s source before any `write_text`/`yaml.safe_dump` call, and that exactly one such
  write call-site exists in the module)
- one Anti-Drift Test Guard test (per test_plan.md's "Anti-Drift Test Guards" section, not itemized
  under "New Tests Required" but required): `test_writer_accepts_missing_status_without_evidence`
  — an entry with `status: missing` (or `unsupported`/`legacy_verified`) and null `v2_evidence`/
  `test_path` is accepted, proving Step 1's `allOf` restructuring did not accidentally tighten
  enforcement for those three statuses.

All tests in `tests/tools/test_parity_ledger_writer.py`.

### Step 6 — Wire in-process index rebuild into `write_entry()` on successful write

**Files:** `tools/parity_ledger_writer.py`

**Change:** Import `build` and `check_staleness` from `tools/parity_index.py` (confirmed present at
`tools/parity_index.py:530` and `:406` respectively — both plain functions, no class state, safe to
import directly, per the explicit reuse precedent `TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY`
set for exactly this: `_shard_manifest_hash` was factored out of `_build_into()` specifically so
`check_staleness()` "can never drift from what a real `build()` computes"). After `write_entry()`'s
shard write succeeds, call `parity_index.build(ledger_dir=ledger_dir, db_path=db_path)` and include
its report in the return value: `{"status": "ok", "shard": ..., "entry_id": ..., "build_report": {...}}`.
Add `db_path=None` parameter to `write_entry`, defaulting to `parity_index.DEFAULT_DB_PATH`
(confirmed present, `tools/parity_index.py` module-level constant) — matching `build`/
`check_staleness`'s own default-parameter shape so callers can point both at the same test-isolated
paths.

**Other writers to the derived index (per fact-verification rule #2):** `parity_index.build()` is
also invoked directly by `make parity-index` (Makefile target, per
`docs/ai/parity_readpath_gate_a_decision.md`'s referenced tooling) and by any agent/session issuing
`python3 tools/parity_index.py build` manually (exactly what Step 7 has `parity-updater.md` continue
to instruct). Both of these remain valid, unchanged, idempotent ways to rebuild the same database —
`build()`'s own atomic-replace lifecycle (`tools/parity_index.py:502-524`,
`_atomic_replace_db`/`os.replace`) means two rebuilds racing (e.g., the writer's in-process call and
a concurrent manual `make parity-index` in a different terminal) each write to their own temp file
and only the last `os.replace` wins — no partial/corrupt state, consistent with `build()`'s existing
concurrency safety, which this ticket does not change. The writer does not introduce a new writer to
`parity-index/parity.db`; it only adds one more caller of the existing `build()` entry point.

**Do NOT touch:** `_atomic_replace_db`, `_build_into`, or any other internal of `parity_index.py` —
this step calls `build()`/`check_staleness()` as black-box imports only, per the explicit
reuse-not-reinvent precedent in investigation.md.

**Verify:**
- `test_successful_write_rebuilds_index_in_same_run` — after a successful `write_entry()` call
  against an isolated `tmp_path` ledger/db pair, `parity_index.check_staleness(db_path=..., ledger_dir=...)`
  reports `{"status": "FRESH", ...}`.
- `test_failed_write_never_triggers_index_rebuild` — a rejected (invalid) `write_entry()` call raises
  `EntryValidationError` before any `build()` call; assert (e.g. via monkeypatching
  `parity_ledger_writer.build` to a call-counting stub) that `build` was never invoked, and that
  `check_staleness()` against a pre-existing `db_path` still reports whatever it reported before the
  rejected call (unchanged).

Both in `tests/tools/test_parity_ledger_writer.py`.

### Step 7 — Update `.claude/agents/parity-updater.md`'s "What to Do" to use the new writer, and to still issue a visible `parity_index.py build` Bash call

**Files:** `.claude/agents/parity-updater.md`

**Change:** Confirmed by direct read (`.claude/agents/parity-updater.md:58-67`) that "What to Do"
step 2-4 currently read: "Read the relevant YAML file... Find the entry... Update the entry..." with
no validation step. Replace steps 2-4 with instructions to construct the full entry dict per the
existing "Entry Schema" section (`.claude/agents/parity-updater.md:40-56`, unchanged — its field
list already matches `docs/parity_ledger/schema.json`'s `properties` block, confirmed by direct
comparison of both, so no edit needed there per this step's AC #3 "either stays accurate or is
updated to match") and invoke the new writer via
`python3 -c "import sys; sys.path.insert(0,'tools'); from parity_ledger_writer import write_entry; import json; print(json.dumps(write_entry('<shard_filename>', <entry_dict>)))"`
(or equivalent single Bash invocation) instead of raw `Edit`. Immediately after, per the
metric-visibility caveat recorded in Design Decisions above, add an explicit new step instructing the
agent to also issue a **separate, visible** `python3 tools/parity_index.py build` Bash call — this is
required for `tools/agent-monitoring/generate_retro.py`'s `_is_parity_index_build_call`
(`tools/agent-monitoring/generate_retro.py:258`, confirmed by direct read: matches only on `Bash`
tool rows whose `command[:80]` text contains both `"parity_index.py"` and `"build"` literally) to
register the co-occurrence signal `compute_tool_safety_metrics` audits — the writer's in-process
`build()` call from Step 6 is invisible to this hook (`tools/agent-monitoring/post_tool_hook.py:15-16`
only records the literal Bash command text of the outer call, not what a script does internally).
State explicitly in the doc that this second Bash call is redundant with the writer's own
in-process rebuild for correctness (the index is already fresh) but required for the retro metric to
see the write happened via a visible tool call.

**Other writers/readers of this doc file (per fact-verification rule #2):** no automated code parses
`.claude/agents/parity-updater.md`'s prose content today except this ticket's own new
architecture-guard test (Step 7's Verify, below) — confirmed via `grep -rn "parity-updater.md"
--include=*.py tools/ tests/` limited to this ticket's new test. `.claude/workflows/implement-ticket.js`
invokes the `parity-updater` agent by name/role, not by parsing this file's body, so this edit does
not affect orchestration wiring.

**Do NOT touch:** "Step 0", "Parity Ledger Files" table, "Output" section, or the "Entry Schema"
section's field list (unless Verify below finds a genuine drift — none found by direct comparison).

**Verify:** `test_parity_updater_agent_md_uses_new_write_path` (new, in
`tests/tools/test_parity_ledger_writer.py` or a new `tests/tools/test_parity_updater_agent_md.py` —
confirm at Implement time which existing test file, if any, already asserts on this doc's static
text and colocate there; otherwise add to `tests/tools/test_parity_ledger_writer.py`) — asserts the
"What to Do" section's text no longer instructs raw `Edit` as the primary mutation path and instead
references `parity_ledger_writer`/`write_entry` by name, and separately asserts the text also
references `python3 tools/parity_index.py build` as a required follow-up step.

### Step 8 — Full scoped verification run

**Files:** none (verification only)

**Change:** Run the complete scoped pytest surface from test_plan.md, in order, and confirm all
pass:
```
pytest tests/tools/test_parity_ledger_schema.py -v
pytest tests/tools/test_parity_ledger_writer.py -v
pytest tests/tools/test_parity_index.py -v
pytest tests/tools/test_parity_index_baseline.py -v
pytest tests/tools/test_gate_a_readpath_review.py -v
pytest tests/tools/test_parity_ledger_scan.py -v
pytest tests/tools/ -k "parity" -v
```
Confirm in particular that `tests/tools/test_parity_index.py::TestArchitectureGuards::
test_no_mutation_cli_or_write_path_to_docs_parity_ledger` and
`test_health_subcommand_never_writes_to_docs_parity_ledger` are unchanged and still pass (proves
`parity_index.py` was not turned into a second, competing write path — Design Decision 1's core
invariant), and that `tests/tools/test_gate_a_readpath_review.py::TestNoMutation::
test_gate_a_review_leaves_protected_files_byte_identical` still passes (proves Steps 3/4 did not
introduce an in-session mutation of any protected file).

**Do NOT touch:** anything — this step is verification-only, no code changes.

**Verify:** all seven commands above exit 0. Never run bare `pytest tests/`.

## Scope Guards

- Do not wire `tools/parity_index.py`'s read path (`entry`/`impact`/`health`) into
  `parity-updater`'s discovery step or any other live workflow gate — Gate A's GO verdict is scoped
  to the read-path review only; that decision belongs to a separate Phase-3 scoping ticket per
  `docs/ai/parity_readpath_gate_a_decision.md` §5.
- Do not touch `tools/parity_index.py`'s `_PATH_REF_RE` or any other read-path/`_populate_ref_tables`
  code — Gate A §6.2 is explicitly deferred (see Anti-Drift Notes), and both this ticket's and its
  parent epic's Out of Scope sections wall this off specifically to prevent a drive-by fix here.
- Do not change any `docs/parity_ledger/*.yaml` shard's content — this ticket ships tooling only, no
  ledger-content diff. All writer tests operate against `tmp_path` fixtures, never the real
  `docs/parity_ledger/` directory.
- Do not broaden `docs/parity_ledger/schema.json`'s `properties` block, field list, enums, or add any
  conditional beyond the three named in Step 1 — the fix expresses the existing, already-documented
  Entry Schema (`.claude/agents/parity-updater.md:40-56`), it does not invent new rules.
- Do not add `jsonschema` to `requirements.txt`/`requirements-knowledge.txt` — Design Decisions above
  resolve this by hand-rolling validation instead.
- Do not add a mutation CLI or any `docs/parity_ledger` write path inside `tools/parity_index.py`
  itself — the writer lives entirely in the new `tools/parity_ledger_writer.py`.
- Do not add duplicate-`id`-across-shards detection to `validate_entry()` — not one of the ticket's
  four enumerated rejection conditions; already caught downstream by `parity_index.build()`'s
  `DuplicateEntryIdError` on rebuild.
- Do not update `docs/parity_ledger/infrastructure.yaml`'s `INFRA-315` entry (confirmed stale,
  predates this ticket, describes the pre-rescope `parity_write_safety` metric design) — flagged in
  investigation.md as a follow-up, not touched here; doing so would violate "no ledger-content
  changes."
- Do not modify `tools/agent-monitoring/generate_retro.py`'s `_is_parity_index_build_call` /
  `_is_parity_ledger_yaml_write` matching logic, or `tools/agent-monitoring/post_tool_hook.py`'s
  `_input_summary` — that belongs to the sibling epic child
  `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`, not this ticket.
- Do not alter `tests/tools/test_gate_a_readpath_review.py`'s `_Adjudications` narrative text,
  `gate_a_corpus.json`, or `gate_a_results.json` — Step 4 touches only
  `_safe_find_p0_intersection`'s `except` clause and its import line.

## Dependency Map

- Step 1 (schema.json fix) — independent, no dependencies.
- Step 2 (parity_index_baseline.py docstring update) — depends on Step 1 (describes the fixed
  schema's shape).
- Step 3 (parity_ledger_scan.py §6.3 fix) — independent, can run in parallel with Steps 1-2.
- Step 4 (test_gate_a_readpath_review.py reconciliation) — depends on Step 3 (needs the new
  exception class to exist and be importable).
- Step 5 (writer validate_entry + write_entry, no rebuild) — depends on Step 1 conceptually (mirrors
  its fixed rule structure) but has no import-level dependency on it; should land after Step 1 so the
  mirrored rules are written against the corrected schema, not the broken one.
- Step 6 (wire rebuild-on-write) — depends on Step 5 (adds to the same function).
- Step 7 (parity-updater.md update) — depends on Steps 5-6 (documents the finished writer's real
  invocation shape).
- Step 8 (full scoped verification) — depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| The writer rejects a malformed entry (each of the 4 Scope conditions) with a clear, specific error — one real test per condition | Step 5 | `test_writer_rejects_bad_id_pattern`, `test_writer_rejects_verified_missing_v2_evidence`, `test_writer_rejects_verified_missing_test_path`, `test_writer_rejects_divergent_missing_v2_evidence`, `test_writer_rejects_divergent_missing_test_path`, `test_writer_rejects_divergent_missing_divergence_note`, `test_writer_rejects_p0_missing_test_path` |
| A successful validated write either rebuilds the derived index in the same run or leaves an unmissable staleness signal | Step 6 | `test_successful_write_rebuilds_index_in_same_run`, `test_failed_write_never_triggers_index_rebuild` |
| `.claude/agents/parity-updater.md` updated to use the new write path; "Entry Schema" section stays accurate or is updated | Step 7 | `test_parity_updater_agent_md_uses_new_write_path` |
| Gate A §6.2/§6.3 fixed (with tests) or explicitly deferred with written rationale | Step 3 (§6.3 fix), Step 4 (dependent-test reconciliation); §6.2 deferred in this plan's Design Decisions and Scope Guards, and already in investigation.md | `test_find_p0_intersection_malformed_shard_raises_labeled_error_not_crash`; §6.2 has no test (deferred, not implemented) |
| Scoped pytest run passes | Step 1, Step 8 (and every step's own Verify) | the seven commands listed in Step 8, including new `test_schema_json_parses_and_has_fixed_allof_structure` (`tests/tools/test_parity_ledger_schema.py`) added by Step 1 as direct, runtime regression-proof of the `schema.json` fix, independent of Step 5/6's hand-rolled `validate_entry()` mirror |

## Anti-Drift Notes

- **Hand-rolled validation vs. `schema.json` drift risk:** `validate_entry()` (Step 5) duplicates
  `schema.json`'s four rules as plain Python rather than interpreting the JSON file at runtime (per
  the `jsonschema`-avoidance Design Decision). Any future edit to `schema.json`'s `allOf` rules must
  be manually mirrored into `validate_entry()` — nothing enforces the two stay in sync automatically.
  This is a real, disclosed tradeoff, not an oversight.
- **Rebuild-on-write proves the writer's own behavior, not the retro metric.** Do not let the
  Completion Summary claim "the `parity_write_safety` metric now shows co-occurrence" — that is a
  separate, `generate_retro.py`-owned observability claim this ticket does not touch (see Design
  Decisions and Scope Guards). Only claim: "the writer rebuilds the index in-process (tested)" and
  "the agent is now instructed to also issue a visible build call (doc updated, tested)."
- **`_is_parity_ledger_yaml_write`'s numerator will structurally shrink going forward.** Once
  `parity-updater` stops using raw `Edit`/`Write` on `docs/parity_ledger/*.yaml` (replaced by one
  `Bash` call to the writer), `generate_retro.py`'s `_is_parity_ledger_yaml_write`
  (`tools/agent-monitoring/generate_retro.py:251`, matches only `Edit`/`Write` tool rows) will stop
  detecting real future parity-ledger writes at all. This is a known, disclosed side effect of fixing
  the underlying tool correctly — not a regression to fix in this ticket (out of scope, belongs to
  the sibling metric-owning ticket), but must not surface as a surprise later.
- **§6.2 stays deferred.** `_PATH_REF_RE` (`tools/parity_index.py:66`) not recognizing
  `.claude/`-prefixed paths is a read-path gap explicitly reserved for a future Phase-3 scoping
  ticket per `docs/ai/parity_readpath_gate_a_decision.md` §5. Do not fix it "for free" while touching
  adjacent code in Step 6 for an unrelated reason (importing `build`/`check_staleness` does not
  require touching `_populate_ref_tables` or `_PATH_REF_RE` at all).
- **`INFRA-315` is already stale** (describes the pre-rescope `parity_write_safety` metric design,
  predates `TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE`) — flagged, not fixed here; any ledger
  content edit is out of scope for this ticket regardless.

## Deviations

- **Steps 5 and 6 landed as a single file write, not two sequential edits.** `tools/parity_ledger_writer.py`
  was written once with `validate_entry()`, `write_entry()`, and the in-process `build()` rebuild call
  all present from the start, rather than authoring Step 5's `write_entry()` first without a rebuild
  and then adding the rebuild call as a distinct Step 6 edit. The final code and its test coverage
  (`tests/tools/test_parity_ledger_writer.py`, including `test_failed_write_never_triggers_index_rebuild`,
  which monkeypatches `parity_ledger_writer.build` to prove the rebuild is gated strictly on write
  success) match exactly what Step 6's own "Change" description specifies as the end state — no
  step's actual content was skipped or altered, only their write-order was collapsed. Pure editing-order
  economy, not a scope or behavior deviation.
- **Pre-existing test failures observed, confirmed unrelated to this ticket, left untouched (not
  silently ignored):** `tests/tools/test_gate_a_readpath_review.py` has 3 failures / 7 errors (missing
  `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_corpus.json` and `gate_a_results.json` --
  those two JSON fixture files were never committed to the repo, per `git log --all --diff-filter=A`
  finding zero add-commits for either path) and `tests/tools/test_parity_index_baseline.py` has 3
  failures (a hardcoded historical `missing_test_path_count` assertion of 1347 vs. the live ledger's
  actual 1343, and a missing doc file `docs/plans/agent_infrastructure/parity_ledger_sqlite_context/
  v1_decisions_phase0.md`). Verified via `git stash` (stashing every file this ticket touched, then
  re-running) that all 6 failures/7 errors are byte-identical in cause and count before and after this
  ticket's changes -- none originate from Steps 1-7. `TestNoMutation::
  test_gate_a_review_leaves_protected_files_byte_identical` (the one test in that file load-bearing for
  this ticket's own Step 3/4 correctness) passes both before and after. Out of scope to fix here (no
  `docs/parity_ledger/*.yaml` content edits permitted by this ticket's own Scope Guards, and the missing
  fixture/doc files belong to their originating tickets, not this one) -- flagged here per the
  "never silently deviate" rule rather than left as an unexplained surprise in Step 8's run.
