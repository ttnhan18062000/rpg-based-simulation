# Milestone D Test Matrix - Trustworthy Concurrency

## 1. Protocol Structure Tests
| Test Case | Input Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_deterministic_packet_id` | Repeated runs | Packet IDs match exactly for same work items | Identity drift across runs |
| `test_sorted_neighbor_canonicality` | Unordered neighbor sets | `neighbor_view` list is identical and sorted | Context order nondeterminism |
| `test_result_traceability` | Valid execution | `source_packet_id` matches request | Orphan or leaked results |

## 2. Option A (Commit) Law Tests
| Test Case | Input Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_duplicate_result_rejection` | 2 results for same entity | Validation error on second result | Multiplicity leakage |
| `test_commit_ordering_invariance` | N results in different arrival times | Authoritative hash is identical across runs | Thread-race ordering drift |
| `test_priority_inclusive_sort` | Same-entity, different work classes | Sort matches class-priority mapping exactly | Priority inversion |

## 3. Fallback & Failure Tests
| Test Case | Input Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_queue_saturation_fallback` | Packets > Queue Depth | Remaining packets execute locally and sort normally | Saturation hang or ordering gap |
| `test_worker_failure_no_op` | Worker exception | Result status FAILURE; authoritative no-op | State corruption on crash |
| `test_no_retry_on_failure` | Failed worker result | No local retry happens for same entity in scale tick | Duplicate work attempts |

## 4. Authoritative Equivalence Proof
| Test Case | Input Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_local_vs_concurrent_identical` | Seed + Profile | Final state hash is bit-identical (local vs workers=4) | Concurrency semantic drift |
| `test_zero_worker_fallback` | `max_workers=0` | Full transparent fallback; hash identical | Local-mode divergence |
