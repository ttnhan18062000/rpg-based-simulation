---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260528-PHASE9-LIFE-ARCS
artifact_type: investigation
tags: [phase9, life, arcs]
---

# Investigation - Phase 9 Campaigns

We need to analyze the existing simulation engine, specifically how it executes ticks, traces events, and stores entities and their states.

### Core Architecture Findings:
1. The kernel runs ticks deterministically.
2. Traces are stored in a database or logs. Let's see if we can capture event traces for each entity inside our CampaignRunner.
3. For life-arc classification and behavioral analysis, we will record events per entity in standard trace dictionaries.
4. We must define expected schemas for CampaignSpec and CampaignResult, ensuring everything is fully typed.
