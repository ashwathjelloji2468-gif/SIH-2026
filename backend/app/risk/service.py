from typing import List, Dict, Any, Optional, TYPE_CHECKING

try:
    from sqlalchemy.orm import Session
except ImportError:
    Session = Any

try:
    from app.repositories.asset_repository import AssetRepository
    from app.repositories.risk_repository import RiskRepository
except ImportError:
    AssetRepository = Any
    RiskRepository = Any

from app.risk.risk_engine import RiskEngine
from app.core.logging import logger

class RiskService:
    """
    Service layer for orchestrating risk assessment calculations, persistence,
    and project-level aggregations.
    """
    def __init__(self, db: Session):
        self.db = db
        self.asset_repo = AssetRepository(db) if hasattr(AssetRepository, "__call__") else None
        self.risk_repo = RiskRepository(db) if hasattr(RiskRepository, "__call__") else None
        self.engine = RiskEngine()

    def assess_asset(
        self,
        asset_id: str,
        data_sensitivity_label: str = "UNKNOWN",
        business_criticality_label: str = "UNKNOWN",
        data_lifetime_years: float = 10.0,
        migration_time_years: float = 3.0,
        quantum_threat_horizon_year: Optional[int] = None,
        force_reassessment: bool = True
    ) -> Dict[str, Any]:
        if not self.asset_repo:
            raise RuntimeError("Database repository unavailable.")

        asset = self.asset_repo.get(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found.")

        # Check existing latest assessment if force_reassessment is False
        if not force_reassessment:
            existing = self.risk_repo.get_latest_for_asset(asset_id)
            if existing:
                threats = self.risk_repo.get_threat_scenarios_for_asset(asset_id)
                return self._assessment_to_dict(existing, asset, threats)

        # Extract evidence information
        detector_names = [e.detector_name for e in (asset.evidence_items or [])]
        excerpts = [e.excerpt for e in (asset.evidence_items or []) if e.excerpt]

        # Dynamically estimate repo-level migration time Y if default 3.0 is passed
        if migration_time_years == 3.0 and self.asset_repo and hasattr(asset, "scan_id"):
            try:
                project_assets = self.asset_repo.get_by_scan(asset.scan_id)
                if project_assets:
                    from app.risk.mosca import estimate_migration_time_from_assets
                    migration_time_years = estimate_migration_time_from_assets(project_assets)
            except Exception:
                pass

        eval_result = self.engine.evaluate_asset_risk(
            algorithm_name=asset.algorithm_name,
            quantum_safety=asset.quantum_safety,
            purpose=asset.purpose,
            asset_type=asset.asset_type.value if hasattr(asset.asset_type, "value") else str(asset.asset_type),
            detector_names=detector_names,
            data_sensitivity_label=data_sensitivity_label,
            business_criticality_label=business_criticality_label,
            data_lifetime_years=data_lifetime_years,
            migration_time_years=migration_time_years,
            quantum_threat_horizon_year=quantum_threat_horizon_year,
            evidence_excerpts=excerpts
        )

        ra = self.risk_repo.store_assessment(asset_id, eval_result)
        threats = self.risk_repo.get_threat_scenarios_for_asset(asset_id)
        return self._assessment_to_dict(ra, asset, threats)

    def assess_project(
        self,
        project_id: str,
        data_sensitivity_label: str = "UNKNOWN",
        business_criticality_label: str = "UNKNOWN",
        quantum_threat_horizon_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        if not self.asset_repo:
            raise RuntimeError("Database repository unavailable.")
        assets = self.asset_repo.get_by_project(project_id)
        if not assets:
            return []
        
        # Calculate dynamic Y for the repository
        from app.risk.mosca import estimate_migration_time_from_assets
        dynamic_y = estimate_migration_time_from_assets(assets)

        to_eval = []
        for asset in assets:
            detector_names = [e.detector_name for e in (getattr(asset, "evidence_items", []) or [])]
            excerpts = [e.excerpt for e in (getattr(asset, "evidence_items", []) or []) if e.excerpt]

            eval_result = self.engine.evaluate_asset_risk(
                algorithm_name=asset.algorithm_name,
                quantum_safety=asset.quantum_safety,
                purpose=asset.purpose,
                asset_type=asset.asset_type.value if hasattr(asset.asset_type, "value") else str(asset.asset_type),
                detector_names=detector_names,
                data_sensitivity_label=data_sensitivity_label,
                business_criticality_label=business_criticality_label,
                data_lifetime_years=10.0,
                migration_time_years=dynamic_y,
                quantum_threat_horizon_year=quantum_threat_horizon_year,
                evidence_excerpts=excerpts
            )
            to_eval.append((asset, eval_result))

        if to_eval and self.risk_repo and hasattr(self.risk_repo, "store_assessments_bulk"):
            bulk_payload = [(item[0].id, item[1]) for item in to_eval]
            ra_records = self.risk_repo.store_assessments_bulk(bulk_payload)
            results = []
            for idx, item in enumerate(to_eval):
                asset = item[0]
                ra = ra_records[idx]
                threats = self.risk_repo.get_threat_scenarios_for_asset(asset.id)
                results.append(self._assessment_to_dict(ra, asset, threats))
            return results

        results = []
        for item in to_eval:
            asset = item[0]
            eval_result = item[1]
            ra = self.risk_repo.store_assessment(asset.id, eval_result) if self.risk_repo else None
            threats = self.risk_repo.get_threat_scenarios_for_asset(asset.id) if self.risk_repo else []
            if ra:
                results.append(self._assessment_to_dict(ra, asset, threats))
            else:
                eval_result["asset_id"] = asset.id
                results.append(eval_result)
        return results

    def get_project_risk_summary(self, project_id: str) -> Dict[str, Any]:
        if not self.asset_repo:
            raise RuntimeError("Database repository unavailable.")
        assets = self.asset_repo.get_by_project(project_id)
        total_assets = len(assets)

        assessed_list = []
        if assets:
            asset_ids = [a.id for a in assets]
            risk_map = {}
            threats_map = {}
            from app.models.db_models import RiskAssessment, ThreatScenario
            all_ras = self.db.query(RiskAssessment).filter(RiskAssessment.asset_id.in_(asset_ids)).all()
            for ra in all_ras:
                if ra.asset_id not in risk_map or (hasattr(ra, 'created_at') and getattr(ra, 'created_at') > getattr(risk_map[ra.asset_id], 'created_at')):
                    risk_map[ra.asset_id] = ra

            all_ts = self.db.query(ThreatScenario).filter(ThreatScenario.asset_id.in_(asset_ids)).all()
            for ts in all_ts:
                threats_map.setdefault(ts.asset_id, []).append(ts)

            for asset in assets:
                ra = risk_map.get(asset.id)
                if ra:
                    threats = threats_map.get(asset.id, [])
                    assessed_list.append(self._assessment_to_dict(ra, asset, threats))

        assessed_count = len(assessed_list)
        unassessed_count = total_assets - assessed_count

        # Categorize risk level counts
        risk_counts = {"low": 0, "moderate": 0, "high": 0, "critical": 0}
        q_vulnerable = 0
        q_resistant = 0
        unknown_q = 0
        deadline_risk_count = 0
        total_score = 0.0
        total_conf = 0.0

        threat_scenario_counts: Dict[str, int] = {}

        for item in assessed_list:
            r_level = (item.get("risk_level") or "LOW").lower()
            if r_level in risk_counts:
                risk_counts[r_level] += 1

            q_stat = (item.get("quantum_status") or "UNKNOWN").upper()
            if "VULNERABLE" in q_stat:
                q_vulnerable += 1
            elif "RESISTANT" in q_stat or "SAFE" in q_stat:
                q_resistant += 1
            else:
                unknown_q += 1

            mosca = item.get("mosca", {})
            if mosca.get("mosca_status") in ["DEADLINE_RISK", "MIGRATION_REQUIRED"]:
                deadline_risk_count += 1

            total_score += item.get("risk_score", 0.0)
            total_conf += item.get("confidence_score", 1.0)

            for ts in item.get("threat_scenarios", []):
                stype = ts.get("scenario_type", "UNKNOWN")
                threat_scenario_counts[stype] = threat_scenario_counts.get(stype, 0) + 1

        if assessed_count == 0 and total_assets > 0:
            for asset in assets:
                qs = str(getattr(asset, "quantum_safety", "") or "").upper()
                if "VULNERABLE" in qs:
                    q_vulnerable += 1
                elif "SAFE" in qs or "RESISTANT" in qs:
                    q_resistant += 1
                else:
                    unknown_q += 1

        avg_score = round(total_score / assessed_count, 1) if assessed_count > 0 else 0.0
        avg_conf = round(total_conf / assessed_count, 2) if assessed_count > 0 else 0.0



        # Deterministic Priority Ranking:
        # 1. risk_score desc
        # 2. quantum_exposure desc
        # 3. data_sensitivity desc
        # 4. business_criticality desc
        priority_list = sorted(
            assessed_list,
            key=lambda x: (
                x.get("risk_score", 0.0),
                x.get("factors", {}).get("quantum_exposure", 0.0),
                x.get("factors", {}).get("data_sensitivity", 0.0),
                x.get("factors", {}).get("business_criticality", 0.0)
            ),
            reverse=True
        )

        # Calculate dynamic Mosca summary for the project
        from app.risk.mosca import calculate_mosca_urgency
        mosca_summary = calculate_mosca_urgency(assets=assets)

        return {
            "project_id": project_id,
            "total_assets": total_assets,
            "assessed_assets": assessed_count,
            "unassessed_assets": unassessed_count,
            "average_risk_score": avg_score,
            "risk_counts": risk_counts,
            "high_or_critical_risk_assets": risk_counts.get("high", 0) + risk_counts.get("critical", 0),
            "quantum_vulnerable_count": q_vulnerable,
            "quantum_resistant_count": q_resistant,
            "unknown_count": unknown_q,
            "migration_deadline_risk_count": deadline_risk_count,
            "threat_scenario_counts": threat_scenario_counts,
            "confidence_summary": {
                "average_confidence": avg_conf
            },
            "mosca": mosca_summary,
            "priority_list": priority_list,
            "highest_risk_assets": priority_list[:5]
        }

    def _assessment_to_dict(self, ra, asset, threats) -> Dict[str, Any]:
        comp_dict = {
            "id": asset.id if asset else ra.asset_id,
            "primitive": asset.algorithm_name if asset else "UNKNOWN",
            "algorithm_name": asset.algorithm_name if asset else "UNKNOWN",
            "key_size": getattr(asset, "key_size", None),
            "location": asset.location if asset else "",
            "purpose": asset.purpose.value if asset and hasattr(asset.purpose, "value") else str(getattr(asset, "purpose", "")) if asset else ""
        }
        project = getattr(asset, "project", None) if asset else None
        
        from app.engines.mosca_engine import MoscaEngine
        m_eval = MoscaEngine().evaluate_component_mosca(
            component=comp_dict,
            user_x_years=getattr(project, "user_x_years", None) if project else None,
            user_domain=getattr(project, "user_domain", None) if project else None,
            user_y_scenario=getattr(project, "user_y_scenario", None) if project else None
        )

        return {
            "id": ra.id,
            "asset_id": ra.asset_id,
            "asset_name": asset.name if asset else "Unknown Asset",
            "algorithm_name": asset.algorithm_name if asset else "Unknown",
            "location": asset.location if asset else "",
            "quantum_status": ra.quantum_status or (asset.quantum_safety.value if asset and hasattr(asset.quantum_safety, "value") else "UNKNOWN"),
            "crypto_purpose": ra.crypto_purpose or (asset.purpose.value if asset and hasattr(asset.purpose, "value") else "UNKNOWN"),
            "risk_score": ra.risk_score,
            "risk_level": ra.risk_level.value if hasattr(ra.risk_level, "value") else str(ra.risk_level),
            "priority": ra.priority or "LOW",
            "confidence_score": ra.confidence_score,
            "x": m_eval["x"],
            "y": m_eval["y"],
            "z": m_eval["z"],
            "z_score": m_eval["z"].get("z_score"),
            "z_planning_horizon_years": m_eval["z"].get("z_planning_horizon_years"),
            "mosca_score": m_eval.get("mosca_score"),
            "technical_urgency": m_eval.get("technical_urgency"),
            "factors": ra.factors or {
                "quantum_exposure": ra.quantum_exposure,
                "data_sensitivity": ra.data_sensitivity_score,
                "business_criticality": ra.business_criticality_score,
                "migration_complexity": ra.migration_complexity_score,
                "lifetime_exposure": ra.lifetime_exposure_score,
                "mosca_score": ra.mosca_factor_score
            },
            "mosca": {
                "mosca_status": ra.mosca_status or m_eval.get("urgency", "UNKNOWN"),
                "quantum_threat_horizon": m_eval["z"].get("z_target_year") or ra.quantum_threat_horizon or 2036,
                "mosca_score": m_eval.get("mosca_score"),
                "x_years": m_eval["x"]["value"],
                "y_years": m_eval["y"]["value"],
                "z_horizon_years": m_eval["z"].get("z_planning_horizon_years"),
                "z_score": m_eval["z"].get("z_score"),
                "rationale": m_eval.get("explanation") or ra.explanation
            },
            "threat_scenarios": [
                {
                    "id": ts.id,
                    "scenario_type": ts.scenario_type.value if hasattr(ts.scenario_type, "value") else str(ts.scenario_type),
                    "name": ts.name,
                    "severity": ts.severity,
                    "urgency": ts.urgency,
                    "description": ts.description,
                    "rationale": ts.rationale,
                    "evidence": ts.evidence or []
                } for ts in threats
            ],
            "rationale": ra.rationale or [ra.explanation] if ra.explanation else [],
            "created_at": ra.created_at.isoformat() if ra.created_at and hasattr(ra.created_at, "isoformat") else str(ra.created_at)
        }
