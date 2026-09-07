from typing import Dict, Any, List, Optional
from app.models.enums import ImpactLevel, RiskLevel
from app.graph.graph_builder import build_project_graph

class ImpactAnalyzer:
    """
    Deterministic Impact Analyzer for SENTRIQ.
    Calculates direct/indirect dependents, affected components/files/packages,
    and a deterministic impact score separate from quantum risk score.
    """
    def analyze_asset_impact(
        self,
        asset: Any,
        all_project_assets: Optional[List[Any]] = None,
        risk_assessment: Optional[Any] = None,
        recommendation: Optional[Any] = None
    ) -> Dict[str, Any]:

        asset_id = getattr(asset, "id", "unknown_asset")
        asset_name = getattr(asset, "name", "Crypto Asset")
        location = getattr(asset, "location", "unknown_file.py")
        asset_type_val = asset.asset_type.value if hasattr(asset, "asset_type") and hasattr(asset.asset_type, "value") else str(getattr(asset, "asset_type", "ALGORITHM"))

        # Build local context graph
        assets = all_project_assets or [asset]
        graph = build_project_graph(assets)

        asset_node_id = f"asset:{asset_id}"
        descendants = graph.analyze_impact(asset_node_id)

        # Derive Component Name from location
        parts = [p for p in location.replace("\\", "/").split("/") if p and p not in [".", ".."]]
        comp_name = parts[-2] if len(parts) > 1 else "Core"

        affected_components = list(set([comp_name]))
        affected_files = list(set([location]))
        affected_packages = []
        affected_services = []

        if asset_type_val == "DEPENDENCY":
            affected_packages.append(asset_name)

        # Count direct & indirect dependents from graph nodes
        direct_dependents = []
        indirect_dependents = []

        if asset_node_id in graph.graph:
            for neighbor in graph.graph.neighbors(asset_node_id):
                direct_dependents.append(neighbor)
            for node_id in descendants:
                if node_id not in direct_dependents and node_id != asset_node_id:
                    indirect_dependents.append(node_id)

        # Calculate Impact Score Factors (Total max 100)
        # Factor 1: Direct dependency score (max 30)
        direct_score = min(30.0, 15.0 + (len(direct_dependents) * 5.0))

        # Factor 2: Indirect dependency score (max 20)
        indirect_score = min(20.0, len(indirect_dependents) * 5.0)

        # Factor 3: Business Criticality score (max 20)
        crit_val = getattr(risk_assessment, "business_criticality_score", 50.0) if risk_assessment else 50.0
        criticality_score = (crit_val / 100.0) * 20.0

        # Factor 4: Risk Level score (max 20)
        r_level = risk_assessment.risk_level.value if (risk_assessment and hasattr(risk_assessment, "risk_level") and hasattr(risk_assessment.risk_level, "value")) else "LOW"
        r_level_upper = str(r_level).upper()
        if r_level_upper == "CRITICAL":
            risk_score_component = 20.0
        elif r_level_upper == "HIGH":
            risk_score_component = 15.0
        elif r_level_upper in ["MODERATE", "MEDIUM"]:
            risk_score_component = 10.0
        else:
            risk_score_component = 5.0

        # Factor 5: Migration Complexity score (max 10)
        complexity_str = getattr(recommendation, "migration_complexity", "MEDIUM") if recommendation else "MEDIUM"
        complexity_upper = str(complexity_str).upper()
        if complexity_upper == "HIGH":
            complexity_score_component = 10.0
        elif complexity_upper == "MEDIUM":
            complexity_score_component = 5.0
        else:
            complexity_score_component = 2.0

        total_impact_score = round(
            direct_score + indirect_score + criticality_score + risk_score_component + complexity_score_component,
            1
        )
        total_impact_score = min(100.0, max(0.0, total_impact_score))

        # Determine Impact Level
        if total_impact_score >= 75.0:
            impact_level = ImpactLevel.CRITICAL
        elif total_impact_score >= 50.0:
            impact_level = ImpactLevel.HIGH
        elif total_impact_score >= 25.0:
            impact_level = ImpactLevel.MODERATE
        else:
            impact_level = ImpactLevel.LOW

        project_id = getattr(getattr(asset, "scan", None), "project_id", "default_project")

        return {
            "asset_id": asset_id,
            "asset_name": asset_name,
            "impact_score": total_impact_score,
            "impact_level": impact_level.value if hasattr(impact_level, "value") else str(impact_level),
            "direct_dependents": direct_dependents,
            "indirect_dependents": indirect_dependents,
            "direct_dependents_count": len(direct_dependents),
            "indirect_dependents_count": len(indirect_dependents),
            "affected_components": affected_components,
            "affected_files": affected_files,
            "affected_packages": affected_packages,
            "affected_services": affected_services,
            "affected_project": project_id,
            "factors": {
                "direct_dependency_score": direct_score,
                "indirect_dependency_score": indirect_score,
                "business_criticality_score": round(criticality_score, 1),
                "risk_level_score": risk_score_component,
                "migration_complexity_score": complexity_score_component
            }
        }
