from typing import List
from app.scanners.base import RawFinding

def deduplicate_findings(findings: List[RawFinding]) -> List[RawFinding]:
    seen = set()
    unique_findings = []

    for f in findings:
        key = (f.file_path, f.line_number, f.algorithm_name, f.asset_type)
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    return unique_findings
