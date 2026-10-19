---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START
artifact_type: plan
tags: [hooks, process-improvement]
---

# plan — TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START

1. Add the session-code paths and a merge-base diff to `settings_freshness.py`. 2. Wire one warning line into the hook for startup, resume and clear, failing open and saying so. 3. Update the guide sentence that said freshness is checked only at launch. Rejected: content compare against the ref (false positives for session-code authors); running the hook from the main checkout (weaker, as the ticket notes).
