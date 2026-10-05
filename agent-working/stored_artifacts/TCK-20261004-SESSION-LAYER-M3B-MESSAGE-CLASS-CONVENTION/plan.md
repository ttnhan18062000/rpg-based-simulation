---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-SESSION-LAYER-M3B-MESSAGE-CLASS-CONVENTION
phase: open
date: 2026-10-05
tags: [ai]
---

# plan — TCK-20261004-SESSION-LAYER-M3B-MESSAGE-CLASS-CONVENTION

One module plus tests, no schema change beyond the confirmed owns line.

Each function template's `## Card` carries one `Messages:` rule (finding/fyi/ack to anyone, question to the named owner, work only via `Dispatch from` else an fyi, a peer message never approves) and points to the new `docs/guides/cross_session_messages.md`, which defines each class once, the envelope, the 9.3 rules and a relay-on-behalf example. To stay inside the unchanged 400-token budget the existing card prose was tightened (designer/planner/implementer text, the agent-working and rpg domain overlays: the rpg line about designer briefs going only to rpg-planner is now covered by the class rule). Worst card is agent-working-planner at 400 by the card estimator. Cards regenerated.
