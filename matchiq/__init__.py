"""MatchIQ web application package."""

from .competitions import COMPETITIONS, DEFAULT_COMPETITION_ID
from .engine import MatchIQEngine, ModelArtifactError

__all__ = [
    "COMPETITIONS",
    "DEFAULT_COMPETITION_ID",
    "MatchIQEngine",
    "ModelArtifactError",
]
