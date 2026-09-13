---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260912-WORKING-LOG-APPEND-HELPER
artifact_type: plan
tags: [data-quality, process-improvement]
---

# Plan — TCK-20260912-WORKING-LOG-APPEND-HELPER

Evidence in `investigation.md`. Order: build the helper, switch the one real caller to it, point
the Finalize prose at it, add the sole-writer guard, update the parity ledger, update CLAUDE.md.

**Revised after Review round 1 (NEEDS_CHANGES, 3 blocking findings, all independently
re-confirmed before this revision — see Deviations section at the bottom for the record).**

## Step 1 — The helper module

New `tools/working_log_writer.py` (beside the existing `tools/working_log_parser.py`, per the
ticket's own Assumptions — one owner, not a particular location, but pairing reader/writer by
name is the clearest signal of that ownership to a future reader).

```python
def append_working_log_row(
    timestamp: str, ticket_id: str, title: str, status: str, summary: str, artifacts_path: str,
    path: Path = _WORKING_LOG_PATH,
) -> None:
```

- `_WORKING_LOG_PATH = Path("tickets/working_log.csv")` is a **module-level constant**, not an
  inline default expression — this is load-bearing for Step 4's AST-based guard, which resolves a
  call's path argument back to a literal by walking name bindings; a module-level constant is a
  single, unambiguous binding site to resolve against, where an inline `Path("...")` default
  literal sitting only in the function signature is exactly the indirection Review found the
  original grep-based design blind to.
- Opens `path` with `open(path, "a", newline="", encoding="utf-8")` (matches the existing call's
  `newline=""` — required for `csv.writer` to own line-ending control, not the platform).
- `csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")`, `.writerow([timestamp,
  ticket_id, title, status, summary, artifacts_path])` — the exact 6-column order
  `working_log_parser.HEADER_FIELDS` expects.
- No monitoring side effects (no run/event recording) — this module's only job is the CSV row,
  matching the ticket's explicit Out of Scope.
- Docstring names both call sites it will have (the closure script, `implement-ticket.js`'s
  Finalize) so it can't quietly drift into single-caller assumptions later.

**CLI wrapper, for Step 3's invocation contract:**

```python
def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", required=True, help="Path to a JSON file: "
                         "{timestamp, ticket_id, title, status, summary, artifacts_path}")
    args = parser.parse_args(argv)
    fields = json.loads(Path(args.data_file).read_text(encoding="utf-8"))
    append_working_log_row(**fields)
```

Reads the 6 field values from a **file**, not a shell/CLI argument — see Step 3 for why.

## Step 2 — Switch the one real caller

`tools/agent-monitoring/record_hand_orchestrated_closure.py`: replace the inline `with
working_log_path.open(...) as f: csv.writer(...).writerow(...)` block with a call to
`append_working_log_row(...)`, passing the same 6 values in the same order. Keep the existing
`try/except OSError` / `log_ok` warning behavior around the call — this ticket does not change
error handling, only who performs the write.

## Step 3 — Point Finalize at the helper, without reintroducing free-text shell/Python embedding

**Why not `python3 -c "...append_working_log_row(...)"` with inline values:** Finalize step 4's
`title`/`summary` are arbitrary agent-authored text (this ticket's own title contains backticks
and an em-dash — a real, not hypothetical, case). Asking the dispatched Finalize agent to hand-
embed that text as Python string-literal source inside a `-c` argument reintroduces exactly the
per-agent-improvisation hazard this ticket exists to close, just moved from CSV-quoting to
shell/Python-quoting. Review's Finding 2 is right that "or equivalent" was not concrete enough.

**Contract:** Finalize step 4's instruction becomes:
1. Use the `Write` tool to create a JSON file (e.g. a scratch path under the ticket's own
   `stored_artifacts/${tid}/` or an ephemeral tmp path) containing exactly `{"timestamp": ...,
   "ticket_id": ..., "title": ..., "status": "DONE", "summary": ..., "artifacts_path": ...}`. The
   `Write` tool's content parameter is not shell-interpreted, so arbitrary title/summary text
   (quotes, backticks, `$`, embedded newlines) needs no escaping at all here — this is the actual
   fix, not a different flavor of escaping.
2. Run `python3 tools/working_log_writer.py --data-file <that path>` via `bash()`.

This mirrors this repo's own existing pattern for the identical class of problem:
`record_events.py`/`record_run.py` already take structured data via `--data '<json>'` rather than
positional free-text args (investigation.md's own §1 evidence), because command-line argument
embedding has the same hazard as `-c` source embedding. This ticket's contract goes one step
further (a file instead of an inline `--data` string) specifically because `--data` still requires
the JSON *string itself* to survive one layer of shell-argument quoting, and a title/summary
containing a single quote can still break that; a file has no such layer at all.

Keep the field-meaning comments (what `timestamp`/`summary`/`artifacts_path` should contain) in
the JS prose — only the *mechanism* of writing changes, not what a Finalize agent must decide to
put in each field.

Add a pin test, `tests/tools/test_finalize_working_log_uses_helper_pin.py`, mirroring
`test_finalize_phase_status_instruction_pin.py`'s raw-source-text pattern, scoped to the
**Finalize agent's own prompt string** specifically — confirmed by direct read that
`phase('Finalize')`'s block also contains 4 unrelated, legitimate orchestrator-run `python3 -c`
self-checks *after* the agent's prompt closes (`finalizeCheckOutput`/`monitoringCheckOutput`/
`tagDriftCheckOutput`/`phaseMetaCheckOutput`), so a negative assertion scanning the whole
`phase('Finalize')` block would be false from the moment it's written, before any regression ever
occurs. Scope the search to the substring between the prompt's own opening anchor
(`` `Finalize ticket ${tid}` ``, unique to this one prompt) and its closing anchor (`` Report each
step: DONE / SKIPPED (reason).`, `` — the literal end of the template string, immediately before
`{ label: 'finalize' }`) — not the wider phase block.

Within that scoped substring, assert:
(a) `working_log_writer.py` and `--data-file` both appear, and step 4's text (identifiable by its
own "4. Append to tickets/working_log.csv" leading anchor) precedes step 5's text ("Move
staging_artifacts", matching the JS's own step ordering);
(b) the substring `python3 -c` does **not** appear anywhere within that same scoped substring —
not adjacency to a specific function name (Review round 2's finding: a realistic reintroduction of
the rejected inline-`-c` pattern would have an import statement, semicolon, or quotes between the
flag and the call, so requiring literal adjacency to `append_working_log_row(` would not fire on
it either way; scoped-but-unqualified "does `python3 -c` appear inside this one prompt string at
all" is both correct today — the prompt has zero legitimate uses of `-c` inline scripting once
step 4 becomes a plain multi-arg `bash()` call — and the assertion that actually catches the
regression).

## Step 4 — Sole-writer guard, AST-based (not grep)

**Why not grep:** Review's Finding 1 is confirmed correct against this very plan's own Step 1 —
the write call is `open(path, "a", ...)`; the literal string `"tickets/working_log.csv"` lives only
in `_WORKING_LOG_PATH`'s own assignment line, not on the `open(` line itself. A literal-text grep
requiring both the path string and an `open(`-shaped call on the same match would find **zero**
callsites anywhere, including the helper's own — worse than useless, since a test asserting
"exactly one match" would pass on zero as easily as on one, hiding exactly the regression it
exists to catch.

**Design:** `tests/tools/test_working_log_writer.py::test_working_log_csv_has_exactly_one_writer`
walks the `ast` of every `.py` file under `tools/` (not `tests/` — fixtures there legitimately use
`tmp_path`, a different, unrelated string):

1. Parse each file with `ast.parse`.
2. Build one **module-level** map of `name -> literal string` from every top-level assignment
   `name = "literal"` or `name = Path("literal")`.
3. For each function, build a **function-local** map from every parameter whose default is: a
   string/`Path("literal")` literal directly, **or** a `Name` that resolves against the
   module-level map from step 2 (exactly `_WORKING_LOG_PATH`'s own case in Step 1 — a
   parameter default referencing a module constant, not embedding the literal inline).
   Also include any local `name = "literal"` / `name = Path("literal")` assignment inside the
   function body. This is deliberately single-hop beyond the module map (a function-local name
   bound to *another* function-local name is not chased further) — sufficient for every real
   writer in this codebase today (confirmed in investigation.md §1: no writer uses deeper
   indirection than this), and a resolver that silently guesses through longer chains would be
   exactly the kind of "looks thorough, isn't" mechanism this ticket argues against.
4. Walk every `ast.Call` node. Match `open(arg0, arg1, ...)` or `<expr>.open(arg0, ...)` shapes.
   Resolve `arg0`: if it's a string/`Path(...)` literal directly, take it as-is; if it's a `Name`,
   look it up first in the enclosing function's local map (step 3), falling back to the
   module-level map (step 2) if not found there.
5. If the resolved value equals `"tickets/working_log.csv"` (compare as plain strings; `Path(...)`
   wrapping doesn't change the comparison) **and** the mode argument (positional `arg1` or a
   `mode=` keyword) indicates write/append (`"a"`, `"w"`, `"a+"`, `"w+"`, `"x"` — no default-mode
   assumption, since `Path.open()`'s own default is `"r"`, not write), record this file:line as a
   writer callsite.
6. Assert the writer-callsite list has exactly one entry, and its file is
   `tools/working_log_writer.py`.

Verified against this exact plan's own Step 1 design before Implement writes it: `_WORKING_LOG_PATH
= Path("tickets/working_log.csv")` binds the module-level name (step 2); `path: Path =
_WORKING_LOG_PATH` binds the parameter's default to that same name (step 3's Name-resolves-
against-module-map case); `open(path, "a", ...)` resolves `path` through the function-local map to
`_WORKING_LOG_PATH`'s literal, mode `"a"` matches — correctly detected as the one writer.

A synthetic-fixture negative test (per test_plan.md) proves the guard actually fires on a second
writer, not just that it currently reports one.

## Step 5 — Parity ledger: update INFRA-416, don't leave it stale

**Review Finding 3, confirmed:** `docs/parity_ledger/infrastructure.yaml`'s `INFRA-416` entry
(status `verified`, priority `P1`) has `v2_evidence` that literally cites
`tools/agent-monitoring/record_hand_orchestrated_closure.py:207 -- csv.writer(f,
quoting=csv.QUOTE_MINIMAL, lineterminator="\n")` as its proof. Step 2 replaces that exact call
site with a call into the helper, so that citation goes stale the moment Step 2 lands.

`write_entry()` does a **full-entry replace-by-id** (`tools/parity_ledger_writer.py:139-143`:
`entries[index] = entry`), not a partial merge — confirmed by direct read. `.claude/agents/
parity-updater.md`'s own documented procedure (Steps 2-3) is exactly "read the relevant YAML file
to find the entry... and to see its current field values" then "construct the full entry dict" —
this step must follow that same read-then-construct-full-dict shape, not a bare field-name mention.

**Concretely:**
1. Read `INFRA-416`'s current entry from `docs/parity_ledger/infrastructure.yaml` (via
   `yaml.safe_load`, or by finding it in the file directly) to capture its current `text`, `status`,
   `priority`, `divergence_note`, `proof_type`, and any other field verbatim.
2. Construct the full entry dict: identical to what was read, except `v2_evidence` now cites
   `tools/working_log_writer.py::append_working_log_row()` (the new site that actually emits
   `lineterminator="\n"`) instead of the old `record_hand_orchestrated_closure.py:207` line, and
   `test_path` gains `test_working_log_csv_has_exactly_one_writer` alongside the existing
   `test_merge_union_no_cr_bytes.py`/`test_merge_union_crlf_duplication_repro.py` entries (those
   two stay unchanged and still pass — they check byte-level file output, not source line numbers).
3. Pass that full dict to `write_entry('infrastructure.yaml', entry)` — never a raw YAML edit, and
   never a dict built from scratch with only the two changed fields.

Test (test_plan.md Step 5): after `write_entry()` runs, re-read `INFRA-416` and assert every field
other than `v2_evidence`/`test_path` is byte-identical to what it was before this step — the
concrete, automated version of "preserve everything else," not just a prose instruction to be
careful.

## Step 6 — CLAUDE.md

Add one sentence to the After Work bullet about `tickets/working_log.csv`: append via
`tools/working_log_writer.py::append_working_log_row()`, never hand-roll the write (matching the
existing "never insert after the header" sentence's own register).

## Step 7 — Unit tests for the helper itself

`tests/tools/test_working_log_writer.py`:
- A field containing a comma, a quote, and an embedded newline round-trips correctly through
  `working_log_parser.parse_working_log()` afterward (proves the two modules agree on the format,
  not just that the writer runs).
- Output ends in a bare `\n`, zero `\r` bytes anywhere in the appended row.
- Appends after existing content, never truncates, never inserts before the header.
- `record_hand_orchestrated_closure.py`'s own existing tests (`tests/tools/
  test_record_hand_orchestrated_closure.py`) pass unmodified — confirms Step 2's swap preserved
  behavior exactly.

## Honesty in the Completion Summary (carried from the ticket's own Assumptions)

State plainly: this is one sanctioned writer plus a CI guard that catches a second write path
appearing, not a hard lock. An agent can still open the file directly and write to it; nothing in
the filesystem or harness prevents that. Claiming prevention would overstate what Step 4's guard
actually does (catch it in CI on the next run, not block it at the moment of writing).

## Out of Scope (carried from the ticket)

- The row format itself (columns, timestamp precision, quoting) — centralizing who writes it, not
  redesigning what is written.
- Monitoring run/event recording — stays with `record_hand_orchestrated_closure.py`.
- Retrofitting historical rows — PR #167 already normalized line endings on `main`.
- `agent-monitoring/data/*/*.jsonl` writers — `tools/agent-monitoring/writer.py` already owns those.

## Risks

- **Import path — resolved before Implement**: `tools/agent-monitoring/done_ticket_monitoring_
  coverage.py` already imports a `tools/`-level sibling from inside `tools/agent-monitoring/` via
  `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` then `from validate_frontmatter
  import extract_frontmatter` — confirmed by direct read, this session. `record_hand_orchestrated_
  closure.py` uses the identical `.parent.parent` insert for `working_log_writer`.
- **AST resolver false positives/negatives**: the design in Step 4 must not flag the parser's own
  read-only `open(path, newline="")` call (mode defaults to `"r"`, excluded by the write-mode
  check) or the identical-shaped `open()` calls in unrelated modules that happen to open some other
  file named similarly — the string-equality check against the *resolved* literal value (not
  against any line mentioning the filename at all) is what keeps this precise, unlike a grep.
- **Single-hop resolution ceiling**: if a future writer introduces a two-hop indirection (a
  parameter default bound to a name that is itself bound to the literal, one level further than
  Step 1's own module-constant hop), the guard would miss it the same way the original grep design
  missed Step 1's one-hop case. This is a known, stated limitation, not silently assumed away —
  acceptable because the guard's job is catching an accidental *second, differently-styled*
  writer appearing, not defending against a writer deliberately designed to evade it.
- **Lock-file protocol, addressed directly since it was asked for**: `tools/agent-monitoring/
  writer.py`'s lock-file protocol (for `agent-monitoring/data/*/*.jsonl` shards) solves a
  same-disk concurrent-process race — multiple processes appending to the identical file on one
  machine at close to the same instant. `tickets/working_log.csv` doesn't have that hazard: each
  row is appended once, inside one ticket's own isolated git worktree, and reconciliation across
  worktrees happens through `git merge` (the `merge=union` + `text eol=lf` mechanism `INFRA-416`
  and `TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION` already own), not through two
  processes racing on one inode. A lock file would solve a problem this file doesn't have and
  wouldn't touch the one it does.

## Deviations (Review round 1)

Round 1 returned `NEEDS_CHANGES` with 3 blocking findings, all independently re-confirmed against
real files before this revision (not accepted on the reviewer's say-so alone):

1. **Sole-writer guard couldn't find its own reference implementation.** The original Step 1 sketch
   put the literal path only in an inline `Path("...")` default expression; the write call itself
   (`open(path, "a", ...)`) carries no literal string a grep could anchor on. Confirmed by
   re-reading the plan's own prior text. Fixed: Step 1 now uses a named module-level constant
   (load-bearing for the guard, not cosmetic), and Step 4 is now AST-based with an explicit,
   single-hop name-resolution design, verified by hand against Step 1's own exact shape before
   Implement writes either file.
2. **Step 3's invocation mechanism reintroduced the exact hazard class this ticket exists to
   close.** Confirmed: this ticket's own title contains backticks and an em-dash, proving
   free-text-in-shell-source is a real, not hypothetical, case. Fixed: Finalize now writes a JSON
   file via the `Write` tool (never shell-interpreted) and the helper reads `--data-file`, rather
   than any value passing through shell/Python source-embedding at all.
3. **INFRA-416's `v2_evidence` would go stale.** Confirmed via direct read of
   `docs/parity_ledger/infrastructure.yaml`: it cites the exact call site Step 2 replaces. Fixed:
   new Step 5 updates it via `write_entry()`.

Non-blocking notes both addressed in the revision: the lock-file-protocol question now has an
explicit answer in Risks; the bare-function-with-positional-args design was left as-is (reviewer
called it acceptable, keyword-only args or a typed record was offered as an optional strengthening
not required for approval — the JSON-file contract in Step 3 already forces call sites to name
fields explicitly via dict keys, which captures most of that benefit without a signature change).

## Deviations (Review round 2)

Round 2 confirmed round 1's Findings 1-2 fully resolved (hand-walked the AST resolver against
Step 1's exact shape; confirmed the Write-tool/`--data-file` contract removes the shell/Python
quoting hazard). Returned `NEEDS_CHANGES` on one unresolved finding plus one new issue, both
independently re-confirmed before this revision:

1. **Step 5's `write_entry()` call risked silently dropping INFRA-416's other fields.** Confirmed
   by direct read of `tools/parity_ledger_writer.py:128-148`: `write_entry()` does a full-entry
   replace-by-id, and `.claude/agents/parity-updater.md`'s own documented procedure is read-the-
   current-entry-then-construct-the-full-dict, which Step 5's original one-sentence "update
   v2_evidence... and add to test_path" phrasing didn't actually instruct. Fixed: Step 5 now
   spells out the 3-step read/construct-full-dict/write sequence explicitly, plus a test asserting
   every other field is byte-identical after the write.
2. **The Step 3 negative-assertion pin was itself found to have a scoping bug, caught before this
   revision reached round 3**: my own first fix ("`python3 -c` must not appear anywhere in the
   Finalize phase block") would have been false immediately, since `phase('Finalize')`'s block
   contains 4 unrelated, legitimate orchestrator-run `python3 -c` self-checks (`finalizeCheckOutput`
   etc.) after the agent's own prompt closes — confirmed by direct read and a live Python check
   against the real file. Fixed: the assertion is now scoped to the Finalize agent's own prompt
   string specifically, bounded by two anchors verified (via a live check against the real file) to
   exist and to correctly isolate that substring from the post-Finalize self-checks.

## Deviations (Implement)

Wording-only, no mechanism change. This plan's own Step 3 prose explains the rejected
inline-embedding approach using the literal phrase "python3 -c". Implement initially carried that
same literal phrase into the actual instruction text written into the Finalize agent's prompt
string in `implement-ticket.js` — which would have made the new pin test's own negative assertion
(`"python3 -c" not in prompt`) false the moment it was written, since the prompt itself would then
contain the forbidden substring. Caught by running the live anchor/substring check against the
real file before finalizing the test (`'python3 -c' in scoped_prompt` was `True` with the first
wording, `False` after). Fixed by rewording the in-prompt caution to "never embed this text as a
Python or shell source string (e.g. an inline `-c` script)" — identical guidance to the plan's own
intent, without reproducing the exact trigger phrase inside the text the test itself scans. No
change to the JSON-file / `--data-file` contract, the AST resolver design, or the parity-ledger
read-modify-write sequence — all implemented exactly as specified above.
