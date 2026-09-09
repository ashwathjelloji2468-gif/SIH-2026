from typing import List, Dict, Tuple
from app.scanners.base import RawFinding

STRUCTURAL_DETECTORS = {
    "PythonASTDetector",
    "JavaScriptTreeSitterDetector",
    "JavaTreeSitterDetector",
    "JavaScriptParser"
}

def deduplicate_findings(findings: List[RawFinding]) -> List[RawFinding]:
    """Deduplicates raw findings.

    Prioritizes structural AST/Tree-sitter findings over Regex findings when both match
    the same file location and algorithm.
    """
    seen: Dict[Tuple[str, int, str], RawFinding] = {}

    for f in findings:
        line_no = f.line_number or 0
        key = (f.file_path, line_no, f.algorithm_name)

        if key not in seen:
            seen[key] = f
        else:
            existing = seen[key]
            # Replace existing regex finding with structural finding if current is structural
            if f.detector_name in STRUCTURAL_DETECTORS and existing.detector_name not in STRUCTURAL_DETECTORS:
                seen[key] = f
            elif f.detector_name in STRUCTURAL_DETECTORS and existing.detector_name in STRUCTURAL_DETECTORS:
                if (f.key_size and not existing.key_size) or (f.extra_metadata and not existing.extra_metadata):
                    seen[key] = f

    return list(seen.values())

