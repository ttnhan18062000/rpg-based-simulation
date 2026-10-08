---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION
artifact_type: investigation
tags: [architecture, testing, hud]
---

# Investigation — TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION

- With the 89 files in place `pytest tests/visual_assets tests/docs tests/static` failed in 10 places, all guards that counted adopted sources or said "no v2 key has an adoption yet" (each now equality against `adopted_facts`).
- `store_list` for sources returns at most 50 items by default (count = items returned), so the stdio test could not see 70 without `limit`; the test now asks for 200 instead of loosening the count.
- The `icondraft` and `icondraft_v2` fixtures stayed identical (adopted references skip slots a set holds and slots that are not built), as in the key set adoption.
