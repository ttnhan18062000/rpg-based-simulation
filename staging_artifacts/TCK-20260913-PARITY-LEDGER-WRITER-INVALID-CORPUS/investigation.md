---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS
artifact_type: investigation
phase: inprogress
date: 2026-09-13
tags: [testing, registry, data-quality]
---

# Investigation: TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS

## Fresh re-measurement (the ticket's own numbers were already stale by the time work started)

Built `tools/parity_corpus_check.py` (a new, permanent, report-only tool — AC #1's own "script
committed so the next person re-runs rather than re-derives") and cross-checked its output against
directly running `validate_entry()` over every entry: **zero mismatches**, confirming the tool's
classification is exact, not an approximation.

Fresh count at investigation time: **1677 of 2187 entries invalid** (matches the ticket's own
total exactly, though the per-class split had already drifted by a few entries in either
direction since the ticket's own "measured 2026-09-13" — ledger content moves continuously):

| Class | Ticket's count | Fresh count at start |
|---|---|---|
| 1: no `test_path` | 1536 | 1537 |
| 2: malformed `test_path` | ~126 | 124 |
| 3: no `support_boundary` | 15 | 15 |
| **4 (new, not in the ticket's own text)** | — | **1** |

**Class 4 discovery**: the cross-check against real `validate_entry()` found one entry
(`SOC-ABAND-TYPE-01`, `social_narrative.yaml`) that fails for a reason none of the ticket's 3
classes cover — its `id` field has a 2-digit numeric suffix (`-01`) where `_ID_PATTERN` requires
exactly 3 digits. The entry is otherwise fully evidenced (real, parseable `test_path`, real
`v2_evidence`). Not fixed here: a different defect class than evidence-completeness, and renaming
a ledger entry ID has its own blast radius (cross-references elsewhere aren't grepped for by this
ticket). Reported so the tool's own total always matches the real validator exactly, never
silently undercounting a real rejection reason the ticket's own text happened not to name.

## Class 3 (15 entries) — fixed in full

Read every entry's full text/evidence before writing anything. 13 of 15 are `unsupported` P0
entries in `infrastructure.yaml` whose `v2_evidence` already states the real reason (a broker
client library — pika/confluent_kafka — was removed entirely by `TCK-20260817-DEAD-INFRA-REMOVAL-
EPIC`, so there is no code path left for the claim to apply to); writing `support_boundary` for
these was legitimate normalization of already-verified language, not new investigation.

The 2 `missing`-status `substrate.yaml` entries (`SUB-325`/`SUB-326`, spatial-index add/remove-
to-cell) needed real investigation, and a first draft of their `support_boundary` was **wrong and
caught before shipping**: it cited `src/platform/spatial_hash.py::SpatialHashV2` (found via a
quick grep) as evidence an implementation exists. A pre-existing, deeper investigation
(`docs/plans/rpg_design_roadmap/rpg_spatial_index_hardening_plan.md`, dated 2026-09-02) already
covered this *exact* question in far more depth (checked `src/engine/spatial.py`,
`src/engine/world_index.py`, `src/engine/domain/view.py`, and the real test file) and reached a
different, better-founded conclusion: the real spatial index used by the authoritative pipeline is
`world_index.py`'s rebuild-based `WorldIndexService` (no incremental add/remove API at all — dirty-
tracking decides rebuild-vs-reuse-cached, never incremental mutation); `SpatialHashV2` is a
different, unrelated class. The entries' own claim framing is mismatched against the real
architecture, and that plan already scopes its own reclassification follow-up. Corrected to cite
that plan instead of inventing a second, contradicting investigation.

## Class 1 (1537 entries) — policy decision

The ticket's own gating instruction: fix the baseline test *before* deciding Class 1 policy, since
exact equality made options (b)/(c) look artificially expensive. See "Baseline fix" below — done
first. Checked all 6 precedent baseline-bump hotfix tickets (`TCK-20260819` ×2, `TCK-20260830`,
`TCK-20260902`, `TCK-20260904`, `TCK-20260905` — the ticket's own text undercounted these as
"four") for a hidden reason exact equality was chosen: none record one beyond "matching the file's
established convention". No rationale was being protected by keeping the assertion exact.

With that resolved, evaluated the three options on their own merits, not through a broken test's
distortion:
- **(a) freeze**: no new code needed at all — `validate_entry()` already requires `test_path` for
  any new `verified`/`divergent` write, and the new ratchet baseline test (below) now catches any
  regression in the *count* through non-writer paths too. This option is really just "formally
  record that this is the decision", not an implementation task.
- **(b) distinct reportable state**: `tools/parity_corpus_check.py` (built for this ticket anyway)
  already reports Class 1 with a P0/P1 status breakdown in its `findings` list — the reporting
  half of (b) already exists as a side effect of this ticket's own required tooling.
- **(c) new `legacy_unverified` status**: would require a `schema.json` enum change, a
  `validate_entry()` change, and re-triaging up to 1537 entries' `status` field individually
  (distinguishing genuinely-unverifiable-forever entries from ones that could still get a real
  citation) — a multi-ticket undertaking on the scale of, or larger than, this entire ticket. Out
  of proportion to decide unilaterally inside this ticket's own scope.

**Decision: (a), no longer provisional.** Recorded formally in the ticket body. (c) remains a
real, credible idea for a future ticket if the ledger's own maintainers want a sharper vocabulary
than "verified" for pre-writer-era entries — not dismissed, just not this ticket's to build.

## Baseline fix

`tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_
path` converted from `assert live_missing == 1315` (exact equality, forcing a hotfix ticket on
every legitimate fix) to `assert live_missing <= _MISSING_TEST_PATH_CEILING` (a ratchet: may
decrease freely, must never increase). The comment immediately above the old assertion had said
for months that the count "naturally drifts downward ... it is not a frozen invariant" while the
assertion demanded exact equality anyway — that direct contradiction is what cost six hotfix
tickets. Verified the ratchet actually catches a regression (not just always-passing) with a
direct synthetic check before relying on it.

## Class 2 (124 entries) — 56 fixed, 68 remain

Categorized all 124 by shape before attempting any transformation. Built a normalizer, ran it in
**dry-run mode first**, then independently verified every single proposed transformation against
real files/functions on disk (grep for the exact function/class name) *before* writing anything —
this caught 5 real problems before they shipped:
- 2 were bugs in my own first-draft normalizer (a multi-file `::`-shorthand expansion that
  anchored to the *first* file in a citation list instead of the *most recently named* one when a
  list spans several files) — found, fixed, reverified.
- 1 was a bare-whitespace multi-target `pytest a.py::x b.py::y -x -v` shape my splitter didn't
  handle at all — added a dedicated extractor, verified it doesn't silently swallow non-flag text
  by requiring every leftover token to match a known flag/flag-argument shape.
- 1 (`SOC-CROSS-EP-005`) needed the same multi-target fix plus a quoted-flag-argument edge case
  (`-m "not slow"` splits into two whitespace tokens, breaking a too-strict flag-matcher).
- 1 (`INFRA-406`) is a **genuine pre-existing bad citation**, not a normalizer bug: it names a test
  function (`test_wave2_wave3_agents_do_not_gain_tools_field`) that was never real in the target
  file (only `test_wave2_...` and `test_wave3_...` exist separately). Left unfixed — guessing which
  of the two real names was "meant" would be inventing a citation, which this ticket's own Class 1
  prohibition extends in spirit to Class 2 as well.

51 entries fixed this way (parenthetical-annotation stripping, shell-command extraction,
multi-file shorthand expansion, multi-target pytest command parsing).

**Separately, a real parser capability gap, not a normalization**: 5 entries cited a bare directory
(e.g. `tests/unit/lab/`) — a completely valid pytest argument that
`mechanics_auditor_static.check_test_path()` *already* handles correctly (`Path.exists()` is true
for directories; `pytest <directory> -x -q` runs every file inside). The only real gap was
`tools/parity_test_path.py`'s own regex never having accepted the shape. Extended it (`_DIR_RE`,
requiring a trailing `/` so an accidentally-truncated file path is never silently reinterpreted as
a directory), verified end-to-end with the real venv python against a real directory before
committing, added 3 new dedicated tests. No ledger data changes were needed for these 5 — the
parser already strips whitespace before matching, so once the regex accepted the shape the
existing raw values parsed as-is.

56 fixed in total (51 + 5). **68 remain, genuinely requiring individual judgment**: the large
majority are prose run-summaries describing a broad, multi-directory pytest re-run
(`"Full scoped pytest re-run (tests/unit/tactical/, tests/unit/combat/, ...)"`) with no single
specific file the citation was ever really about — normalizing these would mean *picking* a
representative file that was never actually named, which is materially different from
reformatting a citation that already names one. Plus `INFRA-406` (bad citation, above) and
`INFRA-TYPE-001` (`make typecheck-py` — a build/lint gate check, not a pytest citation at all; the
schema has no way to express "this claim's evidence is a Makefile target", and extending the
parser to accept arbitrary shell commands is a much larger, more speculative change than the
narrow, well-justified directory-citation fix above).

## "Never sweep" constraint check

`TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s constraint forbids running pytest across the corpus.
`tools/parity_corpus_check.py` runs no tests at all — pure field-level validation via
`validate_entry()`/`parse_test_path_citations()`, both non-executing. Confirmed cheap in practice:
full 2187-entry scan completes in well under a second. Not a sweep in the sense that constraint
targets (which is specifically about running pytest against every cited test_path, an expensive
and non-deterministic operation this ticket never does).
