from app.reports.executive_summary import build_executive_summary

class ReportGenerator:
    def generate_project_report(self, project_name: str, assets: list) -> dict:
        vulnerable = [a for a in assets if getattr(a.quantum_safety, "value", str(a.quantum_safety)) == "QUANTUM_VULNERABLE"]
        
        summary_text = build_executive_summary(
            project_name=project_name,
            scan_count=1,
            total_assets=len(assets),
            vulnerable_count=len(vulnerable),
            top_pqc_candidates=["ML-KEM (FIPS 203)", "ML-DSA (FIPS 204)"]
        )

        return {
            "project_name": project_name,
            "total_assets": len(assets),
            "vulnerable_assets": len(vulnerable),
            "summary_md": summary_text
        }
