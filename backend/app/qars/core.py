from typing import Optional, TYPE_CHECKING
from app.qars.models import QARSCoreInput, QARSCoreOutput, QARSValidationError, QARSPolicyInput, QARSResult
from app.qars.config import QARSConfig

if TYPE_CHECKING:
    from app.qars.policy import ComponentProvider


def compute_qars_core(input_data: QARSCoreInput) -> QARSCoreOutput:
    """
    Computes QARS Core score deterministically:
    - Sn = (S - 1) / 4
    - En = (E - 1) / 4
    - T = clamp((X + Y - Z) / Z, 0, 1)
    - QARS_core = 100 * T * Sn * En

    Strict validation bounds:
    - S (data_sensitivity) in [1..5]
    - E (exposure) in [1..5]
    - X (x_years) > 0
    - Y (y_years) >= 0
    - Z (z_years) > 0
    """
    if input_data is None:
        raise QARSValidationError("input_data cannot be None")

    s = input_data.data_sensitivity
    e = input_data.exposure
    x = input_data.x_years
    y = input_data.y_years
    z = input_data.z_years

    # Input validation
    if s is None or s < 1.0 or s > 5.0:
        raise QARSValidationError(f"data_sensitivity (S) must be between 1 and 5 (inclusive), got {s}")
    if e is None or e < 1.0 or e > 5.0:
        raise QARSValidationError(f"exposure (E) must be between 1 and 5 (inclusive), got {e}")
    if x is None or x <= 0:
        raise QARSValidationError(f"x_years (X) must be strictly greater than 0, got {x}")
    if y is None or y < 0:
        raise QARSValidationError(f"y_years (Y) must be greater than or equal to 0, got {y}")
    if z is None or z <= 0:
        raise QARSValidationError(f"z_years (Z) must be strictly greater than 0, got {z}")

    # Normalization inside QARS Core only
    sn = (s - 1.0) / 4.0
    en = (e - 1.0) / 4.0

    # Timeline pressure with clamp [0, 1]
    raw_t = (x + y - z) / z
    t = min(1.0, max(0.0, raw_t))

    # Core calculation with clamp [0, 100]
    core_score = 100.0 * t * sn * en
    score = min(100.0, max(0.0, core_score))

    return QARSCoreOutput(
        score=score,
        timeline_pressure=t,
        sensitivity_normalized=sn,
        exposure_normalized=en,
        x_years=x,
        y_years=y,
        z_years=z,
    )


def calculate_qars(
    core_input: QARSCoreInput,
    policy_input: Optional[QARSPolicyInput] = None,
    config: Optional[QARSConfig] = None,
    provider: Optional["ComponentProvider"] = None,
) -> QARSResult:
    """
    End-to-end evaluation pipeline: QARS Core -> Policy Engine -> QARSResult.
    """
    from app.qars.policy import QARSPolicyEngine

    core_output = compute_qars_core(core_input)
    engine = QARSPolicyEngine(config=config, provider=provider)
    if policy_input is None:
        policy_input = QARSPolicyInput(core_input=core_input)
    elif policy_input.core_input is None:
        policy_input.core_input = core_input

    return engine.evaluate(core_output, policy_input)
