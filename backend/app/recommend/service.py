from typing import List, Dict, Any, Optional

try:
    from sqlalchemy.orm import Session
except ImportError:
    Session = Any

try:
    from app.repositories.asset_repository import AssetRepository
    from app.repositories.risk_repository import RiskRepository
    from app.repositories.recommendation_repository import RecommendationRepository
except ImportError:
    AssetRepository = Any
    RiskRepository = Any
    RecommendationRepository = Any

from app.recommend.engine import RecommendationEngine

class RecommendationService:
    """
    Service layer orchestrating PQC recommendation generation, persistence,
    and project-level summary aggregations.
    """
    def __init__(self, db: Session):
        self.db = db
        self.asset_repo = AssetRepository(db) if hasattr(AssetRepository, "__call__") else None
        self.risk_repo = RiskRepository(db) if hasattr(RiskRepository, "__call__") else None
        self.rec_repo = RecommendationRepository(db) if hasattr(RecommendationRepository, "__call__") else None
        self.engine = RecommendationEngine()

    def recommend_asset(self, asset_id: str, force_regeneration: bool = True) -> Dict[str, Any]:
        if not self.asset_repo:
            raise RuntimeError("Database repository unavailable.")

        asset = self.asset_repo.get(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found.")

        # Load latest RiskAssessment and ThreatScenarios
        ra = self.risk_repo.get_latest_for_asset(asset_id) if self.risk_repo else None
        threats = self.risk_repo.get_threat_scenarios_for_asset(asset_id) if self.risk_repo else []

        threat_dict_list = [
            {
                "id": getattr(ts, "id", None),
                "scenario_type": ts.scenario_type.value if hasattr(ts, "scenario_type") and hasattr(ts.scenario_type, "value") else str(getattr(ts, "scenario_type", "MODERATE")),
                "name": getattr(ts, "name", "Threat Scenario"),
                "description": getattr(ts, "description", "")
            } for ts in threats
        ]

        if not force_regeneration and self.rec_repo:
            existing = self.rec_repo.get_latest_for_asset(asset_id)
            if existing:
                return self._recommendation_to_dict(existing, asset, ra, threat_dict_list)

        detector_names = [e.detector_name for e in (getattr(asset, "evidence_items", []) or [])]

        risk_level = ra.risk_level.value if (ra and hasattr(ra, "risk_level") and hasattr(ra.risk_level, "value")) else "LOW"
        risk_score = ra.risk_score if ra else 0.0
        complexity = getattr(ra, "migration_complexity_score", 50.0) if ra else 50.0

        comp_str = "HIGH" if complexity >= 75.0 else ("MEDIUM" if complexity >= 40.0 else "LOW")

        rec_eval = self.engine.generate_recommendation(
            algorithm_name=asset.algorithm_name,
            purpose=asset.purpose,
            quantum_safety=asset.quantum_safety,
            risk_level=risk_level,
            risk_score=risk_score,
            threat_scenarios=threat_dict_list,
            migration_complexity=comp_str,
            detector_names=detector_names
        )

        rec_record = self.rec_repo.store_recommendation(
            asset_id=asset_id,
            rec_data=rec_eval,
            risk_assessment_id=ra.id if ra else None
        ) if self.rec_repo else None

        if rec_record:
            return self._recommendation_to_dict(rec_record, asset, ra, threat_dict_list)
        else:
            rec_eval["asset_id"] = asset_id
            rec_eval["asset_name"] = asset.name
            return rec_eval

    def recommend_project(self, project_id: str) -> List[Dict[str, Any]]:
        if not self.asset_repo:
            raise RuntimeError("Database repository unavailable.")
        assets = self.asset_repo.get_by_project(project_id)
        results = []
        for asset in assets:
            res = self.recommend_asset(asset.id, force_regeneration=True)
            results.append(res)
        return results

    def get_project_recommendation_summary(self, project_id: str) -> Dict[str, Any]:
        if not self.asset_repo:
            raise RuntimeError("Database repository unavailable.")
        assets = self.asset_repo.get_by_project(project_id)
        total_assets = len(assets)

        rec_list = []
        for asset in assets:
            rec = self.recommend_asset(asset.id, force_regeneration=False)
            rec_list.append(rec)

        category_counts = {
            "pqc_replacement_count": 0,
            "hybrid_count": 0,
            "retain_crypto_count": 0,
            "manual_review_count": 0,
            "no_action_required_count": 0
        }

        algorithm_counts = {
            "ML-KEM": 0,
            "ML-DSA": 0,
            "SLH-DSA": 0,
            "RETAIN_EXISTING": 0,
            "MANUAL_REVIEW_REQUIRED": 0
        }

        priority_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MODERATE": 0,
            "LOW": 0
        }

        for rec in rec_list:
            cat = str(rec.get("category", "")).upper()
            if "PQC_REPLACEMENT" in cat:
                category_counts["pqc_replacement_count"] += 1
            elif "HYBRID" in cat:
                category_counts["hybrid_count"] += 1
            elif "RETAIN" in cat:
                category_counts["retain_crypto_count"] += 1
            elif "MANUAL" in cat:
                category_counts["manual_review_count"] += 1
            else:
                category_counts["no_action_required_count"] += 1

            algo = str(rec.get("recommended_algorithm", ""))
            if "ML-KEM" in algo:
                algorithm_counts["ML-KEM"] += 1
            elif "ML-DSA" in algo:
                algorithm_counts["ML-DSA"] += 1
            elif "SLH-DSA" in algo:
                algorithm_counts["SLH-DSA"] += 1
            elif "RETAIN" in algo:
                algorithm_counts["RETAIN_EXISTING"] += 1
            else:
                algorithm_counts["MANUAL_REVIEW_REQUIRED"] += 1

            prio = str(rec.get("priority", "LOW")).upper()
            if prio in priority_counts:
                priority_counts[prio] += 1

        return {
            "project_id": project_id,
            "total_recommendations": len(rec_list),
            "total_assets": total_assets,
            "category_summary": category_counts,
            "algorithm_counts": algorithm_counts,
            "priority_counts": priority_counts,
            "recommendations": rec_list
        }

    def _recommendation_to_dict(self, rec, asset, ra, threats) -> Dict[str, Any]:
        return {
            "id": rec.id,
            "asset_id": rec.asset_id,
            "asset_name": asset.name if asset else "Unknown Asset",
            "algorithm_name": asset.algorithm_name if asset else "Unknown",
            "crypto_purpose": asset.purpose.value if (asset and hasattr(asset.purpose, "value")) else "UNKNOWN",
            "quantum_status": asset.quantum_safety.value if (asset and hasattr(asset.quantum_safety, "value")) else "UNKNOWN",
            "risk_assessment_id": rec.risk_assessment_id or (ra.id if ra else None),
            "risk_score": ra.risk_score if ra else 0.0,
            "risk_level": ra.risk_level.value if (ra and hasattr(ra.risk_level, "value")) else "LOW",
            "target_pqc_candidate": rec.target_pqc_candidate,
            "recommended_algorithm": rec.recommended_algorithm or rec.target_pqc_candidate,
            "alternative_algorithm": rec.alternative_algorithm,
            "category": rec.category.value if hasattr(rec.category, "value") else str(rec.category),
            "priority": rec.priority or "LOW",
            "standard_status": rec.standard_status.value if hasattr(rec.standard_status, "value") else str(rec.standard_status),
            "rationale": rec.rationale,
            "compatibility_notes": rec.compatibility_notes,
            "performance_notes": rec.performance_notes,
            "tradeoffs": rec.tradeoffs or {},
            "threat_scenarios": threats or rec.threat_scenarios or [],
            "migration_notes": rec.migration_notes,
            "migration_complexity": rec.migration_complexity or "MEDIUM",
            "confidence": rec.confidence,
            "kb_version": rec.kb_version or "2026.3.0-NIST-PQC",
            "created_at": rec.created_at.isoformat() if (rec.created_at and hasattr(rec.created_at, "isoformat")) else str(rec.created_at)
        }
