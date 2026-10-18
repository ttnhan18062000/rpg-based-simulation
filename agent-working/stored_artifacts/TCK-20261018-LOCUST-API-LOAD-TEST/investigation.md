---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-LOCUST-API-LOAD-TEST
artifact_type: investigation
tags: [platform, observability]
---

# Investigation: TCK-20261018-LOCUST-API-LOAD-TEST

**Written retrospectively at ticket close (2026-10-18).** The plan was given in platform-planner's dispatch messages and the ticket Scope; this file records it after the fact.

## Findings (recorded in the ticket's Implementation Notes and Test Summary)
- The env var for the key hashes is `RPG_API_KEY_HASHES` (ConfigLoader prefix `RPG_` + field `api_key_hashes`).
- `uv lock` moved `requests` 2.32.3 -> 2.34.2, forced by Locust; `requests` is a runtime dependency, so this is a runtime bump. The lock also has two `cffi` entries split by platform marker (2.0.0 for Linux, 2.1.1 for win32); lead decides.
- Smoke-run findings 1-7 are in the ticket: `parse_failures_csv` missed 429s because Locust writes `CatchResponseError('admission_429')`; a per-user key still measured the per-key bucket, hence round-robin keys; the manifest crashed on a `Path`; the old `backend_cpu` and `swap` saturation rules were unsound; `engine_state` was empty because the status key's bucket was drained; a root-owned `data/runs` dir appeared after compose.
- Open item 6b (9 pool 429s at 5 users, round-robin run) was resolved during the measured run: no 429s in any step of any run; see `docs/runbooks/records/2026-10-18-api-load-test.md` section 9.
