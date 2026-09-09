from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.repositories.asset_repository import AssetRepository
from app.repositories.risk_repository import RiskRepository
from app.models.db_models import AuditEvent, CryptoAsset
from app.risk.service import RiskService
from app.prioritization.priority_engine import PriorityEngine
from app.prioritization.schemas import (
    TechnicalAssessmentSchema,
    BusinessContextSchema,
    PrioritizedAssetSchema,
    UserContextUpdateRequest,
    PrioritizationSummaryResponse
)
from app.core.logging import logger

class PrioritizationService:
    def __init__(self, db: Session):
        self.db = db
        self.asset_repo = AssetRepository(db)
        self.risk_repo = RiskRepository(db)
        self.risk_service = RiskService(db)
        self.priority_engine = PriorityEngine()

    def get_prioritized_queue(self, project_id: str) -> PrioritizationSummaryResponse:
        assets = self.asset_repo.get_by_project(project_id)
        if not assets:
            return PrioritizationSummaryResponse(
                project_id=project_id,
                total_assets=0,
                p1_count=0,
                p2_count=0,
                p3_count=0,
                user_focused_count=0,
                user_adjusted_count=0,
                prioritized_queue=[]
            )

        # Get latest risk assessments for all project assets
        risk_summary = self.risk_service.get_project_risk_summary(project_id)
        assessed_list = risk_summary.get("priority_list", [])

        # If any asset is unassessed, run assess_project
        if len(assessed_list) < len(assets):
            assessed_list = self.risk_service.assess_project(project_id)

        # Map asset_id -> assessment dict
        assessed_map = {item["asset_id"]: item for item in assessed_list if "asset_id" in item}

        unranked_queue = []
        user_focused_count = 0
        user_adjusted_count = 0

        for asset in assets:
            extra = asset.extra_metadata or {}
            user_focus = bool(extra.get("user_focus", False))
            
            system_crit = asset.business_criticality_label
            effective_crit = extra.get("effective_planning_criticality", system_crit)
            adj_reason = extra.get("adjustment_reason")
            is_adjusted = (effective_crit != system_crit) or bool(adj_reason)

            if user_focus:
                user_focused_count += 1
            if is_adjusted:
                user_adjusted_count += 1

            assessment_dict = assessed_map.get(asset.id, {})
            risk_score = assessment_dict.get("risk_score", 0.0)
            risk_level = assessment_dict.get("risk_level", "LOW")
            quantum_status = assessment_dict.get("quantum_status", asset.quantum_safety.value if hasattr(asset.quantum_safety, "value") else str(asset.quantum_safety))
            
            mosca_dict = assessment_dict.get("mosca", {})
            mosca_status = mosca_dict.get("mosca_status", "UNKNOWN")
            quantum_threat_horizon = mosca_dict.get("quantum_threat_horizon", 2033)

            priority_tier = self.priority_engine.categorize_tier(
                risk_score=risk_score,
                risk_level=risk_level,
                mosca_status=mosca_status,
                effective_criticality=effective_crit,
                user_focus=user_focus
            )

            reasons = self.priority_engine.generate_reasons(
                risk_score=risk_score,
                risk_level=risk_level,
                mosca_status=mosca_status,
                system_criticality=system_crit,
                effective_criticality=effective_crit,
                user_focus=user_focus,
                is_adjusted=is_adjusted,
                adjustment_reason=adj_reason
            )

            item_dict = {
                "asset_id": asset.id,
                "asset_name": asset.name,
                "algorithm_name": asset.algorithm_name,
                "location": asset.location,
                "line_number": asset.line_number,
                "priority_tier": priority_tier,
                "priority_rank": 0,
                "technical_assessment": {
                    "quantum_safety": quantum_status,
                    "risk_level": risk_level,
                    "risk_score": risk_score,
                    "mosca_status": mosca_status,
                    "quantum_threat_horizon": quantum_threat_horizon
                },
                "business_context": {
                    "system_criticality": system_crit,
                    "effective_planning_criticality": effective_crit,
                    "user_focus": user_focus,
                    "is_user_adjusted": is_adjusted,
                    "adjustment_reason": adj_reason
                },
                "reasons": reasons
            }
            unranked_queue.append(item_dict)

        ranked_queue = self.priority_engine.rank_assets(unranked_queue)

        p1_count = sum(1 for item in ranked_queue if item["priority_tier"] == "P1")
        p2_count = sum(1 for item in ranked_queue if item["priority_tier"] == "P2")
        p3_count = sum(1 for item in ranked_queue if item["priority_tier"] == "P3")

        typed_queue = [PrioritizedAssetSchema(**item) for item in ranked_queue]

        return PrioritizationSummaryResponse(
            project_id=project_id,
            total_assets=len(assets),
            p1_count=p1_count,
            p2_count=p2_count,
            p3_count=p3_count,
            user_focused_count=user_focused_count,
            user_adjusted_count=user_adjusted_count,
            prioritized_queue=typed_queue
        )

    def update_user_context(self, req: UserContextUpdateRequest) -> Dict[str, Any]:
        asset = self.asset_repo.get(req.asset_id)
        if not asset:
            raise ValueError(f"Asset '{req.asset_id}' not found.")

        extra = dict(asset.extra_metadata or {})

        changes = []
        if req.user_focus is not None:
            prev = extra.get("user_focus", False)
            extra["user_focus"] = req.user_focus
            changes.append(f"user_focus: {prev} -> {req.user_focus}")

        if req.effective_planning_criticality is not None:
            prev_crit = extra.get("effective_planning_criticality", asset.business_criticality_label)
            extra["effective_planning_criticality"] = req.effective_planning_criticality
            changes.append(f"effective_planning_criticality: {prev_crit} -> {req.effective_planning_criticality}")

        if req.adjustment_reason is not None:
            extra["adjustment_reason"] = req.adjustment_reason
            changes.append(f"adjustment_reason: '{req.adjustment_reason}'")

        asset.extra_metadata = extra

        # Record audit event
        scan = asset.scan if hasattr(asset, "scan") else None
        project_id = scan.project_id if scan else None

        audit_entry = AuditEvent(
            project_id=project_id,
            action="UPDATE_USER_CONTEXT",
            actor="user",
            details={
                "asset_id": asset.id,
                "algorithm_name": asset.algorithm_name,
                "changes": changes,
                "system_criticality": asset.business_criticality_label,
                "effective_planning_criticality": extra.get("effective_planning_criticality"),
                "user_focus": extra.get("user_focus")
            }
        )
        self.db.add(audit_entry)
        self.db.commit()

        logger.info(f"User context updated for asset {asset.id}: {', '.join(changes)}")

        # Return updated prioritized item representation
        if project_id:
            summary = self.get_prioritized_queue(project_id)
            for item in summary.prioritized_queue:
                if item.asset_id == asset.id:
                    return item.dict()

        return {
            "asset_id": asset.id,
            "system_criticality": asset.business_criticality_label,
            "effective_planning_criticality": extra.get("effective_planning_criticality"),
            "user_focus": extra.get("user_focus"),
            "adjustment_reason": extra.get("adjustment_reason")
        }
