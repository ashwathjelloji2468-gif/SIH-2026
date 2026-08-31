from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.db_models import Project
from app.models.schemas import ProjectCreate, ProjectUpdate

class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, obj_in: ProjectCreate) -> Project:
        db_obj = Project(
            name=obj_in.name,
            description=obj_in.description,
            repository_url=obj_in.repository_url
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get(self, project_id: str) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Project]:
        return self.db.query(Project).offset(skip).limit(limit).all()

    def update(self, project_id: str, obj_in: ProjectUpdate) -> Optional[Project]:
        db_obj = self.get(project_id)
        if not db_obj:
            return None
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, project_id: str) -> bool:
        db_obj = self.get(project_id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
