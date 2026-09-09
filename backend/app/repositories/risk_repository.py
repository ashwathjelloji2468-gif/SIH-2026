from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models.db_models import RiskAssessment, ThreatScenario, CryptoAsset, Scan
from app.models.enums import RiskLevel, ThreatScenarioType

class RiskRepository:
    """
    Database repository for RiskAssessment and ThreatScenario records.
    DB operations only — does NOT calculate risk scores.
    """
    def __init__(self, db: Session):
        self.db = db

    def store_assessment(self, asset_id: str, eval_result: Dict[str, Any]) -> RiskAssessment:
        factors = eval_result.get("factors", {})
        mosca = eval_result.get("mosca", {})
        
        level_str = eval_result.get("risk_level", "LOW")
        try:
            r_level = RiskLevel(level_str)
        except ValueError:
            r_level = RiskLevel.LOW

        ra = RiskAssessment(
            asset_id=asset_id,
            risk_score=eval_result.get("risk_score", 0.0),
            risk_level=r_level,
            quantum_exposure=factors.get("quantum_exposure", 0.0),
            quantum_vulnerability_score=factors.get("quantum_exposure", 0.0),
            data_sensitivity_score=factors.get("data_sensitivity", 0.0),
            business_criticality_score=factors.get("business_criticality", 0.0),
            mosca_factor_score=factors.get("mosca_score", 0.0),
            exposure_score=factors.get("quantum_exposure", 0.0),
            migration_complexity_score=factors.get("migration_complexity", 0.0),
            lifetime_exposure_score=factors.get("lifetime_exposure", 0.0),
            confidence_score=eval_result.get("confidence_score", 1.0),
            quantum_status=eval_result.get("quantum_status"),
            crypto_purpose=eval_result.get("crypto_purpose"),
            mosca_status=mosca.get("mosca_status"),
            quantum_threat_horizon=mosca.get("quantum_threat_horizon", 2033),
            priority=eval_result.get("priority", "LOW"),
            explanation=eval_result.get("explanation"),
            rationale=eval_result.get("rationale"),
            factors=factors
        )
        self.db.add(ra)
        self.db.commit()
        self.db.refresh(ra)

        # Store associated threat scenarios
        for sc in eval_result.get("threat_scenarios", []):
            stype_str = sc.get("scenario_type", "MODERATE")
            try:
                stype = ThreatScenarioType(stype_str)
            except ValueError:
                stype = ThreatScenarioType.MODERATE

            ts = ThreatScenario(
                asset_id=asset_id,
                name=sc.get("name", "Threat Scenario"),
                scenario_type=stype,
                quantum_threat_horizon_year=mosca.get("quantum_threat_horizon", 2033),
                severity=sc.get("severity", "HIGH"),
                urgency=sc.get("urgency", "HIGH"),
                description=sc.get("description"),
                rationale=sc.get("rationale"),
                evidence=sc.get("evidence", [])
            )
            self.db.add(ts)
        self.db.commit()

        return ra

    def store_assessments_bulk(self, assessments_data: List[tuple]) -> List[RiskAssessment]:
        ra_objs = []
        ts_objs = []
        for asset_id, eval_result in assessments_data:
            factors = eval_result.get("factors", {})
            mosca = eval_result.get("mosca", {})
            
            level_str = eval_result.get("risk_level", "LOW")
            try:
                r_level = RiskLevel(level_str)
            except ValueError:
                r_level = RiskLevel.LOW

            ra = RiskAssessment(
                asset_id=asset_id,
                risk_score=eval_result.get("risk_score", 0.0),
                risk_level=r_level,
                quantum_exposure=factors.get("quantum_exposure", 0.0),
                quantum_vulnerability_score=factors.get("quantum_exposure", 0.0),
                data_sensitivity_score=factors.get("data_sensitivity", 0.0),
                business_criticality_score=factors.get("business_criticality", 0.0),
                mosca_factor_score=factors.get("mosca_score", 0.0),
                exposure_score=factors.get("quantum_exposure", 0.0),
                migration_complexity_score=factors.get("migration_complexity", 0.0),
                lifetime_exposure_score=factors.get("lifetime_exposure", 0.0),
                confidence_score=eval_result.get("confidence_score", 1.0),
                quantum_status=eval_result.get("quantum_status"),
                crypto_purpose=eval_result.get("crypto_purpose"),
                mosca_status=mosca.get("mosca_status"),
                quantum_threat_horizon=mosca.get("quantum_threat_horizon", 2033),
                priority=eval_result.get("priority", "LOW"),
                explanation=eval_result.get("explanation"),
                rationale=eval_result.get("rationale"),
                factors=factors
            )
            ra_objs.append(ra)

            for sc in eval_result.get("threat_scenarios", []):
                stype_str = sc.get("scenario_type", "MODERATE")
                try:
                    stype = ThreatScenarioType(stype_str)
                except ValueError:
                    stype = ThreatScenarioType.MODERATE

                ts = ThreatScenario(
                    asset_id=asset_id,
                    name=sc.get("name", "Threat Scenario"),
                    scenario_type=stype,
                    quantum_threat_horizon_year=mosca.get("quantum_threat_horizon", 2033),
                    severity=sc.get("severity", "HIGH"),
                    urgency=sc.get("urgency", "HIGH"),
                    description=sc.get("description"),
                    rationale=sc.get("rationale"),
                    evidence=sc.get("evidence", [])
                )
                ts_objs.append(ts)

        self.db.add_all(ra_objs)
        self.db.add_all(ts_objs)
        self.db.commit()
        return ra_objs

    def get(self, assessment_id: str) -> Optional[RiskAssessment]:
        return self.db.query(RiskAssessment).filter(RiskAssessment.id == assessment_id).first()

    def get_latest_for_asset(self, asset_id: str) -> Optional[RiskAssessment]:
        return (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.asset_id == asset_id)
            .order_by(desc(RiskAssessment.created_at))
            .first()
        )

    def get_by_asset(self, asset_id: str) -> List[RiskAssessment]:
        return (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.asset_id == asset_id)
            .order_by(desc(RiskAssessment.created_at))
            .all()
        )

    def list_assessments(
        self,
        project_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        quantum_status: Optional[str] = None,
        scenario: Optional[str] = None,
        minimum_score: Optional[float] = None
    ) -> List[RiskAssessment]:
        query = self.db.query(RiskAssessment).join(CryptoAsset).join(Scan)

        if project_id:
            query = query.filter(Scan.project_id == project_id)

        if risk_level:
            query = query.filter(RiskAssessment.risk_level == risk_level)

        if quantum_status:
            query = query.filter(RiskAssessment.quantum_status == quantum_status)

        if minimum_score is not None:
            query = query.filter(RiskAssessment.risk_score >= minimum_score)

        if scenario:
            query = query.join(ThreatScenario, ThreatScenario.asset_id == CryptoAsset.id).filter(
                ThreatScenario.scenario_type == scenario
            )

        return query.order_by(desc(RiskAssessment.risk_score)).all()

    def get_threat_scenarios_for_asset(self, asset_id: str) -> List[ThreatScenario]:
        return self.db.query(ThreatScenario).filter(ThreatScenario.asset_id == asset_id).all()
