---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261014-SWAPS-AND-YIELDS-PAY-TERRAIN-STEP-TIME-D75-COMPLETION
date: 2026-10-14
tags: []
---

# Investigation: TCK-20261014-SWAPS-AND-YIELDS-PAY-TERRAIN-STEP-TIME-D75-COMPLETION

The D75 attribution counted 921 untimed steps and 26 steps taken while held over five frontier seeds: position swaps and yield displacements wrote a new position without setting or checking step_ready_tick. After the fix 0 steps break the hold; 78 ordinary move steps remain untimed (writer not identified).
