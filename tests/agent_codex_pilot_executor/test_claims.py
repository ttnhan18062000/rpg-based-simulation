from __future__ import annotations

from pathlib import Path
from multiprocessing import Barrier, Event, Process, Queue
import time

import pytest


TICKET_ID = "TCK-20260731-CODEX-PILOT-EXECUTOR"
EXECUTION_ID = "codex-TCK-20260731-CODEX-PILOT-EXECUTOR-1722470400000-deadbeef"


def _race_claim(root: str, barrier: Barrier, results: Queue):
    from tools.agent_codex_pilot_executor.claims import ClaimRefusedError, acquire_claim

    barrier.wait()
    try:
        acquire_claim(Path(root), TICKET_ID, EXECUTION_ID)
        results.put("acquired")
    except ClaimRefusedError:
        results.put("refused")


def _hold_transition_lock(root: str, entered: Event, release: Event):
    from tools.agent_codex_pilot_executor.claims import _transition_lock
    from tools.agent_codex_pilot_executor.paths import resolve_scratch_paths

    paths = resolve_scratch_paths(
        scratch_root=Path(root), ticket_id=TICKET_ID, execution_id=EXECUTION_ID
    )
    with _transition_lock(paths.lock_path):
        entered.set()
        release.wait(timeout=10)


def _replace_terminal(root: str, execution_id: str, barrier: Barrier, results: Queue):
    from tools.agent_codex_pilot_executor.claims import ClaimRefusedError, acquire_claim

    barrier.wait()
    try:
        results.put(acquire_claim(Path(root), TICKET_ID, execution_id).execution_id)
    except ClaimRefusedError:
        results.put("refused")


def test_active_claim_refuses_second_owner_and_terminal_marker_can_be_replaced(tmp_path: Path):
    from tools.agent_codex_pilot_executor.claims import (
        ClaimRefusedError,
        acquire_claim,
        terminalize_claim,
    )

    claim = acquire_claim(tmp_path, TICKET_ID, EXECUTION_ID)
    with pytest.raises(ClaimRefusedError):
        acquire_claim(tmp_path, TICKET_ID, EXECUTION_ID)

    terminalize_claim(tmp_path, TICKET_ID, EXECUTION_ID, "completed")
    replacement = acquire_claim(tmp_path, TICKET_ID, EXECUTION_ID)
    assert replacement.state == "active"


def test_multiprocess_same_ticket_race_has_exactly_one_active_owner(tmp_path: Path):
    barrier = Barrier(2)
    results: Queue = Queue()
    processes = [Process(target=_race_claim, args=(str(tmp_path), barrier, results)) for _ in range(2)]
    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=10)
        assert process.exitcode == 0
    outcomes = sorted(results.get(timeout=2) for _ in processes)
    assert outcomes == ["acquired", "refused"]


def test_multiprocess_terminal_marker_replacement_has_exactly_one_new_owner(tmp_path: Path):
    from tools.agent_codex_pilot_executor.claims import acquire_claim, terminalize_claim

    acquire_claim(tmp_path, TICKET_ID, EXECUTION_ID)
    terminalize_claim(tmp_path, TICKET_ID, EXECUTION_ID, "completed")
    barrier, results = Barrier(2), Queue()
    ids = [
        "codex-TCK-20260731-CODEX-PILOT-EXECUTOR-1722470400001-deadbeef",
        "codex-TCK-20260731-CODEX-PILOT-EXECUTOR-1722470400002-deadbeef",
    ]
    workers = [Process(target=_replace_terminal, args=(str(tmp_path), value, barrier, results)) for value in ids]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=10)
        assert worker.exitcode == 0
    outcomes = [results.get(timeout=2) for _ in workers]
    assert sorted(outcomes).count("refused") == 1
    assert next(value for value in outcomes if value != "refused") in ids


def test_contender_cannot_enter_while_another_process_holds_transition_lock(tmp_path: Path):
    from tools.agent_codex_pilot_executor.claims import acquire_claim

    entered, release, results = Event(), Event(), Queue()
    holder = Process(target=_hold_transition_lock, args=(str(tmp_path), entered, release))
    holder.start()
    assert entered.wait(timeout=5)
    contender = Process(target=_race_claim, args=(str(tmp_path), Barrier(1), results))
    contender.start()
    # Exceed the former O_EXCL stale-lock threshold (5s): an advisory flock
    # must still prevent a contender from entering while its live owner holds
    # the descriptor, rather than relying on age-based lock-file reclamation.
    time.sleep(5.2)
    assert results.empty()
    release.set()
    holder.join(timeout=10)
    contender.join(timeout=10)
    assert holder.exitcode == contender.exitcode == 0
    assert results.get(timeout=2) == "acquired"


def test_terminalization_refuses_wrong_execution_owner_and_malformed_active_marker(tmp_path: Path):
    from tools.agent_codex_pilot_executor.claims import ClaimRefusedError, acquire_claim, terminalize_claim

    acquire_claim(tmp_path, TICKET_ID, EXECUTION_ID)
    wrong = "codex-TCK-20260731-CODEX-PILOT-EXECUTOR-1722470400001-deadbeef"
    with pytest.raises(ClaimRefusedError, match="ownership"):
        terminalize_claim(tmp_path, TICKET_ID, wrong, "failed")
    claim = tmp_path / "claims" / f"{TICKET_ID}.json"
    claim.write_text("not-json", encoding="utf-8")
    with pytest.raises(ClaimRefusedError, match="malformed"):
        terminalize_claim(tmp_path, TICKET_ID, EXECUTION_ID, "failed")
