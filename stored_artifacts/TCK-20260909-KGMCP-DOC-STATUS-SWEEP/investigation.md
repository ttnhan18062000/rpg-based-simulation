---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260909-KGMCP-DOC-STATUS-SWEEP
artifact_type: investigation
tags: [mcp, documentation]
---

# Investigation — TCK-20260909-KGMCP-DOC-STATUS-SWEEP

## Current Behavior

`docs/engine/contracts/knowledge_gateway_mcp/` contains 13 markdown files (verified fresh via
`ls` and `docs/REGISTRY.yaml` at Investigate time, 2026-09-09, on branch `bash-secret-scan-hook`):

| File | Live `status:` | Ticket's starting guess |
|---|---|---|
| `phase1_baseline_comparison.md` | active | clearly historical |
| `phase2_baseline_recomparison.md` | active | clearly historical |
| `phase3_pilot_acceptance_measurement.md` | active | clearly historical |
| `phase4_direct_tool_comparison.md` | active | clearly historical |
| `phase4_warm_direct_tool_comparison.md` | active | clearly historical |
| `phase4_workflow_recommendation.md` | active | clearly historical |
| `phase5_repeated_demand_measurement.md` | active | clearly historical |
| `measurement_baseline_contract.md` | active | clearly historical |
| `cache_migration_plan.md` | active | likely historical, confirm |
| `evidence_cache_identity_contract.md` | active | likely historical, confirm |
| `audit_phase0_5.md` | active | judgment call |
| `redaction_retention_policy.md` | active | do NOT blanket-mark |
| `keep_or_deprecate_decision.md` | **historical (already)** | (baseline) |

This exactly matches the ticket's own "12 active / 1 already historical" claim — re-verified
live, not assumed. `docs/REGISTRY.yaml` (regenerated recently, `make docs-registry`-current)
agrees with the on-disk frontmatter for all 13 files. The `.json` schema files in the same
directory (`evidence_identity_kinds.schema.json`, `knowledge_context_request.schema.json`,
`knowledge_context_response.schema.json`, `knowledge_status_response.schema.json`,
`provider_capabilities_context_search.json`, `provider_capabilities_graphify.json`,
`provider_capabilities_parity_ledger.json`, `provider_capabilities.schema.json`,
`shared_enums.schema.json`) carry no frontmatter and are correctly out of scope — confirmed not
indexed by `docs/REGISTRY.yaml` (only `.md` files are walked by `tools/generate_registry.py`'s
`collect_docs()`).

### The 8 "clearly historical" phase/measurement records

Read in full or in substantial excerpt: `phase1_baseline_comparison.md`,
`phase2_baseline_recomparison.md`, `phase3_pilot_acceptance_measurement.md`,
`phase4_direct_tool_comparison.md`, `phase4_warm_direct_tool_comparison.md`,
`phase4_workflow_recommendation.md`, `phase5_repeated_demand_measurement.md`,
`measurement_baseline_contract.md`. Every one is a point-in-time measurement/contract record
against a frozen 7-entry corpus and a gateway (`tools/knowledge_gateway_mcp.py`) that is now
archived at `tools/archive/knowledge_gateway_mcp.py`, deregistered from `.mcp.json`
(`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`). None describes currently-enforced behavior;
all describe what a now-dead gateway did when measured on a specific date. Confirmed clearly
historical — no content in any of these 8 files survived the archival into a live module the way
`redaction_retention_policy.md`'s §2-§7 did.

### The 2 "likely historical, confirm" docs

`cache_migration_plan.md` (246 lines) and `evidence_cache_identity_contract.md` (191 lines) read
in full. Both are Phase-0 design contracts for `knowledge-index/retrieval_cache.db`'s schema
evolution and the gateway's evidence/cache-identity model — every function/table/module they
name (`tools/knowledge_gateway_cache.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py`) is archived. `cache_migration_plan.md` itself
documents that all 5 of its own ordered migrations are "real, implemented code" added by since-
archived tickets — it is a design record for dead infrastructure, not live guidance. Confirmed
clearly historical too (the ticket's "confirm" was warranted caution, but the confirmation lands
the same way as the 8 already-clear cases).

### `audit_phase0_5.md` — judgment call, resolved to historical

Read in full (208 lines). It is a **consolidated, point-in-time audit** ("as of 2026-08-16") of
everything built/measured in Phases 0-5 of the now-archived gateway. Its own two trailing
"Status update" postscripts (2026-08-24 and 2026-09-07) both point *away* from itself and toward
`keep_or_deprecate_decision.md` as the current authoritative record: "that call has now been
made. See `keep_or_deprecate_decision.md`..." and "...has been superseded. See
`keep_or_deprecate_decision.md` §4...". Every sentence in the document describes past
measurements against dead code, not currently-enforced behavior.

**Recommendation: `historical`.** The re-ratification document it is cited as evidence for
(`keep_or_deprecate_decision.md`) is *itself already* `status: historical` (verified directly —
frontmatter line 2 reads `status: historical`), and citing a historical decision's own evidence
record does not require the evidence record to stay `active` — every one of the 8
"clearly historical" phase docs is *also* cited, repeatedly, by `keep_or_deprecate_decision.md`
and by `audit_phase0_5.md` itself, and citation-as-evidence was never treated as a reason to keep
those `active`. "Retains reference value" (the ticket's own phrasing) is true of every historical
doc in this repository — it is not a distinguishing reason to treat this one file differently
from its 8 sibling phase-record docs, which share the exact same "consolidated point-in-time
measurement/audit of now-dead infrastructure" shape. Marking it `historical` is also what keeps
`search_docs` from over-weighting it as current guidance — the precise symptom this whole ticket
exists to fix.

### `redaction_retention_policy.md` — do NOT blanket-mark, resolved below

See dedicated section.

## Mechanics / Engine Constraints

No `docs/mechanics/` chapter or `docs/engine/` kernel/pipeline contract governs this work — the
Knowledge Gateway MCP is agent-orchestration/retrieval tooling (explicitly classified as not
requiring a parity ledger entry by its own sibling docs' §5/§6 sections), not a simulation-law
subsystem. The only real constraint is CLAUDE.md's own Authoritative Mechanics Rule's spirit
(docs and code must stay in semantic parity) applied to `docs/REGISTRY.yaml`'s `status` field and
`tools/generate_registry.py`'s `STATUS_VALUES = {"authoritative", "active", "historical",
"archive"}` allowlist (`tools/validate_frontmatter.py:44`) — `historical` is the correct,
pre-existing value for "no longer current but retained as record," already used by
`keep_or_deprecate_decision.md` and by every stored-artifact `investigation.md`/`test_plan.md`
this pipeline itself produces (including this one).

## `redaction_retention_policy.md` — live vs. historical content, and the resolution

Read in full (453 lines, 12 sections). `tools/write_path_guard.py`'s own module docstring
(`tools/write_path_guard.py:1-34`) is the authoritative, already-written map of exactly which
sections of this doc are still enforced in code vs. which described dead infrastructure:

**Still live** (backed by real, called code today):
- §2 Eligible Source Types/Allowlist — `check_allowlist()`, `ALLOWED_SOURCE_TYPES` (2 entries,
  unchanged).
- §3 Redaction Rules — `redact_content()`.
- §4 Secret-Scan Disclosure (the 10-pattern baseline) — `scan_for_secrets()`. **This is the exact
  function the live `PreToolUse:Bash` hook calls** (`.claude/settings.json:97`,
  `from tools.write_path_guard import scan_for_secrets`) — the one section this ticket's own
  framing is built around.
- §5 Payload Size Cap — `check_size_cap()`, `MAX_PAYLOAD_BYTES = 65536`, cross-checked live by
  `tests/docs/test_redaction_retention_policy_doc.py::test_payload_size_cap_doc_matches_live_module_constant`.
- §6 Redaction-Policy Version — `redaction_policy_version`, `WriteDecision`,
  `evaluate_write_candidate()` (the fixed-order orchestrator; has no live production caller today
  — `tools/retrieval_cache.py` only references it in docstrings — but is real, tested,
  non-archived code with a named future consumer per the module docstring:
  `governance_capability_policy_epic.md` M4).
- §7 Never-Cache Enumeration — `check_never_cache_categories()`.
- §9 (partial) — only the `open_connection_with_limits()` paragraph (WAL mode, busy_timeout,
  chmod 0600). Confirmed live: `tools/retrieval_cache.py:634,1043,1239` all call
  `_write_path_guard.open_connection_with_limits()`.

**Genuinely historical** (moved to the archived `tools/archive/knowledge_gateway_redaction.py`,
or never had a surviving consumer):
- §1 Purpose — frames the whole document around "future cached *payload* rows" for the gateway's
  own response caching, which is the archived feature.
- §8 Token-Counting Method (`kgmcp_char_heuristic_v1`) — implemented at
  `tools/knowledge_gateway_packet_assembly.py:81`, now archived at
  `tools/archive/knowledge_gateway_packet_assembly.py`; no live caller.
- §9 (remainder) — `check_db_size_within_limit()`, `execute_bounded_transaction()`,
  `acquire_write_guard()`/`release_write_guard()` all "stayed behind" in the archived module per
  `tools/write_path_guard.py`'s own docstring — no live consumer outside the archived gateway.
- §10 Cache-GC Defaults — describes automatic GC that was never implemented even when the gateway
  was live; the one real eviction mechanism it discusses (`prune()`) is `tools/retrieval_cache.py`
  operator-only tooling, not gateway-specific, and this section's content is entirely
  forward-looking policy for a feature that will now never be built.
  the `redaction_retention_policy.md` doc.
- §11 Ratification Status — historical narrative about a ratification event for the (now
  abandoned) Phase 2 payload-caching feature.
- §12 Cross-References — mixed; several entries point at now-archived sibling docs/tests.

### Resolution: explicit scoped note, status stays `active` — not a file split

**Recommendation: keep `redaction_retention_policy.md`'s frontmatter `status: active` unchanged**
(it is already correct — do not touch it) **and add an explicit scoped-status note** near the top
of the document (immediately after the existing intro paragraph, before §1) stating in plain
terms which sections are still enforced (§2-§7, and only the `open_connection_with_limits()`
paragraph of §9) and pointing at `tools/write_path_guard.py` as the current source of truth for
that live subset, versus which sections (§1's framing, §8, the remainder of §9, §10, §11) are
historical record for the archived payload-caching feature and are retained for context only.

**Why a scoped note, not a physical split, is the right call — precedent check:**
- No file-internal "part active / part historical" precedent exists anywhere in this repository.
  Searched `docs/guidelines/intentional_divergences.md` and grepped
  `docs/**/*.md` for a "Status: active (see live sections) / historical (see retired sections)"
  pattern (or any `status_note`/`scoped_status` convention) — zero hits. Every other precedent in
  this repo uses one `status:` value per file (confirmed via `docs/REGISTRY.yaml`'s schema and
  `tools/validate_frontmatter.py`'s `STATUS_VALUES` enum, which is a single scalar field, not a
  per-section map).
- `tests/docs/test_redaction_retention_policy_doc.py` (191 lines) is a tightly-coupled,
  whole-file structure test asserting AC1-AC7 of the *original*
  `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY` ticket against this single file's full text —
  required headings for §1 through §7, the §5/code cross-check, §8's token-counting phrases, §9's
  SQLite-limit phrases, §10's GC-deference phrases, and §11's ratification phrasing. A physical
  split (moving §8/§9-remainder/§10/§11 to a second, `historical`-status file) would force a
  nontrivial rewrite of this test file's path references and section-grouping, for a doc whose
  live consumer (`tools/write_path_guard.py`) already carries its own authoritative live/historical
  section map in its own docstring — the split would duplicate information that already exists in
  a more durable, code-adjacent location, at real risk to a working regression test, for no
  functional gain (the doc's `status:` field is already correctly `active` since real live policy
  content exists in it; nothing is being mis-signaled today).
- A scoped note is reversible, low-risk, additive-only (no section is deleted, moved, or
  reordered), and directly satisfies AC #2's actual requirement: "not wrongly retired." Nothing
  is retired by this approach — the note only clarifies which parts of an already-`active` doc
  back live code and which are retained historical framing.

This is a considered decision, not the default: a split was seriously evaluated and rejected for
the concrete regression-risk and precedent-absence reasons above, not skipped for convenience.

## Docs Requiring Update

- `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md`: change `status:` from `active` to `historical` — pure measurement record for the archived gateway, no live consumer.
- `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md`: change `status:` from `active` to `historical` — same reason.
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`: change `status:` from `active` to `historical` — same reason.
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md`: change `status:` from `active` to `historical` — same reason.
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_warm_direct_tool_comparison.md`: change `status:` from `active` to `historical` — same reason.
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md`: change `status:` from `active` to `historical` — same reason.
- `docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md`: change `status:` from `active` to `historical` — same reason.
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`: change `status:` from `active` to `historical` — same reason.
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`: change `status:` from `active` to `historical` — design contract for archived cache/router/packet-assembly modules, no live consumer.
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`: change `status:` from `active` to `historical` — same reason.
- `docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md`: change `status:` from `active` to `historical` — consolidated point-in-time audit of now-archived infrastructure, superseded by the already-historical `keep_or_deprecate_decision.md`; see reasoning above.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`: add an explicit scoped-status note distinguishing the still-live §2-§7 (+ `open_connection_with_limits()` of §9) content, now implemented in `tools/write_path_guard.py` and consumed by the live `PreToolUse:Bash` secret-scan hook, from the historical §1/§8/§9-remainder/§10/§11 content describing the archived payload-caching feature. `status:` itself stays `active` (already correct) — this is a content addition, not a status change, but the doc is touched and therefore belongs in this bullet.
- `docs/REGISTRY.yaml`: regenerate via `make docs-registry` (or Finalize's automatic regeneration) after the 11 status changes above so the registry reflects the new statuses.

The following docs were considered and are explicitly excluded from this bullet list (Format 2,
prose only):

`docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md` (path:
`docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md`) requires no change —
it is already `status: historical`, confirmed directly by reading its frontmatter.

The `.json` schema files under `docs/engine/contracts/knowledge_gateway_mcp/` (path prefix:
`docs/engine/contracts/knowledge_gateway_mcp/*.schema.json` and
`docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_*.json`) are explicitly out of
scope per this ticket's own Out of Scope section — they carry no frontmatter and are not
registry-indexed, so a `status:` sweep cannot apply to them.

`docs/engine/contracts/knowledge_gateway_mcp_contract.md` (the sibling top-level wire-contract
document, one directory up from the swept subdirectory) is outside this ticket's own Scope (which
names only the `knowledge_gateway_mcp/` subdirectory's 13 files) and is not touched — its own
status was not re-verified as part of this investigation and is left for a future ticket if it
also needs a sweep.

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml` entries `INFRA-340` through `INFRA-359` cover this whole
KGMCP arc (checked directly). All entries in the `INFRA-344`-`INFRA-356` range this ticket's
Related Docs cite are `status: verified`, priority `P1` or `P2` — **no P0 entries** among them, so
no entry requires a newly-passing `test_path` as a gate for this doc-only sweep.
`INFRA-342` (`P1`, `verified`) is specifically the `write_path_guard.py` entry
(`test_path: tests/tools/test_write_path_guard.py`, 54 tests) — the live code this ticket's
`redaction_retention_policy.md` resolution points readers toward; it is unaffected by this
ticket's doc-only changes (no code changes in this ticket's scope) and needs no ledger update.
No new parity ledger entry is required — a pure `status:` frontmatter sweep is not a behavior
change, so `docs/parity_ledger/` is not updated by this ticket (consistent with every sibling
Phase 0-5 doc already carrying "No `docs/parity_ledger/` entry accompanies this document" language
for the same non-engine-behavior reason).

## Prior Work

- `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` (stored_artifacts + tickets/done): the ticket
  that archived `tools/knowledge_gateway_mcp.py`/`knowledge_gateway_router.py`/
  `knowledge_gateway_cache.py`/`knowledge_gateway_packet_assembly.py` and extracted the still-live
  redaction/write-path functions into `tools/write_path_guard.py`. Its own investigation is the
  origin of this ticket's deferred-sweep note and the authoritative source for exactly which
  functions/sections moved where — reused directly above rather than re-derived.
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`: the sibling execution ticket, blocked on its own
  2-week monitoring window, whose Out of Scope deferred this exact sweep here. Confirmed
  independent — this ticket's doc-only changes have no dependency on that window.
- `TCK-20260904-BASH-SECRET-SCAN-HOOK` (tickets/done + stored_artifacts): the ticket that wired
  `scan_for_secrets()` into the live `.claude/settings.json` `PreToolUse:Bash` hook (already
  merged on this branch, confirmed via `git log` showing commit `5c48e810` and the ticket file
  already in `tickets/done/`). This is the concrete "still live" consumer motivating the
  `redaction_retention_policy.md` carve-out.
- `TCK-20260616-DOCS-BATCH-ENGINE` (tickets/done): a prior `docs/engine/` batch-status pass. Not a
  direct mechanical precedent for *this* sweep's mechanics — it treats `status: historical` as a
  trigger to physically *move* files to `docs/archive/` and rewrite them fresh (readability-pass
  scope), which this ticket's own Out of Scope explicitly forbids ("Deleting any of these docs —
  they stay as historical record"). Establishes only that `status: historical` is the correct,
  established value name (not `archive`, not a bespoke value) for a doc that is no longer current.
- `TCK-20260606-DOCSITE-FM-ARCHIVE` (tickets/done): a bulk frontmatter-application pass, but for
  files already physically located under `docs/archive/`, using `status: archive` (a different
  value, for a different physical-location convention) plus `audience: historical`. Not a
  mechanical precedent either — no bulk-edit tool exists there that fits this ticket's shape
  (in-place `status:` value change only, no relocation, no new frontmatter fields). No sanctioned
  bulk-edit tool exists for this exact "flip status: active to status: historical in place" shape
  anywhere in `tools/` — confirmed by grepping for `add_frontmatter` / `status_sweep` /
  `sweep_status` scripts and finding only `tools/add_frontmatter_archive.py` (the
  DOCSITE-FM-ARCHIVE script, which prepends frontmatter to files that have none — not applicable
  here, since all 13 files already have frontmatter). **Manual per-file `Edit` of the `status:`
  line is therefore the correct mechanism** — 11 single-line edits, not a new bulk tool.

## Risks and Open Questions

- None blocking. The one previously-open question (`audit_phase0_5.md`'s status) is resolved
  above with reasoning, not left open.
- Minor residual risk: `redaction_retention_policy.md`'s scoped note is new prose added to a
  regression-tested doc (`tests/docs/test_redaction_retention_policy_doc.py` asserts exact
  substrings). The note must be added in a way that does not disturb any of the existing required
  headings/phrases that test asserts (`## 1. Purpose` through `## 7. Never-Cache Enumeration`
  headings, `"not a production-complete secret scanner"`, `"NEW"`, the `MAX_PAYLOAD_BYTES` value,
  `"kgmcp_char_heuristic_v1"`, the SQLite-limit phrases, the GC-deference phrases, and the
  ratification phrases) — Plan/Implement must place the new note as an insertion before `## 1.
  Purpose` (or as a clearly-separate subsection) and must re-run
  `tests/docs/test_redaction_retention_policy_doc.py` unchanged (no assertion edits) to confirm no
  existing required text was disturbed.
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` (the sibling top-level file, one
  directory up) was not assessed — out of this ticket's Scope by its own text (only the
  subdirectory's 13 files), but a reader following the sweep might reasonably wonder about it. Not
  a blocker; flagged for a future ticket if warranted.

## Anti-Drift Hazards

- Do not touch `redaction_retention_policy.md`'s `status:` frontmatter value — it must stay
  `active`. Flipping it to `historical` (even accidentally, by pattern-matching the other 11
  bullets) would be the exact wrongly-retired-live-policy outcome this ticket's own AC #2 exists
  to prevent, and would desynchronize the doc from `tools/write_path_guard.py`'s real, live,
  tested behavior.
- Do not physically move or delete any of the 13 files — this ticket's Out of Scope is explicit
  that they "stay as historical record."
- Do not touch anything in `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`'s own scope (the
  `tools/archive/` hard-delete, parity-entry finalization, `norecursedirs` cleanup) — that ticket
  remains independently blocked on its 2-week monitoring window regardless of this ticket landing.
- Do not re-litigate the Option C deprecation decision — settled per `keep_or_deprecate_decision.md`
  §4.
- Do not widen scope to `docs/engine/contracts/knowledge_gateway_mcp_contract.md` (the sibling
  top-level doc one directory up) — explicitly outside this ticket's named Scope.
- After the 11 `status:` edits, `docs/REGISTRY.yaml` must be regenerated (`make docs-registry` or
  Finalize's automatic post-migration regeneration) and `make knowledge-index-update` must be run
  — both are named Acceptance Criteria, not optional cleanup.
