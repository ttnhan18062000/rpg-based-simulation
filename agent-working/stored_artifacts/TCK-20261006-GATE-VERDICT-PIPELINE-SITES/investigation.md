---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-PIPELINE-SITES
artifact_type: investigation
tags: [ai, agent-monitoring]
---

# Investigation
Gate rows ride the same fail-open monitoring step as the events (the monitoring agent prompt), so no new permission or process, and a failure cannot change `final_status`. Buffering instead of writing per gate costs no extra agent on the native runtime (`sh` there is an agent call). A static gate behind `shAttested` is already recorded by `attest_gate.py` under the attestation's own gate name (`tag_check`, `doc_staleness`, ...), so recording it again from the script on the native runtime would double-count; it is recorded from the script on the legacy runtime only. Those two id spellings differ; unifying them is not done here.
