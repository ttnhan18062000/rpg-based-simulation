---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260428-RESOURCE-TRANSACTION-GROUPS
artifact_type: plan
tags: [resource, transaction, groups]
---

# Transaction Groups Plan

## Goal
Support atomic "all-or-nothing" resource transfers.

## Approach
1. Add `group_id` to intents.
2. Implement group resolution in pipeline.
3. Add rollback logic.

## Verification
Test rollback on inventory failure.
