---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, agent-monitoring, observability, testing]
---

# Gate A Read-Path Payoff Review Decision — TCK-20260731-PARITY-READPATH-GATE

Resolves Gate A of `docs/plans/agent_infrastructure/parity_ledger_sqlite_context/
idea_parity_ledger_sqlite_context_integration.md`'s "Read-path payoff review" section, ahead
of any later ticket adopting `tools/parity_index.py`'s `entry`/`impact`/`health` read path into
a real workflow or agent context. This document **decides and evidences only** — it implements
nothing, wires nothing into any workflow, and changes no file under `tools/parity_index.py`,
`tools/parity_ledger_scan.py`, `tools/gate_checks/parity_updater_static.py`, or any
`docs/parity_ledger/*.yaml` shard. Every number below is either a real, freshly-computed field
from `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_results.json` (produced by
`tests/tools/test_gate_a_readpath_review.py`, re-run against real, git-pinned ledger data) or an
explicitly labeled estimate/proxy — never an unattributed round number.

**Verdict: GO** (scoped narrowly — see §5 and §6 before treating this as broader than it is).

---

## 1. What the idea doc's Gate A bullet proposed

> Use the read-only impact query on a predeclared set of real tickets or ticket-like fixtures
> and review false negatives, false positives, selection size, and analyst effort against the
> existing scan. Proceed to any write/context work only if the index demonstrates a material
> precision, coverage, or context-size advantage without a regression in obligation recall.
> Otherwise retain the present ledger and close or backlog the later phases.

This document reviews exactly that: `tools/parity_index.py`'s unmodified `entry()`/`impact()`/
`health()` against `tools/parity_ledger_scan.py::find_p0_intersection` and
`tools/gate_checks/parity_updater_static.py::derive_mapping`/`cross_reference_touched`, on a
9-case corpus (6 real, git-pinned, ticket-derived cases; 3 freshly-authored synthetic
legacy-edge-case fixtures), per `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/plan.md`.

---

## 2. Corpus

Full case data lives in `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_corpus.json`
(frozen before any result was computed) and
`staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_results.json` (filled in by the test
run). This table cites them by path rather than re-embedding the JSON.

### 2.1 Real, ticket-derived cases (`ground_truth_or_judgement: "ground_truth"`)

| Case | Pin | Priority / Status | Query path | Expected obligations | Recall | Adjudication summary |
|---|---|---|---|---|---|---|
| `FAC-012` | `68f168ff` | P1 / verified | `src/worldbuilding/compiler.py` | `FAC-012` | **1.0** | Faction-exclusion — `faction.yaml` is not in `CANONICAL_LEDGER_FILES`; both legacy surfaces are structurally blind regardless of priority. |
| `INFRA-296` | `ab06fc10` | P2 / verified | `tools/context_packet_assembler.py` | `INFRA-296`, `INFRA-299` | **1.0** | P0-only filter + `derive_mapping`'s src/\*.py-only scope — legacy can never answer a `tools/` query at all. |
| `INFRA-297` | `ab06fc10` | P2 / verified | `tools/retrieval_events.py` | `INFRA-297`, `INFRA-299` | **1.0** | Same as `INFRA-296`. |
| `INFRA-299` | `ab06fc10` | P1 / verified | `.claude/workflows/implement-ticket.js` | 7 entries (`INFRA-263/265/274/281/282/288/299`) | **0.0** | **Shared blind spot, not an index regression** — see §6.2. |
| `INFRA-300` | `ab06fc10` | P2 / verified | `tools/agent-monitoring/generate_retro.py` | 7 entries (`INFRA-275/283/284/291/297/298/300`) | **1.0** | P0-only filter + src/\*.py-only scope, same as `INFRA-296`/`297`, at full 7-entry selection size. |
| `WORLD-076` | `46c5ae59` | **P0** / **divergent** | `src/observability/hard_law_monitor.py` | `WORLD-076`, `WORLD-112` | **1.0** | P0-only filter — legacy finds `WORLD-076` (P0) but misses `WORLD-112` (P1); index finds both. **Status caveat: see §6.1.** |

### 2.2 Synthetic legacy-edge-case fixtures (`ground_truth_or_judgement: "evaluator_judgement"`)

Freshly authored, distinct IDs/paths/shards from `tests/tools/test_parity_index.py::
TestEquivalenceFixtures`'s `COMB-501/502`, `CM-601/SC-601`, `TR-701`, `FAC-801` — confirmed by
`tests/tools/test_gate_a_readpath_review.py::TestAdjudication::
test_gate_a_no_phase2_synthetic_fixture_relabeled_as_ticket_derived_corpus`.

| Case | Shape | Outcome |
|---|---|---|
| `SYN-P0PAIR-001` | P0/P1 pair, same path | Matches `TestEquivalenceFixtures`'s known shape exactly: `find_p0_intersection` P0-only, `impact()` all-priority. |
| `SYN-MULTISHARD-001` | Two-shard, same path | `derive_mapping`'s ANY-of-shard set matches `impact()`'s two individual entries, at two different granularities. |
| `SYN-MALFORMED-001` | Malformed canonical shard alongside a valid one | **New finding beyond Phase 2's scope** (see §6.3): three distinct real behaviors for one input shape, not two. |

---

## 3. Aggregate Metrics (real cases only — synthetic cases inform adjudication shape, not the headline numbers)

All four figures required by AC #3, read directly from `gate_a_results.json`'s
`aggregate_metrics`:

- **Recall**: `14/21 = 0.667` aggregate across the 6 real cases (`aggregate_recall` field).
  Per-case recall is 1.0 for 5 of 6 cases and 0.0 for `INFRA-299` — the aggregate is
  **reported alongside**, never **instead of**, the per-case table in §2.1, so `INFRA-299`'s
  real 0% result is never averaged away (AC #3's explicit requirement).
- **False positives**: `aggregate_unexplained_false_positive_count = 0`. Every ID `impact()`
  returned beyond a case's `expected_obligation_ids` (e.g. `INFRA-299` appearing in both the
  `INFRA-296` and `INFRA-297` cases' results) is a *genuine* citation independently confirmed in
  that entry's own evidence text, not a spurious match — none required exclusion as an
  "intentional broadening"; there simply were none to exclude.
- **Selection size / context-byte estimate**: `context_byte_estimate_index.value` per case,
  explicitly `"is_estimate": true` in every record — e.g. 249 bytes (`FAC-012`, 1 result) up to
  1660 bytes (`INFRA-300`, 7 results). **This is a structural byte count of `impact()`'s own
  returned payload, never a claimed production token/context saving** (Out of Scope).
- **Analyst-effort proxy**: `shards_scanned_legacy = 8` / `shards_scanned_index = 0` for every
  case (Decision 3's fixed structural constant); `candidates_to_review_legacy_total = 1` vs.
  `candidates_to_review_index_total = 14` across the 6 real cases — legacy's low
  candidate-count reflects how little it actually finds (see recall above), not efficiency.
  **Explicitly a structural proxy for analyst burden, not a measured time-on-task figure.**

`health()` was exercised once each for the `faction` and `infrastructure` subsystems
(`gate_a_results.json`'s `health_snapshots`) as supporting corpus evidence only — it has no
legacy counterpart and is never folded into the recall/false-positive arithmetic above
(confirmed by `TestIndexCapture::test_gate_a_health_snapshots_recorded_but_never_folded_into_metrics`).

---

## 4. Legacy vs. index, side by side

| | `find_p0_intersection` recall (6 real cases) | `impact()` recall (6 real cases) |
|---|---|---|
| Hits / expected | 1 / 21 | 14 / 21 |
| Recall | **4.8%** | **66.7%** |

Legacy's one hit is `WORLD-076` itself (the only P0 entry in the corpus) — it misses its own
P1 sibling `WORLD-112` on the identical query, misses all of `FAC-012` (faction-exclusion),
and misses every `tools/`-path citation entirely (`INFRA-296/297/300`, `derive_mapping`'s
src/\*.py-only scope). **On every one of the 6 real cases, `impact()` performs strictly at
least as well as both legacy surfaces — never worse.** `INFRA-299` is the one tie (0% on both);
it is not a case where legacy wins.

---

## 5. Resolution

**Gate A is resolved: GO**, narrowly scoped as follows. The evidence demonstrates, without any
recall regression on any of the 6 real cases:

- **Faction/all-shard coverage** (idea doc's first named advantage) — structurally and
  empirically demonstrated by `FAC-012`.
- **Materially higher recall with zero unexplained false positives** — 66.7% vs. 4.8%
  aggregate, entry-level rather than legacy `derive_mapping`'s shard-level granularity, with
  every extra ID `impact()` returned independently confirmed as a genuine citation.
- **No recall regression** — confirmed case-by-case in §4, not just in aggregate.

**Next action (scoping only, not implementation):** scope a future Phase-3 ticket to define how
`impact()`/`entry()`/`health()` would be wired behind a workflow gate or shadow context packet,
and require that scoping ticket to resolve, before writing any code, the two structural gaps
this review surfaced (§6.2, §6.3) — specifically whether `_PATH_REF_RE`'s recognized prefix set
needs extending (or the intended query surface needs to stay explicitly scoped to
`src/`/`tools/`/`tests/`/`docs/` paths only) and whether a production rollout needs the full
9-shard index rather than this review's single-shard-per-case reconstruction. This document
does **not** authorize enabling any flag, adding any workflow call site, or extending
`_PATH_REF_RE` itself — those are implementation, explicitly out of scope for a GO verdict here.

---

## 6. Limitations

### 6.1 `WORLD-076`'s `divergent` status — retrieval correctness is not parity correctness

`WORLD-076` is the corpus's one real P0 case, and its ledger `status` is **`divergent`, not
`verified`** — recorded verbatim in `gate_a_corpus.json`, never normalized. This case proves
that the read path correctly **retrieves** a real, git-pinned P0 obligation when queried by its
cited changed path. **It does not certify that `WORLD-076`'s own underlying `src/` behavior is
currently parity-clean** — the real ledger entry's own `divergence_note` states the
spawn-placement RNG collision bug this entry tracks remains unfixed. Do not read this document's
recall claim as also certifying `WORLD-076`'s own parity correctness; those are two independent
claims, and only the first (retrieval) is what Gate A measures.

### 6.2 The `.claude/` prefix gap (`INFRA-299`) — a real, shared blind spot

`tools/parity_index.py`'s `_PATH_REF_RE` (line 66) only recognizes paths prefixed `src/`,
`tools/`, `tests/`, or `docs/`. `.claude/workflows/implement-ticket.js` matches none of those,
so the index's structured `code_refs` extraction produces **zero** rows for it under any entry —
even though 7 real ledger entries' evidence text genuinely cites this exact path (confirmed by
direct read, not fabricated). This is not a legacy-vs-index disagreement: `find_p0_intersection`
excludes all 7 via its P0-only filter (none are P0), and `derive_mapping`'s `src/*.py`-only key
space excludes a `.claude/` path outright — **all three surfaces score 0% recall on this one
query.** Adopting the index would not regress this case relative to legacy (both already could
not serve it), but it also would not improve it. Any future ticket wiring `impact()` into a real
workflow must either extend `_PATH_REF_RE`'s recognized prefixes or explicitly scope the
intended query surface to exclude non-`src/tools/tests/docs` paths — this document does not
decide which.

### 6.3 Malformed-shard handling — a third, previously undocumented behavior

`SYN-MALFORMED-001` discovered that `find_p0_intersection` (`tools/parity_ledger_scan.py:49`)
has no `try`/`except` around `yaml.safe_load` and **raises an uncaught `yaml.YAMLError`** when
it reaches a malformed canonical shard — a real fragility beyond `TestEquivalenceFixtures`'s
original scope (that suite only ever exercised `derive_mapping` against a malformed shard, never
`find_p0_intersection`). Three distinct real behaviors now exist for the same input shape:
`find_p0_intersection` crashes hard; `derive_mapping` silently skips and continues; the index
importer aborts the whole build with a labeled `ShardParseError`. None was "fixed" as part of
this review.

### 6.4 Single-shard-per-case reconstruction

Per `plan.md`'s Decision 2, each case's temporary index was built from **only its own pinned
shard's full content**, not the complete 9-shard production ledger. This keeps every case
reproducibly pinned (other shards keep changing under ongoing, unrelated tickets), but means
this review's selection sizes and recall figures are a **lower bound** — a full production index
build could, in principle, surface additional cross-shard citations this review's per-case
reconstruction cannot see. This is a disclosed scope choice, not an oversight.

### 6.5 `derive_mapping`'s granularity mismatch

`derive_mapping`/`cross_reference_touched` report **shard-level** candidates
(`{path: {shard_filenames}}`), never entry IDs. Every recall/false-positive number in §3-4 is
computed against `find_p0_intersection` (entry-level) and `impact()` (entry-level) — `derive_mapping`'s
shard-level signal is recorded per case in `gate_a_results.json`'s `legacy_derive_mapping_result`
and cited qualitatively in each case's adjudication, but is not folded into the entry-level
recall arithmetic, since the two are not directly comparable counts.

---

## 7. How to reproduce

```
pytest tests/tools/test_gate_a_readpath_review.py -v
```

This single command is the harness (`tests/tools/test_gate_a_readpath_review.py`) — it
re-verifies every real case's pinned git blob content and `canonical_fragment_hash`, rebuilds a
temporary index per case via the real, unmodified `tools/parity_index.build()`, re-runs both
legacy functions and `entry`/`impact`/`health`, re-persists `gate_a_results.json`, and asserts
the protected-file byte-identity guard (`tools/parity_index.py`, `tools/parity_ledger_scan.py`,
`tools/gate_checks/parity_updater_static.py`, every `docs/parity_ledger/*.yaml` shard,
`tools/context_packet_assembler.py`, `.claude/workflows/implement-ticket.js`) held throughout.
