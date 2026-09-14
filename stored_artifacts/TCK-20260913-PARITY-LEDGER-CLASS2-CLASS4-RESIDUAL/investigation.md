---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL
artifact_type: investigation
tags: [testing, registry, data-quality]
---

# Investigation — TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL

## 1. Re-measurement before starting (per the ticket's own instruction)

Ran `python3 tools/parity_corpus_check.py` fresh before touching anything, and diffed the exact
ID list byte-for-byte against the ticket's own enumeration: 68 Class 2 + 1 Class 4, **zero drift**.
Re-confirmed again after merging two rounds of intervening `main` movement (PR #191, PR #182) —
still zero drift on the target IDs (only unrelated entries elsewhere in the corpus changed).

## 2. Defect shapes found, beyond the ticket's own three named categories

The ticket named "prose run-summary", "pipe-delimited", "bad citation", and "non-pytest evidence"
as the observed shapes. Investigation surfaced several more, all handled the same way (extract
real, verified citations; move disclosure prose to `support_boundary`; never invent):

- **Bare-comma shorthand**: `file.py::method1,method2,method3` — only the first fragment carries
  the file prefix; the rest are bare method names the parser can't independently resolve. Expanded
  each to its full file-qualified form (verified real via `grep` before writing).
- **Trailing parenthetical annotations**: a clean citation followed directly by `(41 passed, ...)`
  or similar, with no delimiter before the parenthesis — breaks the whole-string match. Stripped
  the annotation into `support_boundary`.
- **Trailing period after the last citation**: `...test_foo.py.` — the stray `.` makes the final
  segment not match `_NODE_ID_RE`. Stripped.
- **Line-wrap spaces inside a path**: `tests/unit/engine/ test_guild_visit_phase.py` (a spurious
  space from how the YAML value wraps) — closed the gap.
- **Raw shell pytest invocations**: `pytest file1.py file2.py -x -v -m "not slow or slow"` —
  extracted the real file citations, dropped the invocation syntax.
- **`-k`-filtered pytest invocations** (COMB-308, INFRA-272, INFRA-273): a directory/file cited
  with a marker (`-m slow`) and/or `-k` keyword filter attached. **Deliberately excluded from
  test_path**, not cited as a bare file/directory — running the bare path would execute a
  different, larger test set than what the entry's own claim describes as passing. Disclosed in
  `support_boundary` instead of misrepresented.
- **Non-pytest, non-Python evidence** (INFRA-TYPE-001, already known from the ticket text; also
  found: INFRA-280/302/303/304/392's frontend Vitest `.ts`/`.tsx`/Playwright `.spec.ts` tests) —
  see §4 below for how this class was handled.
- **Stale/renamed citations**: INFRA-406 (already known) and INFRA-291's
  `test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope`, confirmed via
  grep to have been renamed to `test_update_index_signature_change_is_deliberate_and_documented`
  by a later ticket (the new test's own docstring states it explicitly replaces the old name).
  Cited the current real name, disclosed the rename.

## 3. Delimiter safety check (INFRA-221/STRAT-236 vs. INFRA-405)

Confirmed via a corpus-wide grep that exactly 3 entries anywhere contain `|` in `test_path`:
INFRA-221, INFRA-405, STRAT-236. INFRA-221/STRAT-236 use a genuine ` | `-delimited multi-citation
with clean citations either side. INFRA-405 contains a literal `|| true` (a shell operator quoted
inside prose describing a test's own assertions, not a delimiter). Verified directly in Python
that `\s+\|\s+` (a single pipe with **required** whitespace on both immediate sides) never matches
either `|` inside `||`, so extending `tools/parity_test_path.py`'s delimiter regex this way is safe
— it fixes the two genuine cases without ever mis-splitting the third. New regression tests pin
both the positive case and the doubled-pipe non-match.

INFRA-405 itself was not fixed by the delimiter change (confirmed by design, not overlooked — its
own commas were already breaking it before this fix, independent of the pipe question) — normalized
separately in §2's "trailing parenthetical" category.

## 4. Genuinely unresolvable: 4 entries (INFRA-280, 302, 303, 304)

All 4 cite only frontend Vitest (`.ts`/`.tsx`) tests — INFRA-280 also disclosed a Playwright
`.spec.ts` for a related entry (INFRA-392), which is a mixed case handled separately (2 real `.py`
citations kept, the Playwright one excluded). For these 4, **no real Python/pytest citation exists
at all** — fabricating one to satisfy the parser would violate this ticket's own hard
no-fabrication constraint.

**Extending the shared parser (`tools/parity_test_path.py`) to accept `.ts`/`.tsx` was considered
and rejected.** The other real consumer of the same parser,
`mechanics_auditor_static.py::check_test_path()`, unconditionally invokes `pytest <citation>` on
any citation the parser accepts. Accepting `.tsx` there would silently break real verification for
every such entry — pytest cannot execute a `.tsx`/`.ts` file. This is a genuine, broader
parser/verifier design question (confirmed not a one-off: 4 real instances across the corpus), out
of this ticket's own scope to resolve unilaterally.

**Why these 4 could not even get a `support_boundary`-only update**: `write_entry()`'s own
`validate_entry()` requires `test_path` to parse via the shared citation parser on **every** write,
regardless of what else changed. There is no legitimate way to persist a disclosure-only update to
one of these 4 entries without either (a) fabricating a fake `.py` citation to satisfy the
parser (forbidden), or (b) bypassing `write_entry()` with a raw YAML edit to an **existing
historical entry** (a real corruption-risk pattern this repo's own established practice reserves
for narrow, already-disclosed exceptions — not warranted here, since nothing about these 4 is
urgent). Left untouched in the ledger; documented here and in the ticket's own Completion Summary
instead, matching the ticket's own accepted "no real citation is identifiable, record that
honestly" category (Out of Scope section).

## 5. Class 4 (`SOC-ABAND-TYPE-01`)

Renamed to `SOC-ABAND-TYPE-001` (exactly 3 digits, per `_ID_PATTERN`). Confirmed via a full-repo
grep before renaming that nothing live (code, other ledger entries, cross-references) names the
old id — only historical `tickets/done/*.md` prose does, left untouched as historical record.
`write_entry()` upserts by id, so it added the new id alongside the old one; removed the resulting
stale duplicate via a disclosed, narrow list-filter-and-rewrite (not `write_entry()`, which has no
delete API) — justified since it undid the same session's own just-created duplicate, matching this
repo's established precedent for that exact situation. Rebuilt the derived parity index afterward
since that raw edit bypassed `write_entry()`'s own automatic rebuild.

## 6. Verification discipline

Every citation added to a `test_path` was independently confirmed to exist on disk (file) or as a
real function/class definition (`grep -n "^def <name>"` / `^class <name>`) **before** being written
— never inferred from field-name similarity alone, matching the parent ticket's own SUB-325/SUB-326
precedent. For entries whose original evidence text was too large to safely hand-copy without
transcription risk, the full original `test_path` string was preserved in `support_boundary` via
direct Python variable reference (not retyped), guaranteeing zero content loss regardless of length.
