"""
Phase 8 — Advanced Simulation Understanding package.

Provides post-run simulation interpretation through seven subsystems:
- understanding.context: AnalysisContext (shared pipeline input)
- understanding.domain: DomainAnalyzerRegistry + per-domain analyzers (M42)
- understanding.expectations: ScenarioExpectationPack + loader (M43)
- understanding.rootcause: RootCauseEngine + hypothesis rules (M44)
- understanding.balance: BalanceDiagnosisEngine (M45)
- understanding.stories: StoryDetector + emergent story patterns (M46)
- understanding.review: FindingReview + ReviewStore (M47)
- understanding.quality: AnalyzerQualityReporter + BaselineEvolutionPolicy (M48)
- understanding.pipeline: UnderstandingPipeline (orchestrator)

Typical usage:
    from src.observability.understanding.pipeline import UnderstandingPipeline
    report = UnderstandingPipeline().run(run_dir="data/runs/run-001", scenario_type="resource_economy")
"""
from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.pipeline import UnderstandingPipeline, UnderstandingReport

__all__ = ["AnalysisContext", "UnderstandingPipeline", "UnderstandingReport"]
