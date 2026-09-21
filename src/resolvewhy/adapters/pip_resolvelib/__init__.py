"""pip/resolvelib capture and normalization adapter."""

from .adapter import AdapterExecutionError, AdapterResult, PipResolvelibAdapter
from .capture import (
    CaptureBuffer,
    CapturedRun,
    ConflictEvent,
    DependencyEvent,
    MatchEvent,
    PinEvent,
    RecordingProvider,
    RecordingReporter,
    RejectionEvent,
    RequirementEvent,
    RoundEvent,
    SatisfactionEvent,
)
from .normalize import (
    AdapterContext,
    AdapterNormalizationError,
    ArtifactView,
    CandidateView,
    DefaultPipSemantics,
    RequirementView,
    SemanticAccessors,
    normalize_capture,
)

__all__ = [
    "AdapterContext",
    "AdapterExecutionError",
    "AdapterNormalizationError",
    "AdapterResult",
    "ArtifactView",
    "CandidateView",
    "CaptureBuffer",
    "CapturedRun",
    "ConflictEvent",
    "DefaultPipSemantics",
    "DependencyEvent",
    "MatchEvent",
    "PinEvent",
    "PipResolvelibAdapter",
    "RecordingProvider",
    "RecordingReporter",
    "RejectionEvent",
    "RequirementEvent",
    "RequirementView",
    "RoundEvent",
    "SemanticAccessors",
    "SatisfactionEvent",
    "normalize_capture",
]
