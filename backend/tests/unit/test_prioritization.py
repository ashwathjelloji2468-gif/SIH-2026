import pytest
from app.prioritization.priority_engine import PriorityEngine

def test_priority_tier_p1():
    engine = PriorityEngine()
    tier = engine.categorize_tier(
        risk_score=92.5,
        risk_level="CRITICAL",
        mosca_status="DEADLINE_RISK",
        effective_criticality="HIGH",
        user_focus=False
    )
    assert tier == "P1"

def test_priority_tier_p2():
    engine = PriorityEngine()
    tier = engine.categorize_tier(
        risk_score=55.0,
        risk_level="HIGH",
        mosca_status="SAFE_TIMELINE",
        effective_criticality="MEDIUM",
        user_focus=False
    )
    assert tier == "P2"

def test_priority_tier_p3():
    engine = PriorityEngine()
    tier = engine.categorize_tier(
        risk_score=15.0,
        risk_level="LOW",
        mosca_status="SAFE_TIMELINE",
        effective_criticality="LOW",
        user_focus=False
    )
    assert tier == "P3"

def test_user_focus_rule():
    engine = PriorityEngine()
    
    risk_score = 45.0
    risk_level = "MODERATE"
    mosca_status = "SAFE_TIMELINE"
    system_crit = "MEDIUM"

    tier_normal = engine.categorize_tier(risk_score, risk_level, mosca_status, system_crit, user_focus=False)
    tier_focused = engine.categorize_tier(risk_score, risk_level, mosca_status, system_crit, user_focus=True)

    assert risk_score == 45.0
    assert risk_level == "MODERATE"
    assert mosca_status == "SAFE_TIMELINE"
    assert system_crit == "MEDIUM"
    assert tier_focused in ["P1", "P2"]

def test_user_adjustment_rule():
    engine = PriorityEngine()

    system_criticality = "HIGH"
    effective_criticality = "MEDIUM"
    adjustment_reason = "Component scheduled for decommissioning"

    tier = engine.categorize_tier(
        risk_score=65.0,
        risk_level="HIGH",
        mosca_status="SAFE_TIMELINE",
        effective_criticality=effective_criticality,
        user_focus=False
    )

    reasons = engine.generate_reasons(
        risk_score=65.0,
        risk_level="HIGH",
        mosca_status="SAFE_TIMELINE",
        system_criticality=system_criticality,
        effective_criticality=effective_criticality,
        user_focus=False,
        is_adjusted=True,
        adjustment_reason=adjustment_reason
    )

    assert system_criticality == "HIGH"
    assert effective_criticality == "MEDIUM"
    assert any("decommissioning" in r for r in reasons)

def test_deterministic_ranking():
    engine = PriorityEngine()

    items = [
        {
            "asset_id": "a1",
            "priority_tier": "P2",
            "technical_assessment": {"risk_score": 50.0, "mosca_status": "SAFE_TIMELINE"},
            "business_context": {"effective_planning_criticality": "MEDIUM", "user_focus": False}
        },
        {
            "asset_id": "a2",
            "priority_tier": "P1",
            "technical_assessment": {"risk_score": 85.0, "mosca_status": "MIGRATION_REQUIRED"},
            "business_context": {"effective_planning_criticality": "HIGH", "user_focus": False}
        },
        {
            "asset_id": "a3",
            "priority_tier": "P1",
            "technical_assessment": {"risk_score": 95.0, "mosca_status": "DEADLINE_RISK"},
            "business_context": {"effective_planning_criticality": "CRITICAL", "user_focus": True}
        },
        {
            "asset_id": "a4",
            "priority_tier": "P3",
            "technical_assessment": {"risk_score": 10.0, "mosca_status": "SAFE_TIMELINE"},
            "business_context": {"effective_planning_criticality": "LOW", "user_focus": False}
        }
    ]

    ranked = engine.rank_assets(items)

    assert ranked[0]["asset_id"] == "a3"  # P1, 95.0 risk score
    assert ranked[0]["priority_rank"] == 1

    assert ranked[1]["asset_id"] == "a2"  # P1, 85.0 risk score
    assert ranked[1]["priority_rank"] == 2

    assert ranked[2]["asset_id"] == "a1"  # P2
    assert ranked[2]["priority_rank"] == 3

    assert ranked[3]["asset_id"] == "a4"  # P3
    assert ranked[3]["priority_rank"] == 4
