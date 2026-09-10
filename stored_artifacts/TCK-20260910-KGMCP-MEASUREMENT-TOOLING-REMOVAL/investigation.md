---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL
artifact_type: investigation
tags: [agent-monitoring, mcp]
---

# Investigation — TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL

## Current Behavior

Re-verified independently against this worktree's HEAD (`2efe6646`, branch
`kgmcp-measurement-tooling-removal`, which already includes `TCK-20260909-HOTFIX-KGMCP-ORPHANED-
PHASE-RUNNERS` and `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`) via full-file reads plus repo-wide
grep across `tools/`, `tests/`, `.claude/`, `Makefile`, `docs/` — not trusting the ticket's own
classification.

### The 3 modules

- `tools/agent-monitoring/kgmcp_baseline_corpus.py` (104 lines) — pure data module: `CORPUS`
  (7-entry frozen query list), `ROUTING_SHAPES`/`USE_CASES` frozensets,
  `kgmcp_char_heuristic_v1_token_count()`. No I/O, no live import of anything deleted.
- `tools/agent-monitoring/kgmcp_baseline_runner.py` (180 lines) — imports `kgmcp_baseline_corpus`
  (:49) and `search_mcp._run_search` (:54), both live. Writes
  `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` (:56-58). One-time,
  hand-run script per its own docstring (:5).
- `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py` (283 lines) —
  imports `registry_query.candidate_tags_from_text` (:69), live. Reads two frozen snapshot
  fixtures (:71-76) and writes `kgmcp_phase5_repeated_demand_measurement_results.json` (:77-83).
  One-time, hand-run script per its own docstring (:49-52).

**Consumer grep (`tools/`, `tests/`, `.claude/`, `Makefile`, `docs/`), all 3 module basenames:**
zero hits outside the modules' own file, `docs/engine/contracts/knowledge_gateway_mcp/*.md`
(all `status: historical`, see Docs section), `docs/plans/knowledge-gateway-mcp-proposal.md`
(`status: active`, narrative "Done" checklist — see Docs section), and
`docs/agent-monitoring/README.md` (`status: active` — see Docs section, this is the one live gap).
**No Makefile target, no `.claude/` reference, no `.py` import anywhere in `tools/` or `tests/`.**
Confirmed via `git cat-file -e HEAD:<path>` that none of the three modules' former test files
(`tests/tools/test_kgmcp_measurement_baseline.py`,
`tests/tools/test_kgmcp_baseline_corpus_dedup_coverage.py`,
`tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py`) exist in this worktree's `HEAD` —
they were already hard-deleted by `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` (commit `22d0949c`),
so the 3 modules currently have **zero test consumers of any kind**, confirming the ticket's claim.
(Other worktrees on older branches still show these files on disk — that is stale worktree state,
not evidence of a live consumer on this branch.)

### The 9 fixtures — independently re-derived consumer set

Grepped every fixture's exact filename across the whole repo (not extension-limited), excluding
self-matches inside `tests/tools/fixtures/` itself:

| Fixture | Real consumers found | Disposition |
|---|---|---|
| `kgmcp_phase1_baseline_comparison_results.json` | tickets/, `stored_artifacts/`, `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` (historical), `docs/plans/knowledge-gateway-mcp-proposal.md` — no `.py` reference anywhere | Orphaned — safe to delete |
| `kgmcp_phase2_baseline_recomparison_results.json` | same as above, plus `tools/write_path_guard.py:61` (comment only, see below) and `docs/parity_ledger/infrastructure.yaml` (narrative `text`/`v2_evidence` prose, `status: unsupported`, `test_path: null` already) | Orphaned — safe to delete |
| `kgmcp_phase3_pilot_acceptance_measurement_results.json` | tickets/, stored_artifacts/, historical doc only | Orphaned — safe to delete |
| `kgmcp_phase4_warm_direct_tool_comparison_results.json` | tickets/, stored_artifacts/, historical doc only | Orphaned — safe to delete |
| `kgmcp_measurement_baseline_corpus_results.json` | Written by `kgmcp_baseline_runner.py` (:57); described in `kgmcp_baseline_corpus.py`'s own docstring (:7); cited in `docs/agent-monitoring/README.md` (:68, live gap) and historical docs/parity-ledger prose. No test. | Falls with the runner — safe to delete |
| `kgmcp_phase5_events_investigate_snapshot.json` | Read only by `kgmcp_phase5_repeated_demand_measurement_runner.py` (:71-72, :150-151). No test. | Falls with the runner — safe to delete |
| `kgmcp_phase5_working_log_snapshot.json` | Read only by the same runner (:74-75, :154-156). No test. | Falls with the runner — safe to delete |
| `kgmcp_phase4_direct_tool_comparison_results.json` | **`tests/docs/test_phase4_direct_tool_comparison_doc.py`** — `json.loads()` direct read (:22-23), 3 tests assert doc content against fixture entries. Confirmed no import of any runner module. | **KEEP — live test consumer** |
| `kgmcp_phase5_repeated_demand_measurement_results.json` | **`tests/docs/test_phase5_repeated_demand_measurement_doc.py`** — `json.loads()` direct read (:26-31), asserts `INFRA-355` parity text matches fixture numbers. Confirmed no import of the phase5 runner module — only `json`, `yaml`, `pathlib`. | **KEEP — live test consumer** |

This independently confirms the ticket's own 4/3/2 split is correct: **7 fixtures safe to delete
(4 outright-orphaned + 3 fall-with-the-runners), 2 fixtures must stay** because
`tests/docs/test_phase4_direct_tool_comparison_doc.py` and
`tests/docs/test_phase5_repeated_demand_measurement_doc.py` read them directly by `json.loads()`
and never import any runner module — deleting the 3 runners cannot break either test.

### `tools/write_path_guard.py:61`

```
MAX_PAYLOAD_BYTES: int = 65536            # §5, redaction_retention_policy.md:121 — recalibrated
                                           # by TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION
                                           # from the real 7-entry corpus's observed cold response
                                           # range (~10,612-30,548 bytes,
                                           # tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json),
                                           # ~2.15x the observed max, rounded to the nearest clean
                                           # power of two (64 KiB).
```

Confirmed comment-only (lines 57-63, all `#`-prefixed continuation of a module-level constant
declaration) — no code reads the fixture path. `check_size_cap()` (§9 of the same module) uses only
the live `MAX_PAYLOAD_BYTES` integer, never the fixture.

**Scope determination:** deleting `kgmcp_phase2_baseline_recomparison_results.json` (this ticket's
own Scope, already agreed safe above) makes this comment cite a file that no longer exists anywhere
in the repo. `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`'s own Out of Scope explicitly excluded
"Any change to `tools/write_path_guard.py` or its live consumers" — at that time the fixture still
existed (it lives in `tests/tools/fixtures/`, never `tools/archive/` or `tests/archive/`, so it was
untouched by that ticket's delete list), so the comment wasn't stale yet. This ticket is the first
and only one whose own action makes it stale, so no other ticket will pick this up — **in scope
here**, as a same-session follow-through of this ticket's own fixture deletion, not scope creep.
Recommended fix (small, mechanical, `tools/` not `docs/`, so it does not appear as a Docs Requiring
Update bullet below): repoint the citation from the fixture path to
`docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` lines 56 and 62,
which carry the identical `~10,612`/`~30,548`-byte figures in a table and is `status: historical`
(retained, not deleted) — the numeric constant itself does not change, only the comment's
provenance citation.

## Mechanics / Engine Constraints

None. This is agent-orchestration/measurement tooling under `tools/agent-monitoring/`, not
simulation logic — no `src/` file is touched, no Mechanics Bible chapter or `docs/engine/`
contract governs this tooling's behavior (same category as INFRA-281 through INFRA-357's own
precedent, confirmed by re-reading several of those entries' `support_boundary` fields during this
investigation).

## Docs Requiring Update

- `docs/agent-monitoring/README.md`: `status: active`, developer-facing live catalog of
  `tools/agent-monitoring/*` modules. Its "## Knowledge Gateway MCP Phase 0 Measurement Baseline"
  section (lines 61-74) currently describes `kgmcp_baseline_corpus.py` and `kgmcp_baseline_runner.py`
  as present, current tooling with live file citations — once this ticket deletes both files, the
  section must be removed (or replaced with a one-line historical note) so the README stops
  cataloging tooling that no longer exists.
- `docs/parity_ledger/infrastructure.yaml`: entry `INFRA-334`'s `v2_evidence` field currently
  states (present tense) "the other source this entry's v2_evidence originally cited,
  `tools/agent-monitoring/kgmcp_baseline_corpus.py`, remains live and untouched by either ticket —
  only this entry's own dedicated regression test is gone." This becomes false once this ticket
  deletes `kgmcp_baseline_corpus.py`; `v2_evidence` must be updated (via
  `tools/parity_ledger_writer.py::write_entry()`, never a raw `Edit`, per the Authoritative
  Mechanics Rule) to state the corpus module is now also deleted. `status` stays `unsupported` and
  `test_path` stays `null` — no status change needed, only the evidence text.

The following docs were considered and explicitly excluded — narrative/historical framing, not
present-tense claims of current tooling availability, matching the precedent
`TCK-20260909-KGMCP-DOC-STATUS-SWEEP` already established for this same directory:

`docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`,
`docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md`, and
`docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md` (path:
`docs/engine/contracts/knowledge_gateway_mcp/`) are all `status: historical` (confirmed by reading
each file's frontmatter), consistent with `TCK-20260909-KGMCP-DOC-STATUS-SWEEP`'s deliberate sweep
that flipped exactly these phase/measurement docs to `historical` on the grounds that they "describe
a now-archived gateway with no live consumer." They cite the 3 modules and the 7 deleted fixtures as
part of a fixed historical record of what a completed, closed ticket did — deleting the underlying
files does not make the historical narrative false, only unreachable, which is the intended,
already-decided posture for this directory. Not touched here.

`docs/plans/knowledge-gateway-mcp-proposal.md` (path: `docs/plans/knowledge-gateway-mcp-proposal.md`)
is `status: active`, but its citations of `kgmcp_baseline_corpus.py`/`kgmcp_baseline_runner.py`
(lines 1114-1121) sit inside a "**Done**"-tagged historical checklist item recording that
`TCK-20260814-KGMCP-MEASUREMENT-BASELINE` was completed — the same narrative-record framing as the
historical docs above, just not yet frontmatter-flipped (that whole-directory frontmatter question
was already explicitly adjudicated by `TCK-20260909-KGMCP-DOC-STATUS-SWEEP`, which did not touch
this file, and re-litigating that adjudication is out of this narrower ticket's scope). This
ticket's own sibling test precedent (`tests/docs/test_phase5_repeated_demand_measurement_doc.py`'s
own docstring) explicitly states edits to this proposal doc are "Document-Update's job," not an
Implement-phase concern for a tooling-removal ticket. Not touched here.

`docs/REGISTRY.yaml` (path: `docs/REGISTRY.yaml`) is not a doc requiring a manual edit — it is
regenerated unconditionally by Finalize's post-migration self-check per this repo's own workflow
rule; no manual bullet needed.

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml` entries touching this ticket's code/fixtures, all already
`status: unsupported` / `test_path: null` from `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`'s prior
hard-delete (re-verified by direct read of each entry, not assumed):

- `INFRA-334` (P2, Phase 0 corpus/runner) — **needs `v2_evidence` text update**, see Docs section.
- `INFRA-339` (P1, Phase 1 runner) — narrative `text` cites `kgmcp_baseline_corpus.py`; `v2_evidence`
  already says only the dedicated test is gone, does not claim the corpus module's current state
  present-tense. No update needed.
- `INFRA-344` (P1, Phase 2 recomparison) — same pattern as INFRA-339, cites
  `kgmcp_phase2_baseline_recomparison_results.json` inside historical `text`/`v2_evidence` prose
  describing what the ticket did; already `test_path: null`. No update needed.
- `INFRA-350` (Phase 3 pilot acceptance) — same pattern. No update needed.
- `INFRA-354` (P2, Phase 4 direct-tool comparison) — cites the **retained**
  `kgmcp_phase4_direct_tool_comparison_results.json` fixture; unaffected by this ticket regardless.
- `INFRA-355` (P2, Phase 5 repeated-demand) — cites the **retained**
  `kgmcp_phase5_repeated_demand_measurement_results.json` fixture and the phase5 runner in
  historical `text`; `v2_evidence`/`test_path` already reflect the deleted test files. No update
  needed for this ticket's own scope (the runner's deletion does not change this entry's already-
  `unsupported`/`null` disposition).
- `INFRA-345` (P1, **verified**, live) — cites `kgmcp_phase2_baseline_recomparison_results.json`
  only inside historical narrative ("this hotfix deliberately left unmodified"); its actual
  `test_path` is `tests/docs/test_redaction_retention_policy_doc.py::test_payload_size_cap_doc_matches_live_module_constant`,
  confirmed (by reading that test) to check only the doc text against the live
  `write_path_guard.py::MAX_PAYLOAD_BYTES` constant — it never touches the fixture file. **Not
  affected by this ticket's fixture deletion.**

**No P0 entries** are involved anywhere in this set (all confirmed P1/P2 by direct read) — no
`test_path`-must-pass gating applies.

## Prior Work

- `TCK-20260907-KGMCP-DEPRECATION-EPIC` (done) — parent epic, decided Option C deprecation.
- `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` (done) — extracted `write_path_guard.py`,
  archived the gateway; its own investigation first flagged the docs `status:` sweep as a future
  follow-on (later executed by `TCK-20260909-KGMCP-DOC-STATUS-SWEEP`).
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` (done) — hard-deleted 26 archived files including
  all 5 gateway-dependent test files and all `tools/archive/kgmcp_phase*_gateway_runner.py`
  scripts; explicitly excluded `tools/write_path_guard.py` from its own scope (see comment-sweep
  discussion above); updated 21 `infrastructure.yaml` entries via `parity_ledger_writer.py`.
- `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS` (done) — archived the 5 gateway-*dependent*
  phase runners; explicitly left the 3 modules this ticket now targets alone because they don't
  import anything deleted (only gateway-*purposed*, not gateway-*dependent*).
- `TCK-20260909-KGMCP-DOC-STATUS-SWEEP` (done) — flipped 11 `docs/engine/contracts/
  knowledge_gateway_mcp/*.md` docs to `status: historical`, explicitly left
  `redaction_retention_policy.md` active (still backs the live secret-scan hook) and did not touch
  `docs/plans/knowledge-gateway-mcp-proposal.md` or `docs/agent-monitoring/README.md` — neither was
  in that ticket's Related Docs (`docs/engine/contracts/knowledge_gateway_mcp/` only), so the
  README gap identified above was not previously caught by any sibling ticket.

## Risks and Open Questions

- None blocking. The 7/2 fixture split, the 3 modules' zero-consumer status, and the
  `write_path_guard.py:61` comment-only classification are all independently re-derived and match
  the ticket's own pre-classification exactly.
- Open, non-blocking recommendation: the `write_path_guard.py:61` comment fix (repoint citation to
  `phase2_baseline_recomparison.md`) is small and mechanical but touches a `tools/` file outside
  this ticket's literal "Related Code Areas" list (`tools/agent-monitoring/kgmcp_*`,
  `tests/tools/fixtures/kgmcp_*.json`). Recommend Implement include it as a one-line same-session
  follow-through (avoids leaving a citation to a deleted file, no behavior change, zero test
  impact), but it is not a hard blocker if the implementer judges it out of the literal scope —
  either call is defensible; do not silently skip without recording the decision either way.
- `docs/agent-monitoring/README.md` was not in the ticket's own Related Docs list — flagging it here
  is exactly the kind of independent re-derivation this investigation is required to do rather than
  trusting the ticket's own docs list as complete.

## Anti-Drift Hazards

- Do not delete `kgmcp_phase4_direct_tool_comparison_results.json` or
  `kgmcp_phase5_repeated_demand_measurement_results.json` — both have live `tests/docs/` consumers
  confirmed above; deleting either breaks a passing test immediately.
- Do not touch `tests/tools/test_knowledge_gateway_archival.py` — confirmed by the ticket and by
  this investigation to be a live regression guard (gateway modules are hard-deleted, not
  archived), unrelated residue.
- Do not widen this ticket into a second full `retrieval_cache.py`/retro/dashboard access-log
  removal — that is explicitly `TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL`'s own scope
  per this ticket's own Out of Scope.
- Do not re-open `TCK-20260909-KGMCP-DOC-STATUS-SWEEP`'s already-settled frontmatter-status
  adjudication for the historical `docs/engine/contracts/knowledge_gateway_mcp/*.md` docs — leave
  their `status: historical` and stale-but-historical citations as-is; only `INFRA-334` and
  `docs/agent-monitoring/README.md` need a substantive edit here.
- If the `write_path_guard.py:61` comment fix is done, verify it is a comment-only, zero-behavior-
  change edit (`git diff` should show only `#`-prefixed lines changed) — do not touch
  `MAX_PAYLOAD_BYTES`'s value or `check_size_cap()`'s logic.
