from enum import Enum
from dataclasses import dataclass


class QARSLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class QARSConfig:
    """
    Centralized configuration for QARS severity thresholds.
    Threshold bands are configurable and must not be hardcoded in business logic.
    """
    low_max: float = 30.0
    medium_max: float = 60.0
    high_max: float = 80.0
    critical_max: float = 100.0

    def resolve_level(self, score: float) -> QARSLevel:
        """
        Resolves a QARS score (0-100) to a conceptual severity band:
        - 0 <= score <= low_max -> LOW
        - low_max < score <= medium_max -> MEDIUM
        - medium_max < score <= high_max -> HIGH
        - score > high_max -> CRITICAL
        """
        s = round(score, 4)
        if s <= self.low_max:
            return QARSLevel.LOW
        elif s <= self.medium_max:
            return QARSLevel.MEDIUM
        elif s <= self.high_max:
            return QARSLevel.HIGH
        else:
            return QARSLevel.CRITICAL


DEFAULT_QARS_CONFIG = QARSConfig()
