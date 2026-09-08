from typing import Dict, Any, List

DEFAULT_CONFIDENTIALITY_HORIZON_YEARS = 20

DOMAIN_X_BASELINES: Dict[str, Dict[str, Any]] = {
    "banking_finance": {
        "key": "banking_finance",
        "title": "Banking & Finance",
        "baseline_x_years": 15,
        "description": "Financial records, transaction logs, payment credentials, and banking data.",
        "compliance_references": ["PCI-DSS", "GLBA", "SOX"],
        "keywords": [
            "bank", "banking", "finance", "financial", "payment", "transaction", "ledger",
            "pci", "credit_card", "account", "balance", "swift", "clearing", "vault"
        ]
    },
    "government_defense": {
        "key": "government_defense",
        "title": "Government & Defense",
        "baseline_x_years": 50,
        "description": "Classified records, defense communication, intelligence, and state security archives.",
        "compliance_references": ["FedRAMP", "DISA STIG", "NIST SP 800-53"],
        "keywords": [
            "gov", "government", "defense", "military", "classified", "intelligence", "tactical",
            "dod", "security_clearance", "sovereign", "diplomatic", "state"
        ]
    },
    "healthcare": {
        "key": "healthcare",
        "title": "Healthcare & Life Sciences",
        "baseline_x_years": 30,
        "description": "Electronic health records (EHR), genomic data, medical device data, and patient history.",
        "compliance_references": ["HIPAA", "HITECH", "GDPR Art 9"],
        "keywords": [
            "health", "healthcare", "medical", "patient", "ehr", "emr", "clinical", "hospital",
            "pharmacy", "genomic", "hipaa", "diagnosis", "prescription"
        ]
    },
    "telecom": {
        "key": "telecom",
        "title": "Telecommunications",
        "baseline_x_years": 10,
        "description": "Call detail records (CDR), network routing tables, subscriber telemetry, and signaling data.",
        "compliance_references": ["FCC", "ePrivacy", "CISA"],
        "keywords": [
            "telecom", "telecommunication", "cellular", "5g", "lte", "carrier", "cdr",
            "sip", "voip", "signaling", "subscriber", "network_operator"
        ]
    },
    "energy_utilities": {
        "key": "energy_utilities",
        "title": "Energy & Critical Utilities",
        "baseline_x_years": 20,
        "description": "Grid infrastructure telemetry, SCADA systems, smart meter data, and utility controls.",
        "compliance_references": ["NERC CIP", "IEC 62443"],
        "keywords": [
            "energy", "utility", "power_grid", "scada", "smart_meter", "electric", "substation",
            "nuclear", "pipeline", "oil_gas", "water_treatment"
        ]
    },
    "aviation_transportation": {
        "key": "aviation_transportation",
        "title": "Aviation & Transportation",
        "baseline_x_years": 20,
        "description": "Avionics telemetry, flight navigation, maritime routing, and logistics management.",
        "compliance_references": ["ICAO", "FAA DO-178C", "TSA"],
        "keywords": [
            "aviation", "aircraft", "flight", "avionics", "maritime", "shipping", "logistics",
            "railway", "transit", "navigation", "ads_b"
        ]
    },
    "cloud_saas": {
        "key": "cloud_saas",
        "title": "Cloud & SaaS Infrastructure",
        "baseline_x_years": 10,
        "description": "Tenant data, identity provider tokens, API gateways, and cloud service backbones.",
        "compliance_references": ["SOC 2 Type II", "ISO 27001", "CSA STAR"],
        "keywords": [
            "cloud", "saas", "tenant", "multi_tenant", "identity", "oauth", "iam", "k8s",
            "kubernetes", "docker", "aws", "azure", "gcp", "api_gateway"
        ]
    },
    "iot_embedded": {
        "key": "iot_embedded",
        "title": "IoT & Embedded Devices",
        "baseline_x_years": 20,
        "description": "Firmware signatures, edge node telemetry, automotive ECUs, and smart home hubs.",
        "compliance_references": ["ETSI EN 303 645", "NIST IR 8259"],
        "keywords": [
            "iot", "embedded", "firmware", "microcontroller", "ecu", "automotive", "sensor",
            "ble", "zigbee", "mqtt", "rtos", "hardware"
        ]
    },
    "legal_pharma": {
        "key": "legal_pharma",
        "title": "Legal & Pharmaceuticals",
        "baseline_x_years": 30,
        "description": "Patents, intellectual property, clinical trials, contract archives, and legal discovery.",
        "compliance_references": ["FDA 21 CFR Part 11", "USPTO", "EMA"],
        "keywords": [
            "legal", "patent", "intellectual_property", "pharma", "pharmaceutical", "trial",
            "drug_discovery", "contract", "compliance", "litigation"
        ]
    },
    "software_supply_chain": {
        "key": "software_supply_chain",
        "title": "Software Supply Chain & DevSecOps",
        "baseline_x_years": 10,
        "description": "Build pipelines, package repositories, code signing keys, and artifact stores.",
        "compliance_references": ["SLSA Level 4", "NIST SSDF", "Executive Order 14028"],
        "keywords": [
            "supply_chain", "pipeline", "ci_cd", "repository", "artifact", "package_manager",
            "npm", "pypi", "maven", "build_system", "signing_key"
        ]
    },
    "media_social": {
        "key": "media_social",
        "title": "Media Streaming & Social Media",
        "baseline_x_years": 7,
        "description": "Content distribution DRM, user interaction logs, media feeds, and messaging metadata.",
        "compliance_references": ["COPPA", "GDPR", "CCPA"],
        "keywords": [
            "media", "streaming", "video", "audio", "social", "chat", "feed", "drm",
            "content", "messaging", "broadcast"
        ]
    }
}

def get_domain_baseline(domain_key: str) -> Dict[str, Any]:
    return DOMAIN_X_BASELINES.get(domain_key, {
        "key": "default_fallback",
        "title": "General / Unclassified Domain",
        "baseline_x_years": DEFAULT_CONFIDENTIALITY_HORIZON_YEARS,
        "description": "Conservative default confidentiality planning horizon for unclassified repositories.",
        "compliance_references": ["NIST SP 800-57"],
        "keywords": []
    })
