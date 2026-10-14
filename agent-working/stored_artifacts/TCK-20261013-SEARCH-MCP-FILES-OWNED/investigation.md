---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-SEARCH-MCP-FILES-OWNED
artifact_type: investigation
tags: [ai, governance]
---

# investigation — TCK-20261013-SEARCH-MCP-FILES-OWNED

- `route.py` gives a path to the domain with the longest matching `owns` glob; the five files matched no domain before.
- Of the 20 cards, only `agent-working-planner` crossed 400 with the two globs (407). After the changes: planner 398, the highest of all roles 399.
- Folding same-directory files changes the text of 14 generated cards (every planner card and some others), formatting only: the same paths in a shorter spelling.
- The fold is applied only when the folded string is shorter than the list it replaces.
