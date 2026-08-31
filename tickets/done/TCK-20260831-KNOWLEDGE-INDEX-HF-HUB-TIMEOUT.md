---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260831-KNOWLEDGE-INDEX-HF-HUB-TIMEOUT
phase: done
date: 2026-08-31
tags: [mcp, setup]
---

# TCK-20260831-KNOWLEDGE-INDEX-HF-HUB-TIMEOUT

## Title
`make knowledge-index`/`make knowledge-index-update` fail their first-ever model download in this
sandbox with `OSError: We couldn't connect to 'https://huggingface.co'` — not actually network-blocked,
just a too-short default request timeout for this network's latency

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary

`TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX` fixed the python3-discovery bug in both targets, but its
own live-verification run hit `OSError: We couldn't connect to 'https://huggingface.co'` on the
first-ever model download and filed that as "network-blocked in this sandbox" — acceptable, out-of-scope
evidence at the time, not investigated further.

That assumption was wrong. Direct investigation today confirmed: `curl` reaches `huggingface.co` and
downloads real files successfully; the connection just runs through a corporate TLS-inspecting proxy at
~375KB/s with 1-3.5s round-trip latency per request even for tiny payloads. `huggingface_hub`'s default
per-request timeout (`HF_HUB_ETAG_TIMEOUT`/`DEFAULT_REQUEST_TIMEOUT`, both 10s) is thin against that
latency profile, especially across the ~10 separate file/ETag checks a cold `all-MiniLM-L6-v2` download
needs — plausible enough to explain repeated give-ups that surface as the generic "couldn't connect...
check your internet connection" `OSError`. `hf_transfer` (the Rust accelerated-download extension
sometimes implicated in corporate-proxy hangs) is confirmed **not installed** in this environment, ruling
that out as a cause.

Live-reproduced the fix directly: with no code change, just patience (backgrounding the download with no
artificial external timeout), the full model (~91MB across ~10 files) downloaded successfully in 465s
at this connection's real, if slow, throughput. `make knowledge-index` (full build) then completed
cleanly: 8,452 documents embedded, and `mcp__knowledge-search__search_docs` now returns real ranked
results — confirmed live, not just "the build didn't error."

## Scope

- `Makefile:333` (`knowledge-index` target) and `Makefile:338` (`knowledge-index-update` target): add
  `HF_HUB_ETAG_TIMEOUT=120` alongside the existing `SSL_CERT_FILE`/`SSL_CERT_DIR` exports, so a *future*
  fresh environment on this same slow/proxied network gets a generous-enough per-request timeout to
  survive its own first cold download without needing a human to notice and manually retry with
  patience, the way this ticket's investigation did.
- Document the real root cause (thin default timeout vs. proxy latency, not a hard block) so a future
  session doesn't re-file this as "network-blocked" and give up the way the prior ticket's own
  live-verification note did.

## Out of Scope

- Any change to `tools/knowledge_search.py`'s embedding/build logic itself — the fix is purely a
  timeout-budget env var on the Makefile invocation, matching the shape of the prior
  `TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX` fix (Makefile-only, script untouched).
- Re-running the full model download in CI or committing the downloaded model/index to the repo —
  `knowledge-index/` and the HF hub cache are both explicitly local-only/gitignored by design
  (`knowledge-index: developer env only — not CI`); this ticket doesn't change that boundary.
- Installing or enabling `hf_transfer` — confirmed not the cause here, not worth adding a new dependency
  to chase a red herring.
- Any fix to `eval-search` (Makefile) even though it likely shares the same thin-timeout exposure —
  same reasoning the prior ticket used to exclude it: not named in this request's scope, a known,
  separately fixable instance of the same class.

## Acceptance Criteria

- [x] `Makefile:333` and `Makefile:338` both export `HF_HUB_ETAG_TIMEOUT=120` alongside the existing
  `SSL_CERT_FILE`/`SSL_CERT_DIR` exports.
- [x] `mcp__knowledge-search__search_docs` returns real ranked results (not `{"error": "index not
  found"}`) — confirmed live, not just inferred from a clean build exit code.
- [x] The corrected root-cause finding (thin timeout vs. genuine block) is recorded here and
  cross-referenced from `TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX`'s own record, so its "network-blocked
  in this sandbox" note isn't left standing uncorrected for the next reader.

## Related Tickets

- `TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX` (done) — fixed the python3-discovery bug in the same two
  Makefile targets; its own live-verification note is the one this ticket corrects (see Request
  Summary). Not a conflict — a direct, intentional follow-up.

## Related Docs

- `docs/guidelines/agent_working_environment.md` — documents `make knowledge-index`/
  `make knowledge-index-update` usage; no content change needed, its guidance becomes reliable on first
  cold run in this kind of network once this fix lands, same as the prior ticket's note.

## Related Stored Artifacts

None — hotfix tier, no staging artifacts required.

## Related Code Areas

- `Makefile` (lines 331-340, the two `knowledge-index*` targets)
- `tools/knowledge_search.py` (invoked by both targets, read-only reference — not modified)
- `tests/tools/test_dashboard_makefile_targets.py` (existing pinned-recipe-snapshot pattern, extended
  here the same way the prior ticket extended it)

## Assumptions / Open Questions

- `HF_HUB_ETAG_TIMEOUT=120` (not `HF_HUB_DOWNLOAD_TIMEOUT`) was chosen as the specific env var to set:
  confirmed via `huggingface_hub.constants` that `HF_HUB_ETAG_TIMEOUT` backs both
  `DEFAULT_ETAG_TIMEOUT`/`DEFAULT_REQUEST_TIMEOUT` (both currently 10s) in the installed version — the
  metadata/ETag preflight check done per-file is the specific step most exposed to this proxy's
  per-request latency, not the bulk chunked-transfer step itself (which already has its own
  longer-lived streaming behavior).
- 120s is a judgment call, not derived from a measured worst-case — chosen as comfortably above the
  observed 1-3.5s single-request round trip with headroom for load spikes, without being so long a
  genuinely dead connection would hang a build indefinitely. Not validated against a slower or
  faster network than this session observed.
- The model is now warm-cached in this specific sandbox's `~/.cache/huggingface/` (local, gitignored,
  not portable to a different machine/container) — this fix specifically targets a *future fresh*
  environment's first cold download, not this session's already-resolved one.

## Implementation Notes

Added `HF_HUB_ETAG_TIMEOUT=120` to the existing `SSL_CERT_FILE=... SSL_CERT_DIR=...` export line in
both `knowledge-index` (Makefile:333) and `knowledge-index-update` (Makefile:338) — pure env-var
addition, no other line in either recipe changed, matching the "purely mechanical, one cause, one fix"
shape the prior ticket in this same pair of targets established.

Added `test_knowledge_index_targets_set_hf_hub_etag_timeout` to
`tests/tools/test_dashboard_makefile_targets.py`, following that file's existing `_makefile_text`/
`_extract_recipe` helper pattern (the same one `TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX` used): asserts
both targets' recipes contain `HF_HUB_ETAG_TIMEOUT=120` alongside the existing `SSL_CERT_FILE` check.

## Test Summary

Ran `tests/tools/test_dashboard_makefile_targets.py` with
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest`: all pass, including the new
pinned-recipe guard and the pre-existing `test_existing_targets_unmodified` (confirms no other pinned
target's recipe was touched) and `test_knowledge_index_targets_use_python3_variable` (confirms this
ticket didn't regress the prior ticket's fix).

Live-verified end to end from this worktree:
- `make -n knowledge-index-update` (dry-run) prints `HF_HUB_ETAG_TIMEOUT=120` in the resolved recipe.
- Cold model download (`sentence-transformers/all-MiniLM-L6-v2`, ~91MB across ~10 files) completed
  successfully in 465s at this connection's real throughput (~375KB/s) — no code change was needed to
  make the *download itself* succeed once given enough wall-clock time; this ticket's Makefile change
  ensures a future session's `huggingface_hub` client doesn't give up on its own default 10s timeout
  before that time elapses.
- `make knowledge-index` (full build) completed: "Corpus: 1616 ticket summaries, 1085 investigation
  files, 1600 working log rows, 4151 docs chunks" → "8452 documents embedded → knowledge-index/knowledge.db".
- `mcp__knowledge-search__search_docs` called live with a real query returned real ranked results
  (semantic + keyword scores, real excerpts) — not the `{"error": "index not found"}` this session
  started with.

## Files Changed

- `Makefile` — `knowledge-index` and `knowledge-index-update` targets now also export
  `HF_HUB_ETAG_TIMEOUT=120`
- `tests/tools/test_dashboard_makefile_targets.py` — added
  `test_knowledge_index_targets_set_hf_hub_etag_timeout`

## Completion Summary

Root-caused `search_docs`' non-functional state to a too-short default `huggingface_hub` request
timeout (10s) against this sandbox's slow, high-latency corporate-proxied connection to
huggingface.co — not a hard network block, correcting the assumption `TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX`'s
own live-verification note left standing. Confirmed `hf_transfer` is not installed, ruling out that
common alternate cause. Added `HF_HUB_ETAG_TIMEOUT=120` to both `knowledge-index` Makefile targets so a
future fresh environment on this same network survives its own first cold download automatically. Live
end-to-end verified: model downloaded and cached, full index built (8,452 documents), and
`search_docs` now returns real results.
