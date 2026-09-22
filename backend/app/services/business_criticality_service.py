from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.repositories.project_repository import ProjectRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.audit_repository import AuditRepository
from app.risk.service import RiskService
from app.core.logging import logger

FACTOR_DEFINITIONS = [
    {"id": "dataSensitivity", "name": "Data Sensitivity", "weight": 0.15},
    {"id": "dataShelfLife", "name": "Data Shelf-Life", "weight": 0.10},
    {"id": "confidentialityImpact", "name": "Confidentiality Impact", "weight": 0.15},
    {"id": "integrityImpact", "name": "Integrity Impact", "weight": 0.10},
    {"id": "availabilityImpact", "name": "Availability Impact", "weight": 0.10},
    {"id": "regulatoryExposure", "name": "Regulatory Exposure", "weight": 0.15},
    {"id": "financialImpact", "name": "Financial Impact", "weight": 0.15},
    {"id": "reputationalImpact", "name": "Reputational Impact", "weight": 0.10},
]

DEFAULT_RATINGS = {
    "dataSensitivity": 5,
    "dataShelfLife": 4,
    "confidentialityImpact": 5,
    "integrityImpact": 4,
    "availabilityImpact": 4,
    "regulatoryExposure": 5,
    "financialImpact": 5,
    "reputationalImpact": 4,
    "exposureRating": 4,
}

class BusinessCriticalityService:
    def __init__(self, db: Session):
        self.db = db
        self.proj_repo = ProjectRepository(db)
        self.asset_repo = AssetRepository(db)
        self.audit_repo = AuditRepository(db)
        self.risk_service = RiskService(db)

    def calculate_scores(self, ratings: Dict[str, int]) -> Dict[str, Any]:
        wis = sum((ratings.get(f["id"], 0) * f["weight"]) for f in FACTOR_DEFINITIONS)
        exp_rating = ratings.get("exposureRating", 0)
        em = 1.0 + (0.09375 * exp_rating)
        raw = wis * em
        normalized = min(5.0, round(raw / 1.5, 2))

        if normalized >= 4.0:
            calc_label = "CRITICAL"
        elif normalized >= 3.0:
            calc_label = "HIGH"
        elif normalized >= 2.0:
            calc_label = "MEDIUM"
        else:
            calc_label = "LOW"

        return {
            "wis": round(wis, 2),
            "exposure_multiplier": round(em, 3),
            "raw_score": round(raw, 3),
            "normalized_score": normalized,
            "calculated_label": calc_label
        }

    def get_project_business_criticality(self, project_id: str) -> Dict[str, Any]:
        proj = self.proj_repo.get(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' not found.")

        bctx = dict(proj.business_context or {})
        ratings = bctx.get("factor_ratings", DEFAULT_RATINGS)
        scores = self.calculate_scores(ratings)

        assets = self.asset_repo.get_by_project(project_id)

        # System criticality derived from assets or factor ratings
        if assets:
            sys_labels = [a.business_criticality_label for a in assets]
            if "CRITICAL" in sys_labels:
                system_criticality = "CRITICAL"
            elif "HIGH" in sys_labels:
                system_criticality = "HIGH"
            elif "MEDIUM" in sys_labels:
                system_criticality = "MEDIUM"
            else:
                system_criticality = "LOW"
        else:
            system_criticality = scores["calculated_label"]

        user_override = bctx.get("user_override")
        adjustment_reason = bctx.get("adjustment_reason") or bctx.get("override_reason")

        effective_criticality = user_override if (user_override and user_override in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]) else system_criticality

        assets_summary = []
        for asset in assets:
            extra = dict(asset.extra_metadata or {})
            a_sys = asset.business_criticality_label
            a_eff = extra.get("effective_planning_criticality") or user_override or a_sys
            a_reason = extra.get("adjustment_reason") or adjustment_reason
            assets_summary.append({
                "asset_id": asset.id,
                "asset_name": asset.name,
                "algorithm_name": asset.algorithm_name,
                "system_criticality": a_sys,
                "effective_planning_criticality": a_eff,
                "adjustment_reason": a_reason,
                "is_overridden": bool(extra.get("effective_planning_criticality") or user_override)
            })

        return {
            "project_id": project_id,
            "project_name": proj.name,
            "system_criticality": system_criticality,
            "user_override": user_override,
            "effective_criticality": effective_criticality,
            "adjustment_reason": adjustment_reason,
            "override_reason": adjustment_reason,
            "is_overridden": bool(user_override),
            "factor_ratings": ratings,
            "scores": scores,
            "assets_summary": assets_summary,
            "updated_at": proj.updated_at.isoformat() if proj.updated_at else None
        }

    def update_project_business_criticality(
        self,
        project_id: str,
        factor_ratings: Optional[Dict[str, int]] = None,
        user_override: Optional[str] = None,
        adjustment_reason: Optional[str] = None,
        revert_override: bool = False,
        actor: str = "user"
    ) -> Dict[str, Any]:
        proj = self.proj_repo.get(project_id)
        if not proj:
            raise ValueError(f"Project '{project_id}' not found.")

        bctx = dict(proj.business_context or {})
        old_state = self.get_project_business_criticality(project_id)

        # Update factor ratings if provided
        if factor_ratings is not None:
            current_ratings = dict(bctx.get("factor_ratings", DEFAULT_RATINGS))
            current_ratings.update(factor_ratings)
            bctx["factor_ratings"] = current_ratings

        # Handle Override / Revert logic
        if revert_override:
            old_override = bctx.get("user_override")
            bctx["user_override"] = None
            bctx["adjustment_reason"] = None
            
            # Record Audit Event
            self.audit_repo.log(
                action="BUSINESS_CRITICALITY_OVERRIDE_REVERTED",
                actor=actor,
                project_id=project_id,
                details={
                    "previous_override": old_override,
                    "system_criticality": old_state["system_criticality"],
                    "effective_criticality": old_state["system_criticality"],
                    "reason": "User reverted planning override to system default."
                }
            )
        elif user_override is not None:
            user_override_clean = user_override.strip().upper()
            if user_override_clean not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                raise ValueError(f"Invalid business criticality override value '{user_override}'. Must be LOW, MEDIUM, HIGH, or CRITICAL.")

            reason_clean = (adjustment_reason or "").strip()
            if not reason_clean:
                raise ValueError("Adjustment reason is required when setting a business criticality override.")

            bctx["user_override"] = user_override_clean
            bctx["adjustment_reason"] = reason_clean

            # Record Audit Event
            self.audit_repo.log(
                action="BUSINESS_CRITICALITY_OVERRIDE",
                actor=actor,
                project_id=project_id,
                details={
                    "old_effective_criticality": old_state["effective_criticality"],
                    "new_effective_criticality": user_override_clean,
                    "user_override": user_override_clean,
                    "system_criticality": old_state["system_criticality"],
                    "reason": reason_clean
                }
            )

        proj.business_context = bctx
        self.db.add(proj)

        # Update asset metadata & propagate effective criticality to assets
        assets = self.asset_repo.get_by_project(project_id)
        effective_crit = bctx.get("user_override") or old_state["system_criticality"]
        reason_val = bctx.get("adjustment_reason")

        for asset in assets:
            extra = dict(asset.extra_metadata or {})
            if revert_override:
                extra.pop("effective_planning_criticality", None)
                extra.pop("adjustment_reason", None)
            elif user_override is not None:
                extra["effective_planning_criticality"] = effective_crit
                extra["adjustment_reason"] = reason_val
            asset.extra_metadata = extra
            self.db.add(asset)

        from app.context.invalidation import invalidate_project_precomputed_data
        invalidate_project_precomputed_data(project_id, self.db)
        self.db.commit()

        # Re-assess risk for project assets using updated effective criticality
        self.risk_service.assess_project(
            project_id=project_id,
            business_criticality_label=effective_crit
        )

        logger.info(f"Project '{project_id}' business criticality updated. Effective: {effective_crit}")
        return self.get_project_business_criticality(project_id)
