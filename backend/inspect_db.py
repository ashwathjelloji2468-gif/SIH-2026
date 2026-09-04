import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.db_models import Project, Scan, CryptoAsset, Evidence
from fastapi.testclient import TestClient
from app.main import app

def inspect():
    db: Session = SessionLocal()
    try:
        projects = db.query(Project).all()
        print(f"Total Projects in Database: {len(projects)}\n")

        for p in projects:
            print("=" * 60)
            print(f"Project ID: {p.id}")
            print(f"Project Name: {p.name}")
            print(f"Description: {p.description}")
            
            scans = db.query(Scan).filter(Scan.project_id == p.id).all()
            print(f"Scan Count: {len(scans)}")
            for s in scans:
                print(f"  - Scan ID: {s.id} | Status: {s.status.value} | Target Path: {s.target_path} | CBOM Ver: {s.cbom_version}")
            
            assets = db.query(CryptoAsset).join(CryptoAsset.scan).filter(Scan.project_id == p.id).all()
            print(f"Total CryptoAsset Rows: {len(assets)}")
            
            evidence_count = db.query(Evidence).join(Evidence.asset).join(CryptoAsset.scan).filter(Scan.project_id == p.id).count()
            print(f"Total Evidence Rows: {evidence_count}")

            if assets:
                print("\nSample Findings (First 5):")
                for a in assets[:5]:
                    ev = a.evidence_items[0] if a.evidence_items else None
                    conf = ev.confidence_score if ev else 1.0
                    ev_type = ev.evidence_type.value if ev else "OBSERVED"
                    print(f"  * Alg: {a.algorithm_name:<16} | File: {a.location} (Line {a.line_number}) | Conf: {conf} | Type: {ev_type}")
            print()

        print("\n--- Verifying FastAPI REST API Endpoints ---")
        client = TestClient(app)
        api_res = client.get("/api/v1/projects")
        print(f"GET /api/v1/projects -> Status {api_res.status_code}, Returned {len(api_res.json())} projects")

        for p in api_res.json():
            inv_res = client.get(f"/api/v1/projects/{p['id']}/inventory")
            inv_data = inv_res.json()
            print(f"  - Project '{p['name']}': GET /inventory returned {len(inv_data)} dynamic assets from DB")

    finally:
        db.close()

if __name__ == "__main__":
    inspect()
