from app.models.enums import EvidenceType

def calculate_confidence_score(evidence_type: EvidenceType, detector_accuracy: float = 0.9, has_ast_validation: bool = False) -> float:
    """
    Calculates finding confidence score separately from risk.
    - OBSERVED from AST: 0.9 - 1.0
    - OBSERVED from Regex: 0.7 - 0.85
    - INFERRED from context: 0.5 - 0.7
    - ASSUMED / DEFAULT: 0.3 - 0.5
    """
    base_scores = {
        EvidenceType.OBSERVED: 0.85,
        EvidenceType.INFERRED: 0.65,
        EvidenceType.ASSUMED: 0.40,
        EvidenceType.EXTERNAL: 0.75
    }

    score = base_scores.get(evidence_type, 0.5)

    if has_ast_validation and evidence_type == EvidenceType.OBSERVED:
        score = min(1.0, score + 0.10)

    score = round(score * detector_accuracy, 2)
    return max(0.0, min(1.0, score))
