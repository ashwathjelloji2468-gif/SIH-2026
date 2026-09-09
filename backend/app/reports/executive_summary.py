from typing import Dict, Any, List

def build_executive_summary(
    project_name: str,
    scan_count: int,
    total_assets: int,
    vulnerable_count: int,
    top_pqc_candidates: List[str],
    risk_counts: Dict[str, int] = None,
    mosca_info: Dict[str, Any] = None,
    recommendation_counts: Dict[str, int] = None
) -> str:
    r_counts = risk_counts or {}
    m_info = mosca_info or {}
    rec_counts = recommendation_counts or {}

    summary = f"""# Executive Cryptographic Risk & PQC Migration Report

**Project Name:** {project_name}  
**Scans Analyzed:** {scan_count}  
**Total Cryptographic Assets Discovered:** {total_assets}  
**Quantum Vulnerable Assets:** {vulnerable_count}  
**Post-Quantum Readiness Level:** {"CRITICAL RISK — IMMEDIATE ACTION REQUIRED" if (r_counts.get("critical", 0) > 0 or vulnerable_count > 0) else "SECURE / HIGH READINESS"}  

---

## 1. Inventory & Algorithm Breakdown
- Discovered **{total_assets}** cryptographic mechanisms across source code, configuration files, and dependencies.
- **{vulnerable_count}** primitives use legacy public-key algorithms (RSA, ECDSA, ECDH) vulnerable to Shor's algorithm on a Cryptanalytically Relevant Quantum Computer (CRQC).

## 2. Quantum Risk Assessment
- **Critical Risk:** {r_counts.get('critical', 0)} assets
- **High Risk:** {r_counts.get('high', 0)} assets
- **Medium Risk:** {r_counts.get('moderate', 0) or r_counts.get('medium', 0)} assets
- **Low Risk:** {r_counts.get('low', 0)} assets

## 3. Mosca Threat Horizon Analysis ($X + Y > Z$)
- **Data Protection Lifetime ($X$):** {m_info.get('data_lifetime_years', 10)} years
- **Estimated Migration Time ($Y$):** {m_info.get('migration_time_years', 3)} years
- **Projected Quantum Threat Horizon ($Z$):** Year {m_info.get('quantum_threat_horizon', 2033)}
- **Verdict:** {"DEADLINE BREACH DETECTED ($M_i > 0$)" if m_info.get('critical_components', 0) > 0 or vulnerable_count > 0 else "CONTROLLED HORIZON"}

## 4. Recommended NIST PQC & Hybrid Migration Pathways
- **Primary PQC Replacements:** {', '.join(top_pqc_candidates) if top_pqc_candidates else 'ML-KEM (FIPS 203), ML-DSA (FIPS 204), SLH-DSA (FIPS 205)'}
- **PQC Replacements Required:** {rec_counts.get('pqc_replacements', vulnerable_count)}
- **Hybrid Deployments:** {rec_counts.get('hybrid_deployments', 0)}
- **Retained Symmetric Primitives:** {rec_counts.get('retained_symmetric', max(0, total_assets - vulnerable_count))}
"""
    return summary
