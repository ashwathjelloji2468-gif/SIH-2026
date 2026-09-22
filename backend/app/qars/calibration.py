import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field


class QARSCalibrationRecord(BaseModel):
    """
    Schema for a versioned QARS algorithm calibration record.
    All numeric calibration factors must belong to [0, 1].
    """
    canonical_algorithm: str
    parameter: Optional[Union[str, int]] = None
    attack_family: str = "UNKNOWN"
    vulnerability_factor: Optional[float] = Field(None, description="Va in [0, 1]")
    security_strength_factor: Optional[float] = Field(None, description="Sp in [0, 1]")
    calibration_status: str = "UNCONFIGURED"
    confidence: str = "INSUFFICIENT_EVIDENCE"
    calibration_version: str = "SENTRIQ QARS Prototype Heuristic Calibration v1"
    source: str = "SENTRIQ_PROTOTYPE_HEURISTIC"
    methodology: str = ""
    notes: Optional[str] = None

    def validate_factors(self) -> None:
        """Validates that Va and Sp, if present, lie in [0, 1]."""
        if self.vulnerability_factor is not None:
            va = float(self.vulnerability_factor)
            if va < 0.0 or va > 1.0:
                raise ValueError(
                    f"Invalid vulnerability_factor (Va={va}) for algorithm '{self.canonical_algorithm}'. Must be in [0, 1]."
                )
        if self.security_strength_factor is not None:
            sp = float(self.security_strength_factor)
            if sp < 0.0 or sp > 1.0:
                raise ValueError(
                    f"Invalid security_strength_factor (Sp={sp}) for algorithm '{self.canonical_algorithm}'. Must be in [0, 1]."
                )


class QARSCalibrationDataset(BaseModel):
    """
    Top-level model for calibration dataset JSON structure.
    """
    version: str
    description: str
    profiles: List[QARSCalibrationRecord]


def get_default_calibration_file_path() -> Path:
    """Returns absolute path to qars_algorithm_calibration.json dataset."""
    return Path(__file__).parent.parent / "knowledge" / "data" / "qars_algorithm_calibration.json"


class QARSCalibrationProvider:
    """
    Versioned Production Calibration Data Provider for QARS Phase 2.
    Loads and validates prototype heuristic calibration data from JSON.
    Resolves algorithm/key-size profiles with priority:
    1. Exact algorithm + parameter
    2. Canonical algorithm (parameter=None)
    3. UNCONFIGURED (confidence = INSUFFICIENT_EVIDENCE)
    """
    def __init__(
        self,
        json_path: Optional[Union[str, Path]] = None,
        data_override: Optional[Dict[str, Any]] = None
    ):
        self.version = "SENTRIQ QARS Prototype Heuristic Calibration v1"
        self.records: List[QARSCalibrationRecord] = []
        self._exact_map: Dict[str, QARSCalibrationRecord] = {}
        self._canonical_map: Dict[str, QARSCalibrationRecord] = {}

        if data_override is not None:
            self._load_from_dict(data_override)
        else:
            target_path = Path(json_path) if json_path else get_default_calibration_file_path()
            self._load_from_file(target_path)

    def _load_from_file(self, path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(f"QARS Calibration dataset file not found at: {path}")
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        self._load_from_dict(raw_data)

    def _load_from_dict(self, raw_data: Dict[str, Any]) -> None:
        dataset = QARSCalibrationDataset(**raw_data)
        self.version = dataset.version
        for record in dataset.profiles:
            record.validate_factors()
            self.records.append(record)

            alg = record.canonical_algorithm.upper().strip()
            param = str(record.parameter).upper().strip() if record.parameter is not None else None

            if param is not None:
                key = f"{alg}:{param}"
                self._exact_map[key] = record
            else:
                self._canonical_map[alg] = record

    def resolve_calibration(
        self,
        canonical_algorithm: str,
        parameter: Optional[Union[int, str]] = None
    ) -> QARSCalibrationRecord:
        if not canonical_algorithm or not str(canonical_algorithm).strip() or str(canonical_algorithm).strip().upper() in ["UNKNOWN", "NONE"]:
            return QARSCalibrationRecord(
                canonical_algorithm="UNKNOWN",
                parameter=parameter,
                attack_family="UNKNOWN",
                vulnerability_factor=None,
                security_strength_factor=None,
                calibration_status="UNCONFIGURED",
                confidence="INSUFFICIENT_EVIDENCE",
                calibration_version=self.version,
                source="QARS_KNOWLEDGE_BASE",
                methodology="Algorithm unidentified or missing.",
                notes="Unconfigured algorithm record."
            )

        alg = str(canonical_algorithm).strip().upper()
        param_str = str(parameter).strip().upper() if parameter is not None else None

        # 1. Exact match priority
        if param_str is not None:
            exact_key = f"{alg}:{param_str}"
            if exact_key in self._exact_map:
                return self._exact_map[exact_key]

        # 2. Canonical fallback priority
        if alg in self._canonical_map:
            return self._canonical_map[alg]

        # 3. UNCONFIGURED fallback
        return QARSCalibrationRecord(
            canonical_algorithm=alg,
            parameter=parameter,
            attack_family="UNKNOWN",
            vulnerability_factor=None,
            security_strength_factor=None,
            calibration_status="UNCONFIGURED",
            confidence="INSUFFICIENT_EVIDENCE",
            calibration_version=self.version,
            source="QARS_KNOWLEDGE_BASE",
            methodology=f"No calibration profile configured for '{alg}' (param={parameter}).",
            notes="Unconfigured fallback record."
        )

    def get_calibration_dictionary(self) -> Dict[str, Dict[str, float]]:
        """
        Exports configured records as a calibration dictionary compatible with QARSKnowledgeResolver.
        """
        result: Dict[str, Dict[str, float]] = {}
        for rec in self.records:
            if rec.calibration_status == "CONFIGURED" and rec.vulnerability_factor is not None and rec.security_strength_factor is not None:
                alg_name = rec.canonical_algorithm.upper()
                if rec.parameter is not None:
                    param_name = f"{alg_name}-{rec.parameter}"
                    result[param_name] = {
                        "vulnerability_factor": rec.vulnerability_factor,
                        "security_strength_factor": rec.security_strength_factor,
                    }
                else:
                    result[alg_name] = {
                        "vulnerability_factor": rec.vulnerability_factor,
                        "security_strength_factor": rec.security_strength_factor,
                    }
        return result


# Singleton instance for default production usage
_DEFAULT_PROVIDER: Optional[QARSCalibrationProvider] = None


def get_default_calibration_provider() -> QARSCalibrationProvider:
    global _DEFAULT_PROVIDER
    if _DEFAULT_PROVIDER is None:
        _DEFAULT_PROVIDER = QARSCalibrationProvider()
    return _DEFAULT_PROVIDER
