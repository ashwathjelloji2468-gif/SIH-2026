from typing import Dict, Any

class CBOMValidator:
    def validate(self, cbom_json: Dict[str, Any]) -> bool:
        return (
            isinstance(cbom_json, dict) and
            cbom_json.get("bomFormat") == "CycloneDX" and
            cbom_json.get("specVersion") == "1.5" and
            "components" in cbom_json
        )
