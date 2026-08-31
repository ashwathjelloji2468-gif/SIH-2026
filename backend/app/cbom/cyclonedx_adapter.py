from datetime import datetime, timezone
from typing import List, Dict, Any
from app.models.db_models import CryptoAsset, Scan
from app.core.versioning import SYSTEM_VERSIONS

def generate_cbom_json(scan: Scan, assets: List[CryptoAsset]) -> Dict[str, Any]:
    components = []

    for asset in assets:
        component = {
            "type": "cryptographic",
            "name": asset.name,
            "bom-ref": f"cbom-{asset.id}",
            "cryptoProperties": {
                "assetType": asset.asset_type.value if hasattr(asset.asset_type, "value") else str(asset.asset_type),
                "algorithmProperties": {
                    "primitive": asset.purpose.value if hasattr(asset.purpose, "value") else str(asset.purpose),
                    "parameterSetIdentifier": str(asset.key_size) if asset.key_size else "default",
                    "cryptoFunctions": [asset.purpose.value if hasattr(asset.purpose, "value") else str(asset.purpose)]
                },
                "classicalSecurityLevel": asset.key_size or 128,
                "nistQuantumSecurityLevel": 1 if (hasattr(asset.quantum_safety, "value") and asset.quantum_safety.value == "QUANTUM_SAFE") else 0
            },
            "evidence": {
                "occurrences": [
                    {
                        "location": asset.location,
                        "line": asset.line_number or 1
                    }
                ]
            }
        }
        components.append(component)

    cbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{scan.id}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tools": [
                {
                    "vendor": "ECDAT",
                    "name": "SIH26164 Cryptographic Discovery Engine",
                    "version": SYSTEM_VERSIONS["ecdat_software_version"]
                }
            ],
            "component": {
                "type": "application",
                "name": f"Scan-{scan.id}",
                "version": "1.6"
            },
            "properties": [
                {"name": "ecdat:scanner_rule_version", "value": SYSTEM_VERSIONS["scanner_rule_version"]},
                {"name": "ecdat:kb_version", "value": SYSTEM_VERSIONS["crypto_knowledge_base_version"]}
            ]
        },
        "components": components
    }

    return cbom
