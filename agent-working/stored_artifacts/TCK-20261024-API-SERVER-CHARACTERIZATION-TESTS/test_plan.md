---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261024-API-SERVER-CHARACTERIZATION-TESTS
artifact_type: test_plan
tags: [architecture, api-design, testing]
---

# Test plan
Passing on origin/main with `src/` untouched (`git diff origin/main -- src/` empty). Two fresh processes write byte-identical fixtures (`cmp`). `tests/api` plus `tests/architecture/test_api_read_model_guard.py`: 173 passed.

Probes (src edited, test run, src reverted each time; every probe fails the snapshot test):
1. rename `get_metrics` endpoint: fails in `default_profile` and `optional_routers_on`;
2. swap the `history` and `search` `include_router` blocks: fails in both route sections;
3. one byte of the UI HTML (`</html>` to `</htm1>`): fails in `responses` (sha256);
4. drop `dependencies=` on the `search` router: fails in both route sections;
5. GZip `minimum_size` 512 to 513: fails in the middleware section.
