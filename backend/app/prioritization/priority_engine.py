from typing import Dict, Any, List, Tuple
from app.models.enums import RiskLevel, QuantumSafety

CRITICALITY_WEIGHTS = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
    "UNKNOWN": 0
}

MOSCA_WEIGHTS = {
    "DEADLINE_BREACH": 5,
    "DEADLINE_RISK": 4,
    "MIGRATION_REQUIRED": 3,
    "URGENT": 3,
    "SAFE_TIMELINE": 1,
    "UNKNOWN": 0
}

TIER_WEIGHTS = {
    "P1": 1,
    "P2": 2,
    "P3": 3
}

class PriorityEngine:
    """
    Deterministic Migration Prioritization Engine (Stage 6).

    Consumes existing outputs from Cryptographic Discovery, Classification,
    Business Criticality, Quantum Risk Assessment, and Mosca Engine without
    recalculating technical scores.
    """
    def categorize_tier(
        self,
        risk_score: float,
        risk_level: str,
        mosca_status: str,
        effective_criticality: str,
        user_focus: bool = False
    ) -> str:
        r_level_upper = (risk_level or "LOW").upper()
        m_status_upper = (mosca_status or "UNKNOWN").upper()
        crit_upper = (effective_criticality or "LOW").upper()

        is_high_risk = r_level_upper in ["CRITICAL", "HIGH"] or risk_score >= 60.0
        is_urgent_mosca = m_status_upper in ["DEADLINE_RISK", "MIGRATION_REQUIRED", "DEADLINE_BREACH", "URGENT"]
        is_high_crit = crit_upper in ["CRITICAL", "HIGH"]

        # P1 Rule: High/Critical Risk AND at least one strong organizational urgency factor
        if is_high_risk and (is_urgent_mosca or is_high_crit or (user_focus and risk_score >= 40.0)):
            return "P1"

        # P2 Rule: Moderate/High Risk or Medium business impact
        if r_level_upper in ["CRITICAL", "HIGH", "MODERATE", "MEDIUM"] or risk_score >= 25.0 or user_focus:
            return "P2"

        # P3 Rule: Low risk / monitor later
        return "P3"

    def rank_assets(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deterministically ranks assets:
        1. Priority Tier (P1 before P2 before P3)
        2. Higher canonical risk_score (desc)
        3. Higher Mosca urgency weight (desc)
        4. Higher effective planning criticality weight (desc)
        5. User Focus (true before false)
        """
        def sort_key(item: Dict[str, Any]) -> Tuple[int, float, int, int, int]:
            tier = item.get("priority_tier", "P3")
            tier_val = TIER_WEIGHTS.get(tier, 3)
            risk_score = float(item.get("technical_assessment", {}).get("risk_score", 0.0))
            
            m_status = item.get("technical_assessment", {}).get("mosca_status", "UNKNOWN").upper()
            mosca_weight = MOSCA_WEIGHTS.get(m_status, 0)
            
            crit = item.get("business_context", {}).get("effective_planning_criticality", "LOW").upper()
            crit_weight = CRITICALITY_WEIGHTS.get(crit, 0)
            
            u_focus = 1 if item.get("business_context", {}).get("user_focus", False) else 0

            return (
                tier_val,           # Ascending: P1=1, P2=2, P3=3
                -risk_score,        # Descending: higher risk score first
                -mosca_weight,      # Descending: higher Mosca urgency first
                -crit_weight,       # Descending: higher business criticality first
                -u_focus            # Descending: user focus first
            )

        sorted_items = sorted(items, key=sort_key)
        for idx, item in enumerate(sorted_items, start=1):
            item["priority_rank"] = idx

        return sorted_items

    def generate_reasons(
        self,
        risk_score: float,
        risk_level: str,
        mosca_status: str,
        system_criticality: str,
        effective_criticality: str,
        user_focus: bool,
        is_adjusted: bool,
        adjustment_reason: str = None
    ) -> List[str]:
        reasons = []

        if (risk_level or "").upper() in ["CRITICAL", "HIGH"] or risk_score >= 60.0:
            reasons.append(f"High quantum risk score ({risk_score:.1f}/100, level {risk_level})")
        elif risk_score >= 25.0:
            reasons.append(f"Moderate quantum risk score ({risk_score:.1f}/100)")
        else:
            reasons.append(f"Low quantum risk score ({risk_score:.1f}/100)")

        if (mosca_status or "").upper() in ["DEADLINE_RISK", "MIGRATION_REQUIRED", "DEADLINE_BREACH", "URGENT"]:
            reasons.append(f"Mosca migration window is {mosca_status}")

        if (effective_criticality or "").upper() in ["CRITICAL", "HIGH"]:
            reasons.append(f"High effective business criticality ({effective_criticality})")

        if user_focus:
            reasons.append("Flagged for organizational User Focus")

        if is_adjusted and adjustment_reason:
            reasons.append(f"Planning context adjusted: {adjustment_reason}")
        elif is_adjusted:
            reasons.append(f"Planning criticality adjusted from {system_criticality} to {effective_criticality}")

        return reasons
