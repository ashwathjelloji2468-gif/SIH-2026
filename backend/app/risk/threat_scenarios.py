from typing import Dict, Any
from app.models.enums import ThreatScenarioType

THREAT_SCENARIOS: Dict[str, Dict[str, Any]] = {
    ThreatScenarioType.CONSERVATIVE: {
        "name": "Conservative Quantum Threat Scenario",
        "quantum_threat_horizon_year": 2030,
        "description": "Assumes rapid quantum computing breakthroughs by 2030."
    },
    ThreatScenarioType.MODERATE: {
        "name": "Moderate Quantum Threat Scenario",
        "quantum_threat_horizon_year": 2035,
        "description": "Standard industry consensus timeline (2033-2035)."
    },
    ThreatScenarioType.AGGRESSIVE: {
        "name": "Aggressive Quantum Threat Scenario",
        "quantum_threat_horizon_year": 2040,
        "description": "Optimistic timeline for quantum hardware scaling."
    }
}
