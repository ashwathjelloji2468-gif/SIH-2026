from typing import List, Dict, Any, Optional

class RecommendationRankingProvider:
    """
    ML Ranking Provider Stub for SENTRIQ Recommendation Engine.
    
    Acts as the clean interface for future ML model integration.
    Currently unconfigured due to absence of historical migration data.
    The deterministic Recommendation Engine remains authoritative.
    """
    def __init__(self):
        self.status = "UNCONFIGURED"
        self.reason = "NO_HISTORICAL_MIGRATION_DATA"

    def rank_candidates(
        self,
        eligible_candidates: List[Dict[str, Any]],
        asset_features: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Rank eligible candidates using trained ML models.
        
        Currently returns candidates in their deterministic eligibility order,
        marking status as UNCONFIGURED without fabricating synthetic scores or predictions.
        """
        return {
            "status": self.status,
            "reason": self.reason,
            "provider_name": "DeterministicBaselineProvider",
            "model_version": None,
            "ranked_candidates": eligible_candidates
        }
