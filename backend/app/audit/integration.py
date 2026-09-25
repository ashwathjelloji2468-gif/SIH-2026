from typing import Any, Dict, Optional
from app.core.logging import logger
from app.audit.models import AuditArtifactType, AuditResult, AuditStatus
from app.audit.service import AuditService, sanitize_metadata


_audit_service: Optional[AuditService] = None


def get_shared_audit_service() -> AuditService:
    """
    Returns shared AuditService instance.
    """
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service


def audit_cbom_snapshot(
    cbom_payload: Dict[str, Any],
    scan_id: str,
    project_id: Optional[str] = None,
    service: Optional[AuditService] = None,
) -> Optional[AuditResult]:
    """
    Non-blocking helper to audit a finalized CBOM snapshot.
    """
    try:
        srv = service or get_shared_audit_service()
        artifact_id = f"cbom-{scan_id}" if scan_id else "cbom-unknown"
        metadata = {
            "scan_id": scan_id,
            "project_id": project_id,
            "spec_version": cbom_payload.get("specVersion", "1.6"),
            "bom_format": cbom_payload.get("bomFormat", "CycloneDX"),
        }
        return srv.record_artifact(
            artifact_type=AuditArtifactType.CBOM_SNAPSHOT,
            artifact_id=artifact_id,
            payload=cbom_payload,
            metadata=metadata,
        )
    except Exception as e:
        logger.warning(f"CBOM audit non-blocking failure for scan {scan_id}: {e}")
        return None


def audit_risk_snapshot(
    risk_payload: Dict[str, Any],
    target_id: str,
    is_project: bool = False,
    service: Optional[AuditService] = None,
) -> Optional[AuditResult]:
    """
    Non-blocking helper to audit a finalized Risk Assessment snapshot.
    """
    try:
        srv = service or get_shared_audit_service()
        artifact_id = f"risk-proj-{target_id}" if is_project else f"risk-asset-{target_id}"
        metadata = {
            "target_id": target_id,
            "is_project": is_project,
            "risk_score": risk_payload.get("risk_score") or risk_payload.get("overall_risk_score"),
        }
        return srv.record_artifact(
            artifact_type=AuditArtifactType.RISK_ASSESSMENT_SNAPSHOT,
            artifact_id=artifact_id,
            payload=risk_payload,
            metadata=metadata,
        )
    except Exception as e:
        logger.warning(f"Risk audit non-blocking failure for target {target_id}: {e}")
        return None


def audit_recommendation_snapshot(
    rec_payload: Dict[str, Any],
    asset_id: str,
    service: Optional[AuditService] = None,
) -> Optional[AuditResult]:
    """
    Non-blocking helper to audit a finalized PQC Recommendation snapshot.
    """
    try:
        srv = service or get_shared_audit_service()
        artifact_id = f"rec-{asset_id}"
        metadata = {
            "asset_id": asset_id,
            "profile": rec_payload.get("profile", "BALANCED"),
            "target_pqc_candidate": rec_payload.get("target_pqc_candidate"),
        }
        return srv.record_artifact(
            artifact_type=AuditArtifactType.RECOMMENDATION_SNAPSHOT,
            artifact_id=artifact_id,
            payload=rec_payload,
            metadata=metadata,
        )
    except Exception as e:
        logger.warning(f"Recommendation audit non-blocking failure for asset {asset_id}: {e}")
        return None


def audit_validation_result(
    val_payload: Dict[str, Any],
    validation_id: str,
    service: Optional[AuditService] = None,
) -> Optional[AuditResult]:
    """
    Non-blocking helper to audit a finalized Migration Validation result.
    """
    try:
        srv = service or get_shared_audit_service()
        artifact_id = f"val-{validation_id}"
        metadata = {
            "validation_id": validation_id,
            "status": val_payload.get("status") or val_payload.get("overall_result"),
            "build_passed": val_payload.get("build_passed"),
        }
        return srv.record_artifact(
            artifact_type=AuditArtifactType.MIGRATION_VALIDATION_RESULT,
            artifact_id=artifact_id,
            payload=val_payload,
            metadata=metadata,
        )
    except Exception as e:
        logger.warning(f"Validation audit non-blocking failure for validation {validation_id}: {e}")
        return None
