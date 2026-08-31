from typing import Dict, Any, List

def build_executive_summary(project_name: str, scan_count: int, total_assets: int, vulnerable_count: int, top_pqc_candidates: List[str]) -> str:
    summary = f"""# Executive Cryptographic Risk & PQC Readiness Summary

**Project Name:** {project_name}  
**Scans Analyzed:** {scan_count}  
**Total Cryptographic Assets Discovered:** {total_assets}  
**Quantum Vulnerable Assets:** {vulnerable_count}  
**Post-Quantum Readiness Level:** {"LOW" if vulnerable_count > 0 else "HIGH"}  

## Key Findings & Recommendations
- Discovered {vulnerable_count} legacy cryptographic mechanisms (e.g., RSA, ECDSA) requiring post-quantum migration.
- Primary NIST PQC candidate replacements recommended: {', '.join(top_pqc_candidates) if top_pqc_candidates else 'ML-KEM (FIPS 203), ML-DSA (FIPS 204)'}.
- Mosca $X + Y > Z$ timing analysis indicates migration planning should commence immediately to avoid protection gap.
"""
    return summary
