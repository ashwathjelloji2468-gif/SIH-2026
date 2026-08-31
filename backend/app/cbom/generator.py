from typing import Dict, Any
from app.cbom.cyclonedx_adapter import generate_cbom_json

class CBOMGenerator:
    def create_cbom(self, scan, assets) -> Dict[str, Any]:
        return generate_cbom_json(scan, assets)

class CBOMValidator:
    def validate(self, cbom_json: Dict[str, Any]) -> bool:
        return (
            cbom_json.get("bomFormat") == "CycloneDX" and
            cbom_json.get("specVersion") == "1.5" and
            "components" in cbom_json
        )
