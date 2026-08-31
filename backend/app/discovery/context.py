from typing import Dict, Any
from app.scanners.base import RawFinding

def enrich_finding_context(finding: RawFinding) -> Dict[str, Any]:
    return {
        "file_path": finding.file_path,
        "line_number": finding.line_number,
        "matched_text": finding.matched_text,
        "context_snippet": finding.context,
        "detector": finding.detector_name
    }
