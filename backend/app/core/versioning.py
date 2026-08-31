from typing import Dict

SYSTEM_VERSIONS: Dict[str, str] = {
    "ecdat_software_version": "1.2.0",
    "scanner_rule_version": "2026.1.0",
    "cbom_schema_version": "1.6",
    "crypto_knowledge_base_version": "2026.3.0-NIST-PQC",
    "risk_model_version": "2.0-MOSCA",
    "threat_scenario_version": "1.1"
}

def get_system_versions() -> Dict[str, str]:
    return SYSTEM_VERSIONS.copy()
