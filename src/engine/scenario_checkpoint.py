# Compliance IDs: INFRA-215
"""ScenarioCheckpointer — checkpoint/restore for ScenarioRuntimeService (E31C)."""
from __future__ import annotations

import json
import pickle
import struct
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.engine.scenario_runtime import ScenarioRuntimeService
    from src.scenarios.schema import SimulationScenarioDefinition


class ScenarioCheckpointer:
    """Save/restore ScenarioRuntimeService state across process restarts.

    File format (binary):
      - 4-byte little-endian uint32: length of JSON header in bytes
      - JSON header bytes (UTF-8): {"tick": N, "spec_id": "...", "rng_checkpoint": ...}
      - Remainder: pickle blob of AuthoritativeState
    """

    @staticmethod
    def save(svc: "ScenarioRuntimeService", path: "str | Path") -> None:
        """Serialise current kernel state to a checkpoint file at *path*.

        Raises RuntimeError if the kernel has not been started.
        """
        if svc._kernel is None:
            raise RuntimeError(
                "Cannot checkpoint: ScenarioRuntimeService has not been started."
            )
        state = svc._kernel.state
        header = {
            "tick": svc.tick,
            "spec_id": svc._spec.id,
            "rng_checkpoint": state.rng_checkpoint,
        }
        header_bytes = json.dumps(header).encode("utf-8")
        payload = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            f.write(struct.pack("<I", len(header_bytes)))
            f.write(header_bytes)
            f.write(payload)

    @staticmethod
    def restore(
        path: "str | Path",
        spec: "SimulationScenarioDefinition",
    ) -> "ScenarioRuntimeService":
        """Restore a ScenarioRuntimeService from a checkpoint file.

        The restored service has its kernel pre-seeded to the checkpoint state.
        Calling .start(tick_limit=N) or .resume(tick_limit=N) continues from
        the checkpoint tick.

        Raises:
            FileNotFoundError: if *path* does not exist.
            ValueError: if the checkpoint spec_id does not match *spec.id*.
        """
        from src.engine.scenario_runtime import ScenarioRuntimeService
        from src.config.profiles import RuntimeProfile, HardwareClass
        from src.platform.rng import DeterministicRNG
        from src.engine.kernel import Kernel

        path = Path(path)
        with path.open("rb") as f:
            header_len = struct.unpack("<I", f.read(4))[0]
            header = json.loads(f.read(header_len).decode("utf-8"))
            state = pickle.loads(f.read())

        if header["spec_id"] != spec.id:
            raise ValueError(
                f"Checkpoint spec_id {header['spec_id']!r} does not match "
                f"supplied spec id {spec.id!r}."
            )

        # Reconstruct RNG from the checkpoint embedded in state.
        # base_seed=0 matches _build_kernel(); the stream is immediately
        # overwritten by set_state() so base_seed is irrelevant post-restore.
        rng = DeterministicRNG(base_seed=0)
        if state.rng_checkpoint is not None:
            rng.set_state(state.rng_checkpoint)

        profile = RuntimeProfile(
            name=spec.id,
            hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=512,
            max_cpu_percent=100.0,
            max_worker_count=0,
            max_queue_depth=1000,
            max_replay_buffer_kb=64,
            max_observability_budget_percent=5.0,
            max_tick_budget_ms=200.0,
        )
        # Pass run_id explicitly to suppress the Domain.INIT RNG draw in
        # Kernel.__init__ that would otherwise advance the stream by 1 after
        # set_state() restores it, breaking the determinism AC.
        kernel = Kernel(
            profile,
            state,
            rng,
            flags={"no_replay": True},
            run_id=f"restored_{spec.id}",
        )

        svc = ScenarioRuntimeService(spec)
        svc._kernel = kernel
        svc._tick = header["tick"]
        return svc
