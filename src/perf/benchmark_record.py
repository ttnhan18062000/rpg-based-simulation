# Compliance IDs: PERF-001, PERF-002
"""Typed benchmark record (schema 1.0) and the one comparison that reads it (PERF-M2-T02b).

``docs/performance/benchmark_identity_schema.md`` is the contract. A ``BenchmarkRecord`` says what was measured and where (identity) and
what came out (result). ``compare(base, head, thresholds)`` returns one of ``PASS``, ``REGRESSION``, ``INCONCLUSIVE`` or ``NOT_APPLICABLE``
with a reason, and it never turns incomparable evidence into a pass.

Decisions written in here (``performance_m2_performance_contract_epic.md``, "Delivery plan", step 1):

* OD-1: percentiles are nearest-rank, ``ceil(q * n)`` (``nearest_rank``); ``protocol.percentile_method`` is blocking.
* OD-3: a head-side ``RuntimeMode`` excursion against an all-``NORMAL`` base is a ``REGRESSION`` under the canonical signal contract
  (the sequence does not depend on the host, so the work changed) and ``INCONCLUSIVE`` under the live one.
* OD-4: hardware class is detected (``HardwareClassifier``); a declared class that differs from the detected one is ``INCONCLUSIVE``.
* OD-6: a tripwire record embeds its raw samples, a capacity record carries a ``{uri, sha256}`` pointer to an uncommitted file.

``compare`` reads identity, the protocol, the mode sequence, the hash scheme and one latency number. It reads no other perf-only result
field (throughput, memory, phases, samples, work), so the RPG gate report can reuse it.

An identity field that cannot be filled today holds ``UNKNOWN``. Policy: ``UNKNOWN`` on both sides is comparable and is listed in a
``PASS`` reason as unverified; ``UNKNOWN`` against a known value is a mismatch. The collector never invents a value.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sysconfig
import types
import typing
import uuid
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
)

import psutil

from src.certification.hardware import HardwareClassifier
from src.config.profiles import RuntimeProfile, SignalContract
from src.core.governance import RuntimeMode
from src.engine.work_units import WORK_MODEL_VERSION

SCHEMA_VERSION = "1.1"  # 1.1 added the optional identity.runner section (additive: a MINOR bump, schema section 4)

#: Source of ``result.cost_accounting_version`` (OD-8: a constant here, no engine edit). DEV-017 (#448) changed what a tick's and a phase's
#: reported cost means, so a record without this value, or with another one, is not comparable on tick cost.
COST_ACCOUNTING_VERSION = "DEV-017"

#: Representation of an identity field the collector cannot fill yet (content_hash, builder_version, cpu_model, det_port_tier, ...).
UNKNOWN = "unknown"

#: A tripwire record embeds raw samples up to this many values; above it the record carries a pointer like a capacity record (OD-6).
MAX_EMBEDDED_SAMPLES = 500

#: Where capacity-run and over-cap tripwire samples go (uncommitted). ``PERF_SAMPLES_DIR`` overrides it; the perf tests set it to a temporary directory.
DEFAULT_SAMPLES_SUBDIR = Path("reports") / "perf" / "samples"
SAMPLES_DIR_ENV = "PERF_SAMPLES_DIR"

_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+$")


class BenchmarkRecordError(ValueError):
    """A record, or a dict claiming to be one, violates schema 1.0."""


class GateTier(str, Enum):
    """Which projection of the performance contract a record belongs to (``performance_contract.md`` section 3)."""

    TRIPWIRE = "tripwire"
    CAPACITY_RUN = "capacity_run"
    COMPARATIVE = "comparative"


class PercentileMethod(str, Enum):
    """How percentiles were computed. The contract's method is ``nearest_rank`` (OD-1); the field is blocking."""

    NEAREST_RANK = "nearest_rank"
    LINEAR = "linear"


class Clock(str, Enum):
    """The clock the latency samples came from."""

    PERF_COUNTER = "perf_counter"
    PROCESS_TIME = "process_time"
    INSTRUCTIONS = "instructions"


class HashScheme(str, Enum):
    """Digest schemes of ``validity.final_state_hash``. v2 since DEV-019 (#455); v1 survives in compile reports. Never compared across."""

    FLAT_SHA256_V1 = "flat-sha256-v1"
    FLAT_SHA256_V2 = "flat-sha256-v2"


class OutcomeState(str, Enum):
    """The four outcomes every projection returns (``performance_contract.md`` section 3.3). Only ``PASS`` satisfies a gate."""

    PASS = "PASS"
    REGRESSION = "REGRESSION"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def _coerce(obj: Any, name: str, enum_type: Type[Enum]) -> None:
    """Frozen-dataclass enum coercion: accept the value string, reject anything that is not a member."""
    value = getattr(obj, name)
    if value is None:
        return
    try:
        object.__setattr__(obj, name, enum_type(value))
    except ValueError:
        allowed = ", ".join(m.value for m in enum_type)
        raise BenchmarkRecordError(f"{name} must be one of [{allowed}], got {value!r}") from None


# ── identity ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Scenario:
    """Which scenario was built and by what."""

    id: str
    builder: str = UNKNOWN
    builder_version: str = UNKNOWN
    checkpoint_id: Optional[str] = None


@dataclass(frozen=True)
class Workload:
    """The cardinality of the work: cost scales with it, so it is blocking."""

    entity_count: int
    unit: str = "entities"
    region_count: Optional[int] = None


@dataclass(frozen=True)
class Engine:
    """The engine revision measured. Recorded only: the difference between two revisions is what a comparison measures."""

    commit: str
    dirty_src: bool


@dataclass(frozen=True)
class Content:
    """The content the world was built from. A content change is a workload change."""

    world_id: Optional[str] = None
    content_hash: str = UNKNOWN
    rules_version: str = UNKNOWN


@dataclass(frozen=True)
class Config:
    """The resolved runtime profile and the operational flags."""

    profile_name: str
    profile_hash: str
    flags: Dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class Rng:
    """The seed: a different seed is a different trajectory."""

    seed: int


@dataclass(frozen=True)
class Runtime:
    """The interpreter and host the run executed on."""

    python_version: str
    implementation: str
    build_flavor: str
    os: str
    arch: str
    cpu_model: str
    logical_cores: int
    ram_mb: int
    hardware_class: str
    native_kernels: Dict[str, str] = field(default_factory=dict)
    #: The class the runner or profile claims. ``None`` means no claim. A claim that differs from ``hardware_class`` (detected) is INCONCLUSIVE.
    declared_hardware_class: Optional[str] = None
    det_port_tier: str = UNKNOWN


@dataclass(frozen=True)
class Runner:
    """Who ran it. ``controlled`` is false until the owner names an approved runner (PERF-M2 OD-5), and then no capacity claim is made."""

    controlled: bool = False
    name: str = UNKNOWN


@dataclass(frozen=True)
class Contract:
    """``signal_contract`` replaces the draft's ``determinism``: ``canonical`` is the canonical contract, ``live`` is PERF-D1's live-bounded one."""

    signal_contract: SignalContract
    work_model_version: str
    verification_level: str = UNKNOWN

    def __post_init__(self) -> None:
        _coerce(self, "signal_contract", SignalContract)


@dataclass(frozen=True)
class Executor:
    """How work was dispatched."""

    backend: str
    worker_count: int


@dataclass(frozen=True)
class Observer:
    """Which observers were attached; observer cost is part of the measurement."""

    level: str = UNKNOWN


@dataclass(frozen=True)
class Gate:
    """Which projection produced the record and what it claims."""

    tier: GateTier
    projection: str

    def __post_init__(self) -> None:
        _coerce(self, "tier", GateTier)


@dataclass(frozen=True)
class BaselineRef:
    """The baseline a record was promoted from or compared against (PERF-M2-T05)."""

    id: str
    schema_version: str
    record_digest: str


@dataclass(frozen=True)
class Identity:
    """What was measured and where (schema section 3.1)."""

    scenario: Scenario
    workload: Workload
    engine: Engine
    content: Content
    config: Config
    rng: Rng
    runtime: Runtime
    contract: Contract
    executor: Executor
    observer: Observer
    gate: Gate
    baseline_ref: Optional[BaselineRef] = None
    runner: Runner = field(default_factory=Runner)


# ── result ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Protocol:
    """How the measurement was taken. Every field is blocking: a 20-tick and a 1000-tick sample are not comparable."""

    warmup_ticks: int
    measured_ticks: int
    percentile_method: PercentileMethod
    repetitions: int = 1
    clock: Clock = Clock.PERF_COUNTER
    gc_disabled: bool = True

    def __post_init__(self) -> None:
        _coerce(self, "percentile_method", PercentileMethod)
        _coerce(self, "clock", Clock)


@dataclass(frozen=True)
class Samples:
    """Raw per-tick samples. Either embedded (tripwire) or a pointer to an uncommitted file (capacity run), never both (OD-6).

    ``latency_ms`` of the record is computed from ``tick_compute_ms``; ``tick_wall_ms`` is the wall time around each ``tick_once``.
    """

    tick_wall_ms: Optional[Tuple[float, ...]] = None
    tick_compute_ms: Optional[Tuple[float, ...]] = None
    uri: Optional[str] = None
    sha256: Optional[str] = None

    def __post_init__(self) -> None:
        embedded = self.tick_wall_ms is not None or self.tick_compute_ms is not None
        pointer = self.uri is not None or self.sha256 is not None
        if embedded == pointer:
            raise BenchmarkRecordError("samples must be either embedded (tick_wall_ms, tick_compute_ms) or a pointer (uri, sha256), not both or neither")
        if embedded and (self.tick_wall_ms is None or self.tick_compute_ms is None):
            raise BenchmarkRecordError("embedded samples need both tick_wall_ms and tick_compute_ms")
        if pointer and (not self.uri or not self.sha256):
            raise BenchmarkRecordError("a samples pointer needs both uri and sha256")


@dataclass(frozen=True)
class ModeRun:
    """A run of consecutive ticks in one ``RuntimeMode``."""

    mode: str
    ticks: int


@dataclass(frozen=True)
class Validity:
    """Replay and digest validity of a capacity run."""

    replay_ok: Optional[bool] = None
    final_state_hash: Optional[str] = None
    hash_scheme: Optional[HashScheme] = None

    def __post_init__(self) -> None:
        _coerce(self, "hash_scheme", HashScheme)
        if self.final_state_hash is not None and self.hash_scheme is None:
            raise BenchmarkRecordError("a final_state_hash needs its hash_scheme")


@dataclass(frozen=True)
class Outcome:
    """A state and the reason for it. A reason is required: an outcome without one is a skip that reads as success."""

    state: OutcomeState
    reason: str

    def __post_init__(self) -> None:
        _coerce(self, "state", OutcomeState)
        if not self.reason:
            raise BenchmarkRecordError("an outcome needs a reason")


@dataclass(frozen=True)
class Result:
    """What came out of the run (schema section 3.1)."""

    protocol: Protocol
    latency_ms: Dict[str, float]
    throughput: Dict[str, float]
    time_s: Dict[str, float]
    memory_mb: Dict[str, float]
    runtime_mode_sequence: Tuple[ModeRun, ...]
    outcome: Outcome
    recorded_at: str
    #: ``None`` is a record from before DEV-017 accounting was versioned; ``compare`` returns INCONCLUSIVE for it (R-2).
    cost_accounting_version: Optional[str] = COST_ACCOUNTING_VERSION
    samples: Optional[Samples] = None
    #: Per-tick means of the kernel's metrics under the names the kernel emits. The processed/dropped/coalesced split is not named yet.
    work: Dict[str, float] = field(default_factory=dict)
    validity: Optional[Validity] = None
    phases: Optional[Dict[str, Dict[str, float]]] = None
    scaling_slope: Optional[Dict[str, float]] = None


@dataclass(frozen=True)
class BenchmarkRecord:
    """One versioned benchmark record: identity plus result."""

    identity: Identity
    result: Result
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, str) or not _VERSION_RE.match(self.schema_version):
            raise BenchmarkRecordError(f"schema_version must be MAJOR.MINOR, got {self.schema_version!r}")

    def to_dict(self) -> Dict[str, Any]:
        """The JSON-ready form: enums as their values, tuples as lists."""
        plain: Dict[str, Any] = _to_plain(self)
        return plain

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BenchmarkRecord":
        """Rebuild a record. Unknown keys are ignored (a newer MINOR may add optional fields); a missing required field raises."""
        record: BenchmarkRecord = _from_plain(cls, data)
        return record


# ── serialization ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def _to_plain(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _to_plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (tuple, list)):
        return [_to_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}
    return value


def _dataclass_from_plain(tp: Any, value: Any) -> Any:
    if not isinstance(value, Mapping):
        raise BenchmarkRecordError(f"{tp.__name__} must be an object, got {type(value).__name__}")
    hints = typing.get_type_hints(tp)
    kwargs = {f.name: _from_plain(hints[f.name], value[f.name]) for f in fields(tp) if f.name in value}
    try:
        return tp(**kwargs)
    except TypeError as exc:
        raise BenchmarkRecordError(f"{tp.__name__}: {exc}") from None


def _enum_from_plain(tp: Any, value: Any) -> Any:
    try:
        return tp(value)
    except ValueError:
        raise BenchmarkRecordError(f"{tp.__name__}: invalid value {value!r}") from None


def _leaf_from_plain(tp: Any, value: Any) -> Any:
    if isinstance(tp, type) and is_dataclass(tp):
        return _dataclass_from_plain(tp, value)
    if isinstance(tp, type) and issubclass(tp, Enum):
        return _enum_from_plain(tp, value)
    return value


def _from_plain(tp: Any, value: Any) -> Any:
    origin = typing.get_origin(tp)
    args = typing.get_args(tp)
    if origin is typing.Union or origin is types.UnionType:
        inner = [a for a in args if a is not type(None)]
        return None if value is None else _from_plain(inner[0], value)
    if value is None:
        return None
    if origin is tuple:
        return tuple(_from_plain(args[0], v) for v in value)
    if origin is dict:
        return {k: _from_plain(args[1], v) for k, v in value.items()}
    return _leaf_from_plain(tp, value)


# ── percentiles (OD-1) ────────────────────────────────────────────────────────────────────────────────────────────────────────────


def nearest_rank(sorted_values: Sequence[float], q: float) -> float:
    """Nearest-rank percentile: the ``ceil(q * n)``-th smallest value (1-based). ``sorted_values`` must be sorted ascending and non-empty.

    For 20 samples p95 is the 19th value, not the 20th (the old ``sorted[int(n * q)]`` made p95 the maximum for n <= 20).
    """
    n = len(sorted_values)
    if n == 0:
        raise ValueError("nearest_rank needs at least one value")
    # round() first: 0.07 * 100 is 7.000000000000001 and would otherwise ceil to 8.
    rank = min(n, max(1, math.ceil(round(q * n, 9))))
    return sorted_values[rank - 1]


def compress_modes(modes: Iterable[str]) -> Tuple[ModeRun, ...]:
    """Run-length encode a per-tick mode name sequence."""
    runs: List[ModeRun] = []
    for mode in modes:
        if runs and runs[-1].mode == mode:
            runs[-1] = ModeRun(mode, runs[-1].ticks + 1)
        else:
            runs.append(ModeRun(mode, 1))
    return tuple(runs)


# ── identity collector ────────────────────────────────────────────────────────────────────────────────────────────────────────────


def profile_hash(profile: RuntimeProfile) -> str:
    """sha256 of the resolved profile fields (sorted JSON), so any field that changes behaviour changes the hash."""
    payload = json.dumps(profile.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def git_state(root: Optional[Path] = None) -> Tuple[str, bool]:
    """``(HEAD sha, src has uncommitted changes)``. When git is unavailable: ``(UNKNOWN, True)`` — unknown counts as dirty."""
    root = root or Path(__file__).resolve().parents[2]
    try:
        head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain", "--", "src"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        return head, bool(dirty)
    except (OSError, subprocess.CalledProcessError):
        return UNKNOWN, True


def _cpu_model() -> str:
    try:
        lines = Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines()
    except OSError:
        return platform.processor() or UNKNOWN
    names = [line.split(":", 1)[1].strip() for line in lines if line.lower().startswith("model name") and ":" in line]
    return (names[0] if names else "") or platform.processor() or UNKNOWN


def observer_level(flags: Mapping[str, bool]) -> str:
    """``bare`` when replay and frame pacing are both off (the harness default); otherwise the enabled observers joined by ``+``."""
    enabled = []
    if not flags.get("no_replay", False):
        enabled.append("replay")
    if not flags.get("no_frame_pacing", False):
        enabled.append("frame_pacing")
    return "+".join(enabled) if enabled else "bare"


def collect_runtime(declared_hardware_class: Optional[str] = None) -> Runtime:
    """Read the interpreter and host. ``hardware_class`` is detected (OD-4); ``declared_hardware_class`` is only what the caller claims."""
    build_flavor = "free-threaded" if sysconfig.get_config_var("Py_GIL_DISABLED") else "gil"
    return Runtime(
        python_version=platform.python_version(),
        implementation=platform.python_implementation(),
        build_flavor=build_flavor,
        os=f"{platform.system()} {platform.release()}",
        arch=platform.machine(),
        cpu_model=_cpu_model(),
        logical_cores=psutil.cpu_count(logical=True) or 1,
        ram_mb=int(psutil.virtual_memory().total // (1024 * 1024)),
        hardware_class=HardwareClassifier.detect_class().value,
        declared_hardware_class=declared_hardware_class,
    )


@dataclass(frozen=True)
class RunSubject:
    """What the harness knows about a run before its first tick."""

    scenario_id: str
    entity_count: int
    seed: int
    flags: Mapping[str, bool]
    warmup_ticks: int
    builder: str = UNKNOWN
    region_count: Optional[int] = None
    world_id: Optional[str] = None


@dataclass(frozen=True)
class RecordOptions:
    """Which projection a record is for and where a capacity record's samples go. Defaults are the tripwire."""

    gate_tier: GateTier = GateTier.TRIPWIRE
    gate_projection: str = "bench_harness"
    samples_dir: Optional[Path] = None
    runner: Runner = field(default_factory=Runner)


def collect_identity(profile: RuntimeProfile, subject: RunSubject, options: RecordOptions = RecordOptions(), repo_root: Optional[Path] = None) -> Identity:  # noqa: B008 - frozen
    """Fill every identity field that has a source today; the rest hold ``UNKNOWN`` (see the module docstring)."""
    commit, dirty_src = git_state(repo_root)
    workers = profile.max_worker_count
    return Identity(
        scenario=Scenario(id=subject.scenario_id, builder=subject.builder),
        workload=Workload(entity_count=subject.entity_count, region_count=subject.region_count),
        engine=Engine(commit=commit, dirty_src=dirty_src),
        content=Content(world_id=subject.world_id),
        config=Config(profile_name=profile.name, profile_hash=profile_hash(profile), flags=dict(subject.flags)),
        rng=Rng(seed=subject.seed),
        runtime=collect_runtime(declared_hardware_class=profile.hardware_class.value),
        contract=Contract(signal_contract=profile.signal_contract, work_model_version=WORK_MODEL_VERSION),
        executor=Executor(backend="thread" if workers > 0 else "sequential", worker_count=workers),
        observer=Observer(level=observer_level(subject.flags)),
        gate=Gate(tier=options.gate_tier, projection=options.gate_projection),
        runner=options.runner,
    )


def utc_now() -> str:
    """The current time as RFC 3339 UTC, for ``recorded_at``."""
    return datetime.now(timezone.utc).isoformat()


def default_samples_dir() -> Path:
    """The directory for pointed-to samples: ``$PERF_SAMPLES_DIR`` if set, else ``reports/perf/samples`` under the working directory."""
    override = os.environ.get(SAMPLES_DIR_ENV)
    return Path(override) if override else DEFAULT_SAMPLES_SUBDIR


def write_samples_file(
    directory: Path, stem: str, tick_wall_ms: Sequence[float], tick_compute_ms: Optional[Sequence[float]] = None
) -> Samples:
    """Write raw samples to a new file in ``directory`` (an uncommitted location) and return the ``{uri, sha256}`` pointer (OD-6).

    The file name is ``stem`` plus a random suffix and the file is created exclusively, so two writes in the same second cannot share a file
    and an earlier pointer's ``sha256`` can never go stale. ``tick_compute_ms`` is omitted when the producer has only wall time.
    """
    directory.mkdir(parents=True, exist_ok=True)
    series: Dict[str, List[float]] = {"tick_wall_ms": list(tick_wall_ms)}
    if tick_compute_ms is not None:
        series["tick_compute_ms"] = list(tick_compute_ms)
    payload = json.dumps(series, sort_keys=True).encode("utf-8")
    path = directory / f"{stem}_{uuid.uuid4().hex[:12]}.json"
    with open(path, "xb") as handle:
        handle.write(payload)
    return Samples(uri=str(path), sha256=hashlib.sha256(payload).hexdigest())


def latency_stats(values: Sequence[float]) -> Dict[str, float]:
    """avg, p50, p95, p99, max and min of ``values``; percentiles are nearest-rank (OD-1). Empty input gives zeroes (no ``min``)."""
    if not values:
        return {"avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
    ordered = sorted(values)
    return {
        "avg": round(sum(values) / len(ordered), 3),
        "p50": round(nearest_rank(ordered, 0.5), 3),
        "p95": round(nearest_rank(ordered, 0.95), 3),
        "p99": round(nearest_rank(ordered, 0.99), 3),
        "max": round(ordered[-1], 3),
        "min": round(ordered[0], 3),
    }


# ── comparison (schema section 4) ─────────────────────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Thresholds:
    """Regression limit on ``latency_ms[metric]``: ``max(absolute_ms, base * (1 + relative))`` — the F1 rule ``max(5 ms, x1.25)``."""

    relative: float = 0.25
    absolute_ms: float = 5.0
    metric: str = "avg"

    def limit(self, base_value: float) -> float:
        """The largest head value that is still within threshold for this base value."""
        return max(self.absolute_ms, base_value * (1.0 + self.relative))


def _python_minor(version: str) -> str:
    return ".".join(version.split(".")[:2])


# (dotted path, normalizer). Blocking fields of schema section 4; engine.commit, engine.dirty_src and recorded_at are recorded only.
_BLOCKING: Tuple[Tuple[str, Any], ...] = tuple(
    (path, None)
    for path in (
        "identity.scenario.id",
        "identity.scenario.builder",
        "identity.scenario.builder_version",
        "identity.scenario.checkpoint_id",
        "identity.workload.entity_count",
        "identity.workload.region_count",
        "identity.workload.unit",
        "identity.content.world_id",
        "identity.content.content_hash",
        "identity.content.rules_version",
        "identity.config.profile_name",
        "identity.config.profile_hash",
        "identity.config.flags",
        "identity.rng.seed",
    )
) + (("identity.runtime.python_version", _python_minor),) + tuple(
    (path, None)
    for path in (
        "identity.runtime.implementation",
        "identity.runtime.build_flavor",
        "identity.runtime.os",
        "identity.runtime.arch",
        "identity.runtime.cpu_model",
        "identity.runtime.native_kernels",
        "identity.runtime.logical_cores",
        "identity.runtime.ram_mb",
        "identity.runtime.hardware_class",
        "identity.runtime.det_port_tier",
        "identity.contract.signal_contract",
        "identity.contract.work_model_version",
        "identity.contract.verification_level",
        "identity.executor.backend",
        "identity.executor.worker_count",
        "identity.observer.level",
        "identity.gate.tier",
        "identity.gate.projection",
        "identity.runner.controlled",
        "identity.runner.name",
        "result.protocol.warmup_ticks",
        "result.protocol.measured_ticks",
        "result.protocol.repetitions",
        "result.protocol.percentile_method",
        "result.protocol.clock",
        "result.protocol.gc_disabled",
        "result.cost_accounting_version",
    )
)


def _get(record: BenchmarkRecord, path: str) -> Any:
    value: Any = record
    for part in path.split("."):
        value = getattr(value, part)
    return value.value if isinstance(value, Enum) else value


def _inconclusive(reason: str) -> Outcome:
    return Outcome(OutcomeState.INCONCLUSIVE, reason)


def _major(version: str) -> str:
    return version.split(".", 1)[0]


def _all_normal(sequence: Sequence[ModeRun]) -> bool:
    return bool(sequence) and all(run.mode == RuntimeMode.NORMAL.name for run in sequence)


Check = Callable[[BenchmarkRecord, BenchmarkRecord, Thresholds], Optional[Outcome]]


def _check_schema(base: BenchmarkRecord, head: BenchmarkRecord, _thresholds: Thresholds) -> Optional[Outcome]:
    if _major(base.schema_version) != _major(head.schema_version):
        return _inconclusive(f"schema_version MAJOR differs: base {base.schema_version} vs head {head.schema_version}")
    return None


def _check_each_side(base: BenchmarkRecord, head: BenchmarkRecord, _thresholds: Thresholds) -> Optional[Outcome]:
    for side, record in (("base", base), ("head", head)):
        if not record.result.cost_accounting_version:
            return _inconclusive(
                f"result.cost_accounting_version is missing on {side}: its tick and phase costs predate DEV-017 accounting and are not comparable"
            )
        runtime = record.identity.runtime
        if runtime.declared_hardware_class is not None and runtime.declared_hardware_class != runtime.hardware_class:
            return _inconclusive(
                f"identity.runtime.declared_hardware_class on {side} is {runtime.declared_hardware_class!r} but the detected class is {runtime.hardware_class!r}"
            )
    return None


def _blocking_values(record: BenchmarkRecord, normalize: Any, path: str) -> Any:
    value = _get(record, path)
    return normalize(value) if normalize is not None else value


def _check_blocking_fields(base: BenchmarkRecord, head: BenchmarkRecord, _thresholds: Thresholds) -> Optional[Outcome]:
    differing = []
    for path, normalize in _BLOCKING:
        base_value, head_value = _blocking_values(base, normalize, path), _blocking_values(head, normalize, path)
        if base_value != head_value:
            differing.append(f"{path} ({base_value!r} != {head_value!r})")
    return _inconclusive("blocking field(s) differ: " + "; ".join(differing)) if differing else None


def _scheme(validity: Validity) -> str:
    return validity.hash_scheme.value if validity.hash_scheme is not None else UNKNOWN


def _check_hash_scheme(base: BenchmarkRecord, head: BenchmarkRecord, _thresholds: Thresholds) -> Optional[Outcome]:
    base_validity, head_validity = base.result.validity, head.result.validity
    if base_validity is None or head_validity is None:
        return None
    if base_validity.final_state_hash is None or head_validity.final_state_hash is None:
        return None
    if base_validity.hash_scheme != head_validity.hash_scheme:
        return _inconclusive(
            f"result.validity.hash_scheme differs ({_scheme(base_validity)} vs {_scheme(head_validity)}): digests of different schemes are not comparable"
        )
    return None


def _check_mode_sequences(base: BenchmarkRecord, head: BenchmarkRecord, _thresholds: Thresholds) -> Optional[Outcome]:
    if not _all_normal(base.result.runtime_mode_sequence):
        return _inconclusive("base runtime_mode_sequence is empty or left NORMAL: the baseline does not prove it did the nominal work")
    if not head.result.runtime_mode_sequence:
        return _inconclusive("head runtime_mode_sequence is empty: it cannot prove it stayed NORMAL")
    if _all_normal(head.result.runtime_mode_sequence):
        return None
    excursion = ", ".join(sorted({run.mode for run in head.result.runtime_mode_sequence} - {RuntimeMode.NORMAL.name}))
    if head.identity.contract.signal_contract is SignalContract.CANONICAL:
        return Outcome(
            OutcomeState.REGRESSION,
            f"head left NORMAL ({excursion}) against an all-NORMAL base under the canonical contract: the mode sequence does not depend on the host, so the work changed",
        )
    return _inconclusive(f"head left NORMAL ({excursion}) under the live contract: the excursion may be host-dependent")


def _check_latency(base: BenchmarkRecord, head: BenchmarkRecord, thresholds: Thresholds) -> Optional[Outcome]:
    metric = thresholds.metric
    if metric not in base.result.latency_ms or metric not in head.result.latency_ms:
        return _inconclusive(f"result.latency_ms.{metric} is missing on base or head")
    base_value, head_value = base.result.latency_ms[metric], head.result.latency_ms[metric]
    limit = thresholds.limit(base_value)
    if head_value > limit:
        return Outcome(OutcomeState.REGRESSION, f"head {metric} {head_value:.3f} ms exceeds the limit {limit:.3f} ms (base {base_value:.3f} ms)")
    reason = f"head {metric} {head_value:.3f} ms is within the limit {limit:.3f} ms (base {base_value:.3f} ms)"
    unverified = [path for path, _ in _BLOCKING if _get(base, path) == UNKNOWN]
    if unverified:
        reason += "; unverified identity (unknown on both sides): " + ", ".join(unverified)
    return Outcome(OutcomeState.PASS, reason)


#: In order. The first check that returns an outcome decides; ``_check_latency`` always does, so ``compare`` always returns one.
_CHECKS: Tuple[Check, ...] = (
    _check_schema,
    _check_each_side,
    _check_blocking_fields,
    _check_hash_scheme,
    _check_mode_sequences,
    _check_latency,
)


def compare(base: Optional[BenchmarkRecord], head: Optional[BenchmarkRecord], thresholds: Thresholds = Thresholds()) -> Outcome:  # noqa: B008 - frozen
    """Compare ``head`` against ``base`` under schema section 4. Only ``PASS`` means the two are comparable and within threshold."""
    if base is None:
        return _inconclusive("no baseline record: nothing to compare against")
    if head is None:
        return _inconclusive("no head record")
    for check in _CHECKS:
        outcome = check(base, head, thresholds)
        if outcome is not None:
            return outcome
    return _inconclusive("no check decided")  # unreachable: _check_latency always returns
