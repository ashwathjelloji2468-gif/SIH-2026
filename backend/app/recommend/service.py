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
        self.asset_repo = AssetRepository(db) if (db and hasattr(AssetRepository, "__call__")) else None
        self.risk_repo = RiskRepository(db) if (db and hasattr(RiskRepository, "__call__")) else None
        self.rec_repo = RecommendationRepository(db) if (db and hasattr(RecommendationRepository, "__call__")) else None
        self.engine = RecommendationEngine()

    def _extract_asset_context(self, asset: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = dict(context) if context else {}
        if not asset:
            return ctx

        if "text_length_bytes" in ctx or "payload_size_bytes" in ctx or "message_size_bytes" in ctx:
            return ctx

        extra = getattr(asset, "extra_metadata", None)
        if isinstance(extra, dict):
            for k in ["text_length_bytes", "text_size_kb", "payload_size_bytes", "message_size_bytes"]:
                if k in extra and extra[k] is not None:
                    ctx[k] = extra[k]

        evidence_items = getattr(asset, "evidence_items", []) or []
        for ev in evidence_items:
            prov = getattr(ev, "provenance", None)
            if isinstance(prov, dict):
                for k in ["text_length_bytes", "text_size_kb", "payload_size_bytes", "message_size_bytes"]:
                    if k in prov and prov[k] is not None and k not in ctx:
                        ctx[k] = prov[k]

            if "text_length_bytes" not in ctx and "payload_size_bytes" not in ctx:
                matched = getattr(ev, "matched_text", None) or getattr(ev, "excerpt", None)
                if matched and isinstance(matched, str) and len(matched.strip()) > 0:
                    ctx["text_length_bytes"] = len(matched.encode("utf-8"))

        scan = getattr(asset, "scan", None)
        if scan:
            project = getattr(scan, "project", None)
            if project:
                b_ctx = getattr(project, "business_context", None)
                if isinstance(b_ctx, dict):
                    for k in ["text_length_bytes", "payload_size_bytes", "message_size_bytes"]:
                        if k in b_ctx and b_ctx[k] is not None and k not in ctx:
                            ctx[k] = b_ctx[k]

        if "text_length_bytes" not in ctx and "payload_size_bytes" not in ctx and "message_size_bytes" not in ctx:
            ctx["text_length_bytes"] = 1024

        return ctx

    def recommend_asset(self, asset_id: str, force_regeneration: bool = False, profile: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.asset_repo:
            raise RuntimeError("Database repository unavailable.")

        asset = self.asset_repo.get(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found.")

        eff_profile = profile
        if not eff_profile and hasattr(asset, "scan") and asset.scan and hasattr(asset.scan, "project") and asset.scan.project:
            eff_profile = getattr(asset.scan.project, "default_migration_profile", "BALANCED")
        if not eff_profile:
            eff_profile = "BALANCED"

        # Load latest RiskAssessment and ThreatScenarios if risk_repo is available
        ra = self.risk_repo.get_latest_for_asset(asset_id) if (self.risk_repo and hasattr(self.risk_repo, "get_latest_for_asset")) else None
        threats = self.risk_repo.get_threat_scenarios_for_asset(asset_id) if (self.risk_repo and hasattr(self.risk_repo, "get_threat_scenarios_for_asset")) else []

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
                res_dict = self._recommendation_to_dict(existing, asset, ra, threat_dict_list)
                res_dict["profile"] = eff_profile
                try:
                    from app.audit.integration import audit_recommendation_snapshot
                    audit_recommendation_snapshot(res_dict, asset_id=str(asset_id))
                except Exception:
                    pass
                return res_dict

        detector_names = [e.detector_name for e in (getattr(asset, "evidence_items", []) or [])]

        r_level_attr = getattr(ra, "risk_level", "LOW") if ra else "LOW"
        risk_level = r_level_attr.value if hasattr(r_level_attr, "value") else str(r_level_attr or "LOW")
        risk_score = ra.risk_score if ra else 0.0
        complexity = getattr(ra, "migration_complexity_score", 50.0) if ra else 50.0

        comp_str = "HIGH" if complexity >= 75.0 else ("MEDIUM" if complexity >= 40.0 else "LOW")

        eff_context = self._extract_asset_context(asset, context)

        rec_eval = self.engine.generate_recommendation(
            algorithm_name=asset.algorithm_name,
            purpose=asset.purpose,
            quantum_safety=asset.quantum_safety,
            risk_level=risk_level,
            risk_score=risk_score,
            threat_scenarios=threat_dict_list,
            migration_complexity=comp_str,
            detector_names=detector_names,
            profile=eff_profile,
            asset_location=getattr(asset, "location", None),
            asset_line_number=getattr(asset, "line_number", None),
            asset_name=getattr(asset, "name", None),
            context=eff_context
        )

        rec_record = self.rec_repo.store_recommendation(
            asset_id=asset_id,
            rec_data=rec_eval,
            risk_assessment_id=ra.id if ra else None
        ) if self.rec_repo else None

        if rec_record:
            res_dict = self._recommendation_to_dict(rec_record, asset, ra, threat_dict_list)
            res_dict["profile"] = eff_profile
        else:
            rec_eval["asset_id"] = asset_id
            rec_eval["asset_name"] = asset.name
            res_dict = rec_eval

        try:
            from app.audit.integration import audit_recommendation_snapshot
            audit_recommendation_snapshot(res_dict, asset_id=str(asset_id))
        except Exception:
            pass

        return res_dict

    def recommend_project(self, project_id: str, force_regeneration: bool = False, profile: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.asset_repo:
            raise RuntimeError("Database repository unavailable.")
        assets = self.asset_repo.get_by_project(project_id)
        if not assets:
            return []

        eff_profile = profile
        if not eff_profile and self.db:
            from app.models.db_models import Project
            proj = self.db.query(Project).filter(Project.id == project_id).first()
            if proj:
                eff_profile = getattr(proj, "default_migration_profile", "BALANCED")
        if not eff_profile:
            eff_profile = "BALANCED"

        asset_ids = [a.id for a in assets]
        existing_map = {}
        if not force_regeneration and self.rec_repo:
            existing_recs = self.rec_repo.list_recommendations(project_id=project_id)
            for r in existing_recs:
                if r.asset_id not in existing_map:
                    existing_map[r.asset_id] = r

        risk_map = {}
        threats_map = {}
        if self.db and self.risk_repo:
            from app.models.db_models import RiskAssessment, ThreatScenario
            all_ras = self.db.query(RiskAssessment).filter(RiskAssessment.asset_id.in_(asset_ids)).all()
            for ra in all_ras:
                if ra.asset_id not in risk_map or (hasattr(ra, 'created_at') and getattr(ra, 'created_at') > getattr(risk_map[ra.asset_id], 'created_at')):
                    risk_map[ra.asset_id] = ra

            all_ts = self.db.query(ThreatScenario).filter(ThreatScenario.asset_id.in_(asset_ids)).all()
            for ts in all_ts:
                threats_map.setdefault(ts.asset_id, []).append(ts)

        to_store = []
        results = []

        for asset in assets:
            ra = risk_map.get(asset.id)
            threats = threats_map.get(asset.id, [])
            threat_dict_list = [
                {
                    "id": getattr(ts, "id", None),
                    "scenario_type": ts.scenario_type.value if hasattr(ts, "scenario_type") and hasattr(ts.scenario_type, "value") else str(getattr(ts, "scenario_type", "MODERATE")),
                    "name": getattr(ts, "name", "Threat Scenario"),
                    "description": getattr(ts, "description", "")
                } for ts in threats
            ]

            if not force_regeneration and asset.id in existing_map:
                existing = existing_map[asset.id]
                res_dict = self._recommendation_to_dict(existing, asset, ra, threat_dict_list)
                try:
                    from app.audit.integration import audit_recommendation_snapshot
                    audit_recommendation_snapshot(res_dict, asset_id=str(asset.id))
                except Exception:
                    pass
                results.append(res_dict)
                continue

            detector_names = [e.detector_name for e in (getattr(asset, "evidence_items", []) or [])]
            r_level_attr = getattr(ra, "risk_level", "LOW") if ra else "LOW"
            risk_level = r_level_attr.value if hasattr(r_level_attr, "value") else str(r_level_attr or "LOW")
            risk_score = ra.risk_score if ra else 0.0
            complexity = getattr(ra, "migration_complexity_score", 50.0) if ra else 50.0
            comp_str = "HIGH" if complexity >= 75.0 else ("MEDIUM" if complexity >= 40.0 else "LOW")

            eff_context = self._extract_asset_context(asset, context)

            rec_eval = self.engine.generate_recommendation(
                algorithm_name=asset.algorithm_name,
                purpose=asset.purpose,
                quantum_safety=asset.quantum_safety,
                risk_level=risk_level,
                risk_score=risk_score,
                threat_scenarios=threat_dict_list,
                migration_complexity=comp_str,
                detector_names=detector_names,
                profile=eff_profile,
                asset_location=getattr(asset, "location", None),
                asset_line_number=getattr(asset, "line_number", None),
                asset_name=getattr(asset, "name", None),
                context=eff_context
            )
            to_store.append((asset.id, rec_eval, ra.id if ra else None, asset, ra, threat_dict_list))

        if to_store and self.rec_repo and hasattr(self.rec_repo, "store_recommendations_bulk"):
            bulk_payload = [(item[0], item[1], item[2]) for item in to_store]
            rec_records = self.rec_repo.store_recommendations_bulk(bulk_payload)
            for idx, rec_record in enumerate(rec_records):
                item = to_store[idx]
                res_dict = self._recommendation_to_dict(rec_record, item[3], item[4], item[5])
                try:
                    from app.audit.integration import audit_recommendation_snapshot
                    audit_recommendation_snapshot(res_dict, asset_id=str(item[0]))
                except Exception:
                    pass
                results.append(res_dict)
        elif to_store:
            for item in to_store:
                rec_eval = item[1]
                rec_eval["asset_id"] = item[0]
                rec_eval["asset_name"] = item[3].name
                try:
                    from app.audit.integration import audit_recommendation_snapshot
                    audit_recommendation_snapshot(rec_eval, asset_id=str(item[0]))
                except Exception:
                    pass
                results.append(rec_eval)

        return results

    def get_project_recommendation_summary(self, project_id: str, force_regeneration: bool = False, profile: Optional[str] = None) -> Dict[str, Any]:
        if not self.asset_repo:
            raise RuntimeError("Database repository unavailable.")
        assets = self.asset_repo.get_by_project(project_id)
        total_assets = len(assets)

        rec_list = self.recommend_project(project_id, force_regeneration=force_regeneration, profile=profile)

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
            if "PQC_REPLACEMENT" in cat or "MIGRATE" in cat:
                category_counts["pqc_replacement_count"] += 1
            elif "HYBRID" in cat:
                category_counts["hybrid_count"] += 1
            elif "RETAIN" in cat:
                category_counts["retain_crypto_count"] += 1
            elif "MANUAL" in cat:
                category_counts["manual_review_count"] += 1
            else:
                category_counts["no_action_required_count"] += 1

            algo = str(rec.get("recommended_algorithm", "") or rec.get("target_pqc_candidate", ""))
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
        tradeoffs = getattr(rec, "tradeoffs", None) or {}
        return {
            "id": getattr(rec, "id", None),
            "asset_id": getattr(rec, "asset_id", None),
            "asset_name": asset.name if asset else "Unknown Asset",
            "algorithm_name": asset.algorithm_name if asset else "Unknown",
            "location": asset.location if asset else "",
            "line_number": asset.line_number if asset else None,
            "crypto_purpose": asset.purpose.value if (asset and hasattr(asset.purpose, "value")) else "UNKNOWN",
            "quantum_status": asset.quantum_safety.value if (asset and hasattr(asset.quantum_safety, "value")) else "UNKNOWN",
            "risk_assessment_id": getattr(rec, "risk_assessment_id", None) or (ra.id if ra else None),
            "risk_score": ra.risk_score if ra else 0.0,
            "risk_level": ra.risk_level.value if (ra and hasattr(ra.risk_level, "value")) else "LOW",
            "target_pqc_candidate": getattr(rec, "target_pqc_candidate", "ML-KEM"),
            "recommended_algorithm": getattr(rec, "recommended_algorithm", None) or getattr(rec, "target_pqc_candidate", "ML-KEM"),
            "alternative_algorithm": getattr(rec, "alternative_algorithm", None),
            "category": rec.category.value if hasattr(rec, "category") and hasattr(rec.category, "value") else str(getattr(rec, "category", "PQC_REPLACEMENT")),
            "priority": getattr(rec, "priority", "LOW") or "LOW",
            "standard_status": rec.standard_status.value if hasattr(rec, "standard_status") and hasattr(rec.standard_status, "value") else str(getattr(rec, "standard_status", "FINAL_STANDARD")),
            "rationale": getattr(rec, "rationale", ""),
            "compatibility_notes": getattr(rec, "compatibility_notes", None),
            "performance_notes": getattr(rec, "performance_notes", None),
            "latency_impact": getattr(rec, "latency_impact", None) or tradeoffs.get("latency_impact", "Minimal latency impact."),
            "cost_impact": getattr(rec, "cost_impact", None) or tradeoffs.get("cost_impact", "Standard migration cost."),
            "latency_level": getattr(rec, "latency_level", None) or tradeoffs.get("latency_level", "LOW"),
            "cost_level": getattr(rec, "cost_level", None) or tradeoffs.get("cost_level", "MEDIUM"),
            "tradeoffs": tradeoffs,
            "threat_scenarios": threats or getattr(rec, "threat_scenarios", []) or [],
            "migration_notes": getattr(rec, "migration_notes", None),
            "migration_complexity": getattr(rec, "migration_complexity", "MEDIUM") or "MEDIUM",
            "confidence": getattr(rec, "confidence", 1.0),
            "kb_version": getattr(rec, "kb_version", "2026.3.0-NIST-PQC") or "2026.3.0-NIST-PQC",
            "created_at": rec.created_at.isoformat() if (hasattr(rec, "created_at") and rec.created_at and hasattr(rec.created_at, "isoformat")) else str(getattr(rec, "created_at", ""))
        }
