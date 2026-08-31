import platform
from datetime import datetime, timezone
from typing import Dict, Any

def create_provenance(scan_id: str, detector_name: str, detector_version: str) -> Dict[str, Any]:
    return {
        "scan_id": scan_id,
        "detector_name": detector_name,
        "detector_version": detector_version,
        "environment": f"Python {platform.python_version()}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
