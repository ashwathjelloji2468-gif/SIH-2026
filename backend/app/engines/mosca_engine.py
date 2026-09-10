"""
Unified Component-Wise Mosca Risk Engine for SENTRIQ.

Integrates:
- Layer 1: X Engine (Remaining confidentiality lifetime X)
- Layer 2: Y Engine (Migration planning assumption Y)
- Layer 3 & 4: Z Engine (Component-wise quantum threat deadline Z_i)
- Layer 5: Mosca Engine (Calculates M_i = X + Y - Z_i for every component)

Formula:
M_i = X + Y - Z_i

Interpretation:
- M_i > 5: CRITICAL (X + Y severely exceeds Z_i)
- 0 < M_i <= 5: HIGH (X + Y exceeds Z_i)
- -5 <= M_i <= 0: MEDIUM (Boundary / Plan Now)
- M_i < -5: LOW (Under current scenario, threat deadline is further away)
- Z_i non-numeric: moscaScore = None, status/urgency derived directly from Z Engine.

Maintains dual priority signals:
- Technical Quantum Urgency (derived from M_i / Z analysis)
- Business Priority (derived from asset criticality / data sensitivity)
"""

from typing import Dict, Any, List, Optional
from app.engines.x_engine import XEngine
from app.engines.y_engine import YEngine
from app.engines.z_engine import ZEngine
from app.config.mosca_config import MOSCA_CONFIG


class MoscaEngine:
    """
    Unified Component-Wise Mosca Risk Engine.
    Combines X, Y, and Z into explainable M_i = X + Y - Z_i assessments.
    """

    def __init__(self):
        self.x_engine = XEngine()
        self.y_engine = YEngine()
        self.z_engine = ZEngine()

    def evaluate_component_mosca(
        self,
        component: Dict[str, Any],
        user_x_years: Optional[int] = None,
        user_domain: Optional[str] = None,
        user_y_scenario: Optional[str] = None,
        quantum_horizon: Optional[int] = None,
        project_name: Optional[str] = None,
        description: Optional[str] = None,
        repository_url: Optional[str] = None,
        target_path: Optional[str] = None,
        folder_contexts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single cryptographic component under the Mosca theorem M_i = X + Y - Z_i.
        """
        # Determine location / folder path of the component
        location = str(component.get("location") or component.get("repository_path") or "")
        folder_path = None
        if location and "/" in location:
            folder_path = location.rsplit("/", 1)[0]

        # 1. Layer 1: X Engine Evaluation
        x_result = self.x_engine.evaluate_x(
            user_x_years=user_x_years,
            user_domain=user_domain,
            project_name=project_name,
            description=description,
            repository_url=repository_url,
            target_path=target_path,
            folder_path=folder_path,
            folder_contexts=folder_contexts
        )
        x_val = float(x_result["value"])

        # 2. Layer 2: Y Engine Evaluation
        y_result = self.y_engine.evaluate_y(user_scenario=user_y_scenario)
        y_val = float(y_result["value"])

        # 3. Layer 3 & 4: Z Engine Evaluation
        z_result = self.z_engine.evaluate_component(component, quantum_horizon=quantum_horizon)
        z_val = z_result.get("z_value") if z_result.get("status") != "NO_IMMEDIATE_QUANTUM_DEADLINE" else None
        z_horizon = z_result.get("z_planning_horizon_years") or z_val

        # 4. Layer 5: Mosca Calculation M_i = X + Y - Z_i
        mosca_score: Optional[float] = None
        technical_urgency: str = "LOW"

        if z_val is not None and isinstance(z_val, (int, float)):
            z_num = float(z_val)
            mosca_score = x_val + y_val - z_num

            if mosca_score > 5.0:
                technical_urgency = "CRITICAL"
                urgency_meaning = "Protection window X+Y severely exceeds component threat deadline Z_i."
            elif mosca_score > 0.0:
                technical_urgency = "HIGH"
                urgency_meaning = "Protection window X+Y exceeds component threat deadline Z_i."
            elif mosca_score >= -5.0:
                technical_urgency = "MEDIUM"
                urgency_meaning = "Protection window X+Y is near boundary with threat deadline Z_i (Plan Now)."
            else:
                technical_urgency = "LOW"
                urgency_meaning = "Under current assumptions, component threat deadline is further away."

            explanation = (
                f"Mosca equation calculation: M_i = X ({x_val:.0f}y) + Y ({y_val:.0f}y) - Z_i ({z_num:.0f}y) = {mosca_score:+.0f} years. "
                f"Result ({technical_urgency}): {urgency_meaning} "
                f"[X: {x_result['explanation']}] [Y: {y_result['explanation']}] [Z: {z_result['explanation']}]"
            )
        else:
            # Handle non-numeric Z_i (e.g. PQC, AES-256, Unknown, Requires Review)
            z_status = z_result.get("status", "REQUIRES_REVIEW")
            if z_status == "REQUIRES_REVIEW":
                technical_urgency = "REQUIRES_REVIEW"
                urgency_meaning = "Non-numeric Z_i. Manual cryptographic/policy review required."
            elif z_status == "REDUCED_BUT_ACCEPTABLE":
                technical_urgency = "LOW"
                urgency_meaning = "Symmetric/hash strength reduced under Grover search but meets policy thresholds."
            elif z_status == "NO_IMMEDIATE_QUANTUM_DEADLINE":
                technical_urgency = "LOW"
                urgency_meaning = "Post-quantum cryptographic primitive. No immediate CRQC deadline assigned."
            else:
                technical_urgency = "LOW"
                urgency_meaning = "Non-numeric Z_i deadline."

            explanation = (
                f"Mosca score not numeric (Z_i is non-numeric for {z_result['quantum_class']}). "
                f"Technical urgency ({technical_urgency}): {urgency_meaning} "
                f"Z status: {z_result['explanation']}"
            )

        # 5. Extract Business Priority (separate from technical urgency)
        raw_criticality = str(component.get("criticality") or component.get("purpose") or "MEDIUM").upper()
        if "CRITICAL" in raw_criticality or "ROOT" in raw_criticality:
            business_priority = "CRITICAL"
        elif "HIGH" in raw_criticality or "KEY_ESTABLISHMENT" in raw_criticality or "SIGNATURE" in raw_criticality:
            business_priority = "HIGH"
        elif "LOW" in raw_criticality:
            business_priority = "LOW"
        else:
            business_priority = "MEDIUM"

        comp_id = str(component.get("id") or component.get("component_id") or component.get("name") or "unknown-component")
        algo_name = str(component.get("algorithm_name") or component.get("algorithm") or component.get("primitive") or "UNKNOWN")

        return {
            "component_id": comp_id,
            "algorithm": algo_name,
            "location": location,
            "x": x_result,
            "y": y_result,
            "z": z_result,
            "mosca_score": mosca_score,
            "urgency": technical_urgency,
            "technical_urgency": technical_urgency,
            "business_priority": business_priority,
            "explanation": explanation
        }

    def evaluate_project_mosca(
        self,
        project: Any,
        assets: List[Any],
        user_x_years: Optional[int] = None,
        user_domain: Optional[str] = None,
        user_y_scenario: Optional[str] = None,
        quantum_horizon: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluate project-wide component-wise Mosca risk.
        """
        x_yr = user_x_years if user_x_years is not None else getattr(project, "user_x_years", None)
        u_dom = user_domain if user_domain is not None else getattr(project, "user_domain", None)
        y_scen = user_y_scenario if user_y_scenario is not None else getattr(project, "user_y_scenario", None)
        folder_contexts = getattr(project, "folder_contexts", None)
        project_name = getattr(project, "name", None)
        description = getattr(project, "description", None)
        repository_url = getattr(project, "repository_url", None)

        component_results = []
        for asset in assets:
            if hasattr(asset, "__dict__"):
                comp_dict = {
                    "id": str(getattr(asset, "id", "")),
                    "primitive": getattr(asset, "algorithm_name", ""),
                    "algorithm_name": getattr(asset, "algorithm_name", ""),
                    "key_size": getattr(asset, "key_size", None),
                    "location": getattr(asset, "location", ""),
                    "asset_type": str(getattr(asset, "asset_type", "")),
                    "purpose": str(getattr(asset, "purpose", ""))
                }
            elif isinstance(asset, dict):
                comp_dict = asset
            else:
                comp_dict = {"id": str(asset)}

            c_res = self.evaluate_component_mosca(
                component=comp_dict,
                user_x_years=x_yr,
                user_domain=u_dom,
                user_y_scenario=y_scen,
                quantum_horizon=quantum_horizon,
                project_name=project_name,
                description=description,
                repository_url=repository_url,
                folder_contexts=folder_contexts
            )
            component_results.append(c_res)

        # Aggregated statistics
        urgency_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "REQUIRES_REVIEW": 0
        }
        for r in component_results:
            u = r["urgency"]
            urgency_counts[u] = urgency_counts.get(u, 0) + 1

        total = len(component_results)
        critical_count = urgency_counts["CRITICAL"] + urgency_counts["HIGH"]

        return {
            "project_id": str(getattr(project, "id", "")),
            "project_name": str(getattr(project, "name", "")),
            "total_components": total,
            "critical_components": critical_count,
            "urgency_distribution": urgency_counts,
            "components": component_results,
            "explanation": (
                f"Component-wise Mosca Risk Engine evaluated M_i = X + Y - Z_i for {total} cryptographic components. "
                f"{critical_count} components require urgent or near-term migration action."
            )
        }
