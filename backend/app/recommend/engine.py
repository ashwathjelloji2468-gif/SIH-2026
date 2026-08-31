from typing import List, Dict, Any
from app.models.db_models import CryptoAsset
from app.knowledge.mapping_rules import get_pqc_recommendations

class RecommendationEngine:
    def evaluate_recommendations(self, asset: CryptoAsset) -> List[Dict[str, Any]]:
        return get_pqc_recommendations(asset.purpose, asset.algorithm_name)
