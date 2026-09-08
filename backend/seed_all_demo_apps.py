import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.core.database import engine, Base, SessionLocal
from app.knowledge.knowledge_loader import init_knowledge_base
from app.repositories.project_repository import ProjectRepository
from app.repositories.scan_repository import ScanRepository
from app.orchestration.scan_orchestrator import ScanOrchestrator

def seed_demo_apps():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        init_knowledge_base(db)
        project_repo = ProjectRepository(db)
        scan_repo = ScanRepository(db)
        orchestrator = ScanOrchestrator()

        base_test_apps = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test_apps"))

        apps = [
            {"name": "demo-bank", "path": os.path.join(base_test_apps, "demo-bank")},
            {"name": "demo-government", "path": os.path.join(base_test_apps, "demo-government")},
            {"name": "demo-healthcare", "path": os.path.join(base_test_apps, "demo-healthcare")}
        ]

        for item in apps:
            existing = [p for p in project_repo.get_multi() if p.name == item["name"]]
            if not existing:
                proj = project_repo.create(type("Obj", (), {
                    "name": item["name"],
                    "description": f"Synthetic demo repository for {item['name']}",
                    "repository_url": None
                }))
            else:
                proj = existing[0]

            scan = scan_repo.create(project_id=proj.id, target_path=item["path"], scan_type="source")
            orchestrator.run_scan(scan.id, db)


    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_apps()
