# Transaction Groups Plan

## Goal
Support atomic "all-or-nothing" resource transfers.

## Approach
1. Add `group_id` to intents.
2. Implement group resolution in pipeline.
3. Add rollback logic.

## Verification
Test rollback on inventory failure.
