---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT
artifact_type: plan
tags: [testing, registry]
---

# Plan — TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT

Implements the revised shape agreed with the repository owner on 2026-09-11: fix the measurement
instrument and the format first, then fix the entries. See `investigation.md` for all evidence.

## Why this order

Fixing the 28 entries first would leave the index still blind to 345 entries (so the next stale citation
goes undetected the same way) and would repair entries using the prose-in-`test_path` pattern that
caused the problem. Each step below is a precondition for the one after it.

## Step 1 — One shared `test_path` parser

Extract `parse_test_path_citations()` and its three regexes from
`tools/gate_checks/mechanics_auditor_static.py` into a new module, `tools/parity_test_path.py`.
`mechanics_auditor_static.py` re-imports it; behavior there is byte-identical.

Replace `parity_index.py`'s `_TEST_PATH_DECLARED_RE` gate (line ~291) with the shared parser, inserting
one `test_refs` row per parsed citation. `_declared_test_path_exists()` keeps its existing
`split("::", 1)[0]` file-level check.

**Stays path-level.** Per `v1_decisions_phase0.md` §"Path-only links", the index does not check symbols.
Symbol-level verification remains `verify_entry_test_path()`'s job. This step widens what the index can
*see*, not what it *checks*.

**Expected effect:** the index gains visibility of roughly 218 previously-blind entries, so its
`absent_file` count **rises** as hidden stale citations surface. That is the intended outcome, not a
regression. Record the post-Step-1 count as the baseline every later measurement compares against.

## Step 2 — `evidence_kind` field (optional, schema only)

Add to `docs/parity_ledger/schema.json`, nullable, not in `required`:

| Value | Means |
|---|---|
| `existence` | A constant, signature, or field exists (what `STRAT-239` cited) |
| `invocation` | A test invokes the behavior and asserts its outcome |
| `runtime_observation` | The behavior was observed in a real run, replay, or simulation |

Mirror it in `parity_ledger_writer.validate_entry()` as an enum check when present.

**Not in this ticket:** any rule forbidding `existence` for `verified` P0/P1 entries. Enforcement and
back-fill across all shards are the follow-on (see Out of Scope below).

## Step 3 — Write-time format contract

In `validate_entry()`: when `test_path` is non-null it must parse via the shared parser, or the write is
rejected. Applies only to entries passed to `write_entry()` — respects the "never sweep" decision.
Entries already on disk are not revalidated.

Verified safe for `TestValidateEntryAgainstRealMultiSegmentCorpus`: all 10 of its entries parse.

Prose that currently lives in `test_path` belongs in `support_boundary` (the existing field for "what
this verification does and does not cover"). The contract error message should say so.

## Step 4 — Resolve the 28 stale entries

All writes via `tools/parity_ledger_writer.write_entry()`. Never a raw YAML edit. P0 entries first.

For **every** entry, before choosing an outcome: search the current tree for a test covering the
entry's `text` under any name. A filename match is not sufficient, and a missing filename is not proof
coverage was lost.

- **Class A (7):** confirm the successor tests the entry's claim, run it, repoint `test_path` to the
  clean citation, set `evidence_kind: invocation`. `STRAT-014` is already confirmed at symbol level.
- **Class B (7):** if coverage is found under another name, treat as Class A. Otherwise set
  `status: missing`, `test_path: null`, and record in `support_boundary` which test was deleted, from
  which commit, and that the behavior is unverified rather than known-broken.
- **Class C (14):** same procedure as Class B, but `support_boundary` must state the cited file never
  existed in this repository. Check `WORLD-061`/`WORLD-062` against `tests/unit/world/` first.

**Status vocabulary caveat.** The schema's `missing` does not distinguish "behavior absent" from
"behavior present but unverified." For Class B/C the second is almost certainly true. Use `missing` —
the ticket itself names it — and make the distinction explicit in `support_boundary`. This ambiguity is
another instance of the missing evidence standard and belongs to the follow-on.

### `TOWN-005` / `TOWN-006`

Not stale — their live citation exists — but they carry a falsified claim (the file they say never
existed is in git history) and they are the precedent this ticket was told to follow. Rewrite both to
the new format: clean citation in `test_path`, accurate history moved to `support_boundary`. Two
entries, bounded.

## Step 5 — Measure

1. Record the `absent_file` count after Step 1 (baseline).
2. After Step 4, confirm it decreased by exactly the number of stale citations resolved.
3. Run `python3 tools/parity_index.py build` and record the health summary.

The ticket's original criterion ("counts decrease by the number fixed") is only meaningful against the
post-Step-1 baseline; against the pre-change count it would be contaminated by the newly-visible entries.

## Out of scope — follow-on tickets to file at close

1. **Evidence-standard enforcement:** forbid `evidence_kind: existence` for `verified` P0/P1; back-fill
   the field across all shards; write-time enforcement of the rule.
2. **Normalize the 127 unparseable `test_path` values.** Step 3 prevents new ones; existing ones are only
   fixed when an entry is next written.
3. **Oracle parity is not exercised.** `test_parity_guards.py` checks the oracle files exist and are
   well-formed; nothing compares behavior to them (investigation.md §7).
4. **`missing` vocabulary** conflates absent behavior with unverified behavior.

## Risks

- **Writer test fixtures** may use prose `test_path` values; Step 3 would reject them. Update fixtures
  rather than weakening the contract.
- **Step 1 changes `absent_file` counts** that other tools or dashboards may read. Check consumers of the
  health summary before landing.
- **Class B/C outcomes change P0 entries from `verified` to `missing`.** That is the honest result, but
  it is a visible downgrade of 21 entries; the completion summary should say so plainly.
