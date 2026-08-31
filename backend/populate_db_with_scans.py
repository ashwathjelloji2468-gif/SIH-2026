import os
import sys

# Ensure backend app is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.core.database import engine, Base, SessionLocal
from app.knowledge.knowledge_loader import init_knowledge_base
from app.repositories.project_repository import ProjectRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.asset_repository import AssetRepository
from app.orchestration.scan_orchestrator import ScanOrchestrator
from app.risk.risk_engine import RiskEngine
from app.recommend.engine import RecommendationEngine

def run_seed():
    print("Initializing Database & Knowledge Base...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        init_knowledge_base(db)

        project_repo = ProjectRepository(db)
        scan_repo = ScanRepository(db)
        asset_repo = AssetRepository(db)
        orchestrator = ScanOrchestrator()
        risk_engine = RiskEngine()
        recommendation_engine = RecommendationEngine()

        targets = [
            {
                "name": "pyca/cryptography",
                "description": "Python core cryptographic primitives library",
                "repo": "https://github.com/pyca/cryptography",
                "path": "/Users/jashwath/.gemini/antigravity/scratch/cloned_repos/cryptography/src/cryptography"
            },
            {
                "name": "paramiko/paramiko",
                "description": "Python SSHv2 protocol implementation",
                "repo": "https://github.com/paramiko/paramiko",
                "path": "/Users/jashwath/.gemini/antigravity/scratch/cloned_repos/paramiko/paramiko"
            }
        ]

        summary_results = []

        for item in targets:
            print(f"\n--- Scanning Project: {item['name']} ---")
            # Create Project
            proj = project_repo.create(type("Obj", (), {
                "name": item["name"],
                "description": item["description"],
                "repository_url": item["repo"]
            }))

            # Create Scan
            scan = scan_repo.create(project_id=proj.id, target_path=item["path"], scan_type="source")
            
            # Execute Scan synchronously
            orchestrator.run_scan(scan.id, db)

            # Query discovered assets
            assets = asset_repo.get_by_project(proj.id)

            # Run Risk & Recommendation Engine
            for asset in assets:
                risk_engine.evaluate_asset_risk(asset.algorithm_name, asset.quantum_safety)
                recommendation_engine.evaluate_recommendations(asset)

            # Collect summary statistics
            alg_counts = {}
            for a in assets:
                alg_counts[a.algorithm_name] = alg_counts.get(a.algorithm_name, 0) + 1

            sample_findings = [
                {
                    "name": a.name,
                    "algorithm": a.algorithm_name,
                    "location": a.location,
                    "line": a.line_number,
                    "purpose": a.purpose.value if hasattr(a.purpose, "value") else str(a.purpose),
                    "quantum_safety": a.quantum_safety.value if hasattr(a.quantum_safety, "value") else str(a.quantum_safety)
                }
                for a in assets[:10]
            ]

            summary_results.append({
                "project_id": proj.id,
                "name": proj.name,
                "asset_count": len(assets),
                "top_algorithms": alg_counts,
                "sample_findings": sample_findings
            })

        return summary_results

    finally:
        db.close()

if __name__ == "__main__":
    results = run_seed()
    print("\n================ DYNAMIC SCAN SUMMARY ================")
    for res in results:
        print(f"\nProject: {res['name']} (ID: {res['project_id']})")
        print(f"Total CryptoAssets Discovered: {res['asset_count']}")
        print(f"Algorithm Distribution: {res['top_algorithms']}")
        print("Sample Findings (Top 5-10):")
        for f in res['sample_findings']:
            print(f"  - [{f['algorithm']}] {f['location']}:L{f['line']} ({f['purpose']}, {f['quantum_safety']})")
