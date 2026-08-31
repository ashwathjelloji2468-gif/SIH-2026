from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.risk.threat_scenarios import THREAT_SCENARIOS
from app.models.schemas import ThreatScenarioCreate, ThreatScenarioResponse

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

@router.get("", response_model=List[Dict[str, Any]])
def list_scenarios():
    return [{"id": k.value, **v} for k, v in THREAT_SCENARIOS.items()]

@router.post("")
def create_scenario(scenario: ThreatScenarioCreate):
    return {"id": "custom-1", **scenario.model_dump()}

@router.get("/{scenario_id}/impact")
def get_scenario_impact(scenario_id: str):
    return {
        "scenario_id": scenario_id,
        "impact_summary": f"Threat horizon adjusted for scenario {scenario_id}. Recalculating Mosca protection gaps across active projects."
    }
