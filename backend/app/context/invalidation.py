from typing import Optional
from sqlalchemy.orm import Session
from app.models.db_models import Project
from app.repositories.asset_repository import AssetRepository
from app.repositories.scan_repository import ScanRepository
from app.orchestration.job_manager import dispatch_post_scan_enrichment_job
from app.core.logging import logger


def invalidate_project_precomputed_data(project_id: str, db: Session, re_enrich: bool = True) -> int:
    """
    Clears precomputed QARS, effective context, and canonical XYZ from operational
    (latest completed scan) asset extra_metadata when project-level context changes.
    
    CRITICAL HARDENING:
    1. Preserves historical scan assets as immutable historical snapshots.
    2. Invalidates ONLY the operational latest-completed scan assets.
    3. Schedules background re-enrichment via job_manager so fallback path does not become a permanent slow path.
    """
    asset_repo = AssetRepository(db)
    # Target ONLY operational latest-completed scan assets
    operational_assets = asset_repo.get_by_project(project_id, latest_only=True)
    invalidated_count = 0

    for asset in operational_assets:
        if asset.extra_metadata and isinstance(asset.extra_metadata, dict):
            extra = dict(asset.extra_metadata)
            modified = False
            for key in ["qars_result", "effective_context", "effective_z", "effective_y"]:
                if key in extra:
                    extra.pop(key, None)
                    modified = True
            if modified:
                asset.extra_metadata = extra
                db.add(asset)
                invalidated_count += 1

    if invalidated_count > 0:
        db.commit()
        logger.info(f"Invalidated precomputed operational data for {invalidated_count} assets in project '{project_id}'.")

    # Schedule background re-enrichment for the latest completed scan
    if re_enrich:
        scan_repo = ScanRepository(db)
        scans = scan_repo.get_by_project(project_id)
        completed_scans = [s for s in scans if getattr(s.status, "value", str(s.status)) == "COMPLETED"]
        if completed_scans:
            latest_scan_id = completed_scans[-1].id
            dispatch_post_scan_enrichment_job(latest_scan_id)
            logger.info(f"Scheduled background re-enrichment for latest scan ID '{latest_scan_id}'.")

    return invalidated_count
