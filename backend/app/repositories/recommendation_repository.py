from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models.db_models import Recommendation, CryptoAsset, Scan
from app.models.enums import StandardStatus, RecommendationCategory

class RecommendationRepository:
    """
    Database repository for Recommendation records.
    DB operations only — does NOT generate recommendations.
    """
    def __init__(self, db: Session):
        self.db = db

    def store_recommendation(
        self,
        asset_id: str,
        rec_data: Dict[str, Any],
        risk_assessment_id: Optional[str] = None
    ) -> Recommendation:
        cat_str = rec_data.get("category", "MANUAL_REVIEW")
        if hasattr(cat_str, "value"):
            cat_str = cat_str.value
        try:
            category = RecommendationCategory(cat_str)
        except ValueError:
            category = RecommendationCategory.MANUAL_REVIEW

        std_status_str = rec_data.get("standard_status", "FINAL_STANDARD")
        if hasattr(std_status_str, "value"):
            std_status_str = std_status_str.value
        try:
            std_status = StandardStatus(std_status_str)
        except ValueError:
            std_status = StandardStatus.FINAL_STANDARD

        rec = Recommendation(
            asset_id=asset_id,
            risk_assessment_id=risk_assessment_id,
            target_pqc_candidate=rec_data.get("target_pqc_candidate", "ML-KEM"),
            recommended_algorithm=rec_data.get("recommended_algorithm"),
            alternative_algorithm=rec_data.get("alternative_algorithm"),
            category=category,
            priority=rec_data.get("priority", "LOW"),
            standard_status=std_status,
            rationale=rec_data.get("rationale", ""),
            compatibility_notes=rec_data.get("compatibility_notes"),
            performance_notes=rec_data.get("performance_notes"),
            tradeoffs=rec_data.get("tradeoffs"),
            threat_scenarios=rec_data.get("threat_scenarios"),
            migration_notes=rec_data.get("migration_notes"),
            migration_complexity=rec_data.get("migration_complexity", "MEDIUM"),
            confidence=rec_data.get("confidence", 1.0),
            kb_version=rec_data.get("kb_version", "2026.3.0-NIST-PQC")
        )
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)
        return rec

    def store_recommendations_bulk(
        self,
        recs_data: List[tuple]
    ) -> List[Recommendation]:
        objs = []
        for asset_id, rec_data, risk_assessment_id in recs_data:
            cat_str = rec_data.get("category", "MANUAL_REVIEW")
            if hasattr(cat_str, "value"):
                cat_str = cat_str.value
            try:
                category = RecommendationCategory(cat_str)
            except ValueError:
                category = RecommendationCategory.MANUAL_REVIEW

            std_status_str = rec_data.get("standard_status", "FINAL_STANDARD")
            if hasattr(std_status_str, "value"):
                std_status_str = std_status_str.value
            try:
                std_status = StandardStatus(std_status_str)
            except ValueError:
                std_status = StandardStatus.FINAL_STANDARD

            rec = Recommendation(
                asset_id=asset_id,
                risk_assessment_id=risk_assessment_id,
                target_pqc_candidate=rec_data.get("target_pqc_candidate", "ML-KEM"),
                recommended_algorithm=rec_data.get("recommended_algorithm"),
                alternative_algorithm=rec_data.get("alternative_algorithm"),
                category=category,
                priority=rec_data.get("priority", "LOW"),
                standard_status=std_status,
                rationale=rec_data.get("rationale", ""),
                compatibility_notes=rec_data.get("compatibility_notes"),
                performance_notes=rec_data.get("performance_notes"),
                tradeoffs=rec_data.get("tradeoffs"),
                threat_scenarios=rec_data.get("threat_scenarios"),
                migration_notes=rec_data.get("migration_notes"),
                migration_complexity=rec_data.get("migration_complexity", "MEDIUM"),
                confidence=rec_data.get("confidence", 1.0),
                kb_version=rec_data.get("kb_version", "2026.3.0-NIST-PQC")
            )
            objs.append(rec)

        self.db.add_all(objs)
        self.db.commit()
        return objs

    def get(self, recommendation_id: str) -> Optional[Recommendation]:
        return self.db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()

    def get_latest_for_asset(self, asset_id: str) -> Optional[Recommendation]:
        return (
            self.db.query(Recommendation)
            .filter(Recommendation.asset_id == asset_id)
            .order_by(desc(Recommendation.created_at))
            .first()
        )

    def list_recommendations(
        self,
        project_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        recommended_algorithm: Optional[str] = None
    ) -> List[Recommendation]:
        query = self.db.query(Recommendation).join(
            CryptoAsset, Recommendation.asset_id == CryptoAsset.id
        ).join(
            Scan, CryptoAsset.scan_id == Scan.id
        )

        if project_id:
            query = query.filter(Scan.project_id == project_id)

        if asset_id:
            query = query.filter(Recommendation.asset_id == asset_id)

        if category:
            query = query.filter(Recommendation.category == category)

        if priority:
            query = query.filter(Recommendation.priority == priority)

        if recommended_algorithm:
            query = query.filter(Recommendation.recommended_algorithm == recommended_algorithm)

        return query.order_by(desc(Recommendation.created_at)).all()
