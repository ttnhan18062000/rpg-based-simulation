"""Simulation Quality Scoring Calibration Script.

Usage:
    python3 tools/calibrate_simq.py --ticks 100 --seed 42 --name sandbox_world
    python3 tools/calibrate_simq.py --ticks 500 --seed 137 --name urban_political
    python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name dungeon_crawl --profile dungeon_crawl

Runs the engine for N ticks, then replays simulation_events.jsonl through QualityHub.
Writes quality_report.json to data/calibration/{name}_seed{seed}_{ticks}t/.

When --name matches a compiled world under data/worlds/{name}/resolved/world.resolved.yaml,
that WorldSpec is loaded and compiled via WorldCompiler.compile() before the simulation run.
If no resolved spec exists, a generic hero + goblins scenario is used.

After running all 8 canonical scenarios, analyze normalized_score distributions and
update config/simulation_quality/grade_thresholds.yaml accordingly.
"""
from __future__ import annotations
import argparse
import json
import logging
import os
import sys
import time

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("calibrate_simq")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class CalibrationIntegrityError(Exception):
    """Raised when a calibration run lost SimQ events to queue overflow or SURVIVAL
    mode-shed — a run in this state must not silently produce a graded quality_report.json.
    """
    pass


def _resolve_profile(name: str) -> str:
    """Return the profile name to use for the given world name.

    Defaults to ``name`` if a matching profile file exists under
    ``config/simulation_quality/profiles/``, otherwise ``'default'``.
    """
    profile_path = os.path.join(
        "config", "simulation_quality", "profiles", f"{name}.yaml"
    )
    return name if os.path.exists(profile_path) else "default"


def _load_profile_feature_flags(profile: str) -> dict:
    """Read the optional ``feature_flags:`` block from a scoring profile YAML.

    Returns a dict mapping flag name → string value (e.g. ``{"ENABLE_SOCIAL_COOPERATION": "ON"}``).
    Returns an empty dict if the profile file does not exist or has no ``feature_flags:`` key.
    This allows per-scenario calibration profiles to activate feature flags without requiring
    the caller to export env vars manually.
    """
    profile_path = os.path.join(
        "config", "simulation_quality", "profiles", f"{profile}.yaml"
    )
    if not os.path.exists(profile_path):
        return {}
    try:
        import yaml
        with open(profile_path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        return {str(k): str(v) for k, v in (raw.get("feature_flags") or {}).items()}
    except Exception as exc:
        logger.warning("Could not read feature_flags from profile '%s': %s", profile, exc)
        return {}


def _load_profile_campaign_episodes(profile: str) -> int:
    """Read the optional ``campaign_episodes:`` key from a scoring profile YAML.

    Returns 0 (selecting the single-episode ``_run_engine()`` path) if the profile file
    does not exist, has no ``campaign_episodes:`` key, or the value is not a positive
    int. A profile with ``campaign_episodes: N`` (N > 0) selects ``_run_campaign_engine()``
    instead — see main() (TCK-20260824-GRIEF-NEMESIS-REACHABILITY).
    """
    profile_path = os.path.join(
        "config", "simulation_quality", "profiles", f"{profile}.yaml"
    )
    if not os.path.exists(profile_path):
        return 0
    try:
        import yaml
        with open(profile_path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        return int(raw.get("campaign_episodes", 0) or 0)
    except Exception as exc:
        logger.warning("Could not read campaign_episodes from profile '%s': %s", profile, exc)
        return 0


def _load_weights(profile: str = "default"):
    from src.simulation_quality.weights import ScoringWeights
    return ScoringWeights.load(
        weights_path="config/simulation_quality/scoring_weights.yaml",
        grade_path="config/simulation_quality/grade_thresholds.yaml",
        detection_path="config/simulation_quality/detection_params.yaml",
        profile=profile,
    )


def _build_hub(weights, run_dir: str, run_id: str):
    from src.simulation_quality.quality_hub import QualityHub
    from src.simulation_quality.persistence import QualityPersistence
    from src.simulation_quality.scorers.agency import AgencyScorer
    from src.simulation_quality.scorers.combat import CombatScorer
    from src.simulation_quality.scorers.cognition import CognitionScorer
    from src.simulation_quality.scorers.economy import EconomyScorer
    from src.simulation_quality.scorers.faction import FactionScorer
    from src.simulation_quality.scorers.information import InformationScorer
    from src.simulation_quality.scorers.narrative import NarrativeScorer
    from src.simulation_quality.scorers.progression import ProgressionScorer
    from src.simulation_quality.scorers.social import SocialScorer
    from src.simulation_quality.scorers.world_dynamics import WorldDynamicsScorer

    scorers = [
        AgencyScorer(weights),
        CombatScorer(weights),
        CognitionScorer(weights),
        EconomyScorer(weights),
        FactionScorer(weights),
        InformationScorer(weights),
        NarrativeScorer(weights),
        ProgressionScorer(weights),
        SocialScorer(weights),
        WorldDynamicsScorer(weights),
    ]
    persistence = QualityPersistence(run_dir)
    hub = QualityHub(scorers, weights, persistence, run_id=run_id)
    return hub, persistence


def _load_world_state(name: str, seed: int):
    """Load and compile a WorldSpec for the given world name.

    Looks for ``data/worlds/{name}/resolved/world.resolved.yaml``.
    Returns ``(AuthoritativeState, compile_report)`` on success. The literal
    name ``"generic"`` (the CLI's ``--name`` default) intentionally has no
    world directory and returns ``(None, None)`` to use the hero+goblins
    fallback scenario. Any other name that fails to resolve raises
    ``FileNotFoundError`` — a mistyped or nonexistent world name must not
    silently degrade into a meaningless synthetic scenario that still
    produces a "successful" quality report.
    """
    resolved_path = os.path.join("data", "worlds", name, "resolved", "world.resolved.yaml")
    if not os.path.exists(resolved_path):
        if name == "generic":
            logger.info("No world requested ('generic') — using generic hero+goblins simulation")
            return None, None
        raise FileNotFoundError(
            f"World '{name}' not found: {resolved_path} does not exist. "
            "Pass --name generic for the synthetic fallback scenario, or check for a typo in --name."
        )

    try:
        from src.worldbuilding.compiler import WorldCompiler
        from src.worldbuilding.repository import WorldRepository

        # TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION: WorldCompiler.compile() can only
        # correctly resolve entity.identity.role/.faction via a catalog lookup when it has
        # context.legacy_roles/.legacy_faction to consult -- without it, role/faction resolution
        # falls back to naive keyword-matching that fails for almost every real monster
        # archetype role_id (e.g. "predator_hunter"/"raider"/"sentinel"/"scout"/"leader"),
        # silently defaulting to CITIZEN. load_world_with_context() surfaces the real,
        # already-computed compile_context.json alongside world.resolved.yaml.
        repo = WorldRepository(os.path.join("data", "worlds"))
        spec, context = repo.load_world_with_context(name)
        state, report = WorldCompiler.compile(spec, seed, context=context)
        logger.info(
            "Loaded world '%s': %d entities, %d regions, %d resource nodes",
            name,
            report["entity_count"],
            report["region_count"],
            report["resource_node_count"],
        )
        return state, report
    except Exception as exc:
        logger.warning("Failed to load/compile world '%s': %s — falling back to generic simulation", name, exc)
        return None, None


def _run_engine(
    name: str,
    seed: int,
    ticks: int,
    entity_count: int = 10,
    extra_flags: dict | None = None,
    cal_dir: str | None = None,
) -> tuple[str, float, str]:
    """Drive the kernel tick_once() N times; return (run_dir, elapsed_sec, run_id).

    If a compiled world spec exists for ``name``, loads it via WorldCompiler and
    injects the resulting AuthoritativeState into the Kernel.  Falls back to a
    generic hero + goblins scenario when no world is found.

    ``extra_flags`` is an optional dict of flag-name → string-value pairs loaded
    from the calibration profile YAML's ``feature_flags:`` block.  These are applied
    before env-var overrides so that environment variables can still override profile
    defaults.

    ``cal_dir``, when given, is where the RunHealthRecord sidecar
    (``quality_report.run_health.json``) is written — same directory
    ``quality_report.json`` itself lands in (see ``main()``).
    """
    from src.engine.kernel import Kernel
    from src.core.state import AuthoritativeState
    from src.platform.rng import DeterministicRNG
    from src.systems.world_systems.generator import EntityGenerator
    from src.config.profiles import PROD_SMALL

    rng = DeterministicRNG(seed)

    # Attempt to load a compiled world spec
    state, compile_report = _load_world_state(name, seed)

    if state is None:
        # Generic fallback: hero + staggered goblins
        # Goblins are placed in a 5-wide grid starting at (20, 20), well clear of
        # the hero at (64, 64) — avoids LAW-OCCUPANCY-COLLISION.
        gen = EntityGenerator(seed)
        entities = {}
        hero = gen.spawn_hero((64.0, 64.0))
        entities[hero.id] = hero
        for i in range(entity_count - 1):
            gx = 20.0 + (i % 5) * 8.0
            gy = 20.0 + (i // 5) * 8.0
            monster = gen.spawn_goblin((gx, gy))
            entities[monster.id] = monster
        state = AuthoritativeState(tick=0, seed=seed, entities=entities)

    # Inject feature-flag overrides from the calibration profile YAML and environment variables.
    # Recognized flags: see _KNOWN_FLAGS below (kept in sync with FeatureFlagManager's live
    # registry in src/domains/optimization/feature_flags.py).
    # Profile YAML feature_flags are applied first; env vars override profile values.
    # Example: ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py ...
    from src.domains.optimization.feature_flags import FeatureMode
    _KNOWN_FLAGS = [
        "ENABLE_WORLD_CAPABILITY_LAYER", "ENABLE_SELF_MODEL_COGNITION",
        "ENABLE_MEMORY_UPDATE", "ENABLE_ADVENTURE_ROUTING", "ENABLE_COMBAT_ENGAGEMENT",
        "ENABLE_BELIEF_ASSIMILATION", "ENABLE_INFORMATION_INTENT_EXECUTION",
        "ENABLE_PROGRESSION_EVOLUTION", "ENABLE_SOCIAL_COOPERATION", "ENABLE_WORLD_EMERGENCE",
        "ENABLE_LIFE_ARC_CAMPAIGNS", "ENABLE_ENHANCED_TRACE_EVENTS",
        "ENABLE_PUSH_EVENT_SHAPERS", "ENABLE_PUSH_EVENT_SHAPERS_PHASE2",
        "ENABLE_GUILD_QUEST_GENERATION", "ENABLE_PUSH_EVENT_SHAPERS_QUEST",
        "ENABLE_PUSH_EVENT_SHAPERS_AGENCY",
    ]

    def _parse_flag_value(raw: str) -> FeatureMode | None:
        val = raw.strip().upper()
        if val in ("ON", "TRUE", "1", "YES"):
            return FeatureMode.ON
        if val == "STRICT":
            return FeatureMode.STRICT
        if val == "SHADOW":
            return FeatureMode.SHADOW
        return None

    combined_flag_overrides: dict = {}

    # 1. Apply profile-level feature_flags (lower priority)
    for flag, raw_val in (extra_flags or {}).items():
        mode = _parse_flag_value(raw_val)
        if mode is not None:
            combined_flag_overrides[flag] = mode
            logger.info("Feature flag override from profile YAML: %s=%s", flag, mode)

    # 2. Apply env-var overrides (higher priority — can override profile)
    for flag in _KNOWN_FLAGS:
        env_val = os.environ.get(flag, "").strip().upper()
        mode = _parse_flag_value(env_val)
        if mode is not None:
            combined_flag_overrides[flag] = mode
            logger.info("Feature flag override from env: %s=%s", flag, mode)

    # 3. Warn on unrecognized ENABLE_* env vars so a future _KNOWN_FLAGS drift (like
    # TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES) is self-diagnosing
    # instead of silently dropping the override.
    for env_key in os.environ:
        if env_key.startswith("ENABLE_") and env_key not in _KNOWN_FLAGS:
            logger.warning(
                "Env var %s starts with ENABLE_ but is not in _KNOWN_FLAGS — "
                "it will NOT be applied as a feature-flag override.", env_key,
            )

    if combined_flag_overrides:
        existing = dict(getattr(state, "feature_flags", None) or {})
        existing.update(combined_flag_overrides)
        from dataclasses import replace as dc_replace
        state = dc_replace(state, feature_flags=existing)

    # no_frame_pacing disables the kernel's tick-rate sleep (which pads each tick to
    # max_tick_budget_ms for real-time pacing). Calibration runs are offline/batch, not
    # real-time, so this sleep only slows down the run without affecting simulation logic.
    # Same fix as tests/regression/test_behavioral_5k.py (TCK-20260628-E-LONGRUN-REGRESSION).
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=rng, flags={"no_frame_pacing": True})

    run_id = getattr(kernel, "_run_id", None)
    start = time.perf_counter()
    for _ in range(ticks):
        kernel.tick_once()
    elapsed = time.perf_counter() - start

    # Read drop/pressure/SURVIVAL state while the recorder is still alive. This must
    # happen before kernel.shutdown() below (EventRecorder.shutdown() does not clear
    # queue.dropped_count — drain() only empties the queue, the counter itself
    # persists — but the guard's raise, not this read, is what the ordering below
    # protects).
    obs_status = kernel.event_recorder.observability_status()
    dropped_count = kernel.event_recorder.queue.dropped_count
    survival_triggered = any(obs_status["survival_counts"].values())
    guard_passed = (
        dropped_count == 0
        and obs_status["mode"] == "NORMAL"
        and not survival_triggered
    )

    if cal_dir:
        from src.simulation_quality.run_health import RunHealthRecord
        from src.simulation_quality.persistence import QualityPersistence
        QualityPersistence.write_run_health(
            cal_dir,
            RunHealthRecord(
                dropped_count=dropped_count,
                pressure_mode_final=obs_status["mode"],
                survival_triggered=survival_triggered,
                guard_passed=guard_passed,
            ),
        )

    # Shutdown so drain worker flushes remaining JSONL events. Unconditional — runs
    # regardless of guard_passed so background threads (this recorder's own drain
    # worker, plus the kernel's independent DecisionTraceWriter worker) and open
    # file handles are always released, even when the guard below is about to
    # hard-fail this run. (Deviation from the original plan's literal "raise
    # strictly BEFORE this block" — see plan.md Deviations: skipping shutdown
    # entirely on guard failure leaked the DecisionTraceWriter worker thread and
    # tripped tests/conftest.py's session-scoped thread-leak sentinel, a real
    # regression this ticket must not introduce. The protected invariant — the
    # raise must never be nested inside / swallowed by this try/except — holds
    # either way, since the raise below is a separate, non-nested statement.)
    try:
        kernel.shutdown()
    except Exception:
        pass
    time.sleep(0.3)

    # P0 hard-fail — raised in its own statement, never nested inside the
    # try/except above. That block swallows exceptions from kernel.shutdown()
    # itself; if this raise were moved inside it (or merged into its body), the
    # guard's hard-fail would be silently swallowed and do nothing.
    if not guard_passed:
        raise CalibrationIntegrityError(
            f"Calibration run integrity check failed for run_id={run_id}: "
            f"dropped_count={dropped_count}, pressure_mode_final={obs_status['mode']}, "
            f"survival_triggered={survival_triggered}. SimQ scoring for this run is "
            "unreliable (events were lost to queue overflow or SURVIVAL mode-shed) — "
            "see quality_report.run_health.json."
        )

    if run_id and os.path.isdir(os.path.join("data", "runs", run_id)):
        run_dir = os.path.join("data", "runs", run_id)
    else:
        import glob
        dirs = sorted(glob.glob("data/runs/run_*"), key=os.path.getmtime, reverse=True)
        run_dir = dirs[0] if dirs else ""

    return run_dir, elapsed, run_id or ""


def _run_campaign_engine(
    name: str,
    seed: int,
    ticks: int,
    episodes: int,
    entity_count: int = 10,
    extra_flags: dict | None = None,
    cal_dir: str | None = None,
) -> tuple[str, float, str]:
    """Drive CampaignOrchestrator.run_episode() N times; return (run_dir, elapsed_sec, run_id).

    Parallel to _run_engine() (same (run_dir, elapsed, run_id) return contract) but for
    campaign-mode profiles (``campaign_episodes > 0`` in the profile YAML, selected by
    main() via _load_profile_campaign_episodes()). Establishes a real production entry
    point for CampaignOrchestrator.run_episode() — previously reachable only from test
    scaffolding (TCK-20260824-GRIEF-NEMESIS-REACHABILITY).

    Each episode runs its own Kernel (via ScenarioRuntimeService inside
    CampaignOrchestrator) and writes its own ``data/runs/{episode_run_id}/
    simulation_events.jsonl``. After all episodes complete, those per-episode JSONL
    files are appended onto the campaign-level EventRecorder's own JSONL file so that
    main()'s existing _replay_jsonl_through_hub() sees every episode's mid-tick events
    (including grief_urgency_triggered) plus the campaign-level events
    (nemesis_relation_formed, chronicle_entry_created) in one replay pass.

    ``extra_flags`` is accepted for signature parity with _run_engine() but not applied
    here — campaign-mode profiles set feature flags via CampaignOrchestrator's own
    AuthoritativeState construction path, not a single upfront Kernel construction.
    """
    from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
    from src.observability.event_recorder import EventRecorder
    from src.scenarios.schema import SimulationScenarioDefinition

    campaign_run_id = f"campaign_{name}_{int(time.time())}"
    campaign_run_dir = os.path.join("data", "runs", campaign_run_id)

    manifest = CampaignManifest(
        id=name,
        episodes=[
            SimulationScenarioDefinition(
                id=f"{name}_ep{i}",
                world_composition="frontier_living_world",
                perspective="hero_guild_perspective",
                victory_conditions=[{"kind": "tick_limit", "value": ticks}],
            )
            for i in range(episodes)
        ],
        base_seed=seed,
    )

    # campaign_recorder only ever receives scenario/campaign-level bookkeeping events
    # (scenario_objective_*, nemesis_relation_formed, chronicle_entry_created) --
    # TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY. The real per-tick kernel
    # stream (combat, cooperation, hard-law) that SimQ scoring actually needs comes from
    # each episode's own Kernel.event_recorder instead, written to its own
    # data/runs/{episode_run_id}/simulation_events.jsonl and appended below -- confirmed
    # by that ticket's investigation not to be missing from SimQ's replay input.
    campaign_recorder = EventRecorder(run_dir=campaign_run_dir, max_events=5000, enabled=True)
    orchestrator = CampaignOrchestrator(manifest, scenario_event_recorder=campaign_recorder)

    start = time.perf_counter()
    episode_run_ids: list[str] = []
    for _ in range(episodes):
        summary = orchestrator.run_episode()
        if summary.run_id:
            episode_run_ids.append(summary.run_id)
    elapsed = time.perf_counter() - start

    campaign_recorder.shutdown()
    time.sleep(0.3)

    if campaign_recorder.filepath:
        with open(campaign_recorder.filepath, "a", encoding="utf-8") as out_fh:
            for episode_run_id in episode_run_ids:
                episode_jsonl = os.path.join(
                    "data", "runs", episode_run_id, "simulation_events.jsonl"
                )
                if os.path.exists(episode_jsonl):
                    with open(episode_jsonl, encoding="utf-8") as in_fh:
                        out_fh.write(in_fh.read())

    return campaign_run_dir, elapsed, campaign_run_id


def _replay_jsonl_through_hub(run_dir: str, hub) -> int:
    """Read simulation_events.jsonl from run_dir and replay each event through hub."""
    from src.observability.events import ObservabilityEventEnvelope

    jsonl_path = os.path.join(run_dir, "simulation_events.jsonl")
    if not os.path.exists(jsonl_path):
        logger.warning("No simulation_events.jsonl found in %s", run_dir)
        return 0

    event_count = 0
    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # Remove fields not in ObservabilityEventEnvelope
                data.pop("related_entity_ids", None)
                env = ObservabilityEventEnvelope(**data)
                hub.on_envelope(env)
                event_count += 1
            except Exception as exc:
                logger.debug("Skipped JSONL event: %s", exc)
    return event_count


def main():
    parser = argparse.ArgumentParser(description="SimQ calibration runner")
    parser.add_argument("--ticks", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--name", type=str, default="generic")
    parser.add_argument("--entities", type=int, default=10)
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help=(
            "Quality scoring profile name (maps to "
            "config/simulation_quality/profiles/{profile}.yaml). "
            "Defaults to --name if a matching profile exists, else 'default'."
        ),
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Override the calibration output directory (default: data/calibration/{name}_seed{seed}_{ticks}t).",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=None,
        dest="window_size",
        help=(
            "Override detection_params.yaml window_size for this run only. "
            "Does not mutate the YAML. Intended for sweep analysis."
        ),
    )
    parser.add_argument(
        "--loop-threshold",
        type=float,
        default=None,
        dest="loop_threshold",
        help=(
            "Override detection_params.yaml loop_threshold for this run only. "
            "Does not mutate the YAML. Intended for sweep analysis."
        ),
    )
    args = parser.parse_args()

    # Resolve profile: explicit > name-based > default
    if args.profile is not None:
        profile = args.profile
    else:
        profile = _resolve_profile(args.name)

    run_tag = f"{args.name}_seed{args.seed}_{args.ticks}t"
    cal_dir = args.output if args.output else os.path.join("data", "calibration", run_tag)
    os.makedirs(cal_dir, exist_ok=True)

    # Load feature_flags from the resolved profile YAML (e.g. urban_political.yaml)
    profile_feature_flags = _load_profile_feature_flags(profile)
    if profile_feature_flags:
        print(f"[calibrate_simq] Profile feature flags: {profile_feature_flags}")

    print(f"[calibrate_simq] Running engine: {run_tag} entities={args.entities} profile={profile}")
    campaign_episodes = _load_profile_campaign_episodes(profile)
    if campaign_episodes > 0:
        print(f"[calibrate_simq] Campaign-mode profile: {campaign_episodes} episode(s)")
        engine_run_dir, elapsed, run_id = _run_campaign_engine(
            args.name, args.seed, args.ticks, campaign_episodes, args.entities,
            extra_flags=profile_feature_flags, cal_dir=cal_dir,
        )
    else:
        engine_run_dir, elapsed, run_id = _run_engine(
            args.name, args.seed, args.ticks, args.entities,
            extra_flags=profile_feature_flags, cal_dir=cal_dir,
        )
    print(f"[calibrate_simq] Engine done in {elapsed:.2f}s. JSONL at: {engine_run_dir}")

    weights = _load_weights(profile)
    if args.window_size is not None or args.loop_threshold is not None:
        patched_detection = weights.detection.model_copy(update={
            k: v for k, v in {
                "window_size": args.window_size,
                "loop_threshold": args.loop_threshold,
            }.items() if v is not None
        })
        weights = weights.model_copy(update={"detection": patched_detection})
    hub, persistence = _build_hub(weights, cal_dir, run_id or run_tag)

    event_count = _replay_jsonl_through_hub(engine_run_dir, hub)
    print(f"[calibrate_simq] Replayed {event_count} events through QualityHub.")

    report = hub.get_quality_report()
    persistence.write_report(report)
    persistence.shutdown()

    print(f"\n=== Quality Report: {run_tag} ===")
    print(
        f"  ticks={args.ticks} events={event_count} elapsed={elapsed:.2f}s profile={profile}"
        f" window_size={weights.detection.window_size} loop_threshold={weights.detection.loop_threshold}"
    )
    print(f"  overall_grade={report.overall_grade} overall_score={report.overall_score:.4f}")
    print("\n  Pillar breakdown:")
    for pillar_id, snap in sorted(report.pillars.items()):
        print(f"    {pillar_id:20s}  grade={snap.grade}  norm={snap.normalized_score:+.4f}  events={snap.event_count}")
    print(f"\n  Report written: {os.path.join(cal_dir, 'quality_report.json')}")
    return report


if __name__ == "__main__":
    main()
