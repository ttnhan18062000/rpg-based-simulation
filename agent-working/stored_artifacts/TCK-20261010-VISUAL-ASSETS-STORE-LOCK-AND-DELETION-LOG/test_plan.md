---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-STORE-LOCK-AND-DELETION-LOG
artifact_type: test_plan
tags: [architecture, security, testing]
---

# Test plan

## Proof Plan (as run)
| Claim | Test (tests/visual_assets/store/unit/) | Mutant that must fail it |
|---|---|---|
| second writer refused at once, names holder, no wait | test_lock.py::test_a_second_writer_is_refused_at_once_naming_the_holder (alarm guard) | drop LOCK_NB (fails by timeout guard) |
| kernel frees the lock on SIGKILL | test_lock.py::test_the_kernel_releases_the_lock_when_the_holder_is_killed | n/a (kernel property) |
| symlinked / non-regular lock refused | test_lock.py symlink + directory tests | drop O_NOFOLLOW |
| non-Linux refused at acquire, import works anywhere | test_lock.py::test_non_linux_is_refused_at_acquire_time_not_at_import | force the platform check False |
| every CLI command classified; writing set takes the lock; exports too | test_lock.py classification + which-invocations + really-holds tests | remove `export-runtime` from WRITING; make `gc --delete` unlocked |
| MCP submit takes the lock | test_lock.py::test_the_mcp_submit_takes_the_lock | remove the `with` |
| record per removal, chained, canonical, hash of removed content | test_deletion_log.py | n/a |
| record BEFORE removal; kill between = note, not break | test_deletion_log.py ordering + interrupted tests | append after removal |
| full log refuses before deleting anything; archive+continue passes; wrong anchor / missing archive = BREAK | test_deletion_log.py budget + archive tests | drop `require_room`; ignore archives in `last_hash`; skip prev_hash check |
| tampered/removed/reordered/forged-path/garbage/torn/oversize log = BREAK | test_deletion_log.py | skip prev_hash check |
| gc never lists lock/log/archive | test_deletion_log.py::test_gc_never_lists_the_lock_the_log_or_an_archive | n/a |
| SIGKILL at 5 adoption points + 3 export points: store readable, audit names orphans, re-run refuses cleanly, documented recovery works | test_kill_mid_publish.py (real subprocess) | drop the empty-source-directory check |

All 11 mutants applied with a single-match assertion and failed the named test (2026-10-10).

## Regression
tests/visual_assets (boundaries, budgets parity, store unit, no_ignored_files), tests/unit/tools and tests/tools before the PR.
