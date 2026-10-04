---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Session domain: agent-working

Source of the agent-working part of a role card. Ownership and routes come from `registries/session_roles.yaml`
and are not restated here. Only `## Card` is injected.

## Card
Domain: agent-working (process, tooling, monitoring, delivery). Other domains report process problems here (symptom, evidence, impact); it decides whether to ticket them. It owns the tooling around `registries/mechanisms.yaml`, not its content. The implementer polls CI; the designer reviews.
