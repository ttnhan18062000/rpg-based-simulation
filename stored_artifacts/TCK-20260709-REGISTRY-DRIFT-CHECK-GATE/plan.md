---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260709-REGISTRY-DRIFT-CHECK-GATE
artifact_type: plan
tags: [testing, observability]
---

# Implementation Plan — TCK-20260709-REGISTRY-DRIFT-CHECK-GATE

## Summary

Add a `check: bool = False` keyword-only parameter to `generate_registry()` in
`tools/generate_registry.py` that, when `True`, computes `output_entries` exactly as today but
never writes to disk — instead it loads the existing on-disk YAML (if present) via
`yaml.safe_load`, compares the **parsed entry lists** (never raw file text, to avoid the
live-timestamp-header false positive), prints a readable diff summary, and returns a distinct exit
code (`2`) when drift is found. Wire this through a new `--check` CLI flag in `main()`. Add all new
tests to the existing `tests/tools/test_generate_registry.py` file, including one exercising
`--check` against the real repo root inside `pytest tests/tools` — which the `api-tools` CI job
already runs — giving CI coverage with zero `.github/workflows/test.yml` diff. Add a new
`INFRA-264` parity ledger entry documenting this backstop as a companion to (not a duplicate of)
`INFRA-183` and `INFRA-263`. This plan resolves all four questions the investigation flagged as
open, adopting the investigator's own recommendations verbatim (rationale given per step/decision
below) — no items are deferred to human review.

## Resolved Decisions (adopted from investigation.md's recommendations)

1. **CI wiring — pytest lane, zero `.yml` diff.** A new test in
   `tests/tools/test_generate_registry.py` runs `--check` (via `main()`/subprocess, see Step 3)
   against the real repo root, colocated in the `api-tools` job's existing `pytest tests/tools`
   invocation. Rationale: satisfies the AC's own "e.g. ... or a dedicated step" wording (either
   form is acceptable), and reusing an already-green CI lane is lower-risk than adding a new `.yml`
   step to a job (`arch-docs`) that doesn't otherwise touch `docs/REGISTRY.yaml`.
2. **Exit code 2 for drift-detected.** Distinct from exit 1 (frontmatter errors) and exit 0
   (success/in-sync). Rationale: matches `tools/evaluate_simq.py`'s existing `sys.exit(2)`
   precedent for "check failed, different failure class than a fatal input error."
3. **`--check` + pre-existing frontmatter errors → short-circuit to exit 1.** The diff step is
   never attempted when `doc_errors` is non-empty. Rationale: a tree with un-computable entries
   cannot produce a trustworthy "correct" comparison target; today's non-`--check` path already
   treats frontmatter errors as the terminal condition, so `--check` inherits that same precedence
   rather than inventing new interaction semantics.
4. **Missing on-disk output file in `--check` mode → treat as drift, exit 2.** Rationale: an absent
   file is definitionally not in sync with what generation would produce; treating it as a third,
   separate exit-code meaning would add complexity with no behavioral benefit over folding it into
   the existing "drift" class.

## Steps

### Step 1 — Add `check` parameter and diff logic to `generate_registry()`
**Files:** `tools/generate_registry.py`

**Change:**
- Change the signature at line 408 from `def generate_registry(root: Path, output: Path) -> int:`
  to `def generate_registry(root: Path, output: Path, check: bool = False) -> int:`. The keyword
  defaults to `False` so every existing two-positional-arg call site (the ~35+ tests, the
  `Makefile` `docs-registry` target, and `check_registry_entry_regenerated()` in
  `tools/gate_checks/done_checker_static.py`) is unaffected.
- Keep lines 410-421 (compute `doc_entries`, `doc_errors`, `ticket_entries`, `all_entries`,
  `output_entries`, strip `None last_verified`) exactly as-is and unconditional — these must run
  identically whether or not `check` is set, since the diff needs a freshly computed
  `output_entries` regardless.
- **Immediately after `output_entries` is finalized (post line 421), insert the frontmatter-error
  short-circuit for `check` mode**: if `check` is `True` and `doc_errors` is non-empty, skip the
  diff step entirely and fall through to the existing `doc_errors`-triggers-return-1 branch (i.e.
  do not attempt the disk-read/diff before that check — reorder so the `doc_errors` check happens
  first when `check=True`, or simply let the existing end-of-function `if doc_errors: return 1`
  branch fire before any diff code runs by placing the new diff branch after it). Resolved decision
  #3 above.
- **Branch on `check`:**
  - If `check` is `False` (default): keep the existing behavior byte-identical — build the
    timestamp header (lines 423-428), `output.parent.mkdir(...)`, `output.open("w")` +
    `_dump_yaml()` (lines 430-432), print the "Wrote N entries" line, `print_summary()`, then the
    existing `doc_errors` → return 1 / else return 0 logic (lines 437-443). **Do not alter this
    branch's behavior at all.**
  - If `check` is `True`:
    - First, if `doc_errors` is non-empty: print the same frontmatter-error stderr block used
      today (lines 438-440) and `return 1` — never proceed to the diff. (Decision #3.)
    - Else, attempt to read the on-disk `output` path:
      - If `output` does not exist: print a "would create N entries (file missing)" style message
        and `return 2`. (Decision #4 — missing file is drift.)
      - If `output` exists: `yaml.safe_load()` its text to get the on-disk entry list. Compare it
        against the freshly computed `output_entries` — **compare the parsed Python
        list-of-dicts, never the raw file text and never anything derived from the header lines
        23-28**. This is the investigation's top-flagged hazard: the header's `# Generated: {ts}`
        line changes on every run and must play no part in the comparison.
      - If the parsed lists are equal: print an "in sync, N entries" message, `return 0`. Do not
        write to `output` in this branch under any circumstance.
      - If they differ: print a readable, substantive diff summary to stdout/stderr — at minimum,
        for each entry present in one side but not the other (matched by `path` key) note
        added/removed, and for entries present in both but with different field values note which
        entry `path` changed and which field(s) differ. Do not write to `output`. `return 2`.
    - Use `yaml.safe_load` for the parse (PyYAML is a hard `requirements.txt` dependency per
      investigation.md — no fallback parser needed; if `_HAS_PYYAML` is somehow `False`, raise a
      clear error rather than silently mis-comparing, since the module already has a
      `_HAS_PYYAML` guard pattern to follow at line ~112-128).
- Update the module docstring (lines 9-13) to document the new `--check` flag, exit code `0`
  (in sync / success), `1` (doc frontmatter errors — unchanged meaning, takes precedence over
  drift), and `2` (drift detected in `--check` mode).

**Do NOT touch:** `collect_docs`, `collect_tickets`, `sort_entries`, `_normalise_entry_for_output`,
`_SKIP_DOC_SUBDIRS`, `join_artifact_files`, `_dump_yaml`'s write-serialization logic, or the
existing non-`check` return-code semantics (`0`/`1`). Do not reorder the two existing positional
parameters. Do not change the `Makefile`'s `docs-registry` target's invocation (it calls
`generate_registry.py` with no `--check`, must keep writing unconditionally).

**Verify:** `test_check_writes_no_file_when_in_sync`, `test_check_exits_nonzero_on_stale_fixture`,
`test_check_ignores_header_timestamp_drift`, `test_check_reports_readable_diff_summary`,
`test_check_writes_no_file_on_missing_output`, `test_check_short_circuits_on_doc_frontmatter_error`,
`test_check_mode_backward_compat_default_still_writes` (all from test_plan.md, added in Step 3).

### Step 2 — Add `--check` CLI flag in `main()`
**Files:** `tools/generate_registry.py`

**Change:** In `main()` (line 446 onward), add a new `argparse` flag:
```python
parser.add_argument(
    "--check",
    action="store_true",
    help="Dry-run: diff in-memory regeneration against on-disk output, write nothing, "
         "exit 0 (in sync) / 1 (doc frontmatter errors) / 2 (drift detected)",
)
```
Change the final call from `sys.exit(generate_registry(root, output))` to
`sys.exit(generate_registry(root, output, check=args.check))`.

**Do NOT touch:** the existing `--root` and `--output` argument definitions (lines 450-459), the
`root`/`output` path-resolution logic (lines 462-465).

**Verify:** `test_cli_check_flag_end_to_end` (subprocess-based, from test_plan.md, added in Step 3).

### Step 3 — Add new tests to `tests/tools/test_generate_registry.py`
**Files:** `tests/tools/test_generate_registry.py`

**Change:** Add a new `TestCheckMode` class (in-process, calling `generate_registry(..., check=True)`
directly) containing:
- `test_check_writes_no_file_when_in_sync`
- `test_check_exits_nonzero_on_stale_fixture` (assert `rc == 2`, distinct from `1`)
- `test_check_ignores_header_timestamp_drift` (the single most important new test — write an
  on-disk file with matching entries but a stale/different header timestamp, assert `rc == 0`)
- `test_check_reports_readable_diff_summary` (assert the differing entry's `path` string appears
  in captured output; do not assert an exact string format)
- `test_check_writes_no_file_on_missing_output` (assert `rc == 2`, no file created)
- `test_check_short_circuits_on_doc_frontmatter_error` (assert `rc == 1`, mirroring the existing
  `test_registry_exits_nonzero_on_missing_doc_frontmatter` fixture shape)
- `test_check_mode_backward_compat_default_still_writes` (call `generate_registry(root, output)`
  with exactly two positional args, no `check` kwarg at all; assert file is written and `rc`
  semantics unchanged)

Add a separate `TestCLICheckFlag` class (subprocess-based, per the
`TestValidateFrontmatterAcceptsOutput` pattern in
`tests/tools/test_add_frontmatter_tickets.py:337-417`) containing:
- `test_cli_check_flag_end_to_end` — runs
  `subprocess.run([sys.executable, str(GENERATE_REGISTRY_PATH), "--root", str(tmp_path), "--output",
  str(fixture_registry), "--check"], capture_output=True, text=True)` against both a matching
  fixture (assert `returncode == 0`) and a stale one (assert `returncode == 2`).

Resolve the CI-wiring decision (Decision #1) by extending `TestRealDocsTree` (or adding a sibling
test in the same style as `test_registry_exits_zero_on_real_docs_tree`) with a new test that runs
`--check` (via `main()`/subprocess, no `--root`/`--output` override) against the **real repo
root and real `docs/REGISTRY.yaml`**, asserting `rc == 0` (in sync) today. This test running inside
`pytest tests/tools` is what gives CI coverage — `.github/workflows/test.yml`'s `api-tools` job
already runs `pytest tests/tools` (confirmed in investigation.md), so no `.yml` edit is needed.
Name it something explicit, e.g. `test_check_flag_detects_no_drift_against_real_registry`, placed
in `TestRealDocsTree` alongside its sibling `test_registry_exits_zero_on_real_docs_tree`.

Do not hardcode any specific entry count in any new test — use only fixed, known `tmp_path`
fixture entry sets for the stale/matching comparison tests, and only assert `rc == 0` (not an
entry count) for the real-tree test.

**Do NOT touch:** the existing 41 tests in this file (`TestDocEntryGeneration`,
`TestTicketEntryGeneration`, `TestArtifactJoin`, `TestSortOrder`, `TestTitleExtraction`,
`TestRelatedCodeAreas`, `TestYAMLOutput`, `TestRealDocsTree`'s existing two tests, `TestEdgeCases`)
— only append new classes/tests.

**Verify:**
```
python3 -m pytest tests/tools/test_generate_registry.py -v --tb=short
```
All ~41 existing tests plus the ~9 new ones pass.

### Step 4 — Cross-check the sibling ticket's call site is unaffected
**Files:** none changed; verification only.

**Change:** No code change. Run the regression cross-check from test_plan.md to confirm
`check_registry_entry_regenerated()` (`tools/gate_checks/done_checker_static.py`, added by the
sibling ticket `TCK-20260709-REGISTRY-REGEN-ON-CLOSE` this session) still calls
`generate_registry(root, registry_output)` with exactly two positional args and unchanged write
behavior — the new `check` kwarg's default (`False`) must make this call site's behavior
byte-identical to before this ticket.

**Do NOT touch:** `tools/gate_checks/done_checker_static.py`, `.claude/workflows/implement-ticket.js`
— both are the sibling ticket's territory and are already done/closed.

**Verify:**
```
python3 -m pytest tests/tools/test_generate_registry.py tests/tools/test_done_checker_static.py -v --tb=short
```
`test_check_registry_entry_regenerated_passes_when_entry_present` and
`test_check_registry_entry_regenerated_fails_when_entry_absent` (existing tests) still pass
unmodified.

### Step 5 — Add parity ledger entry `INFRA-264`
**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Append a new entry after `INFRA-263` (currently the highest-numbered entry, ending
around line 3737), following the exact YAML shape of `INFRA-263`:
```yaml
- id: INFRA-264
  text: >
    CI drift-detection backstop -- generate_registry.py --check regenerates the registry
    in-memory and diffs the parsed entry list (not raw file text/header timestamp) against
    the checked-in docs/REGISTRY.yaml, writing nothing and exiting 2 on mismatch, 1 on
    pre-existing doc-frontmatter errors (short-circuits before the diff), 0 when in sync.
    Runs inside tests/tools/test_generate_registry.py against the real repo root, which the
    api-tools CI job already executes via `pytest tests/tools` -- no .github/workflows/test.yml
    edit required. Independent of, and complementary to, INFRA-263's Finalize-phase
    auto-regen-and-write: this entry catches drift even if that Finalize hook is bypassed,
    skipped, or fails silently.
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: >
    tools/generate_registry.py::generate_registry (check kwarg) + main() --check flag +
    tests/tools/test_generate_registry.py::TestCheckMode,
    TestCLICheckFlag, TestRealDocsTree (api-tools CI job runs pytest tests/tools)
  proof_type: null
  test_path: tests/tools/test_generate_registry.py::test_check_flag_detects_no_drift_against_real_registry
  divergence_note: null
  support_boundary: >
    Doc tooling only -- no simulation behavior involved (mirrors INFRA-183's support_boundary).
    Does not touch, extend, or duplicate INFRA-183 (output shape) or INFRA-263 (Finalize-time
    write-and-verify invocation timing); this is a third, distinct guarantee (CI backstop).
```
Adjust `v2_evidence`/`test_path` to the exact test function names actually used if Step 3's
implementation names them differently than proposed here.

Optionally (at this step's discretion, low priority): add a one-line `v2_evidence` addendum to
`INFRA-183` noting the `--check` flag now exists on the same tool, without changing `INFRA-183`'s
`text` or `status`. This is optional polish, not required for AC satisfaction — do not expand
`INFRA-183`'s scope or restate `INFRA-264`'s content inside it.

**Do NOT touch:** `INFRA-183`'s `text`, `status`, or `test_path` fields; `INFRA-263` in any way
(it is a closed sibling ticket's entry — this ticket must not fold into or edit it, per both
tickets' own explicit non-overlap statements).

**Verify:** No automated test covers parity ledger YAML content directly beyond schema validation
(if `tools/validate_frontmatter.py` or a parity-ledger schema check runs in CI, confirm the new
entry parses — visually confirm YAML validity via `python3 -c "import yaml;
yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`).

## Scope Guards

- Do not touch `tools/gate_checks/done_checker_static.py` or `.claude/workflows/implement-ticket.js`
  — that is `TCK-20260709-REGISTRY-REGEN-ON-CLOSE`'s territory, already implemented and closed this
  session.
- Do not add or edit any step in `.github/workflows/test.yml` — the CI-wiring decision (Decision #1)
  explicitly adopts the zero-`.yml`-diff pytest-lane approach.
- Do not touch `Makefile`'s `docs-registry` target — its unconditional-write meaning must be
  preserved exactly. No new Makefile target is required by this ticket's AC; do not add one
  speculatively.
- Do not touch `collect_docs`, `collect_tickets`, `sort_entries`, `_normalise_entry_for_output`,
  `_SKIP_DOC_SUBDIRS`, `join_artifact_files`, or any other entry-computation internals in
  `tools/generate_registry.py` — this ticket is additive only (new parameter + new branch).
- Do not touch `tools/validate_frontmatter.py`, `tools/tag_registry.py`, or
  `tools/registry_query.py` — listed as Related Code Areas for context only, not in scope for
  changes.
- Do not fix `TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL` or
  `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES` territory (stale skip-list entries / frontmatterless
  tickets) even if `--check` against the real tree surfaces them — those are separately scoped
  tickets.
- Do not hardcode a specific entry count against the real `docs/REGISTRY.yaml` or `docs/` tree in
  any new test.
- Do not alter the existing `0`/`1` exit-code meanings for the non-`check` code path.
- Do not diff raw file text (including the `# Generated: <ts>` header) anywhere in the `--check`
  implementation — comparisons must be over `yaml.safe_load`-parsed entry lists only.
- Do not edit `INFRA-263`'s YAML entry; add `INFRA-264` as a new, separate entry.

## Dependency Map

- Step 1 (core `check` logic in `generate_registry()`) must land before Step 2 (CLI flag wiring
  depends on the `check` kwarg existing) and before Step 3 (tests exercise both).
- Step 2 depends on Step 1.
- Step 3 depends on Steps 1 and 2 (tests exercise both the in-process function and the CLI flag).
- Step 4 (regression cross-check) depends on Step 1 being complete (verifies the sibling call site
  is unaffected by the new signature) — can run any time after Step 1, but is most meaningful after
  Step 3's full test suite is in place.
- Step 5 (parity ledger) depends on Steps 1-3 being complete — the `test_path` and `v2_evidence`
  cite the actual implementation and test names, so it must be written last, after implementation
  details (exact test function names, exact exit-code branch structure) are finalized.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `--check` regenerates in-memory, diffs against on-disk `docs/REGISTRY.yaml`, exits non-zero with readable diff/summary on mismatch, exits 0 when in sync, writes no file in `--check` mode | Step 1, Step 2 | `test_check_writes_no_file_when_in_sync`, `test_check_exits_nonzero_on_stale_fixture`, `test_check_ignores_header_timestamp_drift`, `test_check_reports_readable_diff_summary`, `test_check_writes_no_file_on_missing_output`, `test_cli_check_flag_end_to_end` |
| Frontmatter-error exit code (1) and drift-detected exit code are distinguishable | Step 1 (Decision #2, #3) | `test_check_short_circuits_on_doc_frontmatter_error`, `test_check_exits_nonzero_on_stale_fixture` (asserts `rc == 2 != 1`) |
| CI job/step runs `--check` against the live tree, catching drift independent of the Finalize hook | Step 3 (real-tree test inside `api-tools`'s existing `pytest tests/tools`) | `test_check_flag_detects_no_drift_against_real_registry` (name per Step 3, in `TestRealDocsTree`) |
| New test(s) in `tests/tools/test_generate_registry.py` exercise `--check` against a deliberately-stale fixture (non-zero exit) and a matching fixture (zero exit) | Step 3 | `test_check_writes_no_file_when_in_sync`, `test_check_exits_nonzero_on_stale_fixture`, `test_cli_check_flag_end_to_end` |

## Anti-Drift Notes

- **Header-timestamp false positive is the top implementation risk** (investigation.md's most
  heavily flagged hazard). The `# Generated: {ts}` line (lines 423-428) changes every run; any
  raw-text diff will report drift on every invocation, permanently breaking the gate in the
  opposite direction (always-red) or, if both sides happen to be generated in the same test run,
  falsely appear to pass (`test_check_ignores_header_timestamp_drift` exists specifically to catch
  this). The diff must operate on `yaml.safe_load`-parsed entry lists only.
- **Backward compatibility of the two-positional-arg call signature is load-bearing**: the
  `Makefile`'s `docs-registry` target and `check_registry_entry_regenerated()`
  (`tools/gate_checks/done_checker_static.py`, from the sibling ticket closed this session) both
  call `generate_registry(root, output)` with exactly two positional args and expect the existing
  write-and-return-0/1 behavior. The new `check` parameter must be keyword-only with default
  `False` and must not change default-path behavior in any way.
- **This ticket's `--check` gate and `INFRA-263`'s Finalize-time auto-regen-and-write are
  deliberately independent mechanisms** (prevention vs. backstop) per both tickets' own scope
  text — do not merge their code paths, do not fold `INFRA-264` into `INFRA-263`'s ledger entry,
  and do not have `check_registry_entry_regenerated()` call `generate_registry(..., check=True)`
  (it must keep calling in write mode).
- **No test should assert a hardcoded entry count** against the real `docs/REGISTRY.yaml` or
  `docs/` tree — `TCK-20260709-REGISTRY-COUNT-STALE-DOCS` already had to remove exactly this kind
  of brittle assertion this session.
- **PyYAML is a hard dependency** (`requirements.txt`) — the `--check` parse step should use
  `yaml.safe_load` directly; no stdlib fallback parser is needed, but do not silently assume
  `_HAS_PYYAML` is `True` without the same guard pattern the module already uses for the write
  path (lines ~112-128), to fail clearly rather than mis-comparing if it's ever absent.
