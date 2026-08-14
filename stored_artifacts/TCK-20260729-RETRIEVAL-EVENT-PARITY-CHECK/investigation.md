---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK
artifact_type: investigation
tags: [testing, observability, agent-monitoring]
---

# Investigation — TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK

## Current Behavior

### `tools/retrieval_events.py` — the field-list artifact under test (dependency now landed)
The hard dependency (`TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT`) is DONE
(`tickets/done/TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT.md`). The concrete artifact this ticket
must validate exists and is a module-level constant, not a TypedDict/dataclass:

- `RETRIEVAL_EVENT_FIELDS: frozenset[str]` — `tools/retrieval_events.py:52-73` — 18 names
  (`retrieval_version`, `corpus_generation`, `cache_level`, `cache_status`, `latency_ms`,
  `candidate_count`, `selected_count`, `source_kind_counts`, `authority_counts`,
  `freshness_counts`, `exclusion_reason_counts`, `cited_source_hashes`, `adequacy_verdict`,
  `expansion_reason`, `expansion_count`, `scenario`, `risk_tier`,
  `retrieval_event_schema_version`).
- Module docstring (`tools/retrieval_events.py:13-14`) and an inline comment at `:51` both state
  the exclusion of `execution_id`/`provider` is deliberate, citing
  `docs/ai/monitoring_writer_decision.md` §2.
- Import path confirmed: `from tools import retrieval_events as re_mod` then
  `re_mod.RETRIEVAL_EVENT_FIELDS` (see `tests/tools/test_retrieval_events.py:20-27`).

### `tools/agent_replay_codex/provenance_check.py` — the style to mirror
`assert_no_codex_provider_writes(agent_monitoring_dir: Path, provider_value: str = "codex") -> None`
(`provenance_check.py:18-38`): reads the **real** `runs.jsonl`/`events.jsonl`/`tools.jsonl` files
line-by-line, raises `ContainmentViolationError` (from `tools/agent_replay_codex/errors.py:17-19`)
the first time a record's `"provider"` key equals `provider_value`. No-op (`continue`) on a missing
file or an unparseable line. Read-only — never writes.

This checks **live data on disk** for a forbidden *value*. This ticket's target is structurally
different: it must check a **schema/field-name constant already in memory** (no file I/O) for a
forbidden *field name* (exact match or provider-prefix pattern), which the existing function's
shape does not directly generalize to — the new check needs its own small function, not a
parameterization of `assert_no_codex_provider_writes`.

`tools/agent_replay_codex/errors.py` (full file, 24 lines) has 4 exceptions, all package-specific
to Codex replay/consent/containment/invocation. None fits "a provider-specific field name was
found in a schema constant" semantically — `ContainmentViolationError`'s docstring is scoped to
"a pre/post snapshot diff" or "the committed `.codex/config.toml`", not schema shape. A new
exception is warranted rather than reusing one of these four (see Anti-Drift Hazards).

### `tests/agent_replay_codex/test_monitoring_provenance.py` — the test style to mirror
Two tests (`test_monitoring_provenance.py:17-31`):
1. `test_real_monitoring_corpus_has_zero_codex_provider_records` — calls the check against the
   real `agent-monitoring/` dir, asserts no exception (positive/regression check on live data).
2. `test_negative_control_raises_on_a_codex_provider_record` — builds a `tmp_path` fixture with a
   fabricated `provider: "codex"` record, asserts `pytest.raises(ContainmentViolationError)`.

This exact two-test shape (real-artifact check + tmp_path negative control) is the pattern to
reproduce, adapted to a schema constant instead of a JSONL corpus.

### Gap found: `tests/tools/test_retrieval_events.py` already has a *partial*, non-reusable version of AC1-3
The sibling ticket's own Step 3 (AC3 in that ticket) already added, in
`tests/tools/test_retrieval_events.py`, class `TestSchemaExcludesRawTextAndIdentityFields`:
- `test_no_execution_id_provider_or_raw_text_field` — inline asserts
  `"execution_id" not in fields`, `"provider" not in fields`, and a small
  `{"raw_prompt","raw_text","chunk_text","retrieved_content","payload"}` disjointness check,
  directly against `re_mod.RETRIEVAL_EVENT_FIELDS`.
- `test_cited_source_hashes_is_the_only_content_adjacent_field_and_is_hash_shaped` — a redaction
  shape check (unrelated to provider-parity).

This satisfies part of this ticket's AC2 (explicit assertion that `execution_id`/`provider` are
absent) as **inline literal assertions**, but:
- It is not a standalone, importable **check function** (no `assert_..._parity(...)`-shaped API to
  reuse the way `assert_no_codex_provider_writes()` is reusable) — there is nothing to invoke
  against an arbitrary/injected fixture.
- It has **no negative-control test** — nothing in that file proves the check would actually catch
  a provider-specific field if one were added (this ticket's AC4 requirement).
- It checks a fixed, small denylist of forbidden literal names (`raw_prompt`, etc.), not the
  broader "no field literally naming or prefixing a single provider" shape this ticket's AC1
  requires (e.g. a hypothetical `codex_latency_ms` or `claude_cache_status` would not be caught by
  the existing test, since neither name is in that denylist).

**Conclusion:** this ticket is not fully redundant with the sibling ticket's Step 3, but it must
build a genuinely new, reusable, negative-control-tested check — not just re-assert what
`test_retrieval_events.py` already inline-asserts. The new module/test should be additive and must
not duplicate or contradict the existing `TestSchemaExcludesRawTextAndIdentityFields` class.

### `docs/agent-monitoring/schema.md` — documentation of the field family
`schema.md:246-291`, "Retrieval-event field family (additive)": documents all 18 fields in a
table, states `tools/retrieval_events.py` is the single source of truth (doc is illustrative only,
same convention as `vocabulary.py`), and covers the `RETRIEVAL-EVENT-<slug>` `run_id` prefix
convention. No provider-parity language appears here — this doc does not need editing for this
ticket unless a new doc cross-reference is desired (not required by acceptance criteria).

### `docs/observability/retrieval_retention_redaction_policy.md`
Decision-only doc (no code changes). Establishes MAY-contain (hashes, IDs, counts, reason codes,
scores, latency, versions, cache status) vs. PROHIBITED (raw prompt/chunk text, full tool
payloads) categories for retrieval events. Orthogonal to this ticket's provider-neutrality concern
— it governs *content* redaction, not *provider-naming* in the schema. Already exercised by the
sibling ticket's `test_cited_source_hashes_is_the_only_content_adjacent_field_and_is_hash_shaped`.
No changes needed here.

## Mechanics / Engine Constraints

None. This is agent-orchestration/monitoring tooling, not simulation logic — same
`support_boundary` category as `INFRA-281` through `INFRA-297` in the parity ledger: "no
simulation behavior, Mechanics Bible chapter, or engine contract governs this module's semantics."
No `docs/mechanics/` chapter or `docs/engine/` contract is implicated.

## Parity Ledger Overlap

- **INFRA-297** (`docs/parity_ledger/infrastructure.yaml:6174`) — status `verified`, priority
  `P2`, `test_path: tests/tools/test_retrieval_events.py`. Covers `tools/retrieval_events.py`'s
  field-shape constant and emission path (the artifact this ticket's check validates). Its
  `v2_evidence` already cites `RETRIEVAL_EVENT_FIELDS` excluding `execution_id`/`provider`
  (`infrastructure.yaml:6197-6199`). This ticket does not change `retrieval_events.py`'s behavior,
  so INFRA-297's `status`/`v2_evidence` do not need editing — but its `test_path` could optionally
  be widened, or a **new entry** added, to reference the new structural check module (see below).
  No P0 entries are implicated (INFRA-297 is P2), so there is no hard "must pass before merge"
  ledger gate beyond the ticket's own AC.
- **Precedent for "does this need its own ledger entry": TCK-20260721-CODEX-REPLAY-PARITY** (the
  ticket that created `provenance_check.py` itself, along with 3 other Codex-replay-parity
  packages/tests) has **zero** `infrastructure.yaml` entries referencing it
  (`grep -n "CODEX-REPLAY-PARITY" docs/parity_ledger/infrastructure.yaml` returns nothing) despite
  being a substantially larger change than this ticket. This suggests test-only/structural-guard
  additions in this family of tickets have not historically required a dedicated ledger entry.
  Flagged as an **open question** below rather than assumed — see Risks and Open Questions.
- No other `infrastructure.yaml` entry (INFRA-278 through INFRA-296, checked by range) references
  provider-parity or provenance-check concepts.

## Prior Work

- **`stored_artifacts/TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT/`** (investigation.md, plan.md) —
  the sibling ticket. Its investigation.md explicitly names
  `test_execution_identity_fields_pass_through_unchanged` as the load-bearing precedent proving
  `record_events.validate_record()` passes unknown optional fields through unchanged (this is why
  `execution_id`/`provider`/`ticket_id` *could* be added later without a schema migration, and
  exactly why this ticket needs to assert they currently are **not** present — that precedent makes
  future addition easy, which is the risk this ticket's check guards against). Its plan.md Step 3
  is the already-implemented partial overlap described above (gap analysis).
- **`tickets/done/TCK-20260721-CODEX-REPLAY-PARITY.md`** +
  `stored_artifacts/TCK-20260721-CODEX-REPLAY-PARITY/plan.md` (Step 9, lines 520-546) — the
  ticket that created `provenance_check.py`/`errors.py`/`test_monitoring_provenance.py`. Its plan
  explicitly frames the check as "an always-runnable structural invariant (does not require a real
  Codex invocation)" and specifies the exact two-test shape (real-corpus positive +
  `tmp_path` negative control) this ticket's AC4 asks to mirror. Directly reusable template.
- **`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`**
  line 77 ("Provider-neutral semantics. Claude Code and Codex use the same context...") and line
  190 ("Add a versioned, provider-neutral retrieval event family...") — this is the origin of the
  "provider-neutral" requirement this ticket's check formalizes; no prior ticket in this epic has
  yet added an automated check for it (this ticket is the first).
- No other `tickets/done/` ticket builds a structural/field-shape parity check specifically (the
  `grep` for "negative control"/"provider-neutral"/"structural parity" across `tickets/done/`
  surfaced only tickets tangential to this scope: workflow security gates, tag taxonomy,
  orchestration contracts — none build a comparable field-name-denylist check).

## Risks and Open Questions

- **BLOCKS PLANNING: where should the new check module and its exception class live?** Two
  defensible options, neither clearly mandated by the ticket:
  1. Inside `tools/agent_replay_codex/` (reusing that package's `errors.py`, adding e.g. a new
     `ProviderFieldViolationError`) — matches the ticket's Related Code Areas listing that
     package's files, and keeps all "provider parity" checks in one package.
  2. Beside `tools/retrieval_events.py` (a new `tools/retrieval_events_parity_check.py` or similar,
     with its own small `errors.py` or a locally-defined exception) — matches where the actual
     artifact under test (`RETRIEVAL_EVENT_FIELDS`) lives, and avoids importing Codex-specific
     replay/consent/containment machinery into a check that has nothing to do with Codex
     invocation, consent gates, or shadow-mode comparison (`tools/agent_replay_codex/` is a
     purpose-built package for actually invoking/replaying Codex — this check never invokes
     anything).
  This is a real design fork the planner must resolve, not an implementation detail — do not
  assume either without a documented decision in plan.md.
- **Does this ticket need a new `INFRA-29x` (next: `INFRA-298`) ledger entry, or is it exempt like
  `TCK-20260721-CODEX-REPLAY-PARITY` was?** CLAUDE.md's Authoritative Mechanics Rule says "If no
  entry exists, add one" when a behavior changes — but this ticket changes no runtime behavior (it
  only adds a read-only structural check + tests). The `TCK-20260721-CODEX-REPLAY-PARITY` precedent
  (zero ledger entries for a comparable or larger test-only/structural-guard addition) argues for
  no new entry, but this is not a guaranteed rule — flagging for the planner/parity-updater rather
  than deciding unilaterally.
- **What exact provider-prefix pattern should AC1's "no field literally naming or prefixing a
  single provider" check use?** The ticket says "e.g. `codex_*`/`claude_*`-prefixed" — these are
  examples, not an exhaustive closed list. A denylist of two prefixes would not catch a
  differently-named provider field (e.g. `anthropic_*`, `gpt_*`). Recommend implementing this as a
  substring/prefix check against a small, documented, extensible list of known provider tokens
  (`codex`, `claude`, `anthropic`) rather than a hardcoded 2-item check — but the exact token list
  is a plan.md decision, not assumed here.
- No live data exists to assert against (confirmed — `RETRIEVAL_EVENT_FIELDS` is a static,
  in-memory constant with zero real `RETRIEVAL-EVENT-*` records in the live
  `agent-monitoring/events.jsonl` today, per `schema.md:288-291`). The check is definitional only,
  consistent with the ticket's own Assumptions section.

## Anti-Drift Hazards

- **Do not reuse `ContainmentViolationError` for this new check.** Its docstring is scoped to
  monitoring-corpus/config-file snapshot diffs, not schema-constant field-name violations — reusing
  it would misdocument what the exception actually means at each of its raise sites. Define a new,
  narrowly-scoped exception instead (see Risks above for placement).
- **Do not modify `tools/retrieval_events.py`'s `RETRIEVAL_EVENT_FIELDS` constant, or any of its
  17 field names, as part of adding this check.** The ticket's Out of Scope is explicit: this
  ticket confirms absence, it does not add `execution_id`/`provider`. Any implementation that
  "fixes" the schema instead of just asserting about it is scope creep.
- **Do not duplicate or fork `TestSchemaExcludesRawTextAndIdentityFields` in
  `tests/tools/test_retrieval_events.py`.** That class already exists and passes; a new,
  identically-scoped test class in the same file would be redundant. The new test module should be
  additive (a genuinely reusable check function + its own negative control), not a rewrite of the
  sibling ticket's existing coverage.
- **Do not set `CODEX_REPLAY_PARITY_LIVE_CONSENT`, invoke the real `codex` CLI, or touch
  `tools/agent_replay_codex/consent_gate.py`/`invoker.py`/`shadow_mode.py`.** Explicit Out of
  Scope. This ticket's "parity" is structural/definitional only — it must never accidentally pull
  in the live-Codex-pilot machinery from the sibling package it borrows *style* from.
  `errors.py`/`provenance_check.py` are the only two files from that package this ticket may read
  for style; none of the others should be imported or exercised.
- **Do not touch `tools/agent-monitoring/writer.py`'s `write_line`/`write_lines` functions.**
  Explicit Out of Scope — "No new writer mechanism." This check is read-only against an in-memory
  constant; it should never call into the writer path at all (unlike `retrieval_events.py`'s own
  `emit_retrieval_event()`, which legitimately does).
- **Do not wire this check into any `.claude/workflows/*.js` file.** Explicit Out of Scope,
  consistent with every other Phase 3/4 retrieval ticket in this epic.
- **Do not weaken the negative-control test into a tautology.** The injected provider-specific
  field in the negative-control fixture must be realistic (e.g. `"codex_latency_ms"` or
  `"claude_cache_status"` added to a copy of the real field set), not a trivially-obvious string
  like `"PROVIDER_FIELD_XYZ"` that no real schema drift would ever produce — the point is proving
  the check would catch a plausible accidental addition.
