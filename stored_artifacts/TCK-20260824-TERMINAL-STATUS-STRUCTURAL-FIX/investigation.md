# Investigation — TCK-20260824-TERMINAL-STATUS-STRUCTURAL-FIX

## Root cause

`tools/agent_orchestration_claude_adapter/terminal_status_extractor.py::extract_all_terminal_statuses()`
aggregates `FINALIZE_INCOMPLETE`'s two `writeMonitoring('FINALIZE_INCOMPLETE')` call sites into a
`call_sites: [int, int]` list, populated purely from `text.count("\n", 0, match.start()) + 1` —
raw line numbers computed from wherever the regex happens to match in the current file text. Two
tests assert this list equals a literal `[N, M]`:

- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py:101`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py:69`

Both currently hardcode `== [1546, 1558]` (re-verified live via `grep -n "FINALIZE_INCOMPLETE"
.claude/workflows/implement-ticket.js` — confirmed still accurate as of this investigation, not
drifted again since the ticket was scoped). Any diff that adds/removes even one line above line
1546 in `implement-ticket.js` shifts both numbers, failing both tests. This has happened 8 times
since 2026-08-02 (confirmed via `tickets/done/` history): `TCK-20260802-TERMSTATUS-DRIFT-FIX`,
`TCK-20260802-DOC-COVERAGE-CHECK`, `TCK-20260817-HOTFIX-TERMINAL-STATUS-STALE-LINE-NUMBERS`,
`TCK-20260818-HOTFIX-TERMINAL-STATUS-CONTRACT-DRIFT`, `TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT`,
`TCK-20260824-HOTFIX-TERMINAL-STATUS-EXTRACTOR-DRIFT`, `TCK-20260824-PARITY-NEXT-ID-LOOKUP`,
`TCK-20260824-HOTFIX-FINALIZE-INCOMPLETE-LINE-DRIFT`.

## Why a pure count/ascending check is not quite enough on its own

Replacing `== [1546, 1558]` with just "exactly 2 ascending ints" is structurally sound but weaker
than the original in one respect: it can't distinguish "two genuinely different call sites" from
"the same call site's line accidentally counted twice" or "one real site plus one accidental
duplicate of it" — both would still produce 2 ascending ints. The real invariant under test is
that `FINALIZE_INCOMPLETE` fires from two distinct code paths (self-check-output-unparseable at
:1546, self-check-found-a-real-discrepancy at :1558 — read directly from
`.claude/workflows/implement-ticket.js:1544-1565`). Each call site sits immediately before a
`return { ... message: '<fixed string literal>', ... }` block whose `message:` value is a plain
single-quoted string literal (site 1's has a `+ finalizeCheckOutput` suffix, but the literal prefix
itself — `'Finalize self-check output could not be parsed — treating as incomplete. Raw output: '`
— is captured cleanly by a `message:\s*'([^']*)'` regex, which stops at the first closing quote and
ignores the concatenation). Site 2's message is a plain, fully-literal string with no concatenation.
These two message-literal prefixes are stable, human-authored, semantically meaningful, and always
distinct from each other by construction (they describe different failure conditions) — a strictly
stronger and still line-position-independent structural marker.

## Existing precedent for this design

`agent-orchestration/terminal-statuses.yaml`'s own header comment already documents line citations
as "best-effort provenance only" while treating only `value`/`kind`/`phases` as the authoritative
data — this fix mirrors that same split: `call_sites` (line numbers) stays present as informational
provenance, but no test treats it as an exact-match fixture value anymore; a new `contexts` field
(the message-literal marker) becomes the thing actually asserted for distinctness.

No JS AST/parser tooling exists anywhere in this repo. `tools/gate_checks/workflow_meta_conformance.py::extract_meta_phases`
is the direct precedent this extractor's own docstring already cites for "regex-over-raw-text, no
parser" — confirmed by reading that file: it also does plain `Path.read_text()` + regex, no
subprocess, no JS engine. A full parser rewrite here would be inconsistent with that established
pattern and far larger than the actual problem warrants.

## Blast radius check

`grep -rn "call_sites"` across the repo confirms `call_sites` is referenced only in
`terminal_status_extractor.py` itself (source + docstrings) and the two test files being fixed —
no other test, doc-generation script, or schema validator depends on its exact shape.
`test_terminal_status_schema.py` validates `agent-orchestration/terminal-statuses.yaml`'s committed
YAML structure via `terminal_status_loader.py` — a completely separate data path from the live
extractor's Python return dicts — so adding a new `contexts` field to the extractor's aggregated
dict cannot affect schema validation. A repo-wide grep for other tests hardcoding a line-number
equality against `implement-ticket.js` (`grep -rln "implement-ticket.js" tests/ | xargs grep -lE
"== *\[[0-9]+"`) found only these same two files — confirming no other latent instance of this
drift class exists today.

## Files to change

- `tools/agent_orchestration_claude_adapter/terminal_status_extractor.py` — add a `context` field
  per literal call-site entry (nearby `message:` string-literal prefix, bounded lookahead window,
  `None` if not found) and a parallel `contexts` list in the aggregated `call_sites` bucket.
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py:101` — replace the
  literal equality with structural invariants (count, distinctness, ascending order) plus a new
  distinctness check on `contexts`.
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py:69` — same
  replacement.
- New test in `test_terminal_status_extractor.py`: a synthetic fixture (written to `tmp_path`)
  proving an unrelated line inserted above both call sites doesn't change the pass/fail outcome.
