---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261008-SERVICE-LOOKUP-CRASHES-UNDER-THE-CONCURRENT-EXECUTOR-WORKERPACKET-HAS-NO-BUILDING-TILES
phase: done
date: 2026-10-09
tags: [combat]
---

# test_plan: TCK-20261008-SERVICE-LOOKUP-CRASHES-UNDER-THE-CONCURRENT-EXECUTOR-WORKERPACKET-HAS-NO-BUILDING-TILES

See the ticket: frame service_reach.py:30 confirmed on clean main with a real WorkerPacket; shop/blacksmith run on the main thread; the fix is the getattr guard.
