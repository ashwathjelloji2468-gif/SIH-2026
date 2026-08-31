import json
from typing import Dict, Any

class CBOMExporter:
    def export_json(self, cbom_data: Dict[str, Any]) -> str:
        return json.dumps(cbom_data, indent=2)
