---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL
phase: open
date: 2026-08-23
tags: [architecture, observability, api-design]
---

# TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL

## Title
Per-client HTTP admission control extending `ObservabilityMode`'s NORMAL/PRESSURE/DEGRADED/SURVIVAL vocabulary

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`src/api/server.py` has no rate limiting or admission control — a single client (malicious,
buggy, or just noisy) can degrade service for every other tenant. Item 2 of 2 extracted from
`TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC` — depends on `TCK-20260823-HTTP-API-KEY-AUTH` landing
first, since per-client admission state is keyed by the client identity that ticket establishes.
The mode vocabulary to extend is `ObservabilityMode` (`NORMAL/PRESSURE/DEGRADED/SURVIVAL`,
`src/observability/event_recorder.py`) — **not** `RuntimeMode`
(`NORMAL/CONSTRAINED/DEGRADED/SURVIVAL`, `src/core/governance.py`), a second, differently-named,
easily-confused vocabulary serving an unrelated subsystem. This ticket's own acceptance criteria
match `ObservabilityMode`'s exact naming.

## Scope
- Extend `ObservabilityMode`'s vocabulary/pattern to the HTTP layer, **per-client** (not just a
  single global mode) — reuse the mode names and the `observability_status()`/`reset_mode()`
  accessor-pattern shape (`src/observability/event_recorder.py` §5,
  `docs/architecture/observability_hot_path_safety_contract.md` §5) as the template for an
  equivalent `admission_status()`/`reset_admission_mode()` pair, scoped per-client.
- Reuse `ResourceGovernor`'s hysteresis pattern (`src/engine/governor.py::evaluate()`/
  `_can_recover()`) — NOT `PhaseBudgetGovernor`, which has no hysteresis logic of its own (a
  factual correction from this ticket's parent investigation; do not propagate the doc's own
  mis-attribution into new code/comments). Escalation is immediate on any mode increase; recovery
  requires `dwell_time_ticks` elapsed plus `confidence_window_ticks` consecutive good samples,
  stepping down one level at a time. Reuse `RuntimeProfile`'s existing tunables
  (`recovery_watermark`, `dwell_time_ticks`, `confidence_window_ticks`,
  `src/config/profiles.py:42-44`) rather than inventing new ones.
- **Per-client state bounding**: a dict keyed by client ID holding each client's own
  mode/dwell-tick/confidence-window state is new, previously-unbounded state — this ticket must
  design and implement an eviction/TTL policy for stale/inactive client entries (this is flagged
  by the parent investigation as the single largest genuinely new design surface in this whole
  epic; do not treat it as an afterthought).
- Single-process in-memory token-bucket/sliding-window limiter — sufficient at current scale per
  the source audit's own explicit recommendation.
- Wire into `src/api/server.py` as FastAPI middleware or `Depends()` (Plan decision), reading the
  authenticated client identity `TCK-20260823-HTTP-API-KEY-AUTH` establishes — never reaching into
  `src/engine/governor.py` internals directly from `src/api/` (the existing API/engine module
  boundary is read-through-`V2EngineManager` only).
- Confirm and use `SURVIVAL` as the 4th tier name (matching `ObservabilityMode` and this ticket's
  own acceptance criteria) — `docs/audits/D23_architecture_resilience.md` §L is internally
  inconsistent and calls it `EMERGENCY` in one place; that is the source doc's own drafting error,
  not a real naming option to reconcile.

## Out of Scope
- Any new distributed/shared rate-limit infrastructure (Redis-backed or otherwise) — `redis` being
  an existing dependency is not license to use it here; single-process in-memory only.
- Modifying `ObservabilityMode`/`ObservabilityController` itself, or `RuntimeMode`/
  `PhaseBudgetGovernor`/`ResourceGovernor` — read/reuse their pattern, do not alter the existing,
  already-tested (`tests/unit/observability/test_obs_backpressure.py`, parity entry INFRA-199, P1)
  subsystems. If a shared parallel controller for the HTTP layer touches the same module as
  `ObservabilityController`, `test_obs_backpressure.py` becomes part of this ticket's own
  regression surface and must stay green.
- Auth itself (delivered by the sibling ticket this one depends on).

## Acceptance Criteria
- [x] HTTP requests are admitted/throttled/shed **per-client**, keyed by the authenticated client
      identity from `TCK-20260823-HTTP-API-KEY-AUTH`.
- [x] The mode vocabulary is exactly `NORMAL/PRESSURE/DEGRADED/SURVIVAL` (matching
      `ObservabilityMode`), never `RuntimeMode`'s `CONSTRAINED` naming or a third invented
      vocabulary.
- [x] Escalation is immediate; recovery is gated by dwell-time + confidence-window, one mode level
      at a time — mirroring `ResourceGovernor`'s real hysteresis pattern.
- [x] Per-client state has an explicit, tested eviction/TTL policy — no unbounded growth from an
      ever-increasing set of distinct client IDs.
- [x] `tests/unit/observability/test_obs_backpressure.py` (the existing `ObservabilityMode`
      regression suite) stays green — confirmed if this ticket's implementation touches the same
      module, or confirmed inapplicable if it builds a fully parallel HTTP-side controller.
- [x] `tests/api/` gains real, in-process `TestClient`-based tests covering per-client throttling
      behavior across at least 2 distinct simulated clients (one throttled, one unaffected).

## Related Tickets
- TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC (parent — extracted from here, 2026-08-23)
- TCK-20260823-HTTP-API-KEY-AUTH (sibling — this ticket depends on it; implement first)

## Related Docs
- docs/plans/http_admission_control_epic.md
- docs/architecture/observability_hot_path_safety_contract.md
- docs/audits/D23_architecture_resilience.md

## Related Stored Artifacts
- staging_artifacts/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC/investigation.md (parent epic's
  shared investigation — read first; do not re-derive its findings)

## Related Code Areas
- src/api/server.py
- src/observability/event_recorder.py (read/reuse pattern, do not modify)
- src/engine/governor.py (read/reuse hysteresis pattern, do not modify)
- src/config/profiles.py
- expected: src/api/admission_control.py (or equivalent new module — exact name is a Plan decision)
- expected: tests/api/test_admission_control.py

## Assumptions / Open Questions
- Exact new module/file naming is a Plan decision, not fixed here.
- Whether this ticket builds a fully independent HTTP-side mode controller or literally reuses
  `ObservabilityController`'s class (parameterized per-client) is a Plan decision — Investigate
  should weigh both against `test_obs_backpressure.py`'s existing regression surface.

## Implementation Notes

Implemented all 9 plan steps in order.

- **Step 1**: `src/api/admission_control.py` created verbatim from plan.md's Step 1 source
  (`_MODE_RANK`/`_MODE_BY_RANK`, module constants, `_ClientAdmissionState`,
  `configure_admission_control()`, `_touch_lru()`, `_prune_idle_clients()`,
  `_evict_lru_if_over_capacity()`, `_get_or_create_state()`, `_consume_token()`,
  `_recovery_limit_for()`, `_can_recover()`, `_evaluate()`, `_check_admission()`,
  `require_admission`/`require_admission_header_or_query`/`require_admission_ws`,
  `admission_status()`, `reset_admission_mode()`). Verified against direct reads of
  `src/observability/event_recorder.py` (`ObservabilityMode`/`ObservabilityController` shape,
  thresholds), `src/config/profiles.py` (`RuntimeProfile` tunables), and `src/api/auth.py`
  (`ClientIdentity`/`require_api_key*`) — all matched the plan's citations exactly.
- **Step 2**: `src/api/server.py` wired per plan — `configure_admission_control(profile)` added
  immediately after `configure_api_keys(profile)`; all 27 `dependencies=[Depends(require_api_key*)]`
  sites confirmed at the plan's cited line numbers (unchanged since plan-write time) and updated.
  **Deviation** (see below): 23 sites use pure replace per Decision 2; 4 sites (3 dashboard routes
  + `stream.router`'s 1 wiring site) append the admission dependency alongside the original auth
  dependency instead of replacing it, to keep a pinned regression test green.
- **Step 3**: `tests/api/test_admission_control.py` created with all 14 named tests. Two tests
  required arithmetic beyond the plan's prose (`test_escalation_is_immediate_on_pressure_signal`,
  `test_recovery_is_gated_by_dwell_and_confidence`) — traced the actual `_evaluate()`/
  `_can_recover()` call-count semantics by hand (recovery requires `dwell_time_ticks + 1` total
  evaluate() calls, not `dwell_time_ticks`, since the dwell-count check runs before that call's own
  increment) and wrote assertions matching the real, verified behavior rather than a guessed call
  count. Two integration tests (`test_per_client_state_is_isolated`,
  `test_survival_mode_sheds_or_rejects_requests`) seed `_ClientAdmissionState` directly with
  `last_active_time=time.time()` (not the dataclass default `0.0`) — the default would make the
  seeded entry look 1970s-old and get pruned by `_prune_idle_clients()` before the test's own
  request ever reached the admission check.
- **Steps 4-8**: all five doc updates plus the one new architecture doc completed, all doc-content
  citations (line numbers in `observability_hot_path_safety_contract.md` §5, `PhaseBudgetGovernor`
  mis-attribution location in the epic doc, `known_limitations.md` §2.2) re-verified against direct
  reads at implementation time and matched the plan exactly. `INFRA-378` appended to
  `docs/parity_ledger/infrastructure.yaml` after reconfirming `INFRA-377` was still the last entry
  (no concurrent write since plan-write time). Two colon-followed-by-space sequences in the new
  YAML entry's `text:` block (plain-scalar-illegal in YAML) were caught by
  `python3 -c "import yaml; yaml.safe_load(...)"` and fixed by substituting `--` for `:` at those
  two points; entry now parses cleanly (383 total entries).
- **Step 9**: intentionally left to Finalize per the dispatch instructions — `## Status` set to
  `INPROGRESS`, ticket not moved, epic folder not touched.
- `make knowledge-index-update` was attempted (docs were created/modified) but fails in this
  environment: `sentence-transformers`'s model load requires a HuggingFace network fetch that this
  sandbox's network policy blocks (`OSError: We couldn't connect to 'https://huggingface.co'`) —
  a pre-existing environment limitation unrelated to this ticket's changes, not something
  fixable from within this Implement pass. Flagging for a later phase/environment with network
  access to actually run the index rebuild.

### Deviation from plan.md's Decision 2 (recorded in full in plan.md's own "Deviations" section)

Running the full `tests/api/` regression suite after wiring all 27 sites per Decision 2's pure
"replace in place" strategy surfaced a real failure:
`tests/api/test_api_key_auth.py::test_only_dashboard_and_websocket_routes_use_weaker_auth_channel`
(a file this ticket must not edit, and which Step 2's own Verify section required to "stay green
unmodified") failed, because that test inspects each route's **top-level** `dependant.dependencies`
for `require_api_key_header_or_query`/`require_api_key_ws` by name — a pure replace moves those
names one level deeper into the new admission dependency's own nested parameter-chain, so they no
longer appear at the top level the pinned test inspects. This is a genuine gap in the plan's own
verification claim that neither round of architecture review caught (it only manifests when the
full existing suite, not just the new test file, is actually executed).

Fix: at exactly the 4 sites using the weaker header-or-query/WebSocket auth channel (3 dashboard
routes + `stream.router`'s 1 site backing 3 WebSocket routes), `dependencies=[...]` now lists
**both** the original auth dependency and the new admission dependency
(`[Depends(require_api_key_header_or_query), Depends(require_admission_header_or_query)]` or the
`_ws` equivalent), rather than replacing. This is behavior-neutral — FastAPI caches a resolved
dependency per request by callable (`dependant.cache_key`, Decision 2's own cited mechanism), so
`require_api_key_header_or_query`/`require_api_key_ws` are still computed exactly once per request
whether referenced once, twice, or transitively. The other 23 plain `require_api_key` sites remain
pure replace, unaffected (they don't trip this particular pinned test). Full re-run of
`tests/api/test_api_key_auth.py` (all 14 tests) confirms green after the fix.

## Test Summary

- `pytest tests/api/test_admission_control.py -v` — **14/14 passed**.
- `pytest tests/api/ -v` — **98 passed, 8 failed**. All 8 failures are the pre-existing,
  documented bare-`python3`-lacks-`pydantic`/no-live-server-listening subprocess environment
  failures (`test_live_entity_inspection`, `test_live_health_api_suite`,
  `test_live_observability_endpoints`, `test_observability_websocket_suite`,
  `test_api_rest_parity`, `test_api_compression`, `test_ws_json_handshake`,
  `test_ws_msgpack_handshake`) — same category the sibling auth ticket already documented; count
  went from 9 (before the Decision-2 deviation fix, which incorrectly also broke
  `test_only_dashboard_and_websocket_routes_use_weaker_auth_channel`) back down to 8 after the fix,
  confirming the fix resolved the only *real* regression. `tests/api/test_api_key_auth.py` (all 14
  tests) reconfirmed green in isolation.
- `pytest tests/unit/observability/test_obs_backpressure.py -v` — **28/28 passed**, fully green,
  zero impact confirmed (this module never imports from or mutates `event_recorder.py`).
- `pytest tests/observability/test_metrics_export.py -v` — **4 passed, 1 failed**
  (`test_metrics_endpoint_integration`, the same pre-existing bare-`python3`-subprocess failure
  documented by the sibling ticket) — matches the expected pre-existing count exactly.
- `pytest tests/docs/test_doc_integrity.py -v` — **10 passed, 1 skipped**, confirming all doc
  edits/additions stay structurally valid.
- `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` —
  parses cleanly, 383 entries.

## Files Changed

- `src/api/admission_control.py` (new)
- `src/api/server.py` (modified — import, `configure_admission_control()` call, 27
  `dependencies=[...]` sites updated: 23 replaced, 4 appended per the recorded deviation)
- `tests/api/test_admission_control.py` (new)
- `docs/architecture/http_admission_control.md` (new)
- `docs/architecture/observability_hot_path_safety_contract.md` (modified — §5 paragraph added)
- `docs/parity_ledger/infrastructure.yaml` (modified — `INFRA-378` appended)
- `docs/plans/http_admission_control_epic.md` (modified — `PhaseBudgetGovernor` mis-attribution
  corrected, "HTTP requests are admitted/throttled/shed per-client" bullet struck through/resolved)
- `docs/engine/known_limitations.md` (modified — one bullet added under §2.2)
- `tickets/todos/http-admission-control/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC.md`
  (Document-Update phase: the epic's own tracking ticket — distinct from
  `docs/plans/http_admission_control_epic.md` above, which the implementer had already updated.
  Checked off the auth AC bullet, reworded the admission-control AC bullet to state
  implementation-complete/mid-pipeline rather than "not investigated," rewrote the Completion
  Summary to reflect the real interim state without claiming premature closure.)
- `docs/plans/architecture_resilience_remediation_roadmap.md` (Document-Update phase: the master
  roadmap's Epic F row/section/sequencing-note all still said "gate on deployment plans" /
  "trusted-network-only" — updated to reflect the 2026-08-23 gate firing, the tier reversion to
  epic, and both child tickets' real current status.)
- `tickets/todos/codebase-health-resilience/TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC.md`
  (Document-Update phase: the grandparent tracking ticket's own Epic F row and narrative still
  said "open... gate on a deployment-plan decision not yet made" — updated with a dated
  2026-08-23 paragraph and the 2 extracted child tickets added to Related Tickets, matching the
  same pattern already used there for Epic J's and K's own extracted children.)
- `tickets/inprogress/TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL.md` (this file — Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)
- `staging_artifacts/TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL/plan.md` (modified — appended
  "Deviations (recorded during Implement)" section documenting the Decision 2 amendment above)

## Completion Summary

Implemented per-client HTTP admission control (`src/api/admission_control.py`) extending
`ObservabilityMode`'s NORMAL/PRESSURE/DEGRADED/SURVIVAL vocabulary to the HTTP layer, keyed by the
`ClientIdentity` the sibling auth ticket established. A per-client in-memory token bucket produces
a `fill_ratio` signal fed into a hysteresis state machine mirroring `ResourceGovernor`'s real
escalation/recovery pattern (immediate escalation, dwell+confidence-gated recovery, one mode level
at a time); only `SURVIVAL` rejects (`429`/`Retry-After` for HTTP, WebSocket close code `1013`).
Per-client state is bounded by a lazy idle-TTL prune plus a max-entries LRU cap. Wired onto all 27
of `server.py`'s protected route sites (23 via in-place replace, 4 via append — a plan deviation
recorded above and in `plan.md`, required to keep a pinned pre-existing regression test green).
All 14 new tests pass; the full `tests/api/` and observability regression surfaces show only the
pre-existing, already-documented environment failures, with zero new regressions. All 6 doc
updates (5 existing files + 1 new ADR) and the new `INFRA-378` parity ledger entry are complete.
Steps 1-8 of the plan are fully implemented; Step 9 (ticket close-out/epic finalization) is
deliberately left for the Finalize phase per this dispatch's own instructions.
